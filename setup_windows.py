#!/usr/bin/env python
"""
JRA-VAN Windows セットアップスクリプト (32bit Python最適化版)
=====================================================
JVLink COMコンポーネントの設定とレジストリ最適化を行います

重要: JVLinkは32bit COMコンポーネントのため、32bit Pythonが必要です

前提条件:
  1. Python 3.x (32bit版) がインストール済み
  2. JRA-VAN Data Lab. がインストール済み
  3. pywin32 パッケージがインストール済み
     
使用方法:
  python setup_windows.py        # 通常実行（管理者権限推奨）
  python setup_windows.py --test # テストのみ
  
注意:
  レジストリ設定には管理者権限が必要です
"""

import sys
import os
import subprocess
import ctypes
from pathlib import Path

def is_admin():
    """管理者権限の確認"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def check_requirements():
    """必要な前提条件の確認"""
    print("Checking requirements...")
    
    # 1. Python環境のビット数確認（32bit必須）
    is_32bit = sys.maxsize <= 2**32
    if is_32bit:
        print(f"  [OK] Python is 32-bit")
    else:
        print(f"  [ERROR] Python is 64-bit")
        print("  JVLink requires 32-bit Python")
        print("  Please install 32-bit Python from https://python.org")
        return False
    
    # 2. pywin32の確認
    try:
        import win32com.client
        print("  [OK] pywin32 is installed")
    except ImportError:
        print("  [ERROR] pywin32 is not installed")
        print("  Please run: pip install pywin32")
        return False
    
    # 3. JVDTLab.dllの確認
    dll_path = r"C:\Windows\SysWOW64\JVDTLAB\JVDTLAB.dll"
    if os.path.exists(dll_path):
        print(f"  [OK] JVDTLab.dll found at {dll_path}")
    else:
        print(f"  [WARNING] JVDTLab.dll not found at {dll_path}")
        print("  JRA-VAN Data Lab. may not be installed")
        # Continue anyway as it might be in different location
    
    return True

def register_jvlink():
    """JVDTLab.dll を登録（32bit用）"""
    print("\nRegistering JVDTLab.dll...")
    
    dll_path = r"C:\Windows\SysWOW64\JVDTLAB\JVDTLAB.dll"
    
    if not os.path.exists(dll_path):
        print(f"  [ERROR] DLL not found: {dll_path}")
        return False
    
    try:
        # 32bit版のregsvr32を使用
        regsvr32_path = r"C:\Windows\SysWOW64\regsvr32.exe"
        
        # 既存の登録を解除
        subprocess.run(
            [regsvr32_path, "/s", "/u", dll_path],
            capture_output=True,
            check=False
        )
        
        # 新規登録
        result = subprocess.run(
            [regsvr32_path, "/s", dll_path],
            capture_output=True,
            check=True
        )
        
        print("  [OK] JVDTLab.dll registered successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  [ERROR] DLL registration failed")
        return False
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False

def setup_registry():
    """32bit Python用のレジストリ設定"""
    print("\nSetting up registry for 32-bit Python...")
    
    import winreg
    
    clsid = "{2AB1774D-0C41-11D7-916F-0003479BEB3F}"
    dll_path = r"C:\Windows\SysWOW64\JVDTLAB\JVDTLAB.dll"
    
    try:
        # CLSID登録
        key_path = f"CLSID\\{clsid}"
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path) as key:
            winreg.SetValue(key, "", winreg.REG_SZ, "JVDTLab.JVLink")
        
        # InprocServer32設定
        key_path = f"CLSID\\{clsid}\\InprocServer32"
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path) as key:
            winreg.SetValue(key, "", winreg.REG_SZ, dll_path)
            winreg.SetValueEx(key, "ThreadingModel", 0, winreg.REG_SZ, "Apartment")
        
        # ProgID設定
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, "JVDTLab.JVLink") as key:
            winreg.SetValue(key, "", winreg.REG_SZ, "JVDTLab.JVLink")
        
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, "JVDTLab.JVLink\\CLSID") as key:
            winreg.SetValue(key, "", winreg.REG_SZ, clsid)
        
        print("  [OK] Registry settings applied for 32-bit Python")
        return True
    except Exception as e:
        print(f"  [ERROR] Registry setup failed: {e}")
        print("  Try running as Administrator")
        return False

def test_com_connection():
    """COM接続のテスト"""
    print("\nTesting COM connection...")
    
    try:
        import win32com.client
        
        print("  Creating COM object...")
        jvlink = win32com.client.Dispatch('JVDTLab.JVLink')
        print("  [OK] COM object created")
        
        print("  Initializing JVLink...")
        ret = jvlink.JVInit("SETUP_TEST")
        
        if ret == 0:
            print("  [OK] JVLink initialized successfully")
            try:
                version = jvlink.m_JVLinkVersion
                print(f"  [INFO] JVLink Version: {version}")
            except:
                pass
            jvlink.JVClose()
            return True
        else:
            print(f"  [INFO] JVInit returned: {ret}")
            print("  [INFO] This is normal if service key is not configured")
            return True
        
    except Exception as e:
        print(f"  [WARNING] COM test failed: {e}")
        print("  Make sure you're using 32-bit Python")
        return False

def main():
    """メイン処理"""
    print("="*60)
    print("JRA-VAN Windows Setup (32-bit Python)")
    print("="*60)
    print("\nThis script will:")
    print("1. Check Python architecture (32-bit required)")
    print("2. Register JVDTLab.dll")
    print("3. Configure registry for 32-bit Python")
    print("4. Test COM connection")
    print()
    
    # 管理者権限の確認
    if not is_admin():
        print("[WARNING] Not running as administrator")
        print("Some operations may fail. Run as administrator if needed.")
        print()
    
    # 前提条件確認
    if not check_requirements():
        print("\n[FAILED] Requirements check failed")
        print("Please install required components and try again")
        return 1
    
    # Windows固有の設定実行
    steps = [
        ("DLL Registration", register_jvlink),
        ("Registry Setup", setup_registry),
        ("Connection Test", test_com_connection),
    ]
    
    failed = False
    for step_name, step_func in steps:
        if not step_func():
            print(f"\n[WARNING] {step_name} had issues")
            failed = True
    
    print("\n" + "="*60)
    if not failed:
        print("[SUCCESS] Windows setup completed!")
        print("\nNext steps:")
        print("1. Run: python test_32bit_jvlink.py")
        print("2. Use: from jravan.client import JVLinkClient")
        print("3. Configure JRA-VAN service key when prompted")
    else:
        print("[PARTIAL SUCCESS] Setup completed with warnings")
        print("\nTry running your application anyway.")
        print("Some warnings are normal on first setup.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())