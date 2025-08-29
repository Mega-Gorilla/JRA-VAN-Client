# JRA-VAN REST API Server

[![Python Version](https://img.shields.io/badge/python-3.8%2B%20(32bit)-blue)](https://www.python.org)
[![Windows](https://img.shields.io/badge/platform-Windows-lightgrey)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

JRA-VAN DataLabのデータをREST API経由で提供する高性能サーバー

## 🎯 特徴

- 🚀 **REST API サーバー** - FastAPIによる高性能HTTPインターフェース
- 💾 **2層キャッシュシステム** - メモリ + Redis による高速レスポンス
- 🔄 **64bit互換** - 32bit JVLinkを64bitアプリから利用可能
- ⚡ **リアルタイムデータ対応** - オッズ・馬体重の速報取得
- 📊 **JSON形式** - 扱いやすいデータフォーマット

## 🏗️ アーキテクチャ

```
┌─────────────────────┐
│  64-bit Application │  Python, Node.js, .NET etc.
└──────────┬──────────┘
           │ HTTP/REST
┌──────────▼──────────┐
│   REST API Server   │  32-bit Python + FastAPI
│  ┌───────────────┐  │
│  │  Memory Cache │  │  TTLCache (L1)
│  └───────┬───────┘  │
│  ┌───────▼───────┐  │
│  │  Redis Cache  │  │  Optional (L2)
│  └───────┬───────┘  │
└──────────┬──────────┘
           │ COM
┌──────────▼──────────┐
│      JVLink COM     │  32-bit Only
└─────────────────────┘
```

## 📋 システム要件

| 項目 | 最小要件 | 推奨 |
|------|---------|------|
| OS | Windows 10 | Windows 11 |
| Python | 3.8 (32bit) ⚠️ | 3.11以上 (32bit) |
| メモリ | 4GB | 8GB以上 |
| ディスク | 10GB | 50GB以上 |
| JRA-VAN | Data Lab. SDK | 同左 |
| 契約 | JRA-VAN DataLab（月額2,090円） | 同左 |

⚠️ **重要**: JVLinkは32bit COMコンポーネントのため、**32bit版Python**が必要です

## 🚀 インストール

### 1. リポジトリの取得

```bash
git clone https://github.com/Mega-Gorilla/jra-van-client.git
cd jra-van-client
```

### 2. 32bit Python環境の準備

```bash
# 32bit Pythonか確認
python -c "import sys; print('32-bit OK' if sys.maxsize <= 2**32 else '64-bit ERROR: 32bit版が必要')"

# 仮想環境作成
python -m venv .venv
.venv\Scripts\activate

# 依存関係インストール
pip install -r api/requirements.txt
```

### 3. JV-Linkのインストール

1. [JRA-VAN公式サイト](https://jra-van.jp/dlb/)からSDKをダウンロード
2. SDK内の`JV-Link.exe`インストーラーを実行
3. `C:\Windows\SysWOW64\JVDTLAB\JVDTLAB.dll`が配置されることを確認

※ SDKはこのリポジトリの`JRA-VAN Data Lab. SDK Ver4.9.0.2\JV-Link\JV-Link.exe`にも含まれています

### 4. 接続テスト

```bash
# JVLink接続確認
.venv\Scripts\python.exe api\test_connection.py
```

## 🎮 REST APIサーバーの起動

### 開発サーバー

```bash
# 仮想環境を有効化
.venv\Scripts\activate

# サーバー起動（自動リロード付き）
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 本番サーバー

```bash
# 仮想環境を有効化
.venv\Scripts\activate

# 本番サーバー起動
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 1
```

⚠️ **注意**: JVLink COMの制約により、ワーカー数は1に制限されます

## 📡 API エンドポイント

### ヘルスチェック

```bash
GET http://localhost:8000/health
```

レスポンス例：
```json
{
  "status": "healthy",
  "jvlink_connected": true,
  "cache_memory_size": 42,
  "cache_redis_available": false,
  "timestamp": "2025-08-29T10:30:00"
}
```

### データ取得

```bash
GET http://localhost:8000/api/v1/data/{dataspec}
```

パラメータ：
- `dataspec` (必須): データ種別コード（例: "RACE", "0B12", "HOYU"）
- `from_time` (オプション): 取得開始日時（YYYYMMDDHHmmSS形式）
- `option` (オプション): 取得オプション（1: 通常, 2: 今週, 3: リアルタイム）

#### 使用例

```bash
# レースデータ取得
curl "http://localhost:8000/api/v1/data/RACE?from_time=20250101000000"

# リアルタイムオッズ取得
curl "http://localhost:8000/api/v1/data/0B12?option=3"

# 馬主マスタ取得
curl "http://localhost:8000/api/v1/data/HOYU"
```

## 💻 クライアント実装例

### Python (requests)

```python
import requests

# APIサーバーのURL
API_BASE = "http://localhost:8000"

# ヘルスチェック
response = requests.get(f"{API_BASE}/health")
print(response.json())

# レースデータ取得
response = requests.get(f"{API_BASE}/api/v1/data/RACE", params={
    "from_time": "20250101000000",
    "option": 1
})
data = response.json()
print(f"取得件数: {data['count']}, キャッシュ: {data['cached']}")
```

### JavaScript (fetch)

```javascript
// ヘルスチェック
fetch('http://localhost:8000/health')
  .then(res => res.json())
  .then(data => console.log(data));

// レースデータ取得
fetch('http://localhost:8000/api/v1/data/RACE?from_time=20250101000000')
  .then(res => res.json())
  .then(data => {
    console.log(`Records: ${data.count}, Cached: ${data.cached}`);
    data.data.forEach(record => {
      console.log(record.record_type, record.data);
    });
  });
```

### C# (.NET)

```csharp
using System.Net.Http;
using System.Text.Json;

var client = new HttpClient();

// ヘルスチェック
var response = await client.GetAsync("http://localhost:8000/health");
var json = await response.Content.ReadAsStringAsync();
Console.WriteLine(json);

// レースデータ取得
response = await client.GetAsync("http://localhost:8000/api/v1/data/RACE?from_time=20250101000000");
json = await response.Content.ReadAsStringAsync();
var data = JsonSerializer.Deserialize<Dictionary<string, object>>(json);
Console.WriteLine($"Records: {data["count"]}");
```

## ⚡ パフォーマンス最適化

### キャッシュ戦略

| データ種別 | TTL | 説明 |
|-----------|-----|------|
| リアルタイム (0B*) | 60秒 | オッズ、馬体重など |
| マスタデータ | 24時間 | 馬主、調教師など |
| その他 | 10分 | レース、成績など |

### Redis導入（オプション）

分散キャッシュによる更なる高速化：

```bash
# Redis起動（Docker）
docker run -d -p 6379:6379 redis:alpine

# Redisが利用可能な場合、自動的に2層キャッシュが有効化
```

## 📊 取得可能なデータ

### 基本データ
- **RACE** - レース詳細情報
- **HOSE** - 競走馬マスタ  
- **HOYU** - 馬主マスタ
- **YSCH** - 開催スケジュール

### リアルタイムデータ
- **0B12** - 単勝・複勝オッズ
- **0B15** - 馬連オッズ
- **0B20** - 馬単オッズ
- **0B30** - 3連複オッズ
- **0B31** - 3連単オッズ
- **0B11** - 馬体重

詳細は [docs/specifications/](docs/specifications/) を参照

## 📁 プロジェクト構成

```
jra-van-client/
├── api/
│   ├── main.py            # FastAPI サーバー
│   ├── cache.py           # 2層キャッシュ実装
│   ├── test_connection.py # 接続テスト
│   └── requirements.txt   # 依存関係
├── docs/
│   ├── api-design/        # API設計書
│   └── specifications/    # データ仕様書
├── JRA-VAN Data Lab. SDK Ver4.9.0.2/
│   └── JV-Link/
│       └── JV-Link.exe    # JVLinkインストーラー
└── README.md
```

## 🔧 トラブルシューティング

### JVLink接続エラー

```
Error: 0x800700c1 - Not a valid Win32 application
```
→ 64bit Pythonを使用している。32bit Pythonに切り替える

### COMオブジェクト作成失敗

```
pywintypes.com_error: (-2147221005, 'Invalid class string', None, None)
```
→ JV-Link.exeインストーラーを実行してDLLを配置する

### キャッシュ関連

Redisが利用できない場合：
- 自動的にメモリキャッシュのみで動作
- パフォーマンスへの影響は限定的

## 🤝 コントリビューション

プルリクエスト歓迎！バグ報告は[Issues](https://github.com/Mega-Gorilla/jra-van-client/issues)へ。

## 📝 ライセンス

MIT License with Additional Terms - 詳細は[LICENSE](LICENSE)を参照

### ⚠️ JRA-VANデータ利用に関する重要事項
- JRA-VANデータの利用には**別途契約**（月額2,090円）が必要です
- データ利用時は**JRA-VAN利用規約**を遵守してください
- 本ソフトウェアのライセンスは**データ利用権を付与するものではありません**

## 🙏 謝辞

- JRA-VAN DataLab様 - データ提供
- pywin32開発者の皆様 - COM接続サポート

---

**JRA-VAN REST API Server** - Built with ❤️ by [Mega-Gorilla](https://github.com/Mega-Gorilla)  
競馬データ分析を、もっと簡単に。