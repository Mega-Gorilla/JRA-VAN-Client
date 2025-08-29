# シンプル化されたキャッシュアーキテクチャ

## SQLiteは本当に必要か？

### 答え: **不要です**

REST APIとして完結させる場合、SQLiteは過剰な実装です。以下の理由から、**メモリ + Redisの2層構造**で十分です：

## 1. なぜSQLiteが不要なのか

### 1.1 REST APIの役割
```
REST APIの本質的な役割：
- JVLink COMへのプロキシ
- データ変換とキャッシング
- リアルタイムアクセスの提供

NOT：
- データウェアハウス
- 長期データストレージ
- 分析基盤
```

### 1.2 SQLite導入のデメリット
| 問題点 | 影響 |
|--------|------|
| 複雑性増加 | 開発・保守コスト上昇 |
| ディスクI/O | パフォーマンス低下の要因 |
| データ同期 | JVLinkとの二重管理 |
| ストレージ管理 | 容量監視・削除処理が必要 |
| バックアップ | 運用負荷増加 |

### 1.3 JVLink自体がデータストア
- JVLinkは既にローカルにデータを保持
- 必要に応じてJVLinkから再取得可能
- 二重にデータを保持する意味がない

## 2. シンプルな2層キャッシュアーキテクチャ

### 2.1 推奨アーキテクチャ

```
┌─────────────────────────────────┐
│         クライアント             │
└─────────────────────────────────┘
                ↓
┌─────────────────────────────────┐
│    L1: メモリキャッシュ          │
│    (Python dict/TTLCache)       │
│    容量: 100-1000件              │
│    TTL: 1-5分                   │
└─────────────────────────────────┘
                ↓
┌─────────────────────────────────┐
│    L2: Redis                    │
│    容量: 制限なし                │
│    TTL: データ種別に応じて       │
└─────────────────────────────────┘
                ↓
┌─────────────────────────────────┐
│    JVLink COM                   │
│    (マスターデータソース)        │
└─────────────────────────────────┘
```

### 2.2 シンプルな実装

```python
# simple_cache.py
from typing import Optional, Any, Dict
import json
import hashlib
import redis
from cachetools import TTLCache
import pickle

class SimpleTwoLayerCache:
    """シンプルな2層キャッシュ"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        # L1: メモリキャッシュ
        self.memory_cache = TTLCache(maxsize=500, ttl=300)  # 5分
        
        # L2: Redis
        self.redis_client = redis.Redis.from_url(
            redis_url,
            decode_responses=False  # バイナリデータを扱うため
        )
    
    def _make_key(self, dataspec: str, **kwargs) -> str:
        """キャッシュキー生成"""
        key_dict = {"dataspec": dataspec, **kwargs}
        key_str = json.dumps(key_dict, sort_keys=True)
        return f"jra:{hashlib.md5(key_str.encode()).hexdigest()}"
    
    async def get(self, dataspec: str, **kwargs) -> Optional[Any]:
        """キャッシュ取得（シンプル）"""
        key = self._make_key(dataspec, **kwargs)
        
        # L1チェック
        if key in self.memory_cache:
            return self.memory_cache[key]
        
        # L2チェック
        data = self.redis_client.get(key)
        if data:
            result = pickle.loads(data)
            self.memory_cache[key] = result  # L1に昇格
            return result
        
        return None
    
    async def set(self, data: Any, dataspec: str, **kwargs):
        """キャッシュ保存（シンプル）"""
        key = self._make_key(dataspec, **kwargs)
        ttl = self._get_ttl(dataspec)
        
        # L1保存
        self.memory_cache[key] = data
        
        # L2保存
        if ttl > 0:
            self.redis_client.setex(
                key,
                ttl,
                pickle.dumps(data)
            )
    
    def _get_ttl(self, dataspec: str) -> int:
        """データ種別ごとのTTL（秒）"""
        # シンプルな3段階のみ
        if dataspec[:4] in ['RACE', 'HOSE', 'HOYU']:  # 確定データ
            return 86400  # 24時間
        elif dataspec[:2] == '0B':  # リアルタイムデータ
            return 60  # 1分
        else:  # その他
            return 600  # 10分
```

## 3. さらにシンプル：Redisのみの構成

### 3.1 最小構成

```python
# minimal_cache.py
import redis
import json
import pickle
from typing import Optional, Any

class MinimalCache:
    """最小限のキャッシュ実装"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=False
        )
    
    def get(self, key: str) -> Optional[Any]:
        """取得"""
        data = self.redis_client.get(f"jra:{key}")
        return pickle.loads(data) if data else None
    
    def set(self, key: str, value: Any, ttl: int = 600):
        """保存"""
        self.redis_client.setex(
            f"jra:{key}",
            ttl,
            pickle.dumps(value)
        )

# FastAPIでの使用例
from fastapi import FastAPI, Depends
import win32com.client

app = FastAPI()
cache = MinimalCache()

@app.get("/api/v1/data/{dataspec}")
async def get_data(dataspec: str, from_time: str = ""):
    # キャッシュキー
    cache_key = f"{dataspec}:{from_time}"
    
    # キャッシュチェック
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # JVLinkから取得
    jvlink = win32com.client.Dispatch("JVDTLab.JVLink")
    data = fetch_from_jvlink(jvlink, dataspec, from_time)
    
    # キャッシュに保存
    ttl = 60 if dataspec[:2] == "0B" else 600
    cache.set(cache_key, data, ttl)
    
    return data
```

## 4. メモリのみ（最速だが限定的）

### 4.1 組み込みdict使用

```python
# memory_only_cache.py
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, Tuple

class MemoryOnlyCache:
    """メモリのみの超シンプルキャッシュ"""
    
    def __init__(self):
        self.cache: Dict[str, Tuple[Any, datetime]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            value, expires = self.cache[key]
            if expires > datetime.now():
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        expires = datetime.now() + timedelta(seconds=ttl)
        self.cache[key] = (value, expires)
    
    def cleanup(self):
        """期限切れエントリの削除"""
        now = datetime.now()
        expired = [k for k, (_, exp) in self.cache.items() if exp <= now]
        for k in expired:
            del self.cache[k]
```

## 5. 推奨構成の比較

| 構成 | メリット | デメリット | 推奨ケース |
|------|---------|-----------|-----------|
| **メモリ + Redis** | バランス良好、スケーラブル | Redis必要 | **本番環境（推奨）** |
| **Redisのみ** | シンプル、永続化可能 | 若干遅い | 小規模環境 |
| **メモリのみ** | 最速、依存なし | 容量制限、揮発性 | 開発・テスト環境 |
| ~~メモリ + Redis + SQLite~~ | - | 過剰に複雑 | **非推奨** |

## 6. 実装の段階的アプローチ

### Step 1: メモリキャッシュから開始
```python
# 最初はシンプルに
cache = {}

def get_data(dataspec):
    if dataspec in cache:
        return cache[dataspec]
    
    data = fetch_from_jvlink(dataspec)
    cache[dataspec] = data
    return data
```

### Step 2: TTL追加
```python
# TTLCache導入
from cachetools import TTLCache
cache = TTLCache(maxsize=100, ttl=300)
```

### Step 3: Redis追加（必要に応じて）
```python
# スケールが必要になったら
import redis
redis_client = redis.Redis()

def get_data(dataspec):
    # メモリ → Redis → JVLink
    pass
```

## 7. パフォーマンス比較

| キャッシュ構成 | ヒット時レスポンス | メモリ使用量 | 実装複雑度 |
|--------------|------------------|------------|-----------|
| メモリのみ | **0.01ms** | 低-中 | **最低** |
| Redis のみ | 1-2ms | 最低 | 低 |
| メモリ + Redis | **0.01-2ms** | 低 | **中** |
| ~~+ SQLite~~ | 5-10ms | 高 | 高 |

## 8. 結論

### 推奨実装：**メモリ + Redis の2層構造**

```python
# recommended_implementation.py
from typing import Optional, Any
import redis
from cachetools import TTLCache
import pickle
import hashlib
import json

class RecommendedCache:
    """推奨されるシンプルなキャッシュ実装"""
    
    def __init__(self):
        # L1: 高速メモリキャッシュ
        self.l1 = TTLCache(maxsize=200, ttl=60)  # 1分
        
        # L2: Redis（オプション、スケール時に追加）
        try:
            self.l2 = redis.Redis(host='localhost', port=6379)
            self.l2.ping()  # 接続確認
        except:
            self.l2 = None  # Redisなしでも動作
    
    def get(self, dataspec: str, **params) -> Optional[Any]:
        """2層キャッシュから取得"""
        key = self._make_key(dataspec, **params)
        
        # L1チェック
        if key in self.l1:
            return self.l1[key]
        
        # L2チェック（利用可能な場合）
        if self.l2:
            try:
                data = self.l2.get(key)
                if data:
                    value = pickle.loads(data)
                    self.l1[key] = value  # L1に昇格
                    return value
            except:
                pass  # Redisエラーは無視
        
        return None
    
    def set(self, dataspec: str, value: Any, **params):
        """2層キャッシュに保存"""
        key = self._make_key(dataspec, **params)
        
        # L1保存
        self.l1[key] = value
        
        # L2保存（利用可能な場合）
        if self.l2:
            try:
                ttl = 3600 if dataspec[:4] == 'RACE' else 300
                self.l2.setex(key, ttl, pickle.dumps(value))
            except:
                pass  # Redisエラーは無視
    
    def _make_key(self, dataspec: str, **params) -> str:
        """シンプルなキー生成"""
        key_data = {'ds': dataspec, **params}
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()[:16]
```

### なぜこれがベストか

1. **シンプル**: 理解・保守が容易
2. **高速**: メモリキャッシュで0.01ms
3. **スケーラブル**: Redis追加で水平展開可能
4. **堅牢**: Redisダウンしても動作継続
5. **実用的**: 実際の要件に対して十分

SQLiteは不要です。シンプルに保ちましょう！