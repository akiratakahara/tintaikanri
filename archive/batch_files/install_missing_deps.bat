@echo off
echo Missing Dependencies Installer
echo =================================
echo.

echo [INFO] 仮想環境をアクティベート中...
call .venv\Scripts\activate.bat

echo [INFO] 不足している依存関係をインストール中...
echo.

echo - Google Generative AI...
pip install google-generativeai==0.3.2

echo - SQLAlchemy...
pip install SQLAlchemy==2.0.23

echo - Pillow...
pip install Pillow>=10.2.0

echo - Requests...
pip install requests==2.31.0

echo - Python-dotenv...
pip install python-dotenv==1.0.0

echo.
echo [INFO] インストール確認中...
python -c "import google.generativeai; print('[SUCCESS] Google Generative AI OK')"
python -c "import sqlite3; print('[SUCCESS] SQLite3 OK')"
python -c "import PIL; print('[SUCCESS] Pillow OK')"
python -c "import requests; print('[SUCCESS] Requests OK')"
python -c "import dotenv; print('[SUCCESS] Python-dotenv OK')"

echo.
echo =================================
echo 依存関係のインストールが完了しました
echo =================================
echo.
echo 次のステップ: run_improved.bat を実行
pause