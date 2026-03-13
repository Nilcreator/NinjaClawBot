import { noArgsSchema, moveServosSchema, nameSchema, replySchema } from "./schemas.js";
import {
  ensureBridge,
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

function registerLifecycleHook(api: any, eventName: string, handler: () => Promise<void>) {
  if (typeof api.on !== "function") {
    return;
  }

  api.on(eventName, async () => {
    try {
      await handler();
    } catch (error) {
      console.warn(
        `[ninjaclawbot-bridge] Lifecycle hook '${eventName}' failed: ${
          error instanceof Error ? error.message : String(error)
        }`,
      );
    }
  });
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

  registerLifecycleHook(api, "gateway_start", async () => {
    const startup = await runStartupSequence(api);
    if (startup === null) {
      await setPersistentPresenceMode(api, "idle", "gateway_start");
    }
  });
  registerLifecycleHook(api, "message_received", async () => {
    await setPersistentPresenceMode(api, "thinking", "message_received");
  });
  registerLifecycleHook(api, "agent_end", async () => {
    await setPersistentPresenceMode(api, "idle", "agent_end");
  });
  registerLifecycleHook(api, "gateway_stop", async () => {
    await runShutdownSequence(api, "gateway_stop");
  });

  registerOptionalTool(
    api,
    "ninjaclawbot_reply",
    "Render a conversational NinjaClawBot reply using the built-in emotion policy.",
    replySchema,
    "perform_reply",
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
