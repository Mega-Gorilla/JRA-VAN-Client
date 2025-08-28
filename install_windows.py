#!/usr/bin/env python
"""
⚠️ このスクリプトは非推奨です (DEPRECATED)
============================================

新しいインストール方法:

1. Pythonパッケージのインストール:
   pip install .

2. Windows固有設定の実行:
   python setup_windows.py

詳細は README.md を参照してください。
"""

import sys

def main():
    print(__doc__)
    print("\n" + "="*60)
    print("新しいインストール手順に移行してください")
    print("="*60)
    
    response = input("\n自動的に新しい方法でインストールしますか？ (y/n): ")
    
    if response.lower() == 'y':
        import subprocess
        
        print("\n1. パッケージをインストール中...")
        subprocess.run([sys.executable, "-m", "pip", "install", "."])
        
        print("\n2. Windows設定を実行中...")
        subprocess.run([sys.executable, "setup_windows.py"])
        
        print("\n✅ インストール完了！")
        print("次のコマンドで動作確認してください:")
        print("  jravan --test")
    else:
        print("\n手動でインストールしてください:")
        print("  pip install .")
        print("  python setup_windows.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())