#!/usr/bin/env python3
"""
改善された物件管理タブ - より使いやすい登録フロー
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QLineEdit, 
                             QTextEdit, QMessageBox, QGroupBox, QFormLayout, 
                             QSpinBox, QComboBox, QSplitter, QFrame,
                             QDialog, QDialogButtonBox, QTabWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from models import Property, Customer
from PyQt6.QtWidgets import QInputDialog

class PropertyTabImproved(QWidget):
    """改善された物件管理タブ"""
    
    def __init__(self):
        super().__init__()
        self.current_property_id = None
        self.init_ui()
        self.load_properties()
        self.load_owner_customers()
    
    def init_ui(self):
        """UIを初期化"""
        # メインレイアウト（水平分割）
        main_layout = QHBoxLayout()
        
        # スプリッターを使用して左右に分割
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左側：物件一覧
        left_widget = self.create_property_list_widget()
        left_widget.setMaximumWidth(400)
        splitter.addWidget(left_widget)
        
        # 右側：物件詳細・編集
        right_widget = self.create_property_detail_widget()
        splitter.addWidget(right_widget)
        
        # スプリッターの比率設定
        splitter.setSizes([400, 600])
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
    
    def create_property_list_widget(self):
        """物件一覧ウィジェットを作成"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # ヘッダー
        header_layout = QHBoxLayout()
        title_label = QLabel("物件一覧")
        title_label.setFont(QFont("", 14, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # 新規物件追加ボタン
        self.add_property_button = QPushButton("+ 新規物件")
        self.add_property_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.add_property_button.clicked.connect(self.show_add_property_dialog)
        header_layout.addWidget(self.add_property_button)
        
        layout.addLayout(header_layout)
        
        # 物件一覧テーブル
        self.property_list_table = QTableWidget()
        self.property_list_table.setColumnCount(3)
        self.property_list_table.setHorizontalHeaderLabels(["物件名", "住所", "オーナー数"])
        self.property_list_table.horizontalHeader().setStretchLastSection(True)
        self.property_list_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.property_list_table.cellClicked.connect(self.on_property_selected)
        
        layout.addWidget(self.property_list_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_property_detail_widget(self):
        """物件詳細ウィジェットを作成"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # ヘッダー
        self.detail_header = QLabel("物件を選択してください")
        self.detail_header.setFont(QFont("", 14, QFont.Weight.Bold))
        self.detail_header.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(self.detail_header)
        
        # タブウィジェット
        self.detail_tabs = QTabWidget()
        
        # 基本情報タブ
        self.basic_info_tab = self.create_basic_info_tab()
        self.detail_tabs.addTab(self.basic_info_tab, "基本情報")
        
        # オーナー管理タブ
        self.owner_management_tab = self.create_owner_management_tab()
        self.detail_tabs.addTab(self.owner_management_tab, "オーナー管理")
        
        layout.addWidget(self.detail_tabs)
        
        # ボタンエリア
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_button = QPushButton("変更を保存")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        self.save_button.clicked.connect(self.save_property_changes)
        self.save_button.setEnabled(False)
        
        self.delete_button = QPushButton("物件を削除")
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        self.delete_button.clicked.connect(self.delete_property)
        self.delete_button.setEnabled(False)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.delete_button)
        
        layout.addLayout(button_layout)
        
        widget.setLayout(layout)
        return widget
    
    def create_basic_info_tab(self):
        """基本情報タブを作成"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 基本情報フォーム
        form_group = QGroupBox("物件基本情報")
        form_layout = QFormLayout()
        
        self.property_name_edit = QLineEdit()
        self.address_edit = QTextEdit()
        self.address_edit.setMaximumHeight(80)
        self.structure_edit = QLineEdit()
        self.registry_owner_edit = QLineEdit()
        
        form_layout.addRow("物件名 *:", self.property_name_edit)
        form_layout.addRow("住所 *:", self.address_edit)
        form_layout.addRow("構造:", self.structure_edit)
        form_layout.addRow("登記所有者:", self.registry_owner_edit)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # 運用情報フォーム
        operation_group = QGroupBox("運用情報")
        operation_layout = QFormLayout()
        
        self.management_type_combo = QComboBox()
        self.management_type_combo.addItems(["自社管理", "他社仲介", "共同管理"])
        
        self.management_company_edit = QLineEdit()
        self.available_rooms_spin = QSpinBox()
        self.available_rooms_spin.setRange(0, 999)
        self.renewal_rooms_spin = QSpinBox()
        self.renewal_rooms_spin.setRange(0, 999)
        
        operation_layout.addRow("管理形態:", self.management_type_combo)
        operation_layout.addRow("管理会社:", self.management_company_edit)
        operation_layout.addRow("募集中部屋数:", self.available_rooms_spin)
        operation_layout.addRow("更新予定部屋数:", self.renewal_rooms_spin)
        
        operation_group.setLayout(operation_layout)
        layout.addWidget(operation_group)
        
        # 備考
        notes_group = QGroupBox("備考")
        notes_layout = QVBoxLayout()
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        notes_layout.addWidget(self.notes_edit)
        
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_owner_management_tab(self):
        """オーナー管理タブを作成"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # オーナー追加セクション
        add_section = QGroupBox("オーナー追加")
        add_layout = QHBoxLayout()
        
        self.owner_combo = QComboBox()
        self.owner_combo.setMinimumWidth(200)
        
        self.add_owner_btn = QPushButton("追加")
        self.add_owner_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.add_owner_btn.clicked.connect(self.add_owner_to_property)
        
        self.new_owner_btn = QPushButton("新規オーナー登録")
        self.new_owner_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        self.new_owner_btn.clicked.connect(self.show_new_owner_dialog)
        
        add_layout.addWidget(QLabel("オーナー選択:"))
        add_layout.addWidget(self.owner_combo, 1)
        add_layout.addWidget(self.add_owner_btn)
        add_layout.addWidget(self.new_owner_btn)
        
        add_section.setLayout(add_layout)
        layout.addWidget(add_section)
        
        # オーナー一覧セクション
        list_section = QGroupBox("現在のオーナー")
        list_layout = QVBoxLayout()
        
        self.owner_table = QTableWidget()
        self.owner_table.setColumnCount(5)
        self.owner_table.setHorizontalHeaderLabels([
            "オーナー名", "所有比率(%)", "主要", "連絡先", "操作"
        ])
        self.owner_table.horizontalHeader().setStretchLastSection(True)
        
        list_layout.addWidget(self.owner_table)
        list_section.setLayout(list_layout)
        layout.addWidget(list_section)
        
        widget.setLayout(layout)
        return widget
    
    def show_add_property_dialog(self):
        """新規物件追加ダイアログを表示"""
        dialog = QDialog(self)
        dialog.setWindowTitle("新規物件登録")
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout()
        
        # フォーム
        form_layout = QFormLayout()
        
        name_edit = QLineEdit()
        address_edit = QTextEdit()
        address_edit.setMaximumHeight(80)
        structure_edit = QLineEdit()
        
        form_layout.addRow("物件名 *:", name_edit)
        form_layout.addRow("住所 *:", address_edit)
        form_layout.addRow("構造:", structure_edit)
        
        layout.addLayout(form_layout)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        ok_button = QPushButton("登録")
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        
        cancel_button = QPushButton("キャンセル")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #666;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
            }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        # イベント接続
        def create_property():
            name = name_edit.text().strip()
            address = address_edit.toPlainText().strip()
            
            if not name or not address:
                QMessageBox.warning(dialog, "入力エラー", "物件名と住所は必須です")
                return
            
            try:
                property_id = Property.create(
                    name=name,
                    address=address,
                    structure=structure_edit.text().strip()
                )
                
                QMessageBox.information(dialog, "成功", "物件を登録しました")
                dialog.accept()
                self.load_properties()
                
                # 新しく作成した物件を選択
                for row in range(self.property_list_table.rowCount()):
                    if int(self.property_list_table.item(row, 0).data(Qt.ItemDataRole.UserRole)) == property_id:
                        self.property_list_table.selectRow(row)
                        self.on_property_selected(row, 0)
                        break
                        
            except Exception as e:
                QMessageBox.critical(dialog, "エラー", f"物件登録に失敗しました: {str(e)}")
        
        ok_button.clicked.connect(create_property)
        cancel_button.clicked.connect(dialog.reject)
        
        dialog.exec()
    
    def show_new_owner_dialog(self):
        """新規オーナー登録ダイアログを表示"""
        dialog = QDialog(self)
        dialog.setWindowTitle("新規オーナー登録")
        dialog.setMinimumSize(400, 300)
        
        layout = QFormLayout()
        
        name_edit = QLineEdit()
        phone_edit = QLineEdit()
        email_edit = QLineEdit()
        address_edit = QTextEdit()
        address_edit.setMaximumHeight(80)
        
        layout.addRow("オーナー名 *:", name_edit)
        layout.addRow("電話番号:", phone_edit)
        layout.addRow("メールアドレス:", email_edit)
        layout.addRow("住所:", address_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        def create_owner():
            name = name_edit.text().strip()
            if not name:
                QMessageBox.warning(dialog, "入力エラー", "オーナー名は必須です")
                return
            
            try:
                Customer.create(
                    name=name,
                    customer_type='owner',
                    phone=phone_edit.text().strip(),
                    email=email_edit.text().strip(),
                    address=address_edit.toPlainText().strip()
                )
                
                QMessageBox.information(dialog, "成功", "オーナーを登録しました")
                dialog.accept()
                self.load_owner_customers()
                
            except Exception as e:
                QMessageBox.critical(dialog, "エラー", f"オーナー登録に失敗しました: {str(e)}")
        
        buttons.accepted.connect(create_owner)
        buttons.rejected.connect(dialog.reject)
        
        dialog.exec()
    
    def load_properties(self):
        """物件一覧を読み込み"""
        try:
            properties = Property.get_all()
            self.property_list_table.setRowCount(len(properties))
            
            for row, prop in enumerate(properties):
                # 物件名
                name_item = QTableWidgetItem(prop.get('name', ''))
                name_item.setData(Qt.ItemDataRole.UserRole, prop['id'])
                self.property_list_table.setItem(row, 0, name_item)
                
                # 住所
                self.property_list_table.setItem(row, 1, QTableWidgetItem(prop.get('address', '')))
                
                # オーナー数
                owners = Property.get_owners(prop['id'])
                self.property_list_table.setItem(row, 2, QTableWidgetItem(f"{len(owners)}人"))
                
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"物件一覧の読み込みに失敗しました: {str(e)}")
    
    def load_owner_customers(self):
        """オーナー顧客一覧を読み込み"""
        try:
            customers = Customer.get_all()
            owners = [c for c in customers if c.get('type') == 'owner']
            
            self.owner_combo.clear()
            self.owner_combo.addItem("選択してください", None)
            
            for owner in owners:
                self.owner_combo.addItem(f"{owner['name']} (ID: {owner['id']})", owner['id'])
                
        except Exception as e:
            print(f"オーナー一覧読み込みエラー: {str(e)}")
    
    def on_property_selected(self, row, column):
        """物件が選択されたときの処理"""
        try:
            item = self.property_list_table.item(row, 0)
            if not item:
                return
                
            property_id = item.data(Qt.ItemDataRole.UserRole)
            self.current_property_id = property_id
            
            # 物件情報を読み込み
            property_data = Property.get_by_id(property_id)
            if not property_data:
                return
            
            # ヘッダー更新
            self.detail_header.setText(f"物件詳細: {property_data.get('name', '')}")
            self.detail_header.setStyleSheet("color: #333; padding: 10px; font-weight: bold;")
            
            # フォームに情報を設定
            self.property_name_edit.setText(property_data.get('name', ''))
            self.address_edit.setPlainText(property_data.get('address', ''))
            self.structure_edit.setText(property_data.get('structure', ''))
            self.registry_owner_edit.setText(property_data.get('registry_owner', ''))
            self.notes_edit.setPlainText(property_data.get('notes', ''))
            
            # 運用情報
            management_type = property_data.get('management_type', '自社管理')
            index = self.management_type_combo.findText(management_type)
            if index >= 0:
                self.management_type_combo.setCurrentIndex(index)
            
            self.management_company_edit.setText(property_data.get('management_company', ''))
            self.available_rooms_spin.setValue(property_data.get('available_rooms', 0))
            self.renewal_rooms_spin.setValue(property_data.get('renewal_rooms', 0))
            
            # オーナー情報を読み込み
            self.load_property_owners()
            
            # ボタンを有効化
            self.save_button.setEnabled(True)
            self.delete_button.setEnabled(True)
            
        except Exception as e:
            print(f"物件選択エラー: {str(e)}")
    
    def load_property_owners(self):
        """物件のオーナー一覧を読み込み"""
        if not self.current_property_id:
            self.owner_table.setRowCount(0)
            return
        
        try:
            owners = Property.get_owners(self.current_property_id)
            self.owner_table.setRowCount(len(owners))
            
            for row, owner in enumerate(owners):
                self.owner_table.setItem(row, 0, QTableWidgetItem(owner.get('owner_name', '')))
                self.owner_table.setItem(row, 1, QTableWidgetItem(f"{owner.get('ownership_ratio', 0):.1f}"))
                self.owner_table.setItem(row, 2, QTableWidgetItem("●" if owner.get('is_primary') else ""))
                
                contact = f"{owner.get('phone', '')} / {owner.get('email', '')}"
                self.owner_table.setItem(row, 3, QTableWidgetItem(contact))
                
                # 削除ボタン
                delete_button = QPushButton("削除")
                delete_button.setStyleSheet("""
                    QPushButton {
                        background-color: #f44336;
                        color: white;
                        border: none;
                        padding: 4px 8px;
                        border-radius: 2px;
                    }
                """)
                delete_button.clicked.connect(lambda checked, oid=owner['owner_id']: self.remove_owner_from_property(oid))
                self.owner_table.setCellWidget(row, 4, delete_button)
                
        except Exception as e:
            print(f"オーナー一覧読み込みエラー: {str(e)}")
    
    def add_owner_to_property(self):
        """物件にオーナーを追加"""
        if not self.current_property_id:
            QMessageBox.warning(self, "警告", "物件を選択してください")
            return
        
        owner_id = self.owner_combo.currentData()
        if not owner_id:
            QMessageBox.warning(self, "警告", "オーナーを選択してください")
            return
        
        # 所有比率を入力
        ratio, ok = QInputDialog.getDouble(
            self, "所有比率", "所有比率(%)を入力:", 100.0, 0.0, 100.0, 2
        )
        if not ok:
            return
        
        try:
            Property.add_owner(self.current_property_id, owner_id, ratio, is_primary=(ratio >= 50))
            self.load_property_owners()
            self.load_properties()  # オーナー数を更新
            QMessageBox.information(self, "成功", "オーナーを追加しました")
            
            # コンボボックスをリセット
            self.owner_combo.setCurrentIndex(0)
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"オーナー追加中にエラーが発生しました: {str(e)}")
    
    def remove_owner_from_property(self, owner_id):
        """物件からオーナーを削除"""
        if not self.current_property_id:
            return
        
        reply = QMessageBox.question(self, "確認", "このオーナーを物件から削除しますか？")
        if reply == QMessageBox.StandardButton.Yes:
            try:
                Property.remove_owner(self.current_property_id, owner_id)
                self.load_property_owners()
                self.load_properties()  # オーナー数を更新
                QMessageBox.information(self, "成功", "オーナーを削除しました")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"オーナー削除中にエラーが発生しました: {str(e)}")
    
    def save_property_changes(self):
        """物件情報の変更を保存"""
        if not self.current_property_id:
            return
        
        name = self.property_name_edit.text().strip()
        address = self.address_edit.toPlainText().strip()
        
        if not name or not address:
            QMessageBox.warning(self, "入力エラー", "物件名と住所は必須です")
            return
        
        try:
            Property.update(
                property_id=self.current_property_id,
                name=name,
                address=address,
                structure=self.structure_edit.text().strip(),
                registry_owner=self.registry_owner_edit.text().strip(),
                management_type=self.management_type_combo.currentText(),
                management_company=self.management_company_edit.text().strip(),
                available_rooms=self.available_rooms_spin.value(),
                renewal_rooms=self.renewal_rooms_spin.value(),
                notes=self.notes_edit.toPlainText().strip()
            )
            
            QMessageBox.information(self, "成功", "物件情報を更新しました")
            self.load_properties()
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"物件情報の更新に失敗しました: {str(e)}")
    
    def delete_property(self):
        """物件を削除"""
        if not self.current_property_id:
            return
        
        reply = QMessageBox.question(
            self, "確認", 
            "この物件を削除しますか？\n関連するオーナー情報、部屋情報も削除されます。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                Property.delete(self.current_property_id)
                QMessageBox.information(self, "成功", "物件を削除しました")
                
                # UIをリセット
                self.current_property_id = None
                self.detail_header.setText("物件を選択してください")
                self.detail_header.setStyleSheet("color: #666; padding: 10px;")
                self.save_button.setEnabled(False)
                self.delete_button.setEnabled(False)
                
                # フォームをクリア
                self.clear_form()
                self.load_properties()
                
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"物件削除に失敗しました: {str(e)}")
    
    def clear_form(self):
        """フォームをクリア"""
        self.property_name_edit.clear()
        self.address_edit.clear()
        self.structure_edit.clear()
        self.registry_owner_edit.clear()
        self.notes_edit.clear()
        self.management_type_combo.setCurrentIndex(0)
        self.management_company_edit.clear()
        self.available_rooms_spin.setValue(0)
        self.renewal_rooms_spin.setValue(0)
        self.owner_table.setRowCount(0)