# NinjaClawBot Installation Guide

<div align="center">

**Step-by-Step Raspberry Pi 5 and OpenClaw Build Guide for NinjaClawBot**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python Workspace](https://img.shields.io/badge/workspace-uv-blue.svg)](https://docs.astral.sh/uv/)
[![Platform: Raspberry Pi 5](https://img.shields.io/badge/platform-Raspberry%20Pi%205-red.svg)](https://www.raspberrypi.com/)
[![OpenClaw Ready](https://img.shields.io/badge/OpenClaw-ready-0F766E.svg)](https://docs.openclaw.ai/)

[Project README](README.md) | [Development Guide](DevelopmentGuide.md) | [Archive](backup/README.md)

</div>

---

This guide is the full Raspberry Pi 5 setup path for NinjaClawBot.

It is designed for users who want one clear document that takes them from a
fresh Raspberry Pi to:

- the full NinjaClawBot workspace installed
- all `pi5*` hardware libraries configured through their interactive tools
- the local robot layer validated
- OpenClaw installed and connected
- Telegram reply flow validated
- optional `pi5mic` one-shot and always-on voice input validated

The guide is longer than the individual `pi5*` library READMEs because it
combines all of those libraries into one project path. The goal here is not
just to install packages, but to help you bring up the full robot stack with as
little confusion as possible.

---

## Contents

- [1. What You Will Build](#1-what-you-will-build)
- [2. What You Need](#2-what-you-need)
- [3. Safety First](#3-safety-first)
- [4. Prepare the Raspberry Pi](#4-prepare-the-raspberry-pi)
- [5. Clone and Install NinjaClawBot](#5-clone-and-install-ninjaclawbot)
- [6. Wire the Hardware](#6-wire-the-hardware)
- [7. Run the Guided Setup Tools](#7-run-the-guided-setup-tools)
- [8. Optional but Recommended: Configure `pi5mic`](#8-optional-but-recommended-configure-pi5mic)
- [9. Run Quick Local NinjaClawBot Tests](#9-run-quick-local-ninjaclawbot-tests)
- [10. Install and Onboard OpenClaw](#10-install-and-onboard-openclaw)
- [11. Integrate NinjaClawBot with OpenClaw](#11-integrate-ninjaclawbot-with-openclaw)
- [12. Validate the OpenClaw Plugin and Gateway](#12-validate-the-openclaw-plugin-and-gateway)
- [13. Validate Telegram and Voice Input End to End](#13-validate-telegram-and-voice-input-end-to-end)
- [Appendix A. Raspberry Pi Setup Help](#appendix-a-raspberry-pi-setup-help)
- [Appendix B. Hardware and Local Test Help](#appendix-b-hardware-and-local-test-help)
- [Appendix C. `pi5mic` and Voice Input Help](#appendix-c-pi5mic-and-voice-input-help)
- [Appendix D. OpenClaw and Telegram Help](#appendix-d-openclaw-and-telegram-help)
- [Appendix E. Sanitized `openclaw.json` Example](#appendix-e-sanitized-openclawjson-example)

## 1. What You Will Build

Purpose:
- understand what the finished system should look like

At the end of this guide, you should have:

- a Raspberry Pi 5 with the full NinjaClawBot workspace installed
- working standalone hardware drivers for:
  - `pi5camera`
  - `pi5servo`
  - `pi5buzzer`
  - `pi5disp`
  - `pi5vl53l0x`
  - optional but recommended: `pi5mic`
- the integrated `ninjaclawbot` robot layer working locally
- OpenClaw installed and configured
- the local NinjaClawBot plugin loaded into OpenClaw
- Telegram replies validated if Telegram is enabled
- optional voice input working through `pi5mic` in both one-shot and always-on
  modes

## 2. What You Need

Purpose:
- confirm the hardware, software, and optional accounts before you start

Required hardware:

- Raspberry Pi 5
- Raspberry Pi OS Bookworm or newer
- internet connection
- SPI display supported by `pi5disp`
- at least one servo supported by `pi5servo`
- buzzer supported by `pi5buzzer`
- VL53L0X distance sensor for `pi5vl53l0x`

Optional but strongly recommended hardware:

- Raspberry Pi camera module if you want local photos or face recognition
- USB microphone or microphone module if you may want voice input later

Required software and tools:

- a terminal with `sudo` access
- `uv` for the Python workspace
- OpenClaw Installation (https://github.com/Nilcreator/NinjaClawAgent).

Optional accounts or secrets:

- a model-provider credential for OpenClaw
- a Telegram bot token if you want Telegram as the chat interface
- a Gemini API key if you want Gemini STT in `pi5mic`
- a custom `openWakeWord` model file if you want always-on wake-word input

Helpful words:

- `GPIO`: control pins on the Raspberry Pi
- `SPI`: pin connection usually used by the display
- `I2C`: pin connection usually used by the distance sensor and some servo boards
- `PWM`: timed control signal used by servos
- `STT`: speech-to-text, meaning turning recorded speech into text

## 3. Safety First

Purpose:
- reduce the risk of damaging hardware during setup and testing

Please keep these rules in mind:

- do not force a servo arm by hand while power is on
- if a servo moves unexpectedly, stop immediately
- use a safe external power source for stronger servos when needed
- test one hardware area at a time
- do display, buzzer, sensor, and small-motion tests before running larger
  movements
- treat always-on voice input as manual and privacy-sensitive: start it yourself
  and stop it yourself

## 4. Prepare the Raspberry Pi

Purpose:
- update the operating system and install the base tools needed by the project

### 4.1 Update the system

```bash
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```

What this does:

- updates the Raspberry Pi package index
- installs the latest available system updates
- reboots into the updated system

What you should expect:

- the Pi comes back normally after reboot

### 4.2 Install basic system packages

```bash
sudo apt update
sudo apt install -y \
  git \
  curl \
  ca-certificates \
  python3-dev \
  build-essential \
  cmake \
  pkg-config \
  swig \
  i2c-tools \
  python3-picamera2 \
  libopenblas-dev \
  liblapack-dev \
  libportaudio2 \
  portaudio19-dev
```

What this does:

- installs the base build tools
- installs I2C test tools
- installs the Raspberry Pi camera stack used by `pi5camera`
- installs the PortAudio system libraries used by `pi5mic`
- installs common headers needed by Python and native extensions

What you should expect:

- the install finishes without errors

### 4.3 Enable Raspberry Pi hardware interfaces

Open the Raspberry Pi configuration menu:

```bash
sudo raspi-config
```

Enable:

1. `Interface Options -> SPI -> Yes`
2. `Interface Options -> I2C -> Yes`

If you plan to drive servos directly from GPIO 12 and GPIO 13, also add the
two-channel PWM overlay:

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

What this does:

- enables SPI for the display
- enables I2C for the distance sensor and some servo setups
- enables the direct-PWM overlay if you plan to use native GPIO PWM for servos

### 4.4 Install `uv`

`uv` is the Python environment and command runner used by this project.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"
command -v uv
uv --version
```

What this does:

- installs `uv`
- loads it into the current shell
- confirms the command works

What you should expect:

- `command -v uv` prints a path
- `uv --version` prints a version number

Need help later?
- [Appendix A. Raspberry Pi setup help](#appendix-a-raspberry-pi-setup-help)

## 5. Clone and Install NinjaClawBot

Purpose:
- install the full project workspace in one clean step

### 5.1 Clone the repository

```bash
cd ~
git clone https://github.com/Nilcreator/NinjaClawBot.git
cd ~/NinjaClawBot
```

What this does:

- downloads the project
- places you in the workspace root used by the rest of this guide

### 5.2 Install the workspace

Recommended automated install:

```bash
cd ~/NinjaClawBot
./scripts/bootstrap-rpi-workspace.sh
```

Recommended automated install if you already know that you want always-on
voice input too:

```bash
cd ~/NinjaClawBot
./scripts/bootstrap-rpi-workspace.sh --voiceinput
```

What the bootstrap installer does:

- re-checks and installs the required Raspberry Pi system packages
- installs the Raspberry Pi camera stack (`python3-picamera2`, `python3-libcamera`)
  for `pi5camera`
- recreates `.venv` from scratch with `/usr/bin/python3 -m venv --system-site-packages`
- detects the system Python version and writes it to `.python-version` so `uv`
  uses the same interpreter (prevents `uv` from downloading a different Python
  that cannot see system site-packages)
- runs `uv sync --active --extra dev`
- injects a `.pth` file into the venv that adds `/usr/lib/python3/dist-packages`
  to `sys.path`, ensuring `picamera2` and `libcamera` are always importable
- runs `uv run pi5camera doctor` and a final
  `uv run python -c "import libcamera, picamera2, cv2; print('imports-ok')"`
  check inside the verified environment

Manual fallback if you do not want to use the script:

```bash
sudo apt update
sudo apt install -y python3-picamera2 python3-libcamera python3-venv
cd ~/NinjaClawBot
rm -rf .venv
/usr/bin/python3 -m venv --system-site-packages .venv
source .venv/bin/activate

# Set .python-version to match the system Python so uv uses it.
/usr/bin/python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" > .python-version

uv sync --active --extra dev

# Inject Raspberry Pi system dist-packages path into the venv so
# picamera2 and libcamera are importable regardless of interpreter.
SITE_DIR=$(.venv/bin/python -c "import site; print(site.getsitepackages()[0])")
echo "/usr/lib/python3/dist-packages" > "${SITE_DIR}/raspberry-pi-system-packages.pth"

uv run pi5camera doctor
```

Manual fallback with the optional wake-word listener:

```bash
sudo apt update
sudo apt install -y python3-picamera2 python3-libcamera python3-venv
cd ~/NinjaClawBot
rm -rf .venv
/usr/bin/python3 -m venv --system-site-packages .venv
source .venv/bin/activate

# Set .python-version to match the system Python.
/usr/bin/python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" > .python-version

uv sync --active --extra dev --extra voiceinput

# Inject Raspberry Pi system dist-packages path.
SITE_DIR=$(.venv/bin/python -c "import site; print(site.getsitepackages()[0])")
echo "/usr/lib/python3/dist-packages" > "${SITE_DIR}/raspberry-pi-system-packages.pth"

uv run pi5camera doctor
```

Why the bootstrap installer is recommended:

- it installs the normal development workspace
- it also installs the optional `openWakeWord` dependency used by the always-on
  `pi5mic` listener when `--voiceinput` is used
- it detects the system Python version and updates `.python-version` so `uv`
  uses the same interpreter as `/usr/bin/python3`
- it injects a `.pth` file that adds system dist-packages to the venv path,
  ensuring `picamera2` and `libcamera` remain importable

### 5.3 Verify the workspace install

```bash
cd ~/NinjaClawBot
uv run python -c "import ninjaclawbot, pi5camera, pi5buzzer, pi5servo, pi5disp, pi5mic, pi5vl53l0x; print('imports-ok')"
uv run ninjaclawbot --help
uv run pi5camera --help
uv run pi5servo --help
uv run pi5disp --help
uv run pi5buzzer --help
uv run pi5mic --help
uv run pi5vl53l0x --help
```

Expected result:

- `imports-ok` is printed
- each help command opens normally

Need help later?
- [Appendix A. Raspberry Pi setup help](#appendix-a-raspberry-pi-setup-help)

## 6. Wire the Hardware

Purpose:
- connect the robot hardware before running the guided setup tools

Use these library guides for wiring details:

- Camera: [pi5camera/README.md](pi5camera/README.md)
- Servo: [pi5servo/README.md](pi5servo/README.md)
- Display: [pi5disp/README.md](pi5disp/README.md)
- Buzzer: [pi5buzzer/README.md](pi5buzzer/README.md)
- Distance sensor: [pi5vl53l0x/README.md](pi5vl53l0x/README.md)
- Microphone: [pi5mic/README.md](pi5mic/README.md)

Quick notes:

- direct servo testing is easiest on GPIO 12 or GPIO 13
- the VL53L0X usually appears on I2C address `0x29`
- some servo-controller HATs appear on I2C address `0x10`
- if you plan to use the camera, connect the ribbon cable now and make sure the
  module is seated correctly before power-on
- if you plan to use voice input, plug the USB microphone in now so it is
  visible during `pi5mic` setup

Need help later?
- [Appendix B. Hardware and local test help](#appendix-b-hardware-and-local-test-help)

## 7. Run the Guided Setup Tools

Purpose:
- initialize and test each hardware module using the safest interactive tools
  first

Run these in order.

### 7.1 Servo setup

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

### 7.2 Buzzer setup

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

### 7.3 Display setup

```bash
cd ~/NinjaClawBot
uv run pi5disp init
uv run pi5disp display-tool
```

Inside the tool:

1. confirm the display settings
2. show text such as `HELLO`
3. confirm the screen rotation looks correct

Then export those same settings into the root project file used by
`ninjaclawbot`:

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

### 7.4 Distance sensor setup

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

### 7.5 Camera setup

First confirm the Raspberry Pi camera stack can see the module:

```bash
rpicam-hello --list-cameras
```

Then run the guided tool:

```bash
cd ~/NinjaClawBot
uv run pi5camera camera-tool
```

Inside the tool:

1. run setup
2. keep the default photo directory as `~/NinjaClawBot/photo` unless you have a
   better absolute path already prepared
3. run doctor
4. take one normal photo
5. test one face-recognition cycle

Expected result:

- `camera.json` is created
- the default photo directory is saved as an absolute path
- a captured photo is written under `~/NinjaClawBot/photo/`
- unknown faces can be named and saved for later recognition

#### 7.5.1 Verify face recognition

After camera setup, verify face recognition works end-to-end:

```bash
cd ~/NinjaClawBot
uv run pi5camera doctor
```

Expected output includes:

```text
Recognition: mediapipe_opencv (ready)
Detection:   opencv_haar
```

On Raspberry Pi, face detection uses the OpenCV Haar cascade (MediaPipe is not
available on ARM64). This is normal and expected.

#### 7.5.2 Capture and recognize a face

Use the interactive camera tool:

```bash
cd ~/NinjaClawBot
uv run pi5camera camera-tool
```

Choose option `5. Recognize faces`:

- the camera takes a photo
- detected faces are listed with bounding boxes
- if an unknown face is found, you are prompted to enter a name
- typing a name saves it to the face database for future recognition

Alternatively, use the CLI directly:

```bash
cd ~/NinjaClawBot
uv run pi5camera recognize --prompt-for-names
```

#### 7.5.3 Managing known faces

List all saved face identities:

```bash
cd ~/NinjaClawBot
uv run pi5camera manage-faces list
```

Remove a saved face:

```bash
cd ~/NinjaClawBot
uv run pi5camera manage-faces remove "Alice"
```

Face data is stored in the `camera_data/` directory under your project root.

Need help later?
- [Appendix B. Hardware and local test help](#appendix-b-hardware-and-local-test-help)

## 8. Optional but Recommended: Configure `pi5mic`

Purpose:
- prepare the voice-input layer now, even if you do not plan to use it on the
  first day

Why it is recommended:

- it is easier to verify your microphone while you are still doing local
  hardware bring-up
- OpenClaw voice input later reuses the same `pi5mic` setup
- if the microphone works locally first, OpenClaw debugging becomes much easier

If you are certain you do not want voice input yet, you can skip this section
and come back later.

### 8.1 Build the default local STT backend: `whisper.cpp`

```bash
cd ~
git clone https://github.com/ggml-org/whisper.cpp.git
cd ~/whisper.cpp
sh ./models/download-ggml-model.sh base
cmake -B build
cmake --build build -j
```

Purpose:

- download and build the local speech-to-text engine used by the default
  `pi5mic` path
- install the multilingual `ggml-base.bin` model

Expected result:

- `~/whisper.cpp/build/bin/whisper-cli` exists
- `~/whisper.cpp/models/ggml-base.bin` exists

### 8.2 Register Whisper with `pi5mic`

```bash
cd ~/NinjaClawBot
uv run pi5mic install whispercpp \
  --command ~/whisper.cpp/build/bin/whisper-cli \
  --model-path ~/whisper.cpp/models/ggml-base.bin
```

Purpose:

- tell `pi5mic` exactly where the Whisper command and model are stored

Expected result:

- the resolved command path is printed
- the resolved model path is printed
- the values are saved into `mic.json`

### 8.3 Optional Gemini API key setup

If you want to use Gemini instead of Whisper for STT, set one of these first:

```bash
cd ~/NinjaClawBot
export GEMINI_API_KEY="your_key_here"
```

or:

```bash
cd ~/NinjaClawBot
export GOOGLE_API_KEY="your_key_here"
```

Purpose:

- give the current shell permission to call the Gemini Developer API

Expected result:

- no output is normal
- if both keys are set, the Google SDK uses `GOOGLE_API_KEY`

### 8.4 Optional: prepare a custom `openWakeWord` model

You only need this if you want the optional always-on wake-word listener.

What changed:

- `pi5mic` now uses `openWakeWord` for always-on wake-word detection
- there is no extra account and no access key
- for the word `Ninja`, `pi5mic` needs a custom `.onnx` or `.tflite` model file

Recommended way to get the model:

1. Open the official [openWakeWord GitHub repository](https://github.com/dscripka/openWakeWord).
2. Read the `Training New Models` section.
3. Use the simple Google Colab notebook if you want the easiest first pass.
4. Train or export a model for the phrase `hey Ninja`.
5. Download the finished `.onnx` or `.tflite` model.
6. Save it somewhere stable, for example:

```bash
mkdir -p ~/NinjaClawBot/voiceinput
mv ~/Downloads/hey_Ninja.* ~/NinjaClawBot/voiceinput/
```

Expected result:

- you have a `.onnx` or `.tflite` model saved somewhere you can point to
  during setup

### 8.5 Run the guided `pi5mic` setup

Recommended first run:

```bash
cd ~/NinjaClawBot
uv run pi5mic mic-tool
```

Then choose:

- `1. Run setup wizard`

Recommended first choices for local microphone validation:

- `Profile`: `standalone`
- `Input device`: your USB microphone or `default`
- `Sample rate (Hz)`: accept the recommended value
- `STT backend`: `whisper_cpp` or `gemini`
- if `whisper_cpp`: use your `whisper-cli` path and `ggml-base.bin` path
- if `whisper_cpp`: accept the suggested `threads` value on Raspberry Pi
- if `gemini`: keep the default model unless you have a reason to change it
- `Maximum clip length`: start with `8`, `10`, or `12`
- `Prepare always-on voice input now?`: choose `y` only if you want the manual
  wake-word listener
- if you enable always-on voice input:
  - keep `Wake word` as `hey Ninja` unless you trained a different wake phrase
  - set `openWakeWord model path` to your custom `.onnx` or `.tflite` file
  - keep `Wake-word detection threshold` at `0.5` for the first test
  - keep `Wake-word VAD threshold` at `0` unless you need extra false-trigger
    filtering
  - keep `Enable openWakeWord noise suppression?` at `n` for the first test
  - keep `openWakeWord inference framework` at `auto`
  - keep `Silence stop timeout` at `3`
  - keep `Maximum recorded command length` at `10`
  - keep `Cooldown` at `1.5`

Purpose:

- write the actual microphone profile into `~/NinjaClawBot/mic.json`
- save the standalone-first test path before OpenClaw is involved

Expected result:

- the wizard saves `mic.json`
- it prints either `Configured STT backend looks ready.` or a clear warning
  about what is still missing
- if always-on voice input is enabled, setup reminds you to run
  `uv run pi5mic doctor` before starting the listener manually

### 8.6 Run `doctor`

```bash
cd ~/NinjaClawBot
uv run pi5mic doctor
```

Purpose:

- verify the microphone settings
- verify the selected STT backend
- verify the optional always-on wake-word setup when enabled
- show Raspberry Pi health warnings when available

Expected result:

- for Whisper: command path, model path, and runtime summary are shown
- for Gemini: `doctor` shows which API key variable it found
- if always-on voice input is enabled, `doctor` also checks:
  - whether `openWakeWord` is installed
  - whether the custom `.onnx` or `.tflite` wake-word model exists
  - whether the shared runtime assets are available
  - which inference framework will be used
  - whether the voice-input service is currently running or stopped
- success ends with `pi5mic doctor passed.` or `pi5mic doctor passed with warnings.`

### 8.7 Run one real capture cycle

```bash
cd ~/NinjaClawBot
uv run pi5mic run --once
```

Purpose:

- record one short clip
- transcribe it with the selected backend

Expected result:

- the command records one clip
- the transcript is printed locally

### 8.8 Optional first always-on test in the foreground

Use this only after `doctor` is clean.

If you have not registered the custom wake-word model yet, do that first:

```bash
cd ~/NinjaClawBot
uv run pi5mic install openwakeword \
  --model-path ~/NinjaClawBot/voiceinput/hey_Ninja.onnx \
  --keyword "hey Ninja"
```

Then run:

```bash
cd ~/NinjaClawBot
uv run pi5mic voiceinput-tool foreground
```

Purpose:

- starts the always-on listener in the current terminal
- lets you watch the listener state directly
- is the safest first test because you can stop it with `Ctrl+C`

Expected result:

- the tool says it is waiting for the wake word
- say `hey Ninja`, then a short sentence
- it records after the wake word
- it stops recording after 3 seconds of silence or 10 seconds max
- it prints the recognized transcript in the terminal

Need more detail?
- [pi5mic/README.md](pi5mic/README.md)
- [Appendix C. `pi5mic` and voice input help](#appendix-c-pi5mic-and-voice-input-help)

## 9. Run Quick Local NinjaClawBot Tests

Purpose:
- confirm the full robot layer works before adding OpenClaw

### 9.1 Run direct checks

```bash
cd ~/NinjaClawBot
uv run ninjaclawbot health-check
uv run ninjaclawbot capture-photo
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
- `capture-photo` saves a normal photo into the configured photo directory
- `movement-tool` opens normally
- `using_root_config` is `true`

Need help later?
- [Appendix B. Hardware and local test help](#appendix-b-hardware-and-local-test-help)

## 10. Install and Onboard OpenClaw

Purpose:
- get OpenClaw working only after the local hardware and robot layer are already
  known-good

Use these references in this order:

- official getting-started overview:
  - [OpenClaw Getting Started](https://docs.openclaw.ai/start/getting-started)
- official install page:
  - [OpenClaw Install](https://docs.openclaw.ai/start/installation)
- official onboarding page:
  - [OpenClaw Onboarding CLI](https://docs.openclaw.ai/start/onboarding-cli)

### 10.1 Optional: prepare Telegram before onboarding

If you want Telegram as your user-facing channel, create or confirm your bot
token first so you can enter it during onboarding.

What to prepare:

- a Telegram bot token from BotFather

### 10.2 Install OpenClaw

First, check Node:

```bash
node --version || true
```

OpenClaw currently recommends Node 24 and also supports Node 22.16+.

Then install OpenClaw:

```bash
curl -fsSL https://openclaw.ai/install.sh | bash
```

### 10.3 Run onboarding

```bash
openclaw onboard --install-daemon
```

During onboarding:

- choose your normal provider and model settings
- enter your model-provider credential
- enable Telegram if you want Telegram as the chat interface
- allow the daemon install so OpenClaw can run as a background service

Optional but useful if you want the service to keep working after logout:

```bash
sudo loginctl enable-linger "$USER"
```

### 10.4 Verify the OpenClaw install

```bash
openclaw doctor
openclaw gateway status
openclaw dashboard
```

When you continue with this guide, you should already have:

- the `openclaw` command
- a working `~/.openclaw/openclaw.json`
- your own model settings
- your own Telegram settings if you want Telegram replies

Important:

- do not overwrite your whole `openclaw.json` with a random template
- this guide patches your existing file safely
- never paste real API keys, pairing codes, or tokens into shared screenshots
  or notes

Need help later?
- [Appendix D. OpenClaw and Telegram help](#appendix-d-openclaw-and-telegram-help)

## 11. Integrate NinjaClawBot with OpenClaw

Purpose:
- add NinjaClawBot to your existing OpenClaw setup without losing your own
  secrets or model settings

### 11.1 Save the important paths

```bash
cd ~/NinjaClawBot
export NINJACLAWBOT_ROOT="$(pwd)"
export NINJACLAWBOT_PLUGIN="$(realpath integrations/openclaw/ninjaclawbot-plugin)"
export NINJACLAWBOT_UV="$(command -v uv)"
printf '%s\n%s\n%s\n' "$NINJACLAWBOT_ROOT" "$NINJACLAWBOT_PLUGIN" "$NINJACLAWBOT_UV"
```

### 11.2 Back up `openclaw.json`

```bash
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup.$(date +%Y%m%d-%H%M%S)
```

### 11.3 Patch `openclaw.json` safely

This patch only updates the parts NinjaClawBot needs:

- the main agent tool allowlist
- internal `boot-md`
- the NinjaClawBot skill entry
- plugin allow/load/entry settings

It does not overwrite your existing:

- provider credentials
- active model settings
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

### 11.4 Create `BOOT.md`

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

### 11.5 Create or update `AGENTS.md`

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
- [Appendix D. OpenClaw and Telegram help](#appendix-d-openclaw-and-telegram-help)
- [Appendix E. Sanitized `openclaw.json` example](#appendix-e-sanitized-openclawjson-example)

## 12. Validate the OpenClaw Plugin and Gateway

Purpose:
- confirm the plugin, workspace files, and bridge are healthy before Telegram
  or voice-input testing

### 12.1 Run basic OpenClaw checks

```bash
openclaw doctor --fix
openclaw hooks enable boot-md
openclaw hooks info boot-md
openclaw skills list --eligible | grep -iE 'ninjaclawbot_control|ninjaclawbot' || true
openclaw hooks list --verbose | grep -iE 'boot-md|ninjaclawbot|message_received|agent_end|gateway_stop' || true
openclaw plugins info ninjaclawbot
```

### 12.2 Start the gateway

```bash
openclaw gateway start
openclaw gateway status
```

If normal log follow is blocked, use the raw log file:

```bash
tail -f "$(ls -t /tmp/openclaw/openclaw-*.log | head -n1)"
```

### 12.3 Run `ninjaclawbot_diagnostics`

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
- [Appendix D. OpenClaw and Telegram help](#appendix-d-openclaw-and-telegram-help)

## 13. Validate Telegram and Voice Input End to End

Purpose:
- prove the complete user-facing workflow works

### 13.1 Telegram startup check

```bash
openclaw gateway restart
```

Expected result:

- the robot shows one startup greeting
- the robot returns to idle

### 13.2 Telegram reply check

In Telegram:

1. send `/new`
2. send `hello`
3. send one or two more short messages

Expected result:

- the robot shows a matching expression
- Telegram still receives a normal text reply
- the robot returns to idle after the reply

### 13.3 Telegram shutdown check

```bash
openclaw gateway stop
openclaw gateway status
```

Expected result:

- the robot shows the sleepy expression once
- the display turns off after sleepy finishes

### 13.4 Switch `pi5mic` into OpenClaw mode

```bash
cd ~/NinjaClawBot
uv run pi5mic mic-tool
```

Then choose:

- `1. Run setup wizard`

Recommended choices:

- `Profile`: `openclaw`
- `Input device`: your USB microphone or `default`
- `Sample rate (Hz)`: accept the recommended value
- `STT backend`: choose `whisper_cpp` or `gemini`
- `Voice-input OpenClaw session strategy`: `agent_main`
- `Maximum clip length`: start with `8`, `10`, or `12`
- `Prepare always-on voice input now?`: choose `y` only if you want the
  manual wake-word listener

If you enable always-on voice input:

- keep `Wake word` as `hey Ninja` unless you trained a different phrase
- set `openWakeWord model path` to your custom `.onnx` or `.tflite` file
- keep `Wake-word detection threshold` at `0.5` for the first test
- keep `Wake-word VAD threshold` at `0`
- keep `Enable openWakeWord noise suppression?` at `n` for the first test
- keep `openWakeWord inference framework` at `auto`

Expected result:

- `pi5mic` auto-detects the local OpenClaw CLI, config file, gateway URL, and
  session details when possible
- if an older `mic.json` still uses `voice:local-mic`, `pi5mic` now repairs it
  automatically to `voice-local-mic`
- if OpenClaw Telegram is enabled, `pi5mic` looks for the most recent Telegram
  chat or topic target from OpenClaw session data
- if a Telegram target is found, the wizard asks whether OpenClaw should reply
  both locally and in Telegram for voice turns
- it prints a short summary of the detected OpenClaw settings
- if everything is ready, it ends with:
  - `OpenClaw voice handoff is ready.`

### 13.5 Run the OpenClaw voice health check

```bash
cd ~/NinjaClawBot
uv run pi5mic doctor
```

Expected result:

- the selected STT backend is shown
- the OpenClaw command and config path are shown
- the delivery mode is shown
- if Telegram mirroring is enabled, the saved reply target is shown
- success ends with `pi5mic doctor passed.` or
  `pi5mic doctor passed with warnings.`

### 13.6 Run one OpenClaw voice turn

```bash
cd ~/NinjaClawBot
uv run pi5mic run --once
```

Expected result:

- one short clip is recorded
- the transcript is printed locally
- the transcript is submitted to OpenClaw
- the OpenClaw reply is printed locally
- if dual delivery is enabled, the same reply also appears in Telegram

### 13.7 If OpenClaw says `pairing required`

Recommended fix:

```bash
cd ~/NinjaClawBot
uv run pi5mic setup
```

Then:

- choose `Profile: openclaw`
- let the wizard auto-detect the OpenClaw settings
- answer `y` if it asks:
  - `Approve the newest local OpenClaw device request now?`

Manual fallback:

```bash
openclaw devices approve --latest
uv run pi5mic doctor
uv run pi5mic run --once
```

### 13.8 If the OpenClaw reply only appears locally

Recommended fix:

1. Send one short message to your OpenClaw bot in the Telegram chat or topic
   where you want voice replies to appear.
2. Rerun:

```bash
cd ~/NinjaClawBot
uv run pi5mic setup
```

3. Choose `Profile: openclaw`.
4. Answer `y` if setup asks:
   - `Ask OpenClaw to reply both here and in Telegram?`
5. Verify:

```bash
uv run pi5mic status
uv run pi5mic doctor
uv run pi5mic run --once
```

### 13.9 Test always-on OpenClaw listening in the foreground

Use this only after `doctor` is clean.

```bash
cd ~/NinjaClawBot
uv run pi5mic voiceinput-tool foreground
```

Expected result:

- the tool waits for `hey Ninja`
- after the wake phrase, it records the spoken request
- it stops recording after 3 seconds of silence or 10 seconds max
- it prints the recognized transcript
- it sends the original-language transcript to OpenClaw
- OpenClaw prints the reply locally
- if dual delivery is enabled, the same reply also appears in Telegram
- while OpenClaw is still replying, the listener ignores new wake-word triggers
  on purpose so one request cannot overlap another
- after the reply finishes, the listener returns to waiting mode by itself

### 13.10 Optional background always-on listener

Start it:

```bash
cd ~/NinjaClawBot
uv run pi5mic voiceinput-tool start
```

Check status:

```bash
cd ~/NinjaClawBot
uv run pi5mic voiceinput-tool status
```

Stop it:

```bash
cd ~/NinjaClawBot
uv run pi5mic voiceinput-tool stop
```

If you prefer to launch it from the robot package instead of directly from
`pi5mic`, use the NinjaClawBot wrapper:

```bash
cd ~/NinjaClawBot
uv run ninjaclawbot voiceinput-tool foreground
# or:
uv run ninjaclawbot voiceinput-tool start
uv run ninjaclawbot voiceinput-tool status
uv run ninjaclawbot voiceinput-tool stop
```

If all of the above work, your NinjaClawBot build is ready.

Need help later?
- [Appendix C. `pi5mic` and voice input help](#appendix-c-pi5mic-and-voice-input-help)
- [Appendix D. OpenClaw and Telegram help](#appendix-d-openclaw-and-telegram-help)

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
- `PortAudio library not found`:
  - install `libportaudio2` and `portaudio19-dev`

### Alternative commands

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv
python3 --version
```

## Appendix B. Hardware and Local Test Help

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
- `servo-tool` says `Unable to create/write to /sys/class/pwm/pwmchip0/pwm1` during GPIO13 calibration:
  - update the workspace with `git pull`
  - rerun `uv sync --extra dev`
  - reopen `uv run pi5servo servo-tool`
  - try calibration again from option `3`
  - if `gpio13` is already listed in `servo.json`, the tool should now reuse
    the live servo and keep the current session alive instead of reopening `pwm1`
  - if it still fails, recheck the PWM overlay line in `/boot/firmware/config.txt`
  - if you are testing an unconfigured endpoint, the tool should now suspend the
    live group only for that temporary session and rebuild it afterward
  - if a failed run suddenly makes both `gpio12` and `gpio13` unusable, reboot
    once to clear stale kernel sysfs PWM state, then test again with the latest
    build because current `pi5servo` now retries stale-channel claims, keeps
    healthy channels exported during normal reloads, and rolls back partial
    multi-servo startup claims
- `expression-tool` opens but faces look wrong:
  - export display config again to root `display.json`
- `movement-tool` opens but movement is risky:
  - do not run movements yet
  - go back to `pi5servo servo-tool`

### Alternative commands

```bash
cd ~/NinjaClawBot
uv run pi5servo calib 12
uv run pi5buzzer status --test
uv run pi5disp demo
uv run pi5vl53l0x status
uv run ninjaclawbot list-capabilities
uv run ninjaclawbot perform-expression greeting
uv run ninjaclawbot perform-reply --reply-state success "Finished"
uv run ninjaclawbot stop
uv run ninjaclawbot stop-all
```

## Appendix C. `pi5mic` and Voice Input Help

### Troubleshooting

- `Gemini credentials are not configured`:
  - export `GEMINI_API_KEY` or `GOOGLE_API_KEY`
  - rerun `uv run pi5mic doctor`
- `openWakeWord model file not found`:
  - re-register the real `.onnx` or `.tflite` file with
    `uv run pi5mic install openwakeword --model-path ...`
- `Invalid sample rate`:
  - rerun `uv run pi5mic setup`
  - keep the same microphone
  - accept the recommended sample rate
- foreground mode shows overflow or no spoken command:
  - keep the test command short
  - say the command immediately after the wake phrase
  - retest in foreground mode before using background mode
- Raspberry Pi powers off or reboots during local Whisper transcription:
  - run:

```bash
cd ~/NinjaClawBot
uv run pi5mic doctor
vcgencmd get_throttled
vcgencmd measure_temp
```

Then:

- use a known-good Raspberry Pi 5 power supply
- improve cooling
- shorten the maximum clip length
- lower `whisper.cpp` thread count
- or switch to Gemini if local transcription is too heavy

### Useful concepts

- `whisper.cpp`:
  - the default local speech-to-text backend
  - it transcribes recorded WAV audio on the Raspberry Pi
- Gemini API key:
  - the secret used when `pi5mic` sends audio to Google’s Gemini API
- `openWakeWord`:
  - the wake-word engine used by the always-on listener
  - it detects the wake phrase but does not transcribe the full command
- `.onnx` and `.tflite`:
  - both are local AI model file formats used for the custom wake-word model

### Extra references

- [pi5mic/README.md](pi5mic/README.md)
- [openWakeWord GitHub](https://github.com/dscripka/openWakeWord)
- [whisper.cpp GitHub](https://github.com/ggml-org/whisper.cpp)

## Appendix D. OpenClaw and Telegram Help

### Troubleshooting

- `openclaw doctor --fix` complains about unsupported keys:
  - remove optional old NinjaClawBot config keys such as:
    - `enableAlwaysOn`
    - `enableStartupGreeting`
    - `enableAutoThinking`
    - `enableShutdownSequence`
- OpenClaw says `spawn uv ENOENT`:
  - set `uvCommand` to the absolute result of `command -v uv`
- startup greeting missing:
  - check `boot-md`
  - check workspace `BOOT.md`
  - check `ninjaclawbot_diagnostics`
- OpenClaw says `pairing required`:
  - approve the newest local request
- OpenClaw says `Invalid session ID`:
  - rerun `pi5mic setup` so the session value is repaired
- robot reacts but Telegram has no text reply:
  - recheck workspace `AGENTS.md`
  - make sure it says:
    - first animate the robot
    - then send the normal visible text reply
- voice replies stay local:
  - send one short Telegram message to the target chat or topic
  - rerun `pi5mic setup`
  - enable local plus Telegram reply delivery
- normal log follow is blocked:
  - use the raw log file

### Useful log commands

```bash
tail -f "$(ls -t /tmp/openclaw/openclaw-*.log | head -n1)"
grep -iE 'ninjaclawbot_reply|ninjaclawbot_diagnostics|boot-md|telegram|pi5mic' "$(ls -t /tmp/openclaw/openclaw-*.log | head -n1)" | tail -n 50
```

### Alternative commands

```bash
openclaw plugins install -l ~/NinjaClawBot/integrations/openclaw/ninjaclawbot-plugin
openclaw plugins info ninjaclawbot
openclaw hooks list --verbose
openclaw hooks info boot-md
openclaw skills list --eligible
openclaw gateway restart
openclaw gateway stop
openclaw gateway status
openclaw devices approve --latest
```

## Appendix E. Sanitized `openclaw.json` Example

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
        "primary": "openai-codex/YOUR_OPENAI_MODEL_ID"
      },
      "models": {
        "openai-codex/YOUR_OPENAI_MODEL_ID": {}
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

Optional note:

- if you also want local models later, you can add a separate
  `models.providers.ollama` block
- that block is optional
- the active model still comes from `agents.defaults.model.primary`
