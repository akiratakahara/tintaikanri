import sys
import json
import os
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem,
                             QPushButton, QLabel, QLineEdit, QTextEdit, QFileDialog,
                             QMessageBox, QGroupBox, QFormLayout, QSpinBox, 
                             QDoubleSpinBox, QDateEdit, QCheckBox, QComboBox,
                             QProgressBar, QSplitter, QScrollArea)
from PyQt6.QtCore import Qt, QDate, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

from models import (Customer, Property, TenantContract, Document, ChecklistStatus, 
                   create_tables)
from gemini_ocr import GeminiOCR
from config import APP_TITLE, APP_VERSION
from customer_tab import CustomerTab
from property_tab import PropertyTab
from contract_tab import ContractTab
from document_tab import DocumentTab
from checklist_tab import ChecklistTab
from unit_tab import UnitTab
from task_tab import TaskTab
from communication_tab import CommunicationTab
from consistency_check_tab import ConsistencyCheckTab

class OCRWorker(QThread):
    """OCR処理を非同期で実行するワーカースレッド"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, image_path, ocr_type="text"):
        super().__init__()
        self.image_path = image_path
        self.ocr_type = ocr_type
    
    def run(self):
        try:
            ocr = GeminiOCR()
            if self.ocr_type == "text":
                result = ocr.extract_text_from_image(self.image_path)
            else:
                result = ocr.extract_checklist_items(self.image_path)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    """メインウィンドウ"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_database()
    
    def init_ui(self):
        self.setWindowTitle("賃貸顧客管理システム")
        self.setGeometry(100, 100, 1200, 800)
        
        # メインウィジェット
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # メインレイアウト
        layout = QVBoxLayout()
        
        # タイトル
        title_label = QLabel("賃貸顧客管理システム")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        
        # 顧客管理タブ
        self.customer_tab = CustomerTab()
        self.tab_widget.addTab(self.customer_tab, "顧客管理")
        
        # 物件管理タブ（統合版）
        self.property_tab = PropertyTab()
        self.tab_widget.addTab(self.property_tab, "物件管理")
        
        # 部屋管理タブ
        self.unit_tab = UnitTab()
        self.tab_widget.addTab(self.unit_tab, "部屋管理")
        
        # 契約管理タブ
        self.contract_tab = ContractTab()
        self.tab_widget.addTab(self.contract_tab, "契約管理")
        
        # 書類管理タブ
        self.document_tab = DocumentTab()
        self.tab_widget.addTab(self.document_tab, "書類管理")
        
        # チェックリストタブ
        self.checklist_tab = ChecklistTab()
        self.tab_widget.addTab(self.checklist_tab, "チェックリスト")
        
        # タスク管理タブ
        self.task_tab = TaskTab()
        self.tab_widget.addTab(self.task_tab, "タスク管理")
        
        # 接点履歴タブ
        self.communication_tab = CommunicationTab()
        self.tab_widget.addTab(self.communication_tab, "接点履歴")
        
        # 整合性チェックタブ
        self.consistency_check_tab = ConsistencyCheckTab()
        self.tab_widget.addTab(self.consistency_check_tab, "整合性チェック")
        
        layout.addWidget(self.tab_widget)
        
        main_widget.setLayout(layout)
    
    def init_database(self):
        """データベースの初期化"""
        try:
            create_tables()
            print("データベーステーブルが作成されました。")
        except Exception as e:
            print(f"データベース初期化中にエラーが発生しました: {str(e)}")

def main():
    app = QApplication(sys.argv)
    
    # アプリケーションスタイルの設定
    app.setStyle('Fusion')
    
    # メインウィンドウの作成と表示
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 