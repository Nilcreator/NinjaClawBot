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
- prepare manual always-on wake-word config during `pi5mic setup`
- start, stop, and inspect the optional background listener with `pi5mic voiceinput-tool`
- optionally reuse the OpenClaw main session for always-on voice turns
- show Raspberry Pi health warnings in `pi5mic doctor` when power or thermal history is available

Current limit:

- the package is ready for guided/manual testing, including the first always-on listener build
- the always-on wake-word path still needs long-run Raspberry Pi validation before it should be treated as fully production-ready

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

Normal install:

```bash
uv sync --extra dev
```

If you want the optional always-on wake-word feature too, use:

```bash
uv sync --extra dev --extra voiceinput
```

What this is doing:

- installs all Python packages in the workspace
- includes `pi5mic`
- also includes the Gemini SDK that `pi5mic` uses for the optional cloud backend
- if you use the `voiceinput` extra, it also installs the Porcupine wake-word dependency

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
- `voiceinput-tool`

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
- asks for a sample rate that matches your selected microphone
- can also prepare the optional always-on wake-word listener
- if you choose `Profile: openclaw`, `pi5mic` now tries to detect your local
  OpenClaw settings automatically and then runs a safe readiness check

### Recommended choices for standalone testing

Choose:

- `Profile`: `standalone`
- `Input device`: your microphone number, name, or `default`
- `Sample rate (Hz)`: accept the recommended value shown by `pi5mic`
- `STT backend`: `whisper_cpp`
- `whisper.cpp command path`: your `whisper-cli` path
- `whisper.cpp model path`: your `ggml-base.bin` path
- `whisper.cpp threads`: accept the suggested value on Raspberry Pi, usually `2`
- `Maximum clip length`: start with `8`, `10`, or `12`
- `Prepare always-on voice input now?`: choose `y` only if you want the manual wake-word listener
- if you enable always-on voice input:
  - `Wake word`: keep `ninja` unless you trained a different keyword
  - `Picovoice access-key environment variable`: usually `PICOVOICE_ACCESS_KEY`
  - `Porcupine keyword file (.ppn) path`: provide your custom file for `Ninja` when available
  - `Silence stop timeout`: keep `3`
  - `Maximum recorded command length`: keep `10`
  - `Cooldown`: keep `1.5`

Important note about sample rate:

- many Raspberry Pi USB microphones do not accept `16000` Hz directly
- they often work best at `44100` Hz or `48000` Hz
- `pi5mic` now tries to recommend the device's own default sample rate during setup
- for most users, the safest choice is to accept the recommended value

Important note about Raspberry Pi safety defaults:

- `pi5mic` now normalizes recorded WAV clips to `16000` Hz mono before sending
  them to `whisper.cpp`
- if you leave the thread setting blank, `pi5mic` now uses a safer default on
  Raspberry Pi instead of letting `whisper.cpp` spike to the platform default
- the default max clip length is now shorter because the current preview path
  still records the full clip before transcription

What you should expect:

- a file named `mic.json` is created in the current folder
- if the backend is ready, you should see:
  - `Configured STT backend looks ready.`
- if you enabled always-on voice input, setup also reminds you to run `uv run pi5mic doctor`
  before starting `voiceinput-tool`

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
  - `6. Open voiceinput-tool`
  - `7. Exit`

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

Sometimes you may see:

- `pi5mic doctor passed with warnings.`

This usually means:

- your saved sample rate does not match what the microphone accepts
- `pi5mic` found a safer working rate, such as `48000` Hz
- or `pi5mic` detected Raspberry Pi power, thermal, or memory pressure that may
  affect local Whisper transcription

If that happens:

- rerun `uv run pi5mic setup`
- keep the same microphone
- accept the recommended sample rate

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
  - Whisper runtime or Gemini auth status
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

What `pi5mic` now does automatically for local Whisper on Raspberry Pi:

- keeps a safer default thread count when you leave the setting blank
- converts WAV clips to `16000` Hz mono before transcription
- keeps the default clip shorter so the preview path does less work per cycle

This is the simplest way to test whether the whole standalone microphone flow works.

#### 6. Open voiceinput-tool

What it does:

- opens the dedicated always-on listener control menu
- lets you start, stop, inspect, and debug the manual wake-word service

What to expect:

- a second menu with:
  - `Show voice input status`
  - `Start background listener`
  - `Stop background listener`
  - `Run listener in foreground`
  - `Show recent voice input logs`

#### 7. Exit

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
- if always-on voice input is enabled:
  - wake word
  - session strategy
  - service state
  - state-file and log-file paths

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

If the sample rate is not ideal for the selected microphone, `doctor` may still succeed but show a warning with a better rate to use.

If always-on voice input is enabled, `doctor` also checks:

- whether the Porcupine package is installed
- whether the Picovoice access key variable is present
- whether the custom `.ppn` keyword file exists when needed
- whether the background listener is running or stopped

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

If this command reports `Invalid sample rate`, rerun `uv run pi5mic setup` and accept the sample rate recommended by the wizard.

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

## 6. Manual Always-On Voice Input

This section is for the optional wake-word listener.

Important safety and privacy rule:

- `pi5mic` never starts the microphone automatically
- you must start it yourself
- you can stop it yourself at any time

### Step 18. Confirm the wake-word dependency is installed

```bash
cd ~/NinjaClawBot
uv sync --extra dev --extra voiceinput
```

What this is doing:

- installs Porcupine for wake-word detection

What you should expect:

- the command completes without errors

### Step 19. Set your Picovoice access key

```bash
cd ~/NinjaClawBot
export PICOVOICE_ACCESS_KEY="your_key_here"
```

What this is doing:

- gives the wake-word engine permission to start

What you should expect:

- no output is normal

### Step 20. Validate the always-on config

```bash
cd ~/NinjaClawBot
uv run pi5mic doctor
```

What this is doing:

- checks STT, microphone access, and wake-word readiness together

What you should expect:

- `INFO always-on voice input: enabled`
- `OK   wake-word detector: ...`
- if using `Ninja`, either a valid `.ppn` path or a clear warning/failure telling you what is still missing

### Step 21. Start the listener in the background

```bash
cd ~/NinjaClawBot
uv run pi5mic voiceinput-tool start
```

What this is doing:

- starts the manual wake-word listener in the background
- waits for the wake word
- after wake-word detection, records until 3 seconds of silence or 10 seconds max

What you should expect:

- `Started the always-on voice input listener in the background.`
- the microphone stays idle until it hears the wake word

### Step 22. Check its status

```bash
cd ~/NinjaClawBot
uv run pi5mic voiceinput-tool status
```

What this is doing:

- shows whether the background listener is running
- shows the wake word, session strategy, and the state/log file paths

### Step 23. Stop it manually

```bash
cd ~/NinjaClawBot
uv run pi5mic voiceinput-tool stop
```

What this is doing:

- stops the background wake-word listener

What you should expect:

- `Stopped the always-on voice input listener.`

### Step 24. Use the foreground mode when debugging

```bash
cd ~/NinjaClawBot
uv run pi5mic voiceinput-tool foreground
```

What this is doing:

- runs the same listener in the current terminal
- prints live status messages so you can debug setup problems

What you should expect:

- `Starting voice input in the foreground.`
- `Press Ctrl+C to stop it.`
- useful when debugging STT without speaking again

## Optional OpenClaw Mode Inside NinjaClawBot

Use this after the standalone path already works.

### Step 18. Start from the NinjaClawBot root

```bash
cd ~/NinjaClawBot
```

What this is doing:

- makes sure `mic.json` is written into the NinjaClawBot project folder
- lets `pi5mic` reuse the same OpenClaw installation and Python environment

### Step 19. Run the setup wizard or `mic-tool`

```bash
uv run pi5mic mic-tool
```

Then choose:

- `1. Run setup wizard`

Recommended OpenClaw choices:

- `Profile`: `openclaw`
- `Input device`: your USB microphone or `default`
- `Sample rate (Hz)`: accept the recommended value
- `STT backend`: `whisper_cpp` or `gemini`
- `Maximum clip length`: start with `8`, `10`, or `12`

What `pi5mic` now does automatically in OpenClaw mode:

- finds the local `openclaw` CLI when possible
- reads the local OpenClaw config file when available
- fills in the gateway URL, agent id, and session key automatically
- automatically repairs the old legacy value `voice:local-mic` to the current
  safe OpenClaw session id `voice-local-mic`
- checks whether OpenClaw Telegram is enabled
- looks for the most recent Telegram chat or topic target from OpenClaw session
  data when Telegram is enabled
- asks whether you want each voice turn to reply both locally and in Telegram
- saves the detected Telegram reply target if you answer `y`
- explains whether the NinjaClawBot plugin looks ready
- runs a safe readiness check after saving the config

What you should expect:

- a summary of the detected OpenClaw settings
- if OpenClaw already knows a recent Telegram route, the wizard shows it and
  asks whether it should mirror replies there too
- `Configured STT backend looks ready.` if the selected STT backend is usable
- then either:
  - `OpenClaw voice handoff is ready.`
  - or a warning that explains what still needs attention

### Step 20. If the wizard says OpenClaw needs one-time pairing approval

Sometimes OpenClaw may say `pairing required`.

What this means:

- your microphone and STT backend may already be fine
- OpenClaw created a local device request, but it has not been approved yet

What `pi5mic` does now:

- explains the problem in plain language
- asks whether it should approve the newest local request for you
- retries the readiness check automatically if you say yes

What you should expect:

- a prompt such as:
  - `Approve the newest local OpenClaw device request now?`
- if you answer `y`, `pi5mic` tries:
  - `openclaw devices approve --latest`
- if approval works, the wizard prints:
  - `OpenClaw voice handoff is ready.`

### Step 21. Verify the OpenClaw path

```bash
uv run pi5mic doctor
uv run pi5mic run --once
```

What this is doing:

- checks the saved OpenClaw profile
- confirms the gateway is reachable
- confirms the voice handoff path is ready
- shows whether replies are local only or local plus Telegram
- records one clip, transcribes it, and sends the transcript into OpenClaw

What you should expect:

- `doctor` shows the OpenClaw command, config file, delivery mode, and readiness
  result
- `run --once` shows the transcript and, in OpenClaw mode, the OpenClaw reply
  text
- if you enabled Telegram mirroring during setup, the same voice turn should
  also appear in the detected Telegram chat or topic

## 6. Optional Gemini Setup

Gemini is optional. Only use this if you want to test the alternative cloud backend.

### Step 22. No extra Gemini package install is needed

```bash
cd ~/NinjaClawBot
uv sync --extra dev
```

What this is doing:

- confirms the normal NinjaClawBot workspace install is present
- this already includes the Google Gemini SDK used by `pi5mic`

What you should expect:

- the command finishes without errors
- after this, `pi5mic` can use Gemini if the API key is present

### Step 23. Set your Gemini API key

```bash
export GOOGLE_API_KEY="your_key_here"
```

or:

```bash
export GEMINI_API_KEY="your_key_here"
```

What this is doing:

- gives the current shell permission to call the Gemini Developer API

What you should expect:

- there is usually no output
- the key only exists in the current shell unless you also add it to your shell
  profile
- if both variables are set, the Google SDK uses `GOOGLE_API_KEY` first

### Step 24. Switch the backend in setup

```bash
uv run pi5mic setup
```

Choose:

- `STT backend`: `gemini`
- `Gemini model id`: keep `gemini-2.5-flash` unless you have a reason to change it
- `Gemini request timeout (seconds)`: keep the default to start
- `Gemini retry limit`: keep the default to start

What you should expect:

- the wizard reminds you that Gemini needs an environment variable
- it also tells you which export command format to use

### Step 25. Verify Gemini with doctor

```bash
uv run pi5mic doctor
```

What you should expect:

- `INFO active STT backend: gemini`
- `OK   Gemini credentials found in environment (GEMINI_API_KEY)` or
  `OK   Gemini credentials found in environment (GOOGLE_API_KEY)`
- if the Gemini SDK is somehow missing, `doctor` now reports that cleanly
  instead of crashing

## Common Problem: `SyntaxError: unterminated string literal` when starting `setup` or `mic-tool`

If you see an error like this:

```text
SyntaxError: unterminated string literal
```

it means:

- you are still running an older `pi5mic` source file
- the crash happens before microphone setup starts
- this is a code version problem, not a microphone hardware problem

Fix it with:

```bash
cd ~/NinjaClawBot
git pull
uv sync --extra dev
uv run pi5mic --help
```

Then rerun:

```bash
uv run pi5mic setup
```

What you should expect:

- `uv run pi5mic --help` prints the command list normally
- `setup` opens instead of crashing
- `mic-tool` opens instead of crashing

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

## 8. Common Problem: `Gemini credentials are not configured in the environment`

If you see an error like this:

```text
Gemini credentials are not configured in the environment.
```

it means:

- `pi5mic` is configured to use the Gemini backend
- but the current shell does not have `GOOGLE_API_KEY` or `GEMINI_API_KEY`

Fix it with one of these:

```bash
export GEMINI_API_KEY="your_key_here"
```

or:

```bash
export GOOGLE_API_KEY="your_key_here"
```

Then rerun:

```bash
uv run pi5mic doctor
```

What you should expect:

- doctor should stop failing on Gemini credentials
- it should tell you which environment variable it found

## 9. Common Problem: OpenClaw says `pairing required`

If you see an error like this:

```text
pairing required
```

it means:

- `pi5mic` already reached the OpenClaw CLI
- but the OpenClaw gateway still wants a one-time local device approval before
  it will accept the request

The easiest fix is:

```bash
cd ~/NinjaClawBot
uv run pi5mic setup
```

Then:

- choose `Profile: openclaw`
- let the wizard detect your OpenClaw settings automatically
- answer `y` if it asks to approve the newest local OpenClaw device request

Manual fallback:

```bash
openclaw devices approve --latest
uv run pi5mic doctor
```

What you should expect after the fix:

- `pi5mic doctor` should stop failing on pairing
- `uv run pi5mic run --once` should record, transcribe, and print the OpenClaw
  reply text

### OpenClaw reply stays local instead of Telegram

If `pi5mic` records correctly and OpenClaw replies in the terminal, but nothing
appears in Telegram, it usually means:

- OpenClaw Telegram is enabled, but `pi5mic` does not yet have a concrete
  Telegram reply target saved
- or the saved Telegram target is stale and points at an older chat or topic

The easiest recovery path is:

```bash
cd ~/NinjaClawBot
uv run pi5mic setup
```

Then:

- choose `Profile: openclaw`
- if you want a specific Telegram chat or forum topic, send one short message
  to your OpenClaw bot there first
- answer `y` when setup asks:
  - `Ask OpenClaw to reply both here and in Telegram?`

What you should expect after the fix:

- `pi5mic status` shows a `Reply target:` line
- `pi5mic doctor` shows either the detected Telegram target or a clear warning
  about why it could not be found
- `uv run pi5mic run --once` shows the OpenClaw reply locally and the same turn
  should also appear in Telegram

## 10. Common Problem: OpenClaw says `Invalid session ID`

If you see an error like this:

```text
Invalid session ID
```

it means:

- recording and transcription already worked
- the failure happened only when `pi5mic` handed the text to OpenClaw
- the old legacy session value used colons, which newer OpenClaw builds reject
  for `--session-id`

What `pi5mic` now does automatically:

- changes the old value `voice:local-mic` into `voice-local-mic`
- uses the repaired value when loading `mic.json`
- saves the repaired value the next time setup or another save path runs

The easiest recovery path is:

```bash
cd ~/NinjaClawBot
uv run pi5mic setup
uv run pi5mic doctor
uv run pi5mic run --once
```

What you should expect:

- setup shows the detected OpenClaw settings
- `doctor` should stop failing on `Invalid session ID`
- `run --once` should print the OpenClaw reply instead of stopping after
  transcription

## 11. What Counts As A Successful Standalone Test

You have tested the current standalone `pi5mic` build successfully if all of these work:

1. `uv run pi5mic --help`
2. `uv run pi5mic devices`
3. `uv run pi5mic doctor`
4. `uv run pi5mic record --duration 3 --output mic-test.wav`
5. `uv run pi5mic transcribe mic-test.wav`
6. `uv run pi5mic run --once`
7. `uv run pi5mic mic-tool`

## 12. Common Problem: `Invalid sample rate`

If you see an error like this:

```text
Error opening RawInputStream: Invalid sample rate [PaErrorCode -9997]
```

it usually means:

- the microphone was found correctly
- but the saved sample rate in `mic.json` does not match what that microphone supports

The easiest fix is:

```bash
cd ~/NinjaClawBot
uv run pi5mic setup
```

Then:

- keep the same microphone
- accept the sample rate recommended by the wizard
- run `uv run pi5mic doctor` again
- run `uv run pi5mic run --once` again

Why this happens:

- many Raspberry Pi microphones prefer their hardware default rate
- this is often `44100` Hz or `48000` Hz, not `16000` Hz

## 13. Common Problem: Raspberry Pi powers off, reboots, or suddenly goes dark after recording

If the Raspberry Pi itself powers off or reboots after the `Recording...` step,
that is usually different from a normal Python error.

What this often means:

- the board hit a power or thermal problem while local Whisper transcription was
  starting
- or the board was already under memory pressure before `whisper.cpp` launched

What `pi5mic` now does to reduce that risk:

- shorter default clip length
- safer automatic Whisper thread limit on Raspberry Pi when you leave threads blank
- WAV normalization to `16000` Hz mono before Whisper
- Raspberry Pi `doctor` warnings for:
  - temperature
  - historic or current throttling
  - historic or current undervoltage
  - low available memory

Check it with:

```bash
uv run pi5mic doctor
vcgencmd get_throttled
vcgencmd measure_temp
```

If you see warnings about undervoltage, throttling, or high temperature:

- use a stronger, known-good Raspberry Pi 5 power supply
- add active cooling or improve airflow
- lower `Maximum clip length` in `pi5mic setup` to `8` or `10`
- set `whisper.cpp threads` to `1` or `2`
- if local Whisper is still too heavy for your Pi setup, switch to Gemini

If `doctor` does not show hardware warnings but the Pi still shuts down:

- retest with `uv run pi5mic run --once --audio-file ./mic-test.wav`
- if file transcription is stable but live recording is not, focus on the mic,
  USB power, or other connected peripherals

## 12. Validation Commands For Developers

```bash
cd /Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code\ library/NinjaClawbot/pi5mic
uv run --extra dev python -m compileall src tests
uv run --extra dev ruff check src tests
uv run --extra dev ruff format --check src tests
uv run --extra dev pytest -q tests -c pyproject.toml
```
