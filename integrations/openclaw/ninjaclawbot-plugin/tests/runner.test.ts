import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import {
  alwaysOnEnabled,
  buildCommand,
  buildServeCommand,
  extractPluginConfig,
  inspectDeploymentHealth,
  parseBridgeOutput,
  readBridgeTelemetry,
  readDisplayConfigSummary,
  runNinjaClawbotAction,
  runDiagnostics,
} from "../src/runner.js";

test("extractPluginConfig reads the plugin entry config", () => {
  const config = extractPluginConfig({
    config: {
      plugins: {
        entries: {
          ninjaclawbot: {
            config: {
              projectRoot: "/robot",
              rootDir: "/robot",
              uvCommand: "uv",
            },
          },
        },
      },
    },
  });

  assert.deepEqual(config, {
    projectRoot: "/robot",
    rootDir: "/robot",
    uvCommand: "uv",
    enablePersistentBridge: true,
    bridgeStartTimeoutMs: 10_000,
    bridgeRequestTimeoutMs: 15_000,
    bridgeShutdownTimeoutMs: 5_000,
    enableAlwaysOn: true,
    enableStartupGreeting: true,
    enableAutoThinking: true,
    enableShutdownSequence: true,
  });
});

test("extractPluginConfig supports persistent bridge overrides", () => {
  const config = extractPluginConfig({
    config: {
      plugins: {
        entries: {
          ninjaclawbot: {
            config: {
              projectRoot: "/robot",
              enablePersistentBridge: false,
              bridgeStartTimeoutMs: 1000,
              bridgeRequestTimeoutMs: 2000,
              bridgeShutdownTimeoutMs: 3000,
              enableAlwaysOn: false,
              enableStartupGreeting: false,
              enableAutoThinking: false,
              enableShutdownSequence: false,
            },
          },
        },
      },
    },
  });

  assert.equal(config.enablePersistentBridge, false);
  assert.equal(config.bridgeStartTimeoutMs, 1000);
  assert.equal(config.bridgeRequestTimeoutMs, 2000);
  assert.equal(config.bridgeShutdownTimeoutMs, 3000);
  assert.equal(config.enableAlwaysOn, false);
  assert.equal(config.enableStartupGreeting, false);
  assert.equal(config.enableAutoThinking, false);
  assert.equal(config.enableShutdownSequence, false);
});

test("buildCommand targets the project-root OpenClaw bridge", () => {
  const command = buildCommand(
    {
      projectRoot: "/robot",
      rootDir: "/robot",
      uvCommand: "uv",
    },
    {
      action: "perform_reply",
      parameters: { text: "Hello", reply_state: "greeting" },
    },
  );

  assert.equal(command.command, "uv");
  assert.equal(command.cwd, "/robot");
  assert.deepEqual(command.args.slice(0, 6), [
    "run",
    "--project",
    "/robot",
    "ninjaclawbot",
    "--root-dir",
    "/robot",
  ]);
  assert.equal(command.args[6], "openclaw-action");
});

test("buildServeCommand targets the persistent bridge entrypoint", () => {
  const command = buildServeCommand({
    projectRoot: "/robot",
    rootDir: "/robot",
    uvCommand: "uv",
    enablePersistentBridge: true,
    bridgeStartTimeoutMs: 10_000,
    bridgeRequestTimeoutMs: 15_000,
    bridgeShutdownTimeoutMs: 5_000,
    enableAlwaysOn: true,
    enableStartupGreeting: true,
    enableAutoThinking: true,
    enableShutdownSequence: true,
  });

  assert.equal(command.command, "uv");
  assert.equal(command.cwd, "/robot");
  assert.deepEqual(command.args.slice(0, 6), [
    "run",
    "--project",
    "/robot",
    "ninjaclawbot",
    "--root-dir",
    "/robot",
  ]);
  assert.equal(command.args[6], "openclaw-serve");
});

test("alwaysOnEnabled requires the persistent bridge and Always On config", () => {
  assert.equal(
    alwaysOnEnabled({
      projectRoot: "/robot",
      enablePersistentBridge: true,
      enableAlwaysOn: true,
    }),
    true,
  );
  assert.equal(
    alwaysOnEnabled({
      projectRoot: "/robot",
      enablePersistentBridge: false,
      enableAlwaysOn: true,
    }),
    false,
  );
});

test("parseBridgeOutput can recover JSON from noisy stdout", () => {
  const parsed = parseBridgeOutput(`warning
{
  "status": "success",
  "action": "health_check"
}`);

  assert.equal(parsed.status, "success");
  assert.equal(parsed.action, "health_check");
});

test("runNinjaClawbotAction marks telemetry disabled when persistent bridge is off", async () => {
  const api = {
    config: {
      plugins: {
        entries: {
          ninjaclawbot: {
            config: {
              projectRoot: "/robot",
              enablePersistentBridge: false,
            },
          },
        },
      },
    },
  };

  try {
    await runNinjaClawbotAction(api, { action: "health_check" });
  } catch {
    // One-shot execution will fail in the test environment because /robot does not exist.
  }

  assert.equal(readBridgeTelemetry().status, "disabled");
});

test("readDisplayConfigSummary prefers the root display config when present", () => {
  const baseDir = fs.mkdtempSync(path.join(os.tmpdir(), "ninjaclawbot-display-"));
  const rootDir = path.join(baseDir, "robot");
  const projectRoot = path.join(baseDir, "project");
  fs.mkdirSync(rootDir, { recursive: true });
  fs.mkdirSync(path.join(projectRoot, "pi5disp"), { recursive: true });
  fs.writeFileSync(path.join(rootDir, "display.json"), "{}\n", "utf-8");
  fs.writeFileSync(path.join(projectRoot, "pi5disp", "display.json"), "{}\n", "utf-8");

  const summary = readDisplayConfigSummary({
    projectRoot,
    rootDir,
    enablePersistentBridge: true,
  });

  assert.equal(summary.usingRootConfig, true);
  assert.equal(summary.configPath, path.join(rootDir, "display.json"));
  assert.equal(summary.configExists, true);
});

test("inspectDeploymentHealth reports validated deployment readiness", () => {
  const workspace = fs.mkdtempSync(path.join(os.tmpdir(), "ninjaclawbot-workspace-"));
  fs.writeFileSync(path.join(workspace, "BOOT.md"), "# startup\n", "utf-8");
  fs.writeFileSync(path.join(workspace, "AGENTS.md"), "# policy\n", "utf-8");

  const deployment = inspectDeploymentHealth({
    config: {
      hooks: {
        internal: {
          enabled: true,
          entries: {
            "boot-md": { enabled: true },
          },
        },
      },
      skills: {
        entries: {
          ninjaclawbot_control: { enabled: true },
        },
      },
      agents: {
        defaults: {
          workspace,
        },
        list: [
          {
            id: "main",
            tools: {
              allow: ["ninjaclawbot"],
            },
          },
        ],
      },
      plugins: {
        entries: {
          ninjaclawbot: {
            config: {
              projectRoot: "/robot",
              rootDir: "/robot",
              uvCommand: "uv",
              enablePersistentBridge: true,
            },
          },
        },
      },
    },
  });

  assert.equal(deployment.status, "ready");
  assert.equal(deployment.bootMdPresent, true);
  assert.equal(deployment.agentsMdPresent, true);
  assert.equal(deployment.replyToolOptedIn, true);
  assert.equal(deployment.minimalPluginConfig, true);
});

test("inspectDeploymentHealth flags missing reply allowlist as misconfigured", () => {
  const workspace = fs.mkdtempSync(path.join(os.tmpdir(), "ninjaclawbot-workspace-"));

  const deployment = inspectDeploymentHealth({
    config: {
      hooks: {
        internal: {
          enabled: true,
          entries: {
            "boot-md": { enabled: true },
          },
        },
      },
      skills: {
        entries: {
          ninjaclawbot_control: { enabled: true },
        },
      },
      agents: {
        defaults: {
          workspace,
        },
        list: [
          {
            id: "main",
            tools: {
              allow: [],
            },
          },
        ],
      },
      plugins: {
        entries: {
          ninjaclawbot: {
            config: {
              projectRoot: "/robot",
              enablePersistentBridge: true,
            },
          },
        },
      },
    },
  });

  assert.equal(deployment.status, "misconfigured");
  assert.ok(
    deployment.issues.some((issue) => issue.includes("reply tools")),
  );
});

test("runDiagnostics reports one-shot fallback when persistent bridge is disabled", async () => {
  const workspace = fs.mkdtempSync(path.join(os.tmpdir(), "ninjaclawbot-workspace-"));
  fs.writeFileSync(path.join(workspace, "BOOT.md"), "# startup\n", "utf-8");
  fs.writeFileSync(path.join(workspace, "AGENTS.md"), "# policy\n", "utf-8");

  const diagnostics = await runDiagnostics({
    config: {
      hooks: {
        internal: {
          enabled: true,
          entries: {
            "boot-md": { enabled: true },
          },
        },
      },
      skills: {
        entries: {
          ninjaclawbot_control: { enabled: true },
        },
      },
      agents: {
        defaults: {
          workspace,
        },
        list: [
          {
            id: "main",
            tools: {
              allow: ["ninjaclawbot"],
            },
          },
        ],
      },
      plugins: {
        entries: {
          ninjaclawbot: {
            config: {
              projectRoot: workspace,
              rootDir: workspace,
              enablePersistentBridge: false,
            },
          },
        },
      },
    },
  });

  assert.equal(diagnostics.bridge.status, "disabled");
  assert.equal(diagnostics.summary.state, "one_shot_fallback");
  assert.equal(diagnostics.deployment.status, "warning");
  assert.ok(
    diagnostics.recoveryHints.some((hint) => hint.includes("persistent bridge")),
  );
});
