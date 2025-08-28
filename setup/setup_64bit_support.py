"""
64bit Python用 JV-Link設定スクリプト
32bit COMサーバーを64bit Pythonから使用するための設定

注意：管理者権限で実行する必要があります
"""

import winreg
import sys
import os
import ctypes

def is_admin():
    """管理者権限で実行されているか確認"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def setup_dll_surrogate():
    """DLLサロゲート設定を追加"""
    
    # CLSID
    clsid = "{02AB1774-0C41-11D7-916F-0003479BEB3F}"
    
    print("=" * 70)
    print("JV-Link 64bit対応設定")
    print("=" * 70)
    
    if not is_admin():
        print("エラー: このスクリプトは管理者権限で実行する必要があります")
        print("\n実行方法:")
        print("1. コマンドプロンプトを管理者として実行")
        print("2. 以下のコマンドを実行:")
        print(f"   python {os.path.basename(__file__)}")
        return False
    
    try:
        # レジストリパス
        key_path = f"SOFTWARE\\Classes\\CLSID\\{clsid}"
        
        # 32bit版レジストリにアクセス（WOW64）
        print(f"\n32bitレジストリ確認: CLSID {clsid}")
        
        # HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Classes\CLSID
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                f"SOFTWARE\\WOW6432Node\\Classes\\CLSID\\{clsid}",
                0,
                winreg.KEY_READ | winreg.KEY_WOW64_32KEY
            )
            winreg.CloseKey(key)
            print("  → 32bitレジストリに登録済み")
        except:
            print("  → 32bitレジストリに未登録")
            print("\n先にJV-Link.exeを登録してください:")
            print("1. 管理者権限でコマンドプロンプトを開く")
            print("2. 以下を実行:")
            print('   cd "D:\\Codes\\StableFormer\\JRA-VAN Data Lab. SDK Ver4.9.0.2\\JV-Link"')
            print("   JV-Link.exe /regserver")
            return False
        
        # DllSurrogateキー追加（64bitレジストリ）
        print("\nDLLサロゲート設定追加中...")
        
        # HKEY_CLASSES_ROOT\CLSID\{CLSID}\InprocServer32
        key_path = f"CLSID\\{clsid}\\InprocServer32"
        
        try:
            # 64bitレジストリに書き込み
            key = winreg.CreateKeyEx(
                winreg.HKEY_CLASSES_ROOT,
                key_path,
                0,
                winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY
            )
            
            # DllSurrogate値を設定（空文字列でデフォルトサロゲート使用）
            winreg.SetValueEx(key, "DllSurrogate", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
            
            print("  → DllSurrogate設定完了")
            
        except Exception as e:
            print(f"  → 設定失敗: {e}")
            return False
        
        # AppID設定
        print("\nAppID設定追加中...")
        
        try:
            # AppIDキー作成
            appid_path = f"AppID\\{clsid}"
            key = winreg.CreateKeyEx(
                winreg.HKEY_CLASSES_ROOT,
                appid_path,
                0,
                winreg.KEY_WRITE
            )
            winreg.SetValueEx(key, "DllSurrogate", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
            
            # CLSIDにAppIDを関連付け
            clsid_path = f"CLSID\\{clsid}"
            key = winreg.CreateKeyEx(
                winreg.HKEY_CLASSES_ROOT,
                clsid_path,
                0,
                winreg.KEY_WRITE
            )
            winreg.SetValueEx(key, "AppID", 0, winreg.REG_SZ, clsid)
            winreg.CloseKey(key)
            
            print("  → AppID設定完了")
            
        except Exception as e:
            print(f"  → AppID設定失敗: {e}")
        
        print("\n" + "=" * 70)
        print("設定完了！")
        print("64bit Pythonから32bit JV-Linkにアクセスできるようになりました")
        
        return True
        
    except Exception as e:
        print(f"エラー: {e}")
        return False

def test_connection():
    """接続テスト"""
    print("\n接続テスト実行中...")
    
    try:
        import win32com.client
        jvlink = win32com.client.Dispatch("JVDTLab.JVLink")
        print("  → COMオブジェクト生成成功")
        
        try:
            ret = jvlink.JVInit("TEST")
            if ret == -211:
                print("  → JVInit実行成功（サービスキー認証エラー - 正常）")
                print("    JRA-VAN DataLab契約が必要です")
            elif ret == 0:
                print("  → JVInit成功")
            else:
                print(f"  → JVInit戻り値: {ret}")
            return True
        except Exception as e:
            print(f"  → JVInit失敗: {e}")
            return False
            
    except Exception as e:
        print(f"  → COMオブジェクト生成失敗: {e}")
        return False

if __name__ == "__main__":
    if sys.platform != "win32":
        print("このスクリプトはWindows専用です")
        sys.exit(1)
    
    # 設定実行
    if setup_dll_surrogate():
        # テスト実行
        test_connection()
    
    print("\n終了するにはEnterキーを押してください...")
    input()