# pi5servo

**Velocity-based servo control library for Raspberry Pi 5**

A lightweight, physics-based servo control library for SG90 and MG90S style servos. `pi5servo` keeps the movement model, calibration flow, command format, and interactive tools from `pi0servo`, but replaces the old `pigpio`-only transport with a Raspberry Pi 5 friendly backend system.

The default target is **header-connected servos on Raspberry Pi 5** using hardware-backed PWM. An optional `pca9685` backend is also available for advanced external controller setups.

## ✨ Key Features

- **Velocity-based Motion** – Physics calculations (degrees/sec) instead of arbitrary durations
- **100Hz Update Rate** – 10ms step interval for smooth, controlled motion
- **Cubic Easing (Default)** – Uses `ease_in_out_cubic` for natural S-curve acceleration
- **Per-Servo Speed Limits** – Individual speed limits (0-100%) reduce mechanical stress
- **Thread-safe Abort** – Immediately stop any running movement
- **Interactive Tools** – Menu-driven `servo-tool` plus calibration TUI
- **Pi 5 Standalone Backends** – `auto`, `hardware_pwm`, optional `pca9685`, and legacy `pigpio` compatibility

## 📋 Requirements

- Raspberry Pi 5
- Python 3.11 or 3.12
- `uv` for installation and testing
- SG90, MG90S, or similar hobby servo motors
- External 5V servo power supply for real hardware testing

### Supported Header Pins

The default header-connected backend is `hardware_pwm`. It is intended for these Raspberry Pi 5 PWM-capable GPIO pins:

- GPIO12
- GPIO13
- GPIO18
- GPIO19

> [!IMPORTANT]
> **Only use pins that are enabled in your Pi 5 firmware overlay.** The library can map all four default PWM-capable pins, but your `/boot/firmware/config.txt` setup decides which ones are actually active on the board.

---

## 🚀 Installation

### Step 1: Install `uv`

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart the shell after installation, or run:

```bash
source "$HOME/.local/bin/env"
```

### Step 2: Enable Raspberry Pi 5 PWM

Edit `/boot/firmware/config.txt` and enable one of these common overlay setups:

```ini
# GPIO12 and GPIO13
dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4
```

or

```ini
# GPIO18 and GPIO19
dtoverlay=pwm-2chan
```

Reboot after saving the file.

> [!NOTE]
> `pi5servo` defaults to a pin-to-channel map of `12->0`, `13->1`, `18->2`, and `19->3`. If your overlay uses a different mapping, pass `--pin-channel-map` on the CLI or store the custom mapping in `servo.json`.

### Step 3: Clone the Repository

```bash
git clone https://github.com/Nilcreation/NinjaClawBot.git
cd NinjaClawBot/"Code library"/NinjaClawbot/pi5servo
```

### Step 4: Install with `uv`

```bash
# Install the standalone Raspberry Pi runtime
uv python install 3.11
uv sync --extra pi
```

For development and testing:

```bash
uv sync --extra pi --extra dev
```

> [!NOTE]
> `uv sync` creates and manages `.venv` automatically. You do not need to run `uv venv` or activate the environment manually.

### Step 5: Verify Installation

```bash
uv run pi5servo --help
uv run pi5servo status --pins 12,13
```

If you want to use the optional external controller path later, install the same `pi` extra and run the CLI with `--backend pca9685`.

---

## 🎮 Quick Start

> [!CAUTION]
> **Calibration is REQUIRED before use.** Uncalibrated servos use safe center-only defaults. This prevents unexpected movement, but it also means an uncalibrated servo will not move through its full range.

### 1. Start the Interactive Tool

```bash
uv run pi5servo servo-tool
```

### 2. Main Menu

```
╔══════════════════════════════════════════════════════════╗
║           pi5servo Interactive Tool                      ║
╠══════════════════════════════════════════════════════════╣
║  1. Quick Move    - Enter commands like '12:30/13:M'     ║
║  2. Single Move   - Move one servo to angle              ║
║  3. Calibrate     - Launch calibration TUI               ║
║  4. Set Speed     - Adjust servo speed limit             ║
║  5. Status        - Show backend and servo configs       ║
║  6. Config        - Show/export/import config            ║
║  q. Exit                                                 ║
╚══════════════════════════════════════════════════════════╝
```

### 3. First-Time Setup: Calibrate Your Servos

> [!IMPORTANT]
> **Calibration is required before motion work.** Each servo has different real pulse limits, even when it is the same model.

1. Select option **3. Calibrate**
2. Enter the GPIO pin number that carries the servo signal
3. Use the calibration TUI to find the correct pulse widths

| Key | Action |
|-----|--------|
| **Tab / Shift+Tab** | Cycle through Min, Center, Max |
| **Up / Down** | Large pulse adjustment (±20μs) |
| **w / s** | Fine adjustment (±1μs) |
| **+ / -** | Adjust speed limit |
| **Enter** | Save calibration |
| **q** | Quit |

---

## 📋 Command Format

Commands use the **movement-tool** format:

```text
[GLOBAL_SPEED_]PIN:ANGLE[LOCAL_SPEED][/PIN:ANGLE[LOCAL_SPEED]...]
```

### Examples

| Command | Description |
|---------|-------------|
| `12:45` | Move GPIO12 to 45° at medium speed (default) |
| `F_12:45` | Move GPIO12 to 45° at **Fast** speed |
| `M_12:45/13:-30` | Move two servos at **Medium** speed |
| `S_12:C/13:MF` | Move GPIO12 to Center and GPIO13 to Min with a fast local override |
| `12:45S` | Move GPIO12 to 45° at **Slow** speed |

### Speed Modes

| Prefix | Mode | Description |
|--------|------|-------------|
| `F_` | Fast | Maximum velocity |
| `M_` | Medium | Default balanced speed |
| `S_` | Slow | Gentle movement |

### Special Angles

| Symbol | Meaning |
|--------|---------|
| `C` | Center (0°) |
| `M` | Min (-90°) |
| `X` | Max (90°) |

---

## 🔧 CLI Commands

```bash
# Interactive tool (recommended)
uv run pi5servo servo-tool

# Calibration
uv run pi5servo calib 12
uv run pi5servo calib --show

# Single servo
uv run pi5servo move 12 45
uv run pi5servo move 12 center

# Multi-servo command
uv run pi5servo cmd "F_12:45/13:-30" --pins 12,13

# Status and configuration
uv run pi5servo status --pins 12,13
uv run pi5servo config show
uv run pi5servo config export backup.json
uv run pi5servo config import backup.json
```

### Advanced Backend Examples

```bash
# Use the optional PCA9685 controller
uv run pi5servo move 12 45 \
  --backend pca9685 \
  --address 0x40 \
  --channel-map 12:0

# Override the Pi 5 hardware PWM mapping
uv run pi5servo status \
  --backend hardware_pwm \
  --pins 12,13 \
  --pin-channel-map 12:0,13:1
```

---

## 🐍 Python API

### Basic Standalone Usage

```python
from pi5servo import ConfigManager, ServoGroup

manager = ConfigManager("servo.json")
manager.load()
calibrations = {12: manager.get_calibration(12), 13: manager.get_calibration(13)}

group = ServoGroup(None, pins=[12, 13], calibrations=calibrations)
group.move_all_sync(targets=[45, -30], speed_mode="M")
group.off()
group.close()
```

### Async Usage

```python
await group.move_all_async(targets=[45, -30], speed_mode="M")
group.abort()
```

### Optional External Controller Usage

```python
from pi5servo import ConfigManager, ServoGroup

manager = ConfigManager("servo.json")
manager.load()
calibrations = {12: manager.get_calibration(12)}

group = ServoGroup(
    None,
    pins=[12],
    calibrations=calibrations,
    backend="pca9685",
    backend_kwargs={
        "address": 0x40,
        "channel_map": {12: 0},
    },
)
group.move_all_sync(targets=[45], speed_mode="S")
group.close()
```

### Legacy Compatibility Usage

```python
import pigpio
from pi5servo import ConfigManager, ServoGroup

pi = pigpio.pi()

manager = ConfigManager("servo.json")
manager.load()
calibrations = {12: manager.get_calibration(12)}

group = ServoGroup(pi, pins=[12], calibrations=calibrations)
group.move_all_sync(targets=[45], speed_mode="M")
group.off()
group.close()
pi.stop()
```

---

## 📁 Configuration File

Calibration and optional backend settings are stored in `servo.json`:

```json
{
  "__backend__": {
    "name": "hardware_pwm",
    "kwargs": {
      "pin_channel_map": {
        "12": 0,
        "13": 1
      }
    }
  },
  "12": {
    "pulse_min": 500,
    "pulse_center": 1500,
    "pulse_max": 2500,
    "speed": 80
  }
}
```

> [!NOTE]
> **Default (uncalibrated) values are all `1500`.** This means an uncalibrated servo stays at the safe center-only state until you calibrate it.

---

## 🌊 Easing Functions

| Easing | Behavior |
|--------|----------|
| `ease_in_out_cubic` | Smooth S-curve at both ends **(DEFAULT)** |
| `ease_out_cubic` | Fast start, very slow finish |
| `ease_in_cubic` | Very slow start, fast finish |
| `ease_in_out` | Quadratic S-curve |
| `ease_out` | Fast start, slow finish |
| `ease_in` | Slow start, fast finish |
| `linear` | Constant speed |

> [!TIP]
> `ease_in_out_cubic` with the 100Hz update loop gives the smoothest default motion and keeps the movement profile close to the legacy `pi0servo` behavior.

---

## 🔌 Hardware Wiring

Connect a hobby servo like this:

| Servo Wire | Raspberry Pi 5 / Power |
|------------|-------------------------|
| **Red** (VCC) | External 5V servo power |
| **Brown/Black** (GND) | External power ground and Raspberry Pi ground |
| **Orange/Yellow** (Signal) | GPIO12, GPIO13, GPIO18, or GPIO19 |

> [!WARNING]
> Do **not** power multiple servos from the Raspberry Pi 5 header alone. Use an external 5V supply and connect the grounds together.

> [!CAUTION]
> Before real motion testing, verify the pulse signal with a logic analyser or oscilloscope. `pi5servo` is designed around hardware-backed PWM, but wiring mistakes and overlay mistakes can still drive the wrong signal.

---

## License

MIT License - See [LICENSE](LICENSE) for details.
