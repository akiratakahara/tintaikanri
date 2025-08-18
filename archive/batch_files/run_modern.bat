@echo off
chcp 65001 >nul
echo ========================================
echo 🏢 賃貸管理システム v2.0 - Modern Edition ✅
echo ========================================
echo.
echo ✨ モダンUIで全面刷新されたシステムです
echo 🚀 Modern Edition を起動しています...
echo.
python main.py
if errorlevel 1 (
    echo.
    echo ❌ エラーが発生しました
    echo 💡 PyQt6がインストールされているか確認してください
    echo    pip install PyQt6
    pause
) else (
    echo.
    echo ✅ アプリケーションが正常に終了しました
)
pause