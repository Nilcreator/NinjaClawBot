import assert from "node:assert/strict";
import test from "node:test";

import registerNinjaClawbotPlugin from "../src/index.js";

test("plugin registers lifecycle hooks when api.registerHook is available", () => {
  const hooks: Array<{ event: string; name: string }> = [];
  const tools: Array<{ name: string; description?: string }> = [];
  const gatewayMethods: string[] = [];
  let registeredServiceId = "";

  const api = {
    registerService(service: { id: string }) {
      registeredServiceId = service.id;
    },
    registerTool(tool: { name: string; description?: string }) {
      tools.push(tool);
    },
    registerHook(
      eventName: string,
      _handler: () => Promise<void>,
      metadata: { name: string },
    ) {
      hooks.push({ event: eventName, name: metadata.name });
    },
    registerGatewayMethod(name: string) {
      gatewayMethods.push(name);
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
  assert.ok(tools.some((tool) => tool.name === "ninjaclawbot_reply"));
  assert.ok(
    tools.some(
      (tool) =>
        tool.name === "ninjaclawbot_reply" &&
        tool.description?.includes("normal visible text reply"),
    ),
  );
  assert.ok(tools.some((tool) => tool.name === "ninjaclawbot_diagnostics"));
  assert.ok(tools.some((tool) => tool.name === "ninjaclawbot_stop_all"));
  assert.deepEqual(gatewayMethods, ["ninjaclawbot.presence.set"]);
});

test("plugin falls back to api.on when registerHook is unavailable", () => {
  const hooks: string[] = [];

  const api = {
    registerService() {},
    registerTool() {},
    registerGatewayMethod() {},
    on(eventName: string, _handler: () => Promise<void>) {
      hooks.push(eventName);
    },
  };

  registerNinjaClawbotPlugin(api);

  assert.deepEqual(hooks, ["gateway_start", "message_received", "agent_end", "gateway_stop"]);
});

test("gateway presence method validates mode and responds with the bridge result", async () => {
  const methods = new Map<string, (request: any) => Promise<void>>();
  const workspace = "/tmp/ninjaclawbot-presence";

  const api = {
    config: {
      plugins: {
        entries: {
          ninjaclawbot: {
            config: {
              projectRoot: workspace,
              enablePersistentBridge: false,
            },
          },
        },
      },
    },
    registerService() {},
    registerTool() {},
    registerHook() {},
    registerGatewayMethod(name: string, handler: (request: any) => Promise<void>) {
      methods.set(name, handler);
    },
  };

  registerNinjaClawbotPlugin(api);

  const handler = methods.get("ninjaclawbot.presence.set");
  assert.ok(handler);

  const responseHolder: { current: { ok: boolean; payload?: unknown } | null } = {
    current: null,
  };
  await handler?.({
    params: { mode: "listening", reason: "pi5mic.listening" },
    respond(ok: boolean, payload?: unknown) {
      responseHolder.current = { ok, payload };
    },
  });

  const response = responseHolder.current;
  if (!response) {
    throw new Error("Expected gateway presence method to respond.");
  }
  assert.equal(response.ok, true);
  assert.deepEqual(response.payload, {
    mode: "listening",
    applied: false,
    result: null,
  });
});
