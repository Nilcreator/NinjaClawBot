# NinjaClawBot

<div align="center">

**A Modular Raspberry Pi 5 Robot Control Stack for OpenClaw**

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
- [Installation Guide](InstallationGuide.md)
- [Development Guide](DevelopmentGuide.md)
- Library guides:
  - [ninjaclawbot](ninjaclawbot/README.md)
  - [pi5servo](pi5servo/README.md)
  - [pi5disp](pi5disp/README.md)
  - [pi5buzzer](pi5buzzer/README.md)
  - [pi5vl53l0x](pi5vl53l0x/README.md)
- OpenClaw integration:
  - [Plugin folder](integrations/openclaw/ninjaclawbot-plugin)
  - [Plugin skill](integrations/openclaw/ninjaclawbot-plugin/skills/ninjaclawbot_control/SKILL.md)
- Archived planning and logs:
  - [backup/README.md](backup/README.md)

---

<a id="english"></a>

# English

## Project Overview

**NinjaClawBot** is a Raspberry Pi 5 robot software workspace built around small, reusable hardware libraries and one integrated robot layer.

It is designed for a practical real-world workflow:

- test each hardware module on its own first
- combine them through the `ninjaclawbot` integration layer
- connect the robot to OpenClaw
- use Telegram or another OpenClaw channel as the communication interface

The current validated build supports this flow:

1. OpenClaw starts
2. the robot shows a startup greeting
3. the robot stays in an idle face while waiting
4. a user message triggers robot reaction and AI processing
5. the robot shows the matching reply expression
6. Telegram still receives the normal text answer
7. OpenClaw stop triggers the sleepy power-off sequence

## Robot Specifications

### Hardware

| Component | Current validated direction |
|-----------|-----------------------------|
| **Brain** | Raspberry Pi 5 |
| **Display** | SPI display supported by `pi5disp` |
| **Distance Sensor** | VL53L0X supported by `pi5vl53l0x` |
| **Sound** | Passive buzzer supported by `pi5buzzer` |
| **Movement** | Servos supported by `pi5servo` |
| **Integration** | OpenClaw + Telegram validated |

### Software Stack

| Layer | Technology |
|-------|------------|
| **Python workspace** | `uv` + editable packages |
| **Robot integration** | `ninjaclawbot` |
| **Servo library** | `pi5servo` |
| **Display library** | `pi5disp` |
| **Buzzer library** | `pi5buzzer` |
| **Distance sensor library** | `pi5vl53l0x` |
| **Agent integration** | OpenClaw plugin + workspace `BOOT.md` / `AGENTS.md` |

## Key Features

### Modular hardware libraries

- `pi5servo`: servo calibration, motion assets, and interactive `servo-tool`
- `pi5disp`: display initialization, rendering, and interactive `display-tool`
- `pi5buzzer`: tone and sound playback with `buzzer-tool`
- `pi5vl53l0x`: VL53L0X sensor access and `sensor-tool`

### Integrated robot layer

- structured robot actions through `ninjaclawbot`
- saved expressions and movement assets
- interactive `expression-tool` and `movement-tool`
- reply-state driven expressions such as `greeting`, `thinking`, `success`, and `sleepy`
- health checks and deployment diagnostics

### OpenClaw deployment

- persistent bridge between OpenClaw and the robot runtime
- startup greeting driven by `boot-md` and workspace `BOOT.md`
- normal text reply plus robot expression on each validated Telegram turn
- sleepy shutdown and display power-off when OpenClaw stops
- `ninjaclawbot_diagnostics` for bridge, deployment, and readiness checks

## Quick Start

```bash
# Clone the repository
git clone https://github.com/Nilcreator/NinjaClawBot.git
cd NinjaClawBot

# Install the workspace
uv sync --extra dev

# Check the integrated robot layer
uv run ninjaclawbot health-check

# Open the guided hardware tools
uv run pi5servo servo-tool
uv run pi5disp display-tool
uv run pi5buzzer buzzer-tool
uv run pi5vl53l0x sensor-tool
```

For the full Raspberry Pi build, OpenClaw setup, `openclaw.json` patching, and Telegram validation, follow [InstallationGuide.md](InstallationGuide.md).

## Documentation

| Document | Description |
|----------|-------------|
| [InstallationGuide.md](InstallationGuide.md) | Step-by-step Raspberry Pi and OpenClaw build guide |
| [DevelopmentGuide.md](DevelopmentGuide.md) | Developer reference, architecture, commands, and workflow |
| [ninjaclawbot/README.md](ninjaclawbot/README.md) | Integrated robot layer usage |
| [pi5servo/README.md](pi5servo/README.md) | Servo setup and calibration |
| [pi5disp/README.md](pi5disp/README.md) | Display wiring and setup |
| [pi5buzzer/README.md](pi5buzzer/README.md) | Buzzer setup and sounds |
| [pi5vl53l0x/README.md](pi5vl53l0x/README.md) | Distance sensor setup |
| [backup/README.md](backup/README.md) | Archived plans and logs |

## Current Status

**Status:** Stage 2 OpenClaw integration implemented and validated on Raspberry Pi 5

Validated outcomes:

- persistent bridge reuse
- startup greeting
- idle / thinking / reply / sleepy lifecycle
- Telegram text reply plus robot reaction
- deployment diagnostics through `ninjaclawbot_diagnostics`

## License

This project is licensed under the **MIT License**.

**Copyright (c) 2026 Chihkuang Chang**

---

<a id="japanese"></a>

# 日本語

## プロジェクト概要

**NinjaClawBot** は、Raspberry Pi 5 向けに構成されたロボット制御ワークスペースです。小さく再利用しやすいハードウェアライブラリと、それらをまとめる統合レイヤー `ninjaclawbot` で構成されています。

このプロジェクトは、次の順番で使うことを前提にしています。

- まず各ハードウェアを単体ライブラリで確認する
- 次に `ninjaclawbot` で統合する
- 最後に OpenClaw と接続して会話型ロボットとして動かす

現在の検証済みビルドでは、次の流れが動作します。

1. OpenClaw 起動
2. ロボットが起動あいさつを表示
3. 待機中はアイドル表情
4. ユーザーメッセージでロボットが反応
5. 返信内容に合った表情を表示
6. Telegram には通常のテキスト返信も届く
7. OpenClaw 停止時に sleepy 表情を出して画面を消灯

## ロボット構成

### ハードウェア

| 構成 | 現在の検証方向 |
|------|----------------|
| **本体** | Raspberry Pi 5 |
| **表示** | `pi5disp` 対応の SPI ディスプレイ |
| **距離センサー** | `pi5vl53l0x` 対応の VL53L0X |
| **音** | `pi5buzzer` 対応のパッシブブザー |
| **動作** | `pi5servo` 対応のサーボ |
| **連携** | OpenClaw + Telegram 検証済み |

### ソフトウェアスタック

| レイヤー | 技術 |
|---------|------|
| **Python ワークスペース** | `uv` + editable packages |
| **統合レイヤー** | `ninjaclawbot` |
| **サーボ** | `pi5servo` |
| **ディスプレイ** | `pi5disp` |
| **ブザー** | `pi5buzzer` |
| **距離センサー** | `pi5vl53l0x` |
| **エージェント連携** | OpenClaw plugin + `BOOT.md` / `AGENTS.md` |

## 主な機能

### モジュール式ハードウェアライブラリ

- `pi5servo`: キャリブレーション、モーション制御、`servo-tool`
- `pi5disp`: 画面初期化、描画、`display-tool`
- `pi5buzzer`: 音再生、`buzzer-tool`
- `pi5vl53l0x`: センサー読み取り、`sensor-tool`

### 統合ロボットレイヤー

- `ninjaclawbot` による統合アクション
- 表情とモーションのアセット
- `expression-tool` と `movement-tool`
- `greeting`、`thinking`、`success`、`sleepy` などの返信状態ベース表情
- ヘルスチェックと診断出力

### OpenClaw 連携

- 永続ブリッジによる OpenClaw とロボットの接続
- `boot-md` とワークスペース `BOOT.md` による起動あいさつ
- Telegram への通常返信とロボット表情の両立
- 停止時の sleepy シャットダウン
- `ninjaclawbot_diagnostics` による状態確認

## クイックスタート

```bash
git clone https://github.com/Nilcreator/NinjaClawBot.git
cd NinjaClawBot
uv sync --extra dev
uv run ninjaclawbot health-check
uv run pi5servo servo-tool
uv run pi5disp display-tool
uv run pi5buzzer buzzer-tool
uv run pi5vl53l0x sensor-tool
```

Raspberry Pi の初期構築、OpenClaw 接続、`openclaw.json` の安全な更新、Telegram 検証は [InstallationGuide.md](InstallationGuide.md) を参照してください。

## ドキュメント

| ドキュメント | 内容 |
|-------------|------|
| [InstallationGuide.md](InstallationGuide.md) | Raspberry Pi と OpenClaw の導入手順 |
| [DevelopmentGuide.md](DevelopmentGuide.md) | 開発者向け構成資料とコマンド一覧 |
| [ninjaclawbot/README.md](ninjaclawbot/README.md) | 統合レイヤーの使い方 |
| [pi5servo/README.md](pi5servo/README.md) | サーボ設定 |
| [pi5disp/README.md](pi5disp/README.md) | ディスプレイ設定 |
| [pi5buzzer/README.md](pi5buzzer/README.md) | ブザー設定 |
| [pi5vl53l0x/README.md](pi5vl53l0x/README.md) | 距離センサー設定 |
| [backup/README.md](backup/README.md) | 過去計画と履歴 |

## 現在のステータス

**ステータス:** Stage 2 OpenClaw 連携は Raspberry Pi 5 上で実装・検証済み

検証済み項目:

- 永続ブリッジ
- 起動あいさつ
- idle / thinking / reply / sleepy のライフサイクル
- Telegram テキスト返信とロボット反応
- `ninjaclawbot_diagnostics`

## ライセンス

本プロジェクトは **MIT License** で公開されています。

**Copyright (c) 2026 Chihkuang Chang**

---

<a id="traditional-chinese"></a>

# 繁體中文

## 專案概要

**NinjaClawBot** 是以 Raspberry Pi 5 為核心的機器人控制工作區。它由幾個可獨立測試的硬體函式庫，以及一個整合層 `ninjaclawbot` 組成。

建議的使用流程是：

- 先個別測試每個硬體模組
- 再用 `ninjaclawbot` 把它們整合起來
- 最後接上 OpenClaw，讓機器人透過聊天介面工作

目前已驗證的版本支援以下流程：

1. OpenClaw 啟動
2. 機器人顯示開機問候
3. 等待時保持 idle 表情
4. 使用者傳送訊息後機器人先反應
5. 回答時顯示對應情緒表情
6. Telegram 仍會收到正常文字回覆
7. OpenClaw 停止時顯示 sleepy 並關閉螢幕

## 機器人配置

### 硬體

| 元件 | 目前驗證方向 |
|------|--------------|
| **主機** | Raspberry Pi 5 |
| **顯示器** | `pi5disp` 支援的 SPI 顯示器 |
| **距離感測器** | `pi5vl53l0x` 支援的 VL53L0X |
| **聲音** | `pi5buzzer` 支援的被動式蜂鳴器 |
| **動作** | `pi5servo` 支援的伺服馬達 |
| **整合** | 已驗證 OpenClaw + Telegram |

### 軟體堆疊

| 層級 | 技術 |
|------|------|
| **Python 工作區** | `uv` + editable packages |
| **整合層** | `ninjaclawbot` |
| **伺服馬達** | `pi5servo` |
| **顯示器** | `pi5disp` |
| **蜂鳴器** | `pi5buzzer` |
| **距離感測器** | `pi5vl53l0x` |
| **代理整合** | OpenClaw plugin + `BOOT.md` / `AGENTS.md` |

## 主要功能

### 模組化硬體函式庫

- `pi5servo`: 校正、動作控制、`servo-tool`
- `pi5disp`: 顯示初始化、畫面測試、`display-tool`
- `pi5buzzer`: 聲音播放、`buzzer-tool`
- `pi5vl53l0x`: 感測器讀值、`sensor-tool`

### 整合式機器人層

- 透過 `ninjaclawbot` 執行整合動作
- 已保存的表情與動作資產
- `expression-tool` 與 `movement-tool`
- `greeting`、`thinking`、`success`、`sleepy` 等回覆狀態表情
- 健康檢查與診斷輸出

### OpenClaw 整合

- 透過持久橋接連接 OpenClaw 與機器人
- 以 `boot-md` 和工作區 `BOOT.md` 完成開機問候
- 每次 Telegram 回覆同時保留文字與機器人表情
- 停止時執行 sleepy 關機流程
- 透過 `ninjaclawbot_diagnostics` 檢查部署狀態

## 快速開始

```bash
git clone https://github.com/Nilcreator/NinjaClawBot.git
cd NinjaClawBot
uv sync --extra dev
uv run ninjaclawbot health-check
uv run pi5servo servo-tool
uv run pi5disp display-tool
uv run pi5buzzer buzzer-tool
uv run pi5vl53l0x sensor-tool
```

如果你要從零開始完成 Raspberry Pi、OpenClaw、`openclaw.json` 設定與 Telegram 驗證，請直接依照 [InstallationGuide.md](InstallationGuide.md)。

## 文件

| 文件 | 說明 |
|------|------|
| [InstallationGuide.md](InstallationGuide.md) | Raspberry Pi 與 OpenClaw 完整安裝流程 |
| [DevelopmentGuide.md](DevelopmentGuide.md) | 開發者用架構與指令說明 |
| [ninjaclawbot/README.md](ninjaclawbot/README.md) | 整合層使用方式 |
| [pi5servo/README.md](pi5servo/README.md) | 伺服馬達設定 |
| [pi5disp/README.md](pi5disp/README.md) | 顯示器設定 |
| [pi5buzzer/README.md](pi5buzzer/README.md) | 蜂鳴器設定 |
| [pi5vl53l0x/README.md](pi5vl53l0x/README.md) | 距離感測器設定 |
| [backup/README.md](backup/README.md) | 歷史規劃與記錄 |

## 目前狀態

**狀態:** Stage 2 OpenClaw 整合已在 Raspberry Pi 5 上完成並驗證

已驗證內容:

- 持久橋接
- 開機問候
- idle / thinking / reply / sleepy 生命週期
- Telegram 文字回覆與機器人反應
- `ninjaclawbot_diagnostics`

## 授權

本專案採用 **MIT License**。

**Copyright (c) 2026 Chihkuang Chang**
