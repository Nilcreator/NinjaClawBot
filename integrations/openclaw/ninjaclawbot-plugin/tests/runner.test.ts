import assert from "node:assert/strict";
import test from "node:test";

import { buildCommand, extractPluginConfig, parseBridgeOutput } from "../src/runner.js";

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
  });
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

test("parseBridgeOutput can recover JSON from noisy stdout", () => {
  const parsed = parseBridgeOutput(`warning
{
  "status": "success",
  "action": "health_check"
}`);

  assert.equal(parsed.status, "success");
  assert.equal(parsed.action, "health_check");
});
