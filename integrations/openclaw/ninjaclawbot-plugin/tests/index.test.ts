import assert from "node:assert/strict";
import test from "node:test";

import registerNinjaClawbotPlugin from "../src/index.js";

test("plugin registers lifecycle hooks when api.on is available", () => {
  const hooks: string[] = [];
  const tools: string[] = [];
  let registeredServiceId = "";

  const api = {
    registerService(service: { id: string }) {
      registeredServiceId = service.id;
    },
    registerTool(tool: { name: string }) {
      tools.push(tool.name);
    },
    on(eventName: string, _handler: () => Promise<void>) {
      hooks.push(eventName);
    },
  };

  registerNinjaClawbotPlugin(api);

  assert.equal(registeredServiceId, "ninjaclawbot-bridge");
  assert.deepEqual(hooks, ["gateway_start", "message_received", "agent_end", "gateway_stop"]);
  assert.ok(tools.includes("ninjaclawbot_reply"));
  assert.ok(tools.includes("ninjaclawbot_stop_all"));
});
