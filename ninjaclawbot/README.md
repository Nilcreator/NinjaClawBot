# ninjaclawbot

`ninjaclawbot` is the integrated robot-control layer for NinjaClawBot. It sits above
the standalone Pi 5 driver libraries and provides typed actions, typed execution
results, and interactive tools for robot movements and expressions.

## Installation

`ninjaclawbot` now installs the sibling local Pi 5 driver packages automatically.
Run this from the `ninjaclawbot` folder:

```bash
uv sync --extra dev
```

That one command installs:

- `pi5buzzer[pi]`
- `pi5servo[pi]`
- `pi5disp[pi]`
- `pi5vl53l0x[pi]`
- `ninjaclawbot`

through local editable `uv` sources. The standalone driver folders still work the
same on their own. This only removes the extra manual install step when you want
the full integrated NinjaClawBot environment.
