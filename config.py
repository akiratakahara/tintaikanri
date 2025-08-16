import os
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

# Gemini API設定
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    # 環境変数が設定されていない場合のデフォルト値
    GEMINI_API_KEY = "AIzaSyCrpvxCC6mqPF9Il3qPwDp84hMJFT0XagU"

# データベース設定
DATABASE_URL = "sqlite:///tintai_management.db"

# アプリケーション設定
APP_TITLE = "賃貸顧客管理システム"
APP_VERSION = "1.0.0" 