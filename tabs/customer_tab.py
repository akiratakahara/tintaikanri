from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QLineEdit, 
                             QTextEdit, QMessageBox, QGroupBox, QFormLayout, 
                             QComboBox, QDateEdit, QSpinBox, QDialog, QDialogButtonBox, QTabWidget)
from PyQt6.QtCore import Qt, QDate
import sys
import os

# プロジェクトルートをPythonパスに追加（tabsフォルダ内のモジュールがルートのモジュールにアクセスできるように）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Customer, OwnerProfile, TenantProfile, Property, Unit

class CustomerTab(QWidget):
    """顧客管理タブ"""
    
    def __init__(self):
        super().__init__()
        self.current_customer_id = None
        self.init_ui()
        self.load_customers()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        
        # 顧客管理タブ
        self.customer_management_tab = self.create_customer_management_tab()
        self.tab_widget.addTab(self.customer_management_tab, "顧客管理")
        
        # 所有物件管理タブ（オーナー専用）
        self.property_management_tab = self.create_property_management_tab()
        self.tab_widget.addTab(self.property_management_tab, "所有物件管理")
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
    
    def create_customer_management_tab(self):
        """顧客管理タブを作成"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 顧客登録フォーム
        form_group = QGroupBox("顧客登録")
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.customer_type_combo = QComboBox()
        self.customer_type_combo.addItems(["テナント", "オーナー"])
        self.phone_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.address_edit = QTextEdit()
        self.address_edit.setMaximumHeight(80)
        self.memo_edit = QTextEdit()
        self.memo_edit.setMaximumHeight(60)
        
        form_layout.addRow("顧客名:", self.name_edit)
        form_layout.addRow("顧客種別:", self.customer_type_combo)
        form_layout.addRow("電話番号:", self.phone_edit)
        form_layout.addRow("メールアドレス:", self.email_edit)
        form_layout.addRow("住所:", self.address_edit)
        form_layout.addRow("メモ:", self.memo_edit)
        
        form_group.setLayout(form_layout)
        
        # ボタン
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("顧客登録")
        self.add_button.clicked.connect(self.add_customer)
        self.update_button = QPushButton("更新")
        self.update_button.clicked.connect(self.update_customer)
        self.clear_button = QPushButton("クリア")
        self.clear_button.clicked.connect(self.clear_form)
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        
        # 顧客一覧テーブル
        self.customer_table = QTableWidget()
        self.customer_table.setColumnCount(6)
        self.customer_table.setHorizontalHeaderLabels(["ID", "顧客名", "種別", "電話番号", "メールアドレス", "住所"])
        self.customer_table.cellClicked.connect(self.on_customer_selected)
        
        layout.addWidget(form_group)
        layout.addLayout(button_layout)
        layout.addWidget(QLabel("顧客一覧"))
        layout.addWidget(self.customer_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_property_management_tab(self):
        """所有物件管理タブを作成"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 顧客選択
        customer_select_group = QGroupBox("顧客選択")
        customer_select_layout = QHBoxLayout()
        
        self.selected_customer_label = QLabel("選択されていません")
        customer_select_layout.addWidget(QLabel("選択中の顧客:"))
        customer_select_layout.addWidget(self.selected_customer_label)
        customer_select_layout.addStretch()
        
        customer_select_group.setLayout(customer_select_layout)
        
        # 物件追加セクション
        add_property_group = QGroupBox("物件追加")
        add_property_layout = QVBoxLayout()
        
        # 物件選択
        property_select_layout = QHBoxLayout()
        self.property_combo = QComboBox()
        self.load_property_combo()
        self.add_property_button = QPushButton("物件を追加")
        self.add_property_button.clicked.connect(self.add_property_to_owner)
        
        property_select_layout.addWidget(QLabel("物件選択:"))
        property_select_layout.addWidget(self.property_combo, 1)
        property_select_layout.addWidget(self.add_property_button)
        
        add_property_layout.addLayout(property_select_layout)
        add_property_group.setLayout(add_property_layout)
        
        # 所有物件一覧
        owned_properties_group = QGroupBox("所有物件一覧")
        owned_properties_layout = QVBoxLayout()
        
        self.owned_properties_table = QTableWidget()
        self.owned_properties_table.setColumnCount(6)
        self.owned_properties_table.setHorizontalHeaderLabels([
            "物件名", "住所", "所有比率(%)", "主要", "開始日", "操作"
        ])
        self.owned_properties_table.setMaximumHeight(200)
        
        owned_properties_layout.addWidget(self.owned_properties_table)
        owned_properties_group.setLayout(owned_properties_layout)
        
        # 所有部屋一覧
        owned_units_group = QGroupBox("所有部屋一覧（区分所有）")
        owned_units_layout = QVBoxLayout()
        
        self.owned_units_table = QTableWidget()
        self.owned_units_table.setColumnCount(7)
        self.owned_units_table.setHorizontalHeaderLabels([
            "物件名", "部屋番号", "階数", "面積", "所有比率(%)", "主要", "操作"
        ])
        self.owned_units_table.setMaximumHeight(200)
        
        owned_units_layout.addWidget(self.owned_units_table)
        owned_units_group.setLayout(owned_units_layout)
        
        layout.addWidget(customer_select_group)
        layout.addWidget(add_property_group)
        layout.addWidget(owned_properties_group)
        layout.addWidget(owned_units_group)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def add_customer(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "顧客名を入力してください。")
            return
        
        try:
            # 顧客種別をマッピング
            customer_type_map = {"テナント": "tenant", "オーナー": "owner"}
            customer_type = customer_type_map.get(self.customer_type_combo.currentText(), "tenant")
            
            customer_id = Customer.create(
                name=name,
                customer_type=customer_type,
                phone=self.phone_edit.text().strip(),
                email=self.email_edit.text().strip(),
                address=self.address_edit.toPlainText().strip(),
                memo=self.memo_edit.toPlainText().strip()
            )
            
            # プロフィールを作成
            if customer_type == "owner":
                OwnerProfile.create(customer_id=customer_id)
            else:
                TenantProfile.create(customer_id=customer_id)
            
            QMessageBox.information(self, "成功", "顧客を登録しました。")
            self.clear_form()
            self.load_customers()
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"顧客登録中にエラーが発生しました: {str(e)}")
    
    def clear_form(self):
        self.name_edit.clear()
        self.customer_type_combo.setCurrentIndex(0)
        self.phone_edit.clear()
        self.email_edit.clear()
        self.address_edit.clear()
        self.memo_edit.clear()
    
    def load_customers(self):
        try:
            customers = Customer.get_all()
            
            self.customer_table.setRowCount(len(customers))
            for i, customer in enumerate(customers):
                self.customer_table.setItem(i, 0, QTableWidgetItem(str(customer['id'])))
                self.customer_table.setItem(i, 1, QTableWidgetItem(customer['name']))
                customer_type = "オーナー" if customer['type'] == 'owner' else "テナント"
                self.customer_table.setItem(i, 2, QTableWidgetItem(customer_type))
                self.customer_table.setItem(i, 3, QTableWidgetItem(customer['phone'] or ""))
                self.customer_table.setItem(i, 4, QTableWidgetItem(customer['email'] or ""))
                self.customer_table.setItem(i, 5, QTableWidgetItem(customer['address'] or ""))
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"顧客一覧の読み込み中にエラーが発生しました: {str(e)}")
    
    def on_customer_selected(self, row, column):
        """顧客が選択されたときの処理"""
        try:
            customer_id = int(self.customer_table.item(row, 0).text())
            self.current_customer_id = customer_id
            
            # 顧客情報をフォームに読み込み
            customer = Customer.get_by_id(customer_id)
            if customer:
                self.name_edit.setText(customer.get('name', ''))
                customer_type = "オーナー" if customer.get('type') == 'owner' else "テナント"
                index = self.customer_type_combo.findText(customer_type)
                if index >= 0:
                    self.customer_type_combo.setCurrentIndex(index)
                self.phone_edit.setText(customer.get('phone', ''))
                self.email_edit.setText(customer.get('email', ''))
                self.address_edit.setPlainText(customer.get('address', ''))
                self.memo_edit.setPlainText(customer.get('memo', ''))
                
                # 選択されたオーナーの情報を所有物件管理タブに表示
                if customer.get('type') == 'owner':
                    self.selected_customer_label.setText(f"{customer['name']} (ID: {customer_id})")
                    self.load_owned_properties()
                    self.load_owned_units()
                else:
                    self.selected_customer_label.setText("選択された顧客はテナントです")
                    self.owned_properties_table.setRowCount(0)
                    self.owned_units_table.setRowCount(0)
                
        except Exception as e:
            print(f"顧客選択エラー: {str(e)}")
    
    def update_customer(self):
        """顧客情報を更新"""
        if not self.current_customer_id:
            QMessageBox.warning(self, "警告", "更新する顧客を選択してください")
            return
        
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "顧客名を入力してください")
            return
        
        try:
            customer_type_map = {"テナント": "tenant", "オーナー": "owner"}
            customer_type = customer_type_map.get(self.customer_type_combo.currentText(), "tenant")
            
            Customer.update(
                customer_id=self.current_customer_id,
                name=name,
                customer_type=customer_type,
                phone=self.phone_edit.text().strip(),
                email=self.email_edit.text().strip(),
                address=self.address_edit.toPlainText().strip(),
                memo=self.memo_edit.toPlainText().strip()
            )
            
            QMessageBox.information(self, "成功", "顧客情報を更新しました")
            self.load_customers()
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"顧客情報更新中にエラーが発生しました: {str(e)}")
    
    def load_property_combo(self):
        """物件コンボボックスを読み込み"""
        try:
            properties = Property.get_all()
            self.property_combo.clear()
            for prop in properties:
                self.property_combo.addItem(f"{prop['name']} - {prop['address']}", prop['id'])
        except Exception as e:
            print(f"物件一覧読み込みエラー: {str(e)}")
    
    def add_property_to_owner(self):
        """オーナーに物件を追加"""
        if not self.current_customer_id:
            QMessageBox.warning(self, "警告", "オーナーを選択してください")
            return
        
        # 顧客がオーナーかチェック
        customer = Customer.get_by_id(self.current_customer_id)
        if not customer or customer.get('type') != 'owner':
            QMessageBox.warning(self, "警告", "選択された顧客はオーナーではありません")
            return
        
        property_id = self.property_combo.currentData()
        if not property_id:
            QMessageBox.warning(self, "警告", "物件を選択してください")
            return
        
        # 所有比率を入力
        ratio, ok = QInputDialog.getDouble(
            self, "所有比率", "所有比率(%)を入力:", 100.0, 0.0, 100.0, 2
        )
        if not ok:
            return
        
        try:
            Property.add_owner(property_id, self.current_customer_id, ratio, is_primary=(ratio >= 50))
            self.load_owned_properties()
            QMessageBox.information(self, "成功", "物件を追加しました")
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"物件追加中にエラーが発生しました: {str(e)}")
    
    def load_owned_properties(self):
        """オーナーの所有物件一覧を読み込み"""
        if not self.current_customer_id:
            self.owned_properties_table.setRowCount(0)
            return
        
        try:
            # 全物件から該当オーナーの所有物件を検索
            all_properties = Property.get_all()
            owned_properties = []
            
            for prop in all_properties:
                owners = Property.get_owners(prop['id'])
                for owner in owners:
                    if owner['owner_id'] == self.current_customer_id:
                        prop_data = prop.copy()
                        prop_data.update(owner)
                        owned_properties.append(prop_data)
                        break
            
            self.owned_properties_table.setRowCount(len(owned_properties))
            
            for row, prop in enumerate(owned_properties):
                self.owned_properties_table.setItem(row, 0, QTableWidgetItem(prop.get('name', '')))
                self.owned_properties_table.setItem(row, 1, QTableWidgetItem(prop.get('address', '')))
                self.owned_properties_table.setItem(row, 2, QTableWidgetItem(f"{prop.get('ownership_ratio', 0):.1f}"))
                self.owned_properties_table.setItem(row, 3, QTableWidgetItem("主要" if prop.get('is_primary') else ""))
                self.owned_properties_table.setItem(row, 4, QTableWidgetItem(prop.get('start_date', '')))
                
                # 削除ボタン
                delete_button = QPushButton("削除")
                delete_button.clicked.connect(
                    lambda checked, pid=prop['id']: self.remove_property_from_owner(pid)
                )
                self.owned_properties_table.setCellWidget(row, 5, delete_button)
                
        except Exception as e:
            print(f"所有物件読み込みエラー: {str(e)}")
    
    def load_owned_units(self):
        """オーナーの所有部屋一覧を読み込み（区分所有）"""
        if not self.current_customer_id:
            self.owned_units_table.setRowCount(0)
            return
        
        try:
            # 全部屋から該当オーナーの所有部屋を検索
            all_units = Unit.get_all()
            owned_units = []
            
            for unit in all_units:
                owners = Unit.get_owners(unit['id'])
                for owner in owners:
                    if owner['owner_id'] == self.current_customer_id:
                        unit_data = unit.copy()
                        unit_data.update(owner)
                        # 物件名を取得
                        prop = Property.get_by_id(unit['property_id'])
                        unit_data['property_name'] = prop['name'] if prop else ''
                        owned_units.append(unit_data)
                        break
            
            self.owned_units_table.setRowCount(len(owned_units))
            
            for row, unit in enumerate(owned_units):
                self.owned_units_table.setItem(row, 0, QTableWidgetItem(unit.get('property_name', '')))
                self.owned_units_table.setItem(row, 1, QTableWidgetItem(unit.get('room_number', '')))
                self.owned_units_table.setItem(row, 2, QTableWidgetItem(str(unit.get('floor', ''))))
                self.owned_units_table.setItem(row, 3, QTableWidgetItem(f"{unit.get('area', 0)}㎡" if unit.get('area') else ''))
                self.owned_units_table.setItem(row, 4, QTableWidgetItem(f"{unit.get('ownership_ratio', 0):.1f}"))
                self.owned_units_table.setItem(row, 5, QTableWidgetItem("主要" if unit.get('is_primary') else ""))
                
                # 削除ボタン
                delete_button = QPushButton("削除")
                delete_button.clicked.connect(
                    lambda checked, uid=unit['id']: self.remove_unit_from_owner(uid)
                )
                self.owned_units_table.setCellWidget(row, 6, delete_button)
                
        except Exception as e:
            print(f"所有部屋読み込みエラー: {str(e)}")
    
    def remove_property_from_owner(self, property_id):
        """オーナーから物件を削除"""
        if not self.current_customer_id:
            return
        
        reply = QMessageBox.question(self, "確認", "この物件をオーナーから削除しますか？")
        if reply == QMessageBox.StandardButton.Yes:
            try:
                Property.remove_owner(property_id, self.current_customer_id)
                self.load_owned_properties()
                QMessageBox.information(self, "成功", "物件を削除しました")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"物件削除中にエラーが発生しました: {str(e)}")
    
    def remove_unit_from_owner(self, unit_id):
        """オーナーから部屋を削除"""
        if not self.current_customer_id:
            return
        
        reply = QMessageBox.question(self, "確認", "この部屋をオーナーから削除しますか？")
        if reply == QMessageBox.StandardButton.Yes:
            try:
                Unit.remove_owner(unit_id, self.current_customer_id)
                self.load_owned_units()
                QMessageBox.information(self, "成功", "部屋を削除しました")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"部屋削除中にエラーが発生しました: {str(e)}") 