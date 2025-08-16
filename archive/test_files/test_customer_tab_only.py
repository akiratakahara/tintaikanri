#!/usr/bin/env python3
"""
顧客タブのみを表示するテストスクリプト
"""
import sys
from PyQt6.QtWidgets import QApplication

# モジュールのパスを追加
sys.path.insert(0, '.')

from customer_tab import CustomerTab
from models import create_tables

def main():
    # データベース初期化
    create_tables()
    
    # アプリケーション作成
    app = QApplication(sys.argv)
    
    # 顧客タブのみを表示
    customer_tab = CustomerTab()
    customer_tab.setWindowTitle("顧客管理 - 所有物件管理機能テスト")
    customer_tab.resize(1000, 700)
    customer_tab.show()
    
    print("顧客タブが表示されました。")
    print("画面上部に「顧客管理」と「所有物件管理」の2つのタブがあることを確認してください。")
    
    # アプリケーション実行
    sys.exit(app.exec())

if __name__ == "__main__":
    main()