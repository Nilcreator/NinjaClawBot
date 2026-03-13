# NinjaClawBot Installation Guide

This guide walks you through the full Raspberry Pi 5 setup for **NinjaClawBot**
from a clean machine to a working OpenClaw-connected robot.

The goal is simple:

- install the project on Raspberry Pi
- wire and test the hardware safely
- connect NinjaClawBot to OpenClaw
- enable the validated startup -> reply -> power-off behavior

This guide is written for non-developers too. If a short technical term is used,
the explanation is written next to it in simple words.

If you want the short project overview, read [README.md](README.md).

If you want developer internals, read [DevelopmentGuide.md](DevelopmentGuide.md).

## 1. What You Will Build

At the end of this guide, your Raspberry Pi should be able to do this:

- show a startup greeting when OpenClaw starts
- show a reply expression when OpenClaw answers a Telegram message
- return to idle after the reply
- show a sleepy expression and power down the display when OpenClaw stops

The validated OpenClaw setup used by this guide includes:

- OpenClaw gateway on the Raspberry Pi
- Telegram channel enabled
- NinjaClawBot plugin enabled
- internal `boot-md` hook enabled
- workspace `BOOT.md` for startup greeting
- workspace `AGENTS.md` for reliable reply-tool behavior

## 2. What You Need

Before you start, make sure you have:

- a Raspberry Pi 5
- Raspberry Pi OS Bookworm or newer
- internet access
- a keyboard and screen, or SSH (remote terminal access)
- the hardware you plan to use

Optional hardware supported by this project:

- a passive buzzer for [`pi5buzzer`](pi5buzzer/README.md)
- servos for [`pi5servo`](pi5servo/README.md)
- an ST7789V SPI display
- a VL53L0X distance sensor
- a DFR0566 Raspberry Pi IO Expansion HAT if you want HAT-based servo control

## 3. Safety First

Please read this before wiring anything:

- power off the Raspberry Pi before rewiring GPIO pins
- use **external power** for real servo testing
- keep a **common ground** between the Raspberry Pi and the servo power supply
- start with **one servo only** for the first movement test
- keep the servo arm free so it cannot hit anything during calibration

Short explanations:

- `GPIO`: the Raspberry Pi control pins
- `SPI`: the fast pin bus used by many small displays
- `I2C`: the two-wire bus used by small sensors and HATs
- `PWM`: a timed signal used to control servo position

## 4. Update the Raspberry Pi

Run:

```bash
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```

After the Pi reboots, log in again.

## 5. Install Basic System Packages

These packages are needed for building Python libraries and checking hardware.

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

What they do:

- `git`: downloads and updates the repository
- `curl`: downloads installers
- `python3-dev`: Python build support
- `build-essential`: compiler tools
- `swig`: helper tool sometimes needed for native bindings
- `i2c-tools`: checks I2C devices such as the distance sensor or HAT

## 6. Enable Raspberry Pi Interfaces

NinjaClawBot can use:

- `SPI` for the display
- `I2C` for the distance sensor or HAT
- `PWM` for direct servo control from the Pi header

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

## 7. Optional: Enable Direct PWM Pins for Header Servos

Do this only if you plan to drive servos directly from Raspberry Pi GPIO pins.

Open:

```bash
sudo nano /boot/firmware/config.txt
```

Add this line:

```ini
dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4
```

Save, exit, and reboot:

```bash
sudo reboot
```

If you use only the DFR0566 HAT outputs, you can skip this step.

## 8. Install `uv`

`uv` is the Python environment manager used by this project.

Install it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"
```

Check it:

```bash
command -v uv
uv --version
```

Expected result:

- the first command prints a full path such as `/home/YOUR_USERNAME/.local/bin/uv`
- the second command prints a version number

If `command -v uv` prints nothing, stop here and fix that first.

## 9. Install Node.js and OpenClaw

OpenClaw needs Node.js.

Check whether Node.js is already available:

```bash
node --version
npm --version
```

If Node.js is missing or too old, install OpenClaw first by following the
current official guide, then come back here:

- [OpenClaw Quickstart](https://docs.openclaw.ai/start/quickstart)

At the end of the OpenClaw setup, you should already have:

- the `openclaw` command
- a working `~/.openclaw/openclaw.json`
- your own login, model, Telegram, and gateway secrets already configured

Important:

- do **not** paste your own secrets into this repository
- do **not** replace the whole `openclaw.json` with an example from the internet
- this guide patches your existing `openclaw.json` safely instead

## 10. Clone NinjaClawBot

Clone the repository to your home folder:

```bash
cd ~
git clone https://github.com/Nilcreator/NinjaClawBot.git
cd ~/NinjaClawBot
```

From here onward, this guide assumes the project root is:

```bash
~/NinjaClawBot
```

## 11. Install the Python Environment

Install the full project from the root:

```bash
cd ~/NinjaClawBot
uv sync --extra dev
```

This installs:

- `ninjaclawbot`
- `pi5buzzer`
- `pi5servo`
- `pi5disp`
- `pi5vl53l0x`
- development tools such as `pytest` and `ruff`

## 12. Verify the Basic Environment

Run:

```bash
cd ~/NinjaClawBot
uv run python -c "import ninjaclawbot, pi5buzzer, pi5servo, pi5disp, pi5vl53l0x; print('imports-ok')"
uv run ninjaclawbot --help
uv run pi5servo --help
uv run pi5buzzer --help
uv run pi5disp --help
uv run pi5vl53l0x --help
```

Expected result:

- `imports-ok` is printed
- all help commands work

## 13. Wire the Hardware

Use the dedicated library READMEs for wiring details:

- buzzer: [pi5buzzer/README.md](pi5buzzer/README.md)
- servo: [pi5servo/README.md](pi5servo/README.md)
- display: [pi5disp/README.md](pi5disp/README.md)
- distance sensor: [pi5vl53l0x/README.md](pi5vl53l0x/README.md)

Useful first-test notes:

- direct servo testing works best on GPIO 12 and GPIO 13
- the VL53L0X usually appears at I2C address `0x29`
- the DFR0566 HAT usually appears at I2C address `0x10`

## 14. Create the Hardware Config Files

Do these steps from the project root.

### 14.1 Servo setup

Check the backend:

```bash
cd ~/NinjaClawBot
uv run pi5servo status --no-probe --pins 12,13
```

Calibrate a direct Pi servo:

```bash
uv run pi5servo calib 12
```

Or use the interactive tool:

```bash
uv run pi5servo servo-tool
```

Expected result:

- `servo.json` is created in the project root
- calibration values are saved

### 14.2 Buzzer setup

```bash
cd ~/NinjaClawBot
uv run pi5buzzer init 17
```

Expected result:

- `buzzer.json` is created
- a short test tone plays

### 14.3 Display setup

```bash
cd ~/NinjaClawBot
uv run pi5disp init --defaults
```

Expected result:

- `display.json` is created

### 14.4 Distance sensor setup

Check the I2C bus:

```bash
ls /dev/i2c-1
sudo i2cdetect -y 1
```

Expected result:

- the sensor address `29` appears if the VL53L0X is connected

Optional quick test:

```bash
cd ~/NinjaClawBot
uv run pi5vl53l0x test
```

## 15. Test the Hardware Libraries

### 15.1 Buzzer

```bash
cd ~/NinjaClawBot
uv run pi5buzzer info --health-check
uv run pi5buzzer beep 440 0.3
```

### 15.2 Display

```bash
cd ~/NinjaClawBot
uv run pi5disp info
uv run pi5disp clear
uv run pi5disp text "HELLO"
```

### 15.3 Distance sensor

```bash
cd ~/NinjaClawBot
uv run pi5vl53l0x status
uv run pi5vl53l0x get --count 5 --interval 0.5
```

### 15.4 Servo

Start with one servo only:

```bash
cd ~/NinjaClawBot
uv run pi5servo move 12 center
uv run pi5servo move 12 min
uv run pi5servo move 12 max
```

## 16. Test `ninjaclawbot` Locally

Run the safe checks first:

```bash
cd ~/NinjaClawBot
uv run ninjaclawbot health-check
uv run ninjaclawbot list-assets
uv run ninjaclawbot list-capabilities
```

Then test expressions:

```bash
cd ~/NinjaClawBot
uv run ninjaclawbot perform-expression idle
uv run ninjaclawbot perform-expression greeting
uv run ninjaclawbot perform-reply --reply-state greeting "Hello"
uv run ninjaclawbot set-idle
```

Expected result:

- built-in expressions run
- sound and face outputs work
- idle works

## 17. Find the Real Paths You Need

These are the three important paths:

- project root
- plugin folder
- `uv` executable

Run:

```bash
cd ~/NinjaClawBot
export NINJACLAWBOT_ROOT="$(pwd)"
export NINJACLAWBOT_PLUGIN="$(realpath integrations/openclaw/ninjaclawbot-plugin)"
export NINJACLAWBOT_UV="$(command -v uv)"
printf '%s\n%s\n%s\n' "$NINJACLAWBOT_ROOT" "$NINJACLAWBOT_PLUGIN" "$NINJACLAWBOT_UV"
```

Expected result:

- the first line is your project root
- the second line is your plugin folder
- the third line is the full path to `uv`

## 18. Back Up the OpenClaw Config

Back up your existing config before changing anything:

```bash
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup.$(date +%Y%m%d-%H%M%S)
```

## 19. Patch `openclaw.json` Safely

This is the most important OpenClaw setup step.

The command below:

- keeps your existing secrets
- keeps your existing model settings
- keeps your existing Telegram settings
- adds the validated NinjaClawBot integration settings

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
    "hooks": data.get("hooks", {}),
    "skills": data.get("skills", {}),
    "ninjaclawbot": data.get("plugins", {}).get("entries", {}).get("ninjaclawbot", {})
}, indent=2))
PY
```

## 20. What the Important Parts of `openclaw.json` Should Look Like

Your exact file will include your own secrets and extra settings.

The important parts should look roughly like this:

```json
{
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
      "streaming": false
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

Do **not** paste real tokens from somebody else.

Use your own:

- `YOUR_TELEGRAM_BOT_TOKEN`
- `YOUR_OPENCLAW_GATEWAY_TOKEN`
- your own local paths

## 21. Create the Startup and Reply Instruction Files

These two files are part of the validated setup.

### 21.1 Create `BOOT.md`

This file tells OpenClaw what to do on gateway startup.

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

### 21.2 Create or update `AGENTS.md`

This file gives the main reply rule in plain language.

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

## 22. Run OpenClaw Health Checks

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
- `ninjaclawbot_control` shows as eligible
- NinjaClawBot hooks appear in the hook list
- the plugin shows as loaded from your local project path

## 23. Start OpenClaw

Start the gateway:

```bash
openclaw gateway start
openclaw gateway status
```

If you want a reliable live log without gateway pairing issues, do **not**
depend on `openclaw logs --follow`. Use the raw log file instead:

```bash
tail -f "$(ls -t /tmp/openclaw/openclaw-*.log | head -n1)"
```

## 24. Final Validation

This is the simplest full validation flow for the working build.

### 24.1 Startup validation

Run:

```bash
openclaw gateway restart
```

Then watch the raw log file:

```bash
tail -f "$(ls -t /tmp/openclaw/openclaw-*.log | head -n1)"
```

Expected result:

- the startup greeting appears once
- the robot then returns to idle

### 24.2 Telegram reply validation

Start a fresh session in Telegram:

```text
/new
```

Then send:

```text
hello
```

Expected result:

- the robot shows a reply expression
- the answer is not text-only anymore
- after the reply, the robot returns to idle

If you want to confirm the tool call from the Pi terminal, run:

```bash
grep -iE 'ninjaclawbot_reply|ninjaclawbot_perform_expression|tools' "$(ls -t /tmp/openclaw/openclaw-*.log | head -n1)" | tail -n 30
```

### 24.3 Shutdown validation

Run:

```bash
openclaw gateway stop
openclaw gateway status
```

Expected result:

- the robot shows the sleepy expression once
- the display powers down after the sleepy expression finishes

## 25. Troubleshooting

### 25.1 `spawn uv ENOENT`

Meaning:

- OpenClaw cannot find `uv`

Fix:

```bash
command -v uv
```

Then confirm `plugins.entries.ninjaclawbot.config.uvCommand` matches that full
path.

### 25.2 `openclaw logs --follow` says pairing required

Meaning:

- your gateway CLI session is not authenticated for that log command

Use this instead:

```bash
tail -f "$(ls -t /tmp/openclaw/openclaw-*.log | head -n1)"
```

### 25.3 Startup greeting does not appear

Check:

```bash
openclaw hooks info boot-md
cat "$OPENCLAW_WORKSPACE/BOOT.md"
```

If `BOOT.md` is missing or empty, recreate it from Section 21.1.

### 25.4 Replies are still text-only

Run:

```bash
cat "$OPENCLAW_WORKSPACE/AGENTS.md"
grep -iE 'ninjaclawbot_reply|tool' "$(ls -t /tmp/openclaw/openclaw-*.log | head -n1)" | tail -n 30
```

Then:

- start a fresh Telegram session with `/new`
- try again

If `ninjaclawbot_reply` never appears in the log, the model is still ignoring
the tool instruction and the next repo-side hardening step is needed.

### 25.5 `git pull` fails because of `__pycache__` files

Run:

```bash
cd ~/NinjaClawBot
git ls-files | grep '/__pycache__/.*\.pyc$' | xargs -r git restore --
find ninjaclawbot/src -type d -name __pycache__ -prune -exec rm -rf {} +
git ls-files | grep '/__pycache__/.*\.pyc$' | xargs -r git restore --
git pull
```

## 26. What to Keep Private

Never publish these values:

- Telegram bot token
- OpenClaw gateway token
- pairing codes
- API keys
- any OAuth session data

If you share your `openclaw.json` with someone, replace secrets with placeholders
such as:

- `YOUR_TELEGRAM_BOT_TOKEN`
- `YOUR_OPENCLAW_GATEWAY_TOKEN`
- `YOUR_API_KEY`

## 27. Quick Success Checklist

You are done when all of these are true:

- `uv` works
- the hardware libraries work locally
- `ninjaclawbot` expressions work locally
- OpenClaw loads the NinjaClawBot plugin
- `boot-md` is enabled
- the startup greeting appears
- the Telegram reply shows a robot expression
- the shutdown sleepy powers down the display
