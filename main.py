#!/usr/bin/env python3
"""
賃貸管理システム v2.0 - Modern Edition ✅
メインエントリーポイント
"""

import sys
import os
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ModernMainWindowを直接import
from modern_main_window import ModernMainWindow
from models import create_tables

def main():
    """メイン関数"""
    # Windows文字化け対策
    if os.name == 'nt':
        try:
            os.system('chcp 65001 >nul 2>&1')
            import codecs
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'ignore')
        except:
            pass
    
    app = QApplication(sys.argv)
    
    # 高DPI対応（PyQt6では自動的に有効）
    try:
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    except AttributeError:
        pass  # PyQt6では不要
    
    try:
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        pass  # PyQt6では不要
    
    # フォント設定
    if os.name == 'nt':
        font = QFont("Yu Gothic UI", 9)
        if not font.exactMatch():
            font = QFont("Segoe UI", 9)
        app.setFont(font)
    
    try:
        print("========================================")
        print("🏢 賃貸管理システム v2.0 - Modern Edition ✅")
        print("========================================")
        print("✨ モダンUIで全面刷新しました")
        print("🚀 起動中...")
        print()
        
        # データベース初期化
        create_tables()
        
        window = ModernMainWindow()
        window.show()
        
        print("[SUCCESS] アプリケーションが正常に起動しました")
        print("💡 左のサイドバーからページを切り替えてください")
        
        sys.exit(app.exec())
        
    except Exception as e:
        error_msg = f"アプリケーション起動エラー: {e}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        
        try:
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Icon.Critical)
            error_dialog.setWindowTitle("起動エラー")
            error_dialog.setText("アプリケーションの起動に失敗しました")
            error_dialog.setDetailedText(str(e))
            error_dialog.exec()
        except:
            pass
        
        input("エラーが発生しました。Enterキーで終了...")

if __name__ == "__main__":
    main()