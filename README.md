# NinjaClawBot

NinjaClawBot is the Raspberry Pi 5 robot software stack for the NinjaRobot hardware platform.
It contains two layers:

- standalone Pi 5 driver libraries for buzzer, servo, display, and distance sensor control
- `ninjaclawbot`, a new integration layer that combines those drivers into reusable robot actions, interactive authoring tools, and a controlled external hook for AI agents such as OpenClaw

The project is designed so hardware can be tested manually by a human operator, then reused safely by an external AI assistant without exposing the raw driver packages directly.

## Project Specification

Current hardware/software scope:

- target platform: Raspberry Pi 5
- display: ST7789V SPI display through `pi5disp`
- servo control: native Pi GPIO PWM and optional DFR0566 / PCA9685 backends through `pi5servo`
- buzzer control: passive buzzer through `pi5buzzer`
- distance sensing: VL53L0X through `pi5vl53l0x`
- integration layer: `ninjaclawbot`
- planned external AI caller: OpenClaw, through the `ninjaclawbot` action boundary

Core design rules:

- each `pi5*` package remains usable as a standalone library
- `ninjaclawbot` owns integration, asset loading, action execution, and structured result reporting
- external AI agents should call `ninjaclawbot`, not the raw `pi5*` packages
- manual operator tools and external AI actions should use the same saved movement and expression assets

## Repository Structure

```text
NinjaClawbot/
├── pi5buzzer/              # Pi 5 passive buzzer driver
├── pi5servo/               # Pi 5 servo driver with native and external backends
├── pi5disp/                # Pi 5 ST7789V display driver
├── pi5vl53l0x/             # Pi 5 VL53L0X distance sensor driver
├── ninjaclawbot/           # High-level integration layer and interactive tools
├── NinjaRobotV5_bak/       # Legacy reference implementation and source audit target
├── developmentPlan.md      # migration and integration plan
├── DevelopmentGuide.md     # developer workflow and validation notes
└── DevelopmentLog.md       # dated implementation history
```

## Package Roles

- [pi5buzzer](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer)
  - standalone buzzer driver
  - note playback, emotion playback, queue-based sound worker, CLI tool
- [pi5servo](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo)
  - standalone servo driver
  - native GPIO endpoints, DFR0566 HAT PWM endpoints, optional PCA9685 backend, calibration and CLI tools
- [pi5disp](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp)
  - standalone display driver
  - text, image, demo, brightness, and display tool workflows
- [pi5vl53l0x](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x)
  - standalone distance-sensor driver
  - range reading, calibration, health checks, CLI commands
- [ninjaclawbot](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot)
  - integrated runtime and action executor
  - movement and expression asset storage
  - interactive `movement-tool` and `expression-tool`
  - JSON action entrypoint for future OpenClaw integration

## Installation

### 1. Install `uv`

`uv` is the Python package and virtual-environment manager used by this repository.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

After installation, restart the shell or run:

```bash
source "$HOME/.local/bin/env"
```

### 2. Prepare Raspberry Pi 5 system packages

These packages cover GPIO, SPI, I2C, and driver build support.

```bash
sudo apt update
sudo apt install -y python3-dev build-essential swig i2c-tools
```

### 3. Enable Raspberry Pi interfaces

Enable the interfaces required by the robot drivers:

```bash
sudo raspi-config
```

Enable:

- `I2C`
- `SPI`
- any PWM overlay needed for your servo setup

Reboot after changing interface settings.

### 4. Install the full NinjaClawBot stack

If you want the integrated robot environment, use the single-command install in
the [ninjaclawbot](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot)
folder:

```bash
cd ninjaclawbot
uv sync --extra dev
```

Expected result:

- `uv run python -c "import pi5buzzer, pi5servo, pi5disp, pi5vl53l0x"` works
- `uv run ninjaclawbot --help` works
- `uv run ninjaclawbot health-check` can see the installed driver packages

The `ninjaclawbot` manifest now pulls the sibling `pi5*` libraries in through
local editable `uv` sources, so the integrated environment and the standalone
driver folders use the same code.

### 5. Optional: install a standalone Pi 5 driver by itself

If you only want one driver package on its own, each driver still keeps its own
virtual environment and test flow.

For `pi5servo`, the standalone interactive `servo-tool` is the first validation
target. Quick Move now forces the requested PWM write, so return-to-center
commands like `F_gpio12:0/gpio13:0` should actively re-send the center pulse.
After calibration, the same `servo-tool` session should also rebuild its live
servo state automatically, so you should not need to exit and reopen the tool
before testing Quick Move.

```bash
cd pi5buzzer
uv sync --extra pi --extra dev
cd ../pi5servo
uv sync --extra pi --extra dev
cd ../pi5disp
uv sync --extra pi --extra dev
cd ../pi5vl53l0x
uv sync --extra pi --extra dev
cd ..
```

## Testing Core NinjaClawBot Functions

Run the following commands from [ninjaclawbot](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot).

### Safe smoke tests

Check the package and saved asset directories:

```bash
uv run ninjaclawbot --help
uv run ninjaclawbot list-assets
uv run ninjaclawbot health-check
```

Expected result:

- CLI help is shown
- the asset list returns an empty or existing list
- `health-check` returns a JSON result with driver availability details

### Create and test a movement asset

Start the interactive movement tool:

```bash
uv run ninjaclawbot movement-tool
```

Suggested first test:

1. Choose `2. Create movement`
2. Name it `wave`
3. Enter a movement command such as `M_gpio12:20/hat_pwm1:C`
4. Save the movement
5. Exit the tool

Then run the saved movement:

```bash
uv run ninjaclawbot perform-movement wave
```

Expected result:

- the movement asset is saved under `ninjaclawbot_data/movements`
- the executor returns a JSON result
- the configured servos move only if the related hardware is connected and configured

### Create and test an expression asset

Start the interactive expression tool:

```bash
uv run ninjaclawbot expression-tool
```

Suggested first test:

1. Choose `2. Create expression`
2. Name it `happy`
3. Enter display text such as `Hello`
4. Set a sound emotion such as `happy`
5. Save the expression
6. Exit the tool

Then run the saved expression:

```bash
uv run ninjaclawbot perform-expression happy
```

Expected result:

- the expression asset is saved under `ninjaclawbot_data/expressions`
- the executor returns a JSON result
- the display and buzzer react if the related hardware is connected and configured

### Direct hardware-oriented tests

Move servos directly using the integrated endpoint-aware command syntax:

```bash
uv run ninjaclawbot move-servos "F_gpio12:C/hat_pwm1:15"
```

Read distance through the integrated JSON action path:

```bash
uv run ninjaclawbot run-action '{"action":"read_distance"}'
```

Expected result:

- servo movements return structured action results
- distance reads return structured sensor data in JSON form

## Validation Notes

- `ninjaclawbot` does not replace the standalone driver CLIs. It sits above them.
- For DFR0566 PWM control, use external servo power and a common ground.
- For movement tests, start with one servo and clear mechanical space before running named movements.
- For display and sensor rewiring, power the Raspberry Pi down first.

## Development References

- [developmentPlan.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/developmentPlan.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentLog.md)
- [.agents/skills/ninjaclawbot-implementation/SKILL.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/.agents/skills/ninjaclawbot-implementation/SKILL.md)
