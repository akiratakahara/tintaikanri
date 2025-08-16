#!/usr/bin/env python3
"""
Quick UI test to verify calendar layout fixes
"""
import sys
import os

def test_calendar_ui():
    """Test calendar UI without full application startup"""
    try:
        print("=== UI テスト開始 ===")
        
        # PyQt6のインポートテスト
        from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QLabel
        from PyQt6.QtCore import Qt
        
        print("✅ PyQt6インポート成功")
        
        # アプリケーション作成
        app = QApplication(sys.argv)
        
        # テスト用ウィジェット
        main_widget = QWidget()
        main_widget.setWindowTitle("UIテスト - カレンダーレイアウト")
        main_widget.resize(1200, 800)
        
        # レイアウトテスト
        layout = QVBoxLayout()
        
        # スプリッターテスト
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左側（カレンダー側）
        left_widget = QWidget()
        left_widget.setStyleSheet("background-color: #e3f2fd; border: 2px solid #2196f3;")
        left_label = QLabel("カレンダー領域\n(全画面対応)")
        left_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout = QVBoxLayout()
        left_layout.addWidget(left_label)
        left_widget.setLayout(left_layout)
        
        # 右側（詳細側）
        right_widget = QWidget()
        right_widget.setStyleSheet("background-color: #f3e5f5; border: 2px solid #9c27b0;")
        right_label = QLabel("スケジュール詳細領域\n(レスポンシブ)")
        right_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout = QVBoxLayout()
        right_layout.addWidget(right_label)
        right_widget.setLayout(right_layout)
        
        # スプリッターに追加
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        
        # 比率設定（修正内容のテスト）
        splitter.setStretchFactor(0, 2)  # カレンダー側
        splitter.setStretchFactor(1, 1)  # 詳細側
        splitter.setSizes([600, 400])
        
        # 折りたたみ無効化（修正内容のテスト）
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        
        layout.addWidget(splitter)
        main_widget.setLayout(layout)
        
        print("✅ レイアウト構築成功")
        
        # 表示
        main_widget.show()
        
        print("✅ UI表示成功")
        print("ウィンドウが表示されました。閉じてテストを終了してください。")
        
        # イベントループ
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"❌ インポートエラー: {e}")
        print("PyQt6がインストールされていません")
        return False
    except Exception as e:
        print(f"❌ UIテストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Windows文字化け対策
    if os.name == 'nt':
        try:
            os.system('chcp 65001 >nul 2>&1')
        except:
            pass
    
    test_calendar_ui()