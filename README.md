# Video Slide Extractor

動画からスライドの切り替わりを自動検出し、各スライドの最も鮮明なフレームを抽出してPDFとして出力するCLIツールです。

パワーポイント等のプレゼンテーションをカメラで撮影した動画に対応しており、手ブレやノイズがある環境でもロバストにスライドを検出します。

## 処理構成

```
動画ファイル
  │
  ▼
[1] フレームサンプリング（一定間隔でフレームを取得）
  │
  ▼
[2] 前処理（グレースケール変換 + ガウシアンブラー）
  │
  ▼
[3] SSIM比較（連続フレーム間の構造的類似度を計算）
  │
  ▼
[4] スライド切り替わり検出（SSIM閾値 + デバウンス処理）
  │
  ▼
[5] ベストフレーム選択（各区間でLaplacian分散が最大のフレーム）
  │
  ▼
[6] 出力（PDF生成 / PNG画像保存）
```

### ファイル構成

| ファイル | 説明 |
|---|---|
| `main.py` | CLIエントリポイント（argparseによる引数処理） |
| `extractor.py` | スライド検出・抽出・保存ロジック |
| `requirements.txt` | 依存パッケージ一覧 |

### 主要ライブラリ

- **OpenCV** — 動画読み込み・フレーム処理
- **scikit-image** — SSIM（構造的類似度）計算
- **NumPy** — 数値計算
- **Pillow** — PDF生成
- **tqdm** — 進捗バー表示

## 動作要件

- Python 3.14 以上（推奨）/ 3.9 以上
- Git

## セットアップ

### macOS

```bash
git clone https://github.com/ranranpon-cloud/video-slide-extractor.git
cd video-slide-extractor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Windows

1. **Python のインストール**
   - https://www.python.org/downloads/ から Python 3.9 以上をダウンロード
   - インストール時に **「Add Python to PATH」にチェック** を入れる

2. **Git のインストール**
   - https://git-scm.com/download/win からダウンロードしてインストール

3. **セットアップ**

```cmd
git clone https://github.com/ranranpon-cloud/video-slide-extractor.git
cd video-slide-extractor
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

> **Note:** Windows では `python3` の代わりに `python`、`source venv/bin/activate` の代わりに `venv\Scripts\activate` を使用します。

## 利用方法

### 基本

```bash
python main.py <入力動画> -o <出力PDF>
```

### オプション一覧

| オプション | デフォルト | 説明 |
|---|---|---|
| `-o, --output` | `output.pdf` | 出力PDFファイルのパス |
| `--threshold` | `0.85` | SSIM閾値。高いほど感度が上がる |
| `--interval` | `0.5` | フレームサンプリング間隔（秒） |
| `--min-duration` | `2.0` | スライドの最低表示時間（秒） |
| `--rotate` | `0` | 出力画像の回転角度（0 / 90 / 180 / 270） |
| `--save-images` | - | 個別のPNG画像も保存する |
| `--debug` | - | SSIMグラフを出力（要 matplotlib） |

### 実行例

```bash
# デフォルト設定で実行
python main.py video.mov -o slides.pdf

# 高感度設定 + 右90度回転（横向き撮影の縦書き文書向け）
python main.py video.mov -o slides.pdf --threshold 0.93 --min-duration 0.3 --rotate 90

# 個別画像も保存
python main.py video.mov -o slides.pdf --save-images
```

### パラメータ調整のヒント

- **スライドが少なすぎる場合** → `--threshold` を上げる（例: 0.90 → 0.93）、`--min-duration` を下げる
- **スライドが多すぎる場合** → `--threshold` を下げる（例: 0.85 → 0.80）、`--min-duration` を上げる
- **ページめくりが速い動画** → `--min-duration 0.3` 程度に設定
