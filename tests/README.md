# JRA-VAN Client テスト

このディレクトリには、JRA-VAN Clientのテストスクリプトが含まれています。

## テストファイル

### test_32bit_jvlink.py
32bit Python環境でJVLink COMコンポーネントの動作を確認するテストスクリプト。

**実行方法:**
```bash
# 32bit Python環境で実行
python tests/test_32bit_jvlink.py
```

**テスト内容:**
- Python環境が32bitであることの確認
- JVLink COMオブジェクトの作成
- JVInitによる初期化
- データ取得（YSCH）のテスト

## 前提条件

1. **32bit Python環境**が必要
2. **JV-Link.exe**がインストール済み
3. **setup_windows.py**が実行済み
4. **pywin32**がインストール済み（`pip install .`で自動インストール）

## トラブルシューティング

### 64bit Pythonエラー
```
Architecture: 64-bit [ERROR]
```
→ 32bit Pythonを使用してください

### COMエラー
```
ERROR: (-2147221005, 'Invalid class string', None, None)
```
→ `setup_windows.py`を管理者権限で実行してください

### JVInit エラー -301
```
JVInit returned: -301
```
→ JRA-VANサービスキーが未設定です。初回実行時に設定画面が表示されます。