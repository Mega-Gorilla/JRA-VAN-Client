# REST API パフォーマンス最適化計画

## 1. パフォーマンスボトルネック分析

### 1.1 現状のレイテンシ構成
```
クライアント要求
    ├─ ネットワーク往復: 1-5ms
    ├─ FastAPI処理: 1-3ms
    ├─ JVLink COM呼び出し: 10-30ms
    ├─ データパース: 5-15ms
    ├─ JSON変換: 2-5ms
    └─ レスポンス返送: 1-5ms
    
合計: 20-63ms（平均約40ms）
```

### 1.2 主要ボトルネック
| ボトルネック | 影響度 | 改善可能性 | 優先度 |
|------------|--------|-----------|--------|
| JVLink COM呼び出し | 高（50%） | 中 | 高 |
| データパース | 中（25%） | 高 | 高 |
| 大量データ転送 | 高（状況依存） | 高 | 高 |
| 同期的処理 | 中（20%） | 高 | 中 |

## 2. シンプルな2層キャッシュ戦略

### 2.1 キャッシュアーキテクチャ

```
┌─────────────────────────────────────────────┐
│              クライアント                    │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│          L1: メモリキャッシュ                │
│          (TTLCache, 0.01ms)                 │
│          容量: 200-500エントリ               │
│          TTL: 1-5分                         │
└─────────────────────────────────────────────┘
                    ↓ キャッシュミス時
┌─────────────────────────────────────────────┐
│          L2: Redis (オプション)              │
│          (分散キャッシュ, 1-2ms)            │
│          容量: 無制限                        │
│          TTL: データ種別依存                 │
└─────────────────────────────────────────────┘
                    ↓ キャッシュミス時
┌─────────────────────────────────────────────┐
│          JVLink COM                          │
│          (マスターデータソース)              │
└─────────────────────────────────────────────┘
```

**ポイント**: SQLiteは不要。JVLink自体がデータストアとして機能するため、追加の永続化層は複雑性を増すだけです。

### 2.2 シンプルで効果的なキャッシュ実装

```python
# simple_cache_service.py
from typing import Optional, Any, Dict
import json
import hashlib
import redis
from cachetools import TTLCache
import pickle
import asyncio

class SimpleTwoLayerCache:
    """シンプルで高性能な2層キャッシュ"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        # L1: 超高速メモリキャッシュ
        self.l1_cache = TTLCache(maxsize=500, ttl=300)  # 5分
        
        # L2: Redis (オプション - 無くても動作)
        try:
            self.redis = redis.Redis.from_url(redis_url, decode_responses=False)
            self.redis.ping()  # 接続確認
            self.redis_available = True
        except:
            self.redis = None
            self.redis_available = False
            print("Redis not available, using memory cache only")
    
    def _make_key(self, dataspec: str, **kwargs) -> str:
        """効率的なキャッシュキー生成"""
        key_dict = {"ds": dataspec, **kwargs}
        key_str = json.dumps(key_dict, sort_keys=True)
        # MD5ハッシュの最初の16文字で十分
        return hashlib.md5(key_str.encode()).hexdigest()[:16]
    
    async def get(self, dataspec: str, **kwargs) -> Optional[Any]:
        """2層キャッシュからデータ取得"""
        cache_key = self._make_key(dataspec, **kwargs)
        
        # L1: メモリキャッシュ確認 (0.01ms)
        if cache_key in self.l1_cache:
            return self.l1_cache[cache_key]
        
        # L2: Redis確認 (1-2ms)
        if self.redis_available:
            try:
                data = self.redis.get(f"jra:{cache_key}")
                if data:
                    result = pickle.loads(data)
                    self.l1_cache[cache_key] = result  # L1に昇格
                    return result
            except Exception as e:
                print(f"Redis error: {e}")
                # Redisエラーでも処理継続
        
        return None
    
    async def set(self, data: Any, dataspec: str, **kwargs):
        """2層キャッシュにデータ保存"""
        cache_key = self._make_key(dataspec, **kwargs)
        ttl = self._get_optimal_ttl(dataspec)
        
        # L1: メモリキャッシュに即座に保存
        self.l1_cache[cache_key] = data
        
        # L2: Redisに非同期保存（利用可能な場合）
        if self.redis_available:
            asyncio.create_task(self._save_to_redis(cache_key, data, ttl))
    
    def _get_optimal_ttl(self, dataspec: str) -> int:
        """データ種別に応じた最適なTTL（秒）"""
        ttl_map = {
            # マスタデータ（長期キャッシュ）
            'HOSE': 86400,  # 24時間
            'HOYU': 86400,  # 24時間
            'YSCH': 604800,  # 1週間
            'RACE': 86400,  # 24時間（確定後不変）
            
            # リアルタイムデータ（短期キャッシュ）
            '0B12': 60,     # 1分（単複オッズ）
            '0B15': 60,     # 1分（馬連オッズ）
            '0B30': 300,    # 5分（レース結果速報）
            
            # その他
            'DIFF': 300,    # 5分
            'SLOP': 1800,   # 30分
            'MING': 3600,   # 1時間
        }
        return ttl_map.get(dataspec[:4], 600)  # デフォルト10分
    
    async def _save_to_redis(self, key: str, data: Any, ttl: int):
        """Redisへの非同期保存"""
        try:
            if ttl > 0:
                serialized = pickle.dumps(data)
                self.redis.setex(f"jra:{key}", ttl, serialized)
        except Exception as e:
            print(f"Redis save error: {e}")
            # エラーでも処理継続

# 使用例: FastAPIでの実装
@app.get("/api/v1/data/{dataspec}")
async def get_data(dataspec: str, from_time: str = ""):
    # キャッシュチェック
    cached = await cache.get(dataspec, from_time=from_time)
    if cached:
        return {"data": cached, "cache": "hit"}
    
    # JVLinkから取得
    data = await fetch_from_jvlink(dataspec, from_time)
    
    # キャッシュに保存
    await cache.set(data, dataspec, from_time=from_time)
    
    return {"data": data, "cache": "miss"}

# 賢いプリフェッチング戦略
class SmartPrefetchManager:
    def __init__(self, cache: SimpleTwoLayerCache):
        self.cache = cache
        self.prefetch_queue = asyncio.Queue()
        self.prefetch_task = None
    
    async def start(self):
        """プリフェッチワーカー起動"""
        self.prefetch_task = asyncio.create_task(self._prefetch_worker())
    
    async def _prefetch_worker(self):
        """バックグラウンドでデータをプリフェッチ"""
        while True:
            try:
                request = await self.prefetch_queue.get()
                
                # キャッシュ確認
                cached = await self.cache.get(**request)
                if not cached:
                    # JVLinkから取得してキャッシュ
                    # ※実際のJVLink呼び出しコード
                    pass
                    
            except Exception as e:
                print(f"Prefetch error: {e}")
            
            await asyncio.sleep(0.1)
    
    async def schedule_prefetch(self, dataspec: str, **kwargs):
        """プリフェッチのスケジュール"""
        # 関連データを予測してプリフェッチ
        if dataspec == 'RACE':
            # レースデータ取得時は関連オッズもプリフェッチ
            await self.prefetch_queue.put({
                'dataspec': '0B12',
                **kwargs
            })
            await self.prefetch_queue.put({
                'dataspec': '0B15',
                **kwargs
            })
```

## 3. 非同期処理最適化

### 3.1 接続プール管理

```python
# connection_pool.py
import asyncio
from typing import List, Optional
import win32com.client
import pythoncom
from contextlib import asynccontextmanager
from queue import Queue
import threading

class JVLinkConnectionPool:
    """JVLink接続プール（スレッドセーフ）"""
    
    def __init__(self, pool_size: int = 5):
        self.pool_size = pool_size
        self.connections = Queue(maxsize=pool_size)
        self.semaphore = asyncio.Semaphore(pool_size)
        self._initialize_pool()
    
    def _initialize_pool(self):
        """接続プールの初期化"""
        for _ in range(self.pool_size):
            # 各接続用のスレッドで初期化
            thread = threading.Thread(target=self._create_connection)
            thread.start()
            thread.join()
    
    def _create_connection(self):
        """COM接続の作成（スレッド内）"""
        pythoncom.CoInitialize()
        try:
            jvlink = win32com.client.Dispatch("JVDTLab.JVLink")
            self.connections.put(jvlink)
        finally:
            pythoncom.CoUninitialize()
    
    @asynccontextmanager
    async def acquire(self):
        """接続の取得"""
        async with self.semaphore:
            # 非同期でセマフォを取得
            connection = await asyncio.get_event_loop().run_in_executor(
                None, self.connections.get
            )
            try:
                yield connection
            finally:
                # 接続をプールに戻す
                await asyncio.get_event_loop().run_in_executor(
                    None, self.connections.put, connection
                )

# 非同期バッチ処理
class AsyncBatchProcessor:
    def __init__(self, pool: JVLinkConnectionPool):
        self.pool = pool
    
    async def batch_get_data(self, requests: List[Dict]) -> List[Any]:
        """複数データの並列取得"""
        tasks = []
        for request in requests:
            task = asyncio.create_task(
                self._get_single_data(**request)
            )
            tasks.append(task)
        
        # 並列実行
        results = await asyncio.gather(*tasks)
        return results
    
    async def _get_single_data(self, dataspec: str, **kwargs):
        """単一データ取得（非同期）"""
        async with self.pool.acquire() as jvlink:
            # スレッドプールで実行
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._jvlink_read,
                jvlink,
                dataspec,
                kwargs
            )
            return result
    
    def _jvlink_read(self, jvlink, dataspec, kwargs):
        """JVLink読み込み（同期）"""
        # COM呼び出しはスレッド内で実行
        pythoncom.CoInitialize()
        try:
            # 実際のJVLink呼び出し
            ret = jvlink.JVOpen(dataspec, kwargs.get('from_time', ''), 1, 0, 0, '')
            # データ読み込み処理
            return self._read_all_data(jvlink)
        finally:
            pythoncom.CoUninitialize()
```

## 4. データ圧縮・転送最適化

### 4.1 レスポンス圧縮

```python
# compression.py
from fastapi import Response
from fastapi.responses import StreamingResponse
import gzip
import brotli
import lz4.frame
from typing import Any, Dict
import json
import msgpack
import orjson

class CompressionMiddleware:
    """動的圧縮ミドルウェア"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope['type'] == 'http':
            headers = dict(scope['headers'])
            accept_encoding = headers.get(b'accept-encoding', b'').decode()
            
            # クライアントがサポートする圧縮方式を確認
            if 'br' in accept_encoding:
                compression = 'br'
            elif 'gzip' in accept_encoding:
                compression = 'gzip'
            elif 'lz4' in accept_encoding:
                compression = 'lz4'
            else:
                compression = None
            
            scope['compression'] = compression
        
        await self.app(scope, receive, send)

# 効率的なシリアライゼーション
class OptimizedSerializer:
    @staticmethod
    def serialize(data: Any, format: str = 'json') -> bytes:
        """高速シリアライゼーション"""
        if format == 'json':
            # orjsonは標準jsonより3-10倍高速
            return orjson.dumps(data)
        elif format == 'msgpack':
            # バイナリ形式でコンパクト
            return msgpack.packb(data)
        elif format == 'pickle':
            # Python専用だが最速
            return pickle.dumps(data, protocol=5)
    
    @staticmethod
    def compress(data: bytes, method: str = 'gzip') -> bytes:
        """データ圧縮"""
        if method == 'gzip':
            return gzip.compress(data, compresslevel=6)
        elif method == 'br':
            return brotli.compress(data, quality=4)
        elif method == 'lz4':
            return lz4.frame.compress(data)
        return data

# ストリーミングレスポンス
class StreamingOptimizer:
    @staticmethod
    async def stream_large_dataset(dataspec: str, jvlink):
        """大量データのストリーミング配信"""
        
        async def generate():
            buffer = []
            buffer_size = 0
            max_buffer_size = 1024 * 100  # 100KB
            
            # ヘッダー送信
            yield b'{"records":['
            first = True
            
            # JVLinkからデータを逐次読み込み
            while True:
                data = await read_next_record(jvlink)
                if not data:
                    break
                
                # JSON化
                json_data = orjson.dumps(data)
                
                if not first:
                    json_data = b',' + json_data
                first = False
                
                buffer.append(json_data)
                buffer_size += len(json_data)
                
                # バッファが満たされたら送信
                if buffer_size >= max_buffer_size:
                    yield b''.join(buffer)
                    buffer = []
                    buffer_size = 0
            
            # 残りのバッファを送信
            if buffer:
                yield b''.join(buffer)
            
            yield b']}'
        
        return StreamingResponse(
            generate(),
            media_type="application/json",
            headers={
                "Content-Encoding": "gzip",
                "Transfer-Encoding": "chunked"
            }
        )
```

## 5. 最小限のバッチ処理最適化

### 5.1 効率的なバッチ取得（SQLite不要）

```python
# batch_processor.py
from typing import List, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

class SimpleBatchProcessor:
    """シンプルで効率的なバッチ処理"""
    
    def __init__(self, cache: SimpleTwoLayerCache, max_workers: int = 3):
        self.cache = cache
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def batch_get_data(self, requests: List[Dict]) -> List[Any]:
        """複数データの並列取得"""
        results = []
        
        # キャッシュから一括チェック
        for req in requests:
            cached = await self.cache.get(**req)
            if cached:
                results.append(cached)
            else:
                # JVLinkから非同期取得
                data = await self._fetch_async(req)
                results.append(data)
                # キャッシュに保存
                await self.cache.set(data, **req)
        
        return results
    
    async def _fetch_async(self, request: Dict) -> Any:
        """非同期でJVLinkから取得"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._fetch_from_jvlink,
            request
        )
    
    def _fetch_from_jvlink(self, request: Dict):
        """JVLinkからデータ取得（同期処理）"""
        import pythoncom
        import win32com.client
        
        pythoncom.CoInitialize()
        try:
            jvlink = win32com.client.Dispatch("JVDTLab.JVLink")
            # 実際の取得処理
            return fetch_data(jvlink, **request)
        finally:
            pythoncom.CoUninitialize()

# 使用例
batch_processor = SimpleBatchProcessor(cache)
results = await batch_processor.batch_get_data([
    {"dataspec": "RACE", "from_time": "20250829000000"},
    {"dataspec": "0B12", "from_time": "20250829000000"},
    {"dataspec": "HOSE", "from_time": "20250829000000"}
])
```

## 6. 実装優先度とパフォーマンス改善効果（改訂版）

### 6.1 シンプル化による改善効果

| 最適化手法 | 実装難易度 | 改善効果 | 優先度 |
|-----------|----------|---------|--------|
| L1メモリキャッシュ | **最低** | **80-95%削減** | **最高** |
| Redis（オプション） | 低 | 60-80%削減 | 高 |
| 接続プール | 中 | 30-40%削減 | 高 |
| レスポンス圧縮 | 低 | 転送量60-80%削減 | 高 |
| ストリーミング | 中 | 初期レスポンス90%高速化 | 中 |
| 非同期バッチ処理 | 中 | スループット200-300%向上 | 中 |
| ~~SQLite~~ | - | - | **削除** |

### 6.2 シンプル化された段階的実装計画

#### Phase 1: 即効性のある実装（3-5日）
```python
# 最小限の実装で最大の効果
実装内容:
- TTLCacheによるメモリキャッシュ
- gzip圧縮レスポンス
- シンプルな接続管理

期待効果:
→ レスポンス時間: 40ms → 10ms（75%改善）
→ キャッシュヒット時: 0.01ms（99.9%改善）
```

#### Phase 2: スケーラビリティ対応（1-2週間）
```python
# 本番環境向け最適化
実装内容:
- Redis統合（フォールバック付き）
- ストリーミングAPI
- 非同期バッチ処理

期待効果:
→ レスポンス時間: 10ms → 5ms（87%改善）
→ 同時接続数: 10倍向上
```

#### Phase 3: アドバンスド機能（必要に応じて）
```python
# 追加の最適化（オプション）
実装内容:
- 賢いプリフェッチング
- 適応的TTL調整
- WebSocketリアルタイム配信

期待効果:
→ レスポンス時間: 5ms → 3ms（92%改善）
→ ユーザー体感速度: 大幅向上
```

## 7. ベンチマークコード

```python
# benchmark.py
import asyncio
import time
from statistics import mean, stdev

async def benchmark_endpoint(url: str, iterations: int = 100):
    """エンドポイントのベンチマーク"""
    times = []
    
    async with httpx.AsyncClient() as client:
        # ウォームアップ
        for _ in range(10):
            await client.get(url)
        
        # 計測
        for _ in range(iterations):
            start = time.perf_counter()
            response = await client.get(url)
            end = time.perf_counter()
            
            if response.status_code == 200:
                times.append((end - start) * 1000)  # ms
    
    return {
        'mean': mean(times),
        'stdev': stdev(times),
        'min': min(times),
        'max': max(times),
        'p50': sorted(times)[len(times)//2],
        'p95': sorted(times)[int(len(times)*0.95)],
        'p99': sorted(times)[int(len(times)*0.99)]
    }

# 使用例
results = await benchmark_endpoint(
    'http://localhost:8000/api/v1/data/RACE?from_time=20250829000000'
)
print(f"平均レスポンス時間: {results['mean']:.2f}ms")
print(f"95パーセンタイル: {results['p95']:.2f}ms")
```

## まとめ

### 🎯 シンプル化による大きなメリット

1. **開発速度の向上**
   - SQLite削除により実装が50%簡素化
   - 保守性が大幅に向上
   - バグリスクの低減

2. **パフォーマンスの向上**
   - キャッシュヒット時: **0.01ms**（99.9%高速化）
   - 通常アクセス: **5-10ms**（75-87%高速化）
   - メモリ使用量: 最小限に抑制

3. **運用の簡素化**
   - データベース管理不要
   - バックアップ不要
   - ディスク容量管理不要

### 📊 アーキテクチャ比較

| 構成 | 複雑度 | パフォーマンス | 推奨度 |
|------|--------|--------------|--------|
| メモリのみ | 最低 | 最高（0.01ms） | 開発/小規模 |
| **メモリ+Redis** | **低** | **高（0.01-2ms）** | **本番環境 ✅** |
| ~~+SQLite~~ | 高 | 中（5-10ms） | 非推奨 ❌ |

### 🚀 推奨実装手順

1. **まずメモリキャッシュのみで開始**（3日）
2. **必要に応じてRedis追加**（2日）
3. **パフォーマンステスト実施**
4. **要件に応じて追加最適化**

**結論**: シンプルな2層キャッシュ（メモリ+Redis）で、複雑なSQLite実装を超える性能を実現できます。