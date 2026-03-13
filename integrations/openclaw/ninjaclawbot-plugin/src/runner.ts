import { randomUUID } from "node:crypto";
import { ChildProcessWithoutNullStreams, spawn } from "node:child_process";
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

let activeBridge: BridgeClient | null = null;

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

function configSignature(config: OpenClawPluginConfig): string {
  return JSON.stringify({
    projectRoot: config.projectRoot,
    rootDir: config.rootDir,
    uvCommand: config.uvCommand,
    enablePersistentBridge: config.enablePersistentBridge,
    bridgeStartTimeoutMs: config.bridgeStartTimeoutMs,
    bridgeRequestTimeoutMs: config.bridgeRequestTimeoutMs,
    bridgeShutdownTimeoutMs: config.bridgeShutdownTimeoutMs,
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

export async function ensureBridge(api: OpenClawPluginApiLike): Promise<void> {
  const config = extractPluginConfig(api);
  if (!config.enablePersistentBridge) {
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
  } catch (error) {
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

  const shutdownTimeout = client.config.bridgeShutdownTimeoutMs ?? DEFAULT_BRIDGE_SHUTDOWN_TIMEOUT_MS;
  try {
    await sendBridgeRequest(client, { type: "shutdown" }, shutdownTimeout);
  } catch {
    // Fall through to hard termination below.
  }

  if (!client.exited) {
    client.child.kill("SIGTERM");
  }
}

export async function runNinjaClawbotAction(
  api: OpenClawPluginApiLike,
  payload: NinjaClawbotPayload,
) {
  const config = extractPluginConfig(api);
  if (!config.enablePersistentBridge) {
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
    return response.data ?? {};
  } catch (error) {
    console.warn(
      `[ninjaclawbot-bridge] Falling back to one-shot execution: ${
        error instanceof Error ? error.message : String(error)
      }`,
    );
    await shutdownBridge();
    return runNinjaClawbotActionOneShot(config, payload);
  }
}
