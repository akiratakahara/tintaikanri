#!/usr/bin/env python3
"""
改善された物件管理タブのテストスクリプト
"""
import sys
from PyQt6.QtWidgets import QApplication
from property_tab_improved import PropertyTabImproved
from models import create_tables

def main():
    print("=" * 60)
    print("改善された物件管理タブの機能テスト")
    print("=" * 60)
    
    # データベース初期化
    print("\n1. データベース初期化...")
    create_tables()
    print("   ✅ 完了")
    
    # アプリケーション作成
    print("\n2. テストアプリケーション作成...")
    app = QApplication(sys.argv)
    
    # 改善されたタブ作成
    print("\n3. 改善された物件管理タブ作成...")
    property_tab = PropertyTabImproved()
    print("   ✅ 完了")
    
    # ウィンドウ設定
    property_tab.setWindowTitle("物件管理タブ改善版 - テスト")
    property_tab.resize(1200, 800)
    
    print("\n4. ウィンドウ表示...")
    property_tab.show()
    print("   ✅ 完了")
    
    print("\n" + "=" * 60)
    print("🎉 改善された物件管理タブが正常に起動しました！")
    print("📋 確認できる改善点:")
    print("  ✓ 左右分割レイアウト（物件一覧 | 詳細編集）")
    print("  ✓ モーダルダイアログによる新規登録")
    print("  ✓ タブ形式の詳細表示（基本情報 | オーナー管理）")
    print("  ✓ スタイリッシュなボタンデザイン")
    print("  ✓ 直感的な操作フロー")
    print("=" * 60)
    
    # アプリケーション実行
    sys.exit(app.exec())

if __name__ == "__main__":
    main()