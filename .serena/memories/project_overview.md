# NinjaClawbot Project Overview
- Purpose: Python-based robot software and hardware drivers for NinjaClawBot, developed primarily on macOS and validated on Raspberry Pi 5 hardware.
- Top-level structure: root documentation files (`README.md`, `DevelopmentGuide.md`, `DevelopmentLog.md`, `AGENTS.md`) plus a `NinjaRobotV5_bak/` tree containing Python packages and hardware-related modules such as `pi0servo`, `pi0vl53l0x`, `pi0buzzer`, `pi0disp`, `ninja_core`, `ninja_ble`, `ninja_utils`, and `ninja_webapp`.
- Tech stack: Python, Ruff, pytest, optional mypy where typing is already adopted. Hardware-related domains include GPIO, I2C, SPI, serial, PWM, motors, sensors, camera, and power behavior.
- Primary development machine: Darwin/macOS. Target validation hardware: Raspberry Pi 5.
- Workflow emphasis: research first, phased plans, user approval before coding, per-phase validation, Raspberry Pi validation planning, and mandatory documentation updates.