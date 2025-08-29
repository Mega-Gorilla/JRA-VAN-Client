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
┌─────────────────────────────────────────────────────────┐
│           JRA-VAN REST API Server (32-bit Python)       │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   FastAPI    │  │   Manager    │  │   Cache      │ │
│  │   Endpoint   │──│   Service    │──│   Service    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│           │                │                            │
│           └────────────────┼────────────────────────────┘
│                            ▼                            │
│                  ┌──────────────────┐                   │
│                  │  JVLink COM      │                   │
│                  │  (JVDTLAB.dll)   │                   │
│                  └──────────────────┘                   │
└──────────────────────────────────────────────────────────┘
```

### コンポーネント説明

| コンポーネント | 説明 | 技術スタック |
|--------------|------|------------|
| REST API Server | HTTPエンドポイント提供 | FastAPI, uvicorn (32-bit) |
| Manager Service | JVLink操作の管理 | Python 3.12 (32-bit) |
| Cache Service | データキャッシュ管理 | SQLite/Redis |
| Windows Service | サービス常駐化 | pywin32 |

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

### キャッシュ戦略

| データ種別 | キャッシュ期間 | 更新タイミング |
|-----------|-------------|--------------|
| マスタデータ | 24時間 | 日次バッチ |
| レース結果 | 永続 | 確定後不変 |
| オッズ | 1分 | リアルタイム |
| 馬体重 | 30分 | 発表時 |

### 非同期処理

- 大量データ取得はバックグラウンドジョブで処理
- Celeryによるタスクキュー管理
- Redis/RabbitMQによるメッセージブローカー

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

## 次のステップ

1. FastAPIによる実装
2. Swagger/OpenAPI仕様書の自動生成
3. クライアントSDKの開発（Python, JavaScript, Go）
4. 負荷テストとパフォーマンスチューニング
5. CI/CDパイプラインの構築