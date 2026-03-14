import { randomUUID } from "node:crypto";
import { ChildProcessWithoutNullStreams, spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import readline, { Interface as ReadLineInterface } from "node:readline";

export const PLUGIN_ID = "ninjaclawbot";

const DEFAULT_BRIDGE_START_TIMEOUT_MS = 10_000;
const DEFAULT_BRIDGE_REQUEST_TIMEOUT_MS = 15_000;
const DEFAULT_BRIDGE_SHUTDOWN_TIMEOUT_MS = 5_000;

export interface OpenClawPluginConfig {
  projectRoot: string;
  rootDir?: string;
  uvCommand?: string;
  enablePersistentBridge?: boolean;
  bridgeStartTimeoutMs?: number;
  bridgeRequestTimeoutMs?: number;
  bridgeShutdownTimeoutMs?: number;
  enableAlwaysOn?: boolean;
  enableStartupGreeting?: boolean;
  enableAutoThinking?: boolean;
  enableShutdownSequence?: boolean;
}

export interface NinjaClawbotPayload {
  action: string;
  parameters?: Record<string, unknown>;
  request_id?: string;
}

interface OpenClawPluginApiLike {
  config?: Record<string, unknown>;
}

interface BridgeRequestEnvelope {
  type: string;
  request_id?: string;
  payload?: Record<string, unknown>;
}

interface BridgeResponseEnvelope {
  ok?: boolean;
  request_id?: string;
  data?: Record<string, unknown>;
  error?: string;
}

interface PendingBridgeRequest {
  resolve: (response: BridgeResponseEnvelope) => void;
  reject: (error: Error) => void;
  timer: NodeJS.Timeout;
}

interface BridgeClient {
  child: ChildProcessWithoutNullStreams;
  config: OpenClawPluginConfig;
  signature: string;
  pending: Map<string, PendingBridgeRequest>;
  stdout: ReadLineInterface;
  stderr: ReadLineInterface;
  exited: boolean;
}

type BridgeHealthState = "uninitialized" | "disabled" | "healthy" | "degraded";

export interface BridgeTelemetry {
  status: BridgeHealthState;
  lastError: string | null;
  fallbackCount: number;
  lastModeChangeAt: string | null;
  lastSuccessfulPersistentAt: string | null;
}

type ReadinessStatus = "ready" | "warning" | "misconfigured";
type DiagnosticsSummaryState =
  | "healthy"
  | "warning"
  | "degraded"
  | "one_shot_fallback"
  | "misconfigured";

export interface DisplayConfigSummary {
  configPath: string | null;
  rootConfigPath: string | null;
  packageConfigPath: string | null;
  usingRootConfig: boolean;
  configExists: boolean;
}

export interface DeploymentHealth {
  status: ReadinessStatus;
  persistentBridgeEnabled: boolean;
  minimalPluginConfig: boolean;
  usesOptionalLifecycleOverrides: boolean;
  bootMdEnabled: boolean;
  skillEnabled: boolean;
  workspacePath: string | null;
  workspaceExists: boolean;
  bootMdPath: string | null;
  bootMdPresent: boolean;
  agentsMdPath: string | null;
  agentsMdPresent: boolean;
  replyToolOptedIn: boolean;
  pluginOptedIn: boolean;
  diagnosticsToolOptedIn: boolean;
  allowlist: string[];
  issues: string[];
  warnings: string[];
}

export interface NinjaClawbotDiagnostics {
  bridge: BridgeTelemetry & { persistentBridgeEnabled: boolean; serviceConnected: boolean };
  service: Record<string, unknown> | null;
  deployment: DeploymentHealth;
  display: DisplayConfigSummary;
  summary: {
    state: DiagnosticsSummaryState;
    readiness: ReadinessStatus;
    message: string;
  };
  recoveryHints: string[];
}

let activeBridge: BridgeClient | null = null;
let bridgeTelemetry: BridgeTelemetry = {
  status: "uninitialized",
  lastError: null,
  fallbackCount: 0,
  lastModeChangeAt: null,
  lastSuccessfulPersistentAt: null,
};

const OPTIONAL_LIFECYCLE_CONFIG_KEYS = new Set([
  "enableAlwaysOn",
  "enableStartupGreeting",
  "enableAutoThinking",
  "enableShutdownSequence",
]);

const MINIMAL_PLUGIN_CONFIG_KEYS = new Set([
  "projectRoot",
  "rootDir",
  "uvCommand",
  "enablePersistentBridge",
  "bridgeStartTimeoutMs",
  "bridgeRequestTimeoutMs",
  "bridgeShutdownTimeoutMs",
]);

function updateBridgeTelemetry(
  status: BridgeHealthState,
  options: {
    error?: string | null;
    incrementFallback?: boolean;
    persistentSuccess?: boolean;
  } = {},
) {
  const changed = bridgeTelemetry.status !== status;
  bridgeTelemetry = {
    status,
    lastError: options.error ?? (status === "healthy" ? null : bridgeTelemetry.lastError),
    fallbackCount:
      bridgeTelemetry.fallbackCount + (options.incrementFallback === true ? 1 : 0),
    lastModeChangeAt: changed ? new Date().toISOString() : bridgeTelemetry.lastModeChangeAt,
    lastSuccessfulPersistentAt:
      options.persistentSuccess === true
        ? new Date().toISOString()
        : bridgeTelemetry.lastSuccessfulPersistentAt,
  };
}

export function readBridgeTelemetry(): BridgeTelemetry {
  return { ...bridgeTelemetry };
}

function asObject(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

function asBoolean(value: unknown, fallback: boolean): boolean {
  return typeof value === "boolean" ? value : fallback;
}

function asPositiveInt(value: unknown, fallback: number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? Math.trunc(parsed) : fallback;
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .filter((item): item is string => typeof item === "string")
    .map((item) => item.trim())
    .filter(Boolean);
}

function expandUserPath(rawPath: string | null): string | null {
  if (!rawPath) {
    return null;
  }
  if (rawPath === "~") {
    return os.homedir();
  }
  if (rawPath.startsWith("~/")) {
    return path.join(os.homedir(), rawPath.slice(2));
  }
  return rawPath;
}

function workspacePathFromConfig(api: OpenClawPluginApiLike): string | null {
  const root = asObject(api.config);
  const agents = asObject(root.agents);
  const defaults = asObject(agents.defaults);
  const list = Array.isArray(agents.list)
    ? agents.list.filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === "object")
    : [];
  const mainAgent =
    list.find((item) => String(item.id ?? "").trim() === "main") ?? list[0] ?? {};

  const workspace = String(mainAgent.workspace ?? defaults.workspace ?? "").trim();
  return expandUserPath(workspace || null);
}

function readRawPluginEntryConfig(api: OpenClawPluginApiLike): Record<string, unknown> {
  const root = asObject(api.config);
  const plugins = asObject(root.plugins);
  const entries = asObject(plugins.entries);
  const entry = asObject(entries[PLUGIN_ID]);
  return asObject(entry.config);
}

function readCombinedToolOptInList(api: OpenClawPluginApiLike): string[] {
  const root = asObject(api.config);
  const globalTools = asObject(root.tools);
  const agents = asObject(root.agents);
  const defaults = asObject(agents.defaults);
  const list = Array.isArray(agents.list)
    ? agents.list.filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === "object")
    : [];
  const mainAgent =
    list.find((item) => String(item.id ?? "").trim() === "main") ?? list[0] ?? {};
  const mainTools = asObject(mainAgent.tools);
  const defaultTools = asObject(defaults.tools);

  return Array.from(
    new Set([
      ...asStringArray(globalTools.allow),
      ...asStringArray(globalTools.alsoAllow),
      ...asStringArray(defaultTools.allow),
      ...asStringArray(defaultTools.alsoAllow),
      ...asStringArray(mainTools.allow),
      ...asStringArray(mainTools.alsoAllow),
    ]),
  );
}

function isToolOptedIn(allowlist: string[], toolName: string): boolean {
  return allowlist.includes("group:plugins") || allowlist.includes(PLUGIN_ID) || allowlist.includes(toolName);
}

export function readDisplayConfigSummary(config: OpenClawPluginConfig): DisplayConfigSummary {
  const rootConfigPath = path.resolve(config.rootDir ?? config.projectRoot, "display.json");
  const packageConfigPath = path.resolve(config.projectRoot, "pi5disp", "display.json");
  const usingRootConfig = fs.existsSync(rootConfigPath);
  const configPath = usingRootConfig ? rootConfigPath : packageConfigPath;

  return {
    configPath,
    rootConfigPath,
    packageConfigPath,
    usingRootConfig,
    configExists: fs.existsSync(configPath),
  };
}

export function inspectDeploymentHealth(api: OpenClawPluginApiLike): DeploymentHealth {
  const rawPluginConfig = readRawPluginEntryConfig(api);
  const rawPluginKeys = Object.keys(rawPluginConfig);
  const allowlist = readCombinedToolOptInList(api);
  const workspacePath = workspacePathFromConfig(api);
  const workspaceExists =
    workspacePath !== null && fs.existsSync(workspacePath) && fs.statSync(workspacePath).isDirectory();
  const bootMdPath = workspacePath ? path.join(workspacePath, "BOOT.md") : null;
  const agentsMdPath = workspacePath ? path.join(workspacePath, "AGENTS.md") : null;
  const bootMdPresent = bootMdPath !== null && fs.existsSync(bootMdPath);
  const agentsMdPresent = agentsMdPath !== null && fs.existsSync(agentsMdPath);

  const root = asObject(api.config);
  const hooks = asObject(root.hooks);
  const internalHooks = asObject(hooks.internal);
  const internalEntries = asObject(internalHooks.entries);
  const bootMdEntry = asObject(internalEntries["boot-md"]);
  const skills = asObject(root.skills);
  const skillEntries = asObject(skills.entries);
  const skillEntry = asObject(skillEntries.ninjaclawbot_control);

  let config: OpenClawPluginConfig | null = null;
  const issues: string[] = [];
  const warnings: string[] = [];

  try {
    config = extractPluginConfig(api);
  } catch (error) {
    issues.push(error instanceof Error ? error.message : String(error));
  }

  const persistentBridgeEnabled = config?.enablePersistentBridge ?? false;
  const bootMdEnabled =
    asBoolean(internalHooks.enabled, false) && asBoolean(bootMdEntry.enabled, false);
  const skillEnabled = asBoolean(skillEntry.enabled, false);
  const replyToolOptedIn = isToolOptedIn(allowlist, "ninjaclawbot_reply");
  const pluginOptedIn = allowlist.includes(PLUGIN_ID) || allowlist.includes("group:plugins");
  const diagnosticsToolOptedIn = isToolOptedIn(allowlist, "ninjaclawbot_diagnostics");
  const minimalPluginConfig = rawPluginKeys.every((key) => MINIMAL_PLUGIN_CONFIG_KEYS.has(key));
  const usesOptionalLifecycleOverrides = rawPluginKeys.some((key) =>
    OPTIONAL_LIFECYCLE_CONFIG_KEYS.has(key),
  );

  if (!persistentBridgeEnabled) {
    warnings.push("Persistent bridge is disabled; lifecycle features will fall back to one-shot mode.");
  }
  if (!workspacePath) {
    warnings.push("No OpenClaw workspace path is configured.");
  } else if (!workspaceExists) {
    warnings.push("Configured OpenClaw workspace path does not exist.");
  }
  if (!bootMdEnabled) {
    warnings.push("boot-md is not enabled; startup greeting may not run.");
  }
  if (workspaceExists && !bootMdPresent) {
    warnings.push("Workspace BOOT.md is missing; startup greeting may not run.");
  }
  if (workspaceExists && !agentsMdPresent) {
    warnings.push("Workspace AGENTS.md is missing; reply-tool guidance may be weaker.");
  }
  if (!skillEnabled) {
    warnings.push("ninjaclawbot_control skill is not enabled.");
  }
  if (!replyToolOptedIn) {
    issues.push("The main OpenClaw agent does not allow ninjaclawbot reply tools.");
  }
  if (usesOptionalLifecycleOverrides) {
    warnings.push(
      "Optional lifecycle override keys are configured; the release-tested deployment uses the minimal plugin config.",
    );
  }

  return {
    status: issues.length > 0 ? "misconfigured" : warnings.length > 0 ? "warning" : "ready",
    persistentBridgeEnabled,
    minimalPluginConfig,
    usesOptionalLifecycleOverrides,
    bootMdEnabled,
    skillEnabled,
    workspacePath,
    workspaceExists,
    bootMdPath,
    bootMdPresent,
    agentsMdPath,
    agentsMdPresent,
    replyToolOptedIn,
    pluginOptedIn,
    diagnosticsToolOptedIn,
    allowlist,
    issues,
    warnings,
  };
}

function buildRecoveryHints(
  diagnostics: Pick<NinjaClawbotDiagnostics, "bridge" | "deployment" | "display" | "summary">,
): string[] {
  const hints: string[] = [];
  const { bridge, deployment, display, summary } = diagnostics;

  if (bridge.lastError && bridge.lastError.includes("ENOENT")) {
    hints.push("Set plugins.entries.ninjaclawbot.config.uvCommand to the absolute path from `command -v uv`.");
  }
  if (!deployment.replyToolOptedIn) {
    hints.push("Allowlist `ninjaclawbot` or `ninjaclawbot_reply` for the main OpenClaw agent.");
  }
  if (!deployment.bootMdEnabled || !deployment.bootMdPresent) {
    hints.push("Enable `boot-md` and make sure the workspace BOOT.md file exists for the startup greeting.");
  }
  if (!deployment.agentsMdPresent || !deployment.skillEnabled) {
    hints.push(
      "Keep workspace AGENTS.md and the `ninjaclawbot_control` skill enabled so reply expressions stay reliable.",
    );
  }
  if (!bridge.persistentBridgeEnabled || summary.state === "one_shot_fallback") {
    hints.push("Re-enable the persistent bridge if you want Always On lifecycle behavior instead of one-shot fallback.");
  }
  if (!display.usingRootConfig) {
    hints.push(
      "If display orientation is wrong, export the pi5disp config into the project root with `uv run pi5disp config export \"$PWD/display.json\"`.",
    );
  }

  return Array.from(new Set(hints));
}

function summarizeDiagnostics(
  bridge: NinjaClawbotDiagnostics["bridge"],
  deployment: DeploymentHealth,
): NinjaClawbotDiagnostics["summary"] {
  if (deployment.status === "misconfigured") {
    return {
      state: "misconfigured",
      readiness: deployment.status,
      message: deployment.issues[0] ?? "The OpenClaw deployment is misconfigured.",
    };
  }
  if (bridge.status === "disabled") {
    return {
      state: "one_shot_fallback",
      readiness: deployment.status,
      message: "Persistent bridge is disabled; only one-shot robot actions are available.",
    };
  }
  if (bridge.status === "degraded") {
    return {
      state: "degraded",
      readiness: deployment.status,
      message: bridge.lastError ?? "Persistent bridge is degraded.",
    };
  }
  if (deployment.status === "warning") {
    return {
      state: "warning",
      readiness: deployment.status,
      message: deployment.warnings[0] ?? "Deployment has warnings but is still usable.",
    };
  }
  return {
    state: "healthy",
    readiness: deployment.status,
    message: "Persistent bridge and validated deployment prerequisites are healthy.",
  };
}

export function alwaysOnEnabled(config: OpenClawPluginConfig): boolean {
  return Boolean(config.enablePersistentBridge && config.enableAlwaysOn);
}

function configSignature(config: OpenClawPluginConfig): string {
  return JSON.stringify({
    projectRoot: config.projectRoot,
    rootDir: config.rootDir,
    uvCommand: config.uvCommand,
    enablePersistentBridge: config.enablePersistentBridge,
    bridgeStartTimeoutMs: config.bridgeStartTimeoutMs,
    bridgeRequestTimeoutMs: config.bridgeRequestTimeoutMs,
    bridgeShutdownTimeoutMs: config.bridgeShutdownTimeoutMs,
    enableAlwaysOn: config.enableAlwaysOn,
    enableStartupGreeting: config.enableStartupGreeting,
    enableAutoThinking: config.enableAutoThinking,
    enableShutdownSequence: config.enableShutdownSequence,
  });
}

export function extractPluginConfig(api: OpenClawPluginApiLike): OpenClawPluginConfig {
  const root = asObject(api.config);
  const plugins = asObject(root.plugins);
  const entries = asObject(plugins.entries);
  const entry = asObject(entries[PLUGIN_ID]);
  const config = asObject(entry.config);

  const projectRoot = String(config.projectRoot ?? "").trim();
  if (!projectRoot) {
    throw new Error(
      "The ninjaclawbot OpenClaw plugin requires plugins.entries.ninjaclawbot.config.projectRoot.",
    );
  }

  const rootDir = String(config.rootDir ?? projectRoot).trim() || projectRoot;
  const uvCommand = String(config.uvCommand ?? "uv").trim() || "uv";

  return {
    projectRoot,
    rootDir,
    uvCommand,
    enablePersistentBridge: asBoolean(config.enablePersistentBridge, true),
    bridgeStartTimeoutMs: asPositiveInt(
      config.bridgeStartTimeoutMs,
      DEFAULT_BRIDGE_START_TIMEOUT_MS,
    ),
    bridgeRequestTimeoutMs: asPositiveInt(
      config.bridgeRequestTimeoutMs,
      DEFAULT_BRIDGE_REQUEST_TIMEOUT_MS,
    ),
    bridgeShutdownTimeoutMs: asPositiveInt(
      config.bridgeShutdownTimeoutMs,
      DEFAULT_BRIDGE_SHUTDOWN_TIMEOUT_MS,
    ),
    enableAlwaysOn: asBoolean(config.enableAlwaysOn, true),
    enableStartupGreeting: asBoolean(config.enableStartupGreeting, true),
    enableAutoThinking: asBoolean(config.enableAutoThinking, true),
    enableShutdownSequence: asBoolean(config.enableShutdownSequence, true),
  };
}

export function buildCommand(config: OpenClawPluginConfig, payload: NinjaClawbotPayload) {
  return {
    command: config.uvCommand ?? "uv",
    args: [
      "run",
      "--project",
      config.projectRoot,
      "ninjaclawbot",
      "--root-dir",
      config.rootDir ?? config.projectRoot,
      "openclaw-action",
      JSON.stringify(payload),
    ],
    cwd: config.projectRoot,
  };
}

export function buildServeCommand(config: OpenClawPluginConfig) {
  return {
    command: config.uvCommand ?? "uv",
    args: [
      "run",
      "--project",
      config.projectRoot,
      "ninjaclawbot",
      "--root-dir",
      config.rootDir ?? config.projectRoot,
      "openclaw-serve",
    ],
    cwd: config.projectRoot,
  };
}

export function parseBridgeOutput(output: string) {
  const trimmed = output.trim();
  if (!trimmed) {
    throw new Error("ninjaclawbot bridge returned empty output.");
  }

  try {
    return JSON.parse(trimmed) as Record<string, unknown>;
  } catch {
    const start = trimmed.indexOf("{");
    const end = trimmed.lastIndexOf("}");
    if (start >= 0 && end > start) {
      return JSON.parse(trimmed.slice(start, end + 1)) as Record<string, unknown>;
    }
    throw new Error(`Could not parse ninjaclawbot bridge output: ${trimmed}`);
  }
}

function rejectPending(client: BridgeClient, error: Error) {
  for (const [requestId, pending] of client.pending.entries()) {
    clearTimeout(pending.timer);
    pending.reject(error);
    client.pending.delete(requestId);
  }
}

function handleBridgeResponseLine(client: BridgeClient, line: string) {
  let response: BridgeResponseEnvelope;
  try {
    response = JSON.parse(line) as BridgeResponseEnvelope;
  } catch {
    rejectPending(client, new Error(`Invalid bridge response: ${line}`));
    return;
  }

  const requestId = response.request_id;
  if (!requestId) {
    return;
  }

  const pending = client.pending.get(requestId);
  if (!pending) {
    return;
  }

  clearTimeout(pending.timer);
  client.pending.delete(requestId);
  pending.resolve(response);
}

function createBridgeClient(config: OpenClawPluginConfig): BridgeClient {
  const command = buildServeCommand(config);
  const child = spawn(command.command, command.args, {
    cwd: command.cwd,
    env: process.env,
    stdio: ["pipe", "pipe", "pipe"],
  });

  const client: BridgeClient = {
    child,
    config,
    signature: configSignature(config),
    pending: new Map<string, PendingBridgeRequest>(),
    stdout: readline.createInterface({ input: child.stdout }),
    stderr: readline.createInterface({ input: child.stderr }),
    exited: false,
  };

  client.stdout.on("line", (line) => {
    handleBridgeResponseLine(client, line);
  });
  client.stderr.on("line", (line) => {
    if (line.trim()) {
      console.warn(`[ninjaclawbot-bridge] ${line}`);
    }
  });
  child.on("error", (error) => {
    rejectPending(client, error instanceof Error ? error : new Error(String(error)));
  });
  child.on("close", (code) => {
    client.exited = true;
    client.stdout.close();
    client.stderr.close();
    rejectPending(
      client,
      new Error(`Persistent ninjaclawbot bridge exited with code ${String(code ?? "null")}.`),
    );
    if (activeBridge === client) {
      activeBridge = null;
    }
  });

  return client;
}

function sendBridgeRequest(
  client: BridgeClient,
  envelope: BridgeRequestEnvelope,
  timeoutMs: number,
): Promise<BridgeResponseEnvelope> {
  if (client.exited) {
    return Promise.reject(new Error("Persistent ninjaclawbot bridge is not running."));
  }

  const requestId = envelope.request_id ?? randomUUID();
  const payload = JSON.stringify({ ...envelope, request_id: requestId });

  return new Promise<BridgeResponseEnvelope>((resolve, reject) => {
    const timer = setTimeout(() => {
      client.pending.delete(requestId);
      reject(
        new Error(
          `Persistent ninjaclawbot bridge request '${envelope.type}' timed out after ${timeoutMs}ms.`,
        ),
      );
    }, timeoutMs);

    client.pending.set(requestId, { resolve, reject, timer });
    client.child.stdin.write(`${payload}\n`, (error) => {
      if (!error) {
        return;
      }
      clearTimeout(timer);
      client.pending.delete(requestId);
      reject(error instanceof Error ? error : new Error(String(error)));
    });
  });
}

async function runNinjaClawbotActionOneShot(
  config: OpenClawPluginConfig,
  payload: NinjaClawbotPayload,
) {
  const command = buildCommand(config, payload);

  return await new Promise<Record<string, unknown>>((resolve, reject) => {
    const child = spawn(command.command, command.args, {
      cwd: command.cwd,
      env: process.env,
      stdio: ["ignore", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (chunk) => {
      stdout += String(chunk);
    });
    child.stderr.on("data", (chunk) => {
      stderr += String(chunk);
    });
    child.on("error", (error) => {
      reject(error);
    });
    child.on("close", (code) => {
      if (code !== 0) {
        reject(
          new Error(
            `ninjaclawbot bridge exited with code ${code}: ${stderr.trim() || stdout.trim()}`,
          ),
        );
        return;
      }
      try {
        resolve(parseBridgeOutput(stdout));
      } catch (error) {
        reject(error);
      }
    });
  });
}

async function runPersistentBridgeRequest(
  api: OpenClawPluginApiLike,
  envelope: BridgeRequestEnvelope,
  context: string,
  timeoutMs?: number,
): Promise<Record<string, unknown> | null> {
  const config = extractPluginConfig(api);
  if (!alwaysOnEnabled(config)) {
    if (!config.enablePersistentBridge) {
      updateBridgeTelemetry("disabled");
    }
    return null;
  }

  try {
    await ensureBridge(api);
    if (!activeBridge) {
      throw new Error("Persistent ninjaclawbot bridge is unavailable.");
    }

    const response = await sendBridgeRequest(
      activeBridge,
      envelope,
      timeoutMs ?? config.bridgeRequestTimeoutMs ?? DEFAULT_BRIDGE_REQUEST_TIMEOUT_MS,
    );
    if (!response.ok) {
      throw new Error(response.error ?? `${context} failed.`);
    }
    updateBridgeTelemetry("healthy", { persistentSuccess: true });
    return response.data ?? {};
  } catch (error) {
    updateBridgeTelemetry("degraded", {
      error: error instanceof Error ? error.message : String(error),
    });
    console.warn(
      `[ninjaclawbot-bridge] ${context}: ${
        error instanceof Error ? error.message : String(error)
      }`,
    );
    await shutdownBridge();
    return null;
  }
}

export async function ensureBridge(api: OpenClawPluginApiLike): Promise<void> {
  const config = extractPluginConfig(api);
  if (!config.enablePersistentBridge) {
    updateBridgeTelemetry("disabled");
    return;
  }

  const signature = configSignature(config);
  if (activeBridge && activeBridge.signature !== signature) {
    await shutdownBridge();
  }
  if (!activeBridge) {
    activeBridge = createBridgeClient(config);
  }

  try {
    const response = await sendBridgeRequest(
      activeBridge,
      { type: "health_ping" },
      config.bridgeStartTimeoutMs ?? DEFAULT_BRIDGE_START_TIMEOUT_MS,
    );
    if (!response.ok) {
      throw new Error(response.error ?? "Persistent ninjaclawbot bridge health check failed.");
    }
    updateBridgeTelemetry("healthy", { persistentSuccess: true });
  } catch (error) {
    updateBridgeTelemetry("degraded", {
      error: error instanceof Error ? error.message : String(error),
    });
    await shutdownBridge();
    throw error;
  }
}

export async function shutdownBridge(): Promise<void> {
  const client = activeBridge;
  activeBridge = null;
  if (!client || client.exited) {
    return;
  }

  const shutdownTimeout =
    client.config.bridgeShutdownTimeoutMs ?? DEFAULT_BRIDGE_SHUTDOWN_TIMEOUT_MS;
  try {
    await sendBridgeRequest(client, { type: "shutdown" }, shutdownTimeout);
  } catch {
    // Fall through to hard termination below.
  }

  if (!client.exited) {
    client.child.kill("SIGTERM");
  }
  updateBridgeTelemetry("uninitialized");
}

export async function runStartupSequence(api: OpenClawPluginApiLike) {
  const config = extractPluginConfig(api);
  if (!alwaysOnEnabled(config) || !config.enableStartupGreeting) {
    return null;
  }

  return runPersistentBridgeRequest(api, { type: "startup_sequence" }, "Startup sequence failed");
}

export async function setPersistentPresenceMode(
  api: OpenClawPluginApiLike,
  mode: "idle" | "thinking" | "listening",
  lifecycleEvent: string,
) {
  const config = extractPluginConfig(api);
  if (!alwaysOnEnabled(config)) {
    return null;
  }
  if (mode === "thinking" && !config.enableAutoThinking) {
    return null;
  }

  return runPersistentBridgeRequest(
    api,
    {
      type: "set_presence_mode",
      payload: { mode, lifecycle_event: lifecycleEvent },
    },
    `Presence update '${mode}' failed`,
  );
}

export async function runShutdownSequence(
  api: OpenClawPluginApiLike,
  lifecycleEvent = "gateway_stop",
) {
  const config = extractPluginConfig(api);
  if (!alwaysOnEnabled(config) || !config.enableShutdownSequence) {
    return null;
  }

  return runPersistentBridgeRequest(
    api,
    {
      type: "shutdown_sequence",
      payload: { lifecycle_event: lifecycleEvent },
    },
    "Shutdown sequence failed",
    config.bridgeShutdownTimeoutMs ?? DEFAULT_BRIDGE_SHUTDOWN_TIMEOUT_MS,
  );
}

export async function readBridgeStatus(api: OpenClawPluginApiLike) {
  const config = extractPluginConfig(api);
  if (!config.enablePersistentBridge) {
    updateBridgeTelemetry("disabled");
    return null;
  }

  try {
    await ensureBridge(api);
    if (!activeBridge) {
      throw new Error("Persistent ninjaclawbot bridge is unavailable.");
    }
    const response = await sendBridgeRequest(
      activeBridge,
      { type: "status" },
      config.bridgeRequestTimeoutMs ?? DEFAULT_BRIDGE_REQUEST_TIMEOUT_MS,
    );
    if (!response.ok) {
      throw new Error(response.error ?? "Bridge status request failed.");
    }
    updateBridgeTelemetry("healthy", { persistentSuccess: true });
    return response.data ?? {};
  } catch (error) {
    updateBridgeTelemetry("degraded", {
      error: error instanceof Error ? error.message : String(error),
    });
    console.warn(
      `[ninjaclawbot-bridge] Bridge status failed: ${
        error instanceof Error ? error.message : String(error)
      }`,
    );
    await shutdownBridge();
    return null;
  }
}

export async function runDiagnostics(
  api: OpenClawPluginApiLike,
): Promise<NinjaClawbotDiagnostics> {
  const deployment = inspectDeploymentHealth(api);
  let serviceStatus: Record<string, unknown> | null = null;
  let config: OpenClawPluginConfig | null = null;

  try {
    config = extractPluginConfig(api);
    if (config.enablePersistentBridge) {
      serviceStatus = await readBridgeStatus(api);
    } else {
      updateBridgeTelemetry("disabled");
    }
  } catch (error) {
    updateBridgeTelemetry("degraded", {
      error: error instanceof Error ? error.message : String(error),
    });
  }

  const bridge = {
    ...readBridgeTelemetry(),
    persistentBridgeEnabled: deployment.persistentBridgeEnabled,
    serviceConnected: serviceStatus !== null,
  };
  const display =
    config !== null
      ? readDisplayConfigSummary(config)
      : {
          configPath: null,
          rootConfigPath: null,
          packageConfigPath: null,
          usingRootConfig: false,
          configExists: false,
        };
  const summary = summarizeDiagnostics(bridge, deployment);

  return {
    bridge,
    service: serviceStatus,
    deployment,
    display,
    summary,
    recoveryHints: buildRecoveryHints({
      bridge,
      deployment,
      display,
      summary,
    }),
  };
}

export async function runNinjaClawbotAction(
  api: OpenClawPluginApiLike,
  payload: NinjaClawbotPayload,
) {
  const config = extractPluginConfig(api);
  if (!config.enablePersistentBridge) {
    updateBridgeTelemetry("disabled");
    return runNinjaClawbotActionOneShot(config, payload);
  }

  try {
    await ensureBridge(api);
    if (!activeBridge) {
      throw new Error("Persistent ninjaclawbot bridge is unavailable.");
    }

    const response = await sendBridgeRequest(
      activeBridge,
      {
        type: "execute_action",
        payload: {
          action: payload.action,
          parameters: payload.parameters ?? {},
          request_id: payload.request_id,
        },
      },
      config.bridgeRequestTimeoutMs ?? DEFAULT_BRIDGE_REQUEST_TIMEOUT_MS,
    );

    if (!response.ok) {
      throw new Error(response.error ?? "Persistent ninjaclawbot bridge request failed.");
    }
    updateBridgeTelemetry("healthy", { persistentSuccess: true });
    return response.data ?? {};
  } catch (error) {
    updateBridgeTelemetry("degraded", {
      error: error instanceof Error ? error.message : String(error),
      incrementFallback: true,
    });
    console.warn(
      `[ninjaclawbot-bridge] Falling back to one-shot execution: ${
        error instanceof Error ? error.message : String(error)
      }`,
    );
    await shutdownBridge();
    return runNinjaClawbotActionOneShot(config, payload);
  }
}
