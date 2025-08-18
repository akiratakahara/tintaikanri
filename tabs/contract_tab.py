from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QLineEdit, 
                             QTextEdit, QMessageBox, QGroupBox, QFormLayout, QComboBox, QDateEdit, QSpinBox)
from PyQt6.QtCore import Qt, QDate
import sys
import os

# プロジェクトルートをPythonパスに追加（tabsフォルダ内のモジュールがルートのモジュールにアクセスできるように）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import TenantContract, Unit, Property

class ContractTab(QWidget):
    """契約管理タブ"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_contracts()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 契約登録フォーム
        form_group = QGroupBox("契約登録")
        form_layout = QFormLayout()
        
        self.unit_combo = QComboBox()
        self.contractor_name_edit = QLineEdit()
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate())
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate().addYears(2))
        self.rent_spin = QSpinBox()
        self.rent_spin.setMaximum(999999)
        self.maintenance_fee_spin = QSpinBox()
        self.maintenance_fee_spin.setMaximum(99999)
        self.security_deposit_spin = QSpinBox()
        self.security_deposit_spin.setMaximum(999999)
        self.key_money_spin = QSpinBox()
        self.key_money_spin.setMaximum(999999)
        self.renewal_method_edit = QLineEdit()
        self.insurance_flag_check = QCheckBox("保険加入")
        self.memo_edit = QTextEdit()
        self.memo_edit.setMaximumHeight(60)
        
        form_layout.addRow("部屋:", self.unit_combo)
        form_layout.addRow("契約者名:", self.contractor_name_edit)
        form_layout.addRow("入居開始日:", self.start_date_edit)
        form_layout.addRow("契約終了日:", self.end_date_edit)
        form_layout.addRow("賃料:", self.rent_spin)
        form_layout.addRow("管理費:", self.maintenance_fee_spin)
        form_layout.addRow("敷金:", self.security_deposit_spin)
        form_layout.addRow("礼金:", self.key_money_spin)
        form_layout.addRow("更新方法:", self.renewal_method_edit)
        form_layout.addRow("保険:", self.insurance_flag_check)
        form_layout.addRow("メモ:", self.memo_edit)
        
        form_group.setLayout(form_layout)
        
        # ボタン
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("契約登録")
        self.add_button.clicked.connect(self.add_contract)
        self.clear_button = QPushButton("クリア")
        self.clear_button.clicked.connect(self.clear_form)
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        
        # 契約一覧テーブル
        self.contract_table = QTableWidget()
        self.contract_table.setColumnCount(8)
        self.contract_table.setHorizontalHeaderLabels(["ID", "部屋", "契約者名", "入居開始日", "契約終了日", "賃料", "管理費", "保険"])
        
        layout.addWidget(form_group)
        layout.addLayout(button_layout)
        layout.addWidget(QLabel("契約一覧"))
        layout.addWidget(self.contract_table)
        
        self.setLayout(layout)
        self.load_combo_data()
    
    def load_combo_data(self):
        try:
            # 部屋コンボボックス
            self.load_units()
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"コンボボックスデータの読み込み中にエラーが発生しました: {str(e)}")
    
    def load_units(self):
        """部屋一覧をコンボボックスに読み込み"""
        self.unit_combo.clear()
        self.unit_combo.addItem("部屋を選択", None)
        
        # 全物件の部屋を取得
        properties = Property.get_all()
        for property_data in properties:
            units = Unit.get_by_property(property_data['id'])
            for unit in units:
                display_text = f"{property_data['name']} - {unit['room_number']}"
                self.unit_combo.addItem(display_text, unit['id'])
    
    def add_contract(self):
        unit_id = self.unit_combo.currentData()
        contractor_name = self.contractor_name_edit.text().strip()
        
        if not unit_id:
            QMessageBox.warning(self, "警告", "部屋を選択してください。")
            return
        
        if not contractor_name:
            QMessageBox.warning(self, "警告", "契約者名を入力してください。")
            return
        
        try:
            TenantContract.create(
                unit_id=unit_id,
                contractor_name=contractor_name,
                start_date=self.start_date_edit.date().toString("yyyy-MM-dd"),
                end_date=self.end_date_edit.date().toString("yyyy-MM-dd"),
                rent=self.rent_spin.value() if self.rent_spin.value() > 0 else None,
                maintenance_fee=self.maintenance_fee_spin.value() if self.maintenance_fee_spin.value() > 0 else None,
                security_deposit=self.security_deposit_spin.value() if self.security_deposit_spin.value() > 0 else None,
                key_money=self.key_money_spin.value() if self.key_money_spin.value() > 0 else None,
                renewal_method=self.renewal_method_edit.text().strip() or None,
                insurance_flag=self.insurance_flag_check.isChecked(),
                memo=self.memo_edit.toPlainText().strip() or None
            )
            
            QMessageBox.information(self, "成功", "契約を登録しました。")
            self.clear_form()
            self.load_contracts()
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"契約登録中にエラーが発生しました: {str(e)}")
    
    def clear_form(self):
        self.unit_combo.setCurrentIndex(0)
        self.contractor_name_edit.clear()
        self.start_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setDate(QDate.currentDate().addYears(2))
        self.rent_spin.setValue(0)
        self.maintenance_fee_spin.setValue(0)
        self.security_deposit_spin.setValue(0)
        self.key_money_spin.setValue(0)
        self.renewal_method_edit.clear()
        self.insurance_flag_check.setChecked(False)
        self.memo_edit.clear()
    
    def load_contracts(self):
        try:
            contracts = TenantContract.get_all()
            
            self.contract_table.setRowCount(len(contracts))
            for i, contract in enumerate(contracts):
                self.contract_table.setItem(i, 0, QTableWidgetItem(str(contract['id'])))
                self.contract_table.setItem(i, 1, QTableWidgetItem(f"{contract['property_name']} {contract['room_number']}" if contract['property_name'] else ""))
                self.contract_table.setItem(i, 2, QTableWidgetItem(contract['contractor_name'] or ""))
                self.contract_table.setItem(i, 3, QTableWidgetItem(str(contract['start_date']) if contract['start_date'] else ""))
                self.contract_table.setItem(i, 4, QTableWidgetItem(str(contract['end_date']) if contract['end_date'] else ""))
                self.contract_table.setItem(i, 5, QTableWidgetItem(str(contract['rent']) if contract['rent'] else ""))
                self.contract_table.setItem(i, 6, QTableWidgetItem(str(contract['maintenance_fee']) if contract['maintenance_fee'] else ""))
                self.contract_table.setItem(i, 7, QTableWidgetItem("○" if contract['insurance_flag'] else "×"))
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"契約一覧の読み込み中にエラーが発生しました: {str(e)}") 