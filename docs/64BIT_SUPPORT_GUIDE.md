# JRA-VAN 64bit Python対応ガイド

## 概要

JV-Link.exeは32bit COMサーバーのため、64bit Pythonから直接アクセスできません。
本プロジェクトでは、以下の2つの方法で64bit Python対応を実現しています。

## 方法1: DLLサロゲート方式（推奨）

### 仕組み
Windowsの「DLLサロゲート」機能を使用して、32bit COMサーバーを64bitプロセスから呼び出し可能にします。

### セットアップ手順

1. **管理者権限でコマンドプロンプトを開く**
   ```
   Win + X → Windows Terminal (管理者)
   ```

2. **セットアップスクリプトを実行**
   ```bash
   cd "D:\Codes\JRA VAN Client\setup"
   python setup_64bit_support.py
   ```

3. **動作確認**
   ```bash
   cd "D:\Codes\JRA VAN Client"
   python test_64bit.py
   ```

### メリット
- 追加のPythonインストール不要
- 既存のコードをそのまま使用可能
- パフォーマンスが良い

### デメリット
- レジストリ設定が必要（管理者権限）
- JV-Link再インストール時に再設定が必要

### トラブルシューティング

#### エラー: pywintypes.com_error: (-2147221005, 'クラスが登録されていません', None, None)
```bash
# レジストリファイルを手動適用
cd setup
# jvlink_64bit_support.reg をダブルクリック
```

## 方法2: プロセス間通信ブリッジ方式

### 仕組み
32bit Pythonプロセスを別途起動し、64bit Pythonとパイプ通信でデータをやり取りします。

### セットアップ手順

1. **32bit Pythonのインストール**
   - [Python公式サイト](https://www.python.org/downloads/windows/)から
   - "Windows installer (32-bit)"を選択
   - 例: python-3.11.x-win32.exe

2. **32bit Python用pywin32インストール**
   ```bash
   py -3.11-32 -m pip install pywin32
   ```

3. **動作確認**
   ```bash
   python test_64bit.py
   ```

### メリット
- レジストリ変更不要
- デバッグが容易
- より安定した動作

### デメリット
- 32bit Pythonの追加インストールが必要
- プロセス間通信のオーバーヘッド

## 自動選択機能

本プロジェクトのJVLinkClientは、環境を自動検出して最適な方式を選択します：

```python
from src.jvlink_client import JVLinkClient

# 自動的に64bit/32bitを判定し、適切な方式を使用
client = JVLinkClient()
ret = client.initialize("MYAPP")

if ret == 0:
    print("初期化成功")
    # 64bit環境では自動的にブリッジまたはDLLサロゲート経由
    # 32bit環境では直接COM接続
```

## 推奨設定

### 開発環境
- **方法1（DLLサロゲート）**を推奨
  - セットアップが簡単
  - パフォーマンスが良い

### 本番環境
- **方法2（ブリッジ）**を検討
  - より確実な動作
  - エラー処理が容易

## 技術詳細

### DLLサロゲートの仕組み

1. レジストリにAppIDとDllSurrogateキーを追加
2. dllhost.exe（システム提供）が32bit DLLをロード
3. 64bitプロセスからdllhost.exeにRPC経由でアクセス

### ブリッジの仕組み

1. 64bit Python: JVLinkBridgeクラスがコマンドを送信
2. パイプ経由でJSON形式のコマンドを送信
3. 32bit Python: jvlink_server.pyがコマンドを受信・実行
4. 結果をJSON形式で返送

## FAQ

### Q: どちらの方法を選ぶべき？
A: まず方法1（DLLサロゲート）を試してください。うまくいかない場合は方法2を使用。

### Q: 既存のコードを変更する必要は？
A: ありません。JVLinkClientが自動的に適切な方式を選択します。

### Q: パフォーマンスの違いは？
A: DLLサロゲートの方が若干高速ですが、実用上はほぼ差がありません。

### Q: Windows Server環境では？
A: 両方式とも動作しますが、方法2（ブリッジ）がより確実です。

## 参考資料

- [COM DLL Surrogate（Microsoft Docs）](https://docs.microsoft.com/en-us/windows/win32/com/dll-surrogates)
- [JRA-VAN開発者コミュニティ](https://developer.jra-van.jp/)
- [Python win32com documentation](https://github.com/mhammond/pywin32)