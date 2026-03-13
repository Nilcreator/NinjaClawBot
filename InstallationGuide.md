# NinjaClawBot Installation Guide

This guide shows the shortest reliable way to set up **NinjaClawBot** on a
Raspberry Pi 5 from scratch.

The main path is intentionally simple:

- prepare the Raspberry Pi
- install the project
- use the guided tools to set up each hardware module
- connect OpenClaw
- run the final startup -> reply -> power-off validation

This guide is written for non-developers too. When a short technical term is
used, a simple explanation is included nearby.

If you want the short project overview, read [README.md](README.md).

If you want developer details, read [DevelopmentGuide.md](DevelopmentGuide.md).

## 1. What You Will Have At The End

After you finish this guide, your Raspberry Pi should be able to:

- show a startup greeting when OpenClaw starts
- show a face and sound expression when OpenClaw replies
- return to idle after the reply
- show a sleepy expression and power down the display when OpenClaw stops

## 2. What You Need

You need:

- a Raspberry Pi 5
- Raspberry Pi OS Bookworm or newer
- internet access
- keyboard and screen, or SSH (remote terminal access)
- the robot hardware you plan to use

Optional hardware supported by this project:

- passive buzzer
- servo motors
- ST7789V SPI display
- VL53L0X distance sensor
- DFR0566 expansion HAT for HAT-based servo control

## 3. Safety First

Before wiring anything:

- power off the Raspberry Pi before changing wires
- use external power for real servo tests
- keep a common ground between servo power and the Raspberry Pi
- start with one servo only for the first movement test
- keep moving parts clear of obstacles

Short explanations:

- `GPIO`: the control pins on the Raspberry Pi
- `SPI`: a fast pin connection used by many small displays
- `I2C`: a two-wire connection used by sensors and some HATs
- `PWM`: a timed signal used to move servos

## 4. Update The Raspberry Pi

Purpose:
- make sure the operating system is current before you install anything

Run:

```bash
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```

After reboot, log in again.

Need help later?
- [Troubleshooting](#appendix-a-system-preparation)
- [Alternative commands](#appendix-b-system-preparation-alternatives)

## 5. Install The Basic Packages

Purpose:
- install the tools needed for Python, Git, and Raspberry Pi hardware checks

Run:

```bash
sudo apt update
sudo apt install -y \
  git \
  curl \
  python3-dev \
  build-essential \
  swig \
  i2c-tools
```

Need help later?
- [Troubleshooting](#appendix-a-system-preparation)
- [Alternative commands](#appendix-b-system-preparation-alternatives)

## 6. Enable Raspberry Pi Interfaces

Purpose:
- turn on the Raspberry Pi hardware interfaces used by the display, sensor, and
  optional HAT

Open the Raspberry Pi setup menu:

```bash
sudo raspi-config
```

Enable:

1. `Interface Options` -> `SPI` -> `Yes`
2. `Interface Options` -> `I2C` -> `Yes`

Then reboot:

```bash
sudo reboot
```

If you plan to drive servos directly from GPIO 12 and GPIO 13, also add this
PWM (servo signal) overlay:

```bash
sudo nano /boot/firmware/config.txt
```

Add:

```ini
dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4
```

Then reboot again:

```bash
sudo reboot
```

Need help later?
- [Troubleshooting](#appendix-a-system-preparation)
- [Alternative commands](#appendix-b-system-preparation-alternatives)

## 7. Install `uv`

Purpose:
- install the Python environment tool used by this project

Run:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"
command -v uv
uv --version
```

Expected result:

- `command -v uv` prints a full path such as `/home/YOUR_USERNAME/.local/bin/uv`
- `uv --version` prints a version number

Need help later?
- [Troubleshooting](#appendix-c-python-and-project-installation)
- [Alternative commands](#appendix-d-python-and-project-installation-alternatives)

## 8. Install OpenClaw

Purpose:
- install OpenClaw before connecting NinjaClawBot to it

Follow the official OpenClaw setup guide first:

- [OpenClaw Quickstart](https://github.com/Nilcreator/NinjaClawAgent/blob/main/README.md)

When you come back to this guide, you should already have:

- the `openclaw` command
- a working `~/.openclaw/openclaw.json`
- your own model settings
- your own Telegram bot settings if you plan to use Telegram

Do not replace the whole `openclaw.json` with a template from somewhere else.
This guide patches your existing file safely.

Need help later?
- [Troubleshooting](#appendix-e-openclaw-connection-and-configuration)
- [Alternative commands](#appendix-f-openclaw-connection-and-configuration-alternatives)

## 9. Clone NinjaClawBot

Purpose:
- download the repository to your Raspberry Pi

Run:

```bash
cd ~
git clone https://github.com/Nilcreator/NinjaClawBot.git
cd ~/NinjaClawBot
```

From now on, this guide assumes the project root is:

```bash
~/NinjaClawBot
```

Need help later?
- [Troubleshooting](#appendix-c-python-and-project-installation)
- [Alternative commands](#appendix-d-python-and-project-installation-alternatives)

## 10. Install The Project

Purpose:
- install NinjaClawBot and all included Pi 5 hardware libraries in one step

Run:

```bash
cd ~/NinjaClawBot
uv sync --extra dev
```

Then verify the environment:

```bash
cd ~/NinjaClawBot
uv run python -c "import ninjaclawbot, pi5buzzer, pi5servo, pi5disp, pi5vl53l0x; print('imports-ok')"
uv run ninjaclawbot --help
uv run pi5buzzer --help
uv run pi5servo --help
uv run pi5disp --help
uv run pi5vl53l0x --help
```

Expected result:

- `imports-ok` is printed
- all help commands work

Need help later?
- [Troubleshooting](#appendix-c-python-and-project-installation)
- [Alternative commands](#appendix-d-python-and-project-installation-alternatives)

## 11. Wire The Hardware

Purpose:
- connect the robot hardware before running the guided setup tools

For detailed wiring, use the hardware library READMEs:

- buzzer: [pi5buzzer/README.md](pi5buzzer/README.md)
- servo: [pi5servo/README.md](pi5servo/README.md)
- display: [pi5disp/README.md](pi5disp/README.md)
- distance sensor: [pi5vl53l0x/README.md](pi5vl53l0x/README.md)

Quick first-test notes:

- direct servo tests work best on GPIO 12 or GPIO 13
- the VL53L0X usually appears at I2C address `0x29`
- the DFR0566 HAT usually appears at I2C address `0x10`

Need help later?
- [Troubleshooting](#appendix-g-hardware-wiring-and-guided-module-setup)
- [Alternative commands](#appendix-h-module-setup-alternative-commands)

## 12. Run The Guided Hardware Setup Tools

Purpose:
- initialize, calibrate, and test the hardware using the most beginner-friendly
  tools first

Run these in the order below.

### 12.1 Servo setup

Use the guided servo tool:

```bash
cd ~/NinjaClawBot
uv run pi5servo servo-tool
```

Inside the tool:

1. choose the servo you actually wired, such as `gpio12` or `hat_pwm1`
2. run calibration
3. save the result
4. use quick move or single move to confirm the servo can move safely

Expected result:

- `servo.json` is created
- the servo moves safely after calibration

### 12.2 Buzzer setup

Use the guided buzzer tool:

```bash
cd ~/NinjaClawBot
uv run pi5buzzer buzzer-tool
```

Inside the tool:

1. initialize the buzzer on your GPIO pin, usually `17`
2. run a test beep
3. try one emotion sound such as `happy`

Expected result:

- `buzzer.json` is created
- you hear a short test sound

### 12.3 Display setup

Create the display settings file first:

```bash
cd ~/NinjaClawBot
uv run pi5disp init
```

Then run the guided display tool:

```bash
cd ~/NinjaClawBot
uv run pi5disp display-tool
```

Inside the tool:

1. confirm the saved config
2. clear the screen
3. display text such as `HELLO`
4. optionally run the demo animation

Expected result:

- `display.json` is created
- the display responds correctly

### 12.4 Distance sensor setup

Check that the sensor is visible on I2C:

```bash
ls /dev/i2c-1
sudo i2cdetect -y 1
```

You should normally see `29`.

Then run the guided sensor tool:

```bash
cd ~/NinjaClawBot
uv run pi5vl53l0x sensor-tool
```

Inside the tool:

1. run status
2. take a few readings
3. if needed, run calibration using a known distance

Expected result:

- the sensor returns readings
- if you calibrate it, `vl53l0x.json` is created

Need help later?
- [Troubleshooting](#appendix-g-hardware-wiring-and-guided-module-setup)
- [Alternative commands](#appendix-h-module-setup-alternative-commands)

## 13. Run A Quick Local NinjaClawBot Test

Purpose:
- confirm the full robot layer works before adding OpenClaw

Run:

```bash
cd ~/NinjaClawBot
uv run ninjaclawbot health-check
uv run ninjaclawbot perform-expression greeting
uv run ninjaclawbot perform-reply --reply-state greeting "Hello"
uv run ninjaclawbot set-idle
```

Expected result:

- health check returns structured output
- greeting expression works
- reply expression works
- idle starts

Need help later?
- [Troubleshooting](#appendix-i-ninjaclawbot-local-testing)
- [Alternative commands](#appendix-j-local-testing-alternative-commands)

## 14. Save The Important Paths

Purpose:
- capture the exact local paths needed for the OpenClaw plugin settings

Run:

```bash
cd ~/NinjaClawBot
export NINJACLAWBOT_ROOT="$(pwd)"
export NINJACLAWBOT_PLUGIN="$(realpath integrations/openclaw/ninjaclawbot-plugin)"
export NINJACLAWBOT_UV="$(command -v uv)"
printf '%s\n%s\n%s\n' "$NINJACLAWBOT_ROOT" "$NINJACLAWBOT_PLUGIN" "$NINJACLAWBOT_UV"
```

Expected result:

- line 1 is your project root
- line 2 is the plugin folder
- line 3 is the full path to `uv`

Need help later?
- [Troubleshooting](#appendix-e-openclaw-connection-and-configuration)
- [Alternative commands](#appendix-f-openclaw-connection-and-configuration-alternatives)

## 15. Back Up Your Existing OpenClaw Config

Purpose:
- keep a safe copy of your working OpenClaw config before patching it

Run:

```bash
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup.$(date +%Y%m%d-%H%M%S)
```

Need help later?
- [Troubleshooting](#appendix-e-openclaw-connection-and-configuration)
- [Alternative commands](#appendix-f-openclaw-connection-and-configuration-alternatives)

## 16. Patch `openclaw.json` Safely

Purpose:
- enable the NinjaClawBot plugin without overwriting your own secrets, tokens,
  and model choices

Run:

```bash
cd ~/NinjaClawBot
python3 - <<'PY'
import json
import os
from pathlib import Path

config_path = Path.home() / ".openclaw" / "openclaw.json"
root = os.environ["NINJACLAWBOT_ROOT"]
plugin = os.environ["NINJACLAWBOT_PLUGIN"]
uv_command = os.environ["NINJACLAWBOT_UV"]

tool_names = [
    "ninjaclawbot_reply",
    "ninjaclawbot_perform_expression",
    "ninjaclawbot_perform_movement",
    "ninjaclawbot_move_servos",
    "ninjaclawbot_read_distance",
    "ninjaclawbot_health",
    "ninjaclawbot_capabilities",
    "ninjaclawbot_set_idle",
    "ninjaclawbot_stop",
    "ninjaclawbot_stop_all",
    "ninjaclawbot",
]

with config_path.open("r", encoding="utf-8") as f:
    data = json.load(f)

agents = data.setdefault("agents", {})
defaults = agents.setdefault("defaults", {})
defaults.setdefault("workspace", str(Path.home() / ".openclaw" / "workspace"))

agent_list = agents.setdefault("list", [])
main_agent = next((item for item in agent_list if item.get("id") == "main"), None)
if main_agent is None:
    main_agent = {"id": "main"}
    agent_list.append(main_agent)

tools = main_agent.setdefault("tools", {})
allow = tools.setdefault("allow", [])
for name in tool_names:
    if name not in allow:
        allow.append(name)

hooks = data.setdefault("hooks", {}).setdefault("internal", {})
hooks["enabled"] = True
hook_entries = hooks.setdefault("entries", {})
hook_entries.setdefault("boot-md", {})["enabled"] = True

skills = data.setdefault("skills", {})
skills.setdefault("install", {}).setdefault("nodeManager", "npm")
skill_entries = skills.setdefault("entries", {})
skill_entries.setdefault("ninjaclawbot_control", {})["enabled"] = True

plugins = data.setdefault("plugins", {})
plugin_allow = plugins.setdefault("allow", [])
for plugin_id in ("telegram", "ninjaclawbot"):
    if plugin_id not in plugin_allow:
        plugin_allow.append(plugin_id)

load = plugins.setdefault("load", {})
paths = load.setdefault("paths", [])
if plugin not in paths:
    paths.append(plugin)

entries = plugins.setdefault("entries", {})
entries.setdefault("telegram", {}).setdefault("enabled", True)

ninjaclawbot_entry = entries.setdefault("ninjaclawbot", {})
ninjaclawbot_entry["enabled"] = True
ninjaclawbot_entry.pop("hooks", None)

ninjaclawbot_config = ninjaclawbot_entry.setdefault("config", {})
ninjaclawbot_config["projectRoot"] = root
ninjaclawbot_config["rootDir"] = root
ninjaclawbot_config["uvCommand"] = uv_command
ninjaclawbot_config["enablePersistentBridge"] = True
ninjaclawbot_config["bridgeStartTimeoutMs"] = 10000
ninjaclawbot_config["bridgeRequestTimeoutMs"] = 15000
ninjaclawbot_config["bridgeShutdownTimeoutMs"] = 5000

for unsupported_key in (
    "enableAlwaysOn",
    "enableStartupGreeting",
    "enableAutoThinking",
    "enableShutdownSequence",
):
    ninjaclawbot_config.pop(unsupported_key, None)

with config_path.open("w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
    f.write("\n")

print(f"Updated {config_path}")
print(json.dumps({
    "workspace": defaults.get("workspace"),
    "ninjaclawbot_config": ninjaclawbot_entry,
    "boot_md_enabled": data.get("hooks", {}).get("internal", {}).get("entries", {}).get("boot-md", {}),
    "skill_entry": data.get("skills", {}).get("entries", {}).get("ninjaclawbot_control", {})
}, indent=2))
PY
```

Use your own private values in `openclaw.json`. Never share real:

- Telegram bot tokens
- gateway tokens
- API keys
- pairing codes

Need help later?
- [Troubleshooting](#appendix-e-openclaw-connection-and-configuration)
- [Alternative commands](#appendix-f-openclaw-connection-and-configuration-alternatives)

## 17. Create The Workspace Instruction Files

Purpose:
- make startup greeting and reply expressions reliable in the validated build

### 17.1 Create `BOOT.md`

Run:

```bash
export OPENCLAW_WORKSPACE="$(
python3 - <<'PY'
import json
from pathlib import Path

cfg = json.load((Path.home() / ".openclaw" / "openclaw.json").open("r", encoding="utf-8"))
agents = cfg.get("agents", {}).get("list", [])
main = next((a for a in agents if a.get("id") == "main"), {})
workspace = main.get("workspace") or cfg.get("agents", {}).get("defaults", {}).get("workspace") or str(Path.home() / ".openclaw" / "workspace")
print(Path(workspace).expanduser())
PY
)"
mkdir -p "$OPENCLAW_WORKSPACE"
cat > "$OPENCLAW_WORKSPACE/BOOT.md" <<'EOF'
## NinjaClawBot Startup

At gateway startup, call `ninjaclawbot_reply` exactly once with:
- `text`: `NinjaClawBot is online.`
- `reply_state`: `greeting`
- `display_text`: `HELLO`

Do not send a visible chat reply for this startup task.
After the tool call, reply with `NO_REPLY`.
EOF
```

### 17.2 Create or update `AGENTS.md`

Run:

```bash
python3 - <<'PY'
from pathlib import Path
import os

path = Path(os.environ["OPENCLAW_WORKSPACE"]) / "AGENTS.md"
block = """
## NinjaClawBot Reply Policy

When replying to users in Telegram or other chat channels:
- always use `ninjaclawbot_reply` for the final visible answer
- choose the closest `reply_state` for the tone of the answer
- do not send a plain text-only final answer unless `ninjaclawbot_reply` fails
- after normal replies, let the lifecycle return the robot to idle
""".lstrip()

existing = path.read_text(encoding="utf-8") if path.exists() else ""
marker = "## NinjaClawBot Reply Policy"
if marker not in existing:
    if existing and not existing.endswith("\n"):
        existing += "\n"
    existing += ("\n" if existing else "") + block
    path.write_text(existing, encoding="utf-8")

print(path)
print(path.read_text(encoding="utf-8"))
PY
```

Need help later?
- [Troubleshooting](#appendix-e-openclaw-connection-and-configuration)
- [Alternative commands](#appendix-f-openclaw-connection-and-configuration-alternatives)

## 18. Run OpenClaw Health Checks

Purpose:
- confirm the plugin, hooks, skills, and config are all visible before you test
  the robot behavior

Run:

```bash
openclaw doctor --fix
openclaw hooks enable boot-md
openclaw hooks info boot-md
openclaw skills list --eligible | grep -iE 'ninjaclawbot_control|ninjaclawbot' || true
openclaw hooks list --verbose | grep -iE 'boot-md|ninjaclawbot|message_received|agent_end|gateway_stop' || true
openclaw plugins info ninjaclawbot
```

Expected result:

- `doctor` succeeds
- `boot-md` is enabled
- `ninjaclawbot_control` appears in the eligible skills
- NinjaClawBot hooks appear in the hook list
- the plugin points to your local repo path

Need help later?
- [Troubleshooting](#appendix-e-openclaw-connection-and-configuration)
- [Alternative commands](#appendix-f-openclaw-connection-and-configuration-alternatives)

## 19. Start OpenClaw

Purpose:
- start the gateway and prepare for final robot validation

Run:

```bash
openclaw gateway start
openclaw gateway status
```

If `openclaw logs --follow` is blocked by pairing or auth on your Pi, use the
raw log file instead:

```bash
tail -f "$(ls -t /tmp/openclaw/openclaw-*.log | head -n1)"
```

Need help later?
- [Troubleshooting](#appendix-e-openclaw-connection-and-configuration)
- [Alternative commands](#appendix-f-openclaw-connection-and-configuration-alternatives)

## 20. Final Validation

Purpose:
- confirm the complete validated behavior on the Raspberry Pi

### 20.1 Startup check

Run:

```bash
openclaw gateway restart
```

Expected result:

- one startup greeting appears
- the robot then returns to idle

### 20.2 Reply check

In Telegram, start a fresh session:

```text
/new
```

Then send:

```text
hello
```

Expected result:

- the robot shows a reply expression
- the answer is not text-only
- the robot returns to idle after the reply

If you want to confirm the tool call from the Pi terminal:

```bash
grep -iE 'ninjaclawbot_reply|ninjaclawbot_perform_expression|tools' "$(ls -t /tmp/openclaw/openclaw-*.log | head -n1)" | tail -n 30
```

### 20.3 Shutdown check

Run:

```bash
openclaw gateway stop
openclaw gateway status
```

Expected result:

- the robot shows the sleepy expression once
- the display powers down after sleepy finishes

Need help later?
- [Troubleshooting](#appendix-k-final-validation-troubleshooting)
- [Alternative commands](#appendix-l-final-validation-alternatives)

---

## Appendix A. System Preparation

### Troubleshooting

- `apt` errors:
  run `sudo apt update` again, then retry the install command
- `raspi-config` changes do not take effect:
  reboot the Pi and recheck `/dev/i2c-1` and `/dev/spidev0.0`
- direct GPIO servo PWM does not work:
  re-open `/boot/firmware/config.txt` and confirm the PWM overlay line exists

### Quick checks

```bash
ls /dev/i2c-1
ls /dev/spidev0.0
grep -n 'dtoverlay=pwm-2chan' /boot/firmware/config.txt || true
```

## Appendix B. System Preparation Alternatives

- if you use only the DFR0566 HAT for servo PWM, you can skip the PWM overlay
- if your display or sensor is not connected yet, you can still continue and
  come back to the hardware setup later

## Appendix C. Python And Project Installation

### Troubleshooting

- `command -v uv` prints nothing:
  run the install command again and then `source "$HOME/.local/bin/env"`
- `uv sync --extra dev` fails:
  check internet access and rerun it from `~/NinjaClawBot`
- `git pull` fails because of `__pycache__` files:
  use the cleanup block below

### Quick fixes

```bash
source "$HOME/.local/bin/env"
cd ~/NinjaClawBot
uv sync --extra dev
```

`git pull` cache cleanup:

```bash
cd ~/NinjaClawBot
git ls-files | grep '/__pycache__/.*\.pyc$' | xargs -r git restore --
find ninjaclawbot/src -type d -name __pycache__ -prune -exec rm -rf {} +
git ls-files | grep '/__pycache__/.*\.pyc$' | xargs -r git restore --
git pull
```

## Appendix D. Python And Project Installation Alternatives

- if you only want to test one standalone library first, you can enter that
  library folder and run `uv sync --extra pi --extra dev` there
- if you do not need dev tools, you can use:

```bash
cd ~/NinjaClawBot
uv sync
```

## Appendix E. OpenClaw Connection And Configuration

### Troubleshooting

- `spawn uv ENOENT`:
  make sure `plugins.entries.ninjaclawbot.config.uvCommand` matches the full
  output of `command -v uv`
- `openclaw logs --follow` says pairing required:
  use the raw log file with `tail -f` instead
- `plugins.entries.ninjaclawbot: Unrecognized key: "hooks"`:
  remove that unsupported plugin key from `openclaw.json`
- startup greeting does not appear:
  confirm `boot-md` is enabled and `BOOT.md` exists in the workspace
- reply is still text-only:
  confirm `AGENTS.md` contains the NinjaClawBot reply policy and start a fresh
  Telegram session with `/new`

### Quick checks

```bash
command -v uv
openclaw hooks info boot-md
openclaw hooks list --verbose | grep -iE 'boot-md|ninjaclawbot' || true
openclaw plugins info ninjaclawbot
cat "$OPENCLAW_WORKSPACE/BOOT.md" 2>/dev/null || true
cat "$OPENCLAW_WORKSPACE/AGENTS.md" 2>/dev/null || true
```

## Appendix F. OpenClaw Connection And Configuration Alternatives

- if you already know your workspace path, you can set it manually instead of
  using the discovery command:

```bash
export OPENCLAW_WORKSPACE="/home/YOUR_USERNAME/.openclaw/workspace"
```

- if `grep` filtering is confusing, run the OpenClaw commands without `grep`:

```bash
openclaw skills list --eligible
openclaw hooks list --verbose
openclaw plugins info ninjaclawbot
```

## Appendix G. Hardware Wiring And Guided Module Setup

### Troubleshooting

- no servo motion:
  verify power, ground, and the correct endpoint name such as `gpio12` or `hat_pwm1`
- no buzzer sound:
  confirm the buzzer is on the saved GPIO pin and test with the guided tool
- display stays blank:
  verify SPI is enabled and confirm the saved display pins in `display.json`
- sensor is missing from I2C:
  run `sudo i2cdetect -y 1` and check for `29`

### Quick checks

```bash
cd ~/NinjaClawBot
sudo i2cdetect -y 1
uv run pi5servo status --no-probe --pins 12,13
uv run pi5buzzer info --health-check
uv run pi5disp info
uv run pi5vl53l0x status
```

## Appendix H. Module Setup Alternative Commands

If you prefer direct commands instead of the interactive tools:

### Servo

```bash
cd ~/NinjaClawBot
uv run pi5servo calib 12
uv run pi5servo move 12 center
```

### Buzzer

```bash
cd ~/NinjaClawBot
uv run pi5buzzer init 17
uv run pi5buzzer beep 440 0.3
uv run pi5buzzer play happy
```

### Display

```bash
cd ~/NinjaClawBot
uv run pi5disp init --defaults
uv run pi5disp text "HELLO"
uv run pi5disp demo --num-balls 3 --duration 5
```

### Sensor

```bash
cd ~/NinjaClawBot
uv run pi5vl53l0x test
uv run pi5vl53l0x calibrate --distance 200 --count 10
uv run pi5vl53l0x get --count 5 --interval 0.5
```

## Appendix I. NinjaClawBot Local Testing

### Troubleshooting

- local `ninjaclawbot` expressions fail:
  check that each hardware module worked first
- `health-check` shows unavailable hardware:
  complete the guided module setup before continuing

### Quick checks

```bash
cd ~/NinjaClawBot
uv run ninjaclawbot health-check
uv run ninjaclawbot list-capabilities
uv run ninjaclawbot perform-expression idle
```

## Appendix J. Local Testing Alternative Commands

Extra local checks:

```bash
cd ~/NinjaClawBot
uv run ninjaclawbot list-assets
uv run ninjaclawbot perform-expression greeting
uv run ninjaclawbot perform-reply --reply-state success "Finished"
uv run ninjaclawbot stop
uv run ninjaclawbot stop-all
```

## Appendix K. Final Validation Troubleshooting

- startup works but reply is text-only:
  check the log for `ninjaclawbot_reply`
- shutdown works but startup does not:
  recheck `boot-md` and `BOOT.md`
- `openclaw logs --follow` fails:
  use the raw log file

Log checks:

```bash
tail -f "$(ls -t /tmp/openclaw/openclaw-*.log | head -n1)"
grep -iE 'ninjaclawbot_reply|boot-md|ninjaclawbot' "$(ls -t /tmp/openclaw/openclaw-*.log | head -n1)" | tail -n 50
```

## Appendix L. Final Validation Alternatives

- if you want to validate with direct tool calls before Telegram, use the local
  `ninjaclawbot` CLI from Section 13 first
- if Telegram sessions behave strangely, start a fresh chat with:

```text
/new
```

## Appendix M. Sanitized Reference `openclaw.json`

Use this only as a shape reference. Replace every placeholder with your own
real values.

```json
{
  "auth": {
    "profiles": {
      "YOUR_AUTH_PROFILE_NAME": {
        "provider": "openai-codex",
        "mode": "oauth"
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "openai-codex/gpt-5.3-codex"
      },
      "workspace": "/home/YOUR_USERNAME/.openclaw/workspace"
    },
    "list": [
      {
        "id": "main",
        "tools": {
          "allow": [
            "ninjaclawbot_reply",
            "ninjaclawbot_perform_expression",
            "ninjaclawbot_perform_movement",
            "ninjaclawbot_move_servos",
            "ninjaclawbot_read_distance",
            "ninjaclawbot_health",
            "ninjaclawbot_capabilities",
            "ninjaclawbot_set_idle",
            "ninjaclawbot_stop",
            "ninjaclawbot_stop_all",
            "ninjaclawbot"
          ]
        }
      }
    ]
  },
  "hooks": {
    "internal": {
      "enabled": true,
      "entries": {
        "boot-md": {
          "enabled": true
        }
      }
    }
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "dmPolicy": "pairing",
      "botToken": "YOUR_TELEGRAM_BOT_TOKEN",
      "groupPolicy": "allowlist",
      "streaming": false,
      "network": {
        "autoSelectFamily": false
      }
    }
  },
  "gateway": {
    "port": 18789,
    "mode": "local",
    "bind": "loopback",
    "auth": {
      "mode": "token",
      "token": "YOUR_OPENCLAW_GATEWAY_TOKEN"
    }
  },
  "skills": {
    "install": {
      "nodeManager": "npm"
    },
    "entries": {
      "ninjaclawbot_control": {
        "enabled": true
      }
    }
  },
  "plugins": {
    "allow": [
      "telegram",
      "ninjaclawbot"
    ],
    "load": {
      "paths": [
        "/home/YOUR_USERNAME/NinjaClawBot/integrations/openclaw/ninjaclawbot-plugin"
      ]
    },
    "entries": {
      "telegram": {
        "enabled": true
      },
      "ninjaclawbot": {
        "enabled": true,
        "config": {
          "projectRoot": "/home/YOUR_USERNAME/NinjaClawBot",
          "rootDir": "/home/YOUR_USERNAME/NinjaClawBot",
          "uvCommand": "/home/YOUR_USERNAME/.local/bin/uv",
          "enablePersistentBridge": true,
          "bridgeStartTimeoutMs": 10000,
          "bridgeRequestTimeoutMs": 15000,
          "bridgeShutdownTimeoutMs": 5000
        }
      }
    }
  }
}
```
