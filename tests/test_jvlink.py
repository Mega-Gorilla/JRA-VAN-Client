"""
JV-Link接続テスト（詳細版）
"""

import win32com.client
import win32api
import win32con
import sys
import os

print("=" * 70)
print("JV-Link COM登録状態確認")
print("=" * 70)

# Python情報
print(f"Python: {sys.version}")
print(f"Platform: {sys.platform}")
print(f"64bit: {sys.maxsize > 2**32}")

# JV-Link.exe の存在確認
jvlink_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "setup", "JV-Link.exe")
print(f"\nJV-Link.exe存在確認: {os.path.exists(jvlink_path)}")
if os.path.exists(jvlink_path):
    print(f"  パス: {jvlink_path}")

# レジストリ確認
print("\nレジストリ確認:")
try:
    # HKEY_CLASSES_ROOT\JVDTLab.JVLink を確認
    key = win32api.RegOpenKeyEx(win32con.HKEY_CLASSES_ROOT, "JVDTLab.JVLink")
    print("  JVDTLab.JVLink: 登録済み")
    win32api.RegCloseKey(key)
except:
    print("  JVDTLab.JVLink: 未登録")

try:
    # CLSID確認
    key = win32api.RegOpenKeyEx(win32con.HKEY_CLASSES_ROOT, 
                                r"CLSID\{02AB1774-0C41-11D7-916F-0003479BEB3F}")
    print("  CLSID: 登録済み")
    win32api.RegCloseKey(key)
except:
    print("  CLSID: 未登録")

# COM オブジェクト生成テスト
print("\nCOMオブジェクト生成テスト:")

# 方法1: ProgID使用
print("\n1. ProgID (JVDTLab.JVLink) 使用:")
try:
    jvlink = win32com.client.Dispatch("JVDTLab.JVLink")
    print("  成功: COMオブジェクト生成完了")
    
    # バージョン取得試行
    try:
        version = jvlink.m_JVLinkVersion
        print(f"  JV-Linkバージョン: {version}")
    except:
        print("  バージョン取得失敗")
        
    # JVInit試行
    try:
        ret = jvlink.JVInit("TEST")
        print(f"  JVInit結果: {ret}")
        if ret == -211:
            print("    → サービスキー認証エラー（JRA-VAN契約が必要）")
        elif ret == 0:
            print("    → 初期化成功")
    except Exception as e:
        print(f"  JVInit失敗: {e}")
        
except Exception as e:
    print(f"  失敗: {e}")

# 方法2: CLSID使用
print("\n2. CLSID直接使用:")
try:
    jvlink = win32com.client.Dispatch("{02AB1774-0C41-11D7-916F-0003479BEB3F}")
    print("  成功: COMオブジェクト生成完了")
except Exception as e:
    print(f"  失敗: {e}")

# 方法3: CoCreateInstance使用
print("\n3. CoCreateInstance使用:")
try:
    import pythoncom
    clsid = pythoncom.MakeIID("{02AB1774-0C41-11D7-916F-0003479BEB3F}")
    iid = pythoncom.MakeIID("{00020400-0000-0000-C000-000000000046}")  # IID_IDispatch
    
    obj = pythoncom.CoCreateInstance(clsid, None, 
                                     pythoncom.CLSCTX_LOCAL_SERVER | pythoncom.CLSCTX_INPROC_SERVER,
                                     iid)
    jvlink = win32com.client.Dispatch(obj)
    print("  成功: COMオブジェクト生成完了")
except Exception as e:
    print(f"  失敗: {e}")

print("\n" + "=" * 70)

# 登録方法の案内
print("\nJV-Link登録方法:")
print("1. 管理者権限でコマンドプロンプトを開く")
print("2. 以下のコマンドを実行:")
print(f'   cd "{os.path.dirname(jvlink_path)}"')
print("   JV-Link.exe /regserver")
print("\n登録解除する場合:")
print("   JV-Link.exe /unregserver")

print("\n注意事項:")
print("- JRA-VAN DataLabの契約が必要です（月額2,090円）")
print("- 32bit版のJV-Linkは64bit Windowsでも動作します")
print("- Python 32bit版の使用が推奨されています")