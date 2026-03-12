# NinjaClawBot Installation Guide

This guide is the **single source of truth** for installing, setting up, calibrating, and testing the full NinjaClawBot project on a Raspberry Pi 5.

Use this guide if you want to:

- install the whole project from scratch
- set up the `pi5*` hardware libraries correctly
- calibrate the robot before integrated use
- test `ninjaclawbot` from the project root
- connect NinjaClawBot to the OpenClaw agent

If you want a shorter project overview, read [README.md](README.md).

If you want advanced developer details, read [DevelopmentGuide.md](DevelopmentGuide.md).

## 1. What You Need

Before you start, make sure you have:

- a Raspberry Pi 5
- Raspberry Pi OS Bookworm or newer
- internet access
- a keyboard, screen, or remote shell access
- the NinjaClawBot repository
- the robot hardware you want to use

Optional hardware covered by this guide:

- passive buzzer for [`pi5buzzer`](pi5buzzer/README.md)
- hobby servos for [`pi5servo`](pi5servo/README.md)
- ST7789V SPI display (small SPI screen) for [`pi5disp`](pi5disp/README.md)
- VL53L0X Time-of-Flight sensor (laser distance sensor) for [`pi5vl53l0x`](pi5vl53l0x/README.md)
- DFRobot Raspberry Pi IO Expansion HAT (DFR0566) if you want HAT-based servo control

## 2. Safety Before Powering Hardware

Please read these simple safety rules first:

- power off the Raspberry Pi before rewiring GPIO (general-purpose input/output), SPI (display bus), or I2C (sensor bus) hardware
- use **external servo power** for real servo testing
- keep a **common ground** (shared electrical ground) between the Raspberry Pi and external servo power
- start with **one servo only** for the first movement test
- keep servo arms free from obstacles during calibration

## 3. Update the Raspberry Pi

This makes sure the operating system is current before installing tools.

```bash
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```

After reboot, log in again.

## 4. Install System Packages

These packages support Python builds and Raspberry Pi hardware tools.

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

What these are for:

- `git`: downloads the repository
- `curl`: downloads installers
- `python3-dev`: Python build support
- `build-essential`: compiler tools
- `swig`: needed if a low-level library must build from source
- `i2c-tools`: used to test I2C devices such as the VL53L0X and DFR0566

## 5. Enable Raspberry Pi Interfaces

NinjaClawBot uses:

- `SPI` for the display
- `I2C` for the VL53L0X and DFR0566 HAT
- `PWM` (pulse-width modulation, a timed signal used for servo control) for direct header-connected servos

Open the Raspberry Pi setup tool:

```bash
sudo raspi-config
```

Enable:

1. `Interface Options` -> `SPI` -> `Yes`
2. `Interface Options` -> `I2C` -> `Yes`

Exit the tool.

## 6. Enable PWM for Direct Raspberry Pi Servo Pins

If you plan to drive servos from the Raspberry Pi header directly, add a PWM overlay (firmware setting that enables hardware PWM pins).

Open:

```bash
sudo nano /boot/firmware/config.txt
```

For GPIO 12 and GPIO 13, add:

```ini
dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4
```

Save the file and reboot:

```bash
sudo reboot
```

If you use only the DFR0566 HAT PWM outputs, this step is not required for those HAT PWM channels.

## 7. Install `uv`

`uv` is the project’s Python package manager and virtual-environment tool.

Install it with:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then load it into the shell:

```bash
source "$HOME/.local/bin/env"
```

Check that it works:

```bash
uv --help
```

Expected result:

- a help screen appears

## 8. Install Node.js for OpenClaw

OpenClaw needs Node.js 22.12.0 or newer.

Check your current version:

```bash
node --version
npm --version
```

If Node.js is missing or too old, install Node.js 22 LTS (long-term support) before continuing.

## 9. Clone the NinjaClawBot Repository

```bash
git clone https://github.com/Nilcreator/NinjaClawBot.git
cd NinjaClawBot/"Code library"/NinjaClawbot
```

From this point on, **stay in the project root** unless a step tells you otherwise.

## 10. Install the Full Project From the Root

This is the main install step for the whole project.

```bash
uv sync --extra dev
```

This installs:

- `ninjaclawbot`
- `pi5buzzer[pi]`
- `pi5servo[pi]`
- `pi5disp[pi]`
- `pi5vl53l0x[pi]`
- development tools such as `pytest` and `ruff`

You do **not** need to install each `pi5*` library separately when using the full project.

## 11. Verify the Root Environment

Run:

```bash
uv run python -c "import ninjaclawbot, pi5buzzer, pi5servo, pi5disp, pi5vl53l0x; print('imports-ok')"
uv run ninjaclawbot --help
uv run pi5servo --help
uv run pi5buzzer --help
uv run pi5disp --help
uv run pi5vl53l0x --help
```

Expected result:

- the first command prints `imports-ok`
- all help commands work

## 12. Wire the Hardware

This guide does not repeat every wiring table in full. Use the dedicated library READMEs for detailed wiring:

- buzzer: [pi5buzzer/README.md](pi5buzzer/README.md)
- servo: [pi5servo/README.md](pi5servo/README.md)
- display: [pi5disp/README.md](pi5disp/README.md)
- distance sensor: [pi5vl53l0x/README.md](pi5vl53l0x/README.md)

Important notes:

- `pi5servo` direct PWM works best on Raspberry Pi GPIO 12 and GPIO 13 for first tests
- if you use the DFR0566 HAT PWM outputs:
  - physical `PWM0` = `hat_pwm1`
  - physical `PWM1` = `hat_pwm2`
  - physical `PWM2` = `hat_pwm3`
  - physical `PWM3` = `hat_pwm4`
- the VL53L0X should appear at I2C address `0x29`
- the DFR0566 HAT should appear at I2C address `0x10` unless you changed it

## 13. Initialize and Calibrate the `pi5*` Libraries

Do these steps in order.

### 13.1 Servo setup (`pi5servo`) - required

Servo calibration is the most important setup step for real robot motion.

Check the servo backend first:

```bash
uv run pi5servo status --no-probe --pins 12,13
```

Calibrate the direct Raspberry Pi header servos:

```bash
uv run pi5servo calib 12
uv run pi5servo calib 13
```

Or use the interactive tool:

```bash
uv run pi5servo servo-tool
```

Expected result:

- `servo.json` is created in the project root
- calibrated values are saved
- the servos move safely during calibration

If you use the DFR0566 HAT:

```bash
ls /dev/i2c-1
sudo i2cdetect -y 1
uv run pi5servo status --backend dfr0566 --pins hat_pwm1 --address 0x10 --bus-id 1
```

Expected result:

- `/dev/i2c-1` exists
- `i2cdetect` shows `10`
- the status command reports the DFR0566 path correctly

### 13.2 Buzzer setup (`pi5buzzer`) - recommended

Initialize the buzzer pin:

```bash
uv run pi5buzzer init 17
```

Expected result:

- `buzzer.json` is created in the project root
- the buzzer plays a short test sound

### 13.3 Display setup (`pi5disp`) - recommended

Initialize the display settings:

```bash
uv run pi5disp init --defaults
```

Expected result:

- `display.json` is created in the project root
- default display settings are saved

### 13.4 Distance sensor setup (`pi5vl53l0x`) - recommended if you use the sensor

Confirm the sensor is visible:

```bash
ls /dev/i2c-1
sudo i2cdetect -y 1
```

Expected result:

- `29` appears in the `i2cdetect` output

Run a quick test:

```bash
uv run pi5vl53l0x test
```

If you want offset calibration (distance correction):

```bash
uv run pi5vl53l0x calibrate --distance 200 --count 10
```

Expected result:

- `vl53l0x.json` is created in the project root if you run calibration

## 14. Test Each `pi5*` Library From the Project Root

### 14.1 Test the buzzer

```bash
uv run pi5buzzer info --health-check
uv run pi5buzzer beep 440 0.3
```

Expected result:

- health information is printed
- the buzzer plays one short tone

### 14.2 Test the display

```bash
uv run pi5disp info
uv run pi5disp clear
uv run pi5disp text "HELLO"
```

Expected result:

- the display responds without error
- the screen clears
- the text appears

### 14.3 Test the distance sensor

```bash
uv run pi5vl53l0x status
uv run pi5vl53l0x get --count 5 --interval 0.5
```

Expected result:

- the driver reports sensor status
- repeated distance readings appear

### 14.4 Test the servos

Start with one servo only if this is your first motion test.

```bash
uv run pi5servo move 12 center
uv run pi5servo move 12 min
uv run pi5servo move 12 max
```

Expected result:

- the servo moves correctly to each position

For two direct GPIO servos:

```bash
uv run pi5servo move 12 center
uv run pi5servo move 13 center
uv run pi5servo cmd "F_12:30/13:-30"
uv run pi5servo cmd "F_12:0/13:0"
```

Expected result:

- both servos move
- both servos return to center

## 15. Test `ninjaclawbot` From the Project Root

Run the safe checks first:

```bash
uv run ninjaclawbot health-check
uv run ninjaclawbot list-assets
uv run ninjaclawbot list-capabilities
```

Expected result:

- the robot returns structured JSON
- connected hardware shows `available: true`
- the project reports supported actions, reply states, and built-in expressions

Test the expression engine:

```bash
uv run ninjaclawbot perform-expression idle
uv run ninjaclawbot perform-expression greeting
uv run ninjaclawbot perform-reply --reply-state greeting "Hello"
uv run ninjaclawbot set-idle
```

Expected result:

- built-in expressions run correctly
- reply-state policy chooses the correct face and sound
- `set-idle` starts the idle face

Test the tools:

```bash
uv run ninjaclawbot movement-tool
uv run ninjaclawbot expression-tool
```

Expected result:

- both interactive tools open correctly
- leaving `expression-tool` returns to the shell cleanly

## 16. Install OpenClaw

For the complete, step-by-step OpenClaw installation process, follow the
dedicated `NinjaClawAgent` guide:

- [NinjaClawAgent README](https://github.com/Nilcreator/NinjaClawAgent/blob/main/README.md)

That guide covers:

- Raspberry Pi system setup
- Node.js (JavaScript runtime) installation
- OpenClaw installation
- OpenClaw onboarding
- the main OpenClaw configuration file setup

After you finish the OpenClaw installation in that guide, return here to connect
OpenClaw to NinjaClawBot.

## 17. Find the Real NinjaClawBot Paths and Back Up OpenClaw

You need two real paths from your Raspberry Pi:

- the NinjaClawBot project root path
- the NinjaClawBot OpenClaw plugin folder path

Important path rule:

- the plugin folder is inside the **NinjaClawBot** project
- it is **not** inside the separate `NinjaClawAgent` repository

### 17.1 If you already know where NinjaClawBot is

Move into the NinjaClawBot folder:

```bash
cd /path/to/NinjaClawbot
```

Print the real project root path:

```bash
pwd
```

Print the real plugin folder path:

```bash
realpath integrations/openclaw/ninjaclawbot-plugin
```

### 17.2 If you do not know where NinjaClawBot is

Search your home folder:

```bash
find ~ -type d \( -name NinjaClawbot -o -name NinjaClawBot \) 2>/dev/null
```

Then move into the correct folder and run:

```bash
pwd
realpath integrations/openclaw/ninjaclawbot-plugin
```

### 17.3 Save the paths in shell variables

After you are inside the NinjaClawBot project root, run:

```bash
export NINJACLAWBOT_ROOT="$(pwd)"
export NINJACLAWBOT_PLUGIN="$(realpath integrations/openclaw/ninjaclawbot-plugin)"
echo "$NINJACLAWBOT_ROOT"
echo "$NINJACLAWBOT_PLUGIN"
```

Expected result:

- the first line is the full NinjaClawBot project root path
- the second line is the full NinjaClawBot plugin folder path

### 17.4 Find and back up the OpenClaw configuration file

Typical Raspberry Pi path:

- `~/.openclaw/openclaw.json`

OpenClaw normally uses this file directly. Some OpenClaw versions also support
helper subcommands for config inspection, but you do not need them for this
guide.

Back up the current file before changing it:

```bash
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup.$(date +%Y%m%d-%H%M%S)
```

## 18. Add the NinjaClawBot Plugin to the OpenClaw Configuration File

### 18.1 Recommended: patch the existing OpenClaw config safely

The command below updates your current `openclaw.json` without removing your
existing OpenClaw settings such as:

- login settings
- model settings
- Telegram settings
- gateway settings

Run this from the Raspberry Pi terminal after Section 17:

```bash
python3 - <<'PY'
import json
import os
from pathlib import Path

config_path = Path.home() / ".openclaw" / "openclaw.json"
root = os.environ["NINJACLAWBOT_ROOT"]
plugin = os.environ["NINJACLAWBOT_PLUGIN"]

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
]

with config_path.open("r", encoding="utf-8") as handle:
    data = json.load(handle)

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
ninjaclawbot_entry = entries.setdefault("ninjaclawbot", {})
ninjaclawbot_entry["enabled"] = True
ninjaclawbot_config = ninjaclawbot_entry.setdefault("config", {})
ninjaclawbot_config["projectRoot"] = root

agents = data.setdefault("agents", {})
agent_list = agents.setdefault("list", [])
main_agent = next((item for item in agent_list if item.get("id") == "main"), None)
if main_agent is None:
    main_agent = {"id": "main"}
    agent_list.append(main_agent)

tools = main_agent.setdefault("tools", {})
allow = tools.setdefault("allow", [])
for tool_name in tool_names:
    if tool_name not in allow:
        allow.append(tool_name)

with config_path.open("w", encoding="utf-8") as handle:
    json.dump(data, handle, indent=2)
    handle.write("\n")

print(f"Updated {config_path}")
print(f"projectRoot = {root}")
print(f"pluginPath = {plugin}")
PY
```

What this command does:

- adds trusted plugin ids to `plugins.allow`
- adds the NinjaClawBot plugin folder path to `plugins.load.paths`
- enables the `ninjaclawbot` plugin entry
- sets the plugin `projectRoot`
- adds the NinjaClawBot tool names to the `main` agent allow list
- keeps your existing personal settings in the same file

### 18.2 Check the updated config

Open the file to confirm the result:

```bash
nano ~/.openclaw/openclaw.json
```

The important NinjaClawBot parts should now look like this:

```json
{
  "plugins": {
    "allow": [
      "telegram",
      "ninjaclawbot"
    ],
    "load": {
      "paths": [
        "/absolute/path/to/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin"
      ]
    },
    "entries": {
      "ninjaclawbot": {
        "enabled": true,
        "config": {
          "projectRoot": "/absolute/path/to/NinjaClawbot"
        }
      }
    }
  },
  "agents": {
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
            "ninjaclawbot_stop_all"
          ]
        }
      }
    ]
  }
}
```

### 18.3 Full reference template for a new `openclaw.json`

Use this only if you are building a new OpenClaw config file from scratch.

If you already have a working OpenClaw setup, use the patch command in
Section 18.1 instead so you do not lose your current settings.

Replace every placeholder with your own real value.

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
  "models": {
    "providers": {
      "ollama": {
        "baseUrl": "http://127.0.0.1:11434/v1",
        "apiKey": "YOUR_MODEL_PROVIDER_API_KEY_OR_LOCAL_TAG",
        "api": "openai-completions",
        "models": [
          {
            "id": "YOUR_MODEL_ID",
            "name": "YOUR_MODEL_NAME"
          }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "openai-codex/gpt-5.3-codex"
      },
      "models": {
        "openai-codex/gpt-5.3-codex": {}
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
            "ninjaclawbot_stop_all"
          ]
        }
      }
    ]
  },
  "commands": {
    "native": "auto",
    "nativeSkills": "auto",
    "restart": true,
    "ownerDisplay": "raw"
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
    },
    "tailscale": {
      "mode": "off",
      "resetOnExit": false
    }
  },
  "skills": {
    "install": {
      "nodeManager": "npm"
    },
    "entries": {}
  },
  "plugins": {
    "allow": [
      "telegram",
      "ninjaclawbot"
    ],
    "load": {
      "paths": [
        "/absolute/path/to/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin"
      ]
    },
    "entries": {
      "telegram": {
        "enabled": true
      },
      "ninjaclawbot": {
        "enabled": true,
        "config": {
          "projectRoot": "/absolute/path/to/NinjaClawbot"
        }
      }
    }
  },
  "tools": {
    "media": {
      "audio": {
        "enabled": true,
        "maxBytes": 20971520,
        "scope": {
          "default": "deny",
          "rules": [
            {
              "action": "allow",
              "match": {
                "chatType": "direct"
              }
            }
          ]
        },
        "models": [
          {
            "type": "cli",
            "command": "/home/YOUR_USERNAME/.local/bin/whisper",
            "args": [
              "--model",
              "base",
              "--language",
              "zh",
              "--output_format",
              "txt",
              "--output_dir",
              "/tmp",
              "{{MediaPath}}"
            ]
          }
        ]
      }
    }
  }
}
```

## 19. Start OpenClaw

Start the OpenClaw gateway service:

```bash
openclaw gateway start
```

Check its status:

```bash
openclaw gateway status
```

If you want to run OpenClaw in the foreground and watch the live log output, use:

```bash
openclaw gateway
```

If you plan to connect OpenClaw to Telegram or another messaging channel, follow
the channel setup steps from the `NinjaClawAgent` guide you used in Section 16.

## 20. First OpenClaw-to-NinjaClawBot Tests

Start with safe robot actions only.

Test in this order:

1. run the OpenClaw tool that maps to `ninjaclawbot_health`
2. run the OpenClaw tool that maps to `ninjaclawbot_capabilities`
3. run a greeting reply through `ninjaclawbot_reply`
4. run `ninjaclawbot_set_idle`
5. only after that, test saved expressions and saved movements

Expected result:

- OpenClaw can call the plugin tools
- the plugin calls `ninjaclawbot` from the project root
- the robot display and buzzer respond
- the robot returns to idle when the temporary reply ends

## 21. Safe First Examples With OpenClaw

Good first examples:

- greeting the user
  - OpenClaw should use `reply_state: "greeting"`
- asking for clarification
  - OpenClaw should use `reply_state: "asking_clarification"`
- saying it cannot answer
  - OpenClaw should use `reply_state: "cannot_answer"` or `reply_state: "confusing"`
- task completed
  - OpenClaw should use `reply_state: "success"`

Avoid these until basic tests pass:

- direct servo movement through OpenClaw
- repeated movement loops
- mixed movement plus expression plus sound sequences

## 22. Troubleshooting

### `uv sync --extra dev` fails

Check:

- internet connection
- `uv` is installed
- Python build packages were installed in Step 4

### Servo does not move

Check:

- `servo.json` exists
- the servo was calibrated
- PWM overlay was added for direct GPIO servo control
- servo power is connected correctly
- if using DFR0566 PWM, check `i2cdetect -y 1` for `10`

### Display does not show anything

Check:

- SPI is enabled
- `display.json` exists
- the display wiring matches the `pi5disp` guide
- `uv run pi5disp info` works from the project root

### Distance sensor is not found

Check:

- I2C is enabled
- `i2cdetect -y 1` shows `29`
- the sensor is wired for 3.3V logic

### OpenClaw cannot use NinjaClawBot

Check:

- OpenClaw is installed
- `plugins.allow` contains `ninjaclawbot`
- the plugin path in the config is correct
- `plugins.entries.ninjaclawbot.enabled` is `true`
- the plugin `projectRoot` points to the NinjaClawBot project root
- the OpenClaw agent allowlist includes the `ninjaclawbot_*` tool names
- the plugin folder passes `npm run typecheck` and `npm test`
- `uv run ninjaclawbot list-capabilities` works at the project root

## 23. Where To Read More

- project overview: [README.md](README.md)
- advanced developer guide: [DevelopmentGuide.md](DevelopmentGuide.md)
- buzzer details: [pi5buzzer/README.md](pi5buzzer/README.md)
- servo details: [pi5servo/README.md](pi5servo/README.md)
- display details: [pi5disp/README.md](pi5disp/README.md)
- distance sensor details: [pi5vl53l0x/README.md](pi5vl53l0x/README.md)
- enhancement roadmap: [EnhancementPlan.md](EnhancementPlan.md)
