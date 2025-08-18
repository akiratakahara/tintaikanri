@echo off
echo ========================================
echo Python キャッシュをクリア中...
echo ========================================
echo.

REM .pyc ファイルを削除
for /r %%i in (*.pyc) do (
    echo 削除中: %%i
    del "%%i"
)

REM __pycache__ フォルダを削除
for /d /r %%i in (__pycache__) do (
    echo 削除中: %%i
    rmdir /s /q "%%i" 2>nul
)

echo.
echo ✅ キャッシュクリア完了
echo.

REM Modern Edition を起動
echo Modern Edition を起動中...
python main.py

pause