#!/usr/bin/env python3
"""
アプリケーション起動スクリプト（キャッシュクリア版）
"""

import sys
import os
import shutil

# キャッシュクリア
def clear_cache():
    """Pythonキャッシュをクリア"""
    try:
        # __pycache__ ディレクトリを削除
        for root, dirs, files in os.walk('.'):
            for d in dirs:
                if d == '__pycache__':
                    cache_path = os.path.join(root, d)
                    print(f"Removing cache: {cache_path}")
                    shutil.rmtree(cache_path, ignore_errors=True)
        print("✅ キャッシュクリア完了")
    except Exception as e:
        print(f"⚠️ キャッシュクリア中にエラー: {e}")

if __name__ == "__main__":
    print("🧹 キャッシュをクリアしています...")
    clear_cache()
    
    print("🚀 アプリケーションを起動しています...")
    
    # メインアプリケーションを起動
    try:
        from main import main
        main()
    except Exception as e:
        print(f"❌ 起動エラー: {e}")
        import traceback
        traceback.print_exc()