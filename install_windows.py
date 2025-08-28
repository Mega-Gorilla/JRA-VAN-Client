"""
JRA-VAN Client 統合セットアップスクリプト

このスクリプトは以下を自動的に実行します：
1. 仮想環境の作成
2. 依存パッケージのインストール
3. JV-Linkの登録
4. 64bit対応設定
5. 接続テスト

Author: Mega-Gorilla
Date: 2025-08-28
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import ctypes
import time


def is_admin():
    """管理者権限で実行されているか確認"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin():
    """管理者権限で再実行"""
    if is_admin():
        return True
    else:
        print("管理者権限で再実行します...")
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        return False


def print_header(title):
    """見出しを表示"""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def run_command(command, description="", shell=True, check=True):
    """コマンドを実行"""
    if description:
        print(f"\n{description}...")
    
    try:
        result = subprocess.run(command, shell=shell, capture_output=True, text=True, check=check)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"エラー: {e}")
        if e.stderr:
            print(e.stderr)
        return False


class JRAVANSetup:
    def __init__(self):
        self.root_dir = Path.cwd()
        self.setup_dir = self.root_dir / "setup"
        self.venv_dir = self.root_dir / "venv"
        self.jvlink_exe = self.setup_dir / "JV-Link.exe"
        
    def check_prerequisites(self):
        """前提条件を確認"""
        print_header("前提条件確認")
        
        # Python版確認
        print(f"Python: {sys.version}")
        print(f"64bit: {sys.maxsize > 2**32}")
        
        # JV-Link.exeの確認
        if not self.jvlink_exe.exists():
            # SDKから自動コピー
            sdk_paths = [
                self.root_dir / "JRA-VAN Data Lab. SDK Ver4.9.0.2" / "JV-Link" / "JV-Link.exe",
                Path(r"D:\Codes\StableFormer\JRA-VAN Data Lab. SDK Ver4.9.0.2\JV-Link\JV-Link.exe"),
            ]
            
            for sdk_path in sdk_paths:
                if sdk_path.exists():
                    print(f"JV-Link.exeをコピー: {sdk_path} → {self.jvlink_exe}")
                    shutil.copy2(sdk_path, self.jvlink_exe)
                    break
            else:
                print("警告: JV-Link.exeが見つかりません")
                print("JRA-VAN SDKからJV-Link.exeをsetupフォルダにコピーしてください")
                return False
        
        print(f"JV-Link.exe: {self.jvlink_exe}")
        return True
    
    def setup_venv(self):
        """仮想環境セットアップ"""
        print_header("仮想環境セットアップ")
        
        if not self.venv_dir.exists():
            print("仮想環境を作成中...")
            run_command([sys.executable, "-m", "venv", "venv"])
        else:
            print("仮想環境は既に存在します")
        
        # pip更新
        pip_path = self.venv_dir / "Scripts" / "pip.exe"
        run_command([str(pip_path), "install", "--upgrade", "pip"], "pipを更新")
        
        # pywin32インストール
        run_command([str(pip_path), "install", "pywin32"], "pywin32をインストール")
        
        # pywin32ポストインストール
        python_path = self.venv_dir / "Scripts" / "python.exe"
        postinstall_path = self.venv_dir / "Scripts" / "pywin32_postinstall.py"
        if postinstall_path.exists():
            run_command([str(python_path), str(postinstall_path), "-install"], 
                       "pywin32ポストインストール")
        
        # その他の依存関係（requirements.txt）
        req_file = self.root_dir / "requirements.txt"
        if req_file.exists():
            run_command([str(pip_path), "install", "-r", str(req_file)], 
                       "依存パッケージをインストール", check=False)
        
        return True
    
    def check_and_download_jvlink(self):
        """JV-Link.exeの存在確認とダウンロード案内"""
        if not self.jvlink_exe.exists():
            print("⚠ JV-Link.exeが見つかりません")
            print()
            print("以下の手順でJV-Link.exeをダウンロードしてください：")
            print()
            print("1. JRA-VAN公式サイトにアクセス")
            print("   https://jra-van.jp/dlb/#tab5")
            print()
            print("2. 最新版のSDKをダウンロード")
            print()
            print("3. ZIPを解凍し、JV-Link\\JV-Link.exeを")
            print(f"   {self.setup_dir}\\ にコピー")
            print()
            print("詳細は setup\\DOWNLOAD_JVLINK.md を参照してください")
            print()
            input("ダウンロード完了後、Enterキーを押して続行...")
            
            # 再確認
            if not self.jvlink_exe.exists():
                print("エラー: JV-Link.exeが見つかりません")
                print("セットアップを中止します")
                return False
        
        return True
    
    def register_jvlink(self):
        """JV-Linkを登録"""
        print_header("JV-Link登録")
        
        # JV-Link.exeの存在確認
        if not self.check_and_download_jvlink():
            return False
        
        os.chdir(self.setup_dir)
        result = run_command([str(self.jvlink_exe), "/regserver"], 
                           "JV-Link.exeを登録", check=False)
        os.chdir(self.root_dir)
        
        if result:
            print("✓ JV-Link登録成功")
        else:
            print("× JV-Link登録失敗（既に登録済みの可能性があります）")
        
        return True
    
    def apply_registry_settings(self):
        """レジストリ設定を適用（64bit対応）"""
        print_header("64bit対応レジストリ設定")
        
        # create_registry.pyを使用してレジストリファイルを生成
        create_reg_script = self.setup_dir / "create_registry.py"
        if create_reg_script.exists():
            print("レジストリファイルを自動生成中...")
            result = subprocess.run(
                [sys.executable, str(create_reg_script)],
                capture_output=True,
                text=True,
                cwd=str(self.setup_dir)
            )
            
            if result.returncode != 0:
                print("× レジストリファイル生成失敗")
                print(result.stderr if result.stderr else result.stdout)
                return False
            else:
                print(result.stdout)
        else:
            # フォールバック: 直接生成
            print("レジストリファイルを直接生成中...")
            reg_content = f"""Windows Registry Editor Version 5.00

; JV-Link LocalServer32設定（64bit対応）
[HKEY_CLASSES_ROOT\\CLSID\\{{2AB1774D-0C41-11D7-916F-0003479BEB3F}}\\LocalServer32]
@="{str(self.jvlink_exe).replace(chr(92), chr(92)+chr(92))}"

; DLL Surrogate設定
[HKEY_CLASSES_ROOT\\CLSID\\{{2AB1774D-0C41-11D7-916F-0003479BEB3F}}]
"AppID"="{{2AB1774D-0C41-11D7-916F-0003479BEB3F}}"

[HKEY_CLASSES_ROOT\\AppID\\{{2AB1774D-0C41-11D7-916F-0003479BEB3F}}]
"DllSurrogate"=""
"""
            reg_file = self.setup_dir / "jvlink_localserver.reg"
            # UTF-16 LEで保存（Windowsレジストリエディタ用）
            with open(reg_file, 'w', encoding='utf-16le') as f:
                f.write('\ufeff')  # BOM追加
                f.write(reg_content)
        
        # レジストリ適用
        reg_file = self.setup_dir / "jvlink_localserver.reg"
        if reg_file.exists():
            print(f"レジストリファイルを適用: {reg_file}")
            result = run_command(["reg", "import", str(reg_file)], 
                               "レジストリ設定を適用", check=False)
            
            if result:
                print("✓ レジストリ設定成功")
            else:
                # 手動適用を促す
                print("自動適用に失敗しました。手動で適用してください：")
                print(f"  1. setup\\apply_registry.bat を管理者として実行")
                print(f"  2. または {reg_file} をダブルクリック")
        else:
            print("× レジストリファイルが見つかりません")
            return False
        
        return True
    
    def test_connection(self):
        """接続テスト"""
        print_header("JV-Link接続テスト")
        
        python_path = self.venv_dir / "Scripts" / "python.exe"
        
        test_code = """
import sys
try:
    import win32com.client
    print("Creating COM object...")
    jvlink = win32com.client.Dispatch('JVDTLab.JVLink')
    print("✓ COMオブジェクト作成成功")
    
    ret = jvlink.JVInit('SETUP_TEST')
    print(f"JVInit戻り値: {ret}")
    
    if ret == -211:
        print("✓ 正常動作確認（サービスキー認証エラー）")
        print("  → JRA-VANの契約とサービスキー設定が必要です")
    elif ret == 0:
        print("✓ JVInit成功")
        jvlink.JVClose()
    else:
        print(f"△ その他の戻り値: {ret}")
    
    print("\\n★ セットアップ完了！")
    sys.exit(0)
    
except Exception as e:
    print(f"× エラー: {e}")
    sys.exit(1)
"""
        
        # テストコードを一時ファイルに保存
        test_file = self.setup_dir / "test_jvlink.py"
        test_file.write_text(test_code)
        
        # テスト実行
        result = subprocess.run(
            [str(python_path), str(test_file)],
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        return result.returncode == 0
    
    def run(self):
        """セットアップ実行"""
        print_header("JRA-VAN Client セットアップ")
        print("Version: 1.0.0")
        print("Author: Mega-Gorilla")
        
        steps = [
            ("前提条件確認", self.check_prerequisites),
            ("仮想環境セットアップ", self.setup_venv),
            ("JV-Link登録", self.register_jvlink),
            ("64bit対応設定", self.apply_registry_settings),
            ("接続テスト", self.test_connection),
        ]
        
        for step_name, step_func in steps:
            print(f"\n[{step_name}]")
            if not step_func():
                print(f"\n{step_name}で問題が発生しました")
                input("\nEnterキーで終了...")
                return False
            time.sleep(1)
        
        print_header("セットアップ完了")
        print("\n以下のコマンドで使用開始できます：")
        print("  .\\venv\\Scripts\\python.exe main_jra_van.py --test")
        print("\n初回実行時の注意：")
        print("  - JV-Linkのセットアップ画面が表示されます")
        print("  - JRA-VANのサービスキーを入力してください")
        print("  - データ保存先フォルダを指定してください")
        
        input("\nEnterキーで終了...")
        return True


def main():
    """メイン処理"""
    # 管理者権限確認
    if not is_admin():
        print("このセットアップは管理者権限が必要です")
        if not run_as_admin():
            return
    
    # セットアップ実行
    setup = JRAVANSetup()
    setup.run()


if __name__ == "__main__":
    main()