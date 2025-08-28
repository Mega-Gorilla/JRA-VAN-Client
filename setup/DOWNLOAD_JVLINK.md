# JV-Link.exe ダウンロード手順

**最終更新: 2025年8月28日**

## ⚠️ 重要：JV-Link.exeが必要です

JRA-VAN Clientを利用するためには、JRA-VAN公式サイトから`JV-Link.exe`をダウンロードして、このフォルダに配置する必要があります。

### なぜJV-Link.exeが含まれていないのか？
JV-Link.exeはJRA-VANの著作物であり、再配布が許可されていないため、利用者各自でダウンロードしていただく必要があります。

## 📥 ダウンロード手順

### ステップ1: JRA-VAN公式サイトにアクセス
   - 🔗 [https://jra-van.jp/dlb/#tab5](https://jra-van.jp/dlb/#tab5) を開く
   - ※会員登録（無料）が必要な場合があります

### ステップ2: SDKをダウンロード
   - 「ソフトウェア開発キット（SDK）」タブをクリック
   - 最新版の「JRA-VAN Data Lab. SDK」をダウンロード
   - ファイル名例: `JVLinkSDK_Ver4.9.0.2.zip`

### ステップ3: JV-Link.exeを抽出
   ```
   ダウンロードしたZIPファイル
   └── JV-Link/
       ├── JV-Link.exe     ← これが必要！
       ├── JV-Link.pdf     （マニュアル）
       └── その他のファイル
   ```

### ステップ4: このフォルダにコピー
   - 抽出した`JV-Link.exe`を**このフォルダ（setup/）**にコピー
   - 最終的な配置場所: `setup/JV-Link.exe`

## ✅ 確認方法

### Windowsコマンドプロンプトで確認
```bash
cd setup
dir JV-Link.exe
```

### PowerShellで確認
```powershell
Test-Path ".\setup\JV-Link.exe"
# True が表示されれば配置成功
```

### Pythonで確認
```python
import os
if os.path.exists("setup/JV-Link.exe"):
    print("✅ JV-Link.exe が正しく配置されています")
else:
    print("❌ JV-Link.exe が見つかりません")
```

## 📝 注意事項

### 法的注意
- ⚖️ JV-Link.exeはJRA-VANの著作物のため、再配布は禁止されています
- 📥 必ず公式サイトから正規版をダウンロードしてください
- 🔄 SDKのバージョンが更新された場合は、JV-Link.exeも更新してください

### 技術的注意
- 🖥️ JV-Link.exeは32bitアプリケーションです
- ✅ 本クライアントは64bit Python環境でも動作します（DLL Surrogate機能を使用）
- 🔧 初回実行時にレジストリへの登録が必要です（自動化済み）

## ❓ よくある質問とトラブルシューティング

### Q: ダウンロードリンクが見つからない
**A:** JRA-VANの会員登録（無料）が必要です。[こちら](https://jra-van.jp/)から登録してください。

### Q: どのバージョンをダウンロードすべき？
**A:** 最新版を推奨します（2025年8月現在: Ver4.9.0.2以降）

### Q: ウイルス対策ソフトが警告を出す
**A:** JV-Link.exeはCOMコンポーネントのため、一部のウイルス対策ソフトが警告することがあります。JRA-VAN公式サイトからダウンロードした正規版であれば安全です。

### Q: ダウンロードしたファイルが破損している？
**A:** ファイルサイズを確認してください。JV-Link.exe は約600KB程度です。

### Q: 管理者権限は必要？
**A:** 初回のレジストリ登録時のみ管理者権限が必要です。通常の実行には不要です。

## 🚀 次のステップ

JV-Link.exeの配置が完了したら：

### 1. プロジェクトルートに戻る
```bash
cd ..
```

### 2. Pythonパッケージのインストール（未実行の場合）
```bash
# 仮想環境作成（推奨）
python -m venv venv
venv\Scripts\activate

# パッケージインストール
pip install .
```

### 3. Windows固有設定の実行
```bash
# COM登録とレジストリ設定（管理者権限推奨）
python setup_windows.py
```

### 4. 動作確認
```bash
# 接続テスト
jravan --test

# または
python -m jravan --test
```

詳細は [README.md](../README.md) を参照してください。