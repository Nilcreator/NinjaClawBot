# NinjaClawBot

## Quick Links

- [English](#english)
- [日本語](#日本語)
- [繁體中文](#繁體中文)
- [Installation Guide](InstallationGuide.md)
- [Development Guide](DevelopmentGuide.md)
- Library READMEs:
  - [ninjaclawbot](ninjaclawbot/README.md)
  - [pi5servo](pi5servo/README.md)
  - [pi5disp](pi5disp/README.md)
  - [pi5buzzer](pi5buzzer/README.md)
  - [pi5vl53l0x](pi5vl53l0x/README.md)
- OpenClaw plugin:
  - [Plugin folder](integrations/openclaw/ninjaclawbot-plugin)
  - [Plugin skill](integrations/openclaw/ninjaclawbot-plugin/skills/ninjaclawbot_control/SKILL.md)
- Archive:
  - [backup/README.md](backup/README.md)

---

## English

### What NinjaClawBot is

NinjaClawBot is a Raspberry Pi 5 robot software workspace.

It gives you:

- standalone Pi 5 hardware libraries for servo, buzzer, display, and distance sensor
- one integrated robot layer called `ninjaclawbot`
- an official OpenClaw plugin for chat-driven robot behavior
- guided setup tools so you can calibrate and test hardware step by step

The current validated build supports this real-world flow:

- OpenClaw starts
- the robot shows a startup greeting
- the robot waits in an idle face
- when the user sends a message, the robot reacts
- OpenClaw replies with both:
  - robot expression on Raspberry Pi
  - visible text reply in Telegram
- when OpenClaw stops, the robot shows a sleepy shutdown and powers the display off

### Main parts of the project

#### Standalone hardware libraries

- [pi5servo](pi5servo/README.md): servo control and calibration
- [pi5disp](pi5disp/README.md): SPI display driver and display tool
- [pi5buzzer](pi5buzzer/README.md): buzzer tones and emotion sounds
- [pi5vl53l0x](pi5vl53l0x/README.md): VL53L0X distance sensor driver and sensor tool

These can be tested on their own before you use the full robot layer.

#### Integrated robot layer

- [ninjaclawbot](ninjaclawbot/README.md)

This layer combines all hardware libraries into one robot-facing interface.

It provides:

- structured actions
- saved movement and expression assets
- `movement-tool`
- `expression-tool`
- reply-state based expressions such as `greeting`, `thinking`, `success`, and `sleepy`
- health checks and diagnostics-friendly output

#### OpenClaw integration

- [InstallationGuide.md](InstallationGuide.md)
- [DevelopmentGuide.md](DevelopmentGuide.md)
- [integrations/openclaw/ninjaclawbot-plugin](integrations/openclaw/ninjaclawbot-plugin)

The validated OpenClaw setup is hybrid:

- plugin-managed persistent bridge and shutdown
- `boot-md` plus workspace `BOOT.md` for startup greeting
- workspace `AGENTS.md`, skill enablement, and tool allowlist for reliable reply behavior

### Quick start

If you want to build your own robot from scratch:

1. Follow [InstallationGuide.md](InstallationGuide.md).
2. Use the guided tools:
   - `uv run pi5servo servo-tool`
   - `uv run pi5buzzer buzzer-tool`
   - `uv run pi5disp display-tool`
   - `uv run pi5vl53l0x sensor-tool`
3. Test the integrated layer:
   - `uv run ninjaclawbot health-check`
   - `uv run ninjaclawbot expression-tool`
   - `uv run ninjaclawbot movement-tool`
4. Connect OpenClaw and run the final validation steps in the installation guide.

### Where to read next

- New builder or operator:
  - [InstallationGuide.md](InstallationGuide.md)
- Developer working on code:
  - [DevelopmentGuide.md](DevelopmentGuide.md)
- Working on one hardware library only:
  - [pi5servo/README.md](pi5servo/README.md)
  - [pi5disp/README.md](pi5disp/README.md)
  - [pi5buzzer/README.md](pi5buzzer/README.md)
  - [pi5vl53l0x/README.md](pi5vl53l0x/README.md)
- Need old planning or change history:
  - [backup/README.md](backup/README.md)

### Current status

The Stage 2 OpenClaw integration plan is implemented and validated on Raspberry Pi.

That includes:

- persistent bridge reuse
- startup greeting
- idle / thinking / reply / sleepy lifecycle
- reply-state driven robot expressions
- Telegram text reply plus robot reaction
- diagnostics through `ninjaclawbot_diagnostics`

---

## 日本語

### NinjaClawBot とは

NinjaClawBot は、Raspberry Pi 5 向けのロボット制御ワークスペースです。

このプロジェクトには、次のものが含まれます。

- サーボ、ブザー、表示ディスプレイ、距離センサー用の単体ライブラリ
- それらをまとめて扱う統合レイヤー `ninjaclawbot`
- OpenClaw 用の公式プラグイン
- 初心者でも順番に試せる対話型セットアップツール

現在の検証済みビルドでは、次の流れが動作します。

- OpenClaw を起動
- ロボットが起動あいさつを表示
- 待機中はアイドル表情
- ユーザーがメッセージを送るとロボットが反応
- OpenClaw は次の両方を返す
  - Raspberry Pi 上のロボット表情
  - Telegram 上の通常テキスト返信
- OpenClaw 停止時は sleepy 表情を表示してから画面を消灯

### プロジェクトの主な構成

#### 単体ハードウェアライブラリ

- [pi5servo](pi5servo/README.md): サーボ制御とキャリブレーション
- [pi5disp](pi5disp/README.md): SPI ディスプレイドライバ
- [pi5buzzer](pi5buzzer/README.md): ブザー音と感情サウンド
- [pi5vl53l0x](pi5vl53l0x/README.md): VL53L0X 距離センサー

#### 統合ロボットレイヤー

- [ninjaclawbot](ninjaclawbot/README.md)

この層は、各ライブラリをひとつのロボット制御インターフェースにまとめます。

主な機能:

- 構造化アクション
- モーションと表情アセット
- `movement-tool`
- `expression-tool`
- `greeting`、`thinking`、`success`、`sleepy` などの返信状態ベースの表情
- ヘルスチェックと診断出力

#### OpenClaw 連携

- [InstallationGuide.md](InstallationGuide.md)
- [DevelopmentGuide.md](DevelopmentGuide.md)
- [Plugin folder](integrations/openclaw/ninjaclawbot-plugin)

検証済みの OpenClaw 構成はハイブリッド方式です。

- プラグイン管理の永続ブリッジと停止処理
- 起動あいさつは `boot-md` とワークスペース `BOOT.md`
- 返信動作はワークスペース `AGENTS.md`、スキル有効化、ツール許可リストで安定化

### クイックスタート

自分で最初から構築したい場合:

1. [InstallationGuide.md](InstallationGuide.md) を順番に進める
2. 対話型ツールを使う
   - `uv run pi5servo servo-tool`
   - `uv run pi5buzzer buzzer-tool`
   - `uv run pi5disp display-tool`
   - `uv run pi5vl53l0x sensor-tool`
3. 統合レイヤーを確認する
   - `uv run ninjaclawbot health-check`
   - `uv run ninjaclawbot expression-tool`
   - `uv run ninjaclawbot movement-tool`
4. 最後に OpenClaw を接続して、インストールガイドの最終検証を行う

### 次に読むべき資料

- 組み立てや導入をしたい人:
  - [InstallationGuide.md](InstallationGuide.md)
- 開発者向け:
  - [DevelopmentGuide.md](DevelopmentGuide.md)
- 個別ライブラリだけを触りたい人:
  - [pi5servo/README.md](pi5servo/README.md)
  - [pi5disp/README.md](pi5disp/README.md)
  - [pi5buzzer/README.md](pi5buzzer/README.md)
  - [pi5vl53l0x/README.md](pi5vl53l0x/README.md)
- 過去の計画や履歴を見たい人:
  - [backup/README.md](backup/README.md)

### 現在の状態

Stage 2 の OpenClaw 連携計画は、Raspberry Pi 上で実装・検証済みです。

含まれる内容:

- 永続ブリッジの再利用
- 起動あいさつ
- idle / thinking / reply / sleepy のライフサイクル
- reply_state に基づくロボット表情
- Telegram テキスト返信とロボット反応の両立
- `ninjaclawbot_diagnostics` による診断

---

## 繁體中文

### NinjaClawBot 是什麼

NinjaClawBot 是一個為 Raspberry Pi 5 設計的機器人軟體工作區。

它包含：

- 可獨立使用的硬體函式庫，負責伺服馬達、蜂鳴器、顯示器與距離感測器
- 一個整合層 `ninjaclawbot`
- 一個給 OpenClaw 使用的官方外掛
- 讓初學者也能一步一步完成設定的互動式工具

目前已驗證的版本可以完成這樣的流程：

- 啟動 OpenClaw
- 機器人顯示啟動問候表情
- 等待時維持 idle 表情
- 使用者送出訊息後，機器人做出反應
- OpenClaw 同時回覆：
  - Raspberry Pi 上的機器人表情
  - Telegram 裡的正常文字回覆
- 停止 OpenClaw 時，機器人顯示 sleepy 表情，之後關閉螢幕

### 專案的主要組成

#### 獨立硬體函式庫

- [pi5servo](pi5servo/README.md): 伺服馬達控制與校正
- [pi5disp](pi5disp/README.md): SPI 顯示器驅動
- [pi5buzzer](pi5buzzer/README.md): 蜂鳴器音效與情緒聲音
- [pi5vl53l0x](pi5vl53l0x/README.md): VL53L0X 距離感測器

#### 整合機器人層

- [ninjaclawbot](ninjaclawbot/README.md)

這一層把所有硬體函式庫整合成一個統一的機器人控制介面。

主要功能：

- 結構化動作
- 動作與表情資產
- `movement-tool`
- `expression-tool`
- 依據回覆狀態使用的表情，例如 `greeting`、`thinking`、`success`、`sleepy`
- 健康檢查與診斷輸出

#### OpenClaw 整合

- [InstallationGuide.md](InstallationGuide.md)
- [DevelopmentGuide.md](DevelopmentGuide.md)
- [Plugin folder](integrations/openclaw/ninjaclawbot-plugin)

目前驗證成功的 OpenClaw 架構是混合模式：

- 由外掛管理的持久橋接程序與關閉流程
- 啟動問候由 `boot-md` 與工作區 `BOOT.md` 負責
- 回覆行為透過工作區 `AGENTS.md`、技能啟用與工具允許清單來穩定運作

### 快速開始

如果你想從零開始自己建立機器人：

1. 先按照 [InstallationGuide.md](InstallationGuide.md) 操作
2. 使用互動式工具完成設定
   - `uv run pi5servo servo-tool`
   - `uv run pi5buzzer buzzer-tool`
   - `uv run pi5disp display-tool`
   - `uv run pi5vl53l0x sensor-tool`
3. 測試整合層
   - `uv run ninjaclawbot health-check`
   - `uv run ninjaclawbot expression-tool`
   - `uv run ninjaclawbot movement-tool`
4. 最後接上 OpenClaw，依照安裝指南完成最終驗證

### 下一步建議閱讀

- 想要安裝與部署：
  - [InstallationGuide.md](InstallationGuide.md)
- 想要開發或修改程式：
  - [DevelopmentGuide.md](DevelopmentGuide.md)
- 只想查看單一硬體函式庫：
  - [pi5servo/README.md](pi5servo/README.md)
  - [pi5disp/README.md](pi5disp/README.md)
  - [pi5buzzer/README.md](pi5buzzer/README.md)
  - [pi5vl53l0x/README.md](pi5vl53l0x/README.md)
- 想查看舊的規劃與開發歷史：
  - [backup/README.md](backup/README.md)

### 目前狀態

Stage 2 的 OpenClaw 整合已經完成，並在 Raspberry Pi 上驗證通過。

包含：

- 持久橋接程序重用
- 啟動問候
- idle / thinking / reply / sleepy 生命週期
- 依 reply_state 驅動的機器人表情
- Telegram 文字回覆與機器人反應同時生效
- `ninjaclawbot_diagnostics` 診斷工具
