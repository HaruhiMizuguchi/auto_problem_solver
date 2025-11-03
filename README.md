# Auto Problem Solver

画面に表示された問題をOCRで読み取り、LLM（OpenAIまたはGemini）を使用して自動的に解答を生成するツールです。

## 機能

- **画面キャプチャ**: マウスで画面の任意の領域を選択してキャプチャ
- **OCR処理**: Tesseract OCRを使用して画像から問題文と選択肢を抽出
- **LLM解答**: OpenAIまたはGeminiを使用して問題を解析し、解答と根拠を生成
- **GUI操作**: シンプルなTkinter GUIによる操作
- **MCPサーバー**: Model Context Protocolサーバーとしても動作可能

## 必要な環境

- Python 3.7以上
- Tesseract OCR（システムにインストール済みである必要があります）
- OpenAI APIキーまたはGemini APIキー

## インストール

1. リポジトリをクローンまたはダウンロードします。

2. 依存パッケージをインストールします：
```bash
pip install -r requirements.txt
```

3. Tesseract OCRをインストールします：
   - **Windows**: [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) からインストール
   - **macOS**: `brew install tesseract`
   - **Linux**: `sudo apt-get install tesseract-ocr`（Ubuntu/Debianの場合）

4. 環境変数を設定します。プロジェクトルートに `.env` ファイルを作成し、以下の内容を記述します：

```env
# LLMプロバイダーの選択（'openai' または 'gemini'）
LLM_PROVIDER=openai

# OpenAIを使用する場合
OPENAI_API_KEY=your_openai_api_key_here

# Geminiを使用する場合
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash

# OCR言語設定（デフォルト: 'eng'、日本語の場合は 'jpn'）
OCR_LANG=eng
```

**注意**: WindowsでTesseractのパスが通っていない場合は、`ocr_solver.py`の26行目のコメントを解除してパスを設定してください。

## 使い方

### GUIアプリケーションとして使用

1. メインアプリケーションを起動します：
```bash
python main.py
```

2. 表示されたウィンドウで「画面の問題を解く（範囲選択）」ボタンをクリックします。

3. 画面が半透明の黒いオーバーレイで覆われます。マウスでドラッグして問題が含まれる領域を選択します。

4. マウスを離すと、選択した領域がキャプチャされ、OCR処理とLLM解答が実行されます。

5. 結果がメッセージボックスに表示されます：
   - **回答**: 選択肢のラベル（A、B、C、Dなど）
   - **根拠**: 100〜300字程度の解答根拠

### MCPサーバーとして使用

MCP（Model Context Protocol）サーバーとしても動作します。Base64エンコードされたPNG画像を受け取り、解答を返します。

```bash
python mcp_server.py
```

#### MCPツール仕様

- **ツール名**: `solve_from_png_base64`
- **説明**: PNG(Base64)画像からOCR→LLMで回答と根拠を返す
- **入力パラメータ**:
  - `png_base64` (string): Base64エンコードされたPNG画像データ

#### 使用例

MCPクライアントから以下のように呼び出します：

```json
{
  "type": "tool_call",
  "name": "solve_from_png_base64",
  "arguments": {
    "png_base64": "iVBORw0KGgoAAAANSUhEUgAA..."
  }
}
```

## 対応している問題形式

- 問題文と選択肢が明確に分かれている形式
- 選択肢のラベル形式:
  - 日本語: ア、イ、ウ、エ
  - アルファベット: A、B、C、D、a、b、c、d
  - 数字: 1、2、3、4
  - 丸数字: ①、②、③、④

## プロジェクト構成

```
auto_problem_solver/
├── main.py              # GUIアプリケーションのメインファイル
├── ui_capture.py        # 画面領域キャプチャ機能
├── ocr_solver.py        # OCR処理とLLM解答機能
├── mcp_server.py        # MCPサーバー実装
├── requirements.txt     # 依存パッケージ一覧
└── README.md           # このファイル
```

## 主要なモジュール

### `main.py`
GUIアプリケーションのエントリーポイント。Tkinterを使用したシンプルなインターフェースを提供します。

### `ui_capture.py`
画面の領域選択とキャプチャ機能を実装。全画面オーバーレイでマウスドラッグによる領域選択を可能にします。

### `ocr_solver.py`
- OCR処理: Tesseractを使用して画像からテキストを抽出
- 問題解析: 正規表現を使用して問題文と選択肢を分離
- LLM解答: OpenAIまたはGeminiを使用して解答を生成

### `mcp_server.py`
MCPプロトコルに準拠したサーバー実装。標準入出力を通じてJSONで通信します。

## トラブルシューティング

### OCRが正しく動作しない場合
- Tesseract OCRが正しくインストールされているか確認してください
- Windowsでは、`ocr_solver.py`の26行目でTesseractのパスを明示的に設定してください
- 画像の解像度が低い場合は、OCR精度が低下する可能性があります

### LLM APIエラーが発生する場合
- `.env`ファイルにAPIキーが正しく設定されているか確認してください
- `LLM_PROVIDER`が`openai`または`gemini`のいずれかに設定されているか確認してください
- APIキーに十分なクレジットがあるか確認してください

### 選択肢が正しく認識されない場合
- 画像の品質を確認してください（文字が鮮明に写っているか）
- OCR_LANG環境変数を適切な言語に設定してください（日本語の場合は`jpn`）

## ライセンス

このプロジェクトのライセンス情報については、各依存パッケージのライセンスを確認してください。

## 注意事項

- このツールは学習支援を目的としており、試験の不正行為に使用しないでください
- APIキーは他人と共有しないでください
- LLMの解答は必ずしも正しいとは限りません。自己責任で使用してください

