# NinjaClawBot Installation Guide

## Quick Links

- [1. What you will build](#1-what-you-will-build)
- [2. What you need](#2-what-you-need)
- [3. Safety first](#3-safety-first)
- [4. Prepare the Raspberry Pi](#4-prepare-the-raspberry-pi)
- [5. Install OpenClaw](#5-install-openclaw)
- [6. Clone and install NinjaClawBot](#6-clone-and-install-ninjaclawbot)
- [7. Wire the hardware](#7-wire-the-hardware)
- [8. Run the guided setup tools](#8-run-the-guided-setup-tools)
- [9. Run quick local tests](#9-run-quick-local-tests)
- [10. Save paths and back up OpenClaw config](#10-save-paths-and-back-up-openclaw-config)
- [11. Patch `openclaw.json` safely](#11-patch-openclawjson-safely)
- [12. Create `BOOT.md` and `AGENTS.md`](#12-create-bootmd-and-agentsmd)
- [13. Start OpenClaw and run diagnostics](#13-start-openclaw-and-run-diagnostics)
- [14. Validate with Telegram](#14-validate-with-telegram)
- [Appendix A: Raspberry Pi setup help](#appendix-a-raspberry-pi-setup-help)
- [Appendix B: OpenClaw setup help](#appendix-b-openclaw-setup-help)
- [Appendix C: Hardware setup help](#appendix-c-hardware-setup-help)
- [Appendix D: Local test help](#appendix-d-local-test-help)
- [Appendix E: OpenClaw validation help](#appendix-e-openclaw-validation-help)
- [Appendix F: Sanitized `openclaw.json` example](#appendix-f-sanitized-openclawjson-example)

## 1. What You Will Build

Purpose:
- understand what this guide will give you when you finish

At the end of this guide, you will have:

- a Raspberry Pi 5 with all NinjaClawBot libraries installed
- guided hardware setup completed with interactive tools
- a working `ninjaclawbot` robot layer
- OpenClaw connected to the robot
- a validated flow where:
  - startup shows a greeting
  - Telegram messages trigger robot reactions
  - Telegram still receives normal text replies
  - shutdown shows a sleepy expression and then turns the display off

## 2. What You Need

Purpose:
- confirm you have the right hardware and software before you start

You need:

- Raspberry Pi 5
- Raspberry Pi OS
- internet connection
- a small SPI display supported by `pi5disp`
- at least one servo supported by `pi5servo`
- one buzzer supported by `pi5buzzer`
- one VL53L0X distance sensor for `pi5vl53l0x`
- OpenClaw already installed or ready to install

Helpful words:

- `GPIO`: control pins on the Raspberry Pi
- `SPI`: fast pin connection used by displays
- `I2C`: two-wire connection used by sensors and some controller boards
- `PWM`: timed signal used to move servos

## 3. Safety First

Purpose:
- avoid damaging your Raspberry Pi, servos, or display while testing

Please keep these rules in mind:

- do not force a servo arm by hand while power is on
- use a separate safe power source for stronger servos if needed
- test one hardware part at a time
- stop immediately if a servo moves in an unexpected way
- start with display, buzzer, and sensor checks before larger motion tests

## 4. Prepare The Raspberry Pi

Purpose:
- update the system and install the base tools the project needs

### 4.1 Update the system

```bash
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```

### 4.2 Install basic packages

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

### 4.3 Enable hardware interfaces

Open the Raspberry Pi setup menu:

```bash
sudo raspi-config
```

Enable:

1. `Interface Options` -> `SPI` -> `Yes`
2. `Interface Options` -> `I2C` -> `Yes`

If you plan to drive servos directly from GPIO 12 and GPIO 13, also add the PWM overlay:

```bash
sudo nano /boot/firmware/config.txt
```

Add this line:

```ini
dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4
```

Then reboot:

```bash
sudo reboot
```

### 4.4 Install `uv`

`uv` is the Python environment tool used by this project.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"
command -v uv
uv --version
```

Need help later?
- [Appendix A: Raspberry Pi setup help](#appendix-a-raspberry-pi-setup-help)

## 5. Install OpenClaw

Purpose:
- get OpenClaw working before you connect NinjaClawBot to it

Use these references in this order:

- Key Raspberry Pi companion reference:
  - [NinjaClawAgent README](https://github.com/Nilcreator/NinjaClawAgent/blob/main/README.md)
- Official references:
  - [OpenClaw install guide](https://docs.openclaw.ai/start/installation)
  - [OpenClaw onboarding guide](https://docs.openclaw.ai/start/onboarding)

The NinjaClawAgent guide is the easiest companion guide to follow on Raspberry Pi. The official OpenClaw pages are still the source of truth for the latest installer and onboarding behavior.

### 5.1 Install OpenClaw

```bash
curl -fsSL https://openclaw.ai/install.sh | bash
```

### 5.2 Run onboarding

```bash
openclaw onboard --install-daemon
```

During onboarding:

- choose your normal provider and model settings
- enable Telegram if you want Telegram as the chat interface
- allow the daemon install so OpenClaw can run as a background service

### 5.3 Verify the install

```bash
openclaw doctor
openclaw status
```

When you continue with this guide, you should already have:

- the `openclaw` command
- a working `~/.openclaw/openclaw.json`
- your own model settings
- your own Telegram settings if you want Telegram replies

Important:

- do not overwrite your whole `openclaw.json` with a random template
- this guide patches your existing file safely
- never paste real API keys, pairing codes, or tokens into shared screenshots or notes

Need help later?
- [Appendix B: OpenClaw setup help](#appendix-b-openclaw-setup-help)

## 6. Clone And Install NinjaClawBot

Purpose:
- install the full project workspace in one clean step

### 6.1 Clone the repo

```bash
cd ~
git clone https://github.com/Nilcreator/NinjaClawBot.git
cd ~/NinjaClawBot
```

### 6.2 Install the whole workspace

```bash
cd ~/NinjaClawBot
uv sync --extra dev
```

### 6.3 Verify the install

```bash
cd ~/NinjaClawBot
uv run python -c "import ninjaclawbot, pi5buzzer, pi5servo, pi5disp, pi5vl53l0x; print('imports-ok')"
uv run ninjaclawbot --help
uv run pi5servo --help
uv run pi5disp --help
uv run pi5buzzer --help
uv run pi5vl53l0x --help
```

Expected result:

- `imports-ok` is printed
- each help command opens normally

Need help later?
- [Appendix A: Raspberry Pi setup help](#appendix-a-raspberry-pi-setup-help)

## 7. Wire The Hardware

Purpose:
- connect the robot before running the guided setup tools

Use these library guides for wiring details:

- Servo: [pi5servo/README.md](pi5servo/README.md)
- Display: [pi5disp/README.md](pi5disp/README.md)
- Buzzer: [pi5buzzer/README.md](pi5buzzer/README.md)
- Distance sensor: [pi5vl53l0x/README.md](pi5vl53l0x/README.md)

Quick notes:

- direct servo testing is easiest on GPIO 12 or GPIO 13
- the VL53L0X usually appears on I2C address `0x29`
- some servo controller HATs appear on I2C address `0x10`

Need help later?
- [Appendix C: Hardware setup help](#appendix-c-hardware-setup-help)

## 8. Run The Guided Setup Tools

Purpose:
- initialize and test each hardware module using the safest interactive tools first

Run these in order.

### 8.1 Servo setup

```bash
cd ~/NinjaClawBot
uv run pi5servo servo-tool
```

Inside the tool:

1. choose the real servo endpoint you wired
2. run calibration
3. save the result
4. run one very small test move

Expected result:

- `servo.json` is created
- the servo moves safely

### 8.2 Buzzer setup

```bash
cd ~/NinjaClawBot
uv run pi5buzzer buzzer-tool
```

Inside the tool:

1. initialize the buzzer pin
2. play a short test beep
3. try one emotion sound

Expected result:

- `buzzer.json` is created
- the buzzer plays a short sound

### 8.3 Display setup

```bash
cd ~/NinjaClawBot
uv run pi5disp init
uv run pi5disp display-tool
```

Inside the tool:

1. confirm the display settings
2. show text like `HELLO`
3. confirm the screen rotation looks correct

Then export those same settings into the root project file used by `ninjaclawbot`:

```bash
cd ~/NinjaClawBot
uv run pi5disp config export "$PWD/display.json"
```

Expected result:

- the display works in `display-tool`
- the root `display.json` is created

Why this matters:

- `pi5disp` has its own display config
- `ninjaclawbot` prefers the root `display.json`
- exporting here keeps both layers in sync

### 8.4 Distance sensor setup

First check the sensor on I2C:

```bash
ls /dev/i2c-1
sudo i2cdetect -y 1
```

You should normally see `29`.

Then run the guided tool:

```bash
cd ~/NinjaClawBot
uv run pi5vl53l0x sensor-tool
```

Inside the tool:

1. check status
2. take a few readings
3. run offset calibration if needed

Expected result:

- the sensor returns readings
- `vl53l0x.json` is created if you save calibration

Need help later?
- [Appendix C: Hardware setup help](#appendix-c-hardware-setup-help)

## 9. Run Quick Local Tests

Purpose:
- confirm the full robot layer works before adding OpenClaw

### 9.1 Run direct checks

```bash
cd ~/NinjaClawBot
uv run ninjaclawbot health-check
uv run ninjaclawbot perform-expression greeting
uv run ninjaclawbot perform-reply --reply-state greeting "Hello"
uv run ninjaclawbot set-idle
```

### 9.2 Run the interactive expression tool

```bash
cd ~/NinjaClawBot
uv run ninjaclawbot expression-tool
```

Inside the tool:

1. list built-in expressions
2. preview `greeting`
3. preview `idle`
4. exit cleanly

### 9.3 Run the interactive movement tool

```bash
cd ~/NinjaClawBot
uv run ninjaclawbot movement-tool
```

Inside the tool:

1. confirm the tool opens
2. only run a movement if your servo is already calibrated and mounted safely

### 9.4 Confirm the display config path

```bash
cd ~/NinjaClawBot
uv run ninjaclawbot health-check | grep -iE '"config_path"|"using_root_config"' || true
```

Expected result:

- expressions show correctly on the display
- `movement-tool` opens normally
- `using_root_config` is `true`

Need help later?
- [Appendix D: Local test help](#appendix-d-local-test-help)

## 10. Save Paths And Back Up OpenClaw Config

Purpose:
- collect the exact local paths needed by the plugin
- keep a backup of your working OpenClaw config

### 10.1 Save the important paths

```bash
cd ~/NinjaClawBot
export NINJACLAWBOT_ROOT="$(pwd)"
export NINJACLAWBOT_PLUGIN="$(realpath integrations/openclaw/ninjaclawbot-plugin)"
export NINJACLAWBOT_UV="$(command -v uv)"
printf '%s\n%s\n%s\n' "$NINJACLAWBOT_ROOT" "$NINJACLAWBOT_PLUGIN" "$NINJACLAWBOT_UV"
```

### 10.2 Back up `openclaw.json`

```bash
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup.$(date +%Y%m%d-%H%M%S)
```

Need help later?
- [Appendix B: OpenClaw setup help](#appendix-b-openclaw-setup-help)

## 11. Patch `openclaw.json` Safely

Purpose:
- add NinjaClawBot without overwriting your own secrets and model settings

This patch only updates the parts NinjaClawBot needs:

- the main agent tool allowlist
- internal `boot-md`
- the NinjaClawBot skill entry
- plugin allow/load/entry settings

It does not overwrite your existing:

- model provider settings
- Telegram bot token
- gateway token
- workspace history
- plugin install records

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
    "ninjaclawbot_diagnostics",
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
PY
```

Keep your own real values private. Never share:

- Telegram bot tokens
- OpenClaw gateway tokens
- API keys
- pairing codes

Need help later?
- [Appendix B: OpenClaw setup help](#appendix-b-openclaw-setup-help)
- [Appendix F: Sanitized `openclaw.json` example](#appendix-f-sanitized-openclawjson-example)

## 12. Create `BOOT.md` And `AGENTS.md`

Purpose:
- make the startup greeting and reply behavior reliable

### 12.1 Create `BOOT.md`

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

### 12.2 Create or update `AGENTS.md`

```bash
python3 - <<'PY'
from pathlib import Path
import os

path = Path(os.environ["OPENCLAW_WORKSPACE"]) / "AGENTS.md"
block = """
## NinjaClawBot Reply Policy

When replying to users in Telegram or other chat channels:
- first call `ninjaclawbot_reply` to animate the robot for the answer
- then send the normal visible text reply to the user in the same turn
- choose the closest `reply_state` for the tone of the answer
- do not treat the tool call itself as the final visible chat reply
- if `ninjaclawbot_reply` fails, still send the normal visible text reply
- after normal replies, let the lifecycle return the robot to idle
""".lstrip()

existing = path.read_text(encoding="utf-8") if path.exists() else ""
marker = "## NinjaClawBot Reply Policy"
if marker in existing:
    start = existing.index(marker)
    existing = existing[:start].rstrip() + "\n\n"
if existing and not existing.endswith("\n"):
    existing += "\n"
existing += block
path.write_text(existing, encoding="utf-8")
print(path)
PY
```

Need help later?
- [Appendix B: OpenClaw setup help](#appendix-b-openclaw-setup-help)

## 13. Start OpenClaw And Run Diagnostics

Purpose:
- confirm the plugin, workspace files, and bridge are healthy before Telegram testing

### 13.1 Run basic OpenClaw checks

```bash
openclaw doctor --fix
openclaw hooks enable boot-md
openclaw hooks info boot-md
openclaw skills list --eligible | grep -iE 'ninjaclawbot_control|ninjaclawbot' || true
openclaw hooks list --verbose | grep -iE 'boot-md|ninjaclawbot|message_received|agent_end|gateway_stop' || true
openclaw plugins info ninjaclawbot
```

### 13.2 Start the gateway

```bash
openclaw gateway start
openclaw gateway status
```

If normal log follow is blocked, use the raw log file:

```bash
tail -f "$(ls -t /tmp/openclaw/openclaw-*.log | head -n1)"
```

### 13.3 Run `ninjaclawbot_diagnostics`

This is an OpenClaw tool. It is not a local `uv` command.

```bash
eval "$(
python3 - <<'PY'
import json
import shlex
from pathlib import Path

cfg = json.load((Path.home() / ".openclaw" / "openclaw.json").open("r", encoding="utf-8"))
gateway = cfg.get("gateway", {})
auth = gateway.get("auth", {})
port = int(gateway.get("port", 18789))
token = str(auth.get("token", "")).strip()

print(f"export OPENCLAW_URL=http://127.0.0.1:{port}")
print(f"export OPENCLAW_TOKEN={shlex.quote(token or 'YOUR_OPENCLAW_GATEWAY_TOKEN')}")
PY
)"

curl -sS "$OPENCLAW_URL/tools/invoke" \
  -H "Authorization: Bearer $OPENCLAW_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "tool": "ninjaclawbot_diagnostics",
    "args": {},
    "sessionKey": "main"
  }' | python3 -m json.tool
```

Expected result:

- `summary.state` is usually `healthy` or `warning`
- `bridge.status` is usually `healthy`
- `deployment.status` is `ready` or at least not `misconfigured`
- `startup.trackingMode` is usually `workspace_boot_md`
- `startup.effectiveCompleted` is `true`

Need help later?
- [Appendix E: OpenClaw validation help](#appendix-e-openclaw-validation-help)

## 14. Validate With Telegram

Purpose:
- prove the full user-facing workflow works

### 14.1 Startup check

```bash
openclaw gateway restart
```

Expected result:

- the robot shows one startup greeting
- the robot returns to idle

### 14.2 Reply check

In Telegram:

1. send `/new`
2. send `hello`
3. send one or two more short messages

Expected result:

- the robot shows a matching expression
- Telegram still receives a normal text reply
- the robot returns to idle after the reply

### 14.3 Shutdown check

```bash
openclaw gateway stop
openclaw gateway status
```

Expected result:

- the robot shows the sleepy expression once
- the display turns off after sleepy finishes

### 14.4 Optional direct local checks

```bash
cd ~/NinjaClawBot
uv run ninjaclawbot health-check
uv run ninjaclawbot expression-tool
uv run ninjaclawbot movement-tool
```

If all of the above work, your NinjaClawBot build is ready.

Need help later?
- [Appendix E: OpenClaw validation help](#appendix-e-openclaw-validation-help)

## Appendix A. Raspberry Pi Setup Help

### Troubleshooting

- `uv` command missing:
  - run `source "$HOME/.local/bin/env"`
  - then run `command -v uv`
- SPI or I2C device missing:
  - reopen `sudo raspi-config`
  - confirm SPI and I2C are enabled
- PWM pins not working:
  - recheck `/boot/firmware/config.txt`
  - reboot after editing

### Alternative commands

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv
python3 --version
```

## Appendix B. OpenClaw Setup Help

### Troubleshooting

- `openclaw doctor --fix` complains about unsupported keys:
  - remove optional old NinjaClawBot config keys such as:
    - `enableAlwaysOn`
    - `enableStartupGreeting`
    - `enableAutoThinking`
    - `enableShutdownSequence`
    - `plugins.entries.ninjaclawbot.hooks`
- OpenClaw says `spawn uv ENOENT`:
  - set `uvCommand` to the absolute result of `command -v uv`
- startup greeting missing:
  - check `boot-md`
  - check workspace `BOOT.md`
  - check `ninjaclawbot_diagnostics`

### Alternative commands

```bash
openclaw plugins install -l ~/NinjaClawBot/integrations/openclaw/ninjaclawbot-plugin
openclaw plugins info ninjaclawbot
openclaw hooks list --verbose
openclaw skills list --eligible
```

## Appendix C. Hardware Setup Help

### Troubleshooting

- display works in `display-tool` but not in `expression-tool`:
  - rerun:

```bash
cd ~/NinjaClawBot
uv run pi5disp config export "$PWD/display.json"
uv run ninjaclawbot health-check
```

- sensor does not appear at `29`:
  - recheck wiring
  - rerun `sudo i2cdetect -y 1`
- servo behaves dangerously:
  - stop immediately
  - recalibrate with `servo-tool`

### Alternative commands

```bash
cd ~/NinjaClawBot
uv run pi5servo calib 12
uv run pi5buzzer status --test
uv run pi5disp demo
uv run pi5vl53l0x status
```

## Appendix D. Local Test Help

### Troubleshooting

- `expression-tool` opens but faces look wrong:
  - export display config again to root `display.json`
- `movement-tool` opens but movement is risky:
  - do not run movements yet
  - go back to `pi5servo servo-tool`
- `health-check` shows wrong display config path:
  - rerun the display export command

### Alternative commands

```bash
cd ~/NinjaClawBot
uv run ninjaclawbot list-capabilities
uv run ninjaclawbot perform-expression greeting
uv run ninjaclawbot perform-reply --reply-state success "Finished"
uv run ninjaclawbot stop
uv run ninjaclawbot stop-all
```

## Appendix E. OpenClaw Validation Help

### Troubleshooting

- `ninjaclawbot_diagnostics` says tool not found:
  - add `ninjaclawbot_diagnostics` to the tool allowlist
  - restart OpenClaw
- robot reacts but Telegram has no text reply:
  - recheck workspace `AGENTS.md`
  - make sure it says:
    - first animate the robot
    - then send the normal visible text reply
- shutdown works but startup does not:
  - recheck `boot-md`
  - recheck workspace `BOOT.md`
- normal log follow is blocked:
  - use the raw log file

### Useful log commands

```bash
tail -f "$(ls -t /tmp/openclaw/openclaw-*.log | head -n1)"
grep -iE 'ninjaclawbot_reply|ninjaclawbot_diagnostics|boot-md|telegram' "$(ls -t /tmp/openclaw/openclaw-*.log | head -n1)" | tail -n 50
```

### Alternative commands

```bash
openclaw gateway restart
openclaw gateway stop
openclaw gateway status
```

## Appendix F. Sanitized `openclaw.json` Example

Use this only as a reference shape. Do not overwrite your own real file blindly.

Replace placeholders with your own values.

```json
{
  "meta": {
    "lastTouchedVersion": "YOUR_OPENCLAW_VERSION",
    "lastTouchedAt": "YYYY-MM-DDTHH:MM:SSZ"
  },
  "wizard": {
    "lastRunAt": "YYYY-MM-DDTHH:MM:SSZ",
    "lastRunVersion": "YOUR_OPENCLAW_VERSION",
    "lastRunCommand": "configure",
    "lastRunMode": "local"
  },
  "auth": {
    "profiles": {
      "openai-codex:default": {
        "provider": "openai-codex",
        "mode": "oauth"
      }
    }
  },
  "models": {
    "providers": {
      "ollama": {
        "baseUrl": "http://127.0.0.1:11434/v1",
        "apiKey": "ollama-local",
        "api": "openai-completions",
        "models": [
          {
            "id": "YOUR_LOCAL_MODEL_ID",
            "name": "YOUR_LOCAL_MODEL_NAME"
          }
        ]
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
  "agents": {
    "defaults": {
      "model": {
        "primary": "openai-codex/YOUR_MODEL_ID"
      },
      "models": {
        "openai-codex/YOUR_MODEL_ID": {}
      },
      "workspace": "/home/YOUR_USERNAME/.openclaw/workspace",
      "compaction": {
        "mode": "safeguard"
      }
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
            "ninjaclawbot_diagnostics",
            "ninjaclawbot_set_idle",
            "ninjaclawbot_stop",
            "ninjaclawbot_stop_all",
            "ninjaclawbot"
          ]
        }
      }
    ]
  },
  "tools": {
    "media": {
      "audio": {
        "enabled": true,
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
        "maxBytes": 20971520,
        "models": [
          {
            "type": "cli",
            "command": "/home/YOUR_USERNAME/.local/bin/whisper",
            "args": [
              "--model",
              "base",
              "--language",
              "YOUR_LANGUAGE_CODE",
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
  },
  "commands": {
    "native": "auto",
    "nativeSkills": "auto",
    "restart": true,
    "ownerDisplay": "raw"
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
    },
    "installs": {
      "ninjaclawbot": {
        "source": "path",
        "sourcePath": "/home/YOUR_USERNAME/NinjaClawBot/integrations/openclaw/ninjaclawbot-plugin",
        "installPath": "/home/YOUR_USERNAME/NinjaClawBot/integrations/openclaw/ninjaclawbot-plugin",
        "version": "YOUR_PLUGIN_VERSION",
        "installedAt": "YYYY-MM-DDTHH:MM:SSZ"
      }
    }
  }
}
```
