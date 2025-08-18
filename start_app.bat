@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ========================================================
echo 賃貸管理システム v2.0 - Modern Edition
echo ========================================================
echo モダンUIで全面刷新されたシステムです
echo.
echo Modern Edition を起動中...
echo.

python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] アプリケーションの起動に失敗しました
    echo Python環境またはPyQt6の設定を確認してください
    echo.
    pause
) else (
    echo.
    echo [SUCCESS] アプリケーションが正常に終了しました
    echo.
    pause
)