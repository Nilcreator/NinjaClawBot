# Development Log

## 2026-03-12

### ninjaclawbot Expression Runtime Fix

Summary:

- fixed the `ninjaclawbot` cleanup order so shared display and buzzer GPIO resources shut down safely
- made one-shot `ninjaclawbot` CLI commands close their runtime deterministically instead of relying on process exit
- made integrated expression and sound actions wait for queued buzzer playback to finish before shutdown
- added regression coverage for runtime cleanup order, one-shot CLI runtime ownership, and buzzer wait behavior

Files changed:

- [ninjaclawbot/src/ninjaclawbot/runtime.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/runtime.py)
- [ninjaclawbot/src/ninjaclawbot/adapters.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/adapters.py)
- [ninjaclawbot/src/ninjaclawbot/executor.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/executor.py)
- [ninjaclawbot/src/ninjaclawbot/__main__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/__main__.py)
- [ninjaclawbot/tests/test_runtime.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_runtime.py)
- [ninjaclawbot/tests/test_executor.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_executor.py)
- [ninjaclawbot/tests/test_cli_tools.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_cli_tools.py)
- [ninjaclawbot/tests/test_adapters.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_adapters.py)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentLog.md)

Why:

- `expression-tool` was closing the buzzer backend before the display backend even though both ultimately depended on the same `RPi.GPIO` / `rpi-lgpio` global state
- one-shot commands like `perform-expression` and `health-check` created executors without explicitly closing them
- queued buzzer emotion playback returned immediately, so the process could end before the sound finished

Lint and test results:

- `uv run python -m compileall conftest.py ninjaclawbot/src ninjaclawbot/tests`
- `uv run ruff check ninjaclawbot/src ninjaclawbot/tests`
- `uv run ruff format --check ninjaclawbot/src ninjaclawbot/tests`
- `uv run pytest -q ninjaclawbot/tests -c ninjaclawbot/pyproject.toml` -> `25 passed`
- `uv run ninjaclawbot --help`

Raspberry Pi validation status:

- Raspberry Pi validation is still required for the integrated expression path
- expected pass conditions:
  - `uv run ninjaclawbot expression-tool` exits cleanly after `Goodbye!`
  - `uv run ninjaclawbot perform-expression <name>` keeps the display output stable and plays the full buzzer emotion before returning JSON
  - no `RPi.GPIO` or `lgpio` cleanup traceback appears on exit

### Root Workspace And ninjaclawbot Rebuild

Summary:

- added a real root `uv` install entry so the whole project now installs from the project root
- made `uv sync --extra dev` at the project root install `ninjaclawbot` and all four `pi5*` driver packages in one environment
- rebuilt the `ninjaclawbot` runtime around thin driver adapters instead of directly guessing raw driver behavior
- replaced the old movement asset format with a validated legacy-compatible schema using `speed`, `moves`, and optional `per_servo_speeds`
- updated the integrated `move-servos` command and `movement-tool` to use legacy-style movement syntax safely with canonical endpoint names
- kept the standalone `pi5*` packages unchanged as standalone packages while making them work from the root environment too
- rewrote the root documentation around the new root-first install, calibration, and testing workflow

Files changed:

- [pyproject.toml](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pyproject.toml)
- [.python-version](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/.python-version)
- [src/ninjaclawbot_workspace/__init__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/src/ninjaclawbot_workspace/__init__.py)
- [uv.lock](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/uv.lock)
- [ninjaclawbot/src/ninjaclawbot/actions.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/actions.py)
- [ninjaclawbot/src/ninjaclawbot/adapters.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/adapters.py)
- [ninjaclawbot/src/ninjaclawbot/assets.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/assets.py)
- [ninjaclawbot/src/ninjaclawbot/runtime.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/runtime.py)
- [ninjaclawbot/src/ninjaclawbot/executor.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/executor.py)
- [ninjaclawbot/src/ninjaclawbot/cli/common.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/cli/common.py)
- [ninjaclawbot/src/ninjaclawbot/cli/movement_tool.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/cli/movement_tool.py)
- [ninjaclawbot/src/ninjaclawbot/cli/expression_tool.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/cli/expression_tool.py)
- [ninjaclawbot/src/ninjaclawbot/__main__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/__main__.py)
- [ninjaclawbot/README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/README.md)
- [ninjaclawbot/tests/test_actions.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_actions.py)
- [ninjaclawbot/tests/test_assets.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_assets.py)
- [ninjaclawbot/tests/test_cli_tools.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_cli_tools.py)
- [ninjaclawbot/tests/test_executor.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_executor.py)
- [ninjaclawbot/tests/test_runtime.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_runtime.py)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentLog.md)

Why:

- the previous project state still required the user to think in terms of subpackage installs instead of a root project install
- the earlier `ninjaclawbot` prototype guessed at several `pi5*` driver behaviors and produced incorrect health-check and movement behavior
- the integration layer needed a clean adapter boundary so external callers such as OpenClaw can rely on typed results without touching raw drivers directly

Lint and test results:

- Phase 1 root packaging checks:
  - `uv lock`
  - `uv sync --extra dev`
  - `uv run python -c "import ninjaclawbot, pi5buzzer, pi5servo, pi5disp, pi5vl53l0x; print('imports-ok')"`
  - `uv run ninjaclawbot --help`
  - `uv run pi5servo --help`
  - `uv run pi5buzzer --help`
  - `uv run pi5disp --help`
  - `uv run pi5vl53l0x --help`
- `ninjaclawbot` rebuild gate:
  - `uv run python -m compileall ninjaclawbot/src ninjaclawbot/tests src`
  - `uv run ruff check ninjaclawbot/src ninjaclawbot/tests src pyproject.toml`
  - `uv run ruff format --check ninjaclawbot/src ninjaclawbot/tests src pyproject.toml`
  - `uv run pytest -q ninjaclawbot/tests` -> `18 passed`
- root package test runs:
  - `uv run pytest -q pi5buzzer/tests -c pi5buzzer/pyproject.toml` -> `65 passed`
  - `uv run pytest -q pi5servo/tests -c pi5servo/pyproject.toml` -> `125 passed`
  - `uv run pytest -q pi5disp/tests -c pi5disp/pyproject.toml` -> `63 passed`
  - `uv run pytest -q pi5vl53l0x/tests -c pi5vl53l0x/pyproject.toml` -> `62 passed`
  - `uv run pytest -q ninjaclawbot/tests -c ninjaclawbot/pyproject.toml` -> `18 passed`
- root smoke checks:
  - `uv run ninjaclawbot health-check`
  - `uv run ninjaclawbot list-assets`
  - `uv run ninjaclawbot run-action '{"action":"move_servos","parameters":{"targets":{"gpio12":0},"speed_mode":"F"}}'`

Raspberry Pi validation status:

- Raspberry Pi validation is still required for the rebuilt root workflow
- the rebuilt root commands now return structured hardware-availability errors instead of integration-layer tracebacks on non-Pi environments
- the next validation pass should be run from the project root on the Raspberry Pi 5

## 2026-03-11

### ninjaclawbot Single-Command Install Packaging

Summary:

- updated `ninjaclawbot` packaging so the sibling `pi5buzzer`, `pi5servo`,
  `pi5disp`, and `pi5vl53l0x` packages are installed automatically inside the
  `ninjaclawbot` environment
- used `uv` local editable path sources so the full integrated robot stack can
  be installed with one command: `uv sync --extra dev`
- kept the standalone `pi5*` package folders unchanged so they still work the
  same independently
- added an import smoke test to confirm the integrated environment can import
  all four local driver packages

Files changed:

- [ninjaclawbot/pyproject.toml](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/pyproject.toml)
- [ninjaclawbot/README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/README.md)
- [ninjaclawbot/tests/test_dependency_imports.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_dependency_imports.py)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentLog.md)

Why:

- the previous install flow required users to sync `ninjaclawbot` first and then
  manually install each sibling driver into the same environment
- that was error-prone and made the integrated robot setup harder than the
  standalone driver setup
- the new path-source packaging keeps one shared integrated environment without
  changing the standalone behavior of the driver packages themselves

Lint and test results:

- `uv lock`
- `uv sync --extra dev --refresh`
- `uv run python -m compileall src tests`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pytest -q` -> `15 passed`
- `uv run python -c "import pi5buzzer, pi5servo, pi5disp, pi5vl53l0x"` -> `imports-ok`
- `uv run pi5buzzer --help`
- `uv run pi5servo --help`
- `uv run pi5disp --help`
- `uv run pi5vl53l0x --help`
- `uv run ninjaclawbot --help`

Raspberry Pi validation status:

- no hardware behavior changed in this packaging refinement
- existing Raspberry Pi validation steps for the drivers and `ninjaclawbot`
  remain the same

### ninjaclawbot Foundation And Interactive Tooling

Summary:

- created the new `ninjaclawbot` package as the integrated robot-control layer above the standalone Pi 5 drivers
- added typed action requests, typed action results, and explicit integration-layer error classes
- added a lazy runtime that composes `pi5servo`, `pi5disp`, `pi5buzzer`, and `pi5vl53l0x` without exposing them directly
- added persistent movement and expression assets under `ninjaclawbot_data`
- added the first interactive `movement-tool` and `expression-tool`
- added a CLI entrypoint for `health-check`, `list-assets`, `move-servos`, `perform-movement`, `perform-expression`, and JSON `run-action`
- rewrote the root README to describe the full project structure, installation flow, and integrated test steps

Files changed:

- [ninjaclawbot/pyproject.toml](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/pyproject.toml)
- [ninjaclawbot/README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/README.md)
- [ninjaclawbot/src/ninjaclawbot/__init__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/__init__.py)
- [ninjaclawbot/src/ninjaclawbot/actions.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/actions.py)
- [ninjaclawbot/src/ninjaclawbot/results.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/results.py)
- [ninjaclawbot/src/ninjaclawbot/errors.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/errors.py)
- [ninjaclawbot/src/ninjaclawbot/config.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/config.py)
- [ninjaclawbot/src/ninjaclawbot/locks.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/locks.py)
- [ninjaclawbot/src/ninjaclawbot/assets.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/assets.py)
- [ninjaclawbot/src/ninjaclawbot/runtime.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/runtime.py)
- [ninjaclawbot/src/ninjaclawbot/executor.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/executor.py)
- [ninjaclawbot/src/ninjaclawbot/__main__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/__main__.py)
- [ninjaclawbot/src/ninjaclawbot/cli/common.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/cli/common.py)
- [ninjaclawbot/src/ninjaclawbot/cli/movement_tool.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/cli/movement_tool.py)
- [ninjaclawbot/src/ninjaclawbot/cli/expression_tool.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/cli/expression_tool.py)
- [ninjaclawbot/tests/test_actions.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_actions.py)
- [ninjaclawbot/tests/test_results.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_results.py)
- [ninjaclawbot/tests/test_assets.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_assets.py)
- [ninjaclawbot/tests/test_runtime.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_runtime.py)
- [ninjaclawbot/tests/test_executor.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_executor.py)
- [ninjaclawbot/tests/test_cli_tools.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_cli_tools.py)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentLog.md)

Why:

- the completed Pi 5 driver migrations needed a stable high-level layer before OpenClaw or another external AI assistant can control the robot safely
- the project also needed human-usable authoring tools for saved movements and saved expressions so the same assets can be reused by both operators and AI actions
- the old `ninja_core` execution model exposed broader code and hardware access than the new project should allow

Lint and test results:

- Phase 1: `uv run python -m compileall src tests`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest -q` -> `7 passed`
- Phase 2: same gate after runtime, assets, and executor -> `11 passed`
- Phase 3: same gate after CLI and interactive tools -> `14 passed`

Raspberry Pi validation status:

- local unit and CLI tests passed without requiring Raspberry Pi hardware
- Raspberry Pi 5 validation is still required for live driver composition, movement execution, expression playback, and sensor reads through `ninjaclawbot`
- start with `uv run ninjaclawbot health-check`, then create a small movement asset and a small expression asset before testing direct servo movement

### pi5servo DFR0566 Calibration Fix

Summary:

- audited the failing `pi5servo calib hat_pwm1` and `servo-tool` calibration paths against the live traceback and the DFRobot DFR0566 vendor driver
- fixed `servo-tool` so ad hoc `hat_pwmN` calibration no longer reuses a persistent native GPIO backend
- removed the unsafe empty-config fallback that previously made `servo-tool` assume `GPIO12` and `GPIO13`
- hardened the DFR0566 backend sequencing with the same short settle delays used by the vendor driver around PWM enable and frequency writes
- added regression coverage for HAT calibration routing, empty-config startup, and submenu error recovery
- updated the docs to clarify that current `pi5servo` endpoint names map `hat_pwm1` -> physical HAT `PWM0`, `hat_pwm2` -> `PWM1`, `hat_pwm3` -> `PWM2`, and `hat_pwm4` -> `PWM3`

Files changed:

- [pi5servo/README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/README.md)
- [pi5servo/src/pi5servo/cli/servo_tool.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/servo_tool.py)
- [pi5servo/src/pi5servo/core/backends/dfr0566.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/backends/dfr0566.py)
- [pi5servo/tests/test_servo_tool.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/tests/test_servo_tool.py)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentLog.md)

Why:

- the reported traceback showed `servo-tool` was trying to calibrate `hat_pwm1` through the RP1 hardware PWM backend instead of the DFR0566 backend
- the previous empty-config startup behavior made that failure easier to trigger on a fresh Raspberry Pi setup
- the DFR0566 I2C backend matched the vendor register map, but it did not yet match the vendor timing behavior around PWM enable/frequency updates

Lint and test results:

- `uv run python -m compileall src tests`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pytest -q` -> `121 passed`

Raspberry Pi validation status:

- manual Raspberry Pi 5 validation is still required for the DFR0566 path after this fix
- verify `sudo i2cdetect -y 1` shows `0x10`
- connect only one servo per HAT PWM connector
- for a servo on physical HAT `PWM0`, test `uv run pi5servo move hat_pwm1 center --backend dfr0566 --address 0x10 --bus-id 1`
- then test `uv run pi5servo calib hat_pwm1 --backend dfr0566 --address 0x10 --bus-id 1`
- then test `uv run pi5servo servo-tool` and calibrate `hat_pwm1` from the menu

### pi5servo DFR0566 Refinement Implementation

Summary:

- implemented the full `pi5servo` DFR0566 refinement that was previously only planned
- added explicit endpoint parsing and storage for native GPIO shorthand, explicit `gpioNN` endpoints, and `hat_pwmN` DFR0566 PWM endpoints
- added the dedicated `dfr0566` backend over `smbus2`, with board identity validation and PWM control over I2C
- refactored `Servo` and `ServoGroup` so native GPIO servos and DFR0566 PWM servos can coexist in one mixed motion group
- updated the standalone CLI so `move`, `cmd`, `calib`, `status`, `config`, and `servo-tool` all understand explicit endpoints
- fixed a mixed-endpoint CLI risk in `servo-tool` by replacing unsafe direct sorting of mixed `int` and `str` endpoint keys

Files changed:

- [pi5servo/pyproject.toml](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/pyproject.toml)
- [pi5servo/README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/README.md)
- [pi5servo/src/pi5servo/core/endpoint.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/endpoint.py)
- [pi5servo/src/pi5servo/core/backend.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/backend.py)
- [pi5servo/src/pi5servo/core/backends/hardware_pwm.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/backends/hardware_pwm.py)
- [pi5servo/src/pi5servo/core/backends/dfr0566.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/backends/dfr0566.py)
- [pi5servo/src/pi5servo/core/backends/pca9685.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/backends/pca9685.py)
- [pi5servo/src/pi5servo/core/servo.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/servo.py)
- [pi5servo/src/pi5servo/core/multi_servos.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/multi_servos.py)
- [pi5servo/src/pi5servo/parser/command.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/parser/command.py)
- [pi5servo/src/pi5servo/config/config_manager.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/config/config_manager.py)
- [pi5servo/src/pi5servo/cli/_common.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/_common.py)
- [pi5servo/src/pi5servo/cli/move.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/move.py)
- [pi5servo/src/pi5servo/cli/cmd.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/cmd.py)
- [pi5servo/src/pi5servo/cli/status.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/status.py)
- [pi5servo/src/pi5servo/cli/calib.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/calib.py)
- [pi5servo/src/pi5servo/cli/config_cmd.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/config_cmd.py)
- [pi5servo/src/pi5servo/cli/servo_tool.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/servo_tool.py)
- [pi5servo/tests/test_backend.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/tests/test_backend.py)
- [pi5servo/tests/test_core.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/tests/test_core.py)
- [pi5servo/tests/test_config.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/tests/test_config.py)
- [pi5servo/tests/test_cli.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/tests/test_cli.py)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentLog.md)

Why:

- DFR0566 digital ports and DFR0566 PWM ports are electrically and software-wise different paths, so one integer-only identifier model was not safe enough
- the new robot stack needs standalone Pi 5 support for both direct GPIO servo wiring and HAT-based PWM expansion without reintroducing `pigpio`
- mixed routing had to be solved in the core layer first, not only in the CLI, to keep command execution, calibration, and future robot motion code consistent

Lint and test results:

- Phase 1 gate: `uv run python -m compileall src tests`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest -q` -> `106 passed`
- Phase 2 gate: same commands after `dfr0566` backend integration -> `111 passed`
- Phase 3 gate: same commands after mixed-backend routing refactor -> `115 passed`
- Phase 4 and final package state: same commands after endpoint-aware CLI updates -> `118 passed`

Raspberry Pi validation status:

- manual Raspberry Pi 5 validation is still required
- required native GPIO checks: verify PWM overlay configuration, run `uv run pi5servo move 12 center`, `min`, `max`, and confirm stable signal on the scope
- required DFR0566 checks: verify `sudo i2cdetect -y 1` shows `0x10`, run `uv run pi5servo move hat_pwm1 center --backend dfr0566 --address 0x10 --bus-id 1`, and confirm stable signal/output
- required mixed checks: run `uv run pi5servo cmd "M_gpio12:45/hat_pwm1:-30" --pins gpio12,hat_pwm1`, then run `uv run pi5servo servo-tool` and verify both endpoint types work in one session
- signal-quality requirement: measure both native GPIO and DFR0566 PWM outputs with a logic analyser or oscilloscope before trusting full robot motion

Follow-up:

- run the Raspberry Pi 5 validation checklist for native GPIO, DFR0566 PWM, and mixed routing
- if the checks pass, treat the `pi5servo` DFR0566 refinement as hardware-validated
- if any motion instability appears, capture the exact endpoint type, backend, and pulse measurement before changing calibration or timing logic

### pi5servo DFR0566 Refinement Planning

Summary:

- researched the DFRobot Raspberry Pi IO Expansion HAT DFR0566 using the official wiki, tech specs, and vendor source code
- confirmed the board must be treated as two different servo connection families:
  - native GPIO endpoints, including servos attached to DFR0566 digital ports used as Raspberry Pi GPIO breakouts
  - DFR0566 PWM endpoints, which are MCU-managed over I2C and need a dedicated backend
- audited the current `pi5servo` code to identify the functions that must change for explicit endpoint naming and mixed backend routing
- updated the migration plan and documentation so future implementation work distinguishes `gpioXX` from `hat_pwmN` explicitly

Files changed:

- [developmentPlan.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/developmentPlan.md)
- [pi5servo/README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/README.md)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentLog.md)

Why:

- the current `pi5servo` implementation still assumes one backend and one integer identifier space
- that model is fine for native GPIO-only usage, but it is not enough for mixed native GPIO and DFR0566 PWM routing
- the DFR0566 digital ports and the DFR0566 PWM ports are not equivalent, so the docs and plan need to state that clearly before implementation starts

Affected functions confirmed by audit:

- [create_servo_backend](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/backend.py)
- [Servo.__init__](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/servo.py#L47)
- [ServoGroup.__init__](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/multi_servos.py#L30)
- [ServoGroup._resolve_backend](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/multi_servos.py#L74)
- [ServoGroup._resolve_targets](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/multi_servos.py#L343)
- [ServoTarget](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/parser/command.py#L16)
- [ParsedCommand](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/parser/command.py#L35)
- [parse_command](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/parser/command.py#L50)
- [parse_pin_list](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/_common.py#L30)
- [create_servo_from_config](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/_common.py#L170)
- [create_group_from_config](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/_common.py#L206)
- [ConfigManager.load](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/config/config_manager.py#L63)
- [ConfigManager.get_calibration](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/config/config_manager.py#L118)
- [ConfigManager.set_calibration](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/config/config_manager.py#L141)
- [ConfigManager.get_all_calibrations](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/config/config_manager.py#L158)

Lint and test results:

- no code changes were made in this planning pass
- no package test run was required because this was a documentation-only update

Raspberry Pi validation status:

- no new Pi validation was run
- the DFR0566 refinement validation plan is now documented before implementation begins

## 2026-03-10

### pi5servo Migration

Summary:

- migrated the final standalone Raspberry Pi 5 driver library as [pi5servo](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo)
- kept the legacy `pi0servo` motion model, calibration flow, movement-tool command format, CLI command set, and `servo.json` contract
- replaced direct `pigpio.set_servo_pulsewidth()` usage with a backend layer that supports header-connected Raspberry Pi 5 hardware PWM first, optional PCA9685 support second, and legacy `pigpio` compatibility as a retained future path
- updated the CLI workflow so standalone Pi 5 usage no longer depends on `pigpiod`, and added optional backend metadata to `servo.json`
- added backend, config, core, and CLI regression coverage for the new standalone path

Files changed:

- [pi5servo/pyproject.toml](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/pyproject.toml)
- [pi5servo/.python-version](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/.python-version)
- [pi5servo/README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/README.md)
- [pi5servo/src/pi5servo/__init__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/__init__.py)
- [pi5servo/src/pi5servo/__main__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/__main__.py)
- [pi5servo/src/pi5servo/driver.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/driver.py)
- [pi5servo/src/pi5servo/core/backend.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/backend.py)
- [pi5servo/src/pi5servo/core/backend_errors.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/backend_errors.py)
- [pi5servo/src/pi5servo/core/backends/hardware_pwm.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/backends/hardware_pwm.py)
- [pi5servo/src/pi5servo/core/backends/pca9685.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/backends/pca9685.py)
- [pi5servo/src/pi5servo/core/backends/pwm_pio.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/backends/pwm_pio.py)
- [pi5servo/src/pi5servo/core/servo.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/servo.py)
- [pi5servo/src/pi5servo/core/multi_servos.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/core/multi_servos.py)
- [pi5servo/src/pi5servo/config/__init__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/config/__init__.py)
- [pi5servo/src/pi5servo/config/config_manager.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/config/config_manager.py)
- [pi5servo/src/pi5servo/cli/_common.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/_common.py)
- [pi5servo/src/pi5servo/cli/cmd.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/cmd.py)
- [pi5servo/src/pi5servo/cli/move.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/move.py)
- [pi5servo/src/pi5servo/cli/calib.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/calib.py)
- [pi5servo/src/pi5servo/cli/status.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/status.py)
- [pi5servo/src/pi5servo/cli/config_cmd.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/config_cmd.py)
- [pi5servo/src/pi5servo/cli/servo_tool.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/src/pi5servo/cli/servo_tool.py)
- [pi5servo/tests/test_backend.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/tests/test_backend.py)
- [pi5servo/tests/test_core.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/tests/test_core.py)
- [pi5servo/tests/test_config.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/tests/test_config.py)
- [pi5servo/tests/test_cli.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/tests/test_cli.py)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentLog.md)

Why:

- `pi0servo` is the highest-risk migration because servo motion quality depends on accurate, stable pulse generation
- Raspberry Pi 5 does not support the old `pigpio`-centric standalone path used in the legacy environment
- the new library needed a backend contract so motion planning, calibration, and CLI behavior could stay stable while the pulse generator changes between header-connected Pi 5 PWM and optional external controller backends
- standalone usage for NinjaClawBot now works without mandatory `ninja_core` or `pigpiod` integration

Lint and test results:

- Phase 1: `uv run python -m compileall src tests`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest -q` -> `82 passed`
- Phase 2: same gate after backend layer -> `88 passed`
- Phase 3: same gate after `Servo` and `ServoGroup` backend port -> `90 passed`
- Phase 4 and final package state: same gate after config and CLI migration -> `95 passed`

Raspberry Pi validation status:

- manual Raspberry Pi 5 validation is still required
- planned checks: verify PWM overlay configuration, run `uv run pi5servo status --pins 12,13`, run single-servo center/min/max tests, run `uv run pi5servo cmd "M_12:45/13:-30" --pins 12,13`, run `uv run pi5servo servo-tool`, and verify safe exit centering
- signal-quality requirement: measure the servo output with a logic analyser or oscilloscope before trusting the setup for full robot motion
- expected hardware result: stable pulse output, correct save/load behavior in `servo.json`, repeatable synchronized motion, and clean backend release on exit

Follow-up:

- run the Raspberry Pi 5 manual validation checklist for `pi5servo`
- if hardware validation passes, mark the standalone Pi 5 driver migration set as complete
- if additional channel count or isolation is needed later, extend the optional `pca9685` backend path

### pi5disp Runtime Fixes

Summary:

- audited the `pi5disp` runtime after Raspberry Pi 5 issues were reported in `display-tool`
- identified the first bug as a config/runtime mismatch: the `brightness` command changed a temporary display instance but did not persist the value, and new display sessions did not apply the saved brightness setting
- identified the second bug as backend churn inside `display-tool`: each menu action recreated and destroyed the display backend, which could leave the next demo run visually stuck until a later clear/reset
- fixed the tool to keep one live display session during the interactive menu and added regression coverage for the `demo -> brightness -> demo` sequence

Files changed:

- [pi5disp/src/pi5disp/__main__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/src/pi5disp/__main__.py)
- [pi5disp/src/pi5disp/cli/_common.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/src/pi5disp/cli/_common.py)
- [pi5disp/src/pi5disp/cli/display_tool.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/src/pi5disp/cli/display_tool.py)
- [pi5disp/tests/test_cli.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/tests/test_cli.py)
- [pi5disp/tests/test_display_tool.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/tests/test_display_tool.py)
- [pi5disp/README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/README.md)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentLog.md)

Why:

- `pi5disp brightness` previously behaved like a throwaway runtime change instead of a saved display setting
- `create_display()` did not apply the saved `brightness` value when opening a new display instance
- `display-tool` reused command wrappers that opened and closed fresh Pi 5 backends for each action, which was more fragile than a single live session

Lint and test results:

- `uv run python -m compileall src tests`: passed
- `uv run ruff check .`: passed
- `uv run ruff format --check .`: passed
- `uv run pytest -q`: `63 passed in 27.23s`

Raspberry Pi validation status:

- manual Raspberry Pi 5 validation is still required
- expected validation: run `uv run pi5disp display-tool`, choose ball demo, then brightness, then ball demo again, and confirm the second demo renders without needing `Clear`
- expected validation: run `uv run pi5disp brightness 50`, then `uv run pi5disp config show`, and confirm the saved brightness is `50`

Follow-up:

- verify the fixed `display-tool` sequence on the target Raspberry Pi 5
- if it passes, continue with the `pi5servo` migration phase

### pi5disp Migration

Summary:

- migrated the third Raspberry Pi 5 standalone driver library as [pi5disp](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp)
- kept the legacy `pi0disp` public API shape, CLI command set, renderer helpers, ticker effects, bundled fonts, and `display.json` config contract
- replaced the legacy `pigpio` SPI, GPIO, and backlight control path with a Raspberry Pi 5 compatible backend split across `spidev` and an `RPi.GPIO` compatible interface intended for `rpi-lgpio`
- ported and adapted the legacy test coverage for driver behavior, config handling, renderer helpers, text ticker behavior, and CLI smoke checks

Files changed:

- [pi5disp/pyproject.toml](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/pyproject.toml)
- [pi5disp/.python-version](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/.python-version)
- [pi5disp/display.json](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/display.json)
- [pi5disp/README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/README.md)
- [pi5disp/src/pi5disp/__init__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/src/pi5disp/__init__.py)
- [pi5disp/src/pi5disp/__main__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/src/pi5disp/__main__.py)
- [pi5disp/src/pi5disp/driver.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/src/pi5disp/driver.py)
- [pi5disp/src/pi5disp/core/driver.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/src/pi5disp/core/driver.py)
- [pi5disp/src/pi5disp/core/renderer.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/src/pi5disp/core/renderer.py)
- [pi5disp/src/pi5disp/config/config_manager.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/src/pi5disp/config/config_manager.py)
- [pi5disp/src/pi5disp/effects/text_ticker.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/src/pi5disp/effects/text_ticker.py)
- [pi5disp/src/pi5disp/cli/_common.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/src/pi5disp/cli/_common.py)
- [pi5disp/src/pi5disp/cli/init_cmd.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/src/pi5disp/cli/init_cmd.py)
- [pi5disp/src/pi5disp/cli/image_cmd.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/src/pi5disp/cli/image_cmd.py)
- [pi5disp/src/pi5disp/cli/text_cmd.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/src/pi5disp/cli/text_cmd.py)
- [pi5disp/src/pi5disp/cli/demo_cmd.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/src/pi5disp/cli/demo_cmd.py)
- [pi5disp/src/pi5disp/cli/info_cmd.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/src/pi5disp/cli/info_cmd.py)
- [pi5disp/src/pi5disp/cli/display_tool.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/src/pi5disp/cli/display_tool.py)
- [pi5disp/tests/test_config.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/tests/test_config.py)
- [pi5disp/tests/test_renderer.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/tests/test_renderer.py)
- [pi5disp/tests/test_driver.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/tests/test_driver.py)
- [pi5disp/tests/test_text_ticker.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/tests/test_text_ticker.py)
- [pi5disp/tests/test_cli.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp/tests/test_cli.py)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentLog.md)

Why:

- Raspberry Pi 5 does not support the legacy `pigpio` path used by `pi0disp`
- the display migration needed to preserve the known-good ST7789V behavior while isolating only the transport layer change
- the legacy package and tests require `display()` to remain a full-frame path, with `display_region()` as the partial-update path
- the new library had to remain standalone-first while keeping future compatibility hooks such as `driver.py`

Lint and test results:

- `uv run python -m compileall src tests`: passed
- `uv run ruff check .`: passed
- `uv run ruff format --check .`: passed
- `uv run pytest -q`: `59 passed in 26.78s`
- `uv run pi5disp --help`: passed

Raspberry Pi validation status:

- manual Raspberry Pi 5 validation is still required
- planned checks: `ls /dev/spidev0.0`, `uv run pi5disp --help`, `uv run pi5disp init --defaults`, `uv run pi5disp config show`, `uv run pi5disp info`, `uv run pi5disp clear`, `uv run pi5disp brightness 50`, `uv run pi5disp image ./example.png`, `uv run pi5disp text "Hello NinjaClawBot"`, `uv run pi5disp text "Scrolling text" --scroll --duration 10`, `uv run pi5disp demo --num-balls 3 --duration 10`, and `uv run pi5disp display-tool`
- expected hardware result: stable panel initialization, clear image and text rendering, working brightness control, working scrolling and demo effects, and clean SPI and GPIO release on exit

Follow-up:

- run the Raspberry Pi 5 manual validation checklist for `pi5disp`
- if hardware validation passes, proceed to the `pi5servo` migration phase

### pi5vl53l0x Migration

Summary:

- migrated the second Raspberry Pi 5 standalone driver library as [pi5vl53l0x](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x)
- kept the legacy `pi0vl53l0x` public API shape, CLI command set, config contract, calibration flow, health check, and reinitialize path
- replaced the legacy `pigpio` I2C transport with a thread-safe `smbus2` backend over the Raspberry Pi 5 kernel I2C interface
- ported and adapted the legacy test suite for I2C, sensor logic, config handling, and CLI smoke coverage

Files changed:

- [pi5vl53l0x/pyproject.toml](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/pyproject.toml)
- [pi5vl53l0x/.python-version](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/.python-version)
- [pi5vl53l0x/README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/README.md)
- [pi5vl53l0x/src/pi5vl53l0x/__init__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/src/pi5vl53l0x/__init__.py)
- [pi5vl53l0x/src/pi5vl53l0x/__main__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/src/pi5vl53l0x/__main__.py)
- [pi5vl53l0x/src/pi5vl53l0x/driver.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/src/pi5vl53l0x/driver.py)
- [pi5vl53l0x/src/pi5vl53l0x/registers.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/src/pi5vl53l0x/registers.py)
- [pi5vl53l0x/src/pi5vl53l0x/core/i2c.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/src/pi5vl53l0x/core/i2c.py)
- [pi5vl53l0x/src/pi5vl53l0x/core/sensor.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/src/pi5vl53l0x/core/sensor.py)
- [pi5vl53l0x/src/pi5vl53l0x/config/config_manager.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/src/pi5vl53l0x/config/config_manager.py)
- [pi5vl53l0x/src/pi5vl53l0x/cli/sensor_tool.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/src/pi5vl53l0x/cli/sensor_tool.py)
- [pi5vl53l0x/tests/test_i2c.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/tests/test_i2c.py)
- [pi5vl53l0x/tests/test_sensor.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/tests/test_sensor.py)
- [pi5vl53l0x/tests/test_config.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/tests/test_config.py)
- [pi5vl53l0x/tests/test_cli.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x/tests/test_cli.py)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentLog.md)

Why:

- Raspberry Pi 5 does not support the legacy `pigpio` I2C path used by `pi0vl53l0x`
- the migration needed to preserve the known-good VL53L0X register sequencing while only replacing the transport layer
- the new library had to stay standalone-first for NinjaClawBot while keeping future compatibility hooks such as `driver.py`

Lint and test results:

- `uv run python -m compileall src tests`: passed
- `uv run ruff check .`: passed
- `uv run ruff format --check .`: passed
- `uv run pytest -q`: `62 passed in 2.43s`
- `uv run pi5vl53l0x --help`: passed

Raspberry Pi validation status:

- manual Raspberry Pi 5 validation is still required
- planned checks: `ls /dev/i2c-1`, `sudo i2cdetect -y 1`, `uv run pi5vl53l0x test`, `uv run pi5vl53l0x get --count 5 --interval 0.5`, `uv run pi5vl53l0x status`, `uv run pi5vl53l0x performance --count 50`, `uv run pi5vl53l0x calibrate --distance 200 --count 10`, and `uv run pi5vl53l0x sensor-tool`
- expected hardware result: visible sensor at address `0x29`, stable readings, successful calibration save, and successful reinitialize recovery

Follow-up:

- run the Raspberry Pi 5 manual validation checklist for `pi5vl53l0x`
- if hardware validation passes, proceed to the `pi5servo` or `pi5disp` migration phase

### pi5buzzer Migration

Summary:

- migrated the first Raspberry Pi 5 standalone driver library as [pi5buzzer](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer)
- kept the legacy `pi0buzzer` public API shape, note table, emotion sounds, CLI command set, and `buzzer.json` config format
- replaced direct `pigpio` usage with a backend abstraction and a default `RPi.GPIO` compatible backend factory intended for `rpi-lgpio` on Raspberry Pi 5
- ported and adapted the legacy test suite for the new package

Files changed:

- [pi5buzzer/pyproject.toml](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/pyproject.toml)
- [pi5buzzer/README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/README.md)
- [pi5buzzer/src/pi5buzzer/__init__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/src/pi5buzzer/__init__.py)
- [pi5buzzer/src/pi5buzzer/__main__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/src/pi5buzzer/__main__.py)
- [pi5buzzer/src/pi5buzzer/driver.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/src/pi5buzzer/driver.py)
- [pi5buzzer/src/pi5buzzer/notes.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/src/pi5buzzer/notes.py)
- [pi5buzzer/src/pi5buzzer/core/driver.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/src/pi5buzzer/core/driver.py)
- [pi5buzzer/src/pi5buzzer/core/music.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/src/pi5buzzer/core/music.py)
- [pi5buzzer/src/pi5buzzer/config/config_manager.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/src/pi5buzzer/config/config_manager.py)
- [pi5buzzer/src/pi5buzzer/cli/buzzer_tool.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/src/pi5buzzer/cli/buzzer_tool.py)
- [pi5buzzer/tests/conftest.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/tests/conftest.py)
- [pi5buzzer/tests/test_driver.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/tests/test_driver.py)
- [pi5buzzer/tests/test_music.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/tests/test_music.py)
- [pi5buzzer/tests/test_config.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/tests/test_config.py)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentLog.md)

Why:

- `pi5buzzer` was the lowest-risk first migration and establishes the backend pattern for the remaining Pi 5 libraries
- Raspberry Pi 5 does not support the legacy `pigpio` path used by `pi0buzzer`, so the GPIO transport needed to be isolated behind a Pi 5 compatible interface
- the new library had to remain standalone-first while keeping future integration surfaces such as `driver.py`

Lint and test results:

- `python -m compileall .`: passed
- `ruff check .`: passed
- `ruff format --check .`: passed
- `pytest -q`: `63 passed in 6.32s`

Raspberry Pi validation status:

- manual Raspberry Pi 5 validation is still required
- planned checks: `pi5buzzer --help`, `pi5buzzer init 17`, `pi5buzzer info --health-check`, `pi5buzzer beep 440 0.3`, `pi5buzzer play happy`, and a short `play_song()` Python sequence
- expected hardware result: audible short tones, stable queued playback, and silent output after `off()` or CLI exit

Follow-up:

- run the Raspberry Pi 5 manual validation checklist for `pi5buzzer`
- if hardware validation passes, proceed to the `pi5vl53l0x` migration phase

### pi5buzzer Installation Fix

Summary:

- investigated the standalone Raspberry Pi installation failure reported for `uv sync --extra pi --extra dev`
- identified the failure as an `lgpio` wheel-availability problem, not a `pi5buzzer` code defect
- pinned the standalone project to Python 3.11 and documented the manual recovery steps in the package README

Files changed:

- [pi5buzzer/pyproject.toml](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/pyproject.toml)
- [pi5buzzer/.python-version](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/.python-version)
- [pi5buzzer/README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentLog.md)

Why:

- `rpi-lgpio` depends on `lgpio`
- `lgpio 0.2.2.0` currently publishes Raspberry Pi Linux ARM wheels for CPython 3.9, 3.10, 3.11, and 3.12, but not 3.13
- when `uv` selected Python 3.13, it fell back to a source build, which required `swig` and failed on a normal Raspberry Pi setup
- pinning the package to Python 3.11 gives a reliable install path on Raspberry Pi OS Bookworm

Lint and test results:

- no code tests run
- packaging and documentation update only

Raspberry Pi validation status:

- manual Raspberry Pi 5 installation retry is still required
- expected recovery path: remove `.venv`, rerun `uv sync --extra pi --extra dev`, then verify with `uv run pi5buzzer --help`

Follow-up:

- confirm the updated install flow works on the target Raspberry Pi 5
- if it does, keep Python 3.11 as the standalone default for the next Pi-facing driver packages

### pi5buzzer Shutdown Fix

Summary:

- audited the `pi5buzzer` backend shutdown path after a Raspberry Pi 5 runtime traceback was reported when leaving `buzzer-tool`
- identified the bug as a cleanup-order issue between our backend wrapper and `rpi-lgpio` PWM object destruction
- fixed the backend so PWM objects are released before `GPIO.cleanup()` closes the chip handle
- added regression tests for destructor-safe cleanup and repeated backend stop calls

Files changed:

- [pi5buzzer/src/pi5buzzer/core/driver.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/src/pi5buzzer/core/driver.py)
- [pi5buzzer/tests/conftest.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/tests/conftest.py)
- [pi5buzzer/tests/test_driver.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/tests/test_driver.py)
- [pi5buzzer/README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentLog.md)

Why:

- upstream `rpi-lgpio` PWM objects call `stop()` from `__del__`
- our wrapper previously closed the GPIO chip handle before those PWM objects were fully released
- that left the later destructor path running against a closed chip handle and produced the `NoneType & int` traceback on exit
- the same centralized backend fix also protects the other CLI paths that call `pi.stop()`

Lint and test results:

- `python -m compileall .`: passed
- `ruff check .`: passed
- `ruff format --check .`: passed
- `pytest -q`: `65 passed in 6.32s`

Raspberry Pi validation status:

- manual Raspberry Pi 5 validation is still required
- expected validation: run `uv run pi5buzzer buzzer-tool`, choose `9. Exit`, and confirm there is no cleanup traceback after `Goodbye!`

Follow-up:

- verify the clean shutdown behavior on the target Raspberry Pi 5
- if the result is clean, use the same shutdown pattern in future Pi 5 drivers that wrap `rpi-lgpio` resources

### Workflow Refinement

Summary:

- refined the agentic development workflow for the new Pi 5 driver libraries
- updated the `ninjaclawbot-implementation` skill to follow the standalone-first `pi5*` migration plan
- aligned repository docs so the skill, development plan, and developer guide point to the same workflow

Files changed:

- `.agents/skills/ninjaclawbot-implementation/SKILL.md`
- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`

Why:

- the original skill was too generic for the current Pi 5 library migration work
- the new workflow needed explicit rules for required files, required functions, backend selection, quality checks, and manual Raspberry Pi 5 validation after each library

Lint and test results:

- no code tests run
- documentation-only update

Raspberry Pi validation status:

- not applicable for this change

Follow-up:

- use the updated skill as the default implementation guide for future `pi5buzzer`, `pi5servo`, `pi5disp`, and `pi5vl53l0x` work

### 2026-03-12 `pi5servo` Quick Move Silent-Skip Fix

Summary:

- fixed the `pi5servo` interactive tool so Quick Move now forces the requested PWM write instead of silently skipping commands like `F_gpio12:0/gpio13:0`
- added regression coverage for the direct Quick Move path and for the core forced command-execution path

Files changed:

- `pi5servo/src/pi5servo/core/multi_servos.py`
- `pi5servo/src/pi5servo/cli/servo_tool.py`
- `pi5servo/tests/test_core.py`
- `pi5servo/tests/test_servo_tool.py`
- `pi5servo/README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`

Why:

- the interactive tool could skip a return-to-center command when cached servo state said the target was already `0°`, even if the operator needed the PWM signal to be re-sent
- legacy `ninja_core` movement execution used forced writes to avoid this kind of stale-state skip, and the Pi 5 interactive tool needed the same protection for direct operator commands

Lint and test results:

- `uv run python -m compileall src tests`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pytest -q`
- result in `pi5servo`: `123 passed`

Raspberry Pi validation status:

- manual Raspberry Pi 5 validation is still required

Follow-up:

- on the Raspberry Pi 5, run `uv run pi5servo servo-tool`, move the servos away from center, then run `F_gpio12:0/gpio13:0` in Quick Move and confirm both servos actively return to center
- do not proceed with the `ninjaclawbot` integration-layer reset until this standalone `pi5servo` fix is manually confirmed

### 2026-03-12 `pi5servo` Same-Session Calibration Refresh Fix

Summary:

- audited the remaining `servo-tool` failure after the first Quick Move fix
- identified the true issue as stale live servo-group state after calibration and other config-changing actions inside the same interactive session
- changed `servo-tool` to rebuild its persistent group after calibration, speed changes, and config imports
- stopped temporary native-GPIO servo actions from borrowing and tearing down the persistent backend object

Files changed:

- `pi5servo/src/pi5servo/cli/servo_tool.py`
- `pi5servo/tests/test_servo_tool.py`
- `pi5servo/README.md`
- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`

Why:

- the user reported that `F_12:0/13:0` still failed immediately after calibration, but worked after exiting and restarting `servo-tool`
- that behavior showed the real bug was not only skipped PWM writes; the interactive tool was also keeping stale servo/backend state until the next process restart
- the old `ninja_core` movement flow explicitly rebuilt state after calibration, and the Pi 5 interactive tool needed the same rule

Lint and test results:

- `uv run python -m compileall src tests`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pytest -q`
- result in `pi5servo`: `125 passed`

Raspberry Pi validation status:

- manual Raspberry Pi 5 validation is still required

Follow-up:

- on the Raspberry Pi 5, start `uv run pi5servo servo-tool`, calibrate the servo, stay in the same session, then run Quick Move commands including `F_12:0/13:0`
- confirm the servos still respond correctly without needing to exit and restart the tool
- do not proceed to the `ninjaclawbot` reset until this same-session validation is confirmed
