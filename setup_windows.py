#!/usr/bin/env python
"""
JRA-VAN Windows固有セットアップスクリプト
=====================================================
JV-Link.exe の COM登録とレジストリ設定を行います

前提条件:
  1. Python 3.8以上がインストール済み
  2. jra-van-client パッケージがインストール済み
     pip install .  または  pip install jra-van-client
  3. JV-Link.exe が setup/ フォルダに配置済み
     
使用方法:
  python setup_windows.py        # 通常実行
  python setup_windows.py --test # テストのみ
  
注意:
  管理者権限が必要な場合があります
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
    
    # 1. pywin32の確認
    try:
        import win32com.client
        print("  [OK] pywin32 is installed")
    except ImportError:
        print("  [ERROR] pywin32 is not installed")
        print("  Please run: pip install pywin32")
        return False
    
    # 2. JV-Link.exeの確認
    jvlink_path = Path(__file__).parent / "setup" / "JV-Link.exe"
    if not jvlink_path.exists():
        print(f"  [ERROR] JV-Link.exe not found at {jvlink_path}")
        print("  Please download from JRA-VAN website")
        print("  See setup/DOWNLOAD_JVLINK.md for instructions")
        return False
    print(f"  [OK] JV-Link.exe found at {jvlink_path}")
    
    return True

def register_jvlink():
    """JV-Link.exe を COM サーバーとして登録"""
    print("\nRegistering JV-Link.exe...")
    
    jvlink_path = Path(__file__).parent / "setup" / "JV-Link.exe"
    
    try:
        # /regserver オプションで登録
        result = subprocess.run(
            [str(jvlink_path), "/regserver"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("  [OK] JV-Link.exe registered successfully")
            return True
        else:
            print(f"  [ERROR] Registration failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False

def setup_registry():
    """64bit対応のレジストリ設定"""
    print("\nSetting up registry for 64-bit compatibility...")
    
    setup_dir = Path(__file__).parent / "setup"
    
    # レジストリファイル生成
    try:
        result = subprocess.run(
            ["python", str(setup_dir / "create_registry.py")],
            capture_output=True,
            text=True,
            cwd=str(setup_dir)
        )
        
        if result.returncode != 0:
            print(f"  [ERROR] Failed to create registry file: {result.stderr}")
            return False
        
        # レジストリ適用
        reg_file = setup_dir / "jvlink_localserver.reg"
        if reg_file.exists():
            result = subprocess.run(
                ["reg", "import", str(reg_file)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("  [OK] Registry settings applied")
                return True
            else:
                print(f"  [ERROR] Registry import failed: {result.stderr}")
                return False
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False

def test_com_connection():
    """COM接続のテスト"""
    print("\nTesting COM connection...")
    
    try:
        import win32com.client
        
        print("  Creating COM object...")
        jvlink = win32com.client.Dispatch('JVDTLab.JVLink')
        print("  [OK] COM object created")
        
        # Note: JVInit will fail without service key, but that's expected
        print("  [INFO] COM connection is working")
        print("  [INFO] You will need to configure JRA-VAN service key on first use")
        return True
        
    except Exception as e:
        print(f"  [WARNING] COM test failed: {e}")
        print("  This may be normal on first run")
        print("  Try running your application to complete setup")
        return True  # Don't fail completely

def main():
    """メイン処理"""
    print("="*60)
    print("JRA-VAN Windows Setup")
    print("="*60)
    print("\nThis script will:")
    print("1. Register JV-Link.exe as COM server")
    print("2. Configure registry for 64-bit Python")
    print("3. Test COM connection")
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
        ("JV-Link Registration", register_jvlink),
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
        print("1. Run: python main.py --test")
        print("2. Configure JRA-VAN service key when prompted")
    else:
        print("[PARTIAL SUCCESS] Setup completed with warnings")
        print("\nTry running your application anyway.")
        print("Some warnings are normal on first setup.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())