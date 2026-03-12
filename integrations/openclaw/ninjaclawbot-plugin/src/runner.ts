import { spawn } from "node:child_process";

export const PLUGIN_ID = "ninjaclawbot";

export interface OpenClawPluginConfig {
  projectRoot: string;
  rootDir?: string;
  uvCommand?: string;
}

export interface NinjaClawbotPayload {
  action: string;
  parameters?: Record<string, unknown>;
  request_id?: string;
}

interface OpenClawPluginApiLike {
  config?: Record<string, unknown>;
}

function asObject(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
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

  return { projectRoot, rootDir, uvCommand };
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

export async function runNinjaClawbotAction(
  api: OpenClawPluginApiLike,
  payload: NinjaClawbotPayload,
) {
  const config = extractPluginConfig(api);
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
