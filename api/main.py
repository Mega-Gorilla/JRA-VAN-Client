"""
JRA-VAN REST API Server
最小限の実装（70行程度）
"""
from fastapi import FastAPI, HTTPException
import win32com.client
import pythoncom
from datetime import datetime
from typing import Optional, Dict, List
from cache import CacheService

# グローバル設定
app = FastAPI(title="JRA-VAN REST API", version="1.0.0")
cache = CacheService()  # 2層キャッシュサービス
jvlink = None

@app.on_event("startup")
def startup_event():
    """起動時のJVLink初期化"""
    global jvlink
    try:
        pythoncom.CoInitialize()
        jvlink = win32com.client.Dispatch("JVDTLab.JVLink")
        ret = jvlink.JVInit("UMANARI1.0")
        if ret != 0:
            print(f"JVInit warning: return code {ret}")
    except Exception as e:
        print(f"JVLink initialization error: {e}")
        jvlink = None

@app.on_event("shutdown")
def shutdown_event():
    """終了時のクリーンアップ"""
    if jvlink:
        try:
            jvlink.JVClose()
        except:
            pass
    pythoncom.CoUninitialize()

@app.get("/")
def root():
    """ルートエンドポイント"""
    return {"message": "JRA-VAN REST API Server", "status": "running"}

@app.get("/health")
def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy" if jvlink else "error",
        "jvlink_connected": jvlink is not None,
        "cache_memory_size": len(cache.memory),
        "cache_redis_available": cache.has_redis,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/data/{dataspec}")
def get_data(dataspec: str, from_time: str = "", option: int = 1):
    """JRA-VANデータ取得エンドポイント"""
    # キャッシュチェック
    cached_data = cache.get(dataspec, from_time=from_time, option=option)
    if cached_data is not None:
        return {"data": cached_data, "cached": True}
    
    # JVLink接続確認
    if not jvlink:
        raise HTTPException(status_code=503, detail="JVLink not initialized")
    
    try:
        # データ取得
        records = fetch_jvlink_data(dataspec, from_time, option)
        
        # キャッシュ保存
        cache.set(records, dataspec, from_time=from_time, option=option)
        
        return {"data": records, "cached": False, "count": len(records)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def fetch_jvlink_data(dataspec: str, from_time: str, option: int) -> List[Dict]:
    """JVLinkからデータ取得"""
    records = []
    
    # JVOpen
    ret = jvlink.JVOpen(dataspec, from_time, option, 0, 0, "")
    if ret < 0:
        raise Exception(f"JVOpen error: {ret}")
    
    # データ読み込み
    buf = " " * 110000  # 最大レコードサイズ
    size = 110000
    fname = ""
    
    while True:
        ret = jvlink.JVRead(buf, size, fname)
        if ret == 0:  # 全データ読み込み完了
            break
        elif ret == -1:  # ファイル切り替え
            continue
        elif ret > 0:  # 正常読み込み
            record_data = buf[:ret].strip()
            if record_data:
                records.append({
                    "record_type": record_data[:2],
                    "data": record_data
                })
            # 最大100件で制限（テスト用）
            if len(records) >= 100:
                break
        else:
            # エラー処理
            break
    
    # JVClose
    jvlink.JVClose()
    
    return records

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)