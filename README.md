# JRA-VAN Client

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org)
[![Windows](https://img.shields.io/badge/platform-Windows%2064bit-lightgrey)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

JRA-VAN DataLabから競馬データを簡単に取得・分析するためのPythonクライアント

## ✨ 特徴

- 🚀 **ワンクリックセットアップ** - 管理者権限で`install_windows.py`を実行するだけ
- 💻 **64bit完全対応** - 最新のPython環境で動作
- 🐍 **Pythonic API** - シンプルで使いやすいインターフェース
- 📊 **自動データベース構築** - SQLiteで簡単にデータ管理
- ⚡ **リアルタイムデータ対応** - オッズ・馬体重の速報取得

## 📋 必要要件

- Windows 10/11 (64bit)
- Python 3.8以上
- JRA-VAN DataLab契約（月額2,090円）
- 管理者権限（初回セットアップ時のみ）

## 🚀 クイックスタート

### 1. リポジトリをクローン

```bash
git clone https://github.com/Mega-Gorilla/jra-van-client.git
cd jra-van-client
```

### 2. JV-Link.exeをダウンロード

**重要：** JV-Link.exeはJRA-VAN公式サイトからダウンロードが必要です

1. [JRA-VAN SDKダウンロードページ](https://jra-van.jp/dlb/#tab5)にアクセス
2. 最新版のSDKをダウンロード
3. ZIPを解凍し、`JV-Link\JV-Link.exe`を`setup/`フォルダにコピー

詳細手順は [setup/DOWNLOAD_JVLINK.md](setup/DOWNLOAD_JVLINK.md) を参照

### 3. セットアップ実行（管理者権限必要）

**管理者として**コマンドプロンプトを開いて：

```bash
python install_windows.py
```

これで全ての設定が自動的に完了します！

### 4. 使用開始

```bash
# 接続テスト
.\venv\Scripts\python.exe main.py --test

# 初回データ取得（数時間かかります）
.\venv\Scripts\python.exe main.py --setup

# データ更新
.\venv\Scripts\python.exe main.py --update
```

## 💻 基本的な使い方

### コマンドライン

```bash
# データ更新（毎週実行推奨）
.\venv\Scripts\python.exe main.py --update

# リアルタイムデータ取得（レース当日）
.\venv\Scripts\python.exe main.py --realtime

# 統計情報表示
.\venv\Scripts\python.exe main.py --stats
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
├── install_windows.py      # Windows用インストーラー
├── main.py                 # メインプログラム
├── pyproject.toml          # Pythonパッケージ設定
├── jravan/
│   ├── client.py          # JV-Link COMラッパー
│   ├── manager.py         # データ管理
│   └── parser.py          # データ解析
├── setup/
│   ├── DOWNLOAD_JVLINK.md # JV-Link.exeダウンロード手順
│   ├── create_registry.py  # レジストリ自動生成スクリプト
│   ├── apply_registry.bat  # レジストリ適用バッチ
│   └── register_jvlink.bat # JV-Link登録バッチ
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

## ⚠️ 初回実行時の注意

1. **JV-Linkセットアップ画面**が表示されます
2. **JRA-VANサービスキー**を入力してください
3. **データ保存先フォルダ**を指定してください（デフォルト推奨）
4. **レジストリ設定**は自動的に現在のパスで生成されます

## 🔧 トラブルシューティング

問題が発生した場合は [SETUP_GUIDE.md](SETUP_GUIDE.md) を参照してください。

### よくある質問

**Q: セットアップは毎回必要？**  
A: いいえ、初回のみです。

**Q: JRA-VANの契約は必須？**  
A: はい、月額2,090円の契約が必要です。[JRA-VAN公式サイト](https://jra-van.jp/)

**Q: Mac/Linuxで使える？**  
A: 申し訳ございません。JV-LinkがWindows専用のため対応していません。

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

MITライセンス - 詳細は[LICENSE](LICENSE)を参照

⚠️ JRA-VAN DataLabの利用には別途契約と利用規約への同意が必要です。

## 🙏 謝辞

- JRA-VAN DataLab様 - データ提供
- pywin32開発者の皆様 - COM接続サポート

---

**JRA-VAN Client** - Built with ❤️ by [Mega-Gorilla](https://github.com/Mega-Gorilla)  
競馬データ分析を、もっと簡単に。