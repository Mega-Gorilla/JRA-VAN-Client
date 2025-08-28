# JRA-VAN Client セットアップガイド

## 📌 概要
JRA-VAN DataLabの競馬データをPython（64bit）から利用するためのセットアップガイドです。

## 🔧 事前準備

### JV-Link.exeのダウンロード（必須）

1. [JRA-VAN SDKダウンロードページ](https://jra-van.jp/dlb/#tab5)にアクセス
2. 最新版のSDKをダウンロード
3. ZIPを解凍し、`JV-Link\JV-Link.exe`を`setup/`フォルダにコピー

詳細は [setup/DOWNLOAD_JVLINK.md](setup/DOWNLOAD_JVLINK.md) を参照

## 🎯 クイックスタート（推奨）

### 方法1: 自動セットアップ（最も簡单）

**管理者権限**でコマンドプロンプトを開き、以下を実行：

```bash
python install_windows.py
```

これですべてが自動的に設定されます。

### 方法2: 手動セットアップ

#### 1. 仮想環境作成と依存パッケージインストール

```bash
# 仮想環境作成
python -m venv venv

# アクティベート
venv\Scripts\activate

# pywin32インストール
pip install pywin32

# pywin32のポストインストール
python venv\Scripts\pywin32_postinstall.py -install
```

#### 2. JV-Link登録（管理者権限必要）

```bash
cd setup
# JV-Link.exeが存在することを確認
dir JV-Link.exe

# 登録実行
JV-Link.exe /regserver
```

#### 3. レジストリ設定（64bit対応）

方法A: 自動生成スクリプトを使用
```bash
cd setup
python create_registry.py
reg import jvlink_localserver.reg
```

方法B: バッチファイルを使用（管理者権限必要）
- `setup\apply_registry.bat` を右クリックして「管理者として実行」

**注意**: レジストリファイルはJV-Link.exeのパスに基づいて自動生成されます

#### 4. 接続テスト

```bash
.\venv\Scripts\python.exe main.py --test
```

## ⚠️ 重要事項

### 初回実行時
- **JV-Linkのセットアップ画面**が表示されます
- **JRA-VANのサービスキー**を入力してください
- **データ保存先フォルダ**を指定してください

### 必要な権限
- レジストリ編集には**管理者権限**が必要です
- セットアップ後は通常権限で実行可能です

## 🔧 トラブルシューティング

### エラー: クラスが登録されていません

**原因**: COMオブジェクトが未登録またはレジストリ設定が不完全

**解決方法**:
1. 管理者権限でコマンドプロンプトを開く
2. 以下を順番に実行：
```bash
cd setup
JV-Link.exe /regserver
reg import jvlink_localserver.reg
```

### エラー: -211 (サービスキー認証エラー)

**原因**: JRA-VAN DataLabの契約がないか、サービスキーが未設定

**解決方法**:
1. [JRA-VAN公式サイト](https://jra-van.jp/)で契約（月額2,090円）
2. 初回実行時にサービスキーを入力

### エラー: win32com not found

**原因**: pywin32が未インストール

**解決方法**:
```bash
.\venv\Scripts\pip.exe install pywin32
.\venv\Scripts\python.exe .\venv\Scripts\pywin32_postinstall.py -install
```

## 📁 ファイル構成

### 必須ファイル
- `setup/JV-Link.exe` - JRA-VAN提供のCOMサーバー（公式サイトからダウンロード必須）
- `setup/jvlink_localserver.reg` - 64bit対応レジストリ設定
- `install_windows.py` - Windows用自動インストーラー
- `pyproject.toml` - Pythonパッケージ設定

### 主要スクリプト
- `main.py` - メインプログラム
- `jravan/client.py` - JV-Link COMラッパー
- `jravan/manager.py` - データ管理
- `jravan/parser.py` - データパーサー

## 📊 使い方

### 基本コマンド

```bash
# 接続テスト
.\venv\Scripts\python.exe main.py --test

# 初回データ取得（数時間かかります）
.\venv\Scripts\python.exe main.py --setup

# データ更新
.\venv\Scripts\python.exe main.py --update

# リアルタイムデータ取得
.\venv\Scripts\python.exe main.py --realtime

# 統計情報表示
.\venv\Scripts\python.exe main.py --stats
```

## 🔍 技術詳細

### 64bit Python対応について

JV-Link.exeは32bitアプリケーションですが、以下の設定により64bit Pythonから利用可能：

1. **LocalServer32設定**: EXEベースのCOMサーバーとして登録
2. **DLL Surrogate設定**: プロセス外実行を有効化

### CLSID情報
- **ProgID**: `JVDTLab.JVLink`
- **CLSID**: `{2AB1774D-0C41-11D7-916F-0003479BEB3F}`

この値は全環境で共通です。

## 📝 更新履歴

- **2025-08-28**: 初版作成
- 64bit完全対応
- 自動セットアップスクリプト追加
- 32bit Python不要の実装

## 💡 ヒント

- セットアップは一度だけ実行すればOK
- JV-Link再インストール時は再度セットアップが必要
- データは`jravan.db`（SQLite）に保存されます

## 📮 サポート

問題が発生した場合：
1. このガイドのトラブルシューティングを確認
2. `jravan.log`のエラーメッセージを確認
3. [GitHub Issues](https://github.com/Mega-Gorilla/jra-van-client/issues)で報告