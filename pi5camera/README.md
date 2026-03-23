# pi5camera

Standalone-first Raspberry Pi 5 camera tools for NinjaClawBot.

This package provides:

- guided camera setup through `camera-tool`
- one-shot normal photo capture
- local face recognition and enrollment
- integration hooks for `ninjaclawbot` and OpenClaw

The implementation is designed to stay import-safe on non-Pi development
machines by loading Raspberry Pi camera dependencies lazily.
