"""
シンプルな2層キャッシュサービス
メモリ(必須) + Redis(オプション)
"""
from cachetools import TTLCache
import redis
import pickle
import json
import hashlib
from typing import Optional, Any

class CacheService:
    """シンプルな2層キャッシュ"""
    
    def __init__(self, memory_size: int = 500, memory_ttl: int = 300):
        # L1: メモリキャッシュ（必須）
        self.memory = TTLCache(maxsize=memory_size, ttl=memory_ttl)
        
        # L2: Redis（オプション）
        self.redis_client = None
        self.has_redis = False
        self._init_redis()
    
    def _init_redis(self):
        """Redis接続を試みる（失敗しても継続）"""
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=False,
                socket_connect_timeout=1
            )
            self.redis_client.ping()
            self.has_redis = True
            print("Redis connected successfully")
        except:
            self.has_redis = False
            print("Redis not available, using memory cache only")
    
    def _make_key(self, dataspec: str, **kwargs) -> str:
        """キャッシュキー生成"""
        key_dict = {"ds": dataspec, **kwargs}
        key_str = json.dumps(key_dict, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()[:16]
    
    def get(self, dataspec: str, **kwargs) -> Optional[Any]:
        """キャッシュから取得"""
        key = self._make_key(dataspec, **kwargs)
        
        # L1: メモリキャッシュ確認
        if key in self.memory:
            return self.memory[key]
        
        # L2: Redis確認（利用可能な場合）
        if self.has_redis:
            try:
                data = self.redis_client.get(f"jra:{key}")
                if data:
                    value = pickle.loads(data)
                    self.memory[key] = value  # L1に昇格
                    return value
            except Exception as e:
                print(f"Redis get error: {e}")
        
        return None
    
    def set(self, data: Any, dataspec: str, **kwargs):
        """キャッシュに保存"""
        key = self._make_key(dataspec, **kwargs)
        ttl = self._get_ttl(dataspec)
        
        # L1: メモリに保存
        self.memory[key] = data
        
        # L2: Redisに保存（利用可能な場合）
        if self.has_redis:
            try:
                self.redis_client.setex(
                    f"jra:{key}",
                    ttl,
                    pickle.dumps(data)
                )
            except Exception as e:
                print(f"Redis set error: {e}")
    
    def _get_ttl(self, dataspec: str) -> int:
        """データ種別ごとのTTL（秒）"""
        # リアルタイムデータは短め
        if dataspec.startswith("0B"):
            return 60  # 1分
        # マスタデータは長め
        elif dataspec in ["RACE", "HOSE", "HOYU"]:
            return 86400  # 24時間
        # デフォルト
        else:
            return 600  # 10分
    
    def clear(self):
        """キャッシュクリア"""
        self.memory.clear()
        if self.has_redis:
            try:
                for key in self.redis_client.scan_iter("jra:*"):
                    self.redis_client.delete(key)
            except:
                pass