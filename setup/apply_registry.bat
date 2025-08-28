@echo off
chcp 65001 >nul
echo ========================================
echo JV-Link レジストリ設定適用バッチ
echo ========================================
echo.

REM スクリプトのディレクトリに移動
cd /d "%~dp0"

REM JV-Link.exeの存在確認
if not exist "JV-Link.exe" (
    echo エラー: JV-Link.exeが見つかりません
    echo.
    echo JV-Link.exeをダウンロードしてこのフォルダに配置してください
    echo 詳細は DOWNLOAD_JVLINK.md を参照
    echo.
    pause
    exit /b 1
)

REM レジストリファイル生成
echo レジストリファイルを生成中...
python create_registry.py
if errorlevel 1 (
    echo レジストリファイルの生成に失敗しました
    pause
    exit /b 1
)

REM 管理者権限の確認
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo 管理者権限が必要です
    echo このバッチファイルを右クリックして「管理者として実行」を選択してください
    echo.
    pause
    exit /b 1
)

REM レジストリの適用
echo.
echo レジストリを適用中...
reg import jvlink_localserver.reg
if errorlevel 1 (
    echo レジストリの適用に失敗しました
    pause
    exit /b 1
)

echo.
echo レジストリの適用が完了しました！
echo.
pause