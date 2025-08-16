"""
物件管理タブ - 基本版（OCR機能なし）
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QLineEdit, 
                             QTextEdit, QMessageBox, QGroupBox, QFormLayout, 
                             QComboBox, QSpinBox, QDialog, QDialogButtonBox,
                             QSplitter, QFrame, QScrollArea, QDateEdit, QCheckBox,
                             QDoubleSpinBox, QHeaderView)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QColor
from models import Property, Customer, Unit
from utils import (Validator, TableHelper, MessageHelper, FormatHelper, 
                  SearchHelper, DateHelper)

class UnitEditDialog(QDialog):
    """部屋編集ダイアログ"""
    
    def __init__(self, parent=None, property_id=None, unit_data=None):
        super().__init__(parent)
        self.property_id = property_id
        self.unit_data = unit_data
        self.init_ui()
        if unit_data:
            self.load_unit_data()
    
    def init_ui(self):
        self.setWindowTitle("部屋編集" if self.unit_data else "部屋新規登録")
        self.setModal(True)
        self.resize(500, 600)
        
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 基本情報グループ
        basic_group = QGroupBox("🚪 部屋基本情報")
        basic_layout = QFormLayout()
        basic_layout.setSpacing(12)
        basic_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        basic_layout.setHorizontalSpacing(16)
        
        self.room_number_edit = QLineEdit()
        self.room_number_edit.setPlaceholderText("例: 101, A-201")
        self.room_number_edit.setMinimumHeight(32)
        
        self.floor_edit = QLineEdit()
        self.floor_edit.setPlaceholderText("例: 1F, 2階")
        self.floor_edit.setMinimumHeight(32)
        
        self.area_spin = QDoubleSpinBox()
        self.area_spin.setRange(0.0, 1000.0)
        self.area_spin.setDecimals(2)
        self.area_spin.setSuffix(" m²")
        self.area_spin.setMinimumHeight(32)
        
        basic_layout.addRow("部屋番号 *:", self.room_number_edit)
        basic_layout.addRow("階数:", self.floor_edit)
        basic_layout.addRow("面積:", self.area_spin)
        
        basic_group.setLayout(basic_layout)
        
        # 設備・条件グループ
        facilities_group = QGroupBox("⚙️ 設備・使用条件")
        facilities_layout = QFormLayout()
        facilities_layout.setSpacing(12)
        facilities_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        facilities_layout.setHorizontalSpacing(16)
        
        self.power_capacity_edit = QLineEdit()
        self.power_capacity_edit.setPlaceholderText("例: 30A, 60A")
        self.power_capacity_edit.setMinimumHeight(32)
        
        # チェックボックス
        self.pet_allowed_check = QCheckBox("ペット飼育可")
        self.midnight_allowed_check = QCheckBox("深夜利用可")
        
        self.use_restrictions_edit = QTextEdit()
        self.use_restrictions_edit.setMaximumHeight(80)
        self.use_restrictions_edit.setPlaceholderText("使用制限事項を入力...")
        
        facilities_layout.addRow("電力容量:", self.power_capacity_edit)
        facilities_layout.addRow("", self.pet_allowed_check)
        facilities_layout.addRow("", self.midnight_allowed_check)
        facilities_layout.addRow("使用制限:", self.use_restrictions_edit)
        
        facilities_group.setLayout(facilities_layout)
        
        # 備考グループ
        notes_group = QGroupBox("📝 備考・特記事項")
        notes_layout = QVBoxLayout()
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        self.notes_edit.setPlaceholderText("備考事項を入力...")
        
        notes_layout.addWidget(self.notes_edit)
        notes_group.setLayout(notes_layout)
        
        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # レイアウトに追加
        layout.addWidget(basic_group)
        layout.addWidget(facilities_group)
        layout.addWidget(notes_group)
        layout.addStretch()
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def load_unit_data(self):
        """部屋データを読み込み"""
        if not self.unit_data:
            return
        
        self.room_number_edit.setText(self.unit_data.get('room_number', ''))
        self.floor_edit.setText(self.unit_data.get('floor', ''))
        
        area = self.unit_data.get('area')
        if area is not None:
            self.area_spin.setValue(float(area))
        
        self.power_capacity_edit.setText(self.unit_data.get('power_capacity', ''))
        self.pet_allowed_check.setChecked(bool(self.unit_data.get('pet_allowed', False)))
        self.midnight_allowed_check.setChecked(bool(self.unit_data.get('midnight_allowed', False)))
        self.use_restrictions_edit.setPlainText(self.unit_data.get('use_restrictions', ''))
        self.notes_edit.setPlainText(self.unit_data.get('notes', ''))
    
    def get_unit_data(self):
        """入力されたデータを取得"""
        return {
            'room_number': self.room_number_edit.text().strip(),
            'floor': self.floor_edit.text().strip() or None,
            'area': self.area_spin.value() if self.area_spin.value() > 0 else None,
            'power_capacity': self.power_capacity_edit.text().strip() or None,
            'pet_allowed': self.pet_allowed_check.isChecked(),
            'midnight_allowed': self.midnight_allowed_check.isChecked(),
            'use_restrictions': self.use_restrictions_edit.toPlainText().strip() or None,
            'notes': self.notes_edit.toPlainText().strip() or None
        }
    
    def accept(self):
        """バリデーションと保存"""
        data = self.get_unit_data()
        
        if not data['room_number']:
            MessageHelper.show_warning(self, "部屋番号は必須です")
            self.room_number_edit.setFocus()
            return
        
        super().accept()

class PropertyEditDialog(QDialog):
    """物件編集ダイアログ"""
    
    def __init__(self, parent=None, property_data=None):
        super().__init__(parent)
        self.property_data = property_data
        self.init_ui()
        if property_data:
            self.load_property_data()
    
    def init_ui(self):
        self.setWindowTitle("物件情報編集" if self.property_data else "物件新規登録")
        self.setModal(True)
        self.resize(650, 750)  # サイズを大きくして読みやすく
        
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # スクロール可能エリア（最適化版）
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # スクロールバーのスタイルを改善
        from ui_styles import ModernStyles
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            {ModernStyles.get_scroll_bar_style()}
        """)
        
        # スムーススクロールのための設定
        scroll_area.setMouseTracking(True)
        scroll_area.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        
        # メインコンテナーウィジェット
        container_widget = QWidget()
        container_layout = QVBoxLayout(container_widget)
        container_layout.setSpacing(24)
        container_layout.setContentsMargins(16, 16, 16, 16)
        
        # ===========================================
        # 基本情報セクション
        # ===========================================
        basic_info_group = QGroupBox("🏢 基本情報")
        basic_info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #1f2937;
                padding-top: 16px;
            }
            QGroupBox::title {
                left: 10px;
                top: -8px;
            }
        """)
        basic_layout = QFormLayout(basic_info_group)
        basic_layout.setSpacing(12)
        basic_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        # 物件名
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例: ○○マンション")
        self.name_edit.setMinimumHeight(36)
        
        # 住所
        self.address_edit = QTextEdit()
        self.address_edit.setMaximumHeight(80)
        self.address_edit.setMinimumHeight(60)
        self.address_edit.setPlaceholderText("例: 東京都渋谷区○○1-2-3")
        
        basic_layout.addRow("物件名 *:", self.name_edit)
        basic_layout.addRow("住所 *:", self.address_edit)
        
        # ===========================================
        # 建物登記情報セクション
        # ===========================================
        registry_group = QGroupBox("📜 建物登記情報")
        registry_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #1f2937;
                padding-top: 16px;
            }
            QGroupBox::title {
                left: 10px;
                top: -8px;
            }
        """)
        registry_layout = QFormLayout(registry_group)
        registry_layout.setSpacing(12)
        registry_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        # 建物構造
        self.structure_combo = QComboBox()
        self.structure_combo.addItems([
            "RC造", "SRC造", "鉄骨造", "木造", "軽量鉄骨造", "その他"
        ])
        self.structure_combo.setMinimumHeight(36)
        
        # 登記所有者
        self.registry_owner_edit = QLineEdit()
        self.registry_owner_edit.setPlaceholderText("例: 株式会社○○")
        self.registry_owner_edit.setMinimumHeight(36)
        
        # 建築年月日（新規追加）
        self.construction_date_edit = QDateEdit()
        self.construction_date_edit.setDate(QDate.currentDate())
        self.construction_date_edit.setCalendarPopup(True)
        self.construction_date_edit.setMinimumHeight(36)
        self.construction_date_edit.setDisplayFormat("yyyy年MM月dd日")
        
        registry_layout.addRow("建物構造:", self.structure_combo)
        registry_layout.addRow("登記所有者:", self.registry_owner_edit)
        registry_layout.addRow("建築年月日:", self.construction_date_edit)
        
        # ===========================================
        # 管理情報セクション
        # ===========================================
        management_group = QGroupBox("💼 管理情報")
        management_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #1f2937;
                padding-top: 16px;
            }
            QGroupBox::title {
                left: 10px;
                top: -8px;
            }
        """)
        management_layout = QFormLayout(management_group)
        management_layout.setSpacing(12)
        management_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        # 管理形態
        self.management_type_combo = QComboBox()
        self.management_type_combo.addItems([
            "自社管理", "他社仲介", "共同管理"
        ])
        self.management_type_combo.setMinimumHeight(36)
        
        # 管理会社名
        self.management_company_edit = QLineEdit()
        self.management_company_edit.setPlaceholderText("管理会社名（他社管理の場合）")
        self.management_company_edit.setMinimumHeight(36)
        
        # 募集中部屋数
        self.available_rooms_spin = QSpinBox()
        self.available_rooms_spin.setRange(0, 999)
        self.available_rooms_spin.setMinimumHeight(36)
        self.available_rooms_spin.setSuffix(" 室")
        
        # 更新予定部屋数
        self.renewal_rooms_spin = QSpinBox()
        self.renewal_rooms_spin.setRange(0, 999)
        self.renewal_rooms_spin.setMinimumHeight(36)
        self.renewal_rooms_spin.setSuffix(" 室")
        
        management_layout.addRow("管理形態:", self.management_type_combo)
        management_layout.addRow("管理会社名:", self.management_company_edit)
        management_layout.addRow("募集中部屋数:", self.available_rooms_spin)
        management_layout.addRow("更新予定部屋数:", self.renewal_rooms_spin)
        
        # ===========================================
        # 備考セクション
        # ===========================================
        notes_group = QGroupBox("📝 備考")
        notes_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #1f2937;
                padding-top: 16px;
            }
            QGroupBox::title {
                left: 10px;
                top: -8px;
            }
        """)
        notes_layout = QVBoxLayout(notes_group)
        notes_layout.setSpacing(8)
        
        # 備考
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(120)
        self.notes_edit.setMinimumHeight(80)
        self.notes_edit.setPlaceholderText("物件に関する特記事項、注意点などを記入してください")
        notes_layout.addWidget(self.notes_edit)
        
        # ===========================================
        # 部屋管理セクション（編集時のみ表示）
        # ===========================================
        self.rooms_group = QGroupBox("🚪 部屋管理")
        self.rooms_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #1f2937;
                padding-top: 16px;
            }
            QGroupBox::title {
                left: 10px;
                top: -8px;
            }
        """)
        rooms_layout = QVBoxLayout(self.rooms_group)
        rooms_layout.setSpacing(12)
        
        # 部屋管理ボタン
        buttons_layout = QHBoxLayout()
        
        self.add_room_btn = QPushButton("➕ 部屋追加")
        self.add_room_btn.clicked.connect(self.add_room)
        self.add_room_btn.setMinimumHeight(36)
        
        self.edit_room_btn = QPushButton("✏️ 部屋編集")
        self.edit_room_btn.clicked.connect(self.edit_room)
        self.edit_room_btn.setEnabled(False)
        self.edit_room_btn.setMinimumHeight(36)
        
        self.delete_room_btn = QPushButton("🗑️ 部屋削除")
        self.delete_room_btn.clicked.connect(self.delete_room)
        self.delete_room_btn.setEnabled(False)
        self.delete_room_btn.setMinimumHeight(36)
        
        buttons_layout.addWidget(self.add_room_btn)
        buttons_layout.addWidget(self.edit_room_btn)
        buttons_layout.addWidget(self.delete_room_btn)
        buttons_layout.addStretch()
        
        # 部屋一覧テーブル
        self.rooms_table = QTableWidget()
        self.rooms_table.setColumnCount(6)
        self.rooms_table.setHorizontalHeaderLabels([
            "部屋番号", "階数", "面積", "ペット可", "深夜利用可", "備考"
        ])
        self.rooms_table.setMaximumHeight(200)
        self.rooms_table.setMinimumHeight(150)
        self.rooms_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.rooms_table.setAlternatingRowColors(True)
        self.rooms_table.itemSelectionChanged.connect(self.on_room_selection_changed)
        self.rooms_table.itemDoubleClicked.connect(self.edit_room)
        
        # テーブルの列幅調整
        header = self.rooms_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # 部屋番号
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # 階数
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # 面積
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # ペット可
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # 深夜利用可
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)           # 備考
        
        rooms_layout.addLayout(buttons_layout)
        rooms_layout.addWidget(self.rooms_table)
        
        # 編集時のみ表示
        self.rooms_group.setVisible(self.property_data is not None)
        
        # コンテナーに各セクションを追加
        container_layout.addWidget(basic_info_group)
        container_layout.addWidget(registry_group)
        container_layout.addWidget(management_group)
        container_layout.addWidget(notes_group)
        container_layout.addWidget(self.rooms_group)
        
        # 管理形態による表示制御
        self.management_type_combo.currentTextChanged.connect(self.on_management_type_changed)
        self.on_management_type_changed(self.management_type_combo.currentText())
        
        # スクロールエリアにコンテナーを設定
        scroll_area.setWidget(container_widget)
        
        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(scroll_area)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def on_management_type_changed(self, management_type):
        """管理形態変更時の処理"""
        show_company = (management_type in ["他社仲介", "共同管理"])
        self.management_company_edit.setEnabled(show_company)
        if not show_company:
            self.management_company_edit.clear()
    
    def load_property_data(self):
        """物件データを読み込み"""
        if not self.property_data:
            return
        
        self.name_edit.setText(self.property_data.get('name', ''))
        self.address_edit.setPlainText(self.property_data.get('address', ''))
        
        # 構造設定
        structure = self.property_data.get('structure', '')
        index = self.structure_combo.findText(structure)
        if index >= 0:
            self.structure_combo.setCurrentIndex(index)
        
        self.registry_owner_edit.setText(self.property_data.get('registry_owner', ''))
        
        # 建築年月日設定（新規追加）
        construction_date = self.property_data.get('construction_date')
        if construction_date:
            if isinstance(construction_date, str):
                date = QDate.fromString(construction_date, "yyyy-MM-dd")
                if date.isValid():
                    self.construction_date_edit.setDate(date)
            else:
                try:
                    self.construction_date_edit.setDate(QDate(construction_date))
                except:
                    pass
        
        # 管理形態設定
        management_type = self.property_data.get('management_type', '自社管理')
        index = self.management_type_combo.findText(management_type)
        if index >= 0:
            self.management_type_combo.setCurrentIndex(index)
        
        self.management_company_edit.setText(self.property_data.get('management_company', ''))
        self.available_rooms_spin.setValue(self.property_data.get('available_rooms', 0))
        self.renewal_rooms_spin.setValue(self.property_data.get('renewal_rooms', 0))
        self.notes_edit.setPlainText(self.property_data.get('notes', ''))
        
        # 部屋データを読み込み
        if self.property_data:
            self.load_rooms_data()
    
    def get_property_data(self):
        """入力データを取得"""
        return {
            'name': self.name_edit.text().strip(),
            'address': self.address_edit.toPlainText().strip(),
            'structure': self.structure_combo.currentText(),
            'registry_owner': self.registry_owner_edit.text().strip(),
            'construction_date': self.construction_date_edit.date().toString("yyyy-MM-dd"),
            'management_type': self.management_type_combo.currentText(),
            'management_company': self.management_company_edit.text().strip(),
            'available_rooms': self.available_rooms_spin.value(),
            'renewal_rooms': self.renewal_rooms_spin.value(),
            'notes': self.notes_edit.toPlainText().strip()
        }
    
    def validate_input(self):
        """入力値のバリデーション"""
        data = self.get_property_data()
        
        # 必須項目チェック
        valid, msg = Validator.validate_required(data['name'], '物件名')
        if not valid:
            MessageHelper.show_warning(self, msg)
            return False
        
        valid, msg = Validator.validate_required(data['address'], '住所')
        if not valid:
            MessageHelper.show_warning(self, msg)
            return False
        
        return True
    
    def load_rooms_data(self):
        """物件の部屋データを読み込み"""
        if not self.property_data:
            return
        
        try:
            property_id = self.property_data.get('id')
            if not property_id:
                return
            
            rooms = Unit.get_by_property(property_id)
            self.rooms_table.setRowCount(len(rooms))
            
            for row, room in enumerate(rooms):
                self.rooms_table.setItem(row, 0, QTableWidgetItem(str(room.get('room_number', ''))))
                self.rooms_table.setItem(row, 1, QTableWidgetItem(str(room.get('floor', ''))))
                
                # 面積表示
                area = room.get('area')
                area_text = f"{area}m²" if area else ""
                self.rooms_table.setItem(row, 2, QTableWidgetItem(area_text))
                
                # ペット可表示
                pet_allowed = "○" if room.get('pet_allowed') else ""
                self.rooms_table.setItem(row, 3, QTableWidgetItem(pet_allowed))
                
                # 深夜利用可表示
                midnight_allowed = "○" if room.get('midnight_allowed') else ""
                self.rooms_table.setItem(row, 4, QTableWidgetItem(midnight_allowed))
                
                # 備考（制限事項優先）
                notes = room.get('use_restrictions') or room.get('notes') or ""
                self.rooms_table.setItem(row, 5, QTableWidgetItem(notes))
                
                # データを行に保存（編集・削除用）
                self.rooms_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, room)
        
        except Exception as e:
            print(f"部屋データ読み込みエラー: {e}")
    
    def on_room_selection_changed(self):
        """部屋選択変更時の処理"""
        has_selection = len(self.rooms_table.selectedItems()) > 0
        self.edit_room_btn.setEnabled(has_selection)
        self.delete_room_btn.setEnabled(has_selection)
    
    def get_selected_room(self):
        """選択された部屋データを取得"""
        current_row = self.rooms_table.currentRow()
        if current_row >= 0:
            item = self.rooms_table.item(current_row, 0)
            if item:
                return item.data(Qt.ItemDataRole.UserRole)
        return None
    
    def add_room(self):
        """部屋を追加"""
        if not self.property_data:
            MessageHelper.show_warning(self, "まず物件を保存してから部屋を追加してください")
            return
        
        property_id = self.property_data.get('id')
        if not property_id:
            MessageHelper.show_warning(self, "物件IDが見つかりません")
            return
        
        dialog = UnitEditDialog(self, property_id=property_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_unit_data()
            
            try:
                Unit.create(
                    property_id=property_id,
                    room_number=data['room_number'],
                    floor=data['floor'],
                    area=data['area'],
                    use_restrictions=data['use_restrictions'],
                    power_capacity=data['power_capacity'],
                    pet_allowed=data['pet_allowed'],
                    midnight_allowed=data['midnight_allowed'],
                    notes=data['notes']
                )
                
                MessageHelper.show_success(self, "部屋を追加しました")
                self.load_rooms_data()
            
            except Exception as e:
                MessageHelper.show_error(self, f"部屋の追加に失敗しました: {e}")
    
    def edit_room(self):
        """選択された部屋を編集"""
        room_data = self.get_selected_room()
        if not room_data:
            MessageHelper.show_warning(self, "編集する部屋を選択してください")
            return
        
        property_id = self.property_data.get('id')
        dialog = UnitEditDialog(self, property_id=property_id, unit_data=room_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_unit_data()
            
            try:
                Unit.update(
                    unit_id=room_data['id'],
                    room_number=data['room_number'],
                    floor=data['floor'],
                    area=data['area'],
                    use_restrictions=data['use_restrictions'],
                    power_capacity=data['power_capacity'],
                    pet_allowed=data['pet_allowed'],
                    midnight_allowed=data['midnight_allowed'],
                    notes=data['notes']
                )
                
                MessageHelper.show_success(self, "部屋情報を更新しました")
                self.load_rooms_data()
            
            except Exception as e:
                MessageHelper.show_error(self, f"部屋の更新に失敗しました: {e}")
    
    def delete_room(self):
        """選択された部屋を削除"""
        room_data = self.get_selected_room()
        if not room_data:
            MessageHelper.show_warning(self, "削除する部屋を選択してください")
            return
        
        room_number = room_data.get('room_number', '')
        if MessageHelper.confirm_delete(self, f"部屋「{room_number}」"):
            try:
                Unit.delete(room_data['id'])
                MessageHelper.show_success(self, "部屋を削除しました")
                self.load_rooms_data()
            
            except ValueError as e:
                MessageHelper.show_warning(self, str(e))
            except Exception as e:
                MessageHelper.show_error(self, f"部屋の削除に失敗しました: {e}")
    
    def accept(self):
        """OKボタンが押されたとき"""
        if self.validate_input():
            super().accept()

class UnitBasicDialog(QDialog):
    """部屋情報簡易登録ダイアログ（スクロール対応）"""
    
    def __init__(self, parent=None, property_id=None):
        super().__init__(parent)
        self.property_id = property_id
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("部屋情報登録")
        self.setModal(True)
        self.resize(500, 400)  # サイズを少し大きく
        
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # スクロールエリアを追加
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # スクロールバースタイルを適用
        from ui_styles import ModernStyles
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            {ModernStyles.get_scroll_bar_style()}
        """)
        
        # フォームウィジェット
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setSpacing(16)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        self.room_number_edit = QLineEdit()
        self.room_number_edit.setPlaceholderText("例: 101, 201A")
        self.room_number_edit.setMinimumHeight(36)
        
        self.floor_edit = QLineEdit()
        self.floor_edit.setPlaceholderText("例: 1F, 2F")
        self.floor_edit.setMinimumHeight(36)
        
        self.area_spin = QSpinBox()
        self.area_spin.setRange(1, 9999)
        self.area_spin.setSuffix(" ㎡")
        self.area_spin.setMinimumHeight(36)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        self.notes_edit.setMinimumHeight(60)
        self.notes_edit.setPlaceholderText("部屋に関する特記事項、設備情報など")
        
        form_layout.addRow("部屋番号 *:", self.room_number_edit)
        form_layout.addRow("階層:", self.floor_edit)
        form_layout.addRow("面積:", self.area_spin)
        form_layout.addRow("備考:", self.notes_edit)
        
        # スクロールエリアにフォームを設定
        scroll_area.setWidget(form_widget)
        
        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # ボタンのスタイルを改善
        from ui_styles import ButtonHelper
        ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button:
            ok_button.setText("登録")
            ButtonHelper.set_success(ok_button)
        cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_button:
            cancel_button.setText("キャンセル")
        
        layout.addWidget(scroll_area)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def get_unit_data(self):
        """部屋データを取得"""
        return {
            'property_id': self.property_id,
            'room_number': self.room_number_edit.text().strip(),
            'floor': self.floor_edit.text().strip(),
            'area': self.area_spin.value(),
            'notes': self.notes_edit.toPlainText().strip()
        }
    
    def validate_input(self):
        """入力値のバリデーション"""
        data = self.get_unit_data()
        
        valid, msg = Validator.validate_required(data['room_number'], '部屋番号')
        if not valid:
            MessageHelper.show_warning(self, msg)
            return False
        
        return True
    
    def accept(self):
        """OKボタンが押されたとき"""
        if self.validate_input():
            super().accept()

class PropertyTabBasic(QWidget):
    """物件管理タブ - 基本版"""
    
    property_updated = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_properties()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 検索バー
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("検索:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("物件名、住所、所有者で検索...")
        self.search_edit.textChanged.connect(self.on_search)
        search_layout.addWidget(self.search_edit)
        
        # フィルターコンボボックス
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全て", "自社管理", "他社仲介", "共同管理"])
        self.filter_combo.currentTextChanged.connect(self.on_filter_changed)
        search_layout.addWidget(QLabel("管理形態:"))
        search_layout.addWidget(self.filter_combo)
        
        search_layout.addStretch()
        
        # ボタングループ
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("新規登録")
        self.add_button.clicked.connect(self.add_property)
        self.add_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        
        self.edit_button = QPushButton("編集")
        self.edit_button.clicked.connect(self.edit_property)
        self.edit_button.setEnabled(False)
        
        self.delete_button = QPushButton("削除")
        self.delete_button.clicked.connect(self.delete_property)
        self.delete_button.setEnabled(False)
        self.delete_button.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        
        self.add_unit_button = QPushButton("部屋追加")
        self.add_unit_button.clicked.connect(self.add_unit)
        self.add_unit_button.setEnabled(False)
        self.add_unit_button.setStyleSheet("QPushButton { background-color: #FF9800; color: white; }")
        
        self.refresh_button = QPushButton("更新")
        self.refresh_button.clicked.connect(self.load_properties)
        
        self.export_button = QPushButton("CSV出力")
        self.export_button.clicked.connect(self.export_to_csv)
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.add_unit_button)
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()
        
        # 物件一覧テーブル（ツリー形式）
        from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem
        self.property_tree = QTreeWidget()
        self.property_tree.setHeaderLabels([
            "ID", "物件名/部屋番号", "住所/階層", "構造/面積", "管理形態", "募集中", "更新予定", "最終更新"
        ])
        
        # ツリー設定（レスポンシブ対応）
        self.property_tree.setColumnHidden(0, True)  # IDを非表示
        header = self.property_tree.header()
        
        # 列幅の最適化
        header.resizeSection(1, 180)  # 物件名/部屋番号
        header.resizeSection(2, 160)  # 住所/階層
        header.resizeSection(3, 100)  # 構造/面積
        header.resizeSection(4, 80)   # 管理形態
        header.resizeSection(5, 60)   # 募集中
        header.resizeSection(6, 60)   # 更新予定
        header.resizeSection(7, 100)  # 最終更新
        
        # テーブル設定
        self.property_tree.setAlternatingRowColors(True)
        self.property_tree.setRootIsDecorated(True)
        
        # サイズポリシー設定
        self.property_tree.setSizePolicy(
            self.property_tree.sizePolicy().Policy.Expanding,
            self.property_tree.sizePolicy().Policy.Expanding
        )
        
        # ツリーのイベント
        self.property_tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.property_tree.itemSelectionChanged.connect(self.on_tree_selection_changed)
        
        # 詳細表示エリア
        self.detail_group = QGroupBox("物件詳細")
        detail_layout = QFormLayout()
        detail_layout.setSpacing(12)
        detail_layout.setContentsMargins(16, 16, 16, 16)
        detail_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        detail_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        detail_layout.setHorizontalSpacing(16)
        detail_layout.setVerticalSpacing(12)
        
        self.detail_name_label = QLabel("選択された物件の詳細がここに表示されます")
        self.detail_name_label.setMinimumHeight(24)
        
        self.detail_address_label = QLabel()
        self.detail_address_label.setMinimumHeight(24)
        self.detail_address_label.setWordWrap(True)
        
        self.detail_structure_label = QLabel()
        self.detail_structure_label.setMinimumHeight(24)
        
        self.detail_owner_label = QLabel()
        self.detail_owner_label.setMinimumHeight(24)
        
        self.detail_management_label = QLabel()
        self.detail_management_label.setMinimumHeight(24)
        
        self.detail_notes_label = QLabel()
        self.detail_notes_label.setWordWrap(True)
        self.detail_notes_label.setMinimumHeight(60)
        
        # 初期状態では詳細エリアを非表示に
        self.detail_name_label.setStyleSheet("color: #666; font-style: italic; padding: 2px;")
        
        detail_layout.addRow("物件名:", self.detail_name_label)
        detail_layout.addRow("住所:", self.detail_address_label)
        detail_layout.addRow("構造:", self.detail_structure_label)
        detail_layout.addRow("所有者:", self.detail_owner_label)
        detail_layout.addRow("管理形態:", self.detail_management_label)
        detail_layout.addRow("備考:", self.detail_notes_label)
        
        self.detail_group.setLayout(detail_layout)
        self.detail_group.setMaximumHeight(200)
        
        # スプリッター
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 上部ウィジェット（テーブル）
        top_widget = QWidget()
        top_layout = QVBoxLayout()
        top_layout.addLayout(search_layout)
        top_layout.addLayout(button_layout)
        top_layout.addWidget(self.property_tree)
        top_widget.setLayout(top_layout)
        
        splitter.addWidget(top_widget)
        splitter.addWidget(self.detail_group)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        self.setLayout(layout)
        
        # タブが表示されたときの初期化処理を追加
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
        
        # マウスホイールイベントを有効化
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        
        # スムーススクロールのためのタイマー設定
        self.scroll_timer = None
    
    def showEvent(self, event):
        """タブが表示された時の処理"""
        super().showEvent(event)
        # 物件ツリーが空の場合は再読み込み
        if self.property_tree.topLevelItemCount() == 0:
            self.load_properties()
        # ヘッダーサイズを最適化
        self.property_tree.header().resizeSection(1, 200)
        self.property_tree.header().resizeSection(2, 180)
        
        # ツリーウィジェットのスクロール性能を最適化
        try:
            tree_scroll_area = self.property_tree.findChild(QScrollArea)
            if tree_scroll_area:
                tree_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
                tree_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        except:
            pass
    
    def load_properties(self):
        """物件一覧を読み込み（部屋情報も含む）"""
        try:
            from PyQt6.QtWidgets import QTreeWidgetItem
            
            # テーブルを完全にクリアして再初期化
            self.property_tree.clear()
            self.property_tree.setRootIsDecorated(True)
            self.property_tree.setItemsExpandable(True)
            self.property_tree.setSortingEnabled(False)  # ソート無効化でパフォーマンス向上
            
            # プログレスバー風の表示（大量データ対応）
            loading_item = QTreeWidgetItem(["0", "読み込み中...", "", "", "", "", "", ""])
            self.property_tree.addTopLevelItem(loading_item)
            self.property_tree.repaint()  # 即座に表示更新
            
            try:
                properties = Property.get_all()
                if properties is None:
                    properties = []
            except Exception as prop_error:
                print(f"Property.get_all()エラー: {prop_error}")
                properties = []
            
            # 読み込み中アイテムを削除
            self.property_tree.clear()
            
            if not properties:
                # データがない場合の表示
                empty_item = QTreeWidgetItem(["0", "物件データがありません", "新規登録してください", "", "", "", "", ""])
                empty_item.setDisabled(True)
                self.property_tree.addTopLevelItem(empty_item)
                return
            
            for property_data in properties:
                # 物件の親アイテムを作成
                property_item = QTreeWidgetItem()
                property_item.setText(0, str(property_data['id']))
                property_item.setText(1, property_data['name'])
                property_item.setText(2, property_data.get('address', ''))
                property_item.setText(3, property_data.get('structure', ''))
                
                # 管理形態
                management_type = property_data.get('management_type', '自社管理')
                property_item.setText(4, management_type)
                
                property_item.setText(5, str(property_data.get('available_rooms', 0)))
                property_item.setText(6, str(property_data.get('renewal_rooms', 0)))
                
                # 最終更新日
                updated_at = DateHelper.format_date(property_data.get('updated_at'))
                property_item.setText(7, updated_at)
                
                # 物件の背景色設定
                try:
                    if management_type == '自社管理':
                        property_item.setBackground(4, QColor("#E8F5E8"))  # 薄緑
                    elif management_type == '他社仲介':
                        property_item.setBackground(4, QColor("#E3F2FD"))  # 薄青
                    else:  # 共同管理
                        property_item.setBackground(4, QColor("#FFF3E0"))  # 薄オレンジ
                except Exception as color_error:
                    print(f"背景色設定エラー: {color_error}")
                
                # データを保存（編集・削除で使用）
                property_item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'property', 'data': property_data})
                
                # フォントを太字に
                from PyQt6.QtGui import QFont
                font = property_item.font(1)
                font.setBold(True)
                property_item.setFont(1, font)
                
                # 部屋情報を取得してサブアイテムとして追加
                try:
                    from models import Unit
                    units = Unit.get_by_property(property_data['id'])
                    if units is None:
                        units = []
                    
                    for unit in units:
                        unit_item = QTreeWidgetItem()
                        unit_item.setText(0, str(unit['id']))
                        unit_item.setText(1, f"  └ {unit['room_number']}")  # インデント表示
                        unit_item.setText(2, f"    {unit.get('floor', '')}")
                        
                        # 面積表示
                        area_text = f"{unit.get('area', 0)}㎡" if unit.get('area') else ""
                        unit_item.setText(3, f"    {area_text}")
                        
                        # 部屋の背景色（薄いグレー）
                        try:
                            for col in range(8):
                                unit_item.setBackground(col, QColor("#F8F8F8"))
                        except Exception as color_error:
                            print(f"部屋背景色設定エラー: {color_error}")
                        
                        # データを保存
                        unit_item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'unit', 'data': unit})
                        
                        property_item.addChild(unit_item)
                    
                    # 部屋数をカウントして表示更新
                    if units:
                        property_item.setText(1, f"{property_data['name']} ({len(units)}室)")
                        # 部屋がある場合のみ展開可能にする
                        property_item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)
                    else:
                        # 部屋がない場合は展開インジケーターを隠す
                        property_item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.DontShowIndicator)
                    
                except Exception as e:
                    print(f"部屋情報読み込みエラー: {e}")
                    # エラー時でも物件は表示する
                    error_item = QTreeWidgetItem()
                    error_item.setText(1, f"  └ 部屋情報読み込みエラー: {str(e)[:30]}...")
                    error_item.setDisabled(True)
                    try:
                        for col in range(8):
                            error_item.setBackground(col, QColor("#ffebee"))
                    except Exception as color_error:
                        print(f"エラー表示背景色設定エラー: {color_error}")
                    property_item.addChild(error_item)
                
                self.property_tree.addTopLevelItem(property_item)
                
                # デフォルトで展開（ただし最初の3件まで）
                if self.property_tree.topLevelItemCount() <= 3:
                    property_item.setExpanded(True)
                else:
                    property_item.setExpanded(False)
            
            # ソート機能を再有効化
            self.property_tree.setSortingEnabled(True)
            
            # 列幅を再調整（データ読み込み後）
            self.property_tree.resizeColumnToContents(1)  # 物件名列
            self.property_tree.resizeColumnToContents(2)  # 住所列
            
            print(f"物件データ読み込み完了: {len(properties)}件")
            
        except Exception as e:
            # エラー時の詳細表示
            self.property_tree.clear()
            error_item = QTreeWidgetItem(["0", "エラー発生", f"読み込みエラー: {str(e)[:50]}...", "", "", "", "", ""])
            error_item.setDisabled(True)
            try:
                for col in range(8):
                    error_item.setBackground(col, QColor("#ffcdd2"))
            except Exception as color_error:
                print(f"エラー項目背景色設定エラー: {color_error}")
            self.property_tree.addTopLevelItem(error_item)
            
            print(f"物件データ読み込みエラー: {e}")
            MessageHelper.show_error(self, f"物件一覧の読み込み中にエラーが発生しました:\n{str(e)}")
    
    def on_search(self):
        """検索処理（ツリー対応）"""
        search_text = self.search_edit.text().lower()
        
        for i in range(self.property_tree.topLevelItemCount()):
            property_item = self.property_tree.topLevelItem(i)
            property_match = False
            
            # 物件名・住所・構造で検索
            if (search_text in property_item.text(1).lower() or 
                search_text in property_item.text(2).lower() or 
                search_text in property_item.text(3).lower()):
                property_match = True
            
            # 部屋でも検索
            unit_match = False
            for j in range(property_item.childCount()):
                unit_item = property_item.child(j)
                if (search_text in unit_item.text(1).lower() or 
                    search_text in unit_item.text(2).lower()):
                    unit_match = True
                    break
            
            # どちらかでマッチすれば表示
            if search_text == '' or property_match or unit_match:
                property_item.setHidden(False)
            else:
                property_item.setHidden(True)
    
    def on_filter_changed(self):
        """フィルター変更処理（ツリー対応）"""
        filter_type = self.filter_combo.currentText()
        
        for i in range(self.property_tree.topLevelItemCount()):
            property_item = self.property_tree.topLevelItem(i)
            
            if filter_type == "全て":
                property_item.setHidden(False)
            else:
                management_type = property_item.text(4)
                should_show = (filter_type == management_type)
                property_item.setHidden(not should_show)
    
    def on_tree_selection_changed(self):
        """ツリー選択変更時の処理"""
        selected_items = self.property_tree.selectedItems()
        has_selection = len(selected_items) > 0
        
        # 選択されたアイテムが物件かどうかで動作を変更
        is_property_selected = False
        if has_selection:
            selected_item = selected_items[0]
            item_data = selected_item.data(0, Qt.ItemDataRole.UserRole)
            if item_data and item_data.get('type') == 'property':
                is_property_selected = True
                self.show_property_detail(selected_item)
            elif item_data and item_data.get('type') == 'unit':
                # 部屋が選択された場合は親の物件を選択状態にする
                parent_item = selected_item.parent()
                if parent_item:
                    is_property_selected = True
                    self.show_property_detail(parent_item)
        
        # ボタンの有効/無効を設定
        self.edit_button.setEnabled(is_property_selected)
        self.delete_button.setEnabled(is_property_selected)
        self.add_unit_button.setEnabled(is_property_selected)
    
    def on_item_double_clicked(self, item, column):
        """アイテムダブルクリック時の処理"""
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if item_data:
            if item_data.get('type') == 'property':
                self.edit_property()
            elif item_data.get('type') == 'unit':
                # 部屋編集機能（今後実装）
                MessageHelper.show_warning(self, "部屋の編集機能は今後実装予定です")
    
    def show_property_detail(self, property_item=None):
        """選択された物件の詳細を表示"""
        if not property_item:
            selected_items = self.property_tree.selectedItems()
            if not selected_items:
                return
            
            selected_item = selected_items[0]
            item_data = selected_item.data(0, Qt.ItemDataRole.UserRole)
            
            if item_data and item_data.get('type') == 'property':
                property_item = selected_item
            elif item_data and item_data.get('type') == 'unit':
                property_item = selected_item.parent()
            else:
                return
        
        if not property_item:
            return
        
        item_data = property_item.data(0, Qt.ItemDataRole.UserRole)
        if not item_data or item_data.get('type') != 'property':
            return
        
        property_data = item_data.get('data')
        if property_data:
            self.detail_name_label.setText(property_data.get('name', ''))
            self.detail_address_label.setText(property_data.get('address', ''))
            self.detail_structure_label.setText(property_data.get('structure', ''))
            self.detail_owner_label.setText(property_data.get('registry_owner', ''))
            
            management = property_data.get('management_type', '自社管理')
            company = property_data.get('management_company', '')
            if company:
                management += f" ({company})"
            self.detail_management_label.setText(management)
            
            self.detail_notes_label.setText(property_data.get('notes', ''))
    
    def add_property(self):
        """物件新規登録"""
        dialog = PropertyEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_property_data()
            
            try:
                Property.create(
                    name=data['name'],
                    address=data['address'],
                    structure=data['structure'],
                    registry_owner=data['registry_owner'],
                    management_type=data['management_type'],
                    management_company=data['management_company'],
                    available_rooms=data['available_rooms'],
                    renewal_rooms=data['renewal_rooms'],
                    notes=data['notes']
                )
                
                MessageHelper.show_success(self, "物件を登録しました")
                self.load_properties()
                self.property_updated.emit()
                
            except Exception as e:
                MessageHelper.show_error(self, f"物件登録中にエラーが発生しました: {str(e)}")
    
    def edit_property(self):
        """物件編集"""
        selected_items = self.property_tree.selectedItems()
        if not selected_items:
            return
        
        selected_item = selected_items[0]
        item_data = selected_item.data(0, Qt.ItemDataRole.UserRole)
        
        # 部屋が選択されている場合は親の物件を取得
        if item_data and item_data.get('type') == 'unit':
            selected_item = selected_item.parent()
            if selected_item:
                item_data = selected_item.data(0, Qt.ItemDataRole.UserRole)
        
        if not item_data or item_data.get('type') != 'property':
            return
        
        property_data = item_data.get('data')
        if not property_data:
            return
        
        dialog = PropertyEditDialog(self, property_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_property_data()
            
            try:
                Property.update(
                    id=property_data['id'],
                    name=data['name'],
                    address=data['address'],
                    structure=data['structure'],
                    registry_owner=data['registry_owner'],
                    management_type=data['management_type'],
                    management_company=data['management_company'],
                    available_rooms=data['available_rooms'],
                    renewal_rooms=data['renewal_rooms'],
                    notes=data['notes']
                )
                
                MessageHelper.show_success(self, "物件情報を更新しました")
                self.load_properties()
                self.property_updated.emit()
                
            except Exception as e:
                MessageHelper.show_error(self, f"物件更新中にエラーが発生しました: {str(e)}")
    
    def delete_property(self):
        """物件削除"""
        selected_items = self.property_tree.selectedItems()
        if not selected_items:
            return
        
        selected_item = selected_items[0]
        item_data = selected_item.data(0, Qt.ItemDataRole.UserRole)
        
        # 部屋が選択されている場合は親の物件を取得
        if item_data and item_data.get('type') == 'unit':
            selected_item = selected_item.parent()
            if selected_item:
                item_data = selected_item.data(0, Qt.ItemDataRole.UserRole)
        
        if not item_data or item_data.get('type') != 'property':
            return
        
        property_data = item_data.get('data')
        if not property_data:
            return
        
        property_name = property_data.get('name', '')
        
        if MessageHelper.confirm_delete(self, f"物件「{property_name}」"):
            property_id = property_data['id']
            
            try:
                Property.delete(property_id)
                
                MessageHelper.show_success(self, "物件を削除しました")
                self.load_properties()
                self.property_updated.emit()
                
            except Exception as e:
                MessageHelper.show_error(self, f"物件削除中にエラーが発生しました: {str(e)}")
    
    def add_unit(self):
        """部屋追加"""
        selected_items = self.property_tree.selectedItems()
        if not selected_items:
            return
        
        selected_item = selected_items[0]
        item_data = selected_item.data(0, Qt.ItemDataRole.UserRole)
        
        # 部屋が選択されている場合は親の物件を取得
        if item_data and item_data.get('type') == 'unit':
            selected_item = selected_item.parent()
            if selected_item:
                item_data = selected_item.data(0, Qt.ItemDataRole.UserRole)
        
        if not item_data or item_data.get('type') != 'property':
            return
        
        property_data = item_data.get('data')
        if not property_data:
            return
        
        property_id = property_data['id']
        dialog = UnitBasicDialog(self, property_id)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_unit_data()
            
            try:
                from models import Unit
                Unit.create(
                    property_id=data['property_id'],
                    room_number=data['room_number'],
                    floor=data['floor'],
                    area=data['area'],
                    notes=data['notes']
                )
                
                MessageHelper.show_success(self, "部屋を登録しました")
                self.load_properties()  # ツリーを更新して部屋を表示
                
            except Exception as e:
                MessageHelper.show_error(self, f"部屋登録中にエラーが発生しました: {str(e)}")
    
    def export_to_csv(self):
        """CSV出力"""
        try:
            import csv
            from PyQt6.QtWidgets import QFileDialog
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "CSVファイルの保存", "", "CSV Files (*.csv)"
            )
            
            if file_path:
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # ヘッダー
                    writer.writerow(["物件名", "住所", "構造", "管理形態", "募集中", "更新予定", "部屋番号", "階層", "面積"])
                    
                    # データ（物件と部屋の情報を出力）
                    for i in range(self.property_tree.topLevelItemCount()):
                        property_item = self.property_tree.topLevelItem(i)
                        if not property_item.isHidden():
                            # 物件データ
                            property_row = [
                                property_item.text(1), property_item.text(2), 
                                property_item.text(3), property_item.text(4),
                                property_item.text(5), property_item.text(6),
                                "", "", ""  # 部屋情報は空
                            ]
                            writer.writerow(property_row)
                            
                            # 部屋データ
                            for j in range(property_item.childCount()):
                                unit_item = property_item.child(j)
                                unit_row = [
                                    "", "", "", "", "", "",  # 物件情報は空
                                    unit_item.text(1).replace("  └ ", ""),  # インデント除去
                                    unit_item.text(2).strip(),
                                    unit_item.text(3).strip()
                                ]
                                writer.writerow(unit_row)
                
                MessageHelper.show_success(self, f"CSVファイルを出力しました:\n{file_path}")
                
        except Exception as e:
            MessageHelper.show_error(self, f"CSV出力中にエラーが発生しました: {str(e)}")
    
    def wheelEvent(self, event):
        """マウスホイールイベントの最適化処理"""
        try:
            # Ctrlキーと組み合わせてズーム機能を無効化
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                event.ignore()
                return
            
            # 高速スクロールのための値調整
            delta = event.angleDelta().y()
            if abs(delta) > 120:  # 高速スクロールを制限
                if delta > 0:
                    delta = 120
                else:
                    delta = -120
                
                # 新しいイベントを作成
                from PyQt6.QtGui import QWheelEvent
                new_event = QWheelEvent(
                    event.position(),
                    event.globalPosition(),
                    event.pixelDelta(),
                    event.angleDelta().replace(y=delta),
                    event.buttons(),
                    event.modifiers(),
                    event.phase(),
                    event.inverted()
                )
                super().wheelEvent(new_event)
            else:
                super().wheelEvent(event)
        except Exception as e:
            print(f"ホイールイベントエラー: {e}")
            super().wheelEvent(event)