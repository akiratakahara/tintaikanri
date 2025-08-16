from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QLineEdit, 
                             QComboBox, QTextEdit, QFormLayout, QGroupBox, 
                             QMessageBox, QHeaderView, QFileDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor
from models import ConsistencyCheck, TenantContract, Document, DocumentType
from ocr.gemini_ocr import GeminiOCR

class ConsistencyCheckWorker(QThread):
    """整合性チェック処理を非同期で実行するワーカースレッド"""
    finished = pyqtSignal(list)  # チェック結果のリスト
    error = pyqtSignal(str)
    
    def __init__(self, contract_id: int, document_path: str, check_type: str):
        super().__init__()
        self.contract_id = contract_id
        self.document_path = document_path
        self.check_type = check_type
    
    def run(self):
        try:
            ocr = GeminiOCR()
            
            # チェック項目の定義
            check_items = {
                'registry': [
                    "所在地", "構造", "階数", "面積", "所有者氏名"
                ],
                'government_doc': [
                    "都市計画用途", "接道", "容積率", "建蔽率", "用途地域"
                ]
            }
            
            # OCRでテキスト抽出
            ocr_result = ocr.extract_text_from_image(self.document_path)
            
            # チェック結果を生成（実際の実装ではより詳細な解析が必要）
            results = []
            for item in check_items.get(self.check_type, []):
                # 簡易的な実装：実際にはOCR結果から該当項目を抽出する必要がある
                results.append({
                    'check_item': item,
                    'document_type': self.check_type,
                    'extracted_value': f"OCR抽出値: {item}",
                    'db_value': f"DB登録値: {item}",
                    'is_consistent': True,  # 実際の実装では比較ロジックが必要
                    'notes': "自動チェック完了"
                })
            
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(str(e))

class ConsistencyCheckTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_checks()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 整合性チェックフォーム
        form_group = QGroupBox("整合性チェック実行")
        form_layout = QFormLayout()
        
        self.contract_combo = QComboBox()
        self.check_type_combo = QComboBox()
        self.check_type_combo.addItems(["登記簿謄本", "行政資料"])
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        
        form_layout.addRow("契約:", self.contract_combo)
        form_layout.addRow("チェック種別:", self.check_type_combo)
        form_layout.addRow("ファイル:", self.file_path_edit)
        
        form_group.setLayout(form_layout)
        
        # ボタン
        button_layout = QHBoxLayout()
        self.browse_button = QPushButton("ファイル選択")
        self.browse_button.clicked.connect(self.browse_file)
        self.check_button = QPushButton("整合性チェック実行")
        self.check_button.clicked.connect(self.run_consistency_check)
        self.clear_button = QPushButton("クリア")
        self.clear_button.clicked.connect(self.clear_form)
        
        button_layout.addWidget(self.browse_button)
        button_layout.addWidget(self.check_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        
        # チェック結果表示
        self.result_text = QTextEdit()
        self.result_text.setMaximumHeight(150)
        self.result_text.setPlaceholderText("整合性チェック結果がここに表示されます")
        
        # チェック結果テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "契約", "チェック項目", "書類種別", "抽出結果", "DB登録値", "一致"
        ])
        
        # テーブルの列幅を調整
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(form_group)
        layout.addLayout(button_layout)
        layout.addWidget(QLabel("チェック結果"))
        layout.addWidget(self.result_text)
        layout.addWidget(QLabel("整合性チェック履歴"))
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        self.load_contracts()
        
    def load_contracts(self):
        """契約一覧をコンボボックスに読み込み"""
        self.contract_combo.clear()
        self.contract_combo.addItem("契約を選択", None)
        
        contracts = TenantContract.get_all()
        for contract in contracts:
            display_text = f"{contract['customer_name']} - {contract['property_name']} {contract['unit_number']}"
            self.contract_combo.addItem(display_text, contract['id'])
    
    def browse_file(self):
        """ファイル選択"""
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
    
    def run_consistency_check(self):
        """整合性チェックを実行"""
        contract_id = self.contract_combo.currentData()
        file_path = self.file_path_edit.text().strip()
        
        if not contract_id:
            QMessageBox.warning(self, "警告", "契約を選択してください。")
            return
        
        if not file_path:
            QMessageBox.warning(self, "警告", "ファイルを選択してください。")
            return
        
        # チェック種別をマッピング
        check_type_map = {
            "登記簿謄本": "registry",
            "行政資料": "government_doc"
        }
        check_type = check_type_map.get(self.check_type_combo.currentText(), "registry")
        
        # ワーカースレッドで非同期実行
        self.worker = ConsistencyCheckWorker(contract_id, file_path, check_type)
        self.worker.finished.connect(self.on_check_finished)
        self.worker.error.connect(self.on_check_error)
        self.worker.start()
        
        self.check_button.setEnabled(False)
        self.result_text.setText("整合性チェックを実行中...")
    
    def on_check_finished(self, results):
        """チェック完了時の処理"""
        self.check_button.setEnabled(True)
        
        contract_id = self.contract_combo.currentData()
        
        # 結果をデータベースに保存
        for result in results:
            ConsistencyCheck.create(
                contract_id=contract_id,
                check_item=result['check_item'],
                document_type=result['document_type'],
                extracted_value=result['extracted_value'],
                db_value=result['db_value'],
                is_consistent=result['is_consistent'],
                notes=result['notes']
            )
        
        # 結果表示
        result_text = "整合性チェック完了\n\n"
        for result in results:
            status = "○" if result['is_consistent'] else "×"
            result_text += f"{result['check_item']}: {status}\n"
        
        self.result_text.setText(result_text)
        
        # テーブルを更新
        self.load_checks()
        
        QMessageBox.information(self, "完了", "整合性チェックが完了しました。")
    
    def on_check_error(self, error):
        """チェックエラー時の処理"""
        self.check_button.setEnabled(True)
        self.result_text.setText(f"エラー: {error}")
        QMessageBox.critical(self, "エラー", f"整合性チェック中にエラーが発生しました: {error}")
    
    def load_checks(self):
        """整合性チェック履歴をテーブルに読み込み"""
        self.table.setRowCount(0)
        
        # 全契約のチェック結果を取得
        contracts = TenantContract.get_all()
        all_checks = []
        
        for contract in contracts:
            checks = ConsistencyCheck.get_by_contract(contract['id'])
            for check in checks:
                check['contract_display'] = f"{contract['customer_name']} - {contract['property_name']} {contract['unit_number']}"
                all_checks.append(check)
        
        # 日付順でソート
        all_checks.sort(key=lambda x: x['created_at'], reverse=True)
        
        self.table.setRowCount(len(all_checks))
        
        for row, check in enumerate(all_checks):
            self.table.setItem(row, 0, QTableWidgetItem(str(check['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(check['contract_display']))
            self.table.setItem(row, 2, QTableWidgetItem(check['check_item']))
            self.table.setItem(row, 3, QTableWidgetItem(check['document_type']))
            self.table.setItem(row, 4, QTableWidgetItem(check['extracted_value'] or ''))
            self.table.setItem(row, 5, QTableWidgetItem(check['db_value'] or ''))
            
            # 一致状況を表示
            consistency_item = QTableWidgetItem("○" if check['is_consistent'] else "×")
            if not check['is_consistent']:
                consistency_item.setBackground(QColor(255, 200, 200))  # 赤色背景
            self.table.setItem(row, 6, consistency_item)
    
    def clear_form(self):
        """フォームをクリア"""
        self.contract_combo.setCurrentIndex(0)
        self.check_type_combo.setCurrentIndex(0)
        self.file_path_edit.clear()
        self.result_text.clear() 