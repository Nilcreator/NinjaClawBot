import assert from "node:assert/strict";
import test from "node:test";

import {
  alwaysOnEnabled,
  buildCommand,
  buildServeCommand,
  extractPluginConfig,
  parseBridgeOutput,
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
