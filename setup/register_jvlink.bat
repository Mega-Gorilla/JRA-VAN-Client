@echo off
echo ======================================================================
echo JV-Link.exe 登録バッチ
echo ======================================================================
echo.
echo このバッチは管理者権限で実行してください
echo.

cd /d "D:\Codes\StableFormer\JRA-VAN Data Lab. SDK Ver4.9.0.2\JV-Link"

echo JV-Link.exeを登録中...
JV-Link.exe /regserver

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