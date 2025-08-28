# jra-van-client セットアップ手順

## 現在の状況

- ✅ Python環境: 64bit版 Python 3.13.5
- ✅ pywin32: インストール済み
- ✅ JVDTLab.JVLink: レジストリ登録済み（ProgID）
- ❌ CLSID: 未登録（64bitレジストリ）
- ❌ 問題: 64bit Pythonから32bit COMサーバーにアクセスできない

## セットアップ手順

### ステップ1: 管理者権限でセットアップ（必須）

以下の2つの方法のいずれかを選択してください：

#### 方法A: バッチファイルを使用（推奨）

1. エクスプローラーで `jra_van_client` フォルダーを開く
2. `run_as_admin.bat` を右クリック
3. 「管理者として実行」を選択
4. 実行完了を待つ

#### 方法B: 手動実行

1. **管理者権限でコマンドプロンプト**を開く
   - Windowsキー → 「cmd」と入力
   - 「コマンドプロンプト」を右クリック → 「管理者として実行」

2. JV-Link.exeを登録
   ```cmd
   cd "D:\Codes\StableFormer\JRA-VAN Data Lab. SDK Ver4.9.0.2\JV-Link"
   JV-Link.exe /regserver
   ```

3. 64bit対応設定を実行
   ```cmd
   cd D:\Codes\StableFormer\jra_van_client
   python setup\setup_64bit_support.py
   ```

### ステップ2: 動作確認

通常のコマンドプロンプトまたはPowerShellで：

```powershell
cd D:\Codes\StableFormer\jra_van_client

# 仮想環境有効化
..\.venv\Scripts\Activate.ps1

# 接続テスト
python tests\test_jvlink.py

# メインプログラムテスト
python main_jra_van.py --test
```

## 期待される結果

成功時の出力例：
```
JV-Link COM登録状態確認
======================================================================
レジストリ確認:
  JVDTLab.JVLink: 登録済み
  CLSID: 登録済み

COMオブジェクト生成テスト:
1. ProgID (JVDTLab.JVLink) 使用:
  成功: COMオブジェクト生成完了
  JVInit結果: -211
    → サービスキー認証エラー（JRA-VAN契約が必要）
```

エラー `-211` は正常です。これはJRA-VAN DataLabの契約が必要であることを示しています。

## トラブルシューティング

### エラー: クラスが登録されていません

→ 管理者権限でJV-Link.exeの登録が必要です

### エラー: アクセスが拒否されました

→ 管理者権限でコマンドを実行してください

### それでも動作しない場合

32bit版Pythonの使用を検討してください：

```powershell
# 32bit版Pythonのインストール
py -3.8-32 -m venv venv32
venv32\Scripts\activate
pip install pywin32
python main_jra_van.py --test
```

## 次のステップ

1. JRA-VAN DataLabの契約（月額2,090円）
2. サービスキーの取得
3. データ取得開始

## サポート

問題が解決しない場合は、以下の情報を添えてIssueを作成してください：

- Pythonバージョン（`python --version`）
- エラーメッセージ全文
- `python tests\test_jvlink.py` の出力

---
最終更新: 2025-08-28