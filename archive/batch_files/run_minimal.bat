@echo off
echo ========================================================
echo 賃貸管理システム v2.0 - Minimal Edition
echo ========================================================
echo OCR機能を完全に除去した最小版です
echo PyQt6のみで動作します
echo.

REM システムPythonで直接実行を試行
echo [INFO] システムPythonでの起動を試行中...
python run_minimal.py
if not errorlevel 1 goto :success

REM 仮想環境での実行を試行
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] 仮想環境での起動を試行中...
    call .venv\Scripts\activate.bat
    python run_minimal.py
    if not errorlevel 1 goto :success
)

REM どちらも失敗した場合
echo [ERROR] アプリケーションの起動に失敗しました
echo.
echo 可能な解決方法:
echo 1. Python 3.8以上がインストールされているか確認
echo 2. PyQt6をインストール: pip install PyQt6
echo 3. fix_pyqt6.bat を実行してPyQt6を修正
echo.
goto :end

:success
echo [SUCCESS] アプリケーションが正常に動作しました

:end
pause