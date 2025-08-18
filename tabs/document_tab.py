import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QLineEdit, 
                             QTextEdit, QMessageBox, QGroupBox, QFormLayout, 
                             QComboBox, QFileDialog, QDateEdit, QDialog, QDialogButtonBox)
from PyQt6.QtCore import Qt, QDate, QThread, pyqtSignal
import sys

# プロジェクトルートをPythonパスに追加（tabsフォルダ内のモジュールがルートのモジュールにアクセスできるように）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Document, TenantContract, Customer, Property, DocumentType
from gemini_ocr import GeminiOCR

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

class DocumentTab(QWidget):
    """書類管理タブ"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_documents()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 書類アップロードフォーム
        form_group = QGroupBox("書類アップロード")
        form_layout = QFormLayout()
        
        self.contract_combo = QComboBox()
        self.document_type_combo = QComboBox()
        # DocumentTypeの日本語表示名をコンボボックスに追加
        document_types = [
            ("契約書", DocumentType.CONTRACT),
            ("重要事項説明書", DocumentType.EXPLANATION),
            ("登記簿謄本", DocumentType.REGISTRY),
            ("申込書", DocumentType.APPLICATION),
            ("見積書", DocumentType.ESTIMATE),
            ("鍵預り証", DocumentType.KEY_RECEIPT),
            ("メール履歴", DocumentType.EMAIL_LOG),
            ("行政資料", DocumentType.GOVERNMENT_DOC),
            ("その他", DocumentType.OTHERS)
        ]
        for display_name, doc_type in document_types:
            self.document_type_combo.addItem(display_name, doc_type.value)
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        
        form_layout.addRow("契約:", self.contract_combo)
        form_layout.addRow("書類種別:", self.document_type_combo)
        form_layout.addRow("ファイル:", self.file_path_edit)
        
        form_group.setLayout(form_layout)
        
        # ボタン
        button_layout = QHBoxLayout()
        self.browse_button = QPushButton("ファイル選択")
        self.browse_button.clicked.connect(self.browse_file)
        self.upload_button = QPushButton("書類登録")
        self.upload_button.clicked.connect(self.upload_document)
        self.ocr_button = QPushButton("OCR実行")
        self.ocr_button.clicked.connect(self.run_ocr)
        self.clear_button = QPushButton("クリア")
        self.clear_button.clicked.connect(self.clear_form)
        
        button_layout.addWidget(self.browse_button)
        button_layout.addWidget(self.upload_button)
        button_layout.addWidget(self.ocr_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        
        # OCR結果表示
        self.ocr_result_text = QTextEdit()
        self.ocr_result_text.setMaximumHeight(200)
        self.ocr_result_text.setPlaceholderText("OCR結果がここに表示されます")
        
        # 書類一覧テーブル
        self.document_table = QTableWidget()
        self.document_table.setColumnCount(5)
        self.document_table.setHorizontalHeaderLabels(["ID", "契約", "書類種別", "ファイルパス", "OCR結果"])
        
        layout.addWidget(form_group)
        layout.addLayout(button_layout)
        layout.addWidget(QLabel("OCR結果"))
        layout.addWidget(self.ocr_result_text)
        layout.addWidget(QLabel("書類一覧"))
        layout.addWidget(self.document_table)
        
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
            self, "書類ファイルを選択", "", 
            "すべてのファイル (*.*);;"
            "画像ファイル (*.png *.jpg *.jpeg *.bmp *.tiff);;"
            "PDFファイル (*.pdf);;"
            "Wordファイル (*.doc *.docx);;"
            "Excelファイル (*.xls *.xlsx);;"
            "テキストファイル (*.txt)"
        )
        if file_path:
            self.file_path_edit.setText(file_path)
    
    def upload_document(self):
        contract_id = self.contract_combo.currentData()
        file_path = self.file_path_edit.text().strip()
        
        if not contract_id:
            QMessageBox.warning(self, "警告", "契約を選択してください。")
            return
        
        if not file_path:
            QMessageBox.warning(self, "警告", "ファイルを選択してください。")
            return
        
        try:
            Document.create(
                contract_id=contract_id,
                document_type=self.document_type_combo.currentText(),
                file_path=file_path
            )
            
            QMessageBox.information(self, "成功", "書類を登録しました。")
            self.load_documents()
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"書類登録中にエラーが発生しました: {str(e)}")
    
    def run_ocr(self):
        file_path = self.file_path_edit.text().strip()
        if not file_path:
            QMessageBox.warning(self, "警告", "ファイルを選択してください。")
            return
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "警告", "選択されたファイルが存在しません。")
            return
        
        # OCR処理を非同期で実行
        self.ocr_worker = OCRWorker(file_path, "text")
        self.ocr_worker.finished.connect(self.on_ocr_finished)
        self.ocr_worker.error.connect(self.on_ocr_error)
        self.ocr_worker.start()
        
        QMessageBox.information(self, "処理中", "OCR処理を開始しました。しばらくお待ちください。")
    
    def on_ocr_finished(self, result):
        self.ocr_result_text.setText(result)
        QMessageBox.information(self, "完了", "OCR処理が完了しました。")
    
    def on_ocr_error(self, error):
        QMessageBox.critical(self, "エラー", f"OCR処理中にエラーが発生しました: {error}")
    
    def clear_form(self):
        self.file_path_edit.clear()
        self.ocr_result_text.clear()
    
    def load_documents(self):
        try:
            # 契約情報を取得
            contracts = TenantContract.get_all()
            contract_dict = {contract['id']: contract for contract in contracts}
            
            # 全書類を取得（簡易版）
            documents = []
            for contract in contracts:
                contract_docs = Document.get_by_contract(contract['id'])
                for doc in contract_docs:
                    doc['contract_info'] = contract
                    documents.append(doc)
            
            self.document_table.setRowCount(len(documents))
            for i, document in enumerate(documents):
                contract_info = document['contract_info']
                self.document_table.setItem(i, 0, QTableWidgetItem(str(document['id'])))
                self.document_table.setItem(i, 1, QTableWidgetItem(f"{contract_info['customer_name']} - {contract_info['property_name']} {contract_info['unit_number']}"))
                self.document_table.setItem(i, 2, QTableWidgetItem(document['document_type']))
                self.document_table.setItem(i, 3, QTableWidgetItem(document['file_path'] or ""))
                ocr_result = document['ocr_result'] or ""
                self.document_table.setItem(i, 4, QTableWidgetItem(ocr_result[:50] + "..." if len(ocr_result) > 50 else ocr_result))
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"書類一覧の読み込み中にエラーが発生しました: {str(e)}") 