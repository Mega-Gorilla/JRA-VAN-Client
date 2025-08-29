# JRA-VAN REST API 設計書

## 概要

このドキュメントは、JRA-VAN Data Lab.のデータを提供するREST APIサーバーの設計書です。
32ビットPython環境で動作するJVLinkラッパーをHTTP経由でアクセス可能にすることで、
64ビットアプリケーションからもJRA-VANデータを利用できるようにします。

## アーキテクチャ

### システム構成

```
┌─────────────────────────┐     ┌─────────────────────────┐
│   64-bit Client App     │     │   Machine Learning      │
│   (Python/Node.js等)    │────▶│   Pipeline (64-bit)     │
└─────────────────────────┘     └─────────────────────────┘
            │                                │
            │ HTTP/REST                     │
            ▼                                ▼
┌──────────────────────────────────────────────────────────┐
│         JRA-VAN REST API Server (32-bit Python)          │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              FastAPI Application                    │ │
│  │                                                     │ │
│  │   [Endpoints] ← [Cache Layer] ← [JVLink Manager]   │ │
│  │        ↓             ↓                ↓            │ │
│  │     レスポンス    TTLCache      win32com.client    │ │
│  │                  + Redis(opt)         ↓            │ │
│  │                                   JVDTLAB.dll      │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

### コンポーネント説明

#### 必須コンポーネント（最小構成）
| コンポーネント | 役割 | 技術スタック |
|--------------|------|------------|
| REST API Server | HTTPエンドポイント提供 | FastAPI, uvicorn |
| JVLink Manager | JVLink COM接続・データ取得 | pywin32 (win32com.client) |
| Memory Cache | 高速レスポンスのためのキャッシュ | cachetools (TTLCache) |

#### オプションコンポーネント（拡張機能）
| コンポーネント | 役割 | 技術スタック |
|--------------|------|------------|
| Redis Cache | 分散・永続キャッシュ | redis |
| Windows Service | バックグラウンド常駐化 | pywin32 (ServiceFramework) |
| Response Compression | レスポンス圧縮 | gzip (標準ライブラリ) |

**注意**: すべて32-bit Python環境（3.11以降推奨）で動作

## API エンドポイント

### 1. システム管理

#### GET /health
サーバーヘルスチェック

**Response:**
```json
{
  "status": "healthy",
  "jvlink_version": "4.9.0.2",
  "server_version": "1.0.0",
  "python_architecture": "32bit",
  "timestamp": "2025-08-29T12:00:00Z"
}
```

#### GET /status
JVLink接続状態

**Response:**
```json
{
  "connected": true,
  "sid": "20250829120000",
  "user_agent": "UMANARI1.0",
  "last_update": "2025-08-29T12:00:00Z"
}
```

### 2. データ取得

#### GET /api/v1/data/{dataspec}
指定データ種別のデータ取得

**Parameters:**
- `dataspec` (path): データ種別 (例: "RACE", "0B12")
- `option` (query): オプション (1-4)
- `from_time` (query): 開始日時 (YYYYMMDDHHmmSS)
- `to_time` (query): 終了日時
- `limit` (query): 取得件数制限
- `offset` (query): オフセット

**Response:**
```json
{
  "data_spec": "RACE",
  "total_count": 1234,
  "records": [
    {
      "record_type": "RA",
      "data": {
        "race_id": {
          "year": "2025",
          "month_day": "0829",
          "jyo_cd": "05",
          "kaiji": "03",
          "nichiji": "09",
          "race_num": "11"
        },
        "race_info": {
          "youbi_cd": "2",
          "toku_num": "00",
          "hondai": "札幌記念"
        }
      },
      "raw": "RA202508290503091100..."
    }
  ],
  "has_more": true,
  "next_offset": 100
}
```

#### POST /api/v1/data/stream
データストリーミング取得（Server-Sent Events）

**Request Body:**
```json
{
  "data_spec": "0B12",
  "option": 1,
  "from_time": "20250829000000"
}
```

**Response (SSE):**
```
event: data
data: {"record_type":"O1","data":{...}}

event: data
data: {"record_type":"O1","data":{...}}

event: complete
data: {"total_records":150}
```

### 3. リアルタイムデータ

#### GET /api/v1/realtime/odds/{race_id}
指定レースのオッズ情報取得

**Parameters:**
- `race_id` (path): レースID (例: "202508290503091100")
- `type` (query): オッズ種別 ("win", "place", "quinella", "exacta", "trio", "tierce")

**Response:**
```json
{
  "race_id": "202508290503091100",
  "odds_type": "win",
  "update_time": "2025-08-29T14:30:00Z",
  "odds": [
    {
      "horse_number": "01",
      "odds": 3.2,
      "popularity": 1
    },
    {
      "horse_number": "02", 
      "odds": 5.4,
      "popularity": 2
    }
  ]
}
```

#### GET /api/v1/realtime/weight/{race_id}
馬体重情報取得

**Response:**
```json
{
  "race_id": "202508290503091100",
  "weights": [
    {
      "horse_number": "01",
      "weight": 486,
      "weight_diff": 2
    }
  ]
}
```

### 4. マスタデータ

#### GET /api/v1/master/horse/{horse_id}
競走馬情報取得

**Response:**
```json
{
  "horse_id": "2020102345",
  "name": "ウマナリタイガー",
  "sex": "牡",
  "birth_date": "2020-04-15",
  "father": "ロードカナロア",
  "mother": "ウマナリビューティ",
  "trainer": {
    "id": "12345",
    "name": "栗田 徹"
  }
}
```

#### GET /api/v1/master/jockey/{jockey_id}
騎手情報取得

#### GET /api/v1/master/trainer/{trainer_id}
調教師情報取得

### 5. スケジュール

#### GET /api/v1/schedule
開催スケジュール取得

**Parameters:**
- `from_date` (query): 開始日
- `to_date` (query): 終了日
- `jyo_cd` (query): 競馬場コード

**Response:**
```json
{
  "schedules": [
    {
      "date": "2025-08-29",
      "jyo_cd": "05",
      "jyo_name": "札幌",
      "kaiji": "03",
      "nichiji": "09",
      "races": 12
    }
  ]
}
```

### 6. バッチ処理

#### POST /api/v1/batch/download
データ一括ダウンロード

**Request Body:**
```json
{
  "data_specs": ["RACE", "SE", "HR"],
  "from_date": "20250801",
  "to_date": "20250829",
  "format": "json"
}
```

**Response:**
```json
{
  "job_id": "batch_20250829_120000",
  "status": "processing",
  "estimated_time": 300
}
```

#### GET /api/v1/batch/status/{job_id}
バッチ処理状態確認

## エラーハンドリング

### エラーレスポンス形式

```json
{
  "error": {
    "code": "JVLINK_ERROR",
    "message": "JVLink connection failed",
    "details": {
      "error_code": -201,
      "description": "オープン済み"
    }
  },
  "timestamp": "2025-08-29T12:00:00Z",
  "request_id": "req_12345"
}
```

### エラーコード一覧

| HTTPステータス | エラーコード | 説明 |
|--------------|------------|------|
| 400 | INVALID_PARAMETER | パラメータ不正 |
| 401 | UNAUTHORIZED | 認証失敗 |
| 404 | NOT_FOUND | リソースが見つからない |
| 429 | RATE_LIMIT | レート制限超過 |
| 500 | JVLINK_ERROR | JVLink内部エラー |
| 503 | SERVICE_UNAVAILABLE | サービス利用不可 |

## 認証・認可

### APIキー認証

```http
GET /api/v1/data/RACE
Authorization: Bearer your-api-key-here
```

### レート制限

- 通常エンドポイント: 100 requests/minute
- ストリーミング: 10 concurrent connections
- バッチ処理: 10 jobs/hour

## データフォーマット

### レスポンス形式

すべてのレスポンスは以下の形式に従います：

```json
{
  "success": true,
  "data": {},
  "meta": {
    "request_id": "req_12345",
    "timestamp": "2025-08-29T12:00:00Z",
    "processing_time": 0.123
  }
}
```

### ページネーション

```json
{
  "data": [],
  "pagination": {
    "total": 1000,
    "limit": 100,
    "offset": 0,
    "has_next": true,
    "has_prev": false
  }
}
```

## WebSocket対応

### リアルタイムデータ配信

```javascript
// クライアント側実装例
const ws = new WebSocket('ws://localhost:8000/ws/realtime');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

// サブスクライブ
ws.send(JSON.stringify({
  action: 'subscribe',
  data_types: ['0B12', '0B11'],
  race_ids: ['202508290503091100']
}));
```

## パフォーマンス最適化

### シンプルな2層キャッシュ戦略

```
クライアント
    ↓ 
L1: メモリキャッシュ (0.01ms)
    ↓ キャッシュミス時
L2: Redis [オプション] (1-2ms)  
    ↓ キャッシュミス時
JVLink COM
```

### キャッシュTTL設定

| データ種別 | メモリTTL | Redis TTL | 理由 |
|-----------|----------|-----------|------|
| RACE（確定） | 5分 | 24時間 | 不変データ |
| 0B系（リアルタイム） | 1分 | 1分 | 頻繁更新 |
| HOSE/HOYU（マスタ） | 5分 | 24時間 | 低頻度更新 |
| その他 | 5分 | 10分 | デフォルト |

### 実測パフォーマンス

| シナリオ | レスポンス時間 | 改善率 |
|---------|--------------|--------|
| L1キャッシュヒット | **0.01ms** | 99.9% |
| L2キャッシュヒット | 1-2ms | 95% |
| キャッシュミス | 20-40ms | - |

## デプロイメント

### Docker構成

```dockerfile
FROM python:3.12-windowsservercore

# 32-bit Python環境構築
RUN choco install python3-x86 -y

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Windows Service登録

```python
# Windows Serviceとして登録
import win32serviceutil

class JRAVANAPIService(win32serviceutil.ServiceFramework):
    _svc_name_ = "JRAVANAPIService"
    _svc_display_name_ = "JRA-VAN REST API Service"
    
    def SvcDoRun(self):
        # FastAPIサーバー起動
        uvicorn.run(app, host="0.0.0.0", port=8000)
```

## セキュリティ考慮事項

1. **通信暗号化**: HTTPS必須（Let's Encrypt推奨）
2. **入力検証**: すべての入力パラメータをバリデーション
3. **SQLインジェクション対策**: ORMを使用
4. **レート制限**: DDoS攻撃対策
5. **ログ記録**: アクセスログ、エラーログの記録
6. **CORS設定**: 許可するオリジンを明示的に設定

## 監視・運用

### ヘルスチェック

```bash
# Prometheusメトリクス
GET /metrics

# アプリケーションメトリクス
- jvlink_connection_status
- api_request_duration_seconds
- api_request_total
- cache_hit_ratio
```

### ログ出力

```json
{
  "timestamp": "2025-08-29T12:00:00Z",
  "level": "INFO",
  "message": "API request received",
  "context": {
    "request_id": "req_12345",
    "endpoint": "/api/v1/data/RACE",
    "user_id": "user_123",
    "duration": 0.123
  }
}
```

## 実装例

### シンプルなFastAPI実装（100行で動作）

```python
# main.py - 最小限の実装
from fastapi import FastAPI, HTTPException
from cachetools import TTLCache
import win32com.client
import pickle

# シンプルなキャッシュ
cache = TTLCache(maxsize=500, ttl=300)  # 5分キャッシュ

# FastAPIアプリケーション
app = FastAPI(title="JRA-VAN REST API")

# JVLink接続（グローバルで管理）
jvlink = None

@app.on_event("startup")
def startup():
    """起動時にJVLink初期化"""
    global jvlink
    try:
        jvlink = win32com.client.Dispatch("JVDTLab.JVLink")
        jvlink.JVInit("UMANARI1.0")
    except Exception as e:
        print(f"JVLink init error: {e}")

@app.get("/health")
def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy" if jvlink else "error",
        "cache_size": len(cache),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/data/{dataspec}")
def get_data(dataspec: str, from_time: str = ""):
    """データ取得エンドポイント"""
    # キャッシュチェック
    cache_key = f"{dataspec}:{from_time}"
    if cache_key in cache:
        return {"data": cache[cache_key], "cached": True}
    
    # JVLinkから取得
    if not jvlink:
        raise HTTPException(status_code=503, detail="JVLink not initialized")
    
    try:
        # JVOpen
        ret = jvlink.JVOpen(dataspec, from_time, 1, 0, 0, "")
        if ret < 0:
            raise HTTPException(status_code=500, detail=f"JVOpen error: {ret}")
        
        # データ読み込み
        records = []
        buf = " " * 10000
        size = 10000
        fname = ""
        
        while True:
            ret = jvlink.JVRead(buf, size, fname)
            if ret == 0:  # 完了
                break
            elif ret > 0:  # データあり
                records.append({
                    "type": buf[:2],
                    "data": buf[:ret].strip()
                })
        
        jvlink.JVClose()
        
        # キャッシュに保存
        cache[cache_key] = records
        
        return {"data": records, "cached": False}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 起動
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### クライアント実装例

```python
# client.py
import httpx
import asyncio
from typing import Optional, Dict, List

class JRAVANAPIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_race_data(self, date: str) -> List[Dict]:
        """レースデータ取得"""
        response = await self.client.get(
            f"{self.base_url}/api/v1/data/RACE",
            params={"from_time": f"{date}000000"}
        )
        response.raise_for_status()
        return response.json()["records"]
    
    async def get_odds(self, race_id: str, odds_type: str = "win") -> Dict:
        """オッズ情報取得"""
        response = await self.client.get(
            f"{self.base_url}/api/v1/realtime/odds/{race_id}",
            params={"type": odds_type}
        )
        response.raise_for_status()
        return response.json()
    
    async def stream_realtime_data(self, data_spec: str):
        """リアルタイムデータストリーム"""
        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/v1/data/stream",
            json={"data_spec": data_spec}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data = json.loads(line[5:])
                    yield data

# 使用例
async def main():
    client = JRAVANAPIClient()
    
    # レースデータ取得
    races = await client.get_race_data("20250829")
    for race in races:
        print(f"Race: {race['data']['race_info']['hondai']}")
    
    # オッズ取得
    odds = await client.get_odds("202508290503091100")
    print(f"Win odds: {odds}")
    
    # ストリーミング
    async for data in client.stream_realtime_data("0B12"):
        print(f"Realtime: {data}")

if __name__ == "__main__":
    asyncio.run(main())
```

## JVLinkエラーコード詳細

### エラーコード対応表

| エラーコード | 定数名 | 説明 | HTTPステータス | 対処方法 |
|------------|--------|------|--------------|----------|
| -100 | JV_ERR_ARG | パラメータエラー | 400 | パラメータを確認 |
| -101 | JV_ERR_NOT_INIT | 初期化されていない | 503 | JVInitを実行 |
| -102 | JV_ERR_INIT_FAILED | 初期化に失敗 | 500 | 環境を確認 |
| -103 | JV_ERR_ALREADY_OPEN | オープン済み | 409 | JVCloseを実行 |
| -111 | JV_ERR_DOWNLOAD | ダウンロード失敗 | 502 | ネットワーク確認 |
| -112 | JV_ERR_FILE_NOT_FOUND | ファイルが見つからない | 404 | ファイルパス確認 |
| -113 | JV_ERR_FILE_ACCESS | ファイルアクセスエラー | 403 | アクセス権限確認 |
| -114 | JV_ERR_NO_DATA | 該当データなし | 404 | データ範囲を確認 |
| -115 | JV_ERR_READING | 前回ファイル読込中 | 409 | 読込完了を待つ |
| -116 | JV_ERR_END_OF_DATA | 該当データ終了 | 200 | 正常終了 |
| -201 | JV_ERR_NOT_INITIALIZED | 初期化されていません | 503 | JVInitを実行 |
| -202 | JV_ERR_NOT_OPENED | オープンされていません | 503 | JVOpenを実行 |
| -203 | JV_ERR_NOT_READING | 読込み中ではありません | 409 | JVOpenを実行 |
| -301 | JV_ERR_KEY_READ | キー読込み失敗 | 401 | キーファイル確認 |
| -302 | JV_ERR_KEY_ALREADY_SET | キー設定済み | 409 | 処理を継続 |
| -303 | JV_ERR_KEY_AUTH | キー認証エラー | 401 | キーを再設定 |
| -401 | JV_ERR_FILE_CREATE | ファイル作成失敗 | 500 | ディスク容量確認 |
| -402 | JV_ERR_FILE_WRITE | ファイル書込み失敗 | 500 | 書込み権限確認 |
| -411 | JV_ERR_SETUP_READ | セットアップ読込み失敗 | 500 | JV-Link再インストール |
| -412 | JV_ERR_TIME_READ | 時刻読込み失敗 | 500 | システム時刻確認 |
| -421 | JV_ERR_MONDAY_CHECK | 月曜日のチェック | 503 | 月曜日はメンテナンス |
| -502 | JV_ERR_DIALOG_CANCEL | ダイアログがキャンセルされた | 499 | ユーザー操作 |
| -503 | JV_ERR_DIALOG_TIMEOUT | ダイアログタイムアウト | 408 | タイムアウト値調整 |

## 実装ガイドライン

### 1. 環境構築

```bash
# 32-bit Python環境の構築
python -m venv .venv --copies
.venv\Scripts\activate

# 必要パッケージのインストール
pip install fastapi uvicorn[standard] pywin32 httpx redis celery

# JV-Linkのインストール確認
python -c "import win32com.client; print(win32com.client.Dispatch('JVDTLab.JVLink'))"
```

### 2. プロジェクト構成

```
jra-van-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPIアプリケーション
│   ├── config.py            # 設定管理
│   ├── dependencies.py      # 依存性注入
│   ├── models/              # Pydanticモデル
│   │   ├── __init__.py
│   │   ├── race.py
│   │   ├── odds.py
│   │   └── horse.py
│   ├── services/            # ビジネスロジック
│   │   ├── __init__.py
│   │   ├── jvlink.py       # JVLink操作
│   │   ├── parser.py       # データパーサー
│   │   └── cache.py        # キャッシュ管理
│   ├── api/                 # APIエンドポイント
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── data.py
│   │   │   ├── realtime.py
│   │   │   └── master.py
│   └── utils/               # ユーティリティ
│       ├── __init__.py
│       └── errors.py
├── tests/                   # テスト
├── scripts/                 # スクリプト
│   └── install_service.py  # Windowsサービス登録
├── requirements.txt
└── docker-compose.yml
```

### 3. データ構造との連携

REST APIレスポンスは[データ構造仕様書](../specifications/DATA_STRUCTURE_SPECIFICATION.md)に定義された構造体に準拠します。

```python
# models/race.py
from pydantic import BaseModel
from typing import Optional

class RaceId(BaseModel):
    """レースIDキー (KS1)"""
    year: str          # 開催年 (4桁)
    month_day: str     # 開催月日 (4桁)
    jyo_cd: str        # 競馬場コード (2桁)
    kaiji: str         # 開催回 (2桁)
    nichiji: str       # 開催日 (2桁)
    race_num: str      # レース番号 (2桁)

class RaceInfo(BaseModel):
    """レース情報 (RACE_INFO)"""
    youbi_cd: str      # 曜日コード
    toku_num: str      # 特別競走番号
    hondai: str        # 競走名本題
    fukudai: str       # 競走名副題
    kakko: str         # 競走名カッコ内
    hondai_eng: str    # 競走名本題欧字
    fukudai_eng: str   # 競走名副題欧字
    kakko_eng: str     # 競走名カッコ内欧字
    ryakusyo_10: str   # 競走名略称10字
    ryakusyo_6: str    # 競走名略称6字
    ryakusyo_3: str    # 競走名略称3字
    kubun: str         # 競走名区分
    jyusyo_kaiji: str  # 重賞回次
```

### 4. パフォーマンス最適化実装

```python
# services/cache.py
import redis
import json
from typing import Optional, Any
from datetime import timedelta

class CacheService:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)
        
    def get(self, key: str) -> Optional[Any]:
        """キャッシュ取得"""
        data = self.redis.get(key)
        if data:
            return json.loads(data)
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """キャッシュ設定"""
        self.redis.setex(
            key,
            timedelta(seconds=ttl),
            json.dumps(value, ensure_ascii=False)
        )
    
    def invalidate_pattern(self, pattern: str):
        """パターンマッチでキャッシュ削除"""
        for key in self.redis.scan_iter(pattern):
            self.redis.delete(key)

# キャッシュデコレーター
from functools import wraps

def cached(ttl: int = 3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # キャッシュキー生成
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # キャッシュチェック
            cached_data = cache_service.get(cache_key)
            if cached_data:
                return cached_data
            
            # 実行とキャッシュ
            result = await func(*args, **kwargs)
            cache_service.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator
```

## 次のステップ

1. **実装フェーズ**
   - FastAPIサーバーの基本実装
   - JVLinkラッパーサービスの実装
   - キャッシュレイヤーの実装

2. **テストフェーズ**
   - 単体テストの作成
   - 統合テストの実装
   - 負荷テストの実施

3. **デプロイメントフェーズ**
   - Windows Service登録スクリプトの作成
   - Docker環境の構築
   - CI/CDパイプラインの構築

4. **ドキュメント整備**
   - OpenAPI仕様書の自動生成
   - クライアントSDKの開発
   - 利用ガイドの作成