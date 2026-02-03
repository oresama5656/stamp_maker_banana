# LINE Stamp Maker Tools

LINEスタンプ制作を効率化するためのPythonツールセットです。
スタンプ画像の分割、背景透過、フチ除去、トリミングを自動化します。

## 必要な環境

- Python 3.10以上
- 必要なライブラリのインストール:
  ```bash
  pip install -r requirements.txt
  ```

## 収録ツール

### 1. 高機能スタンプ分割ツール (`stamp_splitter_v2.py`)
$4 \times 2$ のグリッドで並んだスタンプシートを8個の画像に分割し、背景を透過します。
OpenCVを使用し、高速かつ高品質な処理（フチ除去）を行います。

- **機能**:
  - 4x2分割 (長方形) / 3x3分割 (正方形・デフォルト) / 4x4分割 (正方形・オプション)
  - 自動判別機能（アスペクト比で判定、正方形は3x3がデフォルト）
  - 背景色自動検出（左上・右上から検出、マゼンタ以外も対応）
  - フチ（フリンジ）除去機能
- **使い方**:
  1. `input` フォルダにスタンプシート画像を入れます。
  2. 実行: `python stamp_splitter_v2.py`
  3. `output_v2` フォルダに出力されます。
- **オプション**:
  - `--tolerance`: 色の許容範囲（デフォルト: 50）
  - `--erosion`: フチ除去の強さ（デフォルト: 1）
  - `--grid`: `auto` (デフォルト), `4x2`, `3x3`, `4x4`

### 2. 背景透過ツール (`background_remover.py`)
個別の画像の背景を透過します。

- **機能**:
  - **Flood Fill (デフォルト)**: 左上・右上から背景を自動認識して透過。
  - **Auto Color**: 左上・右上の色と同じ色を画像全体から削除。
  - **Color Key**: 指定した色を削除。
- **使い方**:
  1. `input_remover` フォルダに画像を入れます。
  2. 実行: `python background_remover.py`
  3. `output_remover` フォルダに出力されます。
- **オプション**:
  - `--mode`: `flood` (推奨), `auto_color`, `color`

### 3. 自動トリミングツール (`auto_trimmer.py`)
透過画像の余白を自動でカットし、キャラクターサイズに合わせます。

- **機能**:
  - 透明部分を認識してクロップ
  - パディング（余白）の追加
- **使い方**:
  1. `input_trim` フォルダに画像を入れます。
  2. 実行: `python auto_trimmer.py`
  3. `output_trim` フォルダに出力されます。
- **オプション**:
  - `--padding`: 余白サイズ（px）（デフォルト: 10）

### 4. スタンプ整形ツール (`line_stamp_formatter.py`)
LINEスタンプの規格（最大370x320px、偶数サイズ）に合わせてリサイズ・配置し、メイン・タブ画像を生成します。

- **機能**:
  - 370x320pxへのリサイズ（アスペクト比保持、余白10px）
  - `main.png` (240x240) の自動生成
  - `tab.png` (96x74) の自動生成
  - 連番リネーム (01.png ~)
- **使い方**:
  1. `input_format` フォルダに画像を入れます。
  2. 実行: `python line_stamp_formatter.py`
  3. `output_format` フォルダに出力されます。

### 5. 統合GUI (`gui.py`)
全てのツールを統合したGUIアプリケーションです。

- **機能**:
  - ドラッグ＆ドロップでのフォルダ入力
  - **出力フォルダの指定**
  - 各工程（分割、透過、トリミング、整形）の一括実行
  - **背景透過時のフチ除去（Erosion）設定**
  - 進捗ログ表示
- **使い方**:
  1. `python gui.py` を実行します。
  2. 処理したい画像が入ったフォルダをウィンドウにドラッグ＆ドロップします。
  3. 出力先フォルダを選択します（デフォルト: `output_final`）。
  4. 必要な処理にチェックを入れ、オプションを設定します。
  5. 「RUN PROCESS」ボタンを押します。

### 2. 背景透過ツール (`background_remover.py`)
個別の画像の背景を透過します。OpenCVを使用し、フチ除去も可能です。

- **機能**:
  - 3つのモード: `flood` (左上・右上から), `auto_color` (自動色検出), `color` (指定色)
  - フチ除去 (Erosion)
- **オプション**:
  - `--mode`: `flood`, `auto_color`, `color`
  - `--tolerance`: 色の許容範囲
  - `--erosion`: フチ除去の強さ (0-5)

## フォルダ構成

```
stamp_maker_banana/
├── input/              # 分割ツールの入力
├── output_v2/          # 分割ツールの出力
├── input_remover/      # 背景透過ツールの入力
├── output_remover/     # 背景透過ツールの出力
├── input_trim/         # トリミングツールの入力
├── output_trim/        # トリミングツールの出力
├── stamp_splitter_v2.py
├── background_remover.py
├── auto_trimmer.py
├── requirements.txt
└── README.md
```
