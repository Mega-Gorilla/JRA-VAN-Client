# JRA-VAN Client

[![Python Version](https://img.shields.io/badge/python-3.8%2B%20(32bit)-blue)](https://www.python.org)
[![Windows](https://img.shields.io/badge/platform-Windows-lightgrey)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

JRA-VAN DataLabから競馬データを簡単に取得・分析するためのPythonクライアント

## 🚀 Quick Start（5分で始める）

```bash
# 最短手順（経験者向け・32bit Python必須）
git clone https://github.com/Mega-Gorilla/jra-van-client.git
cd jra-van-client
# JV-Link.exeインストーラーを実行してDLLを配置
pip install .  # pywin32も自動インストール
python setup_windows.py  # 管理者権限で実行
jravan --test
```

## ✨ 特徴

- 🐍 **標準的なPythonパッケージ** - `pip install .`でインストール可能
- 💻 **32bit Python対応** - JVLink COMコンポーネントとの完全互換性
- 📦 **Pythonic API** - シンプルで使いやすいインターフェース
- 📊 **自動データベース構築** - SQLiteで簡単にデータ管理
- ⚡ **リアルタイムデータ対応** - オッズ・馬体重の速報取得

## 🚀 インストール

### 📋 システム要件

| 項目 | 最小要件 | 推奨 |
|------|---------|------|
| OS | Windows 10 | Windows 11 |
| Python | 3.8 (32bit) ⚠️ | 3.10以上 (32bit) |
| メモリ | 4GB | 8GB以上 |
| ディスク | 10GB | 50GB以上 |
| JRA-VAN | Data Lab. SDK | 同左 |
| 契約 | JRA-VAN DataLab（月額2,090円） | 同左 |

⚠️ **重要**: JVLinkは32bit COMコンポーネントのため、**32bit版Python**が必要です

### 📥 ステップ1: リポジトリの取得

```bash
git clone https://github.com/Mega-Gorilla/jra-van-client.git
cd jra-van-client
```

または、[GitHubからZIPダウンロード](https://github.com/Mega-Gorilla/jra-van-client/archive/refs/heads/main.zip)

### 📦 ステップ2: 32bit Python環境の準備とパッケージインストール

⚠️ **重要**: JVLinkは32bit COMコンポーネントのため、**必ず32bit版Python**を使用してください。  
64bit Pythonでは動作しません（エラー: 0x800700c1）。

#### 32bit Pythonの確認方法
```bash
# 現在のPythonが32bitか確認
python -c "import sys; print('32-bit ✓' if sys.maxsize <= 2**32 else '64-bit ✗ 32bit版が必要です')"
```

#### インストール手順

**既に32bit Pythonがある場合:**
```bash
# 32bit Python仮想環境作成
python -m venv venv
venv\Scripts\activate

# パッケージインストール（pywin32も自動インストール）
pip install .
```

**32bit Pythonがない場合:**
```bash
# 1. Python公式サイトから32bit版をダウンロード
#    https://python.org → Downloads → Windows installer (32-bit)
#    インストール先例: C:\Python311-32

# 2. 32bit Pythonで仮想環境作成
C:\Python311-32\python.exe -m venv venv
venv\Scripts\activate

# 3. パッケージインストール
pip install .
```

### 📂 ステップ3: JV-Linkのインストール

1. [JRA-VAN公式サイト](https://jra-van.jp/dlb/)からSDKをダウンロード
2. ZIPファイル内の`JV-Link.exe`（インストーラー）を実行
3. インストール後、`C:\Windows\SysWOW64\JVDTLAB\JVDTLAB.dll`が配置されることを確認

詳細: [setup/DOWNLOAD_JVLINK.md](setup/DOWNLOAD_JVLINK.md)

### ⚙️ ステップ4: Windows固有設定（管理者権限必須）

```bash
# 管理者権限でコマンドプロンプトを開いて実行
python setup_windows.py

# または、バッチファイルを管理者権限で実行
setup\setup_registry_32bit.bat
```

### ✅ ステップ5: 動作確認

```bash
# インストール後はjravanコマンドが使用可能
jravan --test

# または直接実行
python -m jravan --test
```

## 💻 基本的な使い方

### コマンドライン（pip install後）

```bash
# 接続テスト
jravan --test

# 初回データ取得（セットアップ）
jravan --setup

# データ更新（毎週実行推奨）
jravan --update

# 統計情報表示
jravan --stats

# ヘルプ
jravan --help
```

### Python API（推奨：コンテキストマネージャー使用）

```python
from jravan.manager import JVDataManager

# コンテキストマネージャーで安全にリソース管理
with JVDataManager("jravan.db") as manager:
    # レースデータ取得
    manager.download_setup_data("RACE")  # 初回
    manager.update_data()                # 更新
# 自動的にリソースがクリーンアップされる

# SQLiteデータベースから分析
import sqlite3
import pandas as pd

conn = sqlite3.connect("jravan.db")
df = pd.read_sql_query("""
    SELECT * FROM races 
    WHERE year = '2025' 
    AND jyo_name LIKE '%東京%'
""", conn)
conn.close()
```

## 📊 取得可能なデータ

### 基本データ
- 📅 **レース情報** - 開催日、距離、馬場状態など
- 🏇 **出走馬情報** - 馬名、騎手、調教師、過去成績
- 🧬 **血統データ** - 父馬、母馬、母父馬
- 📈 **年間スケジュール** - 開催予定、重賞レース日程

### リアルタイムデータ
- 💰 **オッズ** - 単勝、複勝、馬連、3連単など
- ⚖️ **馬体重** - 当日計量結果
- 🏁 **速報結果** - 確定順位、タイム

## 📁 プロジェクト構成

```
jra-van-client/
├── pyproject.toml         # Pythonパッケージ設定（PEP 517/518準拠）
├── setup.py               # 後方互換性用セットアップ
├── setup_windows.py       # Windows固有設定スクリプト
├── check_python.bat       # Python環境確認バッチ
├── jravan/
│   ├── __init__.py       # パッケージ初期化
│   ├── __main__.py       # CLIエントリーポイント
│   ├── client.py         # JV-Link COMラッパー
│   ├── manager.py        # データ管理
│   └── parser.py         # データ解析
├── setup/
│   ├── DOWNLOAD_JVLINK.md # JV-Linkインストール手順
│   ├── setup_registry_32bit.bat # 32bit用レジストリ設定
├── tests/                  # テストスクリプト
│   ├── __init__.py
│   ├── README.md
│   └── test_32bit_jvlink.py
└── docs/                   # 詳細ドキュメント
```

## 🎯 活用例

### 1. 過去レースの分析
```python
# 重賞レースの結果を取得
df_grade = pd.read_sql_query("""
    SELECT * FROM races 
    WHERE grade_cd IN ('1', '2', '3')  -- G1, G2, G3
    ORDER BY year DESC, monthday DESC
""", conn)
```

### 2. 騎手成績の集計
```python
# 騎手別の勝率計算
df_jockey = pd.read_sql_query("""
    SELECT jockey_name, 
           COUNT(*) as rides,
           SUM(CASE WHEN kakutei_jyuni = 1 THEN 1 ELSE 0 END) as wins,
           ROUND(100.0 * SUM(CASE WHEN kakutei_jyuni = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) as win_rate
    FROM results
    WHERE kakutei_jyuni > 0
    GROUP BY jockey_name
    HAVING rides >= 100
    ORDER BY win_rate DESC
""", conn)
```

### 3. リアルタイムオッズ監視
```python
# レース直前のオッズ変動を取得
from jravan.client import JVLinkClient
manager.get_realtime_data(JVLinkClient.REALTIME_SPEC['ODDS_WIN_PLACE'])
```

## 📊 データサイズと処理時間の目安

| データ種別 | サイズ | 初回DL時間 | 更新時間 |
|-----------|--------|-----------|----------|
| RACE (レース) | 約5GB | 2-3時間 | 10-30分 |
| YSCH (スケジュール) | 約100MB | 5-10分 | 1-2分 |
| リアルタイム | - | - | 即時 |

## ⚠️ 初回実行時の注意

1. **JV-Linkセットアップ画面**が表示されます
2. **JRA-VANサービスキー**を入力してください
3. **データ保存先フォルダ**を指定してください（デフォルト推奨）
4. **レジストリ設定**は自動的に現在のパスで生成されます

## 🔧 トラブルシューティング


### よくある質問

**Q: セットアップは毎回必要？**  
A: いいえ、初回のみです。

**Q: JRA-VANの契約は必須？**  
A: はい、月額2,090円の契約が必要です。[JRA-VAN公式サイト](https://jra-van.jp/)

**Q: Mac/Linuxで使える？**  
A: JV-LinkがWindows専用のため対応していません。

## 🆕 最新の改善内容 (2025年8月)

### パフォーマンス最適化
- **バッチ処理実装**: 大量データ処理時のメモリ効率を改善
- **WALモード対応**: SQLiteのWrite-Ahead Loggingで並列処理性能向上
- **接続プール実装**: データベース接続の効率的な管理

### 安全性向上
- **コンテキストマネージャー実装**: リソースの自動クリーンアップ
- **具体的な例外処理**: エラー原因の特定が容易に
- **トランザクション管理強化**: データ整合性の保証

## 📈 今後の予定

- [ ] Web API化
- [ ] 機械学習モデルの統合
- [ ] レース予測機能
- [ ] データ可視化ツール
- [ ] Docker対応

## 🤝 コントリビューション

プルリクエスト歓迎！バグ報告は[Issues](https://github.com/Mega-Gorilla/jra-van-client/issues)へ。

## 📝 ライセンス

MIT License with Additional Terms - 詳細は[LICENSE](LICENSE)を参照

### ⚠️ JRA-VANデータ利用に関する重要事項
- JRA-VANデータの利用には**別途契約**（月額2,090円）が必要です
- データ利用時は**JRA-VAN利用規約**を遵守してください
- 本ソフトウェアのライセンスは**データ利用権を付与するものではありません**
- 詳細は[LICENSE](LICENSE)ファイルの追加条項を参照してください

## 🙏 謝辞

- JRA-VAN DataLab様 - データ提供
- pywin32開発者の皆様 - COM接続サポート

---

**JRA-VAN Client** - Built with ❤️ by [Mega-Gorilla](https://github.com/Mega-Gorilla)  
競馬データ分析を、もっと簡単に。