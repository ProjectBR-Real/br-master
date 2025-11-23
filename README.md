# Real Buckshot Roulette - Core Logic

これは、ビデオゲーム『Buckshot Roulette』を物理的なデバイスで再現するためのコアロジックを提供する Python プロジェクトです。

## 主な機能

- **複数ゲームの同時管理**: `gameId` を用いて、複数のゲームセッションを同時に進行・管理できます。
- **柔軟なプレイヤー人数**: プレイヤーを ID で管理し、2 人以上のプレイにも対応可能な設計です。
- **データ駆動のアイテムシステム**: アイテムの効果が関数として定義されており、新しいアイテムの追加や変更が容易です。
- **外部連携インターフェース**: 物理デバイス（ショットガン、RFID リーダー等）との通信を想定した窓口(`interface.py`)を設け、ロジックとハードウェアの連携を容易にします。
- **設定の外部化**: ゲームのルール（ライフ、弾数、アイテム出現率など）を`config.json`で管理し、コードを変更せずにゲームバランスを調整できます。

## プロジェクト構成

```
br-master/
├── game.py              # 1ゲームの進行と状態を管理するメインクラス
├── game_manager.py      # 複数のゲームインスタンスを管理する司令塔
├── player.py            # プレイヤーの状態を管理するクラス
├── shotgun.py           # ショットガンの弾の状態を管理するクラス
├── items.py             # アイテムのデータと効果を定義
├── logic.py             # ラウンドごとの弾数計算など、ゲームの補助ロジック
├── interface.py         # 外部ハードウェアとの通信を担うインターフェース
├── game_config.py       # config.jsonを読み込む設定クラス
├── config.json          # ゲームの基本設定ファイル
├── main.py              # プログラムの実行エントリーポイント
├── utils.py             # ゲーム状態の表示など、補助的な関数
├── mock_inputs.py       # ターミナルからの入力を処理
└── README.md            # このファイル
```

## 設定 (`config.json`)

このプロジェクトでは、ゲームの主要なルールを `config.json` ファイルで定義しています。これにより、プログラミングの知識がなくてもゲームのバランスを調整できます。

- **`game_rules`**:
  - `initial_lives`: 初期ライフ数。
  - `max_lives`: 最大ライフ数。
- **`shell_counts_by_round`**:
  - ラウンドごとに装填される「実弾」と「空砲」の数を定義します。
  - `default` は、特定のラウンド設定がない場合に適用されます。
- **`item_distribution`**:
  - `items_per_round`: ラウンドごとに各プレイヤーに配布されるアイテムの数。
  - `item_probabilities`: 各アイテムの出現確率（重み）。合計値に対する割合で抽選されます。

## 実行方法

このプロジェクトは `uv` を使って実行することを推奨します。`uv` がインストールされていれば、リポジトリに含まれるスクリプトを実行するだけで、必要なライブラリのインストールとプログラムの起動が自動的に行われます。

```bash
uv venv
.venv\Scripts\activate
# Linux: source .venv/bin/activate
uv pip install -r requirements.txt
uv run python3 main.py
deactivate
```
