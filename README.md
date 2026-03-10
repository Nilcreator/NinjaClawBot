# NinjaClawBot

NinjaClawBot is the Raspberry Pi 5 based evolution of the NinjaRobot driver stack. The current migration focus is the standalone Pi 5 driver libraries:

- `pi5buzzer`
- `pi5servo`
- `pi5disp`
- `pi5vl53l0x`

## Implementation Status

The migrated libraries that now exist are:

- [pi5buzzer](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer)
- [pi5servo](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5servo)
- [pi5disp](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5disp)
- [pi5vl53l0x](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5vl53l0x)

`pi5buzzer` preserves the legacy `pi0buzzer` API shape, note and emotion helpers,
CLI commands, and `buzzer.json` config format, while replacing direct `pigpio`
usage with a Raspberry Pi 5 compatible `RPi.GPIO` style backend intended for
`rpi-lgpio`.

`pi5servo` preserves the legacy `pi0servo` motion model, calibration flow,
movement-tool command format, CLI command set, and `servo.json` contract, while
replacing direct `pigpio` servo pulses with a backend system for Raspberry Pi 5.
The standalone-first path targets header-connected servos through hardware-backed
PWM, with optional PCA9685 support for advanced external controller setups and
legacy `pigpio` compatibility retained for future integration work.

`pi5vl53l0x` preserves the legacy `pi0vl53l0x` class, CLI command set, and
`vl53l0x.json` config format, while replacing the old `pigpio` I2C path with a
thread-safe `smbus2` backend over the Raspberry Pi 5 kernel I2C interface.

`pi5disp` preserves the legacy `pi0disp` `ST7789V` driver, CLI command set, and
`display.json` config format, while replacing the old `pigpio` SPI, GPIO, and
backlight control path with a Raspberry Pi 5 compatible split backend based on
`spidev` and an `RPi.GPIO` style interface intended for `rpi-lgpio`. The Pi 5
runtime now persists saved brightness and keeps `display-tool` on one live
display session across menu actions.

All four standalone-first Pi 5 driver libraries now exist in the project root.

For development workflow and validation guidance:

- see [developmentPlan.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/developmentPlan.md)
- see [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- the agentic implementation workflow is defined in [.agents/skills/ninjaclawbot-implementation/SKILL.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/.agents/skills/ninjaclawbot-implementation/SKILL.md)
