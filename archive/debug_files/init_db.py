#!/usr/bin/env python3
"""
データベース初期化スクリプト
"""

from models import create_tables

def main():
    print("データベースを初期化しています...")
    try:
        create_tables()
        print("✅ データベースの初期化が完了しました！")
        print("アプリケーションを起動できます。")
    except Exception as e:
        print(f"❌ データベース初期化エラー: {e}")

if __name__ == "__main__":
    main() 