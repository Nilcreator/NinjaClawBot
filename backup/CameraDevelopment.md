# pi5camera Development Plan

Last updated: 2026-03-24

## 1. Purpose

This document is the current planning and status guide for `pi5camera`.

It has four jobs:

1. lock the product specification around the approved standalone and integrated
   camera use cases
2. refine the earlier high-level implementation plan into a repository-ready
   phased build plan
3. define the correct ownership boundary between `pi5camera`, `ninjaclawbot`,
   and the OpenClaw plugin
4. provide a practical execution and validation guide before coding begins

This document intentionally follows the more practical structure now used by
`MicDevelopment.md`:

- overall development goal and product spec
- current repository and research findings
- key design decisions
- phased implementation plan
- validation and Raspberry Pi execution guidance

## 2. Overall Development Goal

`pi5camera` is the standalone-first camera library planned for the
NinjaClawBot workspace.

The target product is:

- a local Raspberry Pi camera tool that works by itself
- a guided interactive setup and testing tool for users
- a local face-recognition workflow built on a free open-source backend
- a thin `ninjaclawbot` integration layer for AI-driven orchestration
- an optional OpenClaw plugin surface that reuses `ninjaclawbot` actions rather
  than calling raw camera code directly

The long-term finished user experience should be:

1. install the NinjaClawBot workspace with `uv sync`
2. set up the hardware libraries
3. run `uv run pi5camera camera-tool`
4. capture a photo or run face recognition
5. if a face is new during the interactive local flow, type a name and save the
   enrollment
6. if a face is already known, receive the stored name automatically
7. optionally call the same camera capability through `ninjaclawbot`
8. optionally let OpenClaw chain camera actions with robot actions such as
   servo movement, expression playback, and status reporting

## 3. Product Rules And User Clarifications

These are the locked product rules for the first build.

- repository package name should be `pi5camera` for consistency with the
  existing `pi5*` packages
- the library must remain standalone-first and usable without `ninjaclawbot`
- root workspace installation must include `pi5camera` through the same single
  `uv sync` flow as the other `pi5*` packages
- standalone package-local installation should also work with the normal package
  flow:
  - `cd pi5camera && uv sync --extra dev`
- the primary interactive operator tool should be:
  - `uv run pi5camera camera-tool`
- the primary package CLI should follow the existing package pattern:
  - `setup`
  - `doctor`
  - `status`
  - `capture`
  - `recognize`
  - `enroll`
  - `manage-faces`
  - `camera-tool`
- the first release should focus on still-photo workflows, not continuous video
  streaming
- local interactive recognition is allowed to prompt the user for names when an
  unknown face is found
- non-interactive automation must never block on a local TTY prompt
- `ninjaclawbot` and OpenClaw integrations must return structured unknown-face
  results instead of waiting for local keyboard input
- the default face-recognition path must be local and open-source
- the first release should not depend on a paid or cloud face-recognition API
- OpenClaw must not fail if `pi5camera` is missing, unconfigured, or the camera
  is disconnected
- camera images and enrolled-face data should stay in explicit local files under
  the project or standalone package directory
- the package should be mock-friendly and import-safe on macOS development
  machines with no Raspberry Pi camera attached

## 4. Current Build Status

### 4.1 What is already done

The planning and audit work is already done.

Current completed work:

- repository audit for current package structure and integration patterns
- review of:
  - `README.md`
  - `DevelopmentGuide.md`
  - `InstallationGuide.md`
  - `backup/DevelopmentPlan.md`
  - `backup/MicDevelopment.md`
- audit of current `ninjaclawbot` action, runtime, and adapter boundaries
- audit of the OpenClaw plugin tool-registration pattern
- external research on:
  - `Picamera2`
  - `face_recognition`
  - `DeepFace`
  - `InsightFace`
  - `onnxruntime`
- first-pass implementation plan for the new camera library

### 4.2 What is working today

There is no current `pi5camera` package in the repository.

What is working today is the surrounding project structure that the camera
library will plug into:

- standalone-first `pi5*` package layout
- guided hardware tools such as `servo-tool`, `display-tool`, and `mic-tool`
- `ninjaclawbot` adapter/runtime/action pattern
- OpenClaw plugin registration through typed `ninjaclawbot_*` tools

### 4.3 What is not built yet

The following camera features are still planned work, not finished work:

- the `pi5camera` package scaffold
- camera config and data storage
- still-image capture commands
- camera health-check and doctor flows
- local face enrollment and recognition
- interactive unknown-face naming flow
- `ninjaclawbot` camera actions
- OpenClaw plugin camera tools
- Raspberry Pi 5 field validation for the full camera workflow

## 5. Audit Summary

### 5.1 Repository and package audit findings

Important current strengths:

- the repository already has a clean standalone-first package model
- each `pi5*` package owns:
  - its own CLI
  - its own config manager
  - its own tests
  - its own hardware boundary
- the current project already has a strong template for a guided hardware tool:
  - `pi5mic mic-tool`
- the root workspace already supports sibling editable packages through local
  `uv` sources

Important current constraints:

- there is no existing camera package or config convention yet
- the root workspace currently includes:
  - `pi5buzzer`
  - `pi5servo`
  - `pi5disp`
  - `pi5mic`
  - `pi5vl53l0x`
- the root test and Python path configuration will need to be expanded for
  `pi5camera`

### 5.2 `ninjaclawbot` audit findings

Important current strengths:

- `ninjaclawbot` already composes standalone hardware packages through adapters
- the runtime already uses lazy-import style helpers for optional hardware
  ownership
- the action surface is explicit and typed
- health reporting is centralized

Important current constraints:

- the current action surface does not include camera actions yet
- runtime health-check currently reports:
  - `servo`
  - `buzzer`
  - `display`
  - `distance`
  - optional `voice_input`
- `ninjaclawbot` is the right place for reusable typed camera actions, but not
  for the interactive naming prompt owned by the standalone camera workflow

### 5.3 OpenClaw plugin audit findings

Important current strengths:

- the plugin already exposes typed `ninjaclawbot_*` tools
- the plugin already follows the repository rule that OpenClaw should call
  `ninjaclawbot`, not raw driver CLIs
- optional tools and typed schemas are already established patterns

Important current constraints:

- the plugin should not own direct camera hardware setup
- the plugin should not own local face enrollment prompting
- if camera behavior is exposed to OpenClaw, it should happen only after the
  same behavior exists in `ninjaclawbot`

### 5.4 External fact-check findings

Checked against upstream documentation on 2026-03-24:

- `Picamera2` is the official Raspberry Pi Python camera stack built on
  `libcamera`
- Raspberry Pi recommends installing `Picamera2` with `apt` instead of `pip`
  so the Python package and underlying camera stack stay version-compatible
- Raspberry Pi OS Bookworm renamed the camera CLI apps from `libcamera-*` to
  `rpicam-*`, though compatibility links still exist
- `Picamera2` supports:
  - still capture
  - metadata capture
  - camera controls
  - mode switching
  - request-level access
- `Picamera2` request objects must be released properly
- the Raspberry Pi camera stack expects single-process camera ownership, so the
  library should avoid multi-process camera control
- `face_recognition` provides the simplest local API for:
  - loading images
  - locating faces
  - generating encodings
  - comparing known and unknown faces
  - tuning tolerance
- `face_recognition` documents Raspberry Pi installation guidance and uses a
  default comparison tolerance of `0.6`
- `DeepFace` is feature-rich and offers `verify`, `find`, and `represent`, but
  it is a much heavier stack than needed for the first Pi 5 implementation
- `onnxruntime` supports Linux ARM64, which keeps the door open for a future
  alternative backend
- `InsightFace` code is MIT, but the published model licensing is more
  restrictive, so it should not be the default backend for this repository

## 6. Key Design Decisions

### 6.1 Where the camera runtime should live

The direct camera runtime should live in `pi5camera`, not in `ninjaclawbot`
and not inside the OpenClaw plugin.

Why:

- `pi5camera` should own:
  - camera access
  - still capture
  - face enrollment
  - face recognition
  - local camera diagnostics
- `ninjaclawbot` should stay focused on robot-level composition
- the OpenClaw plugin should stay as a typed tool wrapper around
  `ninjaclawbot`

### 6.2 Where `camera-tool` should live

Recommended decision:

- primary implementation:
  - `uv run pi5camera camera-tool`
- optional future convenience wrapper:
  - `uv run ninjaclawbot camera-tool`

Why:

- this is consistent with the actual repository pattern for standalone hardware
  packages
- `movement-tool` and `expression-tool` are integrated robot tools, while
  `camera-tool` is fundamentally a hardware and data-enrollment tool
- OpenClaw should not invoke `camera-tool` directly; it should call typed
  `ninjaclawbot` actions or plugin tools

### 6.3 Camera backend choice

Recommended first-release backend:

- `Picamera2`

Why:

- it is the official Raspberry Pi Python camera interface
- it is directly aligned with Raspberry Pi 5 and current Bookworm-era camera
  software
- it supports still capture and camera controls without inventing a custom
  wrapper around `rpicam-*`

Operational rule:

- imports of `Picamera2` should stay lazy so the package remains importable
  during macOS development and unit testing

### 6.4 Face-recognition backend choice

Recommended first-release backend:

- `face_recognition`

Recommended future backend model:

- keep recognition behind a pluggable backend interface
- allow an optional heavier backend later if Raspberry Pi validation shows a
  strong need

Why `face_recognition` is the first choice:

- simplest local API
- no cloud dependency
- strong fit for the requested open-source offline workflow
- enough control to build:
  - enrollment
  - known-face matching
  - multi-face handling
  - configurable tolerance

Why `DeepFace` is not the first default:

- heavier dependency and runtime footprint
- broader feature set than the current use case needs

Why `InsightFace` is not the first default:

- model licensing needs more care than this repository should assume by default

### 6.5 Interactive naming policy for unknown faces

This is one of the most important refinements added after reviewing the use
cases.

Recommended policy:

- local interactive `camera-tool` recognition may prompt for names when it
  finds unknown faces
- non-interactive commands should support an explicit `--prompt-for-names`
  style mode only when a real terminal is present
- `ninjaclawbot` actions must never block waiting for local keyboard input
- OpenClaw plugin tools must never block waiting for local keyboard input

Expected non-interactive behavior:

- return:
  - recognized names
  - unknown-face count
  - crop paths or capture paths
  - face locations
  - match distances when useful
- allow a separate explicit enrollment action later if needed

### 6.6 Multi-face policy

The first release should support multiple faces in a single image.

Recommended behavior:

- detect all faces in the image
- order results deterministically
- first implementation should use a stable top-to-bottom then left-to-right
  ordering
- compare every detected face against all stored encodings
- choose the closest accepted match within the configured tolerance
- mark all others as unknown

Interactive naming flow:

- if one unknown face is found:
  - prompt once for a name
- if multiple unknown faces are found:
  - prompt one face at a time with:
    - face index
    - bounding box
    - crop file path if available

### 6.7 Face-store policy

The first implementation should store face data locally in explicit files.

Recommended layout:

- `camera.json`
- `camera_data/captures/`
- `camera_data/known_faces/<person_name>/`
- `camera_data/index/encodings.json`
- optional `camera_data/faces/unknown/` for debug crops if enabled

Recommended matching policy:

- support more than one image per person over time
- generate and store one encoding per enrollment image
- compare against all stored encodings
- return the best accepted match

This is more reliable than forcing a one-image-per-person rule forever.

### 6.8 Privacy and retention policy

The package should stay local-first and explicit.

Recommended rules:

- no automatic cloud upload
- no hidden background sync
- no automatic deletion of enrolled identities without an explicit user command
- capture retention should be configurable
- recognition debug crops should be optional
- users should be able to:
  - list saved identities
  - remove saved identities
  - clear old captures

### 6.9 Integration policy for `ninjaclawbot`

Recommended integrated action surface:

- `camera_health_check`
- `capture_photo`
- `recognize_faces`
- optional future:
  - `enroll_face`
  - `list_known_faces`

Important design rule:

- `ninjaclawbot` should expose typed camera actions
- it should not recreate the full interactive enrollment wizard

### 6.10 Integration policy for OpenClaw

Recommended first plugin tools:

- `ninjaclawbot_capture_photo`
- `ninjaclawbot_recognize_faces`

Optional later plugin tools:

- `ninjaclawbot_list_known_faces`
- `ninjaclawbot_enroll_face`

Important rule:

- plugin tools should only expose actions that already exist in
  `ninjaclawbot`
- unknown-face naming during chat should be a follow-up agent flow, not an
  implicit local prompt

## 7. Recommended Setup Flow

This is the recommended future setup order for the full project.

1. install the NinjaClawBot workspace with `uv sync`
2. physically connect the Raspberry Pi camera module
3. verify the camera is detected with:
   - `rpicam-hello --list-cameras`
   - or `libcamera-hello --list-cameras` on older environments
4. run `uv run pi5camera camera-tool`
5. use `setup` to save camera defaults into `camera.json`
6. capture one test image
7. run one local face-recognition cycle
8. enroll at least one known face
9. if integrated robot use is needed, run `ninjaclawbot` health-check and
   camera-related actions next
10. only after local validation, expose the camera surface through OpenClaw

Important setup message to add later in docs:

- `pi5camera` should be usable by itself
- package-local standalone setup should still work with:
  - `cd /path/to/pi5camera`
  - `uv sync --extra dev`
- but users who plan to let OpenClaw use the camera should still validate local
  camera capture and recognition first

## 8. Camera Specification

### 8.1 Control model

The first release should use a manual tool and typed command model:

- manual start of the CLI tool
- still capture on demand
- recognition on demand
- no always-on background camera watcher
- no hidden auto-capture service

### 8.2 Capture behavior

The first release should support:

- JPEG still capture
- configurable save directory
- timestamp-based default filenames
- access to camera metadata
- configurable preview or no-preview behavior when supported
- basic camera controls through config:
  - resolution
  - timeout/warm-up delay
  - autofocus mode where supported
  - exposure-related controls only if they can be kept simple and stable

### 8.3 Recognition behavior

The face-recognition workflow should behave like this:

- capture or load an image
- locate faces
- generate embeddings
- compare against the stored face index
- return recognized names when matched
- mark other faces as unknown

First-release recognition defaults:

- backend:
  - `face_recognition`
- tolerance:
  - start with `0.6`
- allow later user tuning in config once Pi field results exist

### 8.4 Interactive local unknown-face behavior

The interactive `camera-tool` recognition flow should behave like this:

- automatically capture or load a photo
- attempt recognition
- if all faces are known:
  - print the names and save the result
- if unknown faces exist:
  - prompt for names one face at a time
  - save those new identities locally
  - rebuild the local index cleanly

### 8.5 Non-interactive and agent behavior

The non-interactive and agent flow should behave like this:

- never prompt locally
- never wait for terminal input
- return structured output only

Expected structured output fields:

- capture path
- face count
- `needs_enrollment`
- per-face result entries including:
  - face index
  - bounding box
  - recognized name or `null`
  - accepted match distance if available
  - crop path if exported

### 8.6 Skip behavior

If camera support is missing, the rest of the project should not crash.

Expected skip cases:

- `pi5camera` not installed
- `camera.json` missing
- `Picamera2` missing from the current environment
- no Raspberry Pi camera detected
- face-recognition backend missing
- corrupted local encoding index

In those cases:

- `pi5camera` should surface a clear setup or doctor error
- `ninjaclawbot` should report camera unavailability clearly
- OpenClaw should skip or report the tool failure without breaking the rest of
  the robot stack

## 9. What Has Been Done Already

The following planning work is complete:

- repository audit
- integration-boundary audit
- upstream camera and face-recognition research
- first implementation plan
- refinement against the approved standalone and integration use cases

The most important refined conclusions are:

- `camera-tool` should belong to `pi5camera`, not to the plugin
- `ninjaclawbot` should expose a thin reusable camera action layer
- OpenClaw should call typed `ninjaclawbot_*` tools, not raw camera code
- human naming prompts and agent-safe flows must be separated explicitly

## 10. What Still Needs Improvement

The following work is still open:

- actual package implementation
- field-tested Pi 5 camera configuration defaults
- recognition tuning with multiple lighting conditions
- a clear management UX for editing and deleting known faces
- optional future wrapper alias inside `ninjaclawbot`
- optional future higher-accuracy alternative recognition backend
- optional future support for richer vision tasks beyond face recognition
- optional future anti-spoofing or liveness checks if the project later needs
  them

## 11. Phased Implementation Plan

### 11.1 Camera planning lock

Status: complete

Summary:

- the product goal is now locked around the approved use cases
- the camera library is confirmed as standalone-first
- the integration boundary is confirmed as:
  - `pi5camera` owns camera and recognition
  - `ninjaclawbot` owns typed orchestration
  - the OpenClaw plugin owns typed external tool exposure

### Phase C0: Package contract and workspace lock

Status: planned

Objective:

- create the `pi5camera` package contract and workspace registration before
  hardware logic is added

Likely files:

- `pyproject.toml`
- new `pi5camera/pyproject.toml`
- new `pi5camera/README.md`
- new `pi5camera/src/pi5camera/__init__.py`
- new `pi5camera/src/pi5camera/__main__.py`
- new `pi5camera/src/pi5camera/driver.py`
- new `pi5camera/tests/*`
- `backup/CameraDevelopment.md`

Implementation targets:

- add `pi5camera` to root workspace dependencies and local `uv` sources
- add `pi5camera/src` and `pi5camera/tests` to the root test configuration
- define the package CLI shape
- define compatibility re-export patterns through `driver.py`

Validation:

- planning review
- `uv lock`
- package import smoke tests once the scaffold exists

Risk level:

- low

### Phase C1: Config, storage, and doctor/status scaffold

Status: planned

Objective:

- create the config and filesystem model before live capture or recognition
  logic is added

Likely files:

- `pi5camera/src/pi5camera/errors.py`
- `pi5camera/src/pi5camera/models.py`
- `pi5camera/src/pi5camera/config/config_manager.py`
- `pi5camera/src/pi5camera/cli/setup_cmd.py`
- `pi5camera/src/pi5camera/cli/status.py`
- `pi5camera/src/pi5camera/cli/doctor.py`
- `pi5camera/tests/test_config.py`
- `pi5camera/tests/test_status.py`
- `pi5camera/tests/test_doctor.py`

Expected config direction:

- `camera.json` should capture:
  - capture directory
  - known-faces directory
  - backend selection
  - recognition tolerance
  - camera resolution
  - preview mode
  - autofocus preference where supported
  - capture warm-up delay
  - retention/debug settings

Validation:

- `cd pi5camera && uv run --extra dev python -m compileall src tests`
- `cd pi5camera && uv run --extra dev ruff check src tests`
- `cd pi5camera && uv run --extra dev ruff format --check src tests`
- `cd pi5camera && uv run --extra dev pytest -q tests -c pyproject.toml`

Risk level:

- low

### Phase C2: `Picamera2` capture backend

Status: planned

Objective:

- add a stable still-capture backend using `Picamera2`

Likely files:

- `pi5camera/src/pi5camera/core/camera_backend.py`
- `pi5camera/src/pi5camera/core/capture.py`
- `pi5camera/src/pi5camera/cli/capture_cmd.py`
- `pi5camera/tests/test_capture.py`

Implementation targets:

- lazy import `Picamera2`
- still-image capture to file
- metadata collection
- warm-up delay before capture
- safe close/release behavior
- single-process ownership assumptions documented

Validation:

- package-local Python gate
- Raspberry Pi smoke tests:
  - `rpicam-hello --list-cameras`
  - `uv run pi5camera doctor`
  - `uv run pi5camera capture`

Risk level:

- medium

### Phase C3: Face store and recognition backend

Status: planned

Objective:

- add local enrollment and recognition through `face_recognition`

Likely files:

- `pi5camera/src/pi5camera/recognition/base.py`
- `pi5camera/src/pi5camera/recognition/face_recognition_backend.py`
- `pi5camera/src/pi5camera/storage/face_store.py`
- `pi5camera/src/pi5camera/core/enrollment.py`
- `pi5camera/src/pi5camera/core/recognition.py`
- `pi5camera/tests/test_face_store.py`
- `pi5camera/tests/test_recognition.py`

Implementation targets:

- face detection
- encoding generation
- deterministic per-face result ordering
- local encoding persistence
- one or more images per known identity
- configurable tolerance
- clean rebuild of the encoding index

Validation:

- package-local Python gate
- unit tests for:
  - no faces found
  - one known face
  - one unknown face
  - multiple faces
  - index rebuild
  - corrupted index recovery

Risk level:

- medium

### Phase C4: Interactive `camera-tool` and operator UX

Status: planned

Objective:

- create the guided operator tool that matches the approved local use case

Likely files:

- `pi5camera/src/pi5camera/cli/camera_tool.py`
- `pi5camera/src/pi5camera/cli/enroll_cmd.py`
- `pi5camera/src/pi5camera/cli/recognize_cmd.py`
- `pi5camera/src/pi5camera/cli/manage_faces_cmd.py`
- `pi5camera/tests/test_camera_tool.py`

Implementation targets:

- setup wizard
- one-shot photo capture
- interactive recognition
- unknown-face naming prompts
- listing known faces
- deleting known faces
- optional capture cleanup commands

Validation:

- package-local Python gate
- manual Raspberry Pi flow:
  - run `camera-tool`
  - capture photo
  - enroll one face
  - recognize that face again
  - confirm the tool returns the saved name

Risk level:

- medium

### Phase C5: `ninjaclawbot` camera integration

Status: planned

Objective:

- add a thin camera adapter and typed action surface in `ninjaclawbot`

Likely files:

- `ninjaclawbot/pyproject.toml`
- `ninjaclawbot/src/ninjaclawbot/config.py`
- `ninjaclawbot/src/ninjaclawbot/adapters.py`
- `ninjaclawbot/src/ninjaclawbot/runtime.py`
- `ninjaclawbot/src/ninjaclawbot/actions.py`
- `ninjaclawbot/src/ninjaclawbot/executor.py`
- `ninjaclawbot/tests/test_adapters.py`
- `ninjaclawbot/tests/test_runtime.py`
- `ninjaclawbot/tests/test_actions.py`
- `ninjaclawbot/tests/test_executor.py`

Implementation targets:

- camera config discovery from the root workspace
- optional camera health reporting
- typed capture action
- typed recognition action
- structured unknown-face results
- no local TTY prompt inside `ninjaclawbot`

Validation:

- `cd ninjaclawbot && uv run --extra dev python -m compileall src tests`
- `cd ninjaclawbot && uv run --extra dev ruff check src tests`
- `cd ninjaclawbot && uv run --extra dev ruff format --check src tests`
- `cd ninjaclawbot && uv run --extra dev pytest -q tests -c pyproject.toml`

Risk level:

- medium

### Phase C6: OpenClaw plugin camera tools

Status: planned

Objective:

- expose approved camera actions through optional OpenClaw plugin tools

Likely files:

- `integrations/openclaw/ninjaclawbot-plugin/src/schemas.ts`
- `integrations/openclaw/ninjaclawbot-plugin/src/index.ts`
- `integrations/openclaw/ninjaclawbot-plugin/tests/*`

Implementation targets:

- add typed schemas for camera tools
- expose:
  - `ninjaclawbot_capture_photo`
  - `ninjaclawbot_recognize_faces`
- keep tool responses structured and agent-friendly
- never block on local naming prompts

Validation:

- `cd integrations/openclaw/ninjaclawbot-plugin && npm install`
- `cd integrations/openclaw/ninjaclawbot-plugin && npm run typecheck`
- `cd integrations/openclaw/ninjaclawbot-plugin && npm test`

Risk level:

- low to medium

### Phase C7: Documentation and repository updates

Status: planned

Objective:

- document the final camera package, setup flow, integration surface, and Pi
  validation process

Likely files:

- `README.md`
- `DevelopmentGuide.md`
- `InstallationGuide.md`
- `pi5camera/README.md`
- `ninjaclawbot/README.md`
- `backup/DevelopmentLog.md`
- `backup/CameraDevelopment.md`

Documentation targets:

- add `pi5camera` to the project overview and quick-start flow
- add Raspberry Pi camera validation guidance
- add package usage examples
- add `ninjaclawbot` camera action and plugin tool documentation

Validation:

- `git diff --check`
- run the same lint/test gates for any code touched in the documentation phase

Risk level:

- low

### Phase C8: Raspberry Pi field validation and tuning

Status: planned

Objective:

- validate the final local and integrated camera workflows on Raspberry Pi 5

Validation targets:

- standalone smoke tests:
  - camera detection
  - setup
  - status
  - doctor
  - still capture
- recognition tests:
  - known face
  - unknown face
  - multiple faces
  - repeated re-recognition after enrollment
- integrated tests:
  - `ninjaclawbot` camera action calls
  - OpenClaw camera tool calls
  - sequence with another robot action
- long-run tests:
  - repeated captures
  - repeated recognition cycles
  - storage growth and cleanup behavior
  - thermal and memory monitoring during repeated use

Risk level:

- medium

## 12. Quality Gates

Every implementation phase should pass the matching package gate.

### `pi5camera` package gate

- `cd pi5camera && uv run --extra dev python -m compileall src tests`
- `cd pi5camera && uv run --extra dev ruff check src tests`
- `cd pi5camera && uv run --extra dev ruff format --check src tests`
- `cd pi5camera && uv run --extra dev pytest -q tests -c pyproject.toml`

### Root workspace gate

- `uv run --extra dev python -m compileall .`
- `uv run --extra dev ruff check .`
- `uv run --extra dev ruff format --check .`
- run the package-specific pytest commands from `DevelopmentGuide.md`

### OpenClaw plugin gate

- `npm run typecheck`
- `npm test`

## 13. Raspberry Pi Validation Categories

Always separate validation into:

- safe smoke tests
- communication/interface tests
- actuator-moving tests
- power-risk and long-run tests

Recommended category mapping for camera work:

### Safe smoke tests

- `rpicam-hello --list-cameras`
- `uv run pi5camera doctor`
- `uv run pi5camera status`
- one still capture with no recognition

### Communication/interface tests

- repeated still captures
- metadata capture
- known-face recognition
- unknown-face detection
- enrollment and re-recognition

### Actuator-moving tests

- camera-only package phases should not move hardware
- integrated tests may later combine:
  - one safe servo action
  - one camera capture or recognition action
- do not combine motion and recognition until both are stable separately

### Power-risk and long-run tests

- repeated capture cycles
- repeated recognition cycles
- monitor temperature and throttling
- monitor disk growth in capture and face-store folders
- verify cleanup and recovery after camera disconnect or failure

## 14. Final Recommendation Before Coding

The recommended implementation direction is:

- build `pi5camera` as a standalone-first package
- keep `camera-tool` in `pi5camera`
- use `Picamera2` as the first camera backend
- use `face_recognition` as the first local recognition backend
- keep the recognition backend pluggable for future alternatives
- separate human-interactive unknown-face naming from agent-safe automation
- expose only thin typed camera actions through `ninjaclawbot`
- expose only approved typed camera tools through the OpenClaw plugin
- validate all standalone camera behavior locally before enabling integrated
  OpenClaw use

This is the most practical and repository-consistent path for the current
NinjaClawBot workspace.

## 15. References

Repository inputs reviewed:

- `README.md`
- `DevelopmentGuide.md`
- `InstallationGuide.md`
- `backup/DevelopmentPlan.md`
- `backup/MicDevelopment.md`
- `pyproject.toml`
- `pi5mic/pyproject.toml`
- `pi5mic/README.md`
- `pi5mic/src/pi5mic/__main__.py`
- `pi5mic/src/pi5mic/cli/mic_tool.py`
- `pi5mic/src/pi5mic/cli/setup_cmd.py`
- `pi5mic/src/pi5mic/cli/run_cmd.py`
- `pi5mic/src/pi5mic/config/config_manager.py`
- `ninjaclawbot/README.md`
- `ninjaclawbot/src/ninjaclawbot/actions.py`
- `ninjaclawbot/src/ninjaclawbot/adapters.py`
- `ninjaclawbot/src/ninjaclawbot/runtime.py`
- `ninjaclawbot/src/ninjaclawbot/executor.py`
- `integrations/openclaw/ninjaclawbot-plugin/src/index.ts`
- `integrations/openclaw/ninjaclawbot-plugin/src/schemas.ts`

External primary sources checked on 2026-03-24:

- Raspberry Pi Camera Software docs:
  - https://www.raspberrypi.com/documentation/computers/camera_software.html
- Picamera2 manual:
  - https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf
- Picamera2 GitHub repository:
  - https://github.com/raspberrypi/picamera2
- `face_recognition` README:
  - https://raw.githubusercontent.com/ageitgey/face_recognition/master/README.md
- `DeepFace` GitHub repository:
  - https://github.com/serengil/deepface
- `InsightFace` GitHub repository and licensing note:
  - https://raw.githubusercontent.com/deepinsight/insightface/master/README.md
- ONNX Runtime Python platform support:
  - https://onnxruntime.ai/docs/get-started/with-python.html
