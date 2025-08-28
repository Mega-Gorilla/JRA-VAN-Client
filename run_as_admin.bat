@echo off
echo ======================================================================
echo JRA-VAN Client 管理者権限セットアップ
echo ======================================================================
echo.
echo このバッチファイルを右クリック → 「管理者として実行」してください
echo.

cd /d "%~dp0"

echo [1/2] JV-Link.exeの登録...
"D:\Codes\StableFormer\JRA-VAN Data Lab. SDK Ver4.9.0.2\JV-Link\JV-Link.exe" /regserver

if %errorlevel% == 0 (
    echo     成功！
) else (
    echo     失敗（エラーコード: %errorlevel%）
)

echo.
echo [2/2] 64bit Python対応設定...
python setup\setup_64bit_support.py

echo.
echo セットアップ完了
pause