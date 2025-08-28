# JV-Link セットアップガイド

## 現在の状況

テスト結果から以下の状況が判明しました：

1. **Python環境**: 64bit版 Python 3.13.5
2. **JV-Link**: 32bit COMサーバー
3. **問題**: 64bit Pythonから32bit COMサーバーに直接アクセスできない

## 解決方法

### 方法1: JV-Link.exe を登録する（必須）

管理者権限でコマンドプロンプトを開き、以下を実行：

```cmd
cd "D:\Codes\StableFormer\JRA-VAN Data Lab. SDK Ver4.9.0.2\JV-Link"
JV-Link.exe /regserver
```

または、作成した`register_jvlink.bat`を右クリック→「管理者として実行」

### 方法2: 64bit Python対応（3つの選択肢）

#### A. 32bit版Pythonを使用（推奨）

1. Python公式サイトから32bit版をダウンロード
2. 32bit版で仮想環境を作成：
```powershell
py -3.13-32 -m venv .venv32
.\.venv32\Scripts\Activate.ps1
pip install pywin32
```

#### B. DLLサロゲート設定（上級者向け）

管理者権限でPowerShellを開き：
```powershell
python setup_64bit_support.py
```

#### C. プロキシプロセス方式（代替案）

32bitプロセスを経由してアクセス（実装が必要）

## テスト手順

### 1. JV-Link登録確認
```powershell
python test_jvlink.py
```

### 2. 接続テスト
```powershell
python main_jra_van.py --test
```

## エラー対処法

### エラー: クラスが登録されていません
- 原因: JV-Link.exeが未登録
- 解決: 管理者権限で`register_jvlink.bat`を実行

### エラー: サービスキー認証エラー (-211)
- 原因: JRA-VAN DataLab未契約
- 解決: JRA-VANと契約（月額2,090円）

### エラー: 64bitと32bitの互換性問題
- 原因: アーキテクチャ不一致
- 解決: 上記の方法2を参照

## 確認済み事項

✅ JV-Link.exe は存在（SDK内）
✅ pywin32 インストール済み
✅ Pythonコード実装完了
❌ JV-Link COM登録（管理者権限必要）
❌ 64bit/32bit互換性設定

## 次のステップ

1. **管理者権限で`register_jvlink.bat`を実行**
2. **接続テストを再実行**
3. **必要に応じて32bit Python環境を構築**

---
最終更新: 2025-08-28