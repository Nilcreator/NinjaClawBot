# NinjaClawBot

NinjaClawBot is the Raspberry Pi 5 based evolution of the NinjaRobot driver stack. The current migration focus is the standalone Pi 5 driver libraries:

- `pi5buzzer`
- `pi5servo`
- `pi5disp`
- `pi5vl53l0x`

## Implementation Status

The first migrated library now exists:

- [pi5buzzer](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/pi5buzzer)

`pi5buzzer` preserves the legacy `pi0buzzer` API shape, note and emotion helpers,
CLI commands, and `buzzer.json` config format, while replacing direct `pigpio`
usage with a Raspberry Pi 5 compatible `RPi.GPIO` style backend intended for
`rpi-lgpio`.

Pending migration libraries:

- `pi5servo`
- `pi5disp`
- `pi5vl53l0x`

For development workflow and validation guidance:

- see [developmentPlan.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/developmentPlan.md)
- see [DevelopmentGuide.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/DevelopmentGuide.md)
- the agentic implementation workflow is defined in [.agents/skills/ninjaclawbot-implementation/SKILL.md](/Users/nilcreator/Desktop/0_Projects/Nilcreation/NinjaRobot/Code%20library/NinjaClawbot/.agents/skills/ninjaclawbot-implementation/SKILL.md)
