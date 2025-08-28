"""
レジストリファイル自動生成スクリプト
現在のパスからJV-Link.exeの場所を特定して適切なレジストリファイルを生成
"""

import os
import sys
from pathlib import Path


def create_registry_file():
    """現在のディレクトリからJV-Link.exeのパスを検出してレジストリファイルを生成"""
    
    # スクリプトのあるディレクトリ（setup/）を取得
    setup_dir = Path(__file__).parent.resolve()
    
    # JV-Link.exeのパスを構築
    jvlink_path = setup_dir / "JV-Link.exe"
    
    # パスが存在するか確認
    if not jvlink_path.exists():
        print("エラー: JV-Link.exeが見つかりません")
        print(f"予期されるパス: {jvlink_path}")
        print("\nJV-Link.exeをダウンロードしてsetup/フォルダに配置してください")
        print("詳細は DOWNLOAD_JVLINK.md を参照")
        return False
    
    # Windowsのレジストリ用にパスを変換（バックスラッシュをエスケープ）
    registry_path = str(jvlink_path).replace("\\", "\\\\")
    
    # レジストリファイルの内容
    registry_content = f"""Windows Registry Editor Version 5.00

; JV-Link LocalServer32設定（自動生成）
; 生成日時: {__import__('datetime').datetime.now()}
; JV-Link.exe パス: {jvlink_path}

[HKEY_CLASSES_ROOT\\CLSID\\{{2AB1774D-0C41-11D7-916F-0003479BEB3F}}\\LocalServer32]
@="{registry_path}"

; DLL Surrogate設定（64bit対応）
[HKEY_CLASSES_ROOT\\CLSID\\{{2AB1774D-0C41-11D7-916F-0003479BEB3F}}]
"AppID"="{{2AB1774D-0C41-11D7-916F-0003479BEB3F}}"

[HKEY_CLASSES_ROOT\\AppID\\{{2AB1774D-0C41-11D7-916F-0003479BEB3F}}]
"DllSurrogate"=""
"""
    
    # レジストリファイルを保存
    output_path = setup_dir / "jvlink_localserver.reg"
    output_path.write_text(registry_content, encoding='utf-16-le')
    
    # BOMを追加（Windows レジストリエディタ用）
    with open(output_path, 'rb') as f:
        content = f.read()
    
    with open(output_path, 'wb') as f:
        f.write(b'\xff\xfe')  # UTF-16 LE BOM
        f.write(content)
    
    print("レジストリファイルを生成しました")
    print(f"場所: {output_path}")
    print(f"JV-Link.exe: {jvlink_path}")
    
    return True


if __name__ == "__main__":
    success = create_registry_file()
    sys.exit(0 if success else 1)