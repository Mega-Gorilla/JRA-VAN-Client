# jra-van-client

JRA-VAN DataLabから競馬データを円滑に取得するためのPythonパッケージ

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)](https://www.microsoft.com/windows)

## 📌 概要

`jra-van-client`は、JRA-VAN DataLabのJV-Link APIをPythonから簡単に利用できるようにするラッパーパッケージです。複雑なCOM操作を隠蔽し、Pythonらしいインターフェースで競馬データの取得・管理を実現します。

## ✨ 特徴

- 🚀 **簡単なセットアップ** - 数コマンドでインストール完了
- 🐍 **Pythonic API** - Python開発者に優しいインターフェース
- 📊 **自動データ管理** - SQLiteによる自動データベース構築
- 🔄 **差分更新対応** - 効率的なデータ更新
- ⚡ **リアルタイムデータ** - オッズ・馬体重等の速報データ対応
- 🛠️ **64bit Python対応** - 32bit/64bit両対応

## 📋 必要条件

- Windows OS (Windows 10/11)
- Python 3.8以上
- JRA-VAN DataLab契約（月額2,090円）
- JRA-VAN SDK Ver4.9.0.2

## 🚀 インストール

### 1. パッケージのインストール

```bash
# リポジトリをクローン
git clone https://github.com/Mega-Gorilla/jra-van-client.git
cd jra-van-client

# 仮想環境作成
python -m venv venv
venv\Scripts\activate  # Windows

# 依存パッケージインストール
pip install -r requirements.txt
```

### 2. JV-Link登録（初回のみ・管理者権限必要）

```bash
# 管理者権限でコマンドプロンプトを開く
cd setup
register_jvlink.bat
```

### 3. 64bit Python対応設定（64bit版Pythonの場合）

```bash
# 管理者権限で実行
python setup\setup_64bit_support.py
```

## 💻 使い方

### コマンドライン

```bash
# 接続テスト
python main_jra_van.py --test

# 初回データ取得（セットアップ）
python main_jra_van.py --setup

# データ更新
python main_jra_van.py --update

# リアルタイムデータ取得
python main_jra_van.py --realtime

# 統計情報表示
python main_jra_van.py --stats
```

### Python API

```python
from src.jvdata_manager import JVDataManager
from src.jvlink_client import JVLinkClient

# 基本的な使い方
manager = JVDataManager("jravan.db")

# レースデータ取得
manager.download_setup_data("RACE")  # 初回
manager.update_data()  # 更新

# リアルタイムデータ
manager.get_realtime_data(
    JVLinkClient.REALTIME_SPEC['WEIGHT'],  # 馬体重
    race_key=""  # 空文字で当日全レース
)

# データベースから取得
import sqlite3
conn = sqlite3.connect("jravan.db")
df = pd.read_sql_query("SELECT * FROM races WHERE year='2024'", conn)

manager.close()
```

### 利用可能なデータ種別

#### 蓄積系データ
- `RACE` - レース情報
- `DIFF` - 差分データ
- `BLOD` - 血統データ
- `HOSE` - 競走馬データ
- `YSCH` - 年間スケジュール

#### リアルタイムデータ
- `0B15` - 馬体重
- `0B12` - 単複枠オッズ
- `0B13` - 馬連オッズ
- `0B20` - 速報成績

## 📊 データベース構造

自動的に以下のテーブルが作成されます：

| テーブル名 | 説明 | 主要カラム |
|-----------|------|-----------|
| races | レース情報 | race_key, race_name, race_date, distance |
| results | 出走結果 | race_key, umaban, kakutei_jyuni, time |
| horses | 競走馬マスタ | ketto_num, bamei, father, mother |
| odds | オッズ | race_key, umaban, tansho_odds |
| weights | 馬体重 | race_key, umaban, bataijyu, zogen |
| schedules | 開催日程 | year, kaiji_date, jyo_code |

## 🛠️ トラブルシューティング

### エラー: クラスが登録されていません

```bash
# 管理者権限で実行
cd setup
register_jvlink.bat
```

### エラー: サービスキー認証エラー (-211)

JRA-VAN DataLabの契約が必要です。[JRA-VAN公式サイト](https://jra-van.jp/)から契約してください。

### 64bit/32bit互換性問題

```bash
# オプション1: 32bit Pythonを使用
py -3.8-32 -m venv venv32

# オプション2: 64bit対応設定（管理者権限）
python setup\setup_64bit_support.py
```

## 📁 プロジェクト構造

```
jra-van-client/
├── src/                    # ソースコード
│   ├── __init__.py
│   ├── jvlink_client.py   # JV-Link COMラッパー
│   ├── jvdata_parser.py   # データパーサー
│   └── jvdata_manager.py  # データ管理
├── setup/                  # セットアップツール
│   ├── register_jvlink.bat
│   └── setup_64bit_support.py
├── tests/                  # テストコード
│   └── test_jvlink.py
├── docs/                   # ドキュメント
├── main_jra_van.py        # CLI
├── requirements.txt       # 依存関係
└── README.md             # このファイル
```

## 🔧 開発者向け

### テスト実行

```bash
python tests/test_jvlink.py
pytest tests/  # pytestを使う場合
```

### パッケージとしてインストール

```bash
pip install -e .  # 開発モード
```

## 📝 ライセンス

MITライセンス - 詳細は[LICENSE](LICENSE)を参照

ただし、JRA-VAN DataLabの利用には別途契約と利用規約への同意が必要です。

## 🤝 コントリビューション

プルリクエスト歓迎！詳細は[CONTRIBUTING.md](CONTRIBUTING.md)を参照。

## 📚 参考資料

- [JRA-VAN公式サイト](https://jra-van.jp/)
- [JV-Link仕様書](https://jra-van.jp/dlb/sdv/sdk.html)
- [詳細実装ガイド](docs/README_JRAVAN.md)
- [セットアップガイド](docs/JVLINK_SETUP_GUIDE.md)

## ⚠️ 免責事項

- 本パッケージは非公式です
- JRA-VAN DataLabの契約が別途必要です
- データの利用は自己責任でお願いします

## 📮 サポート

- Issues: [GitHub Issues](https://github.com/Mega-Gorilla/jra-van-client/issues)
- Discussion: [GitHub Discussions](https://github.com/Mega-Gorilla/jra-van-client/discussions)

---

**jra-van-client** - JRA-VAN DataLab Python Client
© 2024 | Built with ❤️ for Japanese Horse Racing Data Analysis