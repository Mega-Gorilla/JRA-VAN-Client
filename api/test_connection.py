"""
JVLink接続テストスクリプト
REST APIサーバーの動作確認用
"""
import sys
import win32com.client
import pythoncom

def test_jvlink_connection():
    """JVLink COM接続テスト"""
    print("=" * 50)
    print("JVLink接続テスト")
    print("=" * 50)
    
    # Python環境確認
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")
    is_32bit = sys.maxsize <= 2**32
    print(f"Architecture: {'32-bit' if is_32bit else '64-bit'}")
    
    if not is_32bit:
        print("\n[WARNING] 64-bit Pythonです。32-bit Pythonが必要です。")
        return False
    
    print("\nJVLink接続を試みます...")
    
    try:
        # COM初期化
        pythoncom.CoInitialize()
        
        # JVLink接続
        jvlink = win32com.client.Dispatch("JVDTLab.JVLink")
        print("[OK] JVLink COMオブジェクト作成成功")
        
        # JVInit
        ret = jvlink.JVInit("TEST1.0")
        print(f"JVInit戻り値: {ret}")
        
        if ret == 0:
            print("[OK] JVLink初期化成功")
        else:
            print(f"[WARNING] JVInit戻り値が0以外: {ret}")
        
        # バージョン確認（可能な場合）
        try:
            # JVVersionを試す
            version = jvlink.JVVersion()
            print(f"JVLinkバージョン: {version}")
        except:
            print("バージョン情報取得不可")
        
        # クローズ
        jvlink.JVClose()
        print("[OK] JVLink接続テスト完了")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return False
    finally:
        pythoncom.CoUninitialize()

def test_api_server():
    """REST APIサーバーテスト"""
    print("\n" + "=" * 50)
    print("REST APIサーバーテスト")
    print("=" * 50)
    
    try:
        import requests
        
        # ヘルスチェック
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            data = response.json()
            print("[OK] APIサーバー稼働中")
            print(f"   JVLink接続: {data.get('jvlink_connected')}")
            print(f"   Redisキャッシュ: {data.get('cache_redis_available')}")
        else:
            print(f"[ERROR] APIサーバーエラー: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("[ERROR] APIサーバーに接続できません")
        print("   uvicorn api.main:app --reload で起動してください")
    except ImportError:
        print("[WARNING] requestsがインストールされていません")
        print("   pip install requests でインストールしてください")

if __name__ == "__main__":
    # JVLink接続テスト
    jvlink_ok = test_jvlink_connection()
    
    # APIサーバーテスト（オプション）
    test_api_server()
    
    if jvlink_ok:
        print("\n[OK] 準備完了: REST APIサーバーを起動できます")
        print("実行コマンド: uvicorn api.main:app --reload")
    else:
        print("\n[ERROR] JVLink接続に問題があります")