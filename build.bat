@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ========================================================
echo 賃貸管理システム v2.0 - ビルドスクリプト
echo ========================================================
echo.

echo [1/4] クリーンアップ中...
if exist "build" rd /s /q "build"
if exist "dist" rd /s /q "dist"
if exist "*.spec" del /q "*.spec"
echo クリーンアップ完了

echo.
echo [2/4] PyInstallerでビルド中...
echo (この処理には数分かかります)
echo.

pyinstaller --clean ^
  --onedir ^
  --windowed ^
  --name "賃貸管理システムv2.0" ^
  --add-data "tabs;tabs" ^
  --add-data "ui;ui" ^
  --hidden-import "PyQt6.QtCore" ^
  --hidden-import "PyQt6.QtGui" ^
  --hidden-import "PyQt6.QtWidgets" ^
  --hidden-import "sqlite3" ^
  main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] ビルドに失敗しました
    pause
    exit /b 1
)

echo.
echo [3/4] 必要なファイルをコピー中...

REM ライセンス契約書をコピー
copy "LICENSE_AGREEMENT.txt" "dist\賃貸管理システムv2.0\" >nul 2>&1

REM README作成
echo 賃貸管理システム v2.0 Professional Edition > "dist\賃貸管理システムv2.0\README.txt"
echo. >> "dist\賃貸管理システムv2.0\README.txt"
echo インストール方法: >> "dist\賃貸管理システムv2.0\README.txt"
echo 1. このフォルダ全体を任意の場所にコピーしてください >> "dist\賃貸管理システムv2.0\README.txt"
echo 2. "賃貸管理システムv2.0.exe" をダブルクリックして起動してください >> "dist\賃貸管理システムv2.0\README.txt"
echo. >> "dist\賃貸管理システムv2.0\README.txt"
echo 初回起動時: >> "dist\賃貸管理システムv2.0\README.txt"
echo - ライセンスキーを入力するか、14日間のトライアルを開始してください >> "dist\賃貸管理システムv2.0\README.txt"
echo. >> "dist\賃貸管理システムv2.0\README.txt"
echo サポート: support@your-domain.com >> "dist\賃貸管理システムv2.0\README.txt"

echo ファイルコピー完了

echo.
echo [4/4] ビルド後のクリーンアップ中...
if exist "build" rd /s /q "build"
if exist "*.spec" del /q "*.spec"

echo.
echo ========================================================
echo ビルド完了！
echo ========================================================
echo.
echo 実行ファイルは以下に作成されました:
echo dist\賃貸管理システムv2.0\
echo.
echo 配布用にZIP圧縮する場合:
echo 上記フォルダ全体を圧縮してください
echo.
pause
