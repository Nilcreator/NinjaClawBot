# NinjaClawBot

<div align="center">

**A modular Raspberry Pi 5 robot workspace with interactive hardware tools, an integrated robot layer, and OpenClaw deployment support**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Raspberry Pi 5](https://img.shields.io/badge/platform-Raspberry%20Pi%205-red.svg)](https://www.raspberrypi.com/)
[![OpenClaw Ready](https://img.shields.io/badge/OpenClaw-ready-0F766E.svg)](https://docs.openclaw.ai/)

[English](#english) | [日本語](#japanese) | [繁體中文](#traditional-chinese)

</div>

---

## Contents

- [English](#english)
- [日本語](#japanese)
- [繁體中文](#traditional-chinese)
- Main guides:
  - [InstallationGuide.md](InstallationGuide.md)
  - [DevelopmentGuide.md](DevelopmentGuide.md)
- Package guides:
  - [ninjaclawbot](ninjaclawbot/README.md)
  - [pi5camera](pi5camera/README.md)
  - [pi5servo](pi5servo/README.md)
  - [pi5disp](pi5disp/README.md)
  - [pi5buzzer](pi5buzzer/README.md)
  - [pi5mic](pi5mic/README.md)
  - [pi5vl53l0x](pi5vl53l0x/README.md)
- OpenClaw integration:
  - [Plugin folder](integrations/openclaw/ninjaclawbot-plugin)
  - [Plugin skill](integrations/openclaw/ninjaclawbot-plugin/skills/ninjaclawbot_control/SKILL.md)
- Archive:
  - [backup/README.md](backup/README.md)

---

<a id="english"></a>

# English

## Project Overview

**NinjaClawBot** is a Raspberry Pi 5 robot software workspace built from small hardware libraries plus one integrated robot layer.

The design goal is practical and beginner-friendly:

1. test each hardware module by itself first
2. combine the modules through `ninjaclawbot`
3. connect the full robot to OpenClaw
4. optionally add microphone input with `pi5mic`

This structure makes the project easier to build, test, and repair because each layer can be validated on its own before you move to the next one.

## What You Can Expect

From this repository, you can expect:

- standalone `pi5*` libraries with interactive tools for setup and testing
- one integrated robot package, `ninjaclawbot`, that combines display, sound, movement, sensing, and optional voice input
- an OpenClaw plugin for chat-driven robot behavior
- a documented Raspberry Pi 5 build path from scratch
- optional voice input with one-shot capture or manual always-on listening

The current validated OpenClaw build supports this flow:

1. OpenClaw starts
2. the robot shows a startup greeting
3. the robot stays in an idle expression while waiting
4. a user message triggers robot reaction and AI processing
5. the robot shows the matching reply expression
6. Telegram still receives the normal text reply
7. OpenClaw stop triggers the sleepy power-off sequence

## System At A Glance

### Hardware

| Part | Current validated direction |
| --- | --- |
| Brain | Raspberry Pi 5 |
| Camera | Raspberry Pi camera module through `pi5camera` |
| Display | SPI display supported by `pi5disp` |
| Microphone | USB microphone or mic module through `pi5mic` |
| Sound | Passive buzzer supported by `pi5buzzer` |
| Movement | Servos supported by `pi5servo` |
| Distance sensing | VL53L0X through `pi5vl53l0x` |
| Chat interface | OpenClaw + Telegram validated |

### Software

| Layer | Purpose |
| --- | --- |
| Root workspace | Installs and syncs all packages with `uv` |
| `pi5*` libraries | Standalone hardware setup, drivers, and test tools |
| `ninjaclawbot` | High-level robot runtime and saved assets |
| OpenClaw plugin | Bridge, diagnostics, and chat-facing tool surface |
| `pi5mic` | One-shot capture, STT, and optional always-on voice input |

## Core Packages

| Package | Main role | Interactive tool |
| --- | --- | --- |
| `pi5servo` | Servo calibration, movement control, motion assets | `servo-tool` |
| `pi5disp` | Display initialization, rendering, brightness, rotation | `display-tool` |
| `pi5buzzer` | Tones, emotion sounds, buzzer config | `buzzer-tool` |
| `pi5camera` | Normal photo capture, face recognition, and face enrollment | `camera-tool` |
| `pi5mic` | Recording, STT, OpenClaw handoff, optional always-on listening | `mic-tool`, `voiceinput-tool` |
| `pi5vl53l0x` | Distance sensor setup and testing | `sensor-tool` |
| `ninjaclawbot` | Integrated robot actions, expressions, movement playback, and camera wrappers | `camera-tool`, `expression-tool`, `movement-tool` |

## Choose Your Path

Choose the path that matches what you want to do:

1. **I only want to test one hardware module.**
   Open the matching package guide in `pi5camera`, `pi5servo`, `pi5disp`, `pi5buzzer`, `pi5mic`, or `pi5vl53l0x`.

2. **I want to build the full robot locally first.**
   Start with [InstallationGuide.md](InstallationGuide.md), wire the hardware, and run the interactive tools one by one.

3. **I want the robot to work with OpenClaw and Telegram.**
   Follow [InstallationGuide.md](InstallationGuide.md) end to end. It covers Raspberry Pi setup, OpenClaw onboarding, config patching, validation, and Telegram checks.

4. **I want voice input now or later.**
   Use [pi5mic/README.md](pi5mic/README.md). `pi5mic` can be used by itself or inside the full NinjaClawBot build.

## Quick Start

This is the shortest safe first path from a fresh clone.

```bash
git clone https://github.com/Nilcreator/NinjaClawBot.git
cd NinjaClawBot
uv sync --extra dev
uv run ninjaclawbot health-check
uv run pi5camera camera-tool
uv run pi5servo servo-tool
uv run pi5disp display-tool
uv run pi5buzzer buzzer-tool
uv run pi5mic mic-tool
uv run pi5vl53l0x sensor-tool
```

On Raspberry Pi, prefer the bootstrap installer before the first `uv run`:

```bash
./scripts/bootstrap-rpi-workspace.sh
```

If you already know that you want always-on voice input too, use:

```bash
./scripts/bootstrap-rpi-workspace.sh --voiceinput
```

The bootstrap installer:

- installs the Raspberry Pi system packages needed by `pi5camera` and `pi5mic`
- installs optional camera and recognition apt packages for `pi5camera` when
  they are available on the Raspberry Pi image
- recreates `.venv` from scratch with `/usr/bin/python3 -m venv --system-site-packages`
- runs `uv sync --active --extra dev`
- installs the `pi5camera` startup hook inside `.venv` so plain `uv run python`
  and `uv run pi5camera ...` commands can see the Raspberry Pi system camera
  stack before user imports
- prefers the Raspberry Pi system recognition stack on ARM boards and only
  falls back to a Python package install when those system packages are not
  available
- finishes with `uv run pi5camera doctor` plus a
  `uv run python -c "import libcamera, picamera2, face_recognition; print('imports-ok')"`
  check

On non-Raspberry Pi development machines, if you already know that you want
always-on voice input, install the optional wake-word dependency too:

```bash
uv sync --extra dev --extra voiceinput
```

What this quick start does:

- installs the whole Python workspace
- checks that the integrated robot layer can load
- opens the guided tools you will use to configure and test each hardware module

What to do next:

- For a complete Raspberry Pi build: go to [InstallationGuide.md](InstallationGuide.md)
- For voice setup and always-on listening: go to [pi5mic/README.md](pi5mic/README.md)
- For developer architecture and maintenance details: go to [DevelopmentGuide.md](DevelopmentGuide.md)

## Documentation Map

| Document | Best for |
| --- | --- |
| [InstallationGuide.md](InstallationGuide.md) | Full Raspberry Pi 5 install, OpenClaw setup, Telegram validation, and voice integration |
| [DevelopmentGuide.md](DevelopmentGuide.md) | Developer reference, architecture, package ownership, validation workflow, and troubleshooting |
| [ninjaclawbot/README.md](ninjaclawbot/README.md) | Integrated robot runtime, expressions, movements, and main CLI |
| [pi5camera/README.md](pi5camera/README.md) | Camera setup, normal photo capture, face recognition, and enrollment |
| [pi5servo/README.md](pi5servo/README.md) | Servo wiring, calibration, and safe movement testing |
| [pi5disp/README.md](pi5disp/README.md) | Display wiring, display config, and display testing |
| [pi5buzzer/README.md](pi5buzzer/README.md) | Buzzer setup and sound playback |
| [pi5mic/README.md](pi5mic/README.md) | Microphone setup, STT backends, always-on listening, and OpenClaw handoff |
| [pi5vl53l0x/README.md](pi5vl53l0x/README.md) | Distance sensor setup and verification |
| [backup/README.md](backup/README.md) | Archived planning documents and development history |

## Current Status

**Status:** Stage 2 OpenClaw integration is implemented and validated on Raspberry Pi 5.

Current highlights:

- persistent bridge between OpenClaw and the robot runtime
- validated startup greeting, idle, thinking, reply, and sleepy lifecycle
- Telegram text replies plus robot reactions on the validated OpenClaw path
- `ninjaclawbot_diagnostics` for deployment and readiness checks
- `pi5camera` available as a standalone package with guided setup, normal photo capture, local face recognition, and second-step face enrollment
- `ninjaclawbot` now exposes `camera-tool`, `capture-photo`, `recognize-faces`, and `enroll-pending-face`
- the OpenClaw plugin now exposes `ninjaclawbot_capture_photo`, `ninjaclawbot_recognize_faces`, and `ninjaclawbot_enroll_pending_face`
- `pi5servo` now reuses configured live native GPIO servos in `servo-tool`, keeps healthy PWM channels exported across normal reloads, repairs stale `pwmchip0/pwm0|pwm1` sysfs nodes on claim, and rolls back partial startup claims so one bad PWM channel does not poison the other
- `pi5mic` available as a standalone package and as an optional part of the full build
- manual always-on voice input preview available through `voiceinput-tool`

Still important:

- the always-on voice path is a manual-start feature, not an auto-start daemon
- long-run Raspberry Pi room-noise tuning is still something users should validate on their own hardware

## License

This project is licensed under the **MIT License**.

**Copyright (c) 2026 Chihkuang Chang**

---

<a id="japanese"></a>

# 日本語

## プロジェクト概要

**NinjaClawBot** は、Raspberry Pi 5 向けに作られたロボット制御ワークスペースです。小さく分けられたハードウェア用ライブラリと、それらを統合する `ninjaclawbot` で構成されています。

基本的な考え方は次のとおりです。

1. 各ハードウェアを単体ライブラリで確認する
2. `ninjaclawbot` で統合する
3. OpenClaw と接続して会話型ロボットとして動かす
4. 必要なら `pi5mic` で音声入力を追加する

## 期待できること

このリポジトリでは次のことができます。

- 各 `pi5*` ライブラリを対話ツールで単体テストする
- `ninjaclawbot` でロボット全体をまとめる
- OpenClaw と Telegram を使った会話型ロボットを構成する
- `pi5mic` で単発音声入力や常時待機音声入力を試す

## 全体構成

### ハードウェア

| 構成 | 現在の検証方向 |
| --- | --- |
| 本体 | Raspberry Pi 5 |
| 表示 | `pi5disp` 対応の SPI ディスプレイ |
| マイク | `pi5mic` を使う USB マイクまたはマイクモジュール |
| 音 | `pi5buzzer` 対応のパッシブブザー |
| 動作 | `pi5servo` 対応のサーボ |
| 距離検知 | `pi5vl53l0x` 対応の VL53L0X |
| 会話連携 | OpenClaw + Telegram 検証済み |

### ソフトウェア

| レイヤー | 役割 |
| --- | --- |
| ルートワークスペース | `uv` で全パッケージをまとめて導入 |
| `pi5*` ライブラリ | 単体のハードウェア設定とテスト |
| `ninjaclawbot` | ロボット統合ランタイム |
| OpenClaw plugin | ブリッジ、診断、会話ツール連携 |
| `pi5mic` | 録音、STT、OpenClaw 連携、常時待機音声入力 |

## 主なパッケージ

| パッケージ | 主な役割 | 対話ツール |
| --- | --- | --- |
| `pi5servo` | サーボ校正、動作制御、モーション管理 | `servo-tool` |
| `pi5disp` | 画面初期化、描画、明るさや回転設定 | `display-tool` |
| `pi5buzzer` | 音再生、音パターン確認 | `buzzer-tool` |
| `pi5mic` | 録音、STT、OpenClaw 引き渡し、常時待機音声入力 | `mic-tool`, `voiceinput-tool` |
| `pi5vl53l0x` | 距離センサー設定と確認 | `sensor-tool` |
| `ninjaclawbot` | 統合アクション、表情、モーション再生 | `expression-tool`, `movement-tool` |

## 使い始める道順

1. **単体ハードウェアだけ試したい**
   対応する `pi5*` パッケージの README を開いてください。

2. **ロボット全体を Raspberry Pi で組みたい**
   [InstallationGuide.md](InstallationGuide.md) を最初から順に進めてください。

3. **OpenClaw と Telegram まで含めて完成させたい**
   [InstallationGuide.md](InstallationGuide.md) の OpenClaw 部分まで含めて実施してください。

4. **音声入力を使いたい**
   [pi5mic/README.md](pi5mic/README.md) を参照してください。単体でも、NinjaClawBot の一部としても使えます。

## クイックスタート

```bash
git clone https://github.com/Nilcreator/NinjaClawBot.git
cd NinjaClawBot
uv sync --extra dev
uv run ninjaclawbot health-check
uv run pi5servo servo-tool
uv run pi5disp display-tool
uv run pi5buzzer buzzer-tool
uv run pi5mic mic-tool
uv run pi5vl53l0x sensor-tool
```

常時待機音声入力も使う予定がある場合は、追加で次を実行します。

```bash
uv sync --extra dev --extra voiceinput
```

次のステップ:

- Raspberry Pi で一式構築したい場合: [InstallationGuide.md](InstallationGuide.md)
- 音声入力を詳しく設定したい場合: [pi5mic/README.md](pi5mic/README.md)
- 開発や保守の情報が必要な場合: [DevelopmentGuide.md](DevelopmentGuide.md)

## ドキュメント案内

| ドキュメント | 用途 |
| --- | --- |
| [InstallationGuide.md](InstallationGuide.md) | Raspberry Pi 5、OpenClaw、Telegram、音声入力まで含む導入手順 |
| [DevelopmentGuide.md](DevelopmentGuide.md) | 開発者向けの構成、所有レイヤー、検証手順、トラブルシュート |
| [ninjaclawbot/README.md](ninjaclawbot/README.md) | 統合ロボットレイヤーの使い方 |
| [pi5servo/README.md](pi5servo/README.md) | サーボ設定と安全な動作確認 |
| [pi5disp/README.md](pi5disp/README.md) | ディスプレイ設定と表示確認 |
| [pi5buzzer/README.md](pi5buzzer/README.md) | ブザー設定と音再生 |
| [pi5mic/README.md](pi5mic/README.md) | マイク設定、STT、常時待機音声入力、OpenClaw 連携 |
| [pi5vl53l0x/README.md](pi5vl53l0x/README.md) | 距離センサー設定 |
| [backup/README.md](backup/README.md) | 過去の計画と履歴 |

## 現在のステータス

**ステータス:** Stage 2 OpenClaw 連携は Raspberry Pi 5 上で実装・検証済みです。

現在の主な状態:

- OpenClaw とロボットランタイムの永続ブリッジ
- 起動、待機、思考中、返信、sleepy の基本ライフサイクル
- Telegram 文字返信とロボット反応の両立
- `ninjaclawbot_diagnostics` による診断
- `pi5mic` の単体利用と統合利用
- `voiceinput-tool` による手動開始の常時待機音声入力プレビュー

## ライセンス

本プロジェクトは **MIT License** で公開されています。

**Copyright (c) 2026 Chihkuang Chang**

---

<a id="traditional-chinese"></a>

# 繁體中文

## 專案概要

**NinjaClawBot** 是一個以 Raspberry Pi 5 為核心的機器人控制工作區，由多個可獨立測試的硬體函式庫，以及一個整合層 `ninjaclawbot` 組成。

建議的使用順序如下：

1. 先個別測試每個硬體模組
2. 再用 `ninjaclawbot` 把模組整合起來
3. 之後接上 OpenClaw，讓機器人透過聊天介面運作
4. 需要時再加入 `pi5mic` 語音輸入

## 你可以期待什麼

這個專案目前提供：

- 各 `pi5*` 函式庫的互動式設定與測試工具
- 一個整合好的機器人層 `ninjaclawbot`
- OpenClaw plugin，讓機器人能與聊天代理整合
- 從零開始的 Raspberry Pi 5 建置文件
- `pi5mic` 單次語音輸入與手動啟動的常時聆聽語音輸入

## 系統總覽

### 硬體

| 元件 | 目前驗證方向 |
| --- | --- |
| 主機 | Raspberry Pi 5 |
| 顯示器 | `pi5disp` 支援的 SPI 顯示器 |
| 麥克風 | 透過 `pi5mic` 使用的 USB 麥克風或麥克風模組 |
| 聲音 | `pi5buzzer` 支援的被動式蜂鳴器 |
| 動作 | `pi5servo` 支援的伺服馬達 |
| 距離感測 | `pi5vl53l0x` 支援的 VL53L0X |
| 對話介面 | 已驗證 OpenClaw + Telegram |

### 軟體

| 層級 | 作用 |
| --- | --- |
| 根工作區 | 用 `uv` 一次安裝全部套件 |
| `pi5*` 函式庫 | 各硬體模組的單獨設定與測試 |
| `ninjaclawbot` | 機器人整合執行層 |
| OpenClaw plugin | 橋接、診斷、聊天工具面 |
| `pi5mic` | 錄音、STT、OpenClaw 交接與常時聆聽 |

## 核心套件

| 套件 | 主要用途 | 互動工具 |
| --- | --- | --- |
| `pi5servo` | 伺服馬達校正、動作控制、動作資產 | `servo-tool` |
| `pi5disp` | 顯示初始化、畫面渲染、亮度與旋轉設定 | `display-tool` |
| `pi5buzzer` | 聲音播放與音效測試 | `buzzer-tool` |
| `pi5mic` | 錄音、STT、OpenClaw 交接、常時語音輸入 | `mic-tool`, `voiceinput-tool` |
| `pi5vl53l0x` | 距離感測器設定與檢查 | `sensor-tool` |
| `ninjaclawbot` | 整合動作、表情、動作播放 | `expression-tool`, `movement-tool` |

## 依需求選擇路徑

1. **只想測試單一硬體模組**
   直接閱讀對應的 `pi5*` 套件 README。

2. **想先在本地完成整體機器人建置**
   請依照 [InstallationGuide.md](InstallationGuide.md) 的流程進行。

3. **想完成 OpenClaw 與 Telegram 整合**
   請完整執行 [InstallationGuide.md](InstallationGuide.md)。

4. **想加入語音輸入**
   請閱讀 [pi5mic/README.md](pi5mic/README.md)。它可單獨使用，也可整合進完整機器人流程。

## 快速開始

```bash
git clone https://github.com/Nilcreator/NinjaClawBot.git
cd NinjaClawBot
uv sync --extra dev
uv run ninjaclawbot health-check
uv run pi5servo servo-tool
uv run pi5disp display-tool
uv run pi5buzzer buzzer-tool
uv run pi5mic mic-tool
uv run pi5vl53l0x sensor-tool
```

如果你之後要用常時語音輸入，再執行：

```bash
uv sync --extra dev --extra voiceinput
```

接下來建議：

- 要完整安裝 Raspberry Pi 與 OpenClaw: 看 [InstallationGuide.md](InstallationGuide.md)
- 要進一步設定語音輸入: 看 [pi5mic/README.md](pi5mic/README.md)
- 要查看開發與維護資訊: 看 [DevelopmentGuide.md](DevelopmentGuide.md)

## 文件導覽

| 文件 | 適合用途 |
| --- | --- |
| [InstallationGuide.md](InstallationGuide.md) | 從零開始完成 Raspberry Pi 5、OpenClaw、Telegram 與語音整合 |
| [DevelopmentGuide.md](DevelopmentGuide.md) | 開發者參考資料、架構、模組責任與驗證流程 |
| [ninjaclawbot/README.md](ninjaclawbot/README.md) | 整合機器人層的使用方式 |
| [pi5servo/README.md](pi5servo/README.md) | 伺服馬達設定與安全測試 |
| [pi5disp/README.md](pi5disp/README.md) | 顯示器設定與顯示測試 |
| [pi5buzzer/README.md](pi5buzzer/README.md) | 蜂鳴器設定與聲音播放 |
| [pi5mic/README.md](pi5mic/README.md) | 麥克風設定、STT、常時語音輸入與 OpenClaw 交接 |
| [pi5vl53l0x/README.md](pi5vl53l0x/README.md) | 距離感測器設定 |
| [backup/README.md](backup/README.md) | 歷史規劃與紀錄 |

## 目前狀態

**狀態:** Stage 2 OpenClaw 整合已在 Raspberry Pi 5 上完成並驗證。

目前重點：

- OpenClaw 與機器人執行層之間的持久橋接
- 開機、待機、思考中、回覆、sleepy 的基本生命週期
- Telegram 文字回覆與機器人反應同時成立
- `ninjaclawbot_diagnostics` 診斷工具
- `pi5mic` 可單獨使用，也可作為完整建置的一部分
- `voiceinput-tool` 提供手動啟動的常時聆聽語音輸入預覽

## 授權

本專案採用 **MIT License**。

**Copyright (c) 2026 Chihkuang Chang**
