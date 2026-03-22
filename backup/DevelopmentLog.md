# Development Log

## 2026-03-20

### MicDevelopment.md Audit Consolidation And Always-On Voice Planning Refresh

Summary:

- reviewed the current `MicDevelopment.md` planning document after the one-shot
  `pi5mic` path became usable in standalone and integrated OpenClaw flows
- found that the document still contained the older longer planning structure,
  which made it harder to see:
  - the current overall product goal
  - which `pi5mic` milestones are already finished
  - which items are still one-shot only
  - what the next always-on build should do
- rewrote `MicDevelopment.md` into a more practical planning document that now
  clearly separates:
  - overall development goal and user-facing spec
  - current implemented features
  - open gaps and needed improvements
  - the audit summary across `pi5mic`, `ninjaclawbot`, and the OpenClaw plugin
  - the recommended architecture for always-on voice input
  - the recommended setup order for the full NinjaClawBot project
  - the phased implementation plan for the always-on feature
- locked the latest clarified design rules into the document:
  - preserve the original spoken language when sending text to OpenClaw
  - keep always-on voice input manual start and manual stop only
  - keep `pi5mic` optional but strongly recommended during project setup
  - keep OpenClaw voice enablement best-effort and skippable when `pi5mic`
    config is missing

Files changed:

- [MicDevelopment.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/MicDevelopment.md)
- [backup/DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

Why:

- the next build step is the always-on voice feature, so the planning document
  needed to become easier to use as a real implementation guide
- the older document was still useful as audit history, but it no longer gave a
  concise status view of what is already built versus what remains
- the user explicitly requested a clearer document that combines the current
  build status with the next-phase always-on implementation plan

Lint and test results:

- `git diff --check`

Raspberry Pi validation status:

- not applicable for this document-only update
- no code behavior changed in this pass

### pi5mic CLI Import Syntax Fix For `setup` And `mic-tool`

Summary:

- audited the Raspberry Pi traceback showing:
  - `SyntaxError: unterminated string literal`
  - import failure in `pi5mic/src/pi5mic/cli/run_cmd.py`
- confirmed the root cause was a malformed multiline f-string in the OpenClaw
  delivery-status banner inside `run_cmd`
- ran a repo-wide Python AST parse sanity check and confirmed that this was the
  only syntax error in the workspace at the time of the audit
- simplified the `run` banner rendering so the delivery label is built first and
  then echoed with one straightforward f-string
- added a regression test that loads an OpenClaw config and verifies that the
  `run` command prints the delivery mode correctly before the cycle starts
- updated the user docs so non-developer Raspberry Pi users can identify this
  exact error quickly and recover with `git pull`, `uv sync --extra dev`, and a
  retry of `pi5mic setup`

Files changed:

- [pi5mic/src/pi5mic/cli/run_cmd.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/cli/run_cmd.py)
- [pi5mic/tests/test_cli.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/tests/test_cli.py)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [pi5mic/README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/README.md)
- [backup/DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

Why:

- the broken string literal prevented the entire `pi5mic` CLI package from
  importing, so the user could not open `setup` or `mic-tool` at all
- because the failure happened during import, it looked like a Raspberry Pi
  runtime issue even though the real problem was a Python syntax regression
- the fix needed both a code repair and a regression test so future OpenClaw
  delivery-label changes do not silently break the CLI entry points again

Lint and test results:

- `python3 -m compileall pi5mic/src pi5mic/tests`
- `uv run --extra dev ruff check pi5mic/src pi5mic/tests`
- `uv run --extra dev ruff format --check pi5mic/src pi5mic/tests`
- `cd pi5mic && uv run --extra dev pytest -q tests -c pyproject.toml`
- result: `69 passed`

Raspberry Pi validation status:

- local validation passed
- Raspberry Pi follow-up still required:
  - `cd ~/NinjaClawBot`
  - `git pull`
  - `uv sync --extra dev`
  - `uv run pi5mic --help`
  - `uv run pi5mic setup`
  - `uv run pi5mic mic-tool`
  - confirm both commands open normally without the old syntax traceback

### pi5mic OpenClaw Dual Reply Delivery And Telegram Route Discovery

Summary:

- reviewed the latest Raspberry Pi validation result after the OpenClaw handoff
  fixes
- confirmed the remaining behavior gap:
  - `pi5mic` could record, transcribe, and hand the text to OpenClaw
  - the local terminal showed the OpenClaw reply
  - Telegram did not receive the same reply for voice-triggered turns
- verified against the current OpenClaw docs and source that:
  - `openclaw agent` can both print locally and deliver outbound replies when
    `--deliver` is used
  - Telegram delivery needs a concrete target such as a chat id or topic target
  - the safest way to discover that target is from OpenClaw session metadata
- refined `pi5mic` so OpenClaw mode now:
  - inspects the local OpenClaw config to see whether Telegram is enabled
  - probes recent OpenClaw session data for the newest Telegram reply target
  - offers a one-step setup choice to reply both locally and in Telegram
  - saves the explicit Telegram reply target into `mic.json` when the user
    approves it
- improved runtime visibility so:
  - `status` now shows the saved reply target
  - `doctor` now shows Telegram enablement, detected targets, and delivery-mode
    mismatches clearly
  - `run --once` now prints the current delivery mode at the start
- updated the user docs so the OpenClaw + Telegram voice path is explained in
  plain language, including the recovery path when replies still stay local

Files changed:

- [pi5mic/src/pi5mic/integration/openclaw_setup.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/integration/openclaw_setup.py)
- [pi5mic/src/pi5mic/integration/delivery.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/integration/delivery.py)
- [pi5mic/src/pi5mic/cli/setup_cmd.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/cli/setup_cmd.py)
- [pi5mic/src/pi5mic/cli/doctor.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/cli/doctor.py)
- [pi5mic/src/pi5mic/cli/status.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/cli/status.py)
- [pi5mic/src/pi5mic/cli/run_cmd.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/cli/run_cmd.py)
- [pi5mic/tests/test_openclaw_setup.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/tests/test_openclaw_setup.py)
- [pi5mic/tests/test_cli.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/tests/test_cli.py)
- [pi5mic/tests/test_doctor.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/tests/test_doctor.py)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [pi5mic/README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/README.md)
- [InstallationGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/InstallationGuide.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [backup/DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

Why:

- the previous OpenClaw setup work made local voice handoff reliable, but it
  still defaulted to local-only replies
- for the real Raspberry Pi workflow, the user wanted the same voice turn to
  show a local terminal reply and also appear in Telegram
- this needed an explicit OpenClaw delivery target, not just more plugin-side
  logic

Lint and test results:

- `cd pi5mic && uv run --extra dev python -m compileall src tests`
- `cd pi5mic && uv run --extra dev ruff check src tests`
- `cd pi5mic && uv run --extra dev ruff format --check src tests`
- `cd pi5mic && uv run --extra dev pytest -q tests -c pyproject.toml`
- result: `68 passed`

Raspberry Pi validation status:

- local package validation passed
- Raspberry Pi follow-up still required:
  - send one short Telegram message to the OpenClaw bot in the chat or topic
    that should receive voice replies
  - rerun `uv run pi5mic setup` and answer `y` when asked to reply both locally
    and in Telegram
  - rerun `uv run pi5mic status`
  - rerun `uv run pi5mic doctor`
  - rerun `uv run pi5mic run --once`
  - confirm the reply appears both:
    - in the local terminal output
    - in the chosen Telegram chat or topic

### pi5mic OpenClaw Session-ID Migration Fix

Summary:

- reviewed the Raspberry Pi validation result after the OpenClaw auto-setup work
- confirmed that recording and Whisper transcription succeeded, but the
  OpenClaw handoff still failed after that with:
  - `Invalid session ID: voice:local-mic`
- verified against the current OpenClaw source that:
  - `openclaw agent --session-id` is validated with a safe session-id regex
  - `:` is not allowed in that field
  - `voice:local-mic` was therefore a legacy-invalid value for newer OpenClaw
    builds
- patched `pi5mic` so the OpenClaw profile now uses a safe default session id:
  - new default: `voice-local-mic`
- added automatic migration so existing `mic.json` files are repaired in memory
  on load and then persisted on the next save
- hardened the transport path so even if a stale config somehow reaches runtime,
  `pi5mic` still normalizes the OpenClaw session id before dispatch
- updated the docs so users can understand what `Invalid session ID` means and
  how the new automatic fix works

Files changed:

- [pi5mic/src/pi5mic/config/config_manager.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/config/config_manager.py)
- [pi5mic/src/pi5mic/integration/openclaw_session.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/integration/openclaw_session.py)
- [pi5mic/src/pi5mic/integration/openclaw_setup.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/integration/openclaw_setup.py)
- [pi5mic/src/pi5mic/transport/openclaw_cli.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/transport/openclaw_cli.py)
- [pi5mic/tests/test_config.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/tests/test_config.py)
- [pi5mic/tests/test_transport_openclaw.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/tests/test_transport_openclaw.py)
- [pi5mic/tests/test_cli.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/tests/test_cli.py)
- [pi5mic/tests/test_doctor.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/tests/test_doctor.py)
- [pi5mic/tests/test_openclaw_setup.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/tests/test_openclaw_setup.py)
- [pi5mic/tests/test_openclaw_session.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/tests/test_openclaw_session.py)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [pi5mic/README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/README.md)
- [InstallationGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/InstallationGuide.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [backup/DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

Why:

- the earlier OpenClaw integration work fixed pairing and auto-discovery, but
  the legacy session-id default still broke the final transcript handoff on the
  user's real Raspberry Pi gateway
- this needed an actual code migration, not just a docs workaround, because old
  configs were already saved in the field

Lint and test results:

- `uv run --extra dev python -m compileall pi5mic/src pi5mic/tests`
- `uv run --extra dev ruff check pi5mic/src pi5mic/tests`
- `uv run --extra dev ruff format --check pi5mic/src pi5mic/tests`
- `cd pi5mic && uv run --extra dev pytest -q tests -c pyproject.toml`
- result: `65 passed`

Raspberry Pi validation status:

- local package validation passed
- Raspberry Pi follow-up still required:
  - rerun `uv run pi5mic setup` in `openclaw` mode
  - rerun `uv run pi5mic doctor`
  - rerun `uv run pi5mic run --once`
  - confirm the OpenClaw reply appears after transcription
  - optional direct OpenClaw check:
    `openclaw agent --agent main --session-id voice-local-mic --message "hello" --json`

### pi5mic OpenClaw Auto-Setup And Guided Pairing Repair

Summary:

- reviewed the real OpenClaw failure mode reported during Raspberry Pi testing:
  - `pi5mic` recorded and transcribed correctly
  - the OpenClaw handoff failed with `pairing required`
  - the old setup flow still asked the user to type OpenClaw details manually
- identified the main usability gap:
  - `pi5mic` already had enough information to reuse most local OpenClaw
    settings, but the setup wizard did not read them automatically
  - pairing recovery also required manual shell commands even though the local
    CLI supports `openclaw devices approve --latest`
- added a new OpenClaw setup helper layer that:
  - locates the local `openclaw` CLI
  - reads `~/.openclaw/openclaw.json` when available
  - derives the gateway URL, agent id, session key, and plugin readiness hints
  - explains common OpenClaw failures in plain language
- refined `pi5mic setup` so `Profile: openclaw` now:
  - auto-discovers the local OpenClaw settings
  - applies them to `mic.json`
  - summarizes what was detected and what fell back to defaults
  - warns clearly if the NinjaClawBot plugin does not look ready
  - runs a safe OpenClaw readiness check after saving
  - offers one-click approval of the newest local pairing request when OpenClaw
    asks for it
- refined the runtime UX:
  - `doctor` now reports the detected OpenClaw config path and readiness result
  - `run --once` now wraps OpenClaw transport/presence errors with actionable
    recovery guidance
  - `mic-tool` now catches command-level `ClickException`s and returns to the
    menu instead of dropping the user out immediately
- updated the user-facing docs so the new OpenClaw flow is explained step by
  step for non-developers

Files changed:

- [pi5mic/src/pi5mic/cli/setup_cmd.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/cli/setup_cmd.py)
- [pi5mic/src/pi5mic/cli/doctor.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/cli/doctor.py)
- [pi5mic/src/pi5mic/cli/run_cmd.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/cli/run_cmd.py)
- [pi5mic/src/pi5mic/cli/mic_tool.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/cli/mic_tool.py)
- [pi5mic/src/pi5mic/integration/openclaw_setup.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/integration/openclaw_setup.py)
- [pi5mic/tests/test_cli.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/tests/test_cli.py)
- [pi5mic/tests/test_doctor.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/tests/test_doctor.py)
- [pi5mic/tests/test_mic_tool_setup.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/tests/test_mic_tool_setup.py)
- [pi5mic/tests/test_openclaw_setup.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/tests/test_openclaw_setup.py)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [pi5mic/README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/README.md)
- [InstallationGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/InstallationGuide.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [backup/DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

Why:

- the previous `openclaw` profile still depended on manual gateway detail entry,
  which made the guided setup promise weaker than the actual local config
  information already available on the Raspberry Pi
- pairing failures were understandable once diagnosed, but the repair path
  belonged inside the setup wizard so non-developers could reach a working
  voice handoff without dropping into OpenClaw commands first
- the operator-facing documentation needed to match the new “detect, explain,
  approve, retry” flow exactly

Lint and test results:

- `uv run --extra dev python -m compileall pi5mic/src pi5mic/tests`
- `uv run --extra dev ruff check pi5mic/src pi5mic/tests`
- `uv run --extra dev ruff format --check pi5mic/src pi5mic/tests`
- `cd pi5mic && uv run --extra dev pytest -q tests -c pyproject.toml`
- result: `60 passed`

Raspberry Pi validation status:

- package-level validation passed locally
- Raspberry Pi follow-up is still required for the new auto-approval flow:
  - choose `Profile: openclaw` in `pi5mic setup`
  - confirm the wizard auto-detects the OpenClaw settings
  - approve the local pairing request if prompted
  - rerun `uv run pi5mic doctor`
  - rerun `uv run pi5mic run --once`

### pi5mic Gemini Default Dependency And OpenClaw Doctor Crash Fix

Summary:

- reviewed the latest Raspberry Pi validation report:
  - standalone Whisper passed
  - standalone Gemini passed
  - OpenClaw Whisper passed
  - OpenClaw Gemini failed in `mic-tool -> doctor`
- identified the direct root cause of the OpenClaw Gemini doctor crash:
  - `doctor` used `importlib.util.find_spec("google.genai")`
  - on environments where the parent `google` package is missing, that call can
    raise `ModuleNotFoundError` instead of returning `None`
  - because that exception was not caught, `doctor` crashed instead of showing a
    normal configuration failure
- fixed the Gemini doctor path so missing SDK discovery now fails gracefully
- changed package installation behavior so Gemini support is now installed by
  default:
  - `pi5mic` now depends on `google-genai` directly
  - the NinjaClawBot root workspace install now also lists `google-genai`
    explicitly
  - users no longer need `--extra gemini` for the normal workspace path
- updated the docs so the current operator flow is now:
  - `uv sync --extra dev`
  - build/register `whisper.cpp` if using local STT
  - export `GEMINI_API_KEY` or `GOOGLE_API_KEY` if using Gemini
  - run `pi5mic setup`, `doctor`, and `run --once`
- expanded the installation guide section `9.5` into a clearer step-by-step
  `pi5mic` path for running inside the NinjaClawBot project

Files changed:

- [pi5mic/src/pi5mic/cli/doctor.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/cli/doctor.py)
- [pi5mic/pyproject.toml](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/pyproject.toml)
- [pyproject.toml](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pyproject.toml)
- [pi5mic/tests/test_doctor.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/tests/test_doctor.py)
- [pi5mic/README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/README.md)
- [InstallationGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/InstallationGuide.md)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [backup/DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

Why:

- the latest Raspberry Pi result showed that the main remaining gap was no
  longer STT correctness but packaging and operator experience
- Gemini is part of the intended supported voice path now, so making it install
  by default removes an unnecessary setup branch and aligns the docs with the
  real recommended workflow

Validation:

- `uv lock`
- `cd pi5mic && uv run --extra dev python -m compileall src tests`
- `cd pi5mic && uv run --extra dev ruff check src tests`
- `cd pi5mic && uv run --extra dev ruff format --check src tests`
- `cd pi5mic && uv run --extra dev pytest -q tests -c pyproject.toml`
- `uv run --extra dev python -m compileall src ninjaclawbot/src pi5mic/src`
- `uv run --extra dev ruff check .`
- `git diff --check`

Raspberry Pi validation status:

- previous field result already confirmed:
  - standalone Whisper passed
  - standalone Gemini passed
  - OpenClaw Whisper passed
- OpenClaw Gemini must be retested after this dependency and doctor-fix update

## 2026-03-19

### pi5mic Raspberry Pi Whisper Hardening And Gemini Doctor Audit

Summary:

- audited two new Raspberry Pi field issues reported during real-device testing:
  - the board powering off or rebooting after local Whisper capture
  - Gemini doctor failure caused by missing environment credentials
- identified the Gemini root cause:
  - the backend and `doctor` path were correctly requiring `GOOGLE_API_KEY` or
    `GEMINI_API_KEY`
  - but the diagnostic was too terse for non-developer setup and the runtime
    config values for timeout/retry were not actually wired into the backend
- identified the Whisper-side robustness gaps:
  - the preview path still allowed relatively heavy local transcription defaults
    on Raspberry Pi
  - there was no Pi-specific health signal in `doctor` to help distinguish code
    failures from undervoltage, thermal throttling, or low-memory conditions
- improved the local Whisper runtime:
  - added a safer automatic thread limit on Raspberry Pi when threads are left
    unset
  - normalized recorded WAV clips to `16000` Hz mono before calling
    `whisper.cpp`
  - shortened the default clip length to reduce fixed-cost preview runs
  - surfaced the effective Whisper runtime in `status` and `doctor`
- improved the Gemini runtime and diagnostics:
  - switched the fallback model default to `gemini-2.5-flash`
  - added explicit environment-key resolution with clearer operator help
  - wired `timeout_seconds` and `retry_limit` into the Google Gen AI client
  - made `doctor` report the detected credential source and missing-package case
- added Raspberry Pi health diagnostics:
  - `doctor` now reports Raspberry Pi model, temperature, and throttled history
    when available through `vcgencmd`
  - `doctor` now warns when Whisper runs are being attempted under low-memory
    conditions
- expanded regression coverage for:
  - Whisper thread recommendation
  - WAV normalization
  - Gemini env-key selection and HTTP options
  - Raspberry Pi throttling warnings
- updated the docs so non-programmer operators now get step-by-step guidance for:
  - Gemini API key setup
  - Raspberry Pi shutdown / reboot troubleshooting
  - the new safer Whisper defaults

Files changed:

- [pi5mic/src/pi5mic/core/system_info.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/core/system_info.py)
- [pi5mic/src/pi5mic/stt/whisper_cpp.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/stt/whisper_cpp.py)
- [pi5mic/src/pi5mic/stt/gemini.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/stt/gemini.py)
- [pi5mic/src/pi5mic/cli/_common.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/cli/_common.py)
- [pi5mic/src/pi5mic/cli/setup_cmd.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/cli/setup_cmd.py)
- [pi5mic/src/pi5mic/cli/doctor.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/cli/doctor.py)
- [pi5mic/src/pi5mic/cli/status.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/cli/status.py)
- [pi5mic/src/pi5mic/config/config_manager.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/config/config_manager.py)
- [pi5mic/tests/test_cli.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/tests/test_cli.py)
- [pi5mic/tests/test_doctor.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/tests/test_doctor.py)
- [pi5mic/tests/test_mic_tool_setup.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/tests/test_mic_tool_setup.py)
- [pi5mic/tests/test_stt_gemini.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/tests/test_stt_gemini.py)
- [pi5mic/tests/test_stt_whisper_cpp.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/tests/test_stt_whisper_cpp.py)
- [pi5mic/tests/test_system_info.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/tests/test_system_info.py)
- [pi5mic/README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/README.md)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [backup/DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

Why:

- the Gemini credential failure was a real setup issue, but it needed a more
  user-friendly explanation and complete runtime wiring
- the Raspberry Pi shutdown report strongly suggested that the preview path
  needed safer local Whisper defaults plus better hardware diagnostics instead
  of treating every failure as a pure Python bug

Validation:

- `cd pi5mic && uv run --extra dev python -m compileall src tests`
- `cd pi5mic && uv run --extra dev ruff check src tests`
- `cd pi5mic && uv run --extra dev ruff format --check src tests`
- `cd pi5mic && uv run --extra dev pytest -q tests -c pyproject.toml`

Raspberry Pi validation status:

- code-side hardening complete
- real Raspberry Pi retest still required:
  - rerun `pi5mic setup`
  - rerun `pi5mic doctor`
  - rerun `pi5mic status`
  - rerun `pi5mic run --once`
  - if the board still powers off, capture `vcgencmd get_throttled` and
    `vcgencmd measure_temp`

### pi5mic Raspberry Pi PortAudio Crash Fix And Standalone README Rewrite

Summary:

- audited the Raspberry Pi traceback from `pi5mic setup` and `mic-tool`
- identified the first root cause:
  - `sounddevice` was installed
  - but importing it raised `OSError: PortAudio library not found`
  - `pi5mic` only converted `ImportError` into friendly user-facing errors, so
    the Pi surfaced a raw traceback instead of a setup hint
- identified the second root cause:
  - `status` assumed `sounddevice.default.device` was always a tuple/list, but
    on the tested environment it was a `sounddevice._InputOutputPair`
  - `pi5mic` also kept the old `16000` Hz default even when the selected ALSA
    microphone only supported its hardware default sample rate, so record/run
    failed later with `Invalid sample rate [PaErrorCode -9997]`
- fixed both audio import paths:
  - microphone discovery now translates missing PortAudio into `DeviceError`
  - recording now translates missing PortAudio into `RecordingError`
- fixed the default-device parsing path so `status` no longer crashes on
  `_InputOutputPair`
- added input-setting validation and fallback behavior:
  - `setup` now recommends the selected microphone's default sample rate
  - `doctor` now validates input stream settings and can pass with warnings
  - recording falls back to the device default sample rate when the configured
    rate is unsupported but a safe default is available
- added regression tests for:
  - missing PortAudio during device discovery
  - missing PortAudio during recording setup
  - `mic-tool -> setup` warning behavior so the interactive path no longer
    crashes on this setup issue
  - `_InputOutputPair` default-device handling
  - invalid-sample-rate fallback and doctor warnings
- rewrote the `pi5mic` README into a clearer beginner-friendly standalone
  setup and testing guide with:
  - step-by-step installation
  - `mic-tool` explanation and usage
  - direct command-line explanation and usage
  - explicit PortAudio troubleshooting
  - explicit invalid-sample-rate troubleshooting

Files changed:

- [pi5mic/src/pi5mic/core/audio_backend.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/core/audio_backend.py)
- [pi5mic/src/pi5mic/core/devices.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/core/devices.py)
- [pi5mic/src/pi5mic/core/recorder.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/core/recorder.py)
- [pi5mic/tests/test_devices.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/tests/test_devices.py)
- [pi5mic/tests/test_recorder.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/tests/test_recorder.py)
- [pi5mic/tests/test_mic_tool_setup.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/tests/test_mic_tool_setup.py)
- [pi5mic/README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [backup/DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

Why:

- on Raspberry Pi, the most common first-run problem is not a missing Python
  package but a missing system PortAudio library
- the earlier implementation hid this case from our tests and therefore failed
  the non-developer operator experience requirement

Validation:

- `cd pi5mic && uv run --extra dev python -m compileall src tests`
- `cd pi5mic && uv run --extra dev ruff check src tests`
- `cd pi5mic && uv run --extra dev ruff format --check src tests`
- `cd pi5mic && uv run --extra dev pytest -q tests -c pyproject.toml`
- `git diff --check`

Raspberry Pi validation status:

- code-side crash fix implemented
- real Raspberry Pi retest still required:
  - rerun `pi5mic setup`
  - rerun `pi5mic mic-tool`
  - rerun `pi5mic doctor`
  - verify the new error message disappears once PortAudio is installed

### pi5mic Preview Implementation, OpenClaw Handoff, And Workspace Integration

Summary:

- implemented the first runnable `pi5mic` preview package in the workspace
- added the default `whisper.cpp` STT backend and kept Gemini as the optional
  alternative backend
- added user-facing operator flows:
  - `pi5mic setup`
  - `pi5mic install whispercpp`
  - `pi5mic doctor`
  - `pi5mic status`
  - `pi5mic run`
  - `pi5mic mic-tool`
- added an OpenClaw-integrated preview path that:
  - records locally
  - transcribes locally
  - submits the transcript through the documented `openclaw agent --json` CLI
  - uses a dedicated session key by default
  - keeps delivery local-only unless an explicit channel target is configured
- added a plugin-owned gateway method:
  - `ninjaclawbot.presence.set`
  - this lets `pi5mic` request `idle`, `thinking`, and `listening` through the
    existing persistent bridge instead of starting a competing long-running
    robot runtime
- integrated `pi5mic` into the root workspace installer and root Python test
  paths
- updated project docs to describe the real current voice-input preview rather
  than the earlier scaffold-only state

Files changed:

- [pi5mic/README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/README.md)
- [pi5mic/src/pi5mic/__init__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/__init__.py)
- [pi5mic/src/pi5mic/__main__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/__main__.py)
- [pi5mic/src/pi5mic/cli](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/cli)
- [pi5mic/src/pi5mic/integration](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/integration)
- [pi5mic/src/pi5mic/transport](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/src/pi5mic/transport)
- [pi5mic/tests](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5mic/tests)
- [integrations/openclaw/ninjaclawbot-plugin/src/index.ts](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin/src/index.ts)
- [integrations/openclaw/ninjaclawbot-plugin/tests/index.test.ts](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin/tests/index.test.ts)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [InstallationGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/InstallationGuide.md)
- [MicDevelopment.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/MicDevelopment.md)
- [pyproject.toml](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pyproject.toml)

Why:

- the earlier implementation only covered the local scaffold and basic STT work,
  which was not enough to make the approved standalone/OpenClaw split truly
  usable
- the new preview path keeps the architecture safe by reusing the OpenClaw
  plugin bridge for robot presence while keeping the microphone process
  separate from direct robot-runtime ownership

Validation:

- `cd pi5mic && uv run --extra dev python -m compileall src tests`
- `cd pi5mic && uv run --extra dev ruff check src tests`
- `cd pi5mic && uv run --extra dev ruff format --check src tests`
- `cd pi5mic && uv run --extra dev pytest -q tests -c pyproject.toml`
- `cd integrations/openclaw/ninjaclawbot-plugin && npm run typecheck`
- `cd integrations/openclaw/ninjaclawbot-plugin && npm test`

Raspberry Pi validation status:

- still required for the new microphone path
- especially important for:
  - real USB microphone device selection
  - `whisper.cpp` runtime behavior on Pi 5
  - OpenClaw profile round-trip with local audio capture
  - long-run wake/listen behavior in future phases

### pi5mic Backend Lock And Guided Setup Planning Refinement

Summary:

- refined the `pi5mic` plan to lock `whisper.cpp` as the default local STT
  backend using the multilingual `base` model
- kept Gemini Flash as the optional cloud STT backend, with credentials coming
  from environment variables instead of `mic.json`
- expanded the plan so `pi5mic` now includes a user-friendly first-run
  operator workflow:
  - `setup`
  - `install whispercpp`
  - `doctor`
  - `run`
  - `status`
  - `mic-tool`
- made the integration recommendation more explicit:
  - standalone mode and OpenClaw-integrated mode should be visible user
    profiles
  - normal NinjaClawBot integration should go through the existing OpenClaw
    plugin and persistent bridge path, not a second direct long-running robot
    runtime
- added planning detail for:
  - `whisper-cli` detection and model install behavior
  - config keys for `whisper_cpp` and `gemini`
  - confirmation rules before writing config or changing integration settings
  - Raspberry Pi validation checks for backend switching and local model
    availability

Files changed:

- [MicDevelopment.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/MicDevelopment.md)
- [backup/DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

Why:

- the prior corrected plan was structurally sound, but it still described
  Gemini too centrally and did not yet spell out the first-run user experience
  clearly enough for a Raspberry Pi builder
- the repository already favors interactive-tool-first setup for hardware
  libraries, so the microphone plan needed to reflect the same operator style
  before implementation begins

Validation:

- targeted repository audit of current `pi5buzzer`, `pi5servo`,
  `ninjaclawbot`, and OpenClaw plugin patterns
- upstream documentation fact-check for `whisper.cpp`, Gemini SDK credential
  handling, and OpenClaw wizard/doctor workflow patterns
- markdown rewrite review

Raspberry Pi validation status:

- not applicable yet
- this change is planning and documentation only

### pi5mic Planning Audit And Fact-Checked MicDevelopment Rewrite

Summary:

- re-audited `MicDevelopment.md` against the current `ninjaclawbot` runtime,
  bridge, and OpenClaw plugin code
- verified the current upstream OpenClaw contracts that matter for microphone
  work:
  - gateway agent entry points
  - lifecycle hooks
  - plugin tool opt-in rules
  - Talk Mode
  - Voice Wake
  - Audio and Voice Notes
  - Telegram delivery behavior
- verified upstream vendor constraints for the proposed voice stack:
  - Gemini audio understanding and transcription guidance
  - Porcupine Raspberry Pi 5 support and AccessKey requirement
- rewrote `MicDevelopment.md` so the implementation plan is stricter and more
  robust around:
  - session isolation
  - explicit delivery targets
  - secret handling
  - audio retention
  - batch STT vs real-time assumptions
  - plugin-owned external presence control
- corrected stale repository assumptions in the plan documentation:
  - archived planning and log files live under `backup/`
  - presence support already exists in Python and bridge layers today

Files changed:

- [MicDevelopment.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/MicDevelopment.md)
- [backup/DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

Why:

- the earlier microphone plan was close in architecture, but it still left
  several high-risk assumptions under-specified, especially around how a local
  microphone process should talk to OpenClaw safely and how outbound Telegram
  mirroring should be controlled
- the revised plan now reflects the real current code boundaries and the real
  upstream contracts we would be building against

Validation:

- manual repository audit with Serena and targeted source review
- upstream documentation fact-check against primary sources
- markdown rewrite review

Raspberry Pi validation status:

- not applicable yet
- this change is planning and documentation only

## 2026-03-14

### Final Documentation Rewrite, Archive Move, And Repository Cleanup

Summary:

- rewrote the root documentation set so the final validated build is described
  in simpler, clearer language
- rewrote the installation guide around the real Raspberry Pi + OpenClaw build
  path with copy-paste steps, troubleshooting, alternatives, and quick links
- rewrote the development guide so future maintenance starts from the real
  current file layout, action surface, runtime model, and validation flow
- rewrote the root README as a high-level project entry point and added English,
  Japanese, and Traditional Chinese sections
- archived older planning and history documents into a new `backup/` folder for
  future reference
- removed tracked repository junk that should not ship to users:
  - `.DS_Store`
  - plugin `node_modules`

Why:

- the project had reached a stable validated build, but the documentation still
  reflected multiple development-era assumptions and was harder to follow than
  necessary for a new Raspberry Pi builder
- the repository also still contained tracked vendor and temporary files that
  were not part of the real product surface

Validation:

- `npm install`
- `npm run typecheck`
- `npm test`
- `uv run --extra dev python -m compileall .`
- `uv run --extra dev ruff check .`
- `uv run --extra dev ruff format --check .`
- `uv run pytest -q pi5buzzer/tests -c pi5buzzer/pyproject.toml`
- `uv run pytest -q pi5servo/tests -c pi5servo/pyproject.toml`
- `uv run pytest -q pi5disp/tests -c pi5disp/pyproject.toml`
- `uv run pytest -q pi5vl53l0x/tests -c pi5vl53l0x/pyproject.toml`
- `uv run pytest -q ninjaclawbot/tests -c ninjaclawbot/pyproject.toml`
- `git diff --check`

### Final Phase 2.5 Follow-up And Documentation Closeout

Summary:

- completed the last Phase 2.5 observability follow-up so
  `ninjaclawbot_diagnostics` now reports startup correctly for the validated
  hybrid OpenClaw deployment
- added explicit startup diagnostics fields:
  - `startup.trackingMode`
  - `startup.configured`
  - `startup.observedByService`
  - `startup.effectiveCompleted`
- updated the main project docs to treat the validated Raspberry Pi path as
  complete instead of still pending
- aligned the diagnostics instructions with the real deployment model:
  - plugin-managed persistent bridge and shutdown
  - `boot-md` plus workspace `BOOT.md` for startup
  - workspace `AGENTS.md`, skill enablement, and allowlist for reply behavior

Files changed:

- [integrations/openclaw/ninjaclawbot-plugin/src/runner.ts](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin/src/runner.ts)
- [integrations/openclaw/ninjaclawbot-plugin/tests/runner.test.ts](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin/tests/runner.test.ts)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)
- [InstallationGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/InstallationGuide.md)
- [EnhancementPlan.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/EnhancementPlan.md)

Why:

- Raspberry Pi validation already proved the real startup -> reply -> shutdown
  path worked, but the diagnostics output still under-reported startup because
  the validated deployment uses `boot-md` and workspace `BOOT.md` instead of
  always calling the Python `startup_sequence()` path directly
- the project documentation still needed one last pass to mark Stage 2 as
  complete and explain the hybrid startup model clearly

Validation:

- `npm run typecheck`
- `npm test`
- `uv run --extra dev python -m compileall src tests`
- `uv run --extra dev ruff check src tests`
- `uv run --extra dev ruff format --check src tests`
- `uv run --extra dev pytest -q tests -c pyproject.toml`
- `git diff --check`

Raspberry Pi validation status:

- completed
- validated by the user on the real Telegram/OpenClaw Raspberry Pi setup:
  - startup greeting
  - `ninjaclawbot_reply`
  - normal Telegram text reply
  - sleepy shutdown
  - healthy diagnostics output
  - deployment readiness reported as `ready`

### Reply And Diagnostics Usage Fix For Telegram/OpenClaw

Summary:

- corrected the OpenClaw-facing reply contract so `ninjaclawbot_reply` is now
  treated as the robot animation step before the normal visible chat reply,
  instead of being treated as the final user-facing answer by itself
- updated the plugin tool description and result guidance so the model is told
  to keep sending the normal Telegram text reply after the robot tool call
- updated the plugin skill and workspace `AGENTS.md` setup template to match
  that behavior
- documented the correct way to run `ninjaclawbot_diagnostics`, which is an
  OpenClaw tool invoked through the gateway, not a local `uv` CLI command
- updated the sanitized OpenClaw allowlist template so
  `ninjaclawbot_diagnostics` is included by default

Files changed:

- [integrations/openclaw/ninjaclawbot-plugin/src/index.ts](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin/src/index.ts)
- [integrations/openclaw/ninjaclawbot-plugin/tests/index.test.ts](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin/tests/index.test.ts)
- [integrations/openclaw/ninjaclawbot-plugin/skills/ninjaclawbot_control/SKILL.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin/skills/ninjaclawbot_control/SKILL.md)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)
- [InstallationGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/InstallationGuide.md)

Why:

- the previous guidance made it too easy for the model to stop after the robot
  tool call, which produced correct hardware reactions but silent Telegram
  replies
- users also needed a clear, correct invocation path for
  `ninjaclawbot_diagnostics`

Validation:

- `npm run typecheck`
- `npm test`
- `uv run --extra dev python -m compileall src tests`
- `uv run --extra dev ruff check src tests`
- `uv run --extra dev ruff format --check src tests`
- `uv run --extra dev pytest -q tests -c pyproject.toml`
- `git diff --check`

Raspberry Pi validation status:

- pending after this fix
- required next checks:
  - call `ninjaclawbot_diagnostics` through the OpenClaw gateway
  - verify Telegram now receives both:
    - robot expression
    - normal text reply
  - verify startup greeting and sleepy shutdown still work

### Phase 2.5: Diagnostics, Deployment Readiness, And Release Gate

Summary:

- implemented the first complete Phase 2.5 slice around operator-facing
  diagnostics, deployment readiness inspection, and release hygiene
- added a new OpenClaw tool, `ninjaclawbot_diagnostics`, that merges:
  - persistent bridge telemetry
  - Python service status
  - deployment readiness hints
  - recovery suggestions
- added plugin-side deployment checks for the validated hybrid setup:
  - `boot-md`
  - workspace `BOOT.md`
  - workspace `AGENTS.md`
  - `ninjaclawbot_control` skill
  - agent tool allowlist
  - minimal plugin config usage
- added a repository hygiene test so tracked Python cache artifacts are caught
  automatically before another Raspberry Pi update
- removed the remaining tracked `__pycache__` and `.pyc` files still present
  across the repo

Files changed:

- [integrations/openclaw/ninjaclawbot-plugin/src/index.ts](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin/src/index.ts)
- [integrations/openclaw/ninjaclawbot-plugin/src/runner.ts](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin/src/runner.ts)
- [integrations/openclaw/ninjaclawbot-plugin/tests/index.test.ts](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin/tests/index.test.ts)
- [integrations/openclaw/ninjaclawbot-plugin/tests/runner.test.ts](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin/tests/runner.test.ts)
- [ninjaclawbot/tests/test_repo_hygiene.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_repo_hygiene.py)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)
- [InstallationGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/InstallationGuide.md)
- [EnhancementPlan.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/EnhancementPlan.md)

Why:

- the bridge and service already tracked useful internal status, but operators
  still had no single place to inspect what was wrong
- recent startup, reply, config, and `uvCommand` issues required too much
  manual log reading and config inspection
- the release gate needed to reflect the real validated hybrid OpenClaw setup,
  not just the intended one

Validation:

- `npm run typecheck`
- `npm test`
- `uv run --extra dev python -m compileall src tests`
- `uv run --extra dev ruff check src tests`
- `uv run --extra dev ruff format --check src tests`
- `uv run --extra dev pytest -q tests -c pyproject.toml`
- `git diff --check`

Raspberry Pi validation status:

- pending after this Phase 2.5 implementation
- required next checks:
  - run `ninjaclawbot_diagnostics` and confirm bridge and deployment state
  - confirm startup greeting, reply expression, and sleepy shutdown still work
  - confirm diagnostics report warning or misconfigured states when one
    prerequisite is intentionally broken
  - confirm `git pull` no longer fails on tracked cache artifacts in older Pi
    working directories

### Display Config Compatibility Fix For `expression-tool`

Summary:

- audited the mismatch reported after Raspberry Pi reinstall where
  `uv run pi5disp display-tool` looked correct but
  `uv run ninjaclawbot expression-tool` rendered facial expressions wrongly
- confirmed the root cause was a config-path split:
  - standalone `pi5disp` tools used the package-local `display.json`
  - integrated `ninjaclawbot` tools used the root project `display.json`
- updated the integrated display adapter to prefer the root config but fall
  back automatically to the standalone `pi5disp` config when the root file does
  not exist yet
- updated the installation guide so the quick local test now explicitly includes
  `expression-tool` and `movement-tool`

Files changed:

- [ninjaclawbot/src/ninjaclawbot/adapters.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/adapters.py)
- [ninjaclawbot/tests/test_adapters.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_adapters.py)
- [InstallationGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/InstallationGuide.md)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

Why:

- the installation flow legitimately encourages users to validate the screen
  with `pi5disp display-tool` before using `ninjaclawbot`
- the integrated layer therefore had to tolerate that setup order instead of
  assuming the root `display.json` already existed

Validation:

- `uv run --extra dev python -m compileall src tests`
- `uv run --extra dev ruff check src tests`
- `uv run --extra dev ruff format --check src tests`
- `uv run --extra dev pytest -q tests -c pyproject.toml`

Raspberry Pi validation status:

- pending after this fix
- required manual check:
  - `uv run pi5disp display-tool`
  - `uv run ninjaclawbot health-check`
  - `uv run ninjaclawbot expression-tool`

### Phase 2.4 Hardening: Lifecycle Dedupe, Root Display Config, And Repository Hygiene

Summary:

- implemented the first hardening slice of Phase 2.4 in the active
  `ninjaclawbot` and OpenClaw bridge code
- added service-core suppression and dedupe rules for repeated low-priority
  lifecycle transitions
- made the integrated display adapter load the root-level `display.json`
  instead of silently using the package-local `pi5disp` default config
- added initial plugin-side bridge telemetry so the code can distinguish
  `healthy`, `degraded`, and `disabled` bridge states for future diagnostics
- removed tracked Python cache artifacts from version control and added a root
  `.gitignore` so Raspberry Pi updates no longer break on generated `__pycache__`
  files

Files changed:

- [ninjaclawbot/src/ninjaclawbot/openclaw/service.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/openclaw/service.py)
- [ninjaclawbot/src/ninjaclawbot/adapters.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/adapters.py)
- [ninjaclawbot/tests/test_openclaw_bridge.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_openclaw_bridge.py)
- [ninjaclawbot/tests/test_adapters.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_adapters.py)
- [integrations/openclaw/ninjaclawbot-plugin/src/runner.ts](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin/src/runner.ts)
- [integrations/openclaw/ninjaclawbot-plugin/tests/runner.test.ts](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin/tests/runner.test.ts)
- [.gitignore](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/.gitignore)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)
- [InstallationGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/InstallationGuide.md)
- [EnhancementPlan.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/EnhancementPlan.md)

Why:

- the happy-path lifecycle already worked on Raspberry Pi, but the service core
  still treated every lifecycle request too literally
- repeated `thinking` and stale fallback `idle` updates needed explicit
  suppression rules before more stress testing
- `ninjaclawbot` had to respect the same root-level display configuration file
  the installation guide tells users to create
- tracked cache files had already caused a real `git pull` failure on Raspberry
  Pi and needed to be removed from the repository itself

Validation:

- `uv run --extra dev python -m compileall src tests`
- `uv run --extra dev ruff check src tests`
- `uv run --extra dev ruff format --check src tests`
- `uv run --extra dev pytest -q tests -c pyproject.toml`
- `npm run typecheck`
- `npm test`

Raspberry Pi validation status:

- not yet rerun after this Phase 2.4 hardening slice
- required next checks:
  - repeated-message dedupe under Telegram/OpenClaw
  - duplicate startup-source suppression
  - root-level `display.json` confirmation from the integrated runtime
  - gateway restart and recovery behavior

### Installation Guide Simplification With Interactive Tools And Appendix

Summary:

- refined the Raspberry Pi installation guide again so the main flow is shorter
  and easier to follow
- changed the main setup path to prefer the guided tools where they are the
  most reliable first-run option:
  - `pi5servo servo-tool`
  - `pi5buzzer buzzer-tool`
  - `pi5disp init` plus `display-tool`
  - `pi5vl53l0x sensor-tool`
- added short purpose explanations to every main step
- moved lower-priority fallback commands out of the main path and into an
  appendix
- added appendix sections for:
  - troubleshooting methods
  - alternative commands
  - quick links from the main steps
- aligned the project-level docs so they now describe the installation guide as
  the interactive-tool-first setup path

Files changed:

- [InstallationGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/InstallationGuide.md)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

Why:

- the previous rewrite was correct, but the main path still exposed too many
  one-off commands before the user reached the guided tools
- the user explicitly asked for a simpler and more reliable guide that leans on
  the interactive utilities and keeps fallback material out of the main flow

Validation:

- documentation rewrite only
- reviewed against the current standalone library READMEs
- reviewed against the validated `openclaw.json` shared by the user
- `git diff --check`

Raspberry Pi validation status:

- the underlying startup -> reply -> power-off path was already validated by
  the user before this documentation refinement
- the rewritten guide now presents that validated path more directly

## 2026-03-13

### Installation Guide Rewrite For The Validated OpenClaw Build

Summary:

- rewrote the entire Raspberry Pi installation guide in plain language instead
  of continuing to patch older sections
- aligned the guide with the final validated OpenClaw configuration shape used
  on Raspberry Pi
- replaced personal values in the example configuration with placeholders
- documented the validated OpenClaw workspace files:
  - `BOOT.md` for startup greeting
  - `AGENTS.md` for reply-tool behavior
- replaced the old validation section with a simpler copy-paste flow for:
  - startup greeting
  - Telegram reply expressions
  - sleepy shutdown and display power-down
- added troubleshooting steps for:
  - `uv` path issues
  - local log access when `openclaw logs --follow` is blocked by pairing
  - `git pull` failures caused by tracked `__pycache__` files

Files changed:

- [InstallationGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/InstallationGuide.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

Why:

- the project now has a validated Raspberry Pi + OpenClaw path, but the old
  installation guide had grown into a mixture of historical workarounds and
  partially outdated instructions
- the user asked for a from-scratch guide that non-developers can follow
  without guessing which pieces are still current
- the attached final `openclaw.json` showed the stable configuration shape that
  should now be treated as the reference

Validation:

- documentation rewrite only
- manual source review against the validated `openclaw.json`
- official OpenClaw docs cross-check for:
  - internal hooks / `boot-md`
  - agent workspace files
  - skills and plugin configuration

Raspberry Pi validation status:

- already validated externally by the user for the final startup -> reply ->
  power-off path
- the rewritten guide now reflects that validated flow directly

### OpenClaw Lifecycle Hook Registration Fix

Summary:

- corrected the OpenClaw plugin lifecycle registration path so the plugin now
  prefers the plugin hook API instead of relying only on `api.on(...)`
- kept the `api.on(...)` path as a compatibility fallback for older OpenClaw
  environments
- updated the plugin tests to verify explicit lifecycle hook registration
- updated the Raspberry Pi validation steps so they now require checking
  `openclaw hooks list --verbose` and starting a fresh Telegram session after
  plugin or skill changes

Files changed:

- [integrations/openclaw/ninjaclawbot-plugin/src/index.ts](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin/src/index.ts)
- [integrations/openclaw/ninjaclawbot-plugin/tests/index.test.ts](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin/tests/index.test.ts)
- [InstallationGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/InstallationGuide.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

Why:

- Raspberry Pi verification showed that the bridge and tools were healthy, but
  `openclaw hooks list --verbose` exposed that no NinjaClawBot lifecycle hooks
  were actually registered
- without registered lifecycle hooks, the gateway cannot trigger startup
  greeting, auto-thinking, or sleepy shutdown even when the bridge is alive
- reply expressions also needed clearer operator validation because OpenClaw
  session prompts can lag behind plugin and skill changes until a fresh chat is
  started

Validation:

- `cd /Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code library/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin`
- `npm run typecheck`
- `npm test`

Raspberry Pi validation status:

- still required after syncing this fix to the Pi
- next validation should confirm that `openclaw hooks list --verbose` shows the
  NinjaClawBot lifecycle hooks before testing startup greeting and sleepy
  shutdown
- Telegram reply validation should be run from a fresh `/new` session

### Phase 2.2 And 2.3 Initial Always On Lifecycle Pass

Summary:

- added explicit persistent presence support for `idle`, `thinking`, and
  `listening`
- added an explicit `shutdown_sequence` action and runtime path for
  `sleepy -> display power-down -> cleanup`
- added display adapter power-down helpers so shutdown can use `sleep()`,
  `off()`, and then `close()` defensively
- extended the persistent Python bridge service with:
  - current presence mode reporting
  - last lifecycle event reporting
  - startup sequence handling
  - presence-mode requests
  - shutdown-sequence requests
- registered OpenClaw lifecycle hooks for:
  - `gateway_start`
  - `message_received`
  - `agent_end`
  - `gateway_stop`
- added bounded Always On config flags for startup greeting, auto-thinking, and
  shutdown sequencing
- updated the OpenClaw skill guidance so the agent does not spam `set_idle`
  when the lifecycle hooks are active
- updated the install and developer docs so Raspberry Pi validation now covers
  startup greeting, automatic thinking, answer-to-idle, and sleepy shutdown

Files changed:

- [ninjaclawbot/src/ninjaclawbot/actions.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/actions.py)
- [ninjaclawbot/src/ninjaclawbot/presence.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/presence.py)
- [ninjaclawbot/src/ninjaclawbot/adapters.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/adapters.py)
- [ninjaclawbot/src/ninjaclawbot/runtime.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/runtime.py)
- [ninjaclawbot/src/ninjaclawbot/executor.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/executor.py)
- [ninjaclawbot/src/ninjaclawbot/expressions/player.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/expressions/player.py)
- [ninjaclawbot/src/ninjaclawbot/openclaw/service.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/openclaw/service.py)
- [ninjaclawbot/src/ninjaclawbot/openclaw/bridge.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/openclaw/bridge.py)
- [ninjaclawbot/tests/test_actions.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_actions.py)
- [ninjaclawbot/tests/test_executor.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_executor.py)
- [ninjaclawbot/tests/test_expressions.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_expressions.py)
- [ninjaclawbot/tests/test_runtime.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_runtime.py)
- [ninjaclawbot/tests/test_openclaw_bridge.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_openclaw_bridge.py)
- [integrations/openclaw/ninjaclawbot-plugin/src/runner.ts](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin/src/runner.ts)
- [integrations/openclaw/ninjaclawbot-plugin/src/index.ts](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin/src/index.ts)
- [integrations/openclaw/ninjaclawbot-plugin/openclaw.plugin.json](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin/openclaw.plugin.json)
- [integrations/openclaw/ninjaclawbot-plugin/tests/index.test.ts](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin/tests/index.test.ts)
- [integrations/openclaw/ninjaclawbot-plugin/tests/runner.test.ts](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin/tests/runner.test.ts)
- [integrations/openclaw/ninjaclawbot-plugin/skills/ninjaclawbot_control/SKILL.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin/skills/ninjaclawbot_control/SKILL.md)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [InstallationGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/InstallationGuide.md)
- [EnhancementPlan.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/EnhancementPlan.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

Why:

- Raspberry Pi testing showed that the persistent bridge was warm, but startup
  greeting, auto-thinking, and sleepy shutdown were still missing because only
  tool calls had been wired to the runtime
- the first Telegram message woke the robot correctly because explicit reply
  tools already worked, but gateway start and stop had no lifecycle-driven
  robot behavior
- this pass closes that gap while preserving the plugin-managed bridge now and
  a future standalone service model later

Lint and test results:

- `cd /Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code library/NinjaClawbot/ninjaclawbot`
- `uv run --extra dev python -m compileall src tests`
- `uv run --extra dev ruff check src tests`
- `uv run --extra dev ruff format --check src tests`
- `uv run --extra dev pytest -q tests -c pyproject.toml` -> `60 passed`
- `cd /Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code library/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin`
- `npm run typecheck`
- `npm test` -> `7 passed`

Raspberry Pi validation status:

- not run yet after this code pass
- the installation guide now includes the required Telegram-backed validation
  flow
- next validation should confirm:
  - startup greeting then persistent idle
  - persistent thinking on user message receipt
  - explicit reply emotion then idle
  - sleepy shutdown then display power-down
  - safe rollback by disabling `enableAlwaysOn` if needed

### Phase 2.1 Plugin-Managed Persistent Bridge Foundation

Summary:

- added a reusable `ninjaclawbot.openclaw` service core that keeps one
  `ActionExecutor` and `NinjaClawbotRuntime` alive across multiple requests
- added a hidden `ninjaclawbot openclaw-serve` stdio bridge for a long-lived
  plugin-managed Python process
- kept the existing hidden `openclaw-action` one-shot bridge for compatibility
  and fallback
- refactored the OpenClaw plugin runner so it prefers the persistent bridge,
  reuses it across tool calls, and degrades safely to the one-shot path if the
  bridge fails to start or exits unexpectedly
- registered an OpenClaw plugin background service that starts and stops the
  persistent bridge with the gateway lifecycle
- extended the plugin manifest config schema with persistent bridge timeout and
  enable/disable settings
- added regression coverage for the persistent bridge protocol, service-core
  reuse, CLI delegation, and plugin runner command building
- updated the root project documentation so the OpenClaw architecture and setup
  guides now describe the persistent bridge plus one-shot fallback model

Files changed:

- [ninjaclawbot/src/ninjaclawbot/__main__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/__main__.py)
- [ninjaclawbot/src/ninjaclawbot/openclaw/__init__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/openclaw/__init__.py)
- [ninjaclawbot/src/ninjaclawbot/openclaw/service.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/openclaw/service.py)
- [ninjaclawbot/src/ninjaclawbot/openclaw/bridge.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/openclaw/bridge.py)
- [ninjaclawbot/tests/test_cli_tools.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_cli_tools.py)
- [ninjaclawbot/tests/test_openclaw_bridge.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_openclaw_bridge.py)
- [integrations/openclaw/ninjaclawbot-plugin/openclaw.plugin.json](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin/openclaw.plugin.json)
- [integrations/openclaw/ninjaclawbot-plugin/src/index.ts](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin/src/index.ts)
- [integrations/openclaw/ninjaclawbot-plugin/src/runner.ts](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin/src/runner.ts)
- [integrations/openclaw/ninjaclawbot-plugin/tests/runner.test.ts](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin/tests/runner.test.ts)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [InstallationGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/InstallationGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

Why:

- the previous OpenClaw path spawned a fresh `uv run ninjaclawbot ...` process
  for every tool call and closed the runtime after each command
- that model could not support later lifecycle-aware presence features such as
  persistent idle, startup greeting, or shutdown cleanup
- Phase 2.1 establishes the persistent transport and runtime ownership layer
  first, while keeping a safe fallback path and preserving flexibility for a
  future standalone daemon mode

Lint and test results:

- `cd integrations/openclaw/ninjaclawbot-plugin`
- `npm run typecheck`
- `npm test` -> `5 passed`
- `cd /Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code library/NinjaClawbot/ninjaclawbot`
- `uv run --extra dev python -m compileall src tests`
- `uv run --extra dev ruff check src tests`
- `uv run --extra dev ruff format --check src tests`
- `uv run --extra dev pytest -q tests -c pyproject.toml` -> `52 passed`
- root CLI smoke:
  - `uv run ninjaclawbot --help`

Raspberry Pi validation status:

- not run yet
- still required before depending on this bridge for real hardware sessions
- next Pi checks should confirm the plugin starts one warm bridge on gateway
  startup, repeated OpenClaw calls reuse it, and fallback still works if the
  bridge is disabled or killed
- no Always On lifecycle hooks were added yet in this phase, so startup
  greeting, thinking presence, and shutdown reaction still remain for later
  phases

## 2026-03-12

### OpenClaw Installation Guide Correction

Summary:

- corrected the OpenClaw setup section in `InstallationGuide.md`
- replaced the direct OpenClaw install commands with a pointer to the dedicated
  `NinjaClawAgent` installation guide
- removed the misleading end-user step that told users to `cd` into the local
  `integrations/openclaw/ninjaclawbot-plugin` folder
- rewrote the plugin setup instructions so users add the `ninjaclawbot` plugin
  by editing the OpenClaw configuration file directly
- added commands to find the true NinjaClawBot project root and plugin folder
  paths on Raspberry Pi
- added a safe copy-paste command that patches the existing
  `~/.openclaw/openclaw.json` file without removing the user's current OpenClaw
  settings
- added a full reference OpenClaw config template with placeholders instead of
  personal values
- aligned the root and package documentation so the normal user path now points
  to `InstallationGuide.md`
- corrected the OpenClaw allowlist examples so they refer to the real
  `ninjaclawbot_*` tool names instead of a single plugin id

### OpenClaw Plugin Metadata Alignment

Summary:

- aligned the local OpenClaw plugin npm package name with the plugin manifest id
- removed the metadata mismatch that caused the warning:
  `plugin id mismatch (manifest uses "ninjaclawbot", entry hints "openclaw-plugin")`
- updated the install guide so it no longer depends on stale OpenClaw CLI
  commands such as `openclaw config file`

Files changed:

- [integrations/openclaw/ninjaclawbot-plugin/package.json](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin/package.json)
- [integrations/openclaw/ninjaclawbot-plugin/package-lock.json](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/integrations/openclaw/ninjaclawbot-plugin/package-lock.json)
- [InstallationGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/InstallationGuide.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

Why:

- OpenClaw was loading the plugin, but it warned because the plugin package name
  suggested `openclaw-plugin` while the manifest id and config entry correctly
  used `ninjaclawbot`
- the install guide also included CLI examples that were not reliable on the
  user's installed OpenClaw build

Validation:

- `cd integrations/openclaw/ninjaclawbot-plugin`
- `npm install`
- `npm run typecheck`
- `npm test` -> `3 passed`
- root CLI smoke:
  - `uv run ninjaclawbot --help`
  - `uv run ninjaclawbot list-capabilities`

Files changed:

- [InstallationGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/InstallationGuide.md)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [ninjaclawbot/README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

Why:

- the previous guide mixed developer plugin-validation steps with the normal
  Raspberry Pi install path
- that caused users following the OpenClaw setup flow from a separate repo to
  hit a broken local `cd integrations/openclaw/ninjaclawbot-plugin` step
- the corrected user flow is to install OpenClaw from the dedicated
  `NinjaClawAgent` guide, then register the NinjaClawBot plugin in the OpenClaw
  config file with the local plugin path and project root

Validation:

- documentation consistency review completed
- command-name smoke checks remain unchanged because this was a docs-only update
- no Python or hardware behavior changed in this step

### Expression Startup Synchronization Phase 1

Summary:

- optimized expression startup so the display is prewarmed before sound playback starts
- latched the first face frame to the panel before buzzer playback begins for face-based expressions
- rendered static text-only expressions before buzzer playback starts
- added regression coverage for startup ordering in the expression player

Files changed:

- [ninjaclawbot/src/ninjaclawbot/adapters.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/adapters.py)
- [ninjaclawbot/src/ninjaclawbot/expressions/player.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/expressions/player.py)
- [ninjaclawbot/tests/test_expressions.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_expressions.py)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

Why:

- the expression player previously started sound immediately while the display still lazily initialized on the first frame
- that caused sound-first playback, visible panel reset flicker, and a delayed face startup
- Phase 1 of the optimization plan was to move the display work ahead of sound without changing the asset model again

Lint and test results:

- `uv run python -m compileall conftest.py ninjaclawbot/src ninjaclawbot/tests`
- `uv run ruff check ninjaclawbot/src ninjaclawbot/tests`
- `uv run ruff format --check ninjaclawbot/src ninjaclawbot/tests`
- `uv run pytest -q ninjaclawbot/tests -c ninjaclawbot/pyproject.toml` -> `37 passed`

Raspberry Pi validation status:

- Raspberry Pi validation is still required
- expected pass conditions:
  - `uv run ninjaclawbot perform-expression idle` shows the first face before or with the first sound
  - `uv run ninjaclawbot perform-expression hello` shows text before or with the first sound
  - startup flicker is reduced compared with the previous build
- current limitation:
  - one-shot CLI execution still rebuilds the runtime for every process, so some panel reset cost can remain until a persistent runtime/session is introduced

### Built-In `perform-expression` Resolution Fix

Summary:

- fixed `ninjaclawbot perform-expression` so it can execute built-in expressions such as `idle` and `greeting`, not only saved JSON expression assets
- kept saved-expression precedence, so a saved asset still wins if it uses the same name as a built-in
- added regression coverage for built-in execution, saved-asset precedence, and invalid-expression failures

Files changed:

- [ninjaclawbot/src/ninjaclawbot/executor.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/executor.py)
- [ninjaclawbot/src/ninjaclawbot/__main__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/__main__.py)
- [ninjaclawbot/src/ninjaclawbot/cli/expression_tool.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/cli/expression_tool.py)
- [ninjaclawbot/tests/test_executor.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_executor.py)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

Why:

- the Stage 1 expression engine introduced built-in expressions, but `perform-expression` still assumed every name had to exist as a saved asset on disk
- that caused built-in names to fail even though the runtime and expression player could already execute them

Lint and test results:

- `uv run python -m compileall conftest.py ninjaclawbot/src ninjaclawbot/tests`
- `uv run ruff check ninjaclawbot/src ninjaclawbot/tests`
- `uv run ruff format --check ninjaclawbot/src ninjaclawbot/tests`
- `uv run pytest -q ninjaclawbot/tests -c ninjaclawbot/pyproject.toml` -> `35 passed`

Raspberry Pi validation status:

- Raspberry Pi validation is still required
- required pass conditions:
  - `uv run ninjaclawbot perform-expression idle` succeeds
  - `uv run ninjaclawbot perform-expression hello` still succeeds for a saved asset
  - if a saved asset intentionally uses a built-in name, the saved asset behavior takes precedence

### Stage 1 Expression-Tool Enhancement

Summary:

- added a first-class expression engine to `ninjaclawbot`, ported from the legacy NinjaRobotV5 facial-expression design
- created a built-in face and sound catalog that preserves legacy expression names and adds new vivid expressions such as `greeting`, `listening`, `thinking`, `curious`, `success`, `warning`, and `error`
- extended expression assets so they can reference built-ins, face chains, sound chains, and `idle_reset`
- added runtime-owned expression orchestration and idle handling instead of treating expressions as only text plus a tone
- upgraded `expression-tool` so it can list built-ins, preview them live, create saved expressions on top of them, and control the idle expression directly

Files changed:

- [ninjaclawbot/src/ninjaclawbot/assets.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/assets.py)
- [ninjaclawbot/src/ninjaclawbot/adapters.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/adapters.py)
- [ninjaclawbot/src/ninjaclawbot/runtime.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/runtime.py)
- [ninjaclawbot/src/ninjaclawbot/executor.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/executor.py)
- [ninjaclawbot/src/ninjaclawbot/cli/expression_tool.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/cli/expression_tool.py)
- [ninjaclawbot/src/ninjaclawbot/expressions/__init__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/expressions/__init__.py)
- [ninjaclawbot/src/ninjaclawbot/expressions/catalog.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/expressions/catalog.py)
- [ninjaclawbot/src/ninjaclawbot/expressions/faces.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/expressions/faces.py)
- [ninjaclawbot/src/ninjaclawbot/expressions/player.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/expressions/player.py)
- [ninjaclawbot/src/ninjaclawbot/expressions/sounds.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/src/ninjaclawbot/expressions/sounds.py)
- [ninjaclawbot/tests/test_assets.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_assets.py)
- [ninjaclawbot/tests/test_cli_tools.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_cli_tools.py)
- [ninjaclawbot/tests/test_executor.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_executor.py)
- [ninjaclawbot/tests/test_expressions.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_expressions.py)
- [ninjaclawbot/tests/test_runtime.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/ninjaclawbot/tests/test_runtime.py)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

Why:

- the current `ninjaclawbot` expression layer was too narrow and did not preserve the legacy NinjaRobotV5 facial-expression behavior
- Stage 1 of the enhancement plan required a real expression engine, not just richer JSON assets
- built-in preview, idle handling, and manual expression testing had to work from the root project environment before any OpenClaw-facing wrapper work starts

Lint and test results:

- Phase 1 gate:
  - `uv run python -m compileall conftest.py ninjaclawbot/src ninjaclawbot/tests`
  - `uv run ruff check ninjaclawbot/src ninjaclawbot/tests`
  - `uv run ruff format --check ninjaclawbot/src ninjaclawbot/tests`
  - `uv run pytest -q ninjaclawbot/tests -c ninjaclawbot/pyproject.toml` -> `27 passed`
- Phase 2 gate:
  - same commands after the face engine and sound helpers -> `30 passed`
- Phase 3 gate:
  - same commands after runtime orchestration and idle handling -> `31 passed`
- Phase 4 gate:
  - same commands after the `expression-tool` enhancement -> `32 passed`

Raspberry Pi validation status:

- manual Raspberry Pi validation is still required for Stage 1 expression behavior
- required pass conditions:
  - `uv run ninjaclawbot expression-tool` can list and preview built-ins such as `idle`, `greeting`, `happy`, `thinking`, and `confusing`
  - `7. Set idle expression` starts the waiting face and `8. Stop active expression` stops it cleanly
  - saved expressions created from built-ins run correctly through `uv run ninjaclawbot perform-expression <name>`
  - the animated face style remains visually aligned with the legacy NinjaRobotV5 design while showing more distinct emotions

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
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

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
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

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
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

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
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

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
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

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
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

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

- [developmentPlan.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/developmentPlan.md)
- [pi5servo/README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo/README.md)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

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
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

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
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

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
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

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
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

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
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

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
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

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
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/backup/DevelopmentLog.md)

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

### 2026-03-12 OpenClaw Stage 2 Reply Policy, Plugin Wrapper, And Skill Wrapper

Summary:

- added the OpenClaw-facing Stage 2 control surface on top of `ninjaclawbot`
- introduced typed Python actions for `perform_reply`, `list_capabilities`, `set_idle`, and `stop_expression`
- added a new `expressions/policy.py` module so OpenClaw reply states map to the correct built-in face and sound behavior instead of constructing expression chains manually
- added the machine-facing `openclaw-action` bridge command for plugin use
- created the official OpenClaw plugin package under `integrations/openclaw/ninjaclawbot-plugin`
- created the `ninjaclawbot_control` OpenClaw skill so the agent is explicitly taught to keep `idle` while waiting and to use the correct reply states for greeting, uncertainty, success, warning, and error cases

Files changed:

- `ninjaclawbot/src/ninjaclawbot/actions.py`
- `ninjaclawbot/src/ninjaclawbot/executor.py`
- `ninjaclawbot/src/ninjaclawbot/__main__.py`
- `ninjaclawbot/src/ninjaclawbot/expressions/policy.py`
- `ninjaclawbot/tests/test_actions.py`
- `ninjaclawbot/tests/test_cli_tools.py`
- `ninjaclawbot/tests/test_executor.py`
- `ninjaclawbot/tests/test_policy.py`
- `integrations/openclaw/ninjaclawbot-plugin/openclaw.plugin.json`
- `integrations/openclaw/ninjaclawbot-plugin/package.json`
- `integrations/openclaw/ninjaclawbot-plugin/tsconfig.json`
- `integrations/openclaw/ninjaclawbot-plugin/src/index.ts`
- `integrations/openclaw/ninjaclawbot-plugin/src/runner.ts`
- `integrations/openclaw/ninjaclawbot-plugin/src/schemas.ts`
- `integrations/openclaw/ninjaclawbot-plugin/tests/runner.test.ts`
- `integrations/openclaw/ninjaclawbot-plugin/skills/ninjaclawbot_control/SKILL.md`
- `README.md`
- `ninjaclawbot/README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`

Why:

- Stage 1 made the expression engine and manual tools stable, but OpenClaw still needed an official execution path instead of shelling directly into raw driver commands
- OpenClaw’s official integration model is plugin tools with JSON-schema parameters plus plugin-shipped skills, so the wrapper needed to follow that model rather than invent a parallel interface
- a dedicated reply policy keeps emotion-selection rules centralized, testable, and consistent with the legacy NinjaRobotV5 face and sound design

Lint and test results:

- Python gate:
  - `uv run python -m compileall conftest.py ninjaclawbot/src ninjaclawbot/tests`
  - `uv run ruff check ninjaclawbot/src ninjaclawbot/tests`
  - `uv run ruff format --check ninjaclawbot/src ninjaclawbot/tests`
  - `uv run pytest -q ninjaclawbot/tests -c ninjaclawbot/pyproject.toml`
  - result: `47 passed`
- OpenClaw plugin gate:
  - `cd integrations/openclaw/ninjaclawbot-plugin`
  - `npm install`
  - `npm run typecheck`
  - `npm test`
  - result: `3 passed`

Raspberry Pi validation status:

- manual Raspberry Pi 5 validation is still required

Follow-up:

- from the project root, run `uv run ninjaclawbot list-capabilities`, `uv run ninjaclawbot perform-reply --reply-state greeting "Hello"`, and `uv run ninjaclawbot set-idle`
- in the plugin folder, confirm the Node toolchain is installed with `npm install`, `npm run typecheck`, and `npm test`
- enable the plugin in OpenClaw, allowlist `ninjaclawbot`, then validate `ninjaclawbot_health`, `ninjaclawbot_capabilities`, `ninjaclawbot_reply`, and `ninjaclawbot_set_idle` on the Raspberry Pi before trusting the agent for live robot control

### 2026-03-12 Installation Guide And Root README Documentation Refresh

Summary:

- created a new root-level `InstallationGuide.md` as the single source of truth for installing, wiring, calibrating, testing, and connecting the full NinjaClawBot project to OpenClaw on Raspberry Pi 5
- rewrote the root `README.md` into a shorter guidebook that explains what the project is, how the major parts fit together, how OpenClaw uses the project, and where to find the detailed documents
- updated the advanced docs so the new document hierarchy is clear

Files changed:

- `InstallationGuide.md`
- `README.md`
- `DevelopmentGuide.md`
- `DevelopmentLog.md`
- `ninjaclawbot/README.md`

Why:

- the project had grown large enough that installation, calibration, standalone driver usage, integrated `ninjaclawbot` usage, and OpenClaw setup needed one clear end-to-end document
- the root README had become too large to act as both overview and full setup manual at the same time
- users need one simple Raspberry Pi path from fresh install to OpenClaw robot control without searching across multiple files

Lint and test results:

- no code behavior changed
- command names and documented root workflows were checked against the current project CLI surface

Raspberry Pi validation status:

- not applicable for this documentation-only update

Follow-up:

- use `InstallationGuide.md` as the first document for new Raspberry Pi setups
- keep future install, calibration, or OpenClaw changes synchronized across `InstallationGuide.md`, `README.md`, and `DevelopmentGuide.md`

### 2026-03-20 pi5mic Always-On Voice Input First Build And Optional Project Integration

Summary:

- implemented the first working always-on `pi5mic` voice-input build with a manual
  privacy-first control surface
- added a dedicated `voiceinput-tool` to `pi5mic` for:
  - status
  - background start
  - background stop
  - foreground debugging
  - recent log inspection
- extended `pi5mic setup`, `doctor`, `status`, and `mic-tool` so users can
  configure and validate the optional wake-word listener without editing JSON
  by hand
- added a `voiceinput` install extra so the optional Porcupine dependency can be
  installed in one step from the NinjaClawBot root
- integrated optional voice-input awareness into `ninjaclawbot` and the OpenClaw
  plugin without auto-starting the microphone

Files changed:

- `pyproject.toml`
- `uv.lock`
- `MicDevelopment.md`
- `README.md`
- `InstallationGuide.md`
- `DevelopmentGuide.md`
- `backup/DevelopmentLog.md`
- `pi5mic/README.md`
- `pi5mic/src/pi5mic/__main__.py`
- `pi5mic/src/pi5mic/cli/__init__.py`
- `pi5mic/src/pi5mic/cli/mic_tool.py`
- `pi5mic/src/pi5mic/cli/setup_cmd.py`
- `pi5mic/src/pi5mic/cli/status.py`
- `pi5mic/src/pi5mic/cli/doctor.py`
- `pi5mic/src/pi5mic/cli/voiceinput_tool.py`
- `pi5mic/src/pi5mic/config/config_manager.py`
- `pi5mic/src/pi5mic/core/voiceinput.py`
- `pi5mic/src/pi5mic/transport/openclaw_cli.py`
- `pi5mic/tests/test_cli.py`
- `pi5mic/tests/test_config.py`
- `pi5mic/tests/test_doctor.py`
- `pi5mic/tests/test_mic_tool.py`
- `pi5mic/tests/test_mic_tool_setup.py`
- `pi5mic/tests/test_transport_openclaw.py`
- `pi5mic/tests/test_voiceinput.py`
- `pi5mic/tests/test_voiceinput_tool.py`
- `ninjaclawbot/README.md`
- `ninjaclawbot/pyproject.toml`
- `ninjaclawbot/uv.lock`
- `ninjaclawbot/src/ninjaclawbot/__main__.py`
- `ninjaclawbot/src/ninjaclawbot/config.py`
- `ninjaclawbot/src/ninjaclawbot/runtime.py`
- `ninjaclawbot/tests/test_cli_tools.py`
- `ninjaclawbot/tests/test_runtime.py`
- `integrations/openclaw/ninjaclawbot-plugin/src/index.ts`
- `integrations/openclaw/ninjaclawbot-plugin/src/runner.ts`
- `integrations/openclaw/ninjaclawbot-plugin/tests/index.test.ts`
- `integrations/openclaw/ninjaclawbot-plugin/tests/runner.test.ts`

Why:

- the one-shot microphone path was working, but the approved next step was the
  always-on voice input feature
- the wake-word listener needed to stay manual-start/manual-stop for privacy and
  safety instead of becoming an auto-start plugin service
- users needed a clearer install path for the optional Porcupine dependency
- `ninjaclawbot` and the OpenClaw plugin needed to detect and report optional
  voice-input readiness without failing when `pi5mic` is missing or not
  configured

Lint and test results:

- Python gate:
  - `python3 -m compileall pi5mic/src pi5mic/tests ninjaclawbot/src ninjaclawbot/tests src`
  - `uv run --extra dev ruff check pi5mic/src pi5mic/tests ninjaclawbot/src ninjaclawbot/tests src`
  - `uv run --extra dev ruff format --check pi5mic/src pi5mic/tests ninjaclawbot/src ninjaclawbot/tests src`
- package test gate:
  - `cd pi5mic && uv run --extra dev --project pi5mic pytest -q tests -c pyproject.toml`
  - result: `79 passed`
  - `cd ninjaclawbot && uv run --extra dev --project ninjaclawbot pytest -q tests -c pyproject.toml`
  - result: `67 passed`
- optional install-path checks:
  - `uv lock`
  - `cd ninjaclawbot && uv lock`
  - `uv run --extra dev --extra voiceinput python -c "import pvporcupine; import pi5mic; print('voiceinput-extra-ok')"`
  - `cd ninjaclawbot && uv run --extra dev --extra voiceinput python -c "import pi5mic; import pvporcupine; print('ninjaclawbot-voiceinput-extra-ok')"`
- OpenClaw plugin gate:
  - `cd integrations/openclaw/ninjaclawbot-plugin`
  - `npm run typecheck`
  - `npm test`
  - result: `16 passed`

Notes:

- the root `uv run --extra dev pytest -q` collection still fails in this
  workspace because the multi-package import paths are not resolving correctly
  there, so validation continues to use the package-level suites that are
  already passing
- Python still emits the existing `audioop` deprecation warning for the Whisper
  and live-resampling path on Python 3.11; this is future upgrade work for
  Python 3.13, not a current runtime failure

Raspberry Pi validation status:

- one-shot standalone and OpenClaw microphone capture were already user-validated
- always-on wake-word mode still needs Raspberry Pi manual validation and
  long-run tuning before it should be treated as production-ready

Follow-up:

- on the Raspberry Pi, install the optional wake-word dependency with
  `uv sync --extra dev --extra voiceinput`
- run `uv run pi5mic setup`, enable always-on voice input, then run
  `uv run pi5mic doctor`
- test `uv run pi5mic voiceinput-tool foreground` first
- then test `uv run pi5mic voiceinput-tool start`, `status`, and `stop`
- if using the integrated robot layer, also test `uv run ninjaclawbot health-check`
  and `uv run ninjaclawbot voiceinput-tool status`

## 2026-03-20 - Documentation refinement for always-on setup

Summary:

- refined the user-facing always-on voice-input documentation without changing
  runtime code

Documentation updates:

- updated [README.md](../README.md) with clearer standalone always-on setup and
  testing steps, including what the Picovoice AccessKey is and how to get it
- updated [InstallationGuide.md](../InstallationGuide.md) with a plain-language
  Picovoice subsection and a safer OpenClaw/NinjaClawBot always-on validation
  flow using `voiceinput-tool foreground`, `start`, `status`, and `stop`

Validation:

- `git diff --check`

Notes:

- this pass was documentation-only
- no code paths or Raspberry Pi behavior changed

## 2026-03-20 - Standalone `pi5mic` voiceinput extra alias

Summary:

- fixed the standalone `pi5mic` packaging mismatch where
  `uv sync --extra dev --extra voiceinput` failed inside the `pi5mic` package
  directory because only the older `wakeword` extra was defined locally

Changes:

- updated [pi5mic/pyproject.toml](../pi5mic/pyproject.toml) to add a
  `voiceinput` optional dependency alias that installs the same Porcupine
  wake-word dependency as `wakeword`

Validation:

- `cd pi5mic && uv sync --extra dev --extra voiceinput`
- `cd pi5mic && uv run --extra dev ruff check src tests`
- `cd pi5mic && uv run --extra dev ruff format --check src tests`
- `cd pi5mic && uv run --extra dev pytest -q tests -c pyproject.toml`

## 2026-03-20 - `MicDevelopment.md` openWakeWord replacement planning update

Summary:

- refined [MicDevelopment.md](../MicDevelopment.md) so it now distinguishes
  the current Porcupine-based always-on preview from the approved next-step
  `openWakeWord` migration

Documentation updates:

- updated the planning document with:
  - a clearer audit summary of current Picovoice coupling points
  - the official `openWakeWord` fit and constraints
  - a dedicated phased replacement plan for packaging, config, backend,
    runtime, tests, docs, and Raspberry Pi validation

Validation:

- `git diff --check -- MicDevelopment.md backup/DevelopmentLog.md`

Notes:

- this pass was planning and documentation only
- no runtime code changed

## 2026-03-20 - `pi5mic` openWakeWord migration

Summary:

- replaced the Picovoice/Porcupine always-on wake-word path with `openWakeWord`
  across `pi5mic` runtime code, packaging, tests, and active setup documents

Implementation changes:

- migrated `pi5mic` wake-word defaults and config migration logic to
  `openWakeWord`
- added `pi5mic install openwakeword --model-path ...` to register a custom
  `.onnx` or `.tflite` `Ninja` model and download shared runtime assets
- replaced the old Porcupine detector with a native `OpenWakeWordDetector`
  wrapper
- updated always-on readiness checks, setup prompts, doctor output, status
  output, and `voiceinput-tool` status text to use model-based wake-word setup
- removed the legacy `porcupine.py` backend implementation
- updated `pi5mic`, workspace, and `ninjaclawbot` optional `voiceinput` extras
  to install `openwakeword` instead of `pvporcupine`
- refreshed package tests for the new backend and legacy-config migration

Documentation updates:

- updated [README.md](../README.md) with the new standalone always-on flow:
  custom model creation, `pi5mic install openwakeword`, `pi5mic setup`,
  `doctor`, and `voiceinput-tool`
- updated [pi5mic/README.md](../pi5mic/README.md) to explain the new
  `openWakeWord` setup and testing flow in plain language
- updated [InstallationGuide.md](../InstallationGuide.md) with the new
  OpenClaw/NinjaClawBot always-on setup steps using a custom `Ninja`
  `openWakeWord` model instead of an access key
- updated [DevelopmentGuide.md](../DevelopmentGuide.md) troubleshooting for the
  new wake-word dependency and model-registration flow
- updated [ninjaclawbot/README.md](../ninjaclawbot/README.md) to explain that
  the optional wrapper now depends on a registered `openWakeWord` model
- updated [MicDevelopment.md](../MicDevelopment.md) status notes to reflect that
  the backend migration is complete and Raspberry Pi validation/tuning is the
  main remaining work

Validation:

- `cd pi5mic && python3 -m compileall src tests`
- `cd pi5mic && uv run --extra dev ruff check src tests`
- `cd pi5mic && uv run --extra dev ruff format --check src tests`
- `cd pi5mic && uv run --extra dev pytest -q tests -c pyproject.toml`
- result: `80 passed`
- `cd pi5mic && uv sync --extra dev --extra voiceinput`
- `cd pi5mic && uv lock`
- `uv lock`
- `cd ninjaclawbot && uv lock`

Notes:

- `openWakeWord` adds a larger local runtime stack than the old backend,
  including `numpy`, `onnxruntime`, `tflite-runtime`, `scikit-learn`, and
  related packages
- the current always-on build still needs Raspberry Pi field validation for
  false-positive tuning, long idle listening, and repeated turn stability

## 2026-03-20 - `pi5mic` wake-word docs clarification

Summary:

- refined the standalone and integrated always-on voice-input setup docs so the
  `openWakeWord` options are easier to understand for non-developers

Implementation changes:

- corrected the standalone `pi5mic` README examples so the working directory is
  `~/pi5mic` instead of `~/NinjaClawBot`
- added plain-language explanations for the always-on setup options in
  [pi5mic/README.md](../pi5mic/README.md)
- added a short explanation of what `.onnx` and `.tflite` wake-word model files
  are, how they differ at a practical level, and how users should choose one
- added matching option explanations to [InstallationGuide.md](../InstallationGuide.md)
  for the OpenClaw/NinjaClawBot setup flow

Documentation updates:

- updated [pi5mic/README.md](../pi5mic/README.md)
- updated [InstallationGuide.md](../InstallationGuide.md)

Validation:

- `git diff --check -- pi5mic/README.md InstallationGuide.md backup/DevelopmentLog.md`

Notes:

- the docs now consistently describe the standalone wake-word model path as a
  file inside `~/pi5mic/voiceinput/`
- integrated examples inside NinjaClawBot continue to use
  `~/NinjaClawBot/voiceinput/`

## 2026-03-20 - `pi5mic` openWakeWord placeholder-path guard

Summary:

- tightened the always-on wake-word setup flow so `pi5mic` warns when the saved
  model path is only `.tflite` or `.onnx` without a real filename

Implementation changes:

- added `is_placeholder_openwakeword_model_path(...)` to the `openWakeWord`
  install helpers
- setup now detects placeholder-only values such as `.tflite`, warns the user,
  and leaves the model path empty instead of saving a misleading path
- wake-word readiness now raises a clearer error if the saved model path is only
  a bare extension without a real file name
- added regression tests for both the detector path validation and the setup
  wizard behavior

Documentation updates:

- updated [pi5mic/README.md](../pi5mic/README.md)
- updated [InstallationGuide.md](../InstallationGuide.md)
- updated [DevelopmentGuide.md](../DevelopmentGuide.md)

Validation:

- `cd pi5mic && python3 -m compileall src tests`
- `cd pi5mic && uv run --extra dev ruff check src tests`
- `cd pi5mic && uv run --extra dev ruff format --check src tests`
- `cd pi5mic && uv run --extra dev pytest -q tests -c pyproject.toml`

Notes:

- a real `openWakeWord` model path should look like
  `/home/pi/pi5mic/voiceinput/hey_ninja.tflite` or
  `/home/pi/pi5mic/voiceinput/hey_ninja.onnx`, not just `.tflite`

## 2026-03-21 - `pi5mic` always-on overflow and no-speech hardening

Summary:

- fixed the first real Raspberry Pi issues reported from the `openWakeWord`
  always-on listener: audio overflow after a wake-word cycle, hard failure on
  empty Whisper output, and missing foreground transcript visibility

Implementation changes:

- paused the live input stream while a captured command is being transcribed,
  then restarted it cleanly afterward
- reset the `openWakeWord` detector and live resampler state between wake-word
  cycles to reduce stale retriggers after transcription
- added `NoSpeechDetectedError` so empty `whisper.cpp` JSON output is treated as
  a recoverable no-speech result instead of a generic hard STT failure
- updated the always-on processing loop so no-speech cycles re-arm cleanly
  instead of crashing the listener
- added foreground-only detail output so `voiceinput-tool foreground` now shows
  the recognized transcript text directly in the terminal

Documentation updates:

- updated [README.md](../README.md)
- updated [pi5mic/README.md](../pi5mic/README.md)
- updated [InstallationGuide.md](../InstallationGuide.md)
- updated [DevelopmentGuide.md](../DevelopmentGuide.md)

Validation:

- `python3 -m compileall pi5mic/src pi5mic/tests`
- `uv run --extra dev ruff check pi5mic/src pi5mic/tests`
- `uv run --extra dev ruff format --check pi5mic/src pi5mic/tests`
- `cd pi5mic && uv run --extra dev pytest -q tests -c pyproject.toml`

Notes:

- the known Python 3.13 `audioop` deprecation warning is still present and is
  unrelated to these always-on fixes
- Raspberry Pi field validation is still required to tune the wake-word
  threshold for the uploaded `hey_Ninja.onnx` model in the user’s real room

## 2026-03-21 - `pi5mic` continuous OpenClaw voice-loop hardening

Summary:

- hardened the always-on OpenClaw voice-input loop so repeated wake-word cycles
  can continue even when presence updates are slow or the Raspberry Pi audio
  stream reports overflow

Implementation changes:

- reduced the default OpenClaw presence timeout to `3` seconds and made it
  configurable through `integration.openclaw.presence_timeout_seconds`
- moved OpenClaw presence updates off the live audio hot path by running them in
  a background serial worker instead of blocking the wake-word loop
- changed the always-on monitoring loop to recreate the live microphone stream
  after repeated overflow rather than depending on the same long-lived stream
  forever
- added recovery behavior so repeated overflow during an active capture cancels
  that capture, re-arms the listener, and keeps the always-on service alive
- added runtime messages that make the intended single-flight behavior clearer:
  one request is processed at a time through `LISTENING -> TRANSCRIBING ->
  DISPATCHING -> WAITING_FOR_REPLY -> COOLDOWN`
- added regression coverage for:
  - reopening the monitoring stream around a voice cycle
  - presence submission during OpenClaw dispatch
  - recovering after repeated microphone overflow

Documentation updates:

- updated [README.md](../README.md)
- updated [pi5mic/README.md](../pi5mic/README.md)
- updated [InstallationGuide.md](../InstallationGuide.md)
- updated [DevelopmentGuide.md](../DevelopmentGuide.md)

Validation:

- `python3 -m compileall pi5mic/src pi5mic/tests`
- `uv run --extra dev ruff check pi5mic/src pi5mic/tests`
- `uv run --extra dev ruff format --check pi5mic/src pi5mic/tests`
- `cd pi5mic && uv run --extra dev pytest -q tests -c pyproject.toml`

Notes:

- the listener still intentionally ignores overlapping wake-word triggers while
  the previous OpenClaw request is active; this is the safeguard that prevents
  stacked voice commands
- Raspberry Pi field validation is still required to confirm the best threshold
  and overflow behavior for the user’s real USB microphone and room noise

## 2026-03-21 - `pi5mic` fail-open OpenClaw presence diagnostics

Summary:

- refined the OpenClaw presence path so slow or unavailable presence updates no
  longer fail the whole `doctor` check or keep retrying during an active
  listener session

Implementation changes:

- added `OpenClawVoiceReadyReport` so the readiness probe can return successful
  gateway health plus non-fatal presence warnings separately
- updated `pi5mic doctor` and the OpenClaw setup readiness check to treat
  non-pairing presence problems as warnings instead of hard failures
- kept pairing-required behavior as a real failure because that usually blocks
  the OpenClaw voice handoff path itself
- updated the async presence updater so the listener disables further presence
  submissions after the first hard failure and keeps the conversation loop alive
- added regression coverage for the new doctor warning path and fail-open
  presence updater behavior

Documentation updates:

- updated [pi5mic/README.md](../pi5mic/README.md)
- updated [InstallationGuide.md](../InstallationGuide.md)
- updated [DevelopmentGuide.md](../DevelopmentGuide.md)

Validation:

- `python3 -m compileall pi5mic/src pi5mic/tests`
- `uv run --extra dev ruff check pi5mic/src pi5mic/tests`
- `uv run --extra dev ruff format --check pi5mic/src pi5mic/tests`
- `cd pi5mic && uv run --extra dev pytest -q tests -c pyproject.toml`

Notes:

- if `doctor` now warns that presence is degraded, voice handoff can still be
  tested as long as the gateway and agent path are otherwise healthy

## 2026-03-22 - `pi5mic` package license and README overhaul

Summary:

- added the missing standalone package `LICENSE` file for `pi5mic`
- rewrote the `pi5mic` README to match the structure and tone of the other
  `pi5*` libraries while keeping the newer microphone, OpenClaw, Gemini, and
  always-on voice-input workflows understandable for non-developers

Implementation changes:

- added [pi5mic/LICENSE](../pi5mic/LICENSE) using the same MIT template as the
  sibling `pi5*` packages
- reorganized [pi5mic/README.md](../pi5mic/README.md) into a clearer package
  guide with:
  - a consistent header and links block
  - a table of contents
  - a full feature summary
  - an architecture/file-tree section
  - a from-scratch Raspberry Pi standalone installation path
  - a shorter beginner-friendly `mic-tool` and `voiceinput-tool` testing flow
  - dedicated OpenClaw mode testing steps
  - a fuller direct command-line reference
  - an appendix for troubleshooting and concept explanations
- corrected the standalone working-directory examples so they use `~/pi5mic`
  instead of `~/NinjaClawBot`
- added plain-language explanations for:
  - what a Gemini API key is and when it is needed
  - what the wake-word model file is
  - what `.onnx` and `.tflite` files are
  - how to create or obtain a custom `hey Ninja` wake-word model

Documentation updates:

- updated [pi5mic/README.md](../pi5mic/README.md)

Validation:

- `git diff --check -- pi5mic/LICENSE pi5mic/README.md backup/DevelopmentLog.md`
- `cd pi5mic && uv run pi5mic --help`
- `cd pi5mic && uv run pi5mic mic-tool --help`
- `cd pi5mic && uv run pi5mic voiceinput-tool --help`

Raspberry Pi validation status:

- not required for this pass because the change is documentation and packaging
  metadata only

Follow-up:

- if the main project docs need the same wording cleanup later, mirror the
  strongest beginner-facing sections from `pi5mic/README.md` into
  `InstallationGuide.md` and the root `README.md`

## 2026-03-22 - `pi5mic` README appendix quick-link refinement

Summary:

- refined the `pi5mic` README so the setup and testing steps now point directly
  to the matching appendix explanations when a user wants more detail

Implementation changes:

- added `Need more detail?` quick-link blocks to the most common question
  points in the standalone setup, always-on setup, Gemini setup, and OpenClaw
  setup flow
- refined the appendix contents list so each appendix item now explains which
  setup or testing steps it supports

Documentation updates:

- updated [pi5mic/README.md](../pi5mic/README.md)

Validation:

- `git diff --check -- pi5mic/README.md backup/DevelopmentLog.md`

Raspberry Pi validation status:

- not required for this pass because the change is documentation only

## 2026-03-22 - `InstallationGuide.md` structure and flow rewrite

Summary:

- rewrote the main installation guide so it now follows a clearer end-to-end
  build flow for Raspberry Pi 5, the `pi5*` libraries, `ninjaclawbot`,
  OpenClaw integration, Telegram validation, and optional `pi5mic` voice input

Implementation changes:

- reorganized [InstallationGuide.md](../InstallationGuide.md) around the real
  user journey:
  - prepare Raspberry Pi
  - install the NinjaClawBot workspace
  - wire hardware
  - configure each `pi5*` library with its interactive tool
  - validate local NinjaClawBot behavior
  - install and onboard OpenClaw
  - patch and validate the OpenClaw integration
  - validate Telegram and voice input end to end
- promoted `pi5mic` from a deep `9.5` subsection into a dedicated major setup
  phase with clearer standalone-first guidance
- removed the old mixed `9.5.xA` heading pattern and replaced it with a more
  consistent section hierarchy
- kept the important technical content from the previous guide, including:
  - the `openclaw.json` patch script
  - the `BOOT.md` script
  - the `AGENTS.md` update script
  - the diagnostics and Telegram validation steps
  - the sanitized `openclaw.json` reference example
- consolidated troubleshooting into more focused appendices for:
  - Raspberry Pi base setup
  - hardware and local tests
  - `pi5mic` and voice input
  - OpenClaw and Telegram

Documentation updates:

- updated [InstallationGuide.md](../InstallationGuide.md)

Validation:

- `git diff --check -- InstallationGuide.md backup/DevelopmentLog.md`
- heading and section sanity review with `rg '^#{1,4} ' InstallationGuide.md`

Raspberry Pi validation status:

- not required for this pass because the change is documentation only

Follow-up:

- if desired, mirror the same phased installation structure into the root
  `README.md` quick-start section later so the high-level and detailed guides
  feel even more consistent

## 2026-03-22 - Root `README.md` and `DevelopmentGuide.md` audience-focused rewrite

Summary:

- rewrote the top-level `README.md` for end users and rebuilt
  `DevelopmentGuide.md` for developers and maintainers so the two documents now
  serve clearer, separate purposes while staying aligned with the current
  Raspberry Pi 5, OpenClaw, and `pi5mic` build

Implementation changes:

- replaced the old top-level [README.md](../README.md) with a more structured
  end-user introduction that now focuses on:
  - project overview and goals
  - what users can expect from the workspace
  - system-at-a-glance hardware and software summaries
  - a clearer package map
  - explicit "choose your path" guidance
  - a shorter quick-start path that routes users to the correct detailed guide
  - more parallel English, Japanese, and Traditional Chinese sections
- replaced the old [DevelopmentGuide.md](../DevelopmentGuide.md) with a cleaner
  maintainer reference organized around:
  - project specification
  - architecture and runtime boundaries
  - repository and package ownership
  - curated repository structure
  - public CLI, action, and OpenClaw tool surfaces
  - configuration and runtime files
  - development workflow
  - validation gates
  - Raspberry Pi validation model
  - maintenance guidance
  - bug triage and troubleshooting shortcuts
- removed the oversized static file-tree emphasis from the previous developer
  guide and replaced it with a smaller curated structure plus clearer ownership
  tables
- reduced install-detail duplication in the root README by directing detailed
  build work to [InstallationGuide.md](../InstallationGuide.md) and package
  READMEs instead of repeating long setup sections there

Documentation updates:

- updated [README.md](../README.md)
- updated [DevelopmentGuide.md](../DevelopmentGuide.md)

Validation:

- `git diff --check -- README.md`
- `uv run ninjaclawbot --help`
- `uv run pi5mic --help`
- `git diff --check -- DevelopmentGuide.md`
- `uv run ninjaclawbot --help`
- `uv run pi5servo --help`
- `uv run pi5disp --help`
- `uv run pi5buzzer --help`
- `uv run pi5mic --help`
- `uv run pi5vl53l0x --help`

Raspberry Pi validation status:

- not required for this pass because the change is documentation only

Follow-up:

- if desired, apply the same audience-and-navigation cleanup next to the
  package-level `ninjaclawbot/README.md` so the integrated runtime guide mirrors
  the new top-level documentation structure even more closely
