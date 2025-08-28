@echo off
echo ======================================================================
echo JV-Link.exe 登録バッチ
echo ======================================================================
echo.
echo このバッチは管理者権限で実行してください
echo.

cd /d "%~dp0"
echo 現在のディレクトリ: %CD%

echo JV-Link.exeを登録中...
if exist JV-Link.exe (
    JV-Link.exe /regserver
) else (
    echo エラー: JV-Link.exeが見つかりません
    echo setupフォルダに JV-Link.exe をコピーしてください
    exit /b 1
)

if %errorlevel% == 0 (
    echo.
    echo 登録成功！
) else (
    echo.
    echo 登録失敗（エラーコード: %errorlevel%）
    echo 管理者権限で実行してください
)

echo.
pause