# pi5camera

<div align="center">

**Standalone-First Camera Tools and Local Face Recognition for Raspberry Pi 5**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Raspberry Pi 5](https://img.shields.io/badge/platform-Raspberry%20Pi%205-red.svg)](https://www.raspberrypi.com/)

[NinjaClawBot README](../README.md) | [Installation Guide](../InstallationGuide.md) | [Development Guide](../DevelopmentGuide.md)

</div>

---

A standalone-first camera library for Raspberry Pi 5.

`pi5camera` helps a Raspberry Pi 5 take photos, save them into a predictable
folder, recognize known faces locally, and enroll new faces for later
recognition. It can work by itself as a local camera tool, or it can be reused
by `ninjaclawbot` and the OpenClaw plugin inside the larger NinjaClawBot
project.

This package is designed for normal Raspberry Pi users, not only developers.
The safest first path is the standalone workflow. After that works, you can
reuse the same `camera.json`, `photo/`, and `camera_data/` folders from the
full NinjaClawBot workspace.

Main functions available today:

- guide first-time setup with `pi5camera setup`
- provide a beginner-friendly menu with `pi5camera camera-tool`
- run camera readiness checks with `pi5camera doctor`
- show the current config and storage paths with `pi5camera status`
- take one still photo with `pi5camera capture`
- recognize faces from a live capture or an existing image with
  `pi5camera recognize`
- optionally prompt for unknown-face names during the same recognition flow
- enroll a face later from a saved pending recognition with `pi5camera enroll`
- list and remove saved identities with `pi5camera manage-faces`
- reuse the same camera flow through `ninjaclawbot` and OpenClaw later

Current project status:

- one-shot photo capture is ready for standalone and integrated use
- local face recognition and second-step enrollment are ready for guided testing
- Raspberry Pi validation is still recommended before treating autofocus,
  lighting, and recognition thresholds as final for your hardware setup

**Part of the [NinjaClawBot](../README.md) project.**

---

## Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Face Recognition Workflow](#face-recognition-workflow)
- [NinjaClawBot and OpenClaw Mode Testing](#ninjaclawbot-and-openclaw-mode-testing)
- [Full Command-Line Reference](#full-command-line-reference)
- [Appendix](#appendix)

---

## Features

| Feature | Description |
|---|---|
| **Standalone-first workflow** | You can install and test `pi5camera` by itself before connecting it to `ninjaclawbot` or OpenClaw |
| **Guided setup** | `pi5camera setup` creates or updates `camera.json` with beginner-friendly prompts |
| **Interactive tool** | Includes `camera-tool` for first-time setup, capture, recognition, and face management |
| **Normal photo capture** | Saves one still image into the configured photo directory |
| **Root-aware default storage** | Uses `<active_root>/photo` and `<active_root>/camera_data` by default |
| **Local face recognition** | Uses `face_recognition` locally instead of a paid cloud face API |
| **Second-step enrollment** | Unknown faces can be named later using saved pending recognition data |
| **Known-face management** | Can list and remove saved identities from the local database |
| **NinjaClawBot integration** | The same camera config can be reused through `ninjaclawbot` wrappers |
| **OpenClaw handoff** | The OpenClaw plugin can capture photos, recognize faces, and enroll unknown faces in a second step |

---

## Architecture

```text
pi5camera/
├── README.md
├── pyproject.toml
├── uv.lock
├── src/pi5camera/
│   ├── __init__.py
│   ├── __main__.py              # CLI entry point
│   ├── driver.py                # Compatibility re-exports
│   ├── errors.py                # Shared pi5camera exceptions
│   ├── models.py                # Shared capture and face models
│   ├── cli/
│   │   ├── _common.py           # Shared CLI helpers
│   │   ├── camera_tool.py       # Beginner-friendly interactive menu
│   │   ├── capture_cmd.py       # One-shot photo capture
│   │   ├── doctor.py            # Readiness and directory checks
│   │   ├── enroll_cmd.py        # Face enrollment commands
│   │   ├── manage_faces_cmd.py  # Known-face list and removal
│   │   ├── recognize_cmd.py     # Face recognition workflow
│   │   ├── setup_cmd.py         # Guided setup wizard
│   │   └── status.py            # Config and readiness summary
│   ├── config/
│   │   └── config_manager.py    # camera.json defaults and load/save
│   ├── core/
│   │   ├── camera_backend.py    # Picamera2 loader
│   │   ├── capture.py           # Still-photo helpers
│   │   ├── enrollment.py        # Known-face enrollment helpers
│   │   └── recognition.py       # Face matching workflow
│   ├── recognition/
│   │   ├── base.py              # Recognition backend interface
│   │   └── face_recognition_backend.py
│   └── storage/
│       └── face_store.py        # Photo output, encodings, pending records
└── tests/
    ├── test_config_manager.py
    └── test_recognition_flow.py
```

Storage layout created by setup and normal use:

```text
<active_root>/
├── camera.json
├── photo/
│   ├── photo-20260324-101500.jpg
│   └── recognition-20260324-101640.jpg
└── camera_data/
    ├── index/
    │   └── encodings.json
    ├── known_faces/
    │   └── Alice/
    └── pending/
        └── <recognition_id>/
            ├── record.json
            └── face-1.jpg
```

---

## Installation

This section is the complete standalone installation path for Raspberry Pi 5.
All standalone examples below assume your working folder is `~/pi5camera`.

If your copy lives somewhere else, replace `~/pi5camera` with your real folder
path in each command.

### Prerequisites

Before you start, make sure you have:

1. A **Raspberry Pi 5** with Raspberry Pi OS Bookworm or newer
2. A **Raspberry Pi camera module** that is already connected correctly
3. An **internet connection** for the first installation
4. A terminal window with permission to run `sudo`

### Step 1. Prepare the standalone `pi5camera` folder

If you already have a standalone `pi5camera` folder, just move into it:

```bash
cd ~/pi5camera
```

If you do not have it yet, create it from the repository:

```bash
cd ~
git clone https://github.com/Nilcreator/NinjaClawBot.git
cp -R ~/NinjaClawBot/pi5camera ~/pi5camera
cd ~/pi5camera
```

What this does:

- downloads the project source code
- creates a standalone `~/pi5camera` working folder
- keeps your camera config and virtual environment separate from the larger
  NinjaClawBot workspace

What you should expect:

- your terminal ends inside `~/pi5camera`
- later commands create `camera.json`, `photo/`, `camera_data/`, and `.venv`
  inside this standalone folder

### Step 2. Install `uv`

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.zshrc
```

What this does:

- installs `uv`, the tool this project uses to create a virtual environment,
  install Python packages, and run commands

What you should expect:

- the installer finishes without errors
- `uv --version` works in a new shell

If your shell is not `zsh`, open a new terminal window or load the correct
shell profile for your shell.

### Step 3. Run the Raspberry Pi bootstrap installer

```bash
cd ~/pi5camera
./scripts/bootstrap-rpi-standalone.sh
```

What this does:

- installs the Raspberry Pi camera and build packages needed by `pi5camera`
- installs optional Raspberry Pi camera and recognition packages such as
  `python3-libcamera`, `python3-scipy`, `python3-dlib`, and
  `python3-face-recognition` when they are available on the host image
- works whether this `pi5camera` folder is still inside the full
  NinjaClawBot workspace or has been copied out and used on its own
- recreates the local `.venv` environment from scratch with
  `/usr/bin/python3 -m venv --system-site-packages`
- runs `uv sync --active --extra dev`
- installs a venv-local startup hook so plain `uv run python` and
  `uv run pi5camera ...` commands resolve selected Raspberry Pi camera and
  recognition modules from the system Python before user imports happen,
  without overriding unrelated venv packages such as `Pillow`
- prefers the Raspberry Pi system recognition stack on ARM boards and only
  falls back to a Python package install if those system packages are not
  available
- runs `uv run pi5camera doctor` and a final
  `uv run python -c "import libcamera, picamera2, face_recognition; print('imports-ok')"`
  check

What you should expect:

- the command finishes successfully
- `uv run pi5camera --help` works afterward
- `uv run python -c "import libcamera, picamera2, face_recognition; print('imports-ok')"`
  works afterward

If you need the manual install path or the `--skip-apt` shortcut, see
[Alternative Raspberry Pi Install Methods](#alternative-raspberry-pi-install-methods)
in the appendix.

### Step 4. Confirm the command-line tools are available

```bash
cd ~/pi5camera
uv run pi5camera --help
```

What this does:

- confirms that the package installed correctly

What you should expect:

- a help screen that lists commands such as `camera-tool`, `setup`, `doctor`,
  `status`, `capture`, `recognize`, `enroll`, and `manage-faces`

### Step 5. Confirm the Raspberry Pi camera stack can see the module

```bash
rpicam-hello --list-cameras
```

What this does:

- asks the Raspberry Pi camera stack to list connected cameras

What you should expect:

- at least one detected camera is listed
- if no camera is listed, fix the ribbon cable or camera seating before you
  continue

---

## Getting Started

This is the safest first-run path for a brand-new `pi5camera` setup.

### Step 1. Open `camera-tool`

```bash
cd ~/pi5camera
uv run pi5camera camera-tool
```

What this does:

- opens the interactive camera menu
- gives you the simplest path to setup, readiness checks, capture, and face
  testing

What you should expect:

- a menu with:
  - `Run setup wizard`
  - `Run doctor`
  - `Show status`
  - `Capture photo`
  - `Recognize faces`
  - `List known faces`
  - `Remove a known face`

### Step 2. Run the setup wizard from `camera-tool`

Inside `camera-tool`, choose:

- `1. Run setup wizard`

Recommended first choices:

- `Photo directory`: keep the suggested absolute path
- `Camera data directory`: keep the suggested absolute path
- `Image width`: start with `1280`
- `Image height`: start with `720`
- `Camera warm-up time`: start with `1.0`
- `Use camera preview when supported?`: `n`
- `Autofocus mode`: `continuous`
- `Recognition tolerance`: start with `0.6`
- `Save crops for unknown faces`: `y`
- `Pending-recognition expiry`: keep `86400`

Purpose:

- writes the actual camera profile into `~/pi5camera/camera.json`
- saves predictable folders for photos and local face data

Expected result:

- the wizard saves `camera.json`
- it prints the resolved photo directory and camera data directory
- by default those folders become:
  - `~/pi5camera/photo`
  - `~/pi5camera/camera_data`

### Step 3. Run `doctor`

```bash
cd ~/pi5camera
uv run pi5camera doctor
```

Purpose:

- verifies the camera config
- verifies the storage directories
- checks whether `Picamera2` and `face_recognition` are importable

Expected result:

- the config path and both storage directories are shown
- success ends with `pi5camera doctor passed.` or
  `pi5camera doctor passed with warnings.`

### Step 4. Capture the first normal photo

```bash
cd ~/pi5camera
uv run pi5camera capture
```

Purpose:

- takes one still image using the configured camera

Expected result:

- a file is created under `~/pi5camera/photo/`
- the terminal prints the saved absolute path

Optional output-path example:

```bash
cd ~/pi5camera
uv run pi5camera capture --output ~/Pictures
```

This saves the photo into the directory you provide instead of the default
`photo/` folder.

### Step 5. Run the first recognition cycle

Recommended first run from the interactive tool:

```bash
cd ~/pi5camera
uv run pi5camera camera-tool
```

Then choose:

- `5. Recognize faces`

Purpose:

- takes a fresh photo
- checks it against the saved face database
- asks for a name if the face is new

Expected result:

- if the face is already known, the saved name is shown
- if the face is unknown, the tool lets you enter a name immediately
- the enrolled face is saved under `camera_data/known_faces/`

### Step 6. Check the current status

```bash
cd ~/pi5camera
uv run pi5camera status
```

Purpose:

- shows the current config path, active root, storage paths, image size, and
  backend readiness

Expected result:

- you can confirm which `camera.json` is active
- you can confirm whether the package sees `Picamera2` and
  `face_recognition`

### Step 7. Test the face database controls

List saved identities:

```bash
cd ~/pi5camera
uv run pi5camera manage-faces list
```

Remove one saved identity:

```bash
cd ~/pi5camera
uv run pi5camera manage-faces remove Alice
```

Purpose:

- confirms that saved identities can be reviewed and cleaned up safely

Expected result:

- `list` prints the saved names
- `remove` deletes the selected identity and its stored face crops

---

## Face Recognition Workflow

This section explains the three face-recognition flows that matter most in real
use.

### Interactive flow from `camera-tool`

This is the easiest path for normal users.

1. Run `uv run pi5camera camera-tool`
2. Choose `Recognize faces`
3. Let `pi5camera` capture a fresh photo
4. If the face is known, the saved name is shown immediately
5. If the face is unknown, `camera-tool` asks for the new name
6. If you enter a name, that face is enrolled for future matches

### Direct command-line recognition flow

If you want a direct CLI command instead of the menu:

```bash
cd ~/pi5camera
uv run pi5camera recognize --prompt-for-names
```

This does the same live-recognition flow, but without opening the full menu.

You can also recognize faces from an existing image:

```bash
cd ~/pi5camera
uv run pi5camera recognize --image-file ~/Pictures/group_photo.jpg
```

### Second-step enrollment flow for unknown faces

When you run recognition without `--prompt-for-names`, unknown faces are saved
as pending records. That is useful when another tool or chat agent should ask
for the name later.

Step 1. Run recognition:

```bash
cd ~/pi5camera
uv run pi5camera recognize
```

If the face is unknown, the output includes:

- `recognition_id`
- one or more `face_id` values such as `face-1`

Step 2. Enroll that same saved unknown face later:

```bash
cd ~/pi5camera
uv run pi5camera enroll \
  --name Alice \
  --recognition-id <recognition_id> \
  --face-id face-1
```

Purpose:

- lets you separate recognition from final enrollment
- keeps the exact original photo and face crop tied to the later saved name

Expected result:

- the chosen pending face is saved as a known identity
- the remaining pending record is updated or removed automatically

### Enroll directly from an existing image

If you already have a single-face image and want to save it directly:

```bash
cd ~/pi5camera
uv run pi5camera enroll --name Alice --image-file ~/Pictures/alice.jpg
```

Expected result:

- the single face in that image is cropped and saved as a known identity
- future recognition can match against it

---

## NinjaClawBot and OpenClaw Mode Testing

Once the standalone camera workflow works, you can reuse it from the full
NinjaClawBot workspace.

### Step 1. Move to the NinjaClawBot workspace

```bash
cd ~/NinjaClawBot
```

### Step 2. Install the Python environment

```bash
cd ~/NinjaClawBot
uv sync --extra dev
```

What this does:

- installs the whole workspace
- installs `pi5camera` alongside `ninjaclawbot` and the other `pi5*` packages

### Step 3. Open the root-aware `camera-tool`

```bash
cd ~/NinjaClawBot
uv run ninjaclawbot camera-tool
```

Purpose:

- opens the same interactive camera flow, but uses the NinjaClawBot root
  `camera.json`

Expected result:

- the default photo directory becomes `~/NinjaClawBot/photo`
- the default face-data directory becomes `~/NinjaClawBot/camera_data`

### Step 4. Run the integrated health check

```bash
cd ~/NinjaClawBot
uv run ninjaclawbot health-check
```

Expected result:

- the health output now includes a `camera` section

### Step 5. Test normal photo capture through `ninjaclawbot`

```bash
cd ~/NinjaClawBot
uv run ninjaclawbot capture-photo
```

Expected result:

- a normal photo is saved into the configured photo directory
- the command prints the saved absolute path

### Step 6. Test face recognition through `ninjaclawbot`

```bash
cd ~/NinjaClawBot
uv run ninjaclawbot recognize-faces
```

Expected result:

- known faces return saved names
- unknown faces return `recognition_id` and `face_id`

### Step 7. Test second-step enrollment through `ninjaclawbot`

If the face is unknown, use the returned ids:

```bash
cd ~/NinjaClawBot
uv run ninjaclawbot enroll-pending-face \
  --recognition-id <recognition_id> \
  --face-id face-1 \
  "Alice"
```

Expected result:

- the pending face is saved under the provided name

### Step 8. Test the OpenClaw tool surface

Once the local `ninjaclawbot` flow works, the OpenClaw plugin exposes:

- `ninjaclawbot_capture_photo`
- `ninjaclawbot_recognize_faces`
- `ninjaclawbot_enroll_pending_face`

Recommended OpenClaw validation order:

1. ask OpenClaw to take a normal photo
2. ask OpenClaw to recognize a face
3. if the face is unknown, give OpenClaw the name in a later turn
4. confirm OpenClaw can save that name and recognize the same person later

---

## Full Command-Line Reference

### Global option

All commands support:

```bash
uv run pi5camera --config-file /absolute/path/to/camera.json <command>
```

This lets you point `pi5camera` at a different root config file when needed.

### Setup and status

```bash
cd ~/pi5camera
uv run pi5camera setup
uv run pi5camera doctor
uv run pi5camera status
uv run pi5camera camera-tool
```

Purpose:

- `setup`: guided first-run wizard
- `doctor`: config, directory, and backend readiness check
- `status`: current config and local summary
- `camera-tool`: beginner-friendly interactive menu

### Photo capture and recognition

```bash
cd ~/pi5camera
uv run pi5camera capture
uv run pi5camera capture --output ~/Pictures --prefix snapshot
uv run pi5camera recognize
uv run pi5camera recognize --prompt-for-names
uv run pi5camera recognize --image-file ~/Pictures/group.jpg
```

Purpose:

- `capture`: one-shot still photo
- `recognize`: live or file-based face recognition
- `--prompt-for-names`: interactive naming for unknown faces

### Enrollment and face management

```bash
cd ~/pi5camera
uv run pi5camera enroll --name Alice --image-file ~/Pictures/alice.jpg
uv run pi5camera enroll --name Alice --recognition-id <recognition_id> --face-id face-1
uv run pi5camera manage-faces list
uv run pi5camera manage-faces remove Alice
```

Purpose:

- `enroll`: save a known face from an image or a pending recognition
- `manage-faces list`: show saved identities
- `manage-faces remove`: delete one saved identity

---

## Appendix

### Appendix Contents

- [Alternative Raspberry Pi Install Methods](#alternative-raspberry-pi-install-methods)
- [Problem Solving](#problem-solving)
- [Successful Standalone Checklist](#successful-standalone-checklist)
- [How the Default Save Folders Work](#how-the-default-save-folders-work)
- [How the Two-Step Unknown-Face Flow Works](#how-the-two-step-unknown-face-flow-works)
- [Developer Validation Commands](#developer-validation-commands)

### Alternative Raspberry Pi Install Methods

If you do not want to use the recommended bootstrap installer in Step 3, use
one of these fallback paths instead.

Manual fallback if you want to install the Raspberry Pi system packages
yourself first:

```bash
sudo apt update
sudo apt install -y \
  build-essential \
  cmake \
  pkg-config \
  python3-venv \
  python3-dev \
  python3-picamera2 \
  python3-libcamera \
  python3-scipy \
  libopenblas-dev \
  liblapack-dev
```

If your Raspberry Pi OS image also provides the recognition packages directly,
install them too:

```bash
sudo apt install -y python3-dlib python3-face-recognition python3-face-recognition-models
```

Then create the environment manually:

```bash
cd ~/pi5camera
rm -rf .venv
/usr/bin/python3 -m venv --system-site-packages .venv
source .venv/bin/activate
uv sync --active --extra dev
.venv/bin/python -c "from pi5camera.environment import install_startup_import_hook; raise SystemExit(0 if install_startup_import_hook() else 1)"
```

If your image does not provide `python3-face-recognition`, install the Python
fallback after `uv sync`:

```bash
cd ~/pi5camera
source .venv/bin/activate
uv pip install --python .venv/bin/python --reinstall "face-recognition>=1.3"
```

If you already installed the required apt packages and only want to recreate the
virtual environment, use:

```bash
cd ~/pi5camera
./scripts/bootstrap-rpi-standalone.sh --skip-apt
```

### Problem Solving

#### `Picamera2 is not importable`

This usually means one of two things:

1. `python3-picamera2` is not installed in Raspberry Pi OS
2. `python3-picamera2` is installed in `/usr/bin/python3`, but your local
   `.venv` was created without system site packages

`pi5camera` includes a runtime auto-fix that detects this mismatch and installs
a targeted import finder for Raspberry Pi camera modules. If `pi5camera doctor`
shows `picamera2 (ready)`, the auto-fix is working and no manual action is
needed.

If doctor still shows `picamera2 (system-only)` or `picamera2 (missing)`,
first install the Raspberry Pi camera stack:

```bash
sudo apt update
sudo apt install -y python3-picamera2 python3-libcamera
```

Then rerun the standalone bootstrap installer:

```bash
cd ~/pi5camera
./scripts/bootstrap-rpi-standalone.sh
```

Or fix manually without the bootstrap script:

```bash
cd ~/pi5camera
rm -rf .venv
/usr/bin/python3 -m venv --system-site-packages .venv
source .venv/bin/activate
uv sync --active --extra dev
.venv/bin/python -c "from pi5camera.environment import install_startup_import_hook; raise SystemExit(0 if install_startup_import_hook() else 1)"
```

> **Important:** Always use `uv sync --active` (not plain `uv sync`) after
> creating a venv with `--system-site-packages`. Without `--active`, `uv` may
> recreate the `.venv` and lose the system-site-packages access to Picamera2.
> The bootstrap script and the manual recovery path also reinstall the
> `pi5camera` startup hook after `uv sync`, because recreating the venv can
> remove that hook.

If you want to confirm the mismatch directly, compare these two commands:

```bash
python3 -c "import sys, libcamera, picamera2; print(sys.executable); print(picamera2.__file__)"
uv run python -c "import sys, libcamera, picamera2; print(sys.executable); print(picamera2.__file__)"
```

#### `face_recognition` is not importable

This means the recognition backend is not usable in the current environment.
On Raspberry Pi, `pi5camera` now prefers the system recognition packages when
they are available, so the most common causes are:

- the Raspberry Pi recognition packages were not available on the image and the
  Python fallback has not been installed yet
- the active `.venv` contains a broken compiled extension such as `dlib`
  shadowing the system copy

Install the recommended build packages:

```bash
sudo apt update
sudo apt install -y build-essential cmake pkg-config python3-dev python3-scipy libopenblas-dev liblapack-dev
```

Then reinstall:

```bash
cd ~/pi5camera
./scripts/bootstrap-rpi-standalone.sh
```

If you want to check the environment directly after reinstalling:

```bash
cd ~/pi5camera
uv run python -c "import face_recognition; print('face-recognition-ok')"
uv run pi5camera doctor
```

If the Raspberry Pi OS image does not provide `python3-face-recognition`, use
the Python fallback manually:

```bash
cd ~/pi5camera
source .venv/bin/activate
uv pip install --python .venv/bin/python --reinstall "face-recognition>=1.3"
.venv/bin/python -c "from pi5camera.environment import install_startup_import_hook; raise SystemExit(0 if install_startup_import_hook() else 1)"
uv run pi5camera doctor
```

If doctor shows an error like `file too short` for `_dlib_pybind11`, that
usually means a stale or corrupted compiled extension is sitting inside
`.venv`. Rerun the bootstrap installer so it rebuilds `.venv` from scratch.

If `recognize` fails before taking a new photo, that is expected when the
recognition backend is missing. `pi5camera` now checks the recognition stack
before starting a live capture so failed imports do not create unnecessary
photos.

#### `No faces were found`

This means the image did not contain a clear detectable face.

Try this path:

1. move into better lighting
2. keep only one face in the frame
3. face the camera more directly
4. rerun:

```bash
uv run pi5camera recognize
```

#### `Found 2 faces ... Use a single-face image for enrollment`

This happens when you try to enroll from an image that contains more than one
face.

Fix path:

```bash
uv run pi5camera enroll --name Alice --image-file /path/to/single-face-image.jpg
```

Use an image that contains only one person for direct enrollment.

#### `Unknown pending recognition`

This means the pending record expired or the id was incorrect.

Fix path:

1. rerun recognition
2. copy the new `recognition_id`
3. use the returned `face_id`
4. enroll again

### Successful Standalone Checklist

You have a healthy first standalone `pi5camera` setup when all of these are
true:

- `uv run pi5camera doctor` passes with no blocking errors
- `uv run pi5camera status` shows the expected `camera.json`
- `uv run pi5camera capture` saves a photo into `photo/`
- `uv run pi5camera recognize --prompt-for-names` works on a fresh photo
- `uv run pi5camera manage-faces list` shows the saved name
- rerunning `recognize` returns the saved name for the same person

### How the Default Save Folders Work

`pi5camera` chooses storage folders from the active config root.

Standalone default:

- config file: `~/pi5camera/camera.json`
- photo directory: `~/pi5camera/photo`
- face data directory: `~/pi5camera/camera_data`

NinjaClawBot workspace default:

- config file: `~/NinjaClawBot/camera.json`
- photo directory: `~/NinjaClawBot/photo`
- face data directory: `~/NinjaClawBot/camera_data`

You can override these during setup with absolute paths if you prefer a
different folder layout.

### How the Two-Step Unknown-Face Flow Works

When recognition finds an unknown face, `pi5camera` can save a pending record
instead of forcing immediate enrollment.

That record stores:

- the original photo path
- the unknown face crop
- the encoding
- the `recognition_id`
- one or more `face_id` values

This is what makes the later save-name step reliable for:

- command-line follow-up
- `ninjaclawbot` integration
- OpenClaw conversations across multiple turns

### Developer Validation Commands

```bash
cd ~/pi5camera
uv run --extra dev python -m compileall src tests
uv run --extra dev ruff check src tests
uv run --extra dev ruff format --check src tests
uv run --extra dev pytest -q tests -c pyproject.toml
```
