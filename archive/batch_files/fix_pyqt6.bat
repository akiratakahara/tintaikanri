@echo off
echo PyQt6 DLL問題の修正スクリプト
echo ================================
echo.

echo 1. 古い仮想環境を削除中...
if exist ".venv" (
    rmdir /s /q .venv
    echo 仮想環境を削除しました
) else (
    echo 仮想環境は存在しませんでした
)
echo.

echo 2. 新しい仮想環境を作成中...
python -m venv .venv
if errorlevel 1 (
    echo エラー: 仮想環境の作成に失敗しました
    pause
    exit /b 1
)
echo 仮想環境を作成しました
echo.

echo 3. 仮想環境をアクティベート中...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo エラー: 仮想環境のアクティベートに失敗しました
    pause
    exit /b 1
)
echo.

echo 4. pipをアップグレード中...
python -m pip install --upgrade pip
echo.

echo 5. PyQt6を新規インストール中...
echo   - 古いPyQt6をアンインストール...
pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip -y

echo   - 最新のPyQt6をインストール...
pip install PyQt6==6.7.0
if errorlevel 1 (
    echo エラー: PyQt6のインストールに失敗しました
    echo 別のバージョンを試行します...
    pip install PyQt6==6.6.1
)
echo.

echo 6. その他の依存関係をインストール中...
pip install python-dotenv==1.0.0
pip install requests==2.31.0
pip install Pillow>=10.2.0
echo.

echo 7. インストール結果を確認中...
python -c "import PyQt6.QtWidgets; print('PyQt6インストール成功!')"
if errorlevel 1 (
    echo エラー: PyQt6の動作確認に失敗しました
    echo.
    echo 追加の修正手順:
    echo 1. Microsoft Visual C++ Redistributable 2015-2022をインストール
    echo 2. Windows Updateを実行
    echo 3. システムを再起動
    pause
    exit /b 1
)
echo.

echo ================================
echo PyQt6の修正が完了しました！
echo ================================
echo.
echo 次のステップ:
echo 1. このウィンドウを閉じる
echo 2. run_improved.bat を実行
echo.
pause