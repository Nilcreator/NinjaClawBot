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
