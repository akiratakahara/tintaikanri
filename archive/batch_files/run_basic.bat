@echo off
echo Starting Rental Management System v2.0 - Basic Edition
echo ========================================================
echo OCR機能を無効にした基本版です
echo.

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo [WARNING] 仮想環境が見つかりません
    echo システムのPythonを使用します
    echo.
    python run_basic.py
    goto :end
)

echo [INFO] 仮想環境をアクティベート中...
call .venv\Scripts\activate.bat

echo [INFO] PyQt6の動作確認中...
python -c "import PyQt6.QtWidgets; print('[SUCCESS] PyQt6が正常に動作します')" 2>nul
if errorlevel 1 (
    echo [WARNING] PyQt6に問題があります。システムPythonで試行します
    echo.
    python run_basic.py
    goto :end
)

echo [INFO] 基本版アプリケーションを起動中...
python run_basic.py

:end
echo.
echo [INFO] アプリケーションが終了しました
pause