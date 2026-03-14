import { noArgsSchema, moveServosSchema, nameSchema, replySchema } from "./schemas.js";
import {
  ensureBridge,
  runDiagnostics,
  runNinjaClawbotAction,
  runShutdownSequence,
  runStartupSequence,
  setPersistentPresenceMode,
  shutdownBridge,
} from "./runner.js";

type ToolParams = Record<string, unknown>;

function jsonContent(payload: unknown) {
  return { content: [{ type: "text", text: JSON.stringify(payload, null, 2) }] };
}

function replyToolContent(payload: unknown) {
  return jsonContent({
    ...((payload && typeof payload === "object" ? payload : {}) as Record<string, unknown>),
    user_reply_required: true,
    next_step:
      "After this tool call, continue by sending the normal visible text reply to the user in chat.",
  });
}

function registerOptionalTool(
  api: any,
  name: string,
  description: string,
  parameters: Record<string, unknown>,
  action: string,
  mapParams: (params: ToolParams) => Record<string, unknown> = (params) => params,
) {
  api.registerTool(
    {
      name,
      description,
      parameters,
      async execute(_id: string, params: ToolParams) {
        const result = await runNinjaClawbotAction(api, {
          action,
          parameters: mapParams(params),
        });
        return jsonContent(result);
      },
    },
    { optional: true },
  );
}

function wrapLifecycleHandler(eventName: string, handler: () => Promise<void>) {
  return async () => {
    try {
      await handler();
    } catch (error) {
      console.warn(
        `[ninjaclawbot-bridge] Lifecycle hook '${eventName}' failed: ${
          error instanceof Error ? error.message : String(error)
        }`,
      );
    }
  };
}

function registerLifecycleHook(
  api: any,
  eventName: string,
  description: string,
  handler: () => Promise<void>,
) {
  const wrapped = wrapLifecycleHandler(eventName, handler);

  if (typeof api.registerHook === "function") {
    api.registerHook(eventName, wrapped, {
      name: `ninjaclawbot.${eventName}`,
      description,
    });
    return;
  }

  if (typeof api.on === "function") {
    api.on(eventName, wrapped);
  }
}

export default function registerNinjaClawbotPlugin(api: any) {
  if (typeof api.registerService === "function") {
    api.registerService({
      id: "ninjaclawbot-bridge",
      name: "NinjaClawBot Bridge",
      async start() {
        try {
          await ensureBridge(api);
        } catch (error) {
          console.warn(
            `[ninjaclawbot-bridge] Persistent bridge startup failed, one-shot fallback remains available: ${
              error instanceof Error ? error.message : String(error)
            }`,
          );
        }
      },
      async stop() {
        await runShutdownSequence(api, "service_stop");
        await shutdownBridge();
      },
    });
  }

  registerLifecycleHook(
    api,
    "gateway_start",
    "Run the NinjaClawBot startup greeting and enter idle on gateway startup.",
    async () => {
      const startup = await runStartupSequence(api);
      if (startup === null) {
        await setPersistentPresenceMode(api, "idle", "gateway_start");
      }
    },
  );
  registerLifecycleHook(
    api,
    "message_received",
    "Switch NinjaClawBot into persistent thinking when a user message arrives.",
    async () => {
      await setPersistentPresenceMode(api, "thinking", "message_received");
    },
  );
  registerLifecycleHook(
    api,
    "agent_end",
    "Return NinjaClawBot to idle after an agent run completes.",
    async () => {
      await setPersistentPresenceMode(api, "idle", "agent_end");
    },
  );
  registerLifecycleHook(
    api,
    "gateway_stop",
    "Run the NinjaClawBot sleepy shutdown sequence on gateway stop.",
    async () => {
      await runShutdownSequence(api, "gateway_stop");
    },
  );

  api.registerTool(
    {
      name: "ninjaclawbot_reply",
      description:
        "Animate NinjaClawBot for a conversational reply. After this tool call, continue by sending the normal visible text reply to the user.",
      parameters: replySchema,
      async execute(_id: string, params: ToolParams) {
        const result = await runNinjaClawbotAction(api, {
          action: "perform_reply",
          parameters: params,
        });
        return replyToolContent(result);
      },
    },
    { optional: true },
  );
  registerOptionalTool(
    api,
    "ninjaclawbot_perform_expression",
    "Run a saved NinjaClawBot expression asset or built-in expression.",
    nameSchema,
    "perform_expression",
  );
  registerOptionalTool(
    api,
    "ninjaclawbot_perform_movement",
    "Run a saved NinjaClawBot movement asset.",
    nameSchema,
    "perform_movement",
  );
  registerOptionalTool(
    api,
    "ninjaclawbot_move_servos",
    "Move servos directly using structured endpoint targets.",
    moveServosSchema,
    "move_servos",
  );
  registerOptionalTool(
    api,
    "ninjaclawbot_read_distance",
    "Read the current distance value from the VL53L0X sensor.",
    noArgsSchema,
    "read_distance",
  );
  registerOptionalTool(
    api,
    "ninjaclawbot_health",
    "Run a full NinjaClawBot hardware health check.",
    noArgsSchema,
    "health_check",
  );
  registerOptionalTool(
    api,
    "ninjaclawbot_capabilities",
    "List supported NinjaClawBot actions, reply states, and available assets.",
    noArgsSchema,
    "list_capabilities",
  );
  registerOptionalTool(
    api,
    "ninjaclawbot_set_idle",
    "Start the persistent idle face on NinjaClawBot.",
    noArgsSchema,
    "set_idle",
  );
  api.registerTool(
    {
      name: "ninjaclawbot_diagnostics",
      description:
        "Inspect NinjaClawBot bridge health, deployment readiness, and recovery hints.",
      parameters: noArgsSchema,
      async execute() {
        const result = await runDiagnostics(api);
        return jsonContent(result);
      },
    },
    { optional: true },
  );
  registerOptionalTool(
    api,
    "ninjaclawbot_stop",
    "Stop the active NinjaClawBot expression loop.",
    noArgsSchema,
    "stop_expression",
  );

  api.registerTool(
    {
      name: "ninjaclawbot_stop_all",
      description: "Stop all active NinjaClawBot outputs, including expressions and servo motion.",
      parameters: noArgsSchema,
      async execute() {
        const result = await runNinjaClawbotAction(api, {
          action: "stop_all",
          parameters: {},
        });
        return jsonContent(result);
      },
    },
    { optional: true },
  );
}
