import os
import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QLineEdit, 
                             QTextEdit, QMessageBox, QGroupBox, QFormLayout, QComboBox, QFileDialog)
from PyQt6.QtCore import QThread, pyqtSignal

# プロジェクトルートをPythonパスに追加（tabsフォルダ内のモジュールがルートのモジュールにアクセスできるように）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ChecklistStatus, TenantContract, Customer, Property
from gemini_ocr import GeminiOCR

class ChecklistWorker(QThread):
    """チェックリスト処理を非同期で実行するワーカースレッド"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
    
    def run(self):
        try:
            ocr = GeminiOCR()
            result = ocr.extract_checklist_items(self.image_path)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class ChecklistTab(QWidget):
    """チェックリスト管理タブ"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_checklists()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # チェックリスト生成フォーム
        form_group = QGroupBox("チェックリスト生成")
        form_layout = QFormLayout()
        
        self.contract_combo = QComboBox()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        
        form_layout.addRow("契約:", self.contract_combo)
        form_layout.addRow("チェックリストファイル:", self.file_path_edit)
        
        form_group.setLayout(form_layout)
        
        # ボタン
        button_layout = QHBoxLayout()
        self.browse_button = QPushButton("ファイル選択")
        self.browse_button.clicked.connect(self.browse_file)
        self.generate_button = QPushButton("チェックリスト生成")
        self.generate_button.clicked.connect(self.generate_checklist)
        self.clear_button = QPushButton("クリア")
        self.clear_button.clicked.connect(self.clear_form)
        
        button_layout.addWidget(self.browse_button)
        button_layout.addWidget(self.generate_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        
        # チェックリスト結果表示
        self.checklist_result_text = QTextEdit()
        self.checklist_result_text.setMaximumHeight(200)
        self.checklist_result_text.setPlaceholderText("チェックリスト結果がここに表示されます")
        
        # チェックリスト一覧テーブル
        self.checklist_table = QTableWidget()
        self.checklist_table.setColumnCount(6)
        self.checklist_table.setHorizontalHeaderLabels(["ID", "契約", "項目名", "必須", "完了", "備考"])
        
        layout.addWidget(form_group)
        layout.addLayout(button_layout)
        layout.addWidget(QLabel("チェックリスト結果"))
        layout.addWidget(self.checklist_result_text)
        layout.addWidget(QLabel("チェックリスト一覧"))
        layout.addWidget(self.checklist_table)
        
        self.setLayout(layout)
        self.load_contract_combo()
    
    def load_contract_combo(self):
        try:
            contracts = TenantContract.get_all()
            self.contract_combo.clear()
            for contract in contracts:
                display_text = f"{contract['customer_name']} - {contract['property_name']} {contract['unit_number']}"
                self.contract_combo.addItem(display_text, contract['id'])
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"契約コンボボックスの読み込み中にエラーが発生しました: {str(e)}")
    
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "チェックリストファイルを選択", "", 
            "すべてのファイル (*.*);;"
            "画像ファイル (*.png *.jpg *.jpeg *.bmp *.tiff);;"
            "PDFファイル (*.pdf);;"
            "Wordファイル (*.doc *.docx);;"
            "Excelファイル (*.xls *.xlsx);;"
            "テキストファイル (*.txt)"
        )
        if file_path:
            self.file_path_edit.setText(file_path)
    
    def generate_checklist(self):
        contract_id = self.contract_combo.currentData()
        file_path = self.file_path_edit.text().strip()
        
        if not contract_id:
            QMessageBox.warning(self, "警告", "契約を選択してください。")
            return
        
        if not file_path:
            QMessageBox.warning(self, "警告", "ファイルを選択してください。")
            return
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "警告", "選択されたファイルが存在しません。")
            return
        
        # OCR処理を非同期で実行
        self.checklist_worker = ChecklistWorker(file_path)
        self.checklist_worker.finished.connect(self.on_checklist_finished)
        self.checklist_worker.error.connect(self.on_checklist_error)
        self.checklist_worker.start()
        
        QMessageBox.information(self, "処理中", "チェックリスト生成を開始しました。しばらくお待ちください。")
    
    def on_checklist_finished(self, result):
        self.checklist_result_text.setText(result)
        QMessageBox.information(self, "完了", "チェックリスト生成が完了しました。")
    
    def on_checklist_error(self, error):
        QMessageBox.critical(self, "エラー", f"チェックリスト生成中にエラーが発生しました: {error}")
    
    def clear_form(self):
        self.file_path_edit.clear()
        self.checklist_result_text.clear()
    
    def load_checklists(self):
        try:
            # 契約情報を取得
            contracts = TenantContract.get_all()
            contract_dict = {contract['id']: contract for contract in contracts}
            
            # 全チェックリスト項目を取得（簡易版）
            all_items = []
            for contract in contracts:
                contract_items = ChecklistStatus.get_by_contract(contract['id'])
                for item in contract_items:
                    item['contract_info'] = contract
                    all_items.append(item)
            
            self.checklist_table.setRowCount(len(all_items))
            for i, item in enumerate(all_items):
                contract_info = item['contract_info']
                self.checklist_table.setItem(i, 0, QTableWidgetItem(str(item['id'])))
                self.checklist_table.setItem(i, 1, QTableWidgetItem(f"{contract_info['customer_name']} - {contract_info['property_name']} {contract_info['unit_number']}"))
                self.checklist_table.setItem(i, 2, QTableWidgetItem(item['item_name']))
                self.checklist_table.setItem(i, 3, QTableWidgetItem("必須" if item['is_required'] else "任意"))
                self.checklist_table.setItem(i, 4, QTableWidgetItem("完了" if item['is_completed'] else "未完了"))
                self.checklist_table.setItem(i, 5, QTableWidgetItem(item['notes'] or ""))
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"チェックリスト一覧の読み込み中にエラーが発生しました: {str(e)}") 