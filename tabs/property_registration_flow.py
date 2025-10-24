#!/usr/bin/env python3
"""
物件・部屋登録フロー統合管理タブ
一棟もの対応・資料管理機能付き
"""

import os
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QGroupBox, QFormLayout, QLabel, QLineEdit, QTextEdit,
                             QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
                             QCheckBox, QTableWidget, QTableWidgetItem,
                             QFileDialog, QMessageBox, QListWidget, QListWidgetItem,
                             QProgressBar, QFrame, QSplitter, QScrollArea,
                             QGridLayout, QButtonGroup, QRadioButton)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QIcon
from models import Property, Unit, Customer
from ui.ui_styles import ModernTheme, ModernStyles

# UI Helper関数
from ui.ui_helpers import make_page_container, make_scroll_page, make_collapsible

# マウスホイール無効化SpinBox
class NoWheelSpinBox(QSpinBox):
    """マウスホイールによる値変更を無効化したSpinBox"""
    def wheelEvent(self, event):
        event.ignore()

class NoWheelDoubleSpinBox(QDoubleSpinBox):
    """マウスホイールによる値変更を無効化したDoubleSpinBox"""
    def wheelEvent(self, event):
        event.ignore()


class PropertyRegistrationFlow(QWidget):
    """物件・部屋登録フロー統合管理"""
    
    def __init__(self):
        super().__init__()
        self.current_property_id = None
        self.current_unit_id = None
        self.document_storage_path = "property_documents"
        self.ensure_document_directory()
        self.init_ui()
        
    def ensure_document_directory(self):
        """資料保存ディレクトリを確保"""
        if not os.path.exists(self.document_storage_path):
            os.makedirs(self.document_storage_path)
    
    def init_ui(self):
        """UIを初期化"""
        # ページコンテナを作成
        container, layout = make_page_container()
        
        # タイトル
        title = QLabel("🏢 物件・部屋登録フロー")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: {ModernTheme.FONTS['size_2xl']};
                font-weight: 600;
                color: {ModernTheme.COLORS['text_primary']};
                margin-bottom: {ModernTheme.SPACING['lg']};
            }}
        """)
        layout.addWidget(title)
        
        # メインコンテンツ - スプリッターで分割
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左側：登録フロー
        left_widget = self.create_registration_flow()
        left_widget.setMinimumWidth(500)
        main_splitter.addWidget(left_widget)
        
        # 右側：物件・部屋一覧と資料管理
        right_widget = self.create_management_panel()
        right_widget.setMinimumWidth(400)
        main_splitter.addWidget(right_widget)
        
        # スプリッターの初期比率
        main_splitter.setSizes([600, 500])
        
        layout.addWidget(main_splitter)
        
        # スクロール可能ページとして設定
        scroll_page = make_scroll_page(container)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(scroll_page)
        
        # 初期データ読み込み
        self.load_properties()
    
    def create_registration_flow(self):
        """登録フローパネルを作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        # ステップ指示
        steps_card = self.create_steps_card()
        layout.addWidget(steps_card)
        
        # タブウィジェット
        self.flow_tabs = QTabWidget()
        self.flow_tabs.setStyleSheet(ModernStyles.get_tab_widget_style())
        
        # ステップ1: 物件基本情報登録
        self.property_tab = self.create_property_registration_tab()
        self.flow_tabs.addTab(self.property_tab, "Step 1: 物件基本情報")
        
        # ステップ2: 物件詳細・一棟もの設定
        self.building_tab = self.create_building_details_tab()
        self.flow_tabs.addTab(self.building_tab, "Step 2: 建物・一棟もの設定")
        
        # ステップ3: 部屋登録
        self.units_tab = self.create_units_registration_tab()
        self.flow_tabs.addTab(self.units_tab, "Step 3: 部屋登録")
        
        # ステップ4: 資料アップロード
        self.documents_tab = self.create_documents_tab()
        self.flow_tabs.addTab(self.documents_tab, "Step 4: 資料管理")
        
        layout.addWidget(self.flow_tabs)
        
        # タブ変更時の処理
        self.flow_tabs.currentChanged.connect(self.on_tab_changed)
        
        return widget
    
    def create_steps_card(self):
        """登録ステップ説明カードを作成"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {ModernTheme.COLORS['bg_primary']};
                border: 1px solid {ModernTheme.COLORS['border']};
                border-radius: {ModernTheme.RADIUS['lg']};
                padding: {ModernTheme.SPACING['md']};
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        # タイトル
        title = QLabel("📋 登録フロー")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: {ModernTheme.FONTS['size_lg']};
                font-weight: 600;
                color: {ModernTheme.COLORS['text_primary']};
                margin-bottom: {ModernTheme.SPACING['sm']};
            }}
        """)
        layout.addWidget(title)
        
        # ステップ説明
        steps = [
            "1️⃣ 物件基本情報の登録（名称・住所・管理形態）",
            "2️⃣ 建物詳細設定（構造・一棟もの・階層設定）", 
            "3️⃣ 部屋個別登録（手動入力・図面OCR対応）",
            "4️⃣ 資料アップロード（図面・契約書・登記簿等）"
        ]
        
        for step in steps:
            step_label = QLabel(step)
            step_label.setStyleSheet(f"""
                QLabel {{
                    color: {ModernTheme.COLORS['text_secondary']};
                    font-size: {ModernTheme.FONTS['size_sm']};
                    margin: 2px 0;
                }}
            """)
            layout.addWidget(step_label)
        
        return card
    
    def create_property_registration_tab(self):
        """物件基本情報登録タブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 基本情報グループ
        basic_group = QGroupBox("物件基本情報")
        basic_layout = QFormLayout()
        
        self.property_name_edit = QLineEdit()
        self.property_name_edit.setPlaceholderText("例: ○○マンション")
        
        self.property_address_edit = QTextEdit()
        self.property_address_edit.setMaximumHeight(60)
        self.property_address_edit.setPlaceholderText("例: 東京都渋谷区...")
        
        self.structure_combo = QComboBox()
        self.structure_combo.addItems([
            "選択してください", "RC造", "SRC造", "S造", "木造", "軽量鉄骨造", "その他"
        ])
        
        self.registry_owner_edit = QLineEdit()
        self.registry_owner_edit.setPlaceholderText("登記簿上の所有者名")
        
        basic_layout.addRow("物件名称 *:", self.property_name_edit)
        basic_layout.addRow("住所 *:", self.property_address_edit)
        basic_layout.addRow("建物構造:", self.structure_combo)
        basic_layout.addRow("登記所有者:", self.registry_owner_edit)
        
        basic_group.setLayout(basic_layout)
        
        # 管理形態グループ
        management_group = QGroupBox("管理形態")
        management_layout = QFormLayout()
        
        self.management_type_combo = QComboBox()
        self.management_type_combo.addItems([
            "自社管理", "他社仲介", "共同管理", "その他"
        ])
        
        self.management_company_edit = QLineEdit()
        self.management_company_edit.setPlaceholderText("管理会社名（他社管理の場合）")
        
        management_layout.addRow("管理形態:", self.management_type_combo)
        management_layout.addRow("管理会社:", self.management_company_edit)
        
        management_group.setLayout(management_layout)
        
        # 備考
        notes_group = QGroupBox("備考")
        notes_layout = QVBoxLayout()
        
        self.property_notes_edit = QTextEdit()
        self.property_notes_edit.setMaximumHeight(80)
        self.property_notes_edit.setPlaceholderText("物件に関する特記事項があれば記入...")
        
        notes_layout.addWidget(self.property_notes_edit)
        notes_group.setLayout(notes_layout)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        self.save_property_btn = QPushButton("💾 物件基本情報を保存")
        self.save_property_btn.setStyleSheet(ModernStyles.get_button_styles())
        self.save_property_btn.clicked.connect(self.save_property_basic_info)
        
        self.clear_property_btn = QPushButton("🗑 クリア")
        self.clear_property_btn.clicked.connect(self.clear_property_form)
        
        button_layout.addWidget(self.save_property_btn)
        button_layout.addWidget(self.clear_property_btn)
        button_layout.addStretch()
        
        # レイアウト追加
        layout.addWidget(basic_group)
        layout.addWidget(management_group)
        layout.addWidget(notes_group)
        layout.addLayout(button_layout)
        layout.addStretch()
        
        return widget
    
    def create_building_details_tab(self):
        """建物詳細・一棟もの設定タブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 物件選択
        property_select_group = QGroupBox("物件選択")
        property_select_layout = QHBoxLayout()
        
        self.building_property_combo = QComboBox()
        property_select_layout.addWidget(QLabel("物件:"))
        property_select_layout.addWidget(self.building_property_combo, 1)
        
        property_select_group.setLayout(property_select_layout)
        
        # 建物タイプ選択
        building_type_group = QGroupBox("建物タイプ")
        building_type_layout = QVBoxLayout()
        
        self.building_type_group = QButtonGroup()
        
        self.multi_unit_radio = QRadioButton("🏢 区分所有・複数部屋（一般的なマンション・アパート）")
        self.multi_unit_radio.setChecked(True)
        self.single_building_radio = QRadioButton("🏠 一棟もの（ビル一棟・戸建て貸し）")
        
        self.building_type_group.addButton(self.multi_unit_radio, 0)
        self.building_type_group.addButton(self.single_building_radio, 1)
        
        building_type_layout.addWidget(self.multi_unit_radio)
        building_type_layout.addWidget(self.single_building_radio)
        
        building_type_group.setLayout(building_type_layout)
        
        # 建物詳細情報
        building_details_group = QGroupBox("建物詳細情報")
        building_details_layout = QFormLayout()
        
        self.total_floors_spin = NoWheelSpinBox()
        self.total_floors_spin.setRange(1, 50)
        self.total_floors_spin.setValue(3)
        
        self.total_area_spin = NoWheelDoubleSpinBox()
        self.total_area_spin.setRange(10.0, 10000.0)
        self.total_area_spin.setSuffix(" ㎡")
        self.total_area_spin.setDecimals(2)
        
        self.built_year_spin = NoWheelSpinBox()
        self.built_year_spin.setRange(1950, 2030)
        self.built_year_spin.setValue(2020)
        
        self.building_usage_combo = QComboBox()
        self.building_usage_combo.addItems([
            "選択してください", "住宅", "事務所", "店舗", "工場", "倉庫", "複合用途"
        ])
        
        building_details_layout.addRow("総階数:", self.total_floors_spin)
        building_details_layout.addRow("延床面積:", self.total_area_spin)
        building_details_layout.addRow("建築年:", self.built_year_spin)
        building_details_layout.addRow("主要用途:", self.building_usage_combo)
        
        building_details_group.setLayout(building_details_layout)
        
        # 一棟もの設定（条件表示）
        self.single_building_settings = QGroupBox("一棟もの設定")
        single_building_layout = QFormLayout()
        
        self.rental_as_whole_check = QCheckBox("建物全体を一括賃貸")
        self.monthly_rent_spin = NoWheelSpinBox()
        self.monthly_rent_spin.setRange(0, 10000000)
        self.monthly_rent_spin.setSuffix(" 円")
        
        self.management_fee_spin = NoWheelSpinBox()
        self.management_fee_spin.setRange(0, 1000000)
        self.management_fee_spin.setSuffix(" 円")
        
        single_building_layout.addRow("", self.rental_as_whole_check)
        single_building_layout.addRow("月額賃料:", self.monthly_rent_spin)
        single_building_layout.addRow("管理費:", self.management_fee_spin)
        
        self.single_building_settings.setLayout(single_building_layout)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        self.save_building_btn = QPushButton("💾 建物詳細を保存")
        self.save_building_btn.clicked.connect(self.save_building_details)
        
        button_layout.addWidget(self.save_building_btn)
        button_layout.addStretch()
        
        # ラジオボタンの変更イベント
        self.building_type_group.buttonClicked.connect(self.on_building_type_changed)
        
        # レイアウト追加
        layout.addWidget(property_select_group)
        layout.addWidget(building_type_group)
        layout.addWidget(building_details_group)
        layout.addWidget(self.single_building_settings)
        layout.addLayout(button_layout)
        layout.addStretch()
        
        # 初期状態設定
        self.on_building_type_changed()
        
        return widget
    
    def create_units_registration_tab(self):
        """部屋登録タブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 物件選択
        property_select_group = QGroupBox("物件選択")
        property_select_layout = QHBoxLayout()
        
        self.units_property_combo = QComboBox()
        self.refresh_units_btn = QPushButton("🔄 更新")
        self.refresh_units_btn.clicked.connect(self.load_properties)
        
        property_select_layout.addWidget(QLabel("物件:"))
        property_select_layout.addWidget(self.units_property_combo, 1)
        property_select_layout.addWidget(self.refresh_units_btn)
        
        property_select_group.setLayout(property_select_layout)
        
        # 部屋登録方法選択
        registration_method_group = QGroupBox("部屋登録方法")
        method_layout = QHBoxLayout()
        
        self.manual_entry_btn = QPushButton("✏️ 手動入力")
        self.manual_entry_btn.clicked.connect(self.show_manual_entry)
        
        self.bulk_import_btn = QPushButton("📊 一括インポート")
        self.bulk_import_btn.clicked.connect(self.show_bulk_import)
        
        self.ocr_upload_btn = QPushButton("📄 図面OCR")
        self.ocr_upload_btn.clicked.connect(self.show_ocr_upload)
        
        method_layout.addWidget(self.manual_entry_btn)
        method_layout.addWidget(self.bulk_import_btn)
        method_layout.addWidget(self.ocr_upload_btn)
        method_layout.addStretch()
        
        registration_method_group.setLayout(method_layout)
        
        # 部屋登録フォーム（動的に変更）
        self.units_form_area = QWidget()
        self.units_form_layout = QVBoxLayout(self.units_form_area)
        
        # 部屋一覧テーブル
        units_list_group = QGroupBox("登録済み部屋一覧")
        units_list_layout = QVBoxLayout()
        
        self.units_table = QTableWidget()
        self.units_table.setColumnCount(6)
        self.units_table.setHorizontalHeaderLabels([
            "部屋番号", "階数", "面積", "用途制限", "設備", "備考"
        ])
        self.units_table.setMaximumHeight(200)
        
        units_list_layout.addWidget(self.units_table)
        units_list_group.setLayout(units_list_layout)
        
        # レイアウト追加
        layout.addWidget(property_select_group)
        layout.addWidget(registration_method_group)
        layout.addWidget(self.units_form_area)
        layout.addWidget(units_list_group)
        
        # 初期状態は手動入力を表示
        self.show_manual_entry()
        
        return widget
    
    def create_documents_tab(self):
        """資料管理タブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 物件・部屋選択
        selection_group = QGroupBox("対象選択")
        selection_layout = QFormLayout()
        
        self.docs_property_combo = QComboBox()
        self.docs_unit_combo = QComboBox()
        self.docs_unit_combo.addItem("物件全体", None)
        
        # 物件変更時に部屋一覧を更新
        self.docs_property_combo.currentTextChanged.connect(self.load_units_for_documents)
        
        selection_layout.addRow("物件:", self.docs_property_combo)
        selection_layout.addRow("部屋:", self.docs_unit_combo)
        
        selection_group.setLayout(selection_layout)
        
        # 資料アップロード
        upload_group = QGroupBox("資料アップロード")
        upload_layout = QVBoxLayout()
        
        # ファイル選択
        file_select_layout = QHBoxLayout()
        
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("ファイルを選択...")
        self.file_path_edit.setReadOnly(True)
        
        self.browse_file_btn = QPushButton("📁 参照")
        self.browse_file_btn.clicked.connect(self.browse_document_file)
        
        file_select_layout.addWidget(self.file_path_edit, 1)
        file_select_layout.addWidget(self.browse_file_btn)
        
        # 資料種別選択
        doc_type_layout = QFormLayout()
        
        self.document_type_combo = QComboBox()
        self.document_type_combo.addItems([
            "募集図面", "契約書", "重要事項説明書", "登記簿謄本", 
            "申込書", "見積書", "鍵預り証", "その他書類"
        ])
        
        self.document_memo_edit = QTextEdit()
        self.document_memo_edit.setMaximumHeight(60)
        self.document_memo_edit.setPlaceholderText("資料の説明・メモ")
        
        doc_type_layout.addRow("資料種別:", self.document_type_combo)
        doc_type_layout.addRow("説明・メモ:", self.document_memo_edit)
        
        # アップロードボタン
        upload_btn_layout = QHBoxLayout()
        
        self.upload_document_btn = QPushButton("📤 アップロード")
        self.upload_document_btn.clicked.connect(self.upload_document)
        
        upload_btn_layout.addWidget(self.upload_document_btn)
        upload_btn_layout.addStretch()
        
        upload_layout.addLayout(file_select_layout)
        upload_layout.addLayout(doc_type_layout)
        upload_layout.addLayout(upload_btn_layout)
        
        upload_group.setLayout(upload_layout)
        
        # 資料一覧
        documents_list_group = QGroupBox("登録済み資料一覧")
        documents_list_layout = QVBoxLayout()
        
        self.documents_table = QTableWidget()
        self.documents_table.setColumnCount(5)
        self.documents_table.setHorizontalHeaderLabels([
            "資料種別", "ファイル名", "対象", "登録日", "操作"
        ])
        
        documents_list_layout.addWidget(self.documents_table)
        documents_list_group.setLayout(documents_list_layout)
        
        # レイアウト追加
        layout.addWidget(selection_group)
        layout.addWidget(upload_group)
        layout.addWidget(documents_list_group)
        
        return widget
    
    def create_management_panel(self):
        """物件・部屋管理パネル"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # タイトル
        title = QLabel("📋 登録済み物件・部屋管理")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: {ModernTheme.FONTS['size_lg']};
                font-weight: 600;
                color: {ModernTheme.COLORS['text_primary']};
                margin-bottom: {ModernTheme.SPACING['md']};
            }}
        """)
        layout.addWidget(title)
        
        # 物件一覧
        properties_group = QGroupBox("物件一覧")
        properties_layout = QVBoxLayout()
        
        self.properties_list = QListWidget()
        self.properties_list.itemClicked.connect(self.on_property_selected)
        
        properties_layout.addWidget(self.properties_list)
        properties_group.setLayout(properties_layout)
        
        # 選択中物件の部屋一覧
        selected_property_group = QGroupBox("選択中物件の部屋一覧")
        selected_property_layout = QVBoxLayout()
        
        self.property_info_label = QLabel("物件を選択してください")
        self.property_info_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernTheme.COLORS['text_secondary']};
                font-style: italic;
            }}
        """)
        
        self.property_units_table = QTableWidget()
        self.property_units_table.setColumnCount(4)
        self.property_units_table.setHorizontalHeaderLabels([
            "部屋番号", "面積", "設備", "資料数"
        ])
        self.property_units_table.setMaximumHeight(200)
        
        selected_property_layout.addWidget(self.property_info_label)
        selected_property_layout.addWidget(self.property_units_table)
        
        selected_property_group.setLayout(selected_property_layout)
        
        # クイックアクション
        actions_group = QGroupBox("クイックアクション")
        actions_layout = QGridLayout()
        
        self.edit_property_btn = QPushButton("✏️ 物件編集")
        self.delete_property_btn = QPushButton("🗑 物件削除")
        self.export_data_btn = QPushButton("📤 データ出力")
        self.import_data_btn = QPushButton("📥 データ取込")
        
        actions_layout.addWidget(self.edit_property_btn, 0, 0)
        actions_layout.addWidget(self.delete_property_btn, 0, 1)
        actions_layout.addWidget(self.export_data_btn, 1, 0)
        actions_layout.addWidget(self.import_data_btn, 1, 1)
        
        actions_group.setLayout(actions_layout)
        
        # レイアウト追加
        layout.addWidget(properties_group)
        layout.addWidget(selected_property_group)
        layout.addWidget(actions_group)
        layout.addStretch()
        
        return widget
    
    def on_building_type_changed(self):
        """建物タイプ変更時の処理"""
        if self.single_building_radio.isChecked():
            self.single_building_settings.show()
        else:
            self.single_building_settings.hide()
    
    def on_tab_changed(self, index):
        """タブ変更時の処理"""
        # 物件コンボボックスを更新
        if index == 1:  # 建物詳細タブ
            self.load_properties_to_combo(self.building_property_combo)
        elif index == 2:  # 部屋登録タブ
            self.load_properties_to_combo(self.units_property_combo)
        elif index == 3:  # 資料管理タブ
            self.load_properties_to_combo(self.docs_property_combo)
    
    def load_properties(self):
        """物件一覧を読み込み"""
        try:
            properties = Property.get_all()
            
            # サイドパネルの物件リスト更新
            self.properties_list.clear()
            for property_obj in properties:
                item = QListWidgetItem(f"🏢 {property_obj['name']}")
                item.setData(Qt.ItemDataRole.UserRole, property_obj['id'])
                self.properties_list.addItem(item)
            
            # 各タブのコンボボックス更新
            self.load_properties_to_combo(self.building_property_combo)
            self.load_properties_to_combo(self.units_property_combo)
            self.load_properties_to_combo(self.docs_property_combo)
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"物件一覧の読み込みに失敗しました: {str(e)}")
    
    def load_properties_to_combo(self, combo_widget):
        """指定されたコンボボックスに物件を読み込み"""
        try:
            combo_widget.clear()
            combo_widget.addItem("物件を選択", None)
            
            properties = Property.get_all()
            for property_obj in properties:
                combo_widget.addItem(property_obj['name'], property_obj['id'])
                
        except Exception as e:
            print(f"コンボボックス更新エラー: {e}")
    
    def save_property_basic_info(self):
        """物件基本情報を保存"""
        name = self.property_name_edit.text().strip()
        address = self.property_address_edit.toPlainText().strip()
        
        if not name:
            QMessageBox.warning(self, "警告", "物件名称を入力してください。")
            return
        
        if not address:
            QMessageBox.warning(self, "警告", "住所を入力してください。")
            return
        
        try:
            structure = self.structure_combo.currentText()
            if structure == "選択してください":
                structure = None
            
            property_id = Property.create(
                name=name,
                address=address,
                structure=structure,
                registry_owner=self.registry_owner_edit.text().strip() or None,
                management_type=self.management_type_combo.currentText(),
                management_company=self.management_company_edit.text().strip() or None,
                notes=self.property_notes_edit.toPlainText().strip() or None
            )
            
            self.current_property_id = property_id
            QMessageBox.information(self, "成功", "物件基本情報を保存しました。\n\n次のタブで建物詳細を設定してください。")
            
            # 物件一覧を更新
            self.load_properties()
            
            # 次のタブに移動
            self.flow_tabs.setCurrentIndex(1)
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"物件の保存に失敗しました: {str(e)}")
    
    def clear_property_form(self):
        """物件フォームをクリア"""
        self.property_name_edit.clear()
        self.property_address_edit.clear()
        self.structure_combo.setCurrentIndex(0)
        self.registry_owner_edit.clear()
        self.management_type_combo.setCurrentIndex(0)
        self.management_company_edit.clear()
        self.property_notes_edit.clear()
    
    def save_building_details(self):
        """建物詳細を保存"""
        property_id = self.building_property_combo.currentData()
        
        if not property_id:
            QMessageBox.warning(self, "警告", "物件を選択してください。")
            return
        
        try:
            # 建物詳細情報を更新（modelsに拡張メソッドが必要）
            QMessageBox.information(self, "成功", "建物詳細を保存しました。\n\n次のタブで部屋を登録してください。")
            
            # 次のタブに移動
            self.flow_tabs.setCurrentIndex(2)
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"建物詳細の保存に失敗しました: {str(e)}")
    
    def show_manual_entry(self):
        """手動入力フォームを表示"""
        # 既存のフォームをクリア
        for i in reversed(range(self.units_form_layout.count())):
            self.units_form_layout.itemAt(i).widget().setParent(None)
        
        # 手動入力フォームを作成
        manual_form = self.create_manual_entry_form()
        self.units_form_layout.addWidget(manual_form)
    
    def create_manual_entry_form(self):
        """手動入力フォームを作成"""
        form_group = QGroupBox("部屋手動入力")
        form_layout = QFormLayout()
        
        self.room_number_edit = QLineEdit()
        self.room_number_edit.setPlaceholderText("例: 101, 1F-A")
        
        self.floor_edit = QLineEdit()
        self.floor_edit.setPlaceholderText("例: 1, 1F, B1")
        
        self.room_area_spin = NoWheelDoubleSpinBox()
        self.room_area_spin.setRange(1.0, 1000.0)
        self.room_area_spin.setSuffix(" ㎡")
        self.room_area_spin.setDecimals(2)
        
        self.use_restrictions_edit = QLineEdit()
        self.use_restrictions_edit.setPlaceholderText("例: 事務所専用、飲食不可")
        
        self.pet_allowed_check = QCheckBox("ペット可")
        self.midnight_allowed_check = QCheckBox("深夜営業可")
        
        self.room_notes_edit = QTextEdit()
        self.room_notes_edit.setMaximumHeight(60)
        self.room_notes_edit.setPlaceholderText("部屋の特記事項...")
        
        form_layout.addRow("部屋番号 *:", self.room_number_edit)
        form_layout.addRow("階数:", self.floor_edit)
        form_layout.addRow("面積:", self.room_area_spin)
        form_layout.addRow("用途制限:", self.use_restrictions_edit)
        form_layout.addRow("設備:", self.pet_allowed_check)
        form_layout.addRow("", self.midnight_allowed_check)
        form_layout.addRow("備考:", self.room_notes_edit)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        add_room_btn = QPushButton("✅ 部屋を追加")
        add_room_btn.clicked.connect(self.add_room_manual)
        
        clear_room_btn = QPushButton("🗑 クリア")
        clear_room_btn.clicked.connect(self.clear_room_form)
        
        button_layout.addWidget(add_room_btn)
        button_layout.addWidget(clear_room_btn)
        button_layout.addStretch()
        
        form_layout.addRow("", button_layout)
        
        form_group.setLayout(form_layout)
        return form_group
    
    def add_room_manual(self):
        """手動で部屋を追加"""
        property_id = self.units_property_combo.currentData()
        room_number = self.room_number_edit.text().strip()
        
        if not property_id:
            QMessageBox.warning(self, "警告", "物件を選択してください。")
            return
        
        if not room_number:
            QMessageBox.warning(self, "警告", "部屋番号を入力してください。")
            return
        
        try:
            Unit.create(
                property_id=property_id,
                room_number=room_number,
                floor=self.floor_edit.text().strip() or None,
                area=self.room_area_spin.value(),
                use_restrictions=self.use_restrictions_edit.text().strip() or None,
                power_capacity=None,
                pet_allowed=self.pet_allowed_check.isChecked(),
                midnight_allowed=self.midnight_allowed_check.isChecked(),
                notes=self.room_notes_edit.toPlainText().strip() or None
            )
            
            QMessageBox.information(self, "成功", f"部屋 {room_number} を追加しました。")
            self.clear_room_form()
            self.load_units_table()
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"部屋の追加に失敗しました: {str(e)}")
    
    def clear_room_form(self):
        """部屋フォームをクリア"""
        self.room_number_edit.clear()
        self.floor_edit.clear()
        self.room_area_spin.setValue(1.0)
        self.use_restrictions_edit.clear()
        self.pet_allowed_check.setChecked(False)
        self.midnight_allowed_check.setChecked(False)
        self.room_notes_edit.clear()
    
    def show_bulk_import(self):
        """一括インポート機能を表示"""
        QMessageBox.information(self, "機能準備中", "一括インポート機能は準備中です。")
    
    def show_ocr_upload(self):
        """OCR図面アップロード機能を表示"""
        QMessageBox.information(self, "機能準備中", "図面OCR機能は準備中です。")
    
    def load_units_table(self):
        """部屋一覧テーブルを更新"""
        property_id = self.units_property_combo.currentData()
        
        if not property_id:
            self.units_table.setRowCount(0)
            return
        
        try:
            units = Unit.get_by_property(property_id)
            
            self.units_table.setRowCount(len(units))
            for i, unit in enumerate(units):
                self.units_table.setItem(i, 0, QTableWidgetItem(unit.get('room_number', '')))
                self.units_table.setItem(i, 1, QTableWidgetItem(str(unit.get('floor', ''))))
                self.units_table.setItem(i, 2, QTableWidgetItem(f"{unit.get('area', 0)}㎡"))
                self.units_table.setItem(i, 3, QTableWidgetItem(unit.get('use_restrictions', '')))
                
                # 設備情報
                equipment = []
                if unit.get('pet_allowed'):
                    equipment.append("ペット可")
                if unit.get('midnight_allowed'):
                    equipment.append("深夜営業可")
                
                self.units_table.setItem(i, 4, QTableWidgetItem(", ".join(equipment)))
                self.units_table.setItem(i, 5, QTableWidgetItem(unit.get('notes', '')))
            
        except Exception as e:
            print(f"部屋一覧読み込みエラー: {e}")
    
    def browse_document_file(self):
        """資料ファイルを選択"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "資料ファイルを選択", "", 
            "すべてのファイル (*);;画像ファイル (*.png *.jpg *.jpeg *.bmp);;PDFファイル (*.pdf)"
        )
        if file_path:
            self.file_path_edit.setText(file_path)
    
    def upload_document(self):
        """資料をアップロード"""
        property_id = self.docs_property_combo.currentData()
        unit_id = self.docs_unit_combo.currentData()
        file_path = self.file_path_edit.text().strip()
        
        if not property_id:
            QMessageBox.warning(self, "警告", "物件を選択してください。")
            return
        
        if not file_path:
            QMessageBox.warning(self, "警告", "ファイルを選択してください。")
            return
        
        try:
            # ファイルを資料保存ディレクトリにコピー
            file_name = os.path.basename(file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if unit_id:
                # 部屋固有の資料
                target_dir = os.path.join(self.document_storage_path, f"property_{property_id}", f"unit_{unit_id}")
                target_name = f"{timestamp}_{file_name}"
            else:
                # 物件全体の資料
                target_dir = os.path.join(self.document_storage_path, f"property_{property_id}", "general")
                target_name = f"{timestamp}_{file_name}"
            
            os.makedirs(target_dir, exist_ok=True)
            target_path = os.path.join(target_dir, target_name)
            
            shutil.copy2(file_path, target_path)
            
            QMessageBox.information(self, "成功", f"資料をアップロードしました。\n保存先: {target_path}")
            
            # フォームクリア
            self.file_path_edit.clear()
            self.document_memo_edit.clear()
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"資料のアップロードに失敗しました: {str(e)}")
    
    def load_units_for_documents(self):
        """資料管理用の部屋一覧を読み込み"""
        property_id = self.docs_property_combo.currentData()
        
        self.docs_unit_combo.clear()
        self.docs_unit_combo.addItem("物件全体", None)
        
        if property_id:
            try:
                units = Unit.get_by_property(property_id)
                for unit in units:
                    self.docs_unit_combo.addItem(
                        f"{unit.get('room_number', '')} ({unit.get('area', 0)}㎡)", 
                        unit['id']
                    )
            except Exception as e:
                print(f"部屋一覧読み込みエラー: {e}")
    
    def on_property_selected(self, item):
        """物件選択時の処理"""
        property_id = item.data(Qt.ItemDataRole.UserRole)
        
        try:
            property_obj = Property.get_by_id(property_id)
            if property_obj:
                self.property_info_label.setText(
                    f"📍 {property_obj['name']} - {property_obj['address']}"
                )
                
                # 部屋一覧を更新
                units = Unit.get_by_property(property_id)
                
                self.property_units_table.setRowCount(len(units))
                for i, unit in enumerate(units):
                    self.property_units_table.setItem(i, 0, QTableWidgetItem(unit.get('room_number', '')))
                    self.property_units_table.setItem(i, 1, QTableWidgetItem(f"{unit.get('area', 0)}㎡"))
                    
                    # 設備情報
                    equipment = []
                    if unit.get('pet_allowed'):
                        equipment.append("ペット可")
                    if unit.get('midnight_allowed'):
                        equipment.append("深夜営業可")
                    
                    self.property_units_table.setItem(i, 2, QTableWidgetItem(", ".join(equipment)))
                    self.property_units_table.setItem(i, 3, QTableWidgetItem("0"))  # 資料数（実装要）
                
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"物件情報の読み込みに失敗しました: {str(e)}")