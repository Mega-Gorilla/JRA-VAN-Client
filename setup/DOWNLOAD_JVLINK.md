# JV-Link インストール手順

**最終更新: 2025年8月29日**

## ⚠️ 重要：JV-Link.exeのインストールが必要です

JRA-VAN Clientを利用するためには、JRA-VAN公式サイトから**JV-Link.exe**（インストーラー）をダウンロード・実行する必要があります。

### なぜJV-Link.exeが必要なのか？
JV-Link.exeはインストーラーで、実行するとJVLink COMコンポーネント（JVDTLAB.dll）がシステムに配置され、競馬データへのアクセスが可能になります。

## 📥 インストール手順

### ステップ1: JRA-VAN公式サイトにアクセス
   - 🔗 [https://jra-van.jp/dlb/](https://jra-van.jp/dlb/) を開く
   - JRA-VAN DataLab会員登録が必要です（月額2,090円）

### ステップ2: JV-Link SDKをダウンロード
   - ログイン後、「ソフトウェア開発キット（SDK）」セクションへ
   - 「JRA-VAN Data Lab. SDK」をダウンロード
   - ファイル名例: `JVLinkSDK_Ver4.9.0.2.zip`

### ステップ3: JV-Link.exeを抽出してインストール
   ```
   ダウンロードしたZIPファイル
   └── JV-Link/
       ├── JV-Link.exe     ← このインストーラーを実行！
       ├── JV-Link.pdf     （マニュアル）
       └── その他のファイル
   ```
   - ZIPファイルを展開
   - **JV-Link.exe**を実行（管理者権限推奨）
   - インストーラーの指示に従ってインストール
   - インストール完了後、以下のDLLが自動的に配置されます：
     - `C:\Windows\SysWOW64\JVDTLAB\JVDTLAB.dll`

### ステップ4: サービスキーの設定
   - 初回起動時にJRA-VANサービスキーの入力が求められます
   - 会員ページからサービスキーを取得して入力してください

## ✅ 確認方法

### DLLの存在確認（コマンドプロンプト）
```bash
dir C:\Windows\SysWOW64\JVDTLAB\JVDTLAB.dll
```

### PowerShellで確認
```powershell
Test-Path "C:\Windows\SysWOW64\JVDTLAB\JVDTLAB.dll"
# True が表示されればインストール成功
```

### Pythonで確認（32bit Python必須）
```python
import sys
import os

# Python環境確認
is_32bit = sys.maxsize <= 2**32
print(f"Python: {'32-bit [OK]' if is_32bit else '64-bit [ERROR]'}")

# DLL存在確認
dll_path = r"C:\Windows\SysWOW64\JVDTLAB\JVDTLAB.dll"
if os.path.exists(dll_path):
    print("✅ JVDTLAB.dll が正しくインストールされています")
else:
    print("❌ JVDTLAB.dll が見つかりません")
```

## 📝 注意事項

### 法的注意
- ⚖️ JV-Link.exeはJRA-VANの著作物です
- 📥 必ず公式サイトから正規版をダウンロードしてください
- 💰 利用には月額2,090円の契約が必要です
- 🚫 JV-Link.exeの再配布は禁止されています

### 技術的注意
- 📦 JV-Link.exeはインストーラーです（実行ファイルではありません）
- 🖥️ JVLinkは32bit COMコンポーネントです
- ⚠️ **重要**: 32bit版Pythonが必須です（64bit Pythonでは動作しません）
- 🔧 インストール後もレジストリへの追加設定が必要です（setup_windows.pyで自動化）

## ❓ よくある質問とトラブルシューティング

### Q: インストーラーが見つからない
**A:** JRA-VAN DataLab会員登録（月額2,090円）が必要です。[こちら](https://jra-van.jp/)から登録してください。

### Q: 64bit Pythonで動作しない
**A:** JVLinkは32bit COMコンポーネントのため、**32bit版Python**が必須です。
- [Python公式サイト](https://python.org/downloads/windows/)から「Windows installer (32-bit)」をダウンロード
- インストール先例: `C:\Python311-32`

### Q: COMエラー（0x800700c1）が発生する
**A:** 64bit Pythonを使用している可能性があります。以下で確認してください：
```python
import sys
print("32-bit" if sys.maxsize <= 2**32 else "64-bit")
```

### Q: レジストリ登録が失敗する
**A:** 管理者権限でコマンドプロンプトを開いて`setup_windows.py`を実行してください。

### Q: JVInitが-301エラーを返す
**A:** サービスキーが未設定です。初回実行時に表示される設定画面で入力してください。

## 🚀 次のステップ

JV-Link.exeのインストールが完了したら：

### 1. 32bit Python環境の準備
```bash
# 32bit Pythonがインストール済みか確認
python -c "import sys; print('32-bit' if sys.maxsize <= 2**32 else '64-bit [ERROR: 32-bit Python required]')"

# 32bit Python仮想環境作成（例: C:\Python311-32を使用）
C:\Python311-32\python.exe -m venv venv_32bit
venv_32bit\Scripts\activate
```

### 2. Pythonパッケージのインストール
```bash
# パッケージインストール（32bit環境で実行）
pip install .  # pywin32も自動的にインストールされます
```

### 3. Windows固有設定の実行
```bash
# DLL登録とレジストリ設定（管理者権限推奨）
python setup_windows.py
```

### 4. 動作確認
```bash
# 接続テスト
python test_32bit_jvlink.py

# CLIツールのテスト
jravan --test

# または
python -m jravan --test
```

詳細は [README.md](../README.md) を参照してください。