import assert from "node:assert/strict";
import test from "node:test";

import registerNinjaClawbotPlugin from "../src/index.js";

test("plugin registers lifecycle hooks when api.registerHook is available", () => {
  const hooks: Array<{ event: string; name: string }> = [];
  const tools: string[] = [];
  let registeredServiceId = "";

  const api = {
    registerService(service: { id: string }) {
      registeredServiceId = service.id;
    },
    registerTool(tool: { name: string }) {
      tools.push(tool.name);
    },
    registerHook(
      eventName: string,
      _handler: () => Promise<void>,
      metadata: { name: string },
    ) {
      hooks.push({ event: eventName, name: metadata.name });
    },
  };

  registerNinjaClawbotPlugin(api);

  assert.equal(registeredServiceId, "ninjaclawbot-bridge");
  assert.deepEqual(hooks, [
    { event: "gateway_start", name: "ninjaclawbot.gateway_start" },
    { event: "message_received", name: "ninjaclawbot.message_received" },
    { event: "agent_end", name: "ninjaclawbot.agent_end" },
    { event: "gateway_stop", name: "ninjaclawbot.gateway_stop" },
  ]);
  assert.ok(tools.includes("ninjaclawbot_reply"));
  assert.ok(tools.includes("ninjaclawbot_diagnostics"));
  assert.ok(tools.includes("ninjaclawbot_stop_all"));
});

test("plugin falls back to api.on when registerHook is unavailable", () => {
  const hooks: string[] = [];

  const api = {
    registerService() {},
    registerTool() {},
    on(eventName: string, _handler: () => Promise<void>) {
      hooks.push(eventName);
    },
  };

  registerNinjaClawbotPlugin(api);

  assert.deepEqual(hooks, ["gateway_start", "message_received", "agent_end", "gateway_stop"]);
});
