# JRA-VAN DataLab Python実装

JRA-VAN DataLab SDK Ver4.9.0.2をベースにしたPython実装です。

## 必要条件

- Windows OS（JV-LinkはWindows専用）
- Python 3.8以上（32bit版推奨）
- JRA-VAN DataLab契約（月額2,090円）

## セットアップ

### 1. JV-Link登録

SDKフォルダのJV-Link.exeを管理者権限で実行：

```bash
cd "JRA-VAN Data Lab. SDK Ver4.9.0.2\JV-Link"
JV-Link.exe /regserver
```

### 2. Python環境構築

```bash
# 仮想環境作成
python -m venv .venv

# 仮想環境有効化
.venv\Scripts\activate

# パッケージインストール（基本）
pip install pywin32

# パッケージインストール（全機能）
pip install -r requirements.txt
```

## 使用方法

### 接続テスト

```bash
python main_jra_van.py --test
```

### 初回セットアップ

```bash
python main_jra_van.py --setup
```
※大量データダウンロードのため数時間かかります

### データ更新（日次実行）

```bash
python main_jra_van.py --update
```

### リアルタイムデータ取得

```bash
python main_jra_van.py --realtime
```

### 統計情報表示

```bash
python main_jra_van.py --stats
```

## ファイル構成

```
StableFormer/
├── jvlink_client.py      # JV-Link COMラッパー
├── jvdata_parser.py      # データパーサー
├── jvdata_manager.py     # データ管理
├── main_jra_van.py       # メインプログラム
├── requirements.txt      # 依存パッケージ
├── jravan.db            # SQLiteデータベース（自動生成）
└── jvdata/              # JV-Dataファイル保存先（自動生成）
```

## データベース構造

- **races**: レース情報
- **results**: 馬毎レース結果
- **horses**: 競走馬マスタ
- **odds**: オッズ情報
- **weights**: 馬体重
- **schedules**: 開催スケジュール

## Python APIサンプル

```python
from jvdata_manager import JVDataManager

# データマネージャー初期化
manager = JVDataManager("jravan.db")

# セットアップ
manager.download_setup_data("RACE")

# 更新
manager.update_data()

# リアルタイム
manager.get_realtime_data("0B15")  # 馬体重

# 終了
manager.close()
```

## トラブルシューティング

### エラー: -211（サービスキー認証エラー）

1. JRA-VAN DataLab契約確認
2. JV-Link.exe登録確認
3. サービスキー有効期限確認

### 64bit Pythonで使用する場合

レジストリ編集でDLLサロゲート設定が必要（管理者権限）

### 文字化け

Shift-JISエンコーディングの問題。パーサーでerrors='ignore'設定済み

## ライセンス

JRA-VAN DataLabの利用規約に準じます。

## お問い合わせ

StableFormerプロジェクト

---
最終更新: 2025-08-28