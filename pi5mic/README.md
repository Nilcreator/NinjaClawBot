# pi5mic

`pi5mic` is the standalone-first microphone library for the NinjaClawBot workspace.

This README is written for normal Raspberry Pi users, not only developers. You can use `pi5mic` as a standalone microphone tool without OpenClaw. The current build also includes an optional OpenClaw profile, but the safest first test is the standalone path.

## What `pi5mic` Can Do Right Now

Current implemented features:

- find available microphone devices
- record a short WAV file
- transcribe speech locally with `whisper.cpp`
- optionally use Gemini instead of `whisper.cpp`
- guide you through setup with `pi5mic setup`
- provide a simple menu with `pi5mic mic-tool`
- run one full record-and-transcribe test with `pi5mic run --once`

Current limit:

- the package is ready for guided/manual testing
- it is not yet a fully validated always-on wake-word background service on Raspberry Pi

## Before You Start

You need:

- a Raspberry Pi with internet access
- a working microphone, usually USB
- `uv` installed
- this repository downloaded

You also need PortAudio system libraries. These are required for microphone access on Raspberry Pi.

## 1. Standalone Installation

These steps install `pi5mic` as a standalone microphone tool.

### Step 1. Install required Raspberry Pi system packages

```bash
sudo apt update
sudo apt install -y git build-essential cmake pkg-config libportaudio2 portaudio19-dev python3-dev
```

What this is doing:

- `git`: lets you clone code from GitHub
- `build-essential`, `cmake`, `pkg-config`: needed to build `whisper.cpp`
- `libportaudio2`, `portaudio19-dev`: needed so the microphone backend can open audio devices
- `python3-dev`: useful for Python package builds on Raspberry Pi

What you should expect:

- the install finishes without errors
- after this step, the common error `PortAudio library not found` should be avoided

### Step 2. Clone the repository

```bash
cd ~
git clone https://github.com/Nilcreator/NinjaClawBot.git
cd ~/NinjaClawBot
```

What this is doing:

- downloads the whole NinjaClawBot workspace
- moves you into the project folder

What you should expect:

- the `~/NinjaClawBot` folder exists

### Step 3. Install the Python workspace

```bash
uv sync --extra dev
```

What this is doing:

- installs all Python packages in the workspace
- includes `pi5mic`

What you should expect:

- the command finishes successfully
- you can now run `uv run pi5mic --help`

### Step 4. Confirm `pi5mic` is installed

```bash
uv run pi5mic --help
```

What this is doing:

- checks that the `pi5mic` command is available

What you should expect:

- a help screen showing commands such as:
  - `devices`
  - `doctor`
  - `install`
  - `mic-tool`
  - `record`
  - `run`
  - `setup`
  - `status`
  - `transcribe`

## 2. Install the Default STT Backend: `whisper.cpp`

`pi5mic` uses `whisper.cpp` as the default speech-to-text backend.

### Step 5. Download and build `whisper.cpp`

```bash
cd ~
git clone https://github.com/ggml-org/whisper.cpp.git
cd whisper.cpp
sh ./models/download-ggml-model.sh base
cmake -B build
cmake --build build -j
```

What this is doing:

- downloads the `whisper.cpp` source code
- downloads the multilingual `base` model
- builds the `whisper-cli` program

What you should expect:

- model file: `~/whisper.cpp/models/ggml-base.bin`
- program path: usually `~/whisper.cpp/build/bin/whisper-cli`

If your build puts `whisper-cli` somewhere slightly different, that is okay. You just need the real path.

### Step 6. Register `whisper.cpp` with `pi5mic`

```bash
cd ~/NinjaClawBot
uv run pi5mic install whispercpp \
  --command ~/whisper.cpp/build/bin/whisper-cli \
  --model-path ~/whisper.cpp/models/ggml-base.bin
```

What this is doing:

- tells `pi5mic` where the `whisper.cpp` command lives
- tells `pi5mic` where the model file lives
- saves both paths into `mic.json`

What you should expect:

- the terminal prints the resolved command path
- the terminal prints the resolved model path
- settings are saved successfully

## 3. First-Time Setup With `pi5mic setup`

This is the command-line wizard.

### Step 7. Start the setup wizard

```bash
cd ~/NinjaClawBot
uv run pi5mic setup
```

What this is doing:

- creates or updates `mic.json`
- asks you which profile, microphone, and STT backend you want

### Recommended choices for standalone testing

Choose:

- `Profile`: `standalone`
- `Input device`: your microphone number, name, or `default`
- `STT backend`: `whisper_cpp`
- `whisper.cpp command path`: your `whisper-cli` path
- `whisper.cpp model path`: your `ggml-base.bin` path
- `Maximum clip length`: `10` or `15`

What you should expect:

- a file named `mic.json` is created in the current folder
- if the backend is ready, you should see:
  - `Configured STT backend looks ready.`

If you still see a warning:

- read the warning carefully
- it should tell you exactly what is still missing

## 4. Full Function Explanation And Setup With `mic-tool`

`mic-tool` is the easiest path for non-programmers.

### Step 8. Start `mic-tool`

```bash
uv run pi5mic mic-tool
```

What this is doing:

- opens a simple text menu
- lets you use the most common actions without remembering command names

What you should expect:

- you will see these menu items:
  - `1. Run setup wizard`
  - `2. Register whisper.cpp`
  - `3. Run doctor`
  - `4. Show status`
  - `5. Run one capture cycle`
  - `6. Exit`

### What each menu item does

#### 1. Run setup wizard

What it does:

- same as `uv run pi5mic setup`

What to expect:

- asks for your profile, microphone, backend, and paths
- saves your settings into `mic.json`

#### 2. Register whisper.cpp

What it does:

- same as `uv run pi5mic install whispercpp`

What to expect:

- saves the command path and model path if they are valid

#### 3. Run doctor

What it does:

- checks whether your config, microphone setup, and backend are ready

What to expect:

- lines starting with `OK`
- then:
  - `pi5mic doctor passed.`

If something is wrong:

- it prints a failure list
- fix those items before going further

#### 4. Show status

What it does:

- shows the current profile and local readiness summary

What to expect:

- values such as:
  - config file path
  - profile
  - input device
  - sample rate
  - STT backend
  - number of detected input devices

#### 5. Run one capture cycle

What it does:

- records one temporary audio clip
- transcribes it
- prints the text result

What to expect:

- `Recording...`
- `Recorded X.XXs of audio.`
- `Transcript:`
- your recognized words
- backend information

This is the simplest way to test whether the whole standalone microphone flow works.

#### 6. Exit

What it does:

- closes the menu

What to expect:

- `Leaving pi5mic mic-tool.`

## 5. Full Function Explanation And Setup With Direct Command Line

If you prefer direct commands, use this section.

### Step 9. List available microphones

```bash
uv run pi5mic devices
```

What this is doing:

- shows all input devices that support recording

What you should expect:

- a numbered list like:
  - `[1] USB Mic`
  - `[2] Desk Mic`

### Step 10. Show the current config

```bash
uv run pi5mic config show
```

What this is doing:

- prints the active `mic.json`

What you should expect:

- readable JSON with sections like:
  - `profile`
  - `audio`
  - `stt`
  - `integration`
  - `retention`

### Step 11. Show a short readiness summary

```bash
uv run pi5mic status
```

What this is doing:

- prints the most important current settings

What you should expect:

- profile
- input device
- sample rate
- STT backend
- audio device count

### Step 12. Run the health check

```bash
uv run pi5mic doctor
```

What this is doing:

- checks that your setup is usable

What you should expect:

- success messages for:
  - config
  - audio device discovery
  - `whisper.cpp` command
  - model file

### Step 13. Test recording only

```bash
uv run pi5mic record --duration 3 --output mic-test.wav
```

What this is doing:

- records a 3-second WAV file
- does not run speech-to-text yet

What you should expect:

- a file named `mic-test.wav`
- metadata such as duration, frames, and bytes

This is a good test when you want to confirm the microphone works before testing transcription.

### Step 14. Test transcription on the saved WAV file

```bash
uv run pi5mic transcribe mic-test.wav
```

What this is doing:

- runs your saved WAV file through the configured STT backend

What you should expect:

- the recognized text
- backend name
- model name
- sometimes a language value

### Step 15. Test the full standalone flow

```bash
uv run pi5mic run --once
```

What this is doing:

- records one temporary clip
- transcribes it
- prints the final result
- deletes the temporary audio file by default

What you should expect:

- `Profile: standalone`
- `STT: whisper_cpp`
- `Recording...`
- a transcript result

### Step 16. Keep the temporary audio file for debugging if needed

```bash
uv run pi5mic run --once --keep-audio
```

What this is doing:

- same as the previous step
- keeps the recorded WAV file instead of deleting it

What you should expect:

- everything from the normal `run --once`
- plus a final line showing where the audio file was saved

### Step 17. Test transcription without recording live audio

```bash
uv run pi5mic run --once --audio-file ./mic-test.wav
```

What this is doing:

- skips live microphone recording
- uses an existing WAV file

What you should expect:

- transcript output only
- useful when debugging STT without speaking again

## 6. Optional Gemini Setup

Gemini is optional. Only use this if you want to test the alternative cloud backend.

### Step 18. Install the Gemini extra

```bash
uv sync --extra dev --extra gemini
```

### Step 19. Set your Gemini API key

```bash
export GOOGLE_API_KEY="your_key_here"
```

or:

```bash
export GEMINI_API_KEY="your_key_here"
```

### Step 20. Switch the backend in setup

```bash
uv run pi5mic setup
```

Choose:

- `STT backend`: `gemini`

What you should expect:

- the wizard reminds you that Gemini needs an environment variable
- `uv run pi5mic doctor` should then report:
  - `OK   Gemini credentials found in environment`

## 7. Common Problem: `PortAudio library not found`

If you see this error:

```text
OSError: PortAudio library not found
```

it means:

- the Python package `sounddevice` is installed
- but the Raspberry Pi is missing the system PortAudio library

Fix it with:

```bash
sudo apt update
sudo apt install -y libportaudio2 portaudio19-dev
```

Then rerun:

```bash
uv run pi5mic doctor
```

You should now get a friendly setup result instead of a crash.

## 8. What Counts As A Successful Standalone Test

You have tested the current standalone `pi5mic` build successfully if all of these work:

1. `uv run pi5mic --help`
2. `uv run pi5mic devices`
3. `uv run pi5mic doctor`
4. `uv run pi5mic record --duration 3 --output mic-test.wav`
5. `uv run pi5mic transcribe mic-test.wav`
6. `uv run pi5mic run --once`
7. `uv run pi5mic mic-tool`

## 9. Validation Commands For Developers

```bash
cd /Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code\ library/NinjaClawbot/pi5mic
uv run --extra dev python -m compileall src tests
uv run --extra dev ruff check src tests
uv run --extra dev ruff format --check src tests
uv run --extra dev pytest -q tests -c pyproject.toml
```
