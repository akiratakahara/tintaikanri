@echo off
echo Starting Rental Management System v2.0...
echo ==========================================
echo.

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] 仮想環境が見つかりません
    echo.
    echo 解決方法:
    echo 1. fix_pyqt6.bat を実行してください
    echo 2. または install_requirements.bat を実行してください
    echo.
    pause
    exit /b 1
)

echo [INFO] 仮想環境をアクティベート中...
call .venv\Scripts\activate.bat

echo [INFO] PyQt6の動作確認中...
python -c "import PyQt6.QtWidgets; print('[SUCCESS] PyQt6が正常に読み込まれました')" 2>nul
if errorlevel 1 (
    echo [ERROR] PyQt6にエラーがあります
    echo.
    echo DLL問題の修正方法:
    echo 1. fix_pyqt6.bat を実行してください
    echo 2. Microsoft Visual C++ Redistributableをインストールしてください
    echo.
    pause
    exit /b 1
)

echo [INFO] アプリケーションを起動中...
python run_improved.py

echo.
echo [INFO] アプリケーションが終了しました
pause