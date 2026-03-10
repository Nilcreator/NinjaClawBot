# NinjaClawBot Development Guide

## Scope

This guide records the current developer workflow for the new standalone Pi 5 driver libraries:

- `pi5buzzer`
- `pi5servo`
- `pi5disp`
- `pi5vl53l0x`

The detailed migration and backend strategy lives in [developmentPlan.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/developmentPlan.md).

## Agentic Workflow

The source of truth for agent-led implementation work is:

- [.agents/skills/ninjaclawbot-implementation/SKILL.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/.agents/skills/ninjaclawbot-implementation/SKILL.md)

That skill requires the following workflow:

1. Audit the legacy `pi0*` driver before planning.
2. Plan one `pi5*` library migration phase at a time.
3. Wait for user approval before coding.
4. Keep each `pi5*` library standalone-first and preserve optional future integration hooks.
5. Pass the quality gate before advancing to the next phase.
6. Produce a manual Raspberry Pi 5 validation checklist after each migrated library.
7. Update developer documentation and the development log before closing the task.

## Required Files To Review During Driver Work

Always review:

- [developmentPlan.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/developmentPlan.md)
- [README.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/README.md)
- [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- [DevelopmentLog.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentLog.md)

For the selected legacy library, inspect:

- `NinjaRobotV5_bak/pi0buzzer`
- `NinjaRobotV5_bak/pi0servo`
- `NinjaRobotV5_bak/pi0disp`
- `NinjaRobotV5_bak/pi0vl53l0x`

At minimum inspect:

- `pyproject.toml`
- `README.md`
- `src/<package>/__init__.py`
- `src/<package>/__main__.py`
- `src/<package>/driver.py` if present
- core modules
- config manager
- CLI modules
- tests

## Quality Checks

Default quality gate for each implementation phase:

```bash
python -m compileall .
ruff check .
ruff format --check .
pytest -q
```

If the package already uses typing checks:

```bash
mypy .
```

Preferred practice:

- run package-local checks while migrating one library
- run broader repo checks only if shared files changed

## pi5buzzer Migration Notes

Implemented package:

- [pi5buzzer](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer)

Legacy source audited for parity:

- [NinjaRobotV5_bak/pi0buzzer](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/NinjaRobotV5_bak/pi0buzzer)

Required public compatibility surface:

- `pi5buzzer.Buzzer`
- `pi5buzzer.MusicBuzzer`
- `pi5buzzer.driver.Buzzer`
- `pi5buzzer.driver.MusicBuzzer`
- CLI commands in [__main__.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/src/pi5buzzer/__main__.py): `init`, `beep`, `play`, `info`, `config`, `buzzer-tool`
- config manager in [config_manager.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/src/pi5buzzer/config/config_manager.py) keeping `buzzer.json` compatibility

Backend rule:

- use the backend factory in [driver.py](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer/src/pi5buzzer/core/driver.py)
- default runtime is an `RPi.GPIO` compatible backend intended for `rpi-lgpio` on Raspberry Pi 5
- keep high-level queueing, frequency clamping, volume semantics, and music helpers independent from the GPIO transport

Phase 1 quality gate result:

- `python -m compileall .`
- `ruff check .`
- `ruff format --check .`
- `pytest -q`
- current result for [pi5buzzer](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer): `63 passed`

Phase 1 Raspberry Pi 5 validation checklist:

- safe smoke tests: install `rpi-lgpio`, run `pi5buzzer --help`, `pi5buzzer init 17`, and verify `buzzer.json` is created
- device communication tests: run `pi5buzzer info --health-check` and confirm the backend can claim the configured GPIO pin
- actuator tests: run `pi5buzzer beep 440 0.3`, `pi5buzzer play happy`, and a short Python `play_song()` sequence
- power-risk tests: verify `off()` and CLI exit leave the buzzer silent with no stuck PWM output
- expected outcome: short tones and queued playback are audible and stable on Raspberry Pi 5
- rollback: uninstall `pi5buzzer`, remove the created `buzzer.json`, and disconnect the buzzer from the GPIO pin

## Raspberry Pi 5 Validation Flow

After each migrated library, produce and review:

- safe smoke tests
- device communication tests
- actuator-moving tests where relevant
- power-risk tests where relevant
- expected outcomes
- rollback steps

Special rule for `pi5servo`:

- treat software-timed servo pulses as testing-only
- prefer hardware-backed PWM
- require direct signal measurement with a logic analyser or oscilloscope during real hardware validation
