# pi5camera Development Plan — Full Rebuild

Last updated: 2026-03-27

---

## 1. Purpose

This document replaces the previous `CameraDevelopment.md` in its entirety.

It has five jobs:

1. present the results of a comprehensive line-by-line code audit of the
   current `pi5camera` implementation
2. document the critical bugs, architectural weaknesses, and stability risks
   found during the audit
3. present research findings on face-recognition backends compatible with the
   Raspberry Pi 5, with a focus on RAM efficiency and dlib-free alternatives
4. define a phased plan to rewrite the library from scratch
5. provide a practical execution, validation, and documentation guide

---

## 2. Overall Development Goal

`pi5camera` is the standalone-first camera library for the NinjaClawBot
workspace.

The target product remains unchanged:

- a local Raspberry Pi 5 camera tool that works by itself
- a guided interactive setup and testing tool for users
- a local face-recognition workflow built on a free, open-source, dlib-free
  backend that runs within the limited RAM of a Raspberry Pi 5
- a thin `ninjaclawbot` integration layer for AI-driven orchestration
- an OpenClaw plugin surface that reuses `ninjaclawbot` actions

---

## 3. Code Audit Results

### 3.1 Audit scope

Every source and test file in `pi5camera/` was reviewed line by line using
Serena symbolic analysis. The files audited were:

**Package scaffold (5 files)**

| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | 61 | Lazy public exports |
| `__main__.py` | 88 | Click CLI entry point with LazyGroup |
| `driver.py` | 58 | Compatibility re-exports (near-duplicate of `__init__.py`) |
| `errors.py` | 24 | Exception hierarchy |
| `models.py` | 89 | Dataclasses: FaceBoundingBox, FaceResult, EncodedFace, CaptureResult |

**Environment and bootstrap (2 files)**

| File | Lines | Purpose |
|------|-------|---------|
| `environment.py` | 538 | Venv+system-package injection, import probes, startup hooks |
| `src/sitecustomize.py` | 89 | Auto-startup hook for system package injection |

**Core workflows (4 files)**

| File | Lines | Purpose |
|------|-------|---------|
| `core/camera_backend.py` | 141 | Picamera2 still-capture backend |
| `core/capture.py` | 54 | One-shot capture orchestration |
| `core/recognition.py` | 107 | Face recognition workflow |
| `core/enrollment.py` | 88 | Known-face enrollment from images or pending records |

**Storage (1 file)**

| File | Lines | Purpose |
|------|-------|---------|
| `storage/face_store.py` | 276 | Filesystem-backed face index, pending records, crops |

**Config (1 file)**

| File | Lines | Purpose |
|------|-------|---------|
| `config/config_manager.py` | 195 | camera.json loading, saving, merging |

**Recognition backend (2 files)**

| File | Lines | Purpose |
|------|-------|---------|
| `recognition/base.py` | 14 | Backend protocol definition |
| `recognition/face_recognition_backend.py` | 74 | face_recognition package wrapper |

**CLI commands (9 files)**

| File | Lines | Purpose |
|------|-------|---------|
| `cli/__init__.py` | 20 | Eager command imports (opposite of lazy main) |
| `cli/_common.py` | 57 | Shared helpers: load_manager, describe_camera_stack |
| `cli/camera_tool.py` | 59 | Interactive menu loop |
| `cli/setup_cmd.py` | 94 | Guided setup wizard |
| `cli/capture_cmd.py` | 30 | One-shot photo capture |
| `cli/doctor.py` | 68 | Backend and directory health check |
| `cli/status.py` | 41 | Config and readiness summary |
| `cli/recognize_cmd.py` | 79 | Recognition with optional name prompting |
| `cli/enroll_cmd.py` | 50 | Enroll from image or pending record |
| `cli/manage_faces_cmd.py` | 50 | List/remove known faces |

**Tests (5 files)**

| File | Lines | Purpose |
|------|-------|---------|
| `tests/test_environment.py` | 261 | Environment probe and injection tests |
| `tests/test_config_manager.py` | 37 | Config defaults and output path tests |
| `tests/test_recognition_flow.py` | 154 | Recognize → enroll integration tests |
| `tests/test_cli_startup.py` | 46 | Lightweight import and CLI help tests |
| `tests/test_sitecustomize.py` | 39 | Sitecustomize targeted finder tests |

**Build config (1 file)**

| File | Lines | Purpose |
|------|-------|---------|
| `pyproject.toml` | 31 | Package metadata, dependencies, tool config |

**Total audited**: ~2,712 lines across 30 files.

---

### 3.2 Critical bugs found

#### BUG-01: `face-recognition` dependency is excluded on Pi ARM64

**File**: `pyproject.toml`
**Severity**: Critical — face recognition cannot be installed via pip on the
target hardware.

```toml
"face-recognition>=1.3; platform_system == 'Linux' and platform_machine != 'aarch64' and platform_machine != 'armv7l' and platform_machine != 'armv6l'"
```

The marker explicitly excludes `aarch64` (Raspberry Pi 5's architecture). This
means `face-recognition` will never be installed by `uv sync` on the Pi. The
code expects runtime injection from system packages, but this only works if the
user manually installs `face-recognition` and `dlib` via `apt` or `pip` outside
the managed environment. This is fragile and undocumented as a hard requirement.

#### BUG-02: `dlib` compilation causes OOM crashes on Raspberry Pi

**File**: `face_recognition_backend.py` (indirect dependency)
**Severity**: Critical — the current face-recognition backend depends on
`dlib`, which requires C++ compilation from source on ARM64. On a Pi 5 with 4GB
of RAM, `dlib` compilation routinely triggers Out-of-Memory kills. Even with
swap management, success is unreliable and the process can take 30+ minutes.

#### BUG-03: `driver.py` is a near-exact duplicate of `__init__.py`

**File**: `driver.py`
**Severity**: Medium — maintenance hazard.

Both files contain identical lazy `__getattr__` handlers and `__all__` exports.
Any change to one must be mirrored to the other. The only difference is the
error message string: `"module 'pi5camera' has no attribute"` vs
`"module 'pi5camera.driver' has no attribute"`.

#### BUG-04: `cli/__init__.py` eagerly imports all commands

**File**: `cli/__init__.py`
**Severity**: Medium — undermines the lazy loading architecture.

The `__main__.py` carefully uses `LazyGroup` to avoid importing heavy modules at
startup. But `cli/__init__.py` does `from .camera_tool import camera_tool` etc.,
which eagerly imports all CLI commands and their dependencies. If anything
imports `pi5camera.cli`, the lazy loading is defeated. The `camera_tool.py`
itself eagerly imports `capture_cmd`, `doctor`, `manage_faces_cmd`,
`recognize_cmd`, `setup_cmd`, and `status` at module level.

#### BUG-05: `core/__init__.py` eagerly imports all core workflows

**File**: `core/__init__.py`
**Severity**: Medium — same problem as BUG-04.

```python
from .capture import capture_photo
from .enrollment import enroll_face_from_image, enroll_pending_face
from .recognition import recognize_faces
```

This triggers loading of `Pillow`, `face_store`, and eventually attempts to load
`face_recognition` the moment `pi5camera.core` is imported anywhere.

#### BUG-06: Timestamp collision risk in file naming

**File**: `face_store.py` line 23
**Severity**: Low — but causes silent overwrites.

```python
def _timestamp() -> str:
    return _utc_now().strftime("%Y%m%d-%H%M%S")
```

Resolution is only to the second. If two captures or enrollments happen within
the same second, file paths collide and data is silently overwritten.

#### BUG-07: `capture.py` suppresses original `CaptureError` on storage failure

**File**: `capture.py`
**Severity**: Low — error masking.

The `except OSError` handler in `capture_photo` will catch filesystem failures
but not camera failures. However, if a `CaptureError` is raised by the backend,
the `finally` block runs `backend.close()` which swallows exceptions silently —
this is actually correct. But the `except OSError` re-raises as `StorageError`,
which could mask the real error if the backend raised an `OSError`-subclass.

#### BUG-08: `sitecustomize.py` and `environment.py` duplicate the same logic

**File**: `src/sitecustomize.py`, `environment.py`
**Severity**: Medium — two independent implementations of the same
system-package injection pattern.

Both files contain their own `_is_virtual_environment()`, site-packages
detection, `MetaPathFinder` subclass, and installation logic. They use different
marker strings. If one is updated without the other, behavior diverges.

#### BUG-09: `_merge_config` silently allows `None` to replace dict sections

**File**: `config_manager.py` line 53-54
**Severity**: Medium — can corrupt config.

```python
if value is None:
    merged[key] = None
    continue
```

If a user's `camera.json` has `"paths": null`, the config manager sets
`paths = None`. Then `_apply_runtime_defaults` tries `config.get("paths")` and
gets `None`, which fails the `isinstance(paths, dict)` check and raises
`ConfigError`. This is technically caught, but the error message is unhelpful:
"Config key 'paths' must be an object." without explaining that `null` in the
JSON caused it.

#### BUG-10: `recognition.py` indexes faces starting from 1 but `face_id` is string

**File**: `recognition.py` line 74
**Severity**: Low — inconsistency.

Faces are indexed `enumerate(detected, start=1)` producing `face_id = "face-1"`,
`"face-2"`, etc. But the `enroll_pending_face` function searches for
`face_id` by string comparison: `str(face.get("face_id")) == face_id`. This
works but is fragile if the indexing ever changes.

---

### 3.3 Architectural weaknesses

#### ARCH-01: Over-engineered environment/venv injection system

The `environment.py` module alone is 538 lines — nearly 20% of the entire
library. It implements:

- subprocess-based Python probing
- system site-package detection
- custom `MetaPathFinder` for selective module injection
- `.pth` file generation
- startup helper code generation
- venv repair guidance text
- separate picamera2 and face_recognition environment descriptions

This complexity addresses a real problem (system packages not visible in venvs)
but the solution is too heavy for a camera library. The same pattern is then
duplicated in `sitecustomize.py`.

A rebuild should simplify this to:

- a single environment probe function
- documented bootstrap scripts
- no runtime `.pth` file or startup hook generation

#### ARCH-02: No backend abstraction for camera capture

The `camera_backend.py` hardcodes `Picamera2StillBackend` as the only backend.
The `build_camera_backend` function ignores any config and always returns
`Picamera2StillBackend`. There is no mock/stub backend for macOS development
or test automation.

#### ARCH-03: Euclidean distance matching is reimplemented manually

The `recognition.py` module implements its own `_euclidean_distance` and
`_best_known_match` functions. The `face_recognition` library provides
`face_recognition.face_distance()` and `face_recognition.compare_faces()` which
are optimized and tested. The manual reimplementation is error-prone and slower.

However, since the rebuild will move away from `face_recognition`+dlib entirely,
this point becomes moot — the new backend will need its own distance function.

#### ARCH-04: No resource cleanup protocol

The `Picamera2StillBackend` creates a `Picamera2` instance in `__init__` and
only closes it in the `close()` method. It does not implement `__enter__` /
`__exit__` context manager protocol. If an exception occurs between
construction and `close()`, camera resources leak.

#### ARCH-05: `FaceStore` mixes storage, indexing, and pending-record lifecycle

The `FaceStore` class (276 lines) handles:

- directory creation
- photo path generation
- face index CRUD
- face crop generation
- pending-recognition record CRUD
- TTL-based expiry purging

This should be split into separate concerns: a photo storage helper, a face
index manager, and a pending-record manager.

---

### 3.4 Test coverage gaps

Current test counts:

| Test file | Tests | Coverage area |
|-----------|-------|---------------|
| `test_environment.py` | 7 | Environment probing, injection |
| `test_config_manager.py` | 2 | Config defaults, output path |
| `test_recognition_flow.py` | 4 | Recognize + enroll integration |
| `test_cli_startup.py` | 2 | Lightweight import checks |
| `test_sitecustomize.py` | 3 | Sitecustomize finder |

**Missing test coverage:**

- Camera backend construction and capture (no mock backend exists)
- `FaceStore` CRUD operations (create, read, update, delete known faces)
- Pending-record expiry and TTL enforcement
- Config merge edge cases (null values, invalid types, missing sections)
- CLI command execution (only `--help` is tested)
- Multi-face recognition ordering
- Error paths: corrupted index recovery, missing photo directory, camera failure
- `driver.py` re-export behavior

---

## 4. Face Recognition Research

### 4.1 Problem statement

The current library depends on `face_recognition` which requires `dlib`. On
Raspberry Pi 5 (ARM64, typically 4GB or 8GB RAM):

- `dlib` must be compiled from C++ source (no ARM64 wheels are published)
- Compilation needs 2-3GB of RAM and routinely triggers OOM kills
- Even with swap management, compilation takes 30+ minutes and is unreliable
- The pyproject.toml explicitly excludes ARM64 from the dependency marker
- Success requires manual system-level intervention that is poorly documented

This makes the current approach unacceptable for a library that should be
installable with a simple `uv sync`.

### 4.2 Requirements for the replacement backend

The replacement face-recognition backend must:

1. be free and open source (MIT, Apache 2.0, or similar)
2. install on ARM64 Linux without compiling C++ from source
3. run face detection and embedding generation within 2GB of peak RAM
4. work offline — no cloud API dependency
5. support the existing workflow: detect → encode → compare → enroll
6. have pre-built Python wheels or be pip-installable on aarch64

### 4.3 Researched alternatives

#### Option A: MediaPipe face detection + OpenCV DNN FaceNet embeddings

**Face detection**: Google's MediaPipe provides lightweight, optimized face
detection models that run efficiently on ARM64. MediaPipe installs via pip with
pre-built wheels (`mediapipe`) on Linux ARM64. It detects faces with 6 key
landmarks and can handle multiple faces in a single frame.

**Face embeddings**: OpenCV's DNN module can load a pre-trained FaceNet or
VGGFace2 model in ONNX format to generate 128-d or 256-d face embeddings. This
avoids dlib entirely. OpenCV (`opencv-python-headless`) has pre-built ARM64
wheels.

**Pros:**
- No dlib dependency
- No C++ compilation required
- MediaPipe is highly optimized for ARM CPUs
- Low peak RAM usage (~200-400 MB for detection + embedding)
- Well-documented Raspberry Pi 5 support
- Pre-built ARM64 wheels available
- Google-backed, actively maintained

**Cons:**
- MediaPipe does face detection, not recognition (embeddings need separate model)
- Requires managing a small ONNX model file (~5-30 MB)
- Slightly more integration work than a single `face_recognition.face_encodings()` call

**Verdict**: **Recommended primary backend for the rebuild.**

#### Option B: OpenCV DNN face detection + FaceNet ONNX embeddings (no MediaPipe)

Same as Option A but uses OpenCV's DNN module for face detection too (SSD
MobileNet or YuNet). This eliminates the MediaPipe dependency entirely and uses
only OpenCV + numpy.

**Pros:**
- Single vision library dependency (OpenCV)
- OpenCV DNN face detection runs at 8-12 FPS on Pi 5
- Minimal additional dependencies

**Cons:**
- OpenCV DNN face detection is less accurate than MediaPipe on edge cases
- More manual setup for detection model configuration

**Verdict**: Good fallback if MediaPipe installation causes issues.

#### Option C: ONNX Runtime + custom face models

Use `onnxruntime` directly with a lightweight face detection model
(e.g., UltraFace, SCRFD) and a face embedding model (MobileFaceNet, InsSightFace
ArcFace). ONNX Runtime supports Linux ARM64.

**Pros:**
- Maximum control over model selection
- Support for INT8 quantized models
- Future-proof: can swap models easily

**Cons:**
- More integration work
- `onnxruntime` ARM64 installation can be slow
- Heavier dependency than pure OpenCV

**Verdict**: Consider for a future high-accuracy backend option.

#### Option D: Keep `face_recognition` + dlib (current approach)

**Verdict**: **Rejected.** The dlib compilation problem is fundamental and
cannot be reliably solved without pre-built ARM64 wheels, which don't exist.

#### Option E: DeepFace

**Verdict**: **Rejected for first release.** Too heavy for Pi 5 first release
(pulls in TensorFlow and multiple model backends).

#### Option F: InsightFace

**Verdict**: **Rejected.** Model licensing is restrictive (non-commercial use
only for default models). Code is MIT but models are not.

### 4.4 Recommended backend strategy

**Primary backend (Phase 1)**: MediaPipe face detection + OpenCV DNN FaceNet
embedding via ONNX model.

**Dependencies to add:**
- `mediapipe` (pre-built ARM64 wheels)
- `opencv-python-headless` (pre-built ARM64 wheels)
- `numpy` (already required)

**Dependencies to remove:**
- `face-recognition` (removes dlib dependency entirely)
- `dlib` (no longer needed)

**Backend interface**: Keep the existing `RecognitionBackend` protocol but
implement a new `MediaPipeFaceNetBackend` class that uses MediaPipe for
detection and OpenCV DNN for embedding generation.

**ONNX model management**: Ship a small FaceNet ONNX model (~5-30 MB) or
download it on first use during setup. Prefer shipping with the package for
fully offline operation.

### 4.5 RAM usage comparison

| Backend | Peak RAM (detection + encoding) | Install method |
|---------|-------------------------------|----------------|
| face_recognition + dlib | ~800MB runtime, 2-3GB compile | Compile from source |
| MediaPipe + OpenCV DNN + ONNX | ~200-400 MB | Pre-built wheels |
| OpenCV DNN only | ~150-300 MB | Pre-built wheels |
| DeepFace + TF | ~1-2 GB | Pre-built wheels |

The MediaPipe + OpenCV DNN approach uses **2-4x less RAM** than the current
approach and requires **zero compilation**.

---

## 5. Key Design Decisions For The Rebuild

### 5.1 Complete rewrite, not incremental patching

The audit found 10 bugs and 5 architectural weaknesses. Many are structural and
cannot be fixed without breaking the module boundaries. A clean rewrite is the
most practical path.

The rewrite should preserve:

- the package name `pi5camera`
- the CLI command surface (`setup`, `doctor`, `status`, `capture`, `recognize`,
  `enroll`, `manage-faces`, `camera-tool`)
- the config file `camera.json` format and key structure
- the `FaceResult`, `CaptureResult`, `EncodedFace`, and `FaceBoundingBox`
  dataclass contracts
- the `RecognitionBackend` protocol
- the integration surface for `ninjaclawbot` and OpenClaw

### 5.2 Eliminate dlib dependency entirely

Replace `face_recognition` + `dlib` with MediaPipe + OpenCV DNN + FaceNet ONNX.
This removes the biggest blocker for reliable Pi 5 installation.

### 5.3 Simplify the environment/bootstrap system

Replace the 538-line `environment.py` and 89-line `sitecustomize.py` with:

- a simple environment probe (~50 lines) that checks for camera and recognition
  availability
- documented bootstrap scripts for venv setup
- no runtime `.pth` file generation
- no custom `MetaPathFinder`
- no startup helper code generation

### 5.4 Add a mock camera backend

For macOS development and test automation, implement a `StubCameraBackend` that
returns a placeholder image without accessing real hardware. Register it via
config.

### 5.5 Split `FaceStore` into focused components

- `PhotoStorage`: timestamped photo path generation, directory management
- `FaceIndex`: known-face encoding CRUD, index rebuild
- `PendingRecordManager`: pending recognition lifecycle, TTL expiry

### 5.6 Fix lazy loading throughout

- `cli/__init__.py` should be empty or only export `__all__` strings
- `core/__init__.py` should use lazy `__getattr__` like `__init__.py` does
- `camera_tool.py` should use lazy imports for subcommands

### 5.7 Add microsecond timestamps

Replace `%Y%m%d-%H%M%S` with `%Y%m%d-%H%M%S-%f` to avoid file collisions.

---

## 6. Phased Rebuild Plan

### Phase R0: Scaffold cleanup and workspace registration

Status: planned

Objective: Create a clean package scaffold with correct dependencies and no
legacy bugs.

Likely files to create or rewrite:

- `pi5camera/pyproject.toml` — replace `face-recognition` with `mediapipe` and
  `opencv-python-headless`; fix requires-python
- `pi5camera/src/pi5camera/__init__.py` — clean lazy exports
- `pi5camera/src/pi5camera/__main__.py` — keep LazyGroup, fix entrypoint
- `pi5camera/src/pi5camera/driver.py` — generate from `__init__.py`, not
  duplicate
- `pi5camera/src/pi5camera/errors.py` — keep error hierarchy, add
  `BackendNotAvailableError`
- `pi5camera/src/pi5camera/models.py` — keep dataclasses, add microsecond
  timestamp helper

Files to delete:

- `pi5camera/src/sitecustomize.py`
- `pi5camera/src/pi5camera/core/__init__.py` (replace with lazy version)
- `pi5camera/src/pi5camera/cli/__init__.py` (replace with lazy version or empty)

Validation:

- `uv lock` succeeds from workspace root
- `cd pi5camera && uv sync --extra dev` succeeds
- `python -m compileall src tests`
- `ruff check src tests`
- `ruff format --check src tests`
- `import pi5camera` does not load Pillow, OpenCV, or MediaPipe

Risk level: low

---

### Phase R1: Config, storage split, and doctor/status

Status: planned

Objective: Rewrite config management and split FaceStore into focused components.

Likely files to create or rewrite:

- `pi5camera/src/pi5camera/config/config_manager.py` — fix null-section
  handling, keep merge logic
- `pi5camera/src/pi5camera/storage/photo_storage.py` — timestamped photo
  paths with microseconds
- `pi5camera/src/pi5camera/storage/face_index.py` — known-face CRUD, index
  rebuild, corrupted index recovery
- `pi5camera/src/pi5camera/storage/pending_records.py` — pending-recognition
  lifecycle, TTL expiry
- `pi5camera/src/pi5camera/storage/__init__.py` — clean re-exports
- `pi5camera/src/pi5camera/environment.py` — simplified probe: check camera
  (rpicam-hello), check mediapipe, check opencv; ~50-80 lines max
- `pi5camera/src/pi5camera/cli/setup_cmd.py` — rewrite
- `pi5camera/src/pi5camera/cli/doctor.py` — rewrite
- `pi5camera/src/pi5camera/cli/status.py` — rewrite
- `pi5camera/src/pi5camera/cli/_common.py` — simplify
- `pi5camera/tests/test_config_manager.py` — expand
- `pi5camera/tests/test_photo_storage.py` — new
- `pi5camera/tests/test_face_index.py` — new
- `pi5camera/tests/test_pending_records.py` — new

Validation:

- `cd pi5camera && uv run --extra dev python -m compileall src tests`
- `cd pi5camera && uv run --extra dev ruff check src tests`
- `cd pi5camera && uv run --extra dev ruff format --check src tests`
- `cd pi5camera && uv run --extra dev pytest -q tests -c pyproject.toml`
- All new storage tests pass
- Config edge cases (null sections, missing keys) tested

Risk level: low

---

### Phase R2: Camera backend with mock support

Status: planned

Objective: Rewrite the camera capture backend with context manager support
and a stub backend for macOS development.

Likely files to create or rewrite:

- `pi5camera/src/pi5camera/core/camera_backend.py` — add `CameraBackend`
  protocol, `Picamera2StillBackend` (with `__enter__`/`__exit__`),
  `StubCameraBackend`
- `pi5camera/src/pi5camera/core/capture.py` — use context manager, clean error
  handling
- `pi5camera/src/pi5camera/cli/capture_cmd.py` — rewrite
- `pi5camera/tests/test_camera_backend.py` — new: test stub backend, config
  dispatch
- `pi5camera/tests/test_capture.py` — new: test capture orchestration with
  mock backend

Validation:

- Package-local quality gate passes
- Stub backend capture produces a valid JPEG
- Config dispatches to stub vs picamera2 based on a config flag
- Capture creates correct timestamped file paths

Risk level: medium (Picamera2 interaction cannot be tested on macOS)

---

### Phase R3: MediaPipe + OpenCV DNN recognition backend

Status: planned

Objective: Implement the new dlib-free face detection and embedding backend.

Likely files to create or rewrite:

- `pi5camera/src/pi5camera/recognition/base.py` — keep protocol, add
  `detect_faces` and `encode_faces` methods if needed
- `pi5camera/src/pi5camera/recognition/mediapipe_opencv_backend.py` — new:
  MediaPipe face detection + OpenCV DNN FaceNet embedding
- `pi5camera/src/pi5camera/recognition/face_recognition_backend.py` — delete
  or keep as deprecated optional backend
- `pi5camera/src/pi5camera/core/recognition.py` — rewrite with new backend
- `pi5camera/src/pi5camera/core/enrollment.py` — rewrite
- `pi5camera/tests/test_recognition_backend.py` — new: unit tests with
  synthetic face data
- `pi5camera/tests/test_recognition_flow.py` — rewrite
- `pi5camera/models/` — add FaceNet ONNX model file or download script

Dependencies to verify:

- `mediapipe` installs on macOS (development) and Linux ARM64 (Pi 5)
- `opencv-python-headless` installs on both platforms
- FaceNet ONNX model loads correctly in OpenCV DNN

Validation:

- Package-local quality gate passes
- Detection returns correct bounding boxes on test images
- Embedding generation produces consistent 128-d vectors
- Known-face comparison with euclidean distance works
- End-to-end recognize flow with mock backend passes
- No import of `face_recognition` or `dlib` anywhere

Risk level: high (core accuracy-critical change)

---

### Phase R4: Interactive camera-tool and operator UX

Status: planned

Objective: Rewrite the interactive `camera-tool` with lazy imports and clean
error handling.

Likely files to create or rewrite:

- `pi5camera/src/pi5camera/cli/camera_tool.py` — rewrite with lazy command
  imports
- `pi5camera/src/pi5camera/cli/recognize_cmd.py` — rewrite
- `pi5camera/src/pi5camera/cli/enroll_cmd.py` — rewrite
- `pi5camera/src/pi5camera/cli/manage_faces_cmd.py` — rewrite
- `pi5camera/tests/test_cli_commands.py` — new: CLI invocation tests with
  CliRunner

Validation:

- Package-local quality gate passes
- `camera-tool --help` does not load heavy dependencies
- Each CLI command exits cleanly with appropriate messages
- Interactive recognition with name prompting flow works end-to-end

Risk level: low

---

### Phase R5: `ninjaclawbot` camera integration

Status: planned

Objective: Add thin camera adapter and typed action surface in `ninjaclawbot`.

Likely files:

- `ninjaclawbot/pyproject.toml` — add optional `pi5camera` dependency
- `ninjaclawbot/src/ninjaclawbot/adapters.py` — add camera adapter
- `ninjaclawbot/src/ninjaclawbot/runtime.py` — add camera health reporting
- `ninjaclawbot/src/ninjaclawbot/actions.py` — add camera actions
- `ninjaclawbot/tests/` — test stubs

Implementation targets:

- `camera_health_check`
- `capture_photo`
- `recognize_faces`
- `enroll_pending_face`
- All actions return structured results, never block on TTY

Validation:

- `ninjaclawbot` quality gate passes
- Camera unavailability is reported gracefully

Risk level: medium

---

### Phase R6: OpenClaw plugin camera tools

Status: planned

Objective: Expose camera actions through the OpenClaw plugin.

Likely files:

- `integrations/openclaw/ninjaclawbot-plugin/src/schemas.ts`
- `integrations/openclaw/ninjaclawbot-plugin/src/index.ts`

Plugin tools:

- `ninjaclawbot_capture_photo`
- `ninjaclawbot_recognize_faces`
- `ninjaclawbot_enroll_pending_face`

Validation:

- `npm run typecheck`
- `npm test`

Risk level: low-medium

---

### Phase R7: Documentation update

Status: planned

Objective: Update all project documentation to reflect the new camera library.

Files:

- `README.md`
- `DevelopmentGuide.md`
- `InstallationGuide.md`
- `pi5camera/README.md`
- `ninjaclawbot/README.md`
- `backup/CameraDevelopment.md`
- `backup/DevelopmentLog.md`

Risk level: low

---

### Phase R8: Raspberry Pi 5 field validation

Status: planned

Objective: Validate the rebuilt library on Raspberry Pi 5 hardware.

Safe smoke tests:

- `rpicam-hello --list-cameras`
- `uv run pi5camera doctor`
- `uv run pi5camera status`
- One still capture with no recognition

Communication/interface tests:

- Repeated still captures
- Known-face recognition
- Unknown-face detection
- Enrollment and re-recognition
- Multi-face detection and ordering

Performance tests:

- Measure RAM usage during detection + embedding (target: < 400 MB)
- Measure single-frame recognition latency (target: < 3 seconds)
- Check thermal throttling during repeated cycles

Long-run tests:

- Repeated capture+recognize cycles (10+ rounds)
- Storage growth monitoring
- Recovery after camera disconnect

Risk level: medium

---

## 7. Quality Gates

### `pi5camera` package gate (all phases)

```bash
cd pi5camera && uv run --extra dev python -m compileall src tests
cd pi5camera && uv run --extra dev ruff check src tests
cd pi5camera && uv run --extra dev ruff format --check src tests
cd pi5camera && uv run --extra dev pytest -q tests -c pyproject.toml
```

### Root workspace gate (when shared files change)

```bash
uv run --extra dev python -m compileall .
uv run --extra dev ruff check .
uv run --extra dev ruff format --check .
```

### OpenClaw plugin gate (Phase R6)

```bash
cd integrations/openclaw/ninjaclawbot-plugin && npm run typecheck
cd integrations/openclaw/ninjaclawbot-plugin && npm test
```

---

## 8. Raspberry Pi Validation Categories

### Safe smoke tests

- `rpicam-hello --list-cameras`
- `uv run pi5camera doctor`
- `uv run pi5camera status`
- One still capture with no recognition

### Communication/interface tests

- Repeated still captures
- Metadata capture
- Known-face recognition
- Unknown-face detection
- Enrollment and re-recognition

### Performance tests

- RAM usage measurement: `ps -o rss= -p $PID` during recognition
- Latency measurement: time from capture command to result
- Thermal monitoring: `vcgencmd measure_temp` during repeated cycles

### Long-run tests

- 10+ capture+recognize cycles
- Storage growth in `photo/` and `camera_data/`
- Recovery after camera disconnect and reconnect

---

## 9. References

### Audit sources

All 30 files in `pi5camera/` were audited line-by-line via Serena on 2026-03-27.

### Face recognition research sources (checked 2026-03-27)

- MediaPipe: https://developers.google.com/mediapipe
- OpenCV DNN module: https://docs.opencv.org/4.x/d2/d58/tutorial_table_of_content_dnn.html
- FaceNet model: https://github.com/davidsandberg/facenet
- ONNX Runtime ARM64: https://onnxruntime.ai/docs/get-started/with-python.html
- face_recognition/dlib Pi issues: https://github.com/ageitgey/face_recognition/issues
- dlib ARM64 compilation OOM: confirmed via field reports and conversation
  c4ceb32c-5349-4222-b221-c375ebb1b41d

### Previous planning sources

- `README.md`
- `DevelopmentGuide.md`
- `InstallationGuide.md`
- `backup/DevelopmentPlan.md`
- `backup/MicDevelopment.md`
- `ninjaclawbot/README.md`
