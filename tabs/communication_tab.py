from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QLineEdit, 
                             QComboBox, QTextEdit, QDateEdit, QFormLayout, 
                             QGroupBox, QMessageBox, QHeaderView)
from PyQt6.QtCore import Qt, QDate
from models import Communication, Customer, TenantContract, Unit, Property

class CommunicationTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_communications()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 入力フォーム
        form_group = QGroupBox("接点履歴登録")
        form_layout = QFormLayout()
        
        self.customer_combo = QComboBox()
        self.contract_combo = QComboBox()
        self.communication_type_combo = QComboBox()
        self.communication_type_combo.addItems(["電話", "メール", "面談", "その他"])
        self.subject_edit = QLineEdit()
        self.content_edit = QTextEdit()
        self.content_edit.setMaximumHeight(100)
        self.contact_date_edit = QDateEdit()
        self.contact_date_edit.setDate(QDate.currentDate())
        self.next_action_edit = QTextEdit()
        self.next_action_edit.setMaximumHeight(60)
        
        form_layout.addRow("顧客:", self.customer_combo)
        form_layout.addRow("契約:", self.contract_combo)
        form_layout.addRow("接点種別:", self.communication_type_combo)
        form_layout.addRow("件名:", self.subject_edit)
        form_layout.addRow("内容:", self.content_edit)
        form_layout.addRow("接触日:", self.contact_date_edit)
        form_layout.addRow("次回アクション:", self.next_action_edit)
        
        form_group.setLayout(form_layout)
        
        # ボタン
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("登録")
        self.add_button.clicked.connect(self.add_communication)
        self.clear_button = QPushButton("クリア")
        self.clear_button.clicked.connect(self.clear_form)
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        
        # テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "顧客名", "物件名", "部屋番号", "接点種別", 
            "件名", "接触日", "次回アクション"
        ])
        
        # テーブルの列幅を調整
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(form_group)
        layout.addLayout(button_layout)
        layout.addWidget(QLabel("接点履歴一覧"))
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        self.load_customers()
        self.load_contracts()
        
        # 顧客選択時の契約更新
        self.customer_combo.currentIndexChanged.connect(self.update_contract_combo)
        
    def load_customers(self):
        """顧客一覧をコンボボックスに読み込み"""
        self.customer_combo.clear()
        self.customer_combo.addItem("顧客を選択", None)
        
        customers = Customer.get_all()
        for customer in customers:
            self.customer_combo.addItem(customer['name'], customer['id'])
    
    def load_contracts(self):
        """契約一覧をコンボボックスに読み込み"""
        self.contract_combo.clear()
        self.contract_combo.addItem("契約を選択（任意）", None)
        
        contracts = TenantContract.get_all()
        for contract in contracts:
            display_text = f"{contract['customer_name']} - {contract['property_name']} {contract['unit_number']}"
            self.contract_combo.addItem(display_text, contract['id'])
    
    def update_contract_combo(self):
        """選択された顧客の契約のみを表示"""
        customer_id = self.customer_combo.currentData()
        if not customer_id:
            self.load_contracts()
            return
        
        self.contract_combo.clear()
        self.contract_combo.addItem("契約を選択（任意）", None)
        
        contracts = TenantContract.get_all()
        for contract in contracts:
            if contract['customer_id'] == customer_id:
                display_text = f"{contract['property_name']} {contract['unit_number']}"
                self.contract_combo.addItem(display_text, contract['id'])
    
    def load_communications(self):
        """接点履歴一覧をテーブルに読み込み"""
        self.table.setRowCount(0)
        
        # 全顧客の接点履歴を取得
        customers = Customer.get_all()
        all_communications = []
        
        for customer in customers:
            communications = Communication.get_by_customer(customer['id'])
            for comm in communications:
                comm['customer_name'] = customer['name']
                all_communications.append(comm)
        
        # 日付順でソート
        all_communications.sort(key=lambda x: x['contact_date'] or '', reverse=True)
        
        self.table.setRowCount(len(all_communications))
        
        for row, comm in enumerate(all_communications):
            self.table.setItem(row, 0, QTableWidgetItem(str(comm['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(comm['customer_name']))
            self.table.setItem(row, 2, QTableWidgetItem(comm['property_name'] or ''))
            self.table.setItem(row, 3, QTableWidgetItem(comm['unit_number'] or ''))
            self.table.setItem(row, 4, QTableWidgetItem(comm['communication_type']))
            self.table.setItem(row, 5, QTableWidgetItem(comm['subject'] or ''))
            self.table.setItem(row, 6, QTableWidgetItem(comm['contact_date'] or ''))
            self.table.setItem(row, 7, QTableWidgetItem(comm['next_action'] or ''))
    
    def add_communication(self):
        """接点履歴を登録"""
        customer_id = self.customer_combo.currentData()
        if not customer_id:
            QMessageBox.warning(self, "警告", "顧客を選択してください。")
            return
        
        contract_id = self.contract_combo.currentData()  # 任意
        
        try:
            Communication.create(
                customer_id=customer_id,
                contract_id=contract_id,
                communication_type=self.communication_type_combo.currentText(),
                subject=self.subject_edit.text().strip() or None,
                content=self.content_edit.toPlainText().strip() or None,
                contact_date=self.contact_date_edit.date().toString("yyyy-MM-dd"),
                next_action=self.next_action_edit.toPlainText().strip() or None
            )
            
            # 顧客の最終接触日を更新
            Customer.update_last_contact(customer_id)
            
            QMessageBox.information(self, "成功", "接点履歴を登録しました。")
            self.clear_form()
            self.load_communications()
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"接点履歴の登録に失敗しました: {str(e)}")
    
    def clear_form(self):
        """フォームをクリア"""
        self.customer_combo.setCurrentIndex(0)
        self.contract_combo.setCurrentIndex(0)
        self.communication_type_combo.setCurrentIndex(0)
        self.subject_edit.clear()
        self.content_edit.clear()
        self.contact_date_edit.setDate(QDate.currentDate())
        self.next_action_edit.clear() 