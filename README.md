# NinjaClawBot

NinjaClawBot is the Raspberry Pi 5 software stack for the NinjaRobot hardware platform.

It has two layers:

- standalone Pi 5 driver libraries for each hardware device
- `ninjaclawbot`, the high-level integration layer that combines those drivers into reusable robot actions, saved movements, saved expressions, and a controlled hook for external AI agents such as OpenClaw

The project is now **root-first**:

- install from the project root
- run all commands from the project root
- keep shared config files such as `servo.json`, `buzzer.json`, `display.json`, and `vl53l0x.json` at the project root

## Project Specification

Current hardware and software scope:

- target board: Raspberry Pi 5
- buzzer: passive buzzer through `pi5buzzer`
- servos: direct Pi PWM, DFR0566 HAT PWM, and optional PCA9685 through `pi5servo`
- display: ST7789V SPI display through `pi5disp`
- distance sensor: VL53L0X through `pi5vl53l0x`
- integration layer: `ninjaclawbot`
- planned external AI caller: OpenClaw through the `ninjaclawbot` action boundary

Core design rules:

- each `pi5*` package must keep working as a standalone package
- `ninjaclawbot` must call the real `pi5*` package APIs instead of duplicating driver logic
- external AI assistants should call `ninjaclawbot`, not raw `pi5*` drivers
- manual users and AI agents should reuse the same saved movement and expression assets

## File Structure

```text
NinjaClawbot/
├── pyproject.toml              # root install entry for the whole project
├── uv.lock                     # root dependency lock file
├── src/
│   └── ninjaclawbot_workspace/ # minimal root workspace package
├── pi5buzzer/                  # standalone passive buzzer driver
├── pi5servo/                   # standalone servo driver
├── pi5disp/                    # standalone ST7789V display driver
├── pi5vl53l0x/                 # standalone VL53L0X driver
├── ninjaclawbot/               # integration layer, executor, and interactive tools
├── NinjaRobotV5_bak/           # legacy reference implementation
├── developmentPlan.md          # migration and integration plan
├── DevelopmentGuide.md         # developer workflow and validation reference
└── DevelopmentLog.md           # dated implementation history
```

Important runtime files created at the project root:

- `servo.json`
- `buzzer.json`
- `display.json`
- `vl53l0x.json`
- `ninjaclawbot_data/movements/*.json`
- `ninjaclawbot_data/expressions/*.json`

## Package Roles

- `pi5buzzer`
  - plays tones, notes, songs, and emotion sounds
  - includes `buzzer-tool`
- `pi5servo`
  - controls servos through native GPIO and supported external PWM controllers
  - includes calibration and `servo-tool`
- `pi5disp`
  - drives the ST7789V display
  - includes text, image, demo, and `display-tool`
- `pi5vl53l0x`
  - reads distance and supports offset calibration
  - includes `sensor-tool`
- `ninjaclawbot`
  - runs integrated robot actions
  - stores saved movements and expressions
  - includes a first-class facial/sound expression engine, `movement-tool`, `expression-tool`, `health-check`, and JSON `run-action`

## Installation

### 1. Install `uv`

`uv` is the Python package manager and virtual-environment tool used by this project.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then restart the shell, or run:

```bash
source "$HOME/.local/bin/env"
```

### 2. Install Raspberry Pi system packages

These packages support GPIO, SPI, I2C, and Python extension builds:

```bash
sudo apt update
sudo apt install -y python3-dev build-essential swig i2c-tools
```

### 3. Enable Raspberry Pi interfaces

Run:

```bash
sudo raspi-config
```

Enable:

- `I2C`
- `SPI`
- the PWM overlay needed for your servo setup

Then reboot the Raspberry Pi.

### 4. Install the whole project from the project root

From the **project root**, run:

```bash
uv sync --extra dev
```

This single command installs:

- `ninjaclawbot`
- `pi5buzzer[pi]`
- `pi5servo[pi]`
- `pi5disp[pi]`
- `pi5vl53l0x[pi]`
- development tools such as `pytest` and `ruff`

You do **not** need to install each `pi5*` package separately when using the full NinjaClawBot project.

### 5. Verify the root environment

Still from the project root, run:

```bash
uv run python -c "import ninjaclawbot, pi5buzzer, pi5servo, pi5disp, pi5vl53l0x; print('imports-ok')"
uv run ninjaclawbot --help
uv run pi5servo --help
uv run pi5buzzer --help
uv run pi5disp --help
uv run pi5vl53l0x --help
```

Expected result:

- the import check prints `imports-ok`
- all five CLI help commands work from the project root

## Calibration And Setup Before Using `ninjaclawbot`

Some drivers can work with defaults, but servo control should be calibrated before integrated robot use.

### `pi5servo` calibration: required for reliable motion

Recommended first step:

```bash
uv run pi5servo status --no-probe --pins 12,13
uv run pi5servo calib 12
uv run pi5servo calib 13
```

Or use the interactive tool:

```bash
uv run pi5servo servo-tool
```

Expected result:

- `servo.json` is created at the project root
- calibrated endpoints are saved there
- later `ninjaclawbot` movement commands reuse that same root-level `servo.json`

If you use the DFR0566 HAT:

- physical HAT `PWM0` is `hat_pwm1`
- physical HAT `PWM1` is `hat_pwm2`
- physical HAT `PWM2` is `hat_pwm3`
- physical HAT `PWM3` is `hat_pwm4`

For DFR0566 PWM servos, use **external servo power** and a common ground with the Raspberry Pi.

### `pi5buzzer` setup: recommended

If you want a custom GPIO pin or want to create the root config file explicitly:

```bash
uv run pi5buzzer init 17
```

Expected result:

- `buzzer.json` is created at the project root
- a short test beep is played when the hardware is available

### `pi5disp` setup: recommended

Create or refresh the root display config:

```bash
uv run pi5disp init --defaults
```

Expected result:

- `display.json` is created at the project root
- the default ST7789V pin and rotation settings are saved

### `pi5vl53l0x` setup: optional but recommended

Check the sensor and optionally calibrate the offset:

```bash
sudo i2cdetect -y 1
uv run pi5vl53l0x test
uv run pi5vl53l0x calibrate --distance 200 --count 10
```

Expected result:

- `i2cdetect` shows `0x29`
- the test command returns stable distance readings
- `vl53l0x.json` is saved at the project root if you run calibration

## Testing From The Project Root

### Safe smoke tests

```bash
uv run ninjaclawbot health-check
uv run ninjaclawbot list-assets
```

Expected result:

- `health-check` returns structured JSON
- unavailable hardware is reported clearly instead of crashing the program
- `list-assets` returns the saved movement and expression names
- one-shot `ninjaclawbot` commands now close their runtime cleanly instead of leaving GPIO cleanup to process exit

### Direct driver tests

Run these one by one from the project root:

```bash
uv run pi5buzzer info --health-check
uv run pi5disp info
uv run pi5vl53l0x status
uv run pi5servo status --pins 12,13
```

Expected result:

- each driver reports its own state using the same root-level config files

### Direct integrated servo test

```bash
uv run ninjaclawbot move-servos "F_12:C/13:C"
```

Expected result:

- the command returns a structured JSON result
- if the servo backend is not ready, the result still returns a clear typed error message

### Create and run a movement

Start the interactive tool:

```bash
uv run ninjaclawbot movement-tool
```

Suggested first test:

1. Choose `2. Create movement`
2. Enter a command such as `F_12:20/13:-20`
3. Choose `3. Finish Recording`
4. Save it as `wave`
5. Exit the tool

Then run:

```bash
uv run ninjaclawbot perform-movement wave
```

Expected result:

- `ninjaclawbot_data/movements/wave.json` is created at the project root
- the integrated executor runs the saved movement with structured JSON output

### Preview and run built-in expressions

Start the interactive tool:

```bash
uv run ninjaclawbot expression-tool
```

Suggested first test:

1. Choose `2. List built-in expressions`
2. Choose `3. Preview built-in expression`
3. Preview `idle`, `greeting`, `happy`, `thinking`, and `confusing`
4. Choose `7. Set idle expression`
5. Choose `8. Stop active expression`

Expected result:

- the built-in face engine follows the legacy NinjaRobotV5 visual language on the SPI display
- previews use coordinated facial animation and buzzer emotion playback
- `idle` can start and stop without leaving the display or buzzer in a bad state
- leaving `uv run ninjaclawbot expression-tool` should return to the shell without a GPIO cleanup traceback

### Create and run a saved expression

Start the interactive tool:

```bash
uv run ninjaclawbot expression-tool
```

Suggested first saved-expression test:

1. Choose `4. Create expression asset`
2. Name it `happy`
3. Set built-in expression to `happy`
4. Optionally add display text such as `Hello`
5. Keep the default `Return to idle after playing?` value
6. Exit and save

Then run:

```bash
uv run ninjaclawbot perform-expression happy
```

Expected result:

- `ninjaclawbot_data/expressions/happy.json` is created at the project root
- the saved asset can reuse a built-in expression plus optional text and sound overrides
- the integrated executor drives display and buzzer actions through the real `pi5*` packages
- the buzzer emotion melody finishes before the command exits
- temporary expressions return to the animated `idle` face when `idle_reset` is enabled

### JSON action test

```bash
uv run ninjaclawbot run-action '{"action":"read_distance"}'
```

Expected result:

- JSON is returned with the action result
- if the sensor is not available, the result reports a clear failure instead of a traceback

## Safety Notes

- Start with one servo only before testing saved movements.
- Keep clear mechanical space around moving parts.
- Use external servo power where required.
- Power the Raspberry Pi down before rewiring SPI, I2C, or servo connections.
- For DFR0566 PWM control, do not treat the HAT PWM ports and HAT digital breakout ports as the same signal path.

## Development References

- `developmentPlan.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`
- `ninjaclawbot/README.md`
