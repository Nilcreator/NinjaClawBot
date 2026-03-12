# ninjaclawbot

`ninjaclawbot` is the integrated robot-control layer for NinjaClawBot.

It sits above the standalone Pi 5 driver packages:

- `pi5buzzer`
- `pi5servo`
- `pi5disp`
- `pi5vl53l0x`

Its job is to provide:

- typed robot actions
- typed action results
- saved movement assets
- saved expression assets
- interactive `movement-tool` and `expression-tool`
- a controlled external hook for AI callers such as OpenClaw

## Recommended Install

Use the **project root** as the main install location:

```bash
cd /path/to/NinjaClawbot
uv sync --extra dev
```

Then run:

```bash
uv run ninjaclawbot --help
```

That root install also installs the sibling `pi5*` driver packages into the same environment.

## Standalone Package Install

If you want to work only on the integration layer by itself, you can still install it from this folder:

```bash
cd /path/to/NinjaClawbot/ninjaclawbot
uv sync --extra dev
```

This package still depends on the sibling `pi5*` folders through local editable `uv` sources.

## Runtime Files

When you run `ninjaclawbot` from the project root, it uses these root-level files:

- `servo.json`
- `buzzer.json`
- `display.json`
- `vl53l0x.json`
- `ninjaclawbot_data/movements/*.json`
- `ninjaclawbot_data/expressions/*.json`

## Key Commands

From the project root:

```bash
uv run ninjaclawbot health-check
uv run ninjaclawbot list-assets
uv run ninjaclawbot move-servos "F_12:C/13:C"
uv run ninjaclawbot movement-tool
uv run ninjaclawbot expression-tool
uv run ninjaclawbot perform-movement <name>
uv run ninjaclawbot perform-expression <name>
uv run ninjaclawbot run-action '{"action":"read_distance"}'
```

`expression-tool` now supports:

- listing saved expressions
- listing built-in expressions
- previewing built-in animated face/sound expressions
- creating saved expressions that reuse a built-in expression plus optional text or sound overrides
- starting and stopping the idle expression manually

`perform-expression <name>` now supports both:

- saved expression assets such as `hello`
- built-in expression names such as `idle`, `greeting`, or `confusing`

## Calibration Note

Before using integrated movement features, calibrate `pi5servo` first from the project root:

```bash
uv run pi5servo calib 12
uv run pi5servo calib 13
```

Or use:

```bash
uv run pi5servo servo-tool
```

That creates `servo.json`, which `ninjaclawbot` reuses directly.
