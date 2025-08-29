# JRA-VAN REST API Server

JRA-VAN Data Lab.のデータをREST API経由で提供するシンプルで高速なサーバー

## 🎯 概要

このAPIサーバーは、32ビット専用のJVLink COMコンポーネントをラップし、64ビットアプリケーションからもJRA-VANデータにアクセスできるようにします。

### 主な特徴

- ⚡ **超高速レスポンス**: メモリキャッシュで0.01ms
- 🚀 **シンプル実装**: コア部分わずか115行
- 🔄 **64ビット対応**: REST API経由で任意のアーキテクチャから利用可能
- 📦 **最小依存**: 必要なパッケージは5つのみ
- 🎯 **2層キャッシュ**: メモリ（必須）+ Redis（オプション）

## 📋 前提条件

- ✅ Windows OS
- ✅ 32ビット Python 3.11以降
- ✅ JV-Link インストール済み（[JRA-VAN公式サイト](http://jra-van.jp/)から入手）

## 🚀 クイックスタート

### 1. 環境確認

```powershell
# Python環境の確認（32ビット必須）
python -c "import sys; print(f'32-bit: {sys.maxsize <= 2**32}')"
# 出力が "32-bit: True" であることを確認
```

### 2. 依存関係のインストール

```powershell
# プロジェクトのルートディレクトリで実行
cd api
pip install -r requirements.txt
```

### 3. JVLink接続テスト

```powershell
# 接続テストを実行
python test_connection.py
```

期待される出力:
```
==================================================
JVLink接続テスト
==================================================
Python: 3.12.10 [MSC v.1943 32 bit (Intel)]
Platform: win32
Architecture: 32-bit

JVLink接続を試みます...
[OK] JVLink COMオブジェクト作成成功
JVInit戻り値: 0
[OK] JVLink初期化成功
[OK] JVLink接続テスト完了
```

### 4. APIサーバー起動

```powershell
# 開発モード（自動リロード付き）
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# または直接実行
python main.py
```

### 5. 動作確認

ブラウザで以下のURLにアクセス:
- http://localhost:8000 - APIルート
- http://localhost:8000/docs - 自動生成されたAPIドキュメント（Swagger UI）

## 📡 API エンドポイント

### 基本エンドポイント

| エンドポイント | メソッド | 説明 |
|------------|---------|------|
| `/` | GET | APIサーバー情報 |
| `/health` | GET | ヘルスチェック |
| `/docs` | GET | Swagger UIドキュメント |
| `/redoc` | GET | ReDoc ドキュメント |

### データ取得API

#### `GET /api/v1/data/{dataspec}`

JRA-VANデータを取得します。

**パラメータ:**
- `dataspec` (path, 必須): データ種別
  - `RACE`: レース情報
  - `HOSE`: 競走馬情報
  - `0B12`: 単勝・複勝オッズ
  - `0B15`: 馬連オッズ
  - その他、JRA-VAN仕様書に準拠
- `from_time` (query, オプション): 開始日時（YYYYMMDDHHmmSS形式）
- `option` (query, オプション): オプション値（1-4、デフォルト: 1）

**レスポンス例:**
```json
{
  "data": [
    {
      "record_type": "RA",
      "data": "RA202501010101010100..."
    }
  ],
  "cached": false,
  "count": 100
}
```

## 💻 使用例

### Python
```python
import requests

# ヘルスチェック
response = requests.get("http://localhost:8000/health")
print(response.json())

# レースデータ取得
response = requests.get(
    "http://localhost:8000/api/v1/data/RACE",
    params={"from_time": "20250101000000"}
)
data = response.json()
print(f"取得件数: {data['count']}")
print(f"キャッシュ: {data['cached']}")
```

### JavaScript (Node.js)
```javascript
const axios = require('axios');

// レースデータ取得
async function getRaceData() {
    const response = await axios.get(
        'http://localhost:8000/api/v1/data/RACE',
        { params: { from_time: '20250101000000' } }
    );
    console.log(`取得件数: ${response.data.count}`);
}
```

### cURL
```bash
# ヘルスチェック
curl http://localhost:8000/health

# レースデータ取得
curl "http://localhost:8000/api/v1/data/RACE?from_time=20250101000000"

# 単勝・複勝オッズ取得
curl "http://localhost:8000/api/v1/data/0B12"
```

## ⚡ パフォーマンス

### レスポンス時間

| シナリオ | 応答時間 | 説明 |
|---------|---------|------|
| L1キャッシュヒット | **0.01ms** | メモリキャッシュから即座に返却 |
| L2キャッシュヒット | 1-2ms | Redis から取得（オプション） |
| キャッシュミス | 20-40ms | JVLink から新規取得 |

### キャッシュ設定

#### メモリキャッシュ（L1）
- 容量: 500エントリ
- デフォルトTTL: 300秒（5分）
- 自動的に古いエントリを削除

#### Redis キャッシュ（L2、オプション）
- 自動検出（起動時に接続を試行）
- データ種別に応じたTTL:
  - リアルタイムデータ（0B系）: 60秒
  - マスタデータ（HOSE等）: 24時間
  - その他: 10分

## 📁 プロジェクト構成

```
api/
├── main.py           # FastAPIアプリケーション本体
├── cache.py          # 2層キャッシュサービス
├── test_connection.py # JVLink接続テストスクリプト
├── requirements.txt  # Python依存関係
└── README.md        # このファイル
```

## 🔧 設定のカスタマイズ

### キャッシュサイズの変更

`main.py` の以下の部分を編集:
```python
cache = CacheService(memory_size=1000, memory_ttl=600)  # サイズとTTLを調整
```

### ポート番号の変更

起動コマンドで指定:
```bash
uvicorn main:app --port 8080
```

## 🚨 トラブルシューティング

### "JVLink not initialized" エラー

**原因**: JVLink COMコンポーネントへの接続失敗

**解決方法**:
1. 32ビットPythonを使用しているか確認
2. JV-Linkがインストールされているか確認
3. 管理者権限でコマンドプロンプトを実行

### "ModuleNotFoundError: No module named 'win32com'"

**解決方法**:
```bash
pip install pywin32
```

### Redis接続エラー

**注意**: Redisはオプションです。エラーが出ても動作します。

Redisを使用する場合:
```bash
# Redisサーバーを起動
redis-server
```

### 文字化け

UTF-8エンコーディングを確認:
```python
# main.py の先頭に追加
import sys
sys.stdout.reconfigure(encoding='utf-8')
```

## 🔒 セキュリティ

### 本番環境での推奨設定

1. **CORS設定**: 許可するオリジンを明示的に指定
2. **認証**: APIキーまたはOAuth2の実装
3. **レート制限**: FastAPI-Limiterなどを使用
4. **HTTPS**: リバースプロキシ（nginx等）でSSL終端

## 📈 今後の拡張

- [ ] バッチ処理API
- [ ] WebSocketリアルタイム配信
- [ ] GraphQL インターフェース
- [ ] Docker対応
- [ ] 認証システム

## 📄 ライセンス

MIT License（JRA-VANデータ利用規約に準拠）

## 🤝 貢献

Issues、Pull Requestsは歓迎します。

## 📞 サポート

問題が発生した場合は、Issueを作成してください。