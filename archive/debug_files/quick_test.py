#!/usr/bin/env python3
"""
修正後のアプリケーション起動テスト
"""
import sys
from PyQt6.QtWidgets import QApplication

# モジュールのパスを追加
sys.path.insert(0, '.')

from modern_main_window import ModernMainWindow
from models import create_tables

def main():
    print("=" * 50)
    print("修正後のアプリケーション起動テスト")
    print("=" * 50)
    
    # データベース初期化
    print("\n1. データベース初期化中...")
    create_tables()
    print("   ✓ データベース初期化完了")
    
    # アプリケーション作成
    print("\n2. アプリケーション作成中...")
    app = QApplication(sys.argv)
    print("   ✓ QApplication作成完了")
    
    # メインウィンドウ作成
    print("\n3. メインウィンドウ作成中...")
    main_window = ModernMainWindow()
    print("   ✓ メインウィンドウ作成完了")
    
    # ウィンドウ表示
    print("\n4. ウィンドウ表示中...")
    main_window.show()
    print("   ✓ ウィンドウ表示完了")
    
    print("\n" + "=" * 50)
    print("✅ アプリケーションが正常に起動しました！")
    print("📋 確認できること:")
    print("  - 左サイドバーに「顧客管理」メニュー")
    print("  - 顧客管理ページ内に「所有物件管理」タブ")
    print("  - 物件管理ページ内に「オーナー情報」セクション")
    print("  - 部屋管理ページ内に「オーナー情報」セクション")
    print("  - ダッシュボードの「最近の活動」にアクティビティログ")
    print("=" * 50)
    
    # アプリケーション実行
    sys.exit(app.exec())

if __name__ == "__main__":
    main()