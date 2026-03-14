# NinjaClawBot Enhancement Plan

Updated: 2026-03-14
Branch baseline: `clawbotV1_beta_01`

This document is the concise implementation record for the current enhancement work.

- Stage 1 is kept as a completed reference.
- Stage 2 tracks the current OpenClaw-facing robot presence work.
- The validated deployment model is now hybrid:
  - plugin-managed persistent bridge and shutdown
  - OpenClaw `boot-md` plus workspace `BOOT.md` for startup greeting
  - workspace `AGENTS.md` plus enabled skill and tool allowlist for reply-expression behavior

## Stage 1: Completed Foundation

Status: Done

### Objective

Establish the modern `ninjaclawbot` runtime, expression system, and first approved OpenClaw integration boundary on top of the Pi 5 driver libraries.

### Key Implementation Points

- built the expression and reply-state model
- added animated face playback and sound-expression orchestration
- added persistent `idle`
- added `expression-tool`
- added the first official OpenClaw plugin and skill wrapper

### Libraries Affected

- `ninjaclawbot`
- `pi5disp`
- `pi5buzzer`
- `pi5servo`
- `pi5vl53l0x`
- `integrations/openclaw/ninjaclawbot-plugin`

## Stage 2: Always On OpenClaw Integration

Status: In Progress

### Objective

Make NinjaClawBot behave like a continuously present robot companion during OpenClaw gateway use, while keeping the Python service core reusable for a future standalone host.

### Current Validated Build Shape

- minimal supported plugin config:
  - `projectRoot`
  - `rootDir`
  - `uvCommand`
  - `enablePersistentBridge`
  - bridge timeout settings
- startup greeting is validated through `boot-md` and workspace `BOOT.md`
- reply-expression behavior is validated through:
  - tool allowlist
  - enabled `ninjaclawbot_control` skill
  - workspace `AGENTS.md`
- shutdown sleepy and display power-down are validated through the plugin-managed persistent bridge

### Stage 2 Architecture

```text
OpenClaw gateway
  -> NinjaClawBot plugin background service
  -> persistent Python bridge
  -> lifecycle/service core
  -> NinjaClawbotRuntime / ActionExecutor / ExpressionPlayer
  -> pi5disp / pi5buzzer / pi5servo / pi5vl53l0x
```

### Phase 2.1: Persistent Bridge Service

Status: Done

#### Objective

Replace per-call robot process startup with one persistent Python bridge owned by the OpenClaw plugin.

#### Key Implementation Points

- added long-lived `openclaw-serve` bridge support
- kept the one-shot action path as fallback
- moved bridge lifecycle ownership into the plugin service layer
- kept the Python bridge reusable for future standalone deployment

#### Libraries Affected

- `ninjaclawbot`
- `integrations/openclaw/ninjaclawbot-plugin`

### Phase 2.2: Presence Modes And Shutdown Sequence

Status: Done

#### Objective

Add explicit robot presence states and a controlled shutdown sequence instead of one-shot reaction-only behavior.

#### Key Implementation Points

- added persistent presence-mode support for lifecycle control
- added startup, `thinking`, and `idle` presence transitions in the Python service core
- added `sleepy -> display power-down -> cleanup` shutdown sequencing
- kept reply emotion explicit through `reply_state`

#### Libraries Affected

- `ninjaclawbot`
- `pi5disp`
- `pi5buzzer`

### Phase 2.3: Hybrid OpenClaw Lifecycle Integration

Status: Done in validated hybrid deployment form

#### Objective

Wire the persistent robot service into OpenClaw lifecycle behavior without forcing a plugin-only architecture.

#### Key Implementation Points

- plugin-managed bridge start and stop are active
- startup greeting is delivered through OpenClaw `boot-md` and workspace `BOOT.md`
- reply-expression reliability is delivered through:
  - `ninjaclawbot_reply`
  - enabled `ninjaclawbot_control` skill
  - workspace `AGENTS.md`
  - tool allowlist
- shutdown sleepy is driven by the persistent bridge stop path

#### Libraries Affected

- `integrations/openclaw/ninjaclawbot-plugin`
- `ninjaclawbot`
- OpenClaw workspace files and config

### Phase 2.4: Arbitration, Dedupe, Degraded Mode, And Config Hardening

Status: Initial hardening slice implemented and Pi-validated

#### Objective

Make lifecycle behavior deterministic under duplicate, overlapping, stale, or partially degraded events, and align the code with the validated Raspberry Pi deployment.

#### Key Implementation Points

- added service-side suppression and dedupe for:
  - duplicate startup after startup already completed
  - repeated `message_received -> thinking`
  - stale or unnecessary `agent_end -> idle`
- added internal status fields for:
  - activity epochs
  - suppressed lifecycle counts
  - last transition source and reason
  - last explicit action
- added plugin-side bridge telemetry for:
  - `healthy`
  - `degraded`
  - `disabled`
- hardened display config loading so `ninjaclawbot` honors the root `display.json` path and falls back safely when needed
- removed tracked Python cache artifacts and added ignore rules so Pi `git pull` no longer breaks on generated files

#### Libraries Affected

- `ninjaclawbot`
- `integrations/openclaw/ninjaclawbot-plugin`
- `pi5disp`
- repository root ignore/config files

### Phase 2.5: Validation, Observability, And Release Gate

Status: Planned next phase

#### Objective

Make the current build diagnosable by non-developers, expose the real deployment state safely, and turn the validated Raspberry Pi flow into a repeatable release gate.

#### Why This Phase Is Necessary

- the code already tracks useful internal state, but operators still have no direct diagnostics tool
- recent bugs required manual log inspection and config spelunking to understand:
  - bad `uvCommand`
  - missing workspace files
  - missing hook behavior
  - reply-tool selection failures
- the current deployment is hybrid, so readiness depends on more than plugin code alone

#### Key Implementation Points

1. Operator-facing diagnostics
   - add a secret-safe tool such as `ninjaclawbot_diagnostics`
   - expose:
     - bridge status
     - degraded or fallback mode
     - current presence mode
     - startup completion
     - last lifecycle event
     - last error
     - request counters
     - suppression counters

2. Deployment health reporting
   - report whether the validated deployment prerequisites are present:
     - persistent bridge enabled
     - workspace path available
     - `BOOT.md` present
     - `AGENTS.md` present
     - required tools allowlisted
     - `ninjaclawbot_control` skill enabled
   - treat optional lifecycle plugin flags as compatibility overrides, not the primary supported setup

3. Release gate
   - define the release-tested path as:
     - startup greeting
     - reply expression
     - idle recovery
     - sleepy shutdown
     - degraded fallback visibility
   - add a concise regression and Pi validation checklist
   - keep repository hygiene checks in the release gate

4. Recovery and rollback guidance
   - provide a direct path for diagnosing:
     - bridge degradation
     - missing workspace guidance
     - text-only reply fallback
     - one-shot rollback when needed

#### Libraries Affected

- `ninjaclawbot`
- `integrations/openclaw/ninjaclawbot-plugin`
- OpenClaw workspace and deployment documentation

#### Planned Validation Gate

- `npm run typecheck`
- `npm test`
- `uv run --extra dev python -m compileall src tests`
- `uv run --extra dev ruff check src tests`
- `uv run --extra dev ruff format --check src tests`
- `uv run --extra dev pytest -q tests -c pyproject.toml`
- Raspberry Pi validation for:
  - startup
  - thinking
  - reply expression
  - shutdown
  - degraded-mode diagnostics
  - recovery and rollback

## Current Recommended Next Step

Implement Phase 2.5 in small slices:

1. expose operator-facing diagnostics first
2. add deployment health checks that match the validated OpenClaw setup
3. finish the release gate and Pi validation pack

That keeps the current working robot behavior intact while making the deployment safer to update and easier to support.
