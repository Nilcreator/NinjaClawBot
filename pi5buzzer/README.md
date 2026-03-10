# pi5buzzer

`pi5buzzer` is the Raspberry Pi 5 migration of the legacy `pi0buzzer` library.
It keeps the same non-blocking playback model, note and emotion helpers, JSON
config manager, and CLI workflow, but replaces direct `pigpio` usage with an
`RPi.GPIO`-compatible backend intended for `rpi-lgpio` on Raspberry Pi 5.

## Features

- non-blocking queued playback
- `Buzzer` and `MusicBuzzer` public API parity with the legacy library
- note lookup, demo song, and 14 emotion sounds
- JSON config manager with `buzzer.json` compatibility
- CLI commands: `init`, `beep`, `play`, `info`, `config`, `buzzer-tool`
- optional future `ninja_core` integration via `driver.py` re-exports

## Installation

On Raspberry Pi 5, install the Pi backend extra:

```bash
pip install ".[pi]"
```

Or install the runtime dependency directly:

```bash
pip install rpi-lgpio
```

`rpi-lgpio` provides the `RPi.GPIO` compatible API used by this library on
Raspberry Pi 5.

## Quick Start

```bash
pi5buzzer init 17
pi5buzzer beep 440 0.5
pi5buzzer play happy
pi5buzzer info --health-check
pi5buzzer buzzer-tool
```

## Python API

```python
from pi5buzzer import MusicBuzzer

with MusicBuzzer(pin=17) as buzzer:
    buzzer.play_sound(440, 0.5)
    buzzer.play_note("C5", 0.3)
    buzzer.play_emotion("happy")
```
