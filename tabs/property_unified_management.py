#!/usr/bin/env python3
"""
物件統合管理タブ - 登録から管理まで一元化
物件・部屋・資料のすべてを一箇所で管理
"""

import os
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QGroupBox, QFormLayout, QLabel, QLineEdit, QTextEdit,
                             QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
                             QCheckBox, QTableWidget, QTableWidgetItem,
                             QFileDialog, QMessageBox, QListWidget, QListWidgetItem,
                             QSplitter, QFrame, QGridLayout, QButtonGroup, 
                             QRadioButton, QTreeWidget, QTreeWidgetItem,
                             QStackedWidget, QScrollArea, QDialog, QDialogButtonBox,
                             QHeaderView)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QIcon
import sys
import os
# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Property, Unit, Customer
from ui.ui_styles import ModernStyles
from modern_ui_system import ModernUITheme

# UI Helper関数
from ui.ui_helpers import make_page_container, make_scroll_page

class PropertyUnifiedManagement(QWidget):
    """物件統合管理 - 登録から管理まで一元化"""
    
    def __init__(self):
        super().__init__()
        self.current_property_id = None
        self.current_unit_id = None
        self.current_property_data = None
        self.current_unit_data = None
        self.current_selection_type = None  # 'property', 'unit', or None
        self.document_storage_path = "property_documents"
        self.ensure_document_directory()
        self.init_ui()
        
    def ensure_document_directory(self):
        """資料保存ディレクトリを確保"""
        if not os.path.exists(self.document_storage_path):
            os.makedirs(self.document_storage_path)
    
    def get_document_count(self, property_id, unit_id=None):
        """指定された物件・部屋の資料数を取得"""
        try:
            if unit_id:
                # 部屋固有の資料ディレクトリ
                docs_dir = os.path.join(self.document_storage_path, f"property_{property_id}", f"unit_{unit_id}")
            else:
                # 物件全体の資料ディレクトリ
                docs_dir = os.path.join(self.document_storage_path, f"property_{property_id}", "general")
            
            if not os.path.exists(docs_dir):
                return 0
            
            # ファイル数をカウント
            count = 0
            for item in os.listdir(docs_dir):
                if os.path.isfile(os.path.join(docs_dir, item)):
                    count += 1
            
            return count
            
        except Exception as e:
            print(f"資料数取得エラー: {e}")
            return 0
    
    def clear_selection(self):
        """選択状態をクリア"""
        self.current_property_id = None
        self.current_unit_id = None
        self.current_property_data = None
        self.current_unit_data = None
        self.current_selection_type = None
        self.update_action_buttons('none', None)
        self.detail_stack.setCurrentIndex(0)  # ウェルカム画面
    
    def set_property_selection(self, property_id, property_data):
        """物件選択状態を設定"""
        self.current_property_id = property_id
        self.current_unit_id = None
        self.current_property_data = property_data
        self.current_unit_data = None
        self.current_selection_type = 'property'
        self.update_action_buttons('property', property_id)
    
        # 詳細表示を更新
        self.update_property_detail_display()
    
    def set_unit_selection(self, unit_id, unit_data, property_id):
        """部屋選択状態を設定"""
        self.current_property_id = property_id
        self.current_unit_id = unit_id
        self.current_unit_data = unit_data
        self.current_selection_type = 'unit'
        # 物件データも更新
        try:
            self.current_property_data = Property.get_by_id(property_id)
        except:
            self.current_property_data = None
        self.update_action_buttons('unit', unit_id, property_id)
        
        # 詳細表示を更新
        self.update_unit_detail_display()
    
    def init_ui(self):
        """UIを初期化"""
        # ページコンテナを作成
        container, layout = make_page_container()
        
        # 1. ウェルカムメッセージ（最上部）
        welcome_group = QGroupBox("物件統合管理へようこそ")
        welcome_layout = QVBoxLayout()
        welcome_label = QLabel("物件・部屋の統合管理システムです。物件の登録、更新、登記簿管理、階層詳細まで一元管理できます。")
        welcome_label.setWordWrap(True)
        welcome_label.setStyleSheet(f"""
            QLabel {{
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_lg']};
                color: {ModernUITheme.COLORS['primary']};
                padding: {ModernUITheme.SPACING['md']};
            }}
        """)
        welcome_layout.addWidget(welcome_label)
        welcome_group.setLayout(welcome_layout)
        layout.addWidget(welcome_group)
        
        # 2. クイックアクション（2番目）
        quick_action_group = QGroupBox("クイックアクション")
        quick_action_layout = QHBoxLayout()
        
        new_property_btn = QPushButton("➕ 新規物件登録")
        new_property_btn.setStyleSheet(ModernStyles.get_button_styles())
        new_property_btn.clicked.connect(self.show_new_property_form)
        
        refresh_btn = QPushButton("🔄 更新")
        refresh_btn.setStyleSheet(ModernStyles.get_button_styles())
        refresh_btn.clicked.connect(self.load_property_tree)
        
        view_details_btn = QPushButton("👁️ 詳細表示")
        view_details_btn.setStyleSheet(ModernStyles.get_button_styles())
        view_details_btn.clicked.connect(self.show_property_details)
        
        quick_action_layout.addWidget(new_property_btn)
        quick_action_layout.addWidget(refresh_btn)
        quick_action_layout.addWidget(view_details_btn)
        quick_action_layout.addStretch()
        
        quick_action_group.setLayout(quick_action_layout)
        layout.addWidget(quick_action_group)
        
        # 3. 物件一覧（3番目）
        property_list_group = QGroupBox("物件一覧")
        property_list_layout = QVBoxLayout()
        
        # 検索・フィルター機能
        search_layout = QHBoxLayout()
        search_label = QLabel("検索:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("物件名、住所で検索...")
        self.search_edit.textChanged.connect(self.filter_properties)
        
        filter_combo = QComboBox()
        filter_combo.addItems(["すべて", "自社管理", "他社仲介", "共同管理"])
        filter_combo.currentTextChanged.connect(self.filter_properties)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_edit, 1)
        search_layout.addWidget(QLabel("管理形態:"))
        search_layout.addWidget(filter_combo)
        
        property_list_layout.addLayout(search_layout)
        
        # 物件ツリー（高さを調整）
        self.property_tree = QTreeWidget()
        self.property_tree.setHeaderHidden(True)
        self.property_tree.itemClicked.connect(self.on_tree_item_clicked)
        self.property_tree.setMinimumHeight(300)
        
        # ツリーのスタイル
        self.property_tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {ModernUITheme.COLORS['bg_primary']};
                border: 1px solid {ModernUITheme.COLORS['border']};
                border-radius: {ModernUITheme.RADIUS['base']};
                padding: {ModernUITheme.SPACING['xs']};
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_sm']};
            }}
            QTreeWidget::item {{
                padding: {ModernUITheme.SPACING['xs']} {ModernUITheme.SPACING['sm']};
                border-radius: {ModernUITheme.RADIUS['sm']};
                margin: 1px;
            }}
            QTreeWidget::item:hover {{
                background-color: {ModernUITheme.COLORS['primary_lighter']};
            }}
            QTreeWidget::item:selected {{
                background-color: {ModernUITheme.COLORS['primary']};
                color: white;
            }}
        """)
        
        property_list_layout.addWidget(self.property_tree)
        
        # アクションボタンを物件一覧の下に追加
        action_buttons_layout = QHBoxLayout()
        
        # 物件関連アクション
        self.edit_property_btn = QPushButton("✏️ 物件編集")
        self.edit_property_btn.clicked.connect(self.edit_current_property)
        self.edit_property_btn.setEnabled(False)
        self.edit_property_btn.setStyleSheet(ModernStyles.get_button_styles())
        
        self.delete_property_btn = QPushButton("🗑 物件削除")
        self.delete_property_btn.clicked.connect(self.delete_current_property)
        self.delete_property_btn.setEnabled(False)
        self.delete_property_btn.setStyleSheet(ModernStyles.get_button_styles())
        
        # 部屋関連アクション
        self.add_unit_btn = QPushButton("➕ 部屋追加")
        self.add_unit_btn.clicked.connect(self.show_add_unit_form)
        self.add_unit_btn.setEnabled(False)
        self.add_unit_btn.setStyleSheet(ModernStyles.get_button_styles())
        
        self.edit_unit_btn = QPushButton("✏️ 部屋編集")
        self.edit_unit_btn.clicked.connect(self.edit_current_unit)
        self.edit_unit_btn.setEnabled(False)
        self.edit_unit_btn.setStyleSheet(ModernStyles.get_button_styles())
        
        self.delete_unit_btn = QPushButton("🗑 部屋削除")
        self.delete_unit_btn.clicked.connect(self.delete_current_unit)
        self.delete_unit_btn.setEnabled(False)
        self.delete_unit_btn.setStyleSheet(ModernStyles.get_button_styles())
        
        # 資料関連アクション
        self.upload_docs_btn = QPushButton("📤 資料アップロード")
        self.upload_docs_btn.clicked.connect(self.show_upload_dialog)
        self.upload_docs_btn.setEnabled(False)
        self.upload_docs_btn.setStyleSheet(ModernStyles.get_button_styles())
        
        self.view_docs_btn = QPushButton("📋 資料一覧")
        self.view_docs_btn.clicked.connect(self.show_documents_list)
        self.view_docs_btn.setEnabled(False)
        self.view_docs_btn.setStyleSheet(ModernStyles.get_button_styles())
        
        action_buttons_layout.addWidget(self.edit_property_btn)
        action_buttons_layout.addWidget(self.delete_property_btn)
        action_buttons_layout.addWidget(self.add_unit_btn)
        action_buttons_layout.addWidget(self.edit_unit_btn)
        action_buttons_layout.addWidget(self.delete_unit_btn)
        action_buttons_layout.addWidget(self.upload_docs_btn)
        action_buttons_layout.addWidget(self.view_docs_btn)
        action_buttons_layout.addStretch()
        
        property_list_layout.addLayout(action_buttons_layout)
        property_list_group.setLayout(property_list_layout)
        layout.addWidget(property_list_group)
        
        # 4. 詳細表示・編集エリア（4番目）
        detail_group = QGroupBox("詳細管理")
        detail_layout = QVBoxLayout()
        
        # スタックウィジェット（表示内容を切り替え）
        self.detail_stack = QStackedWidget()
        
        # 1. ウェルカム画面
        welcome_page = self.create_welcome_page()
        self.detail_stack.addWidget(welcome_page)
        
        # 2. 物件詳細表示・編集
        property_detail_page = self.create_property_detail_page()
        self.detail_stack.addWidget(property_detail_page)
        
        # 3. 部屋詳細表示・編集
        unit_detail_page = self.create_unit_detail_page()
        self.detail_stack.addWidget(unit_detail_page)
        
        # 4. 新規物件登録フォーム
        new_property_page = self.create_new_property_page()
        self.detail_stack.addWidget(new_property_page)
        
        detail_layout.addWidget(self.detail_stack)
        detail_group.setLayout(detail_layout)
        layout.addWidget(detail_group)
        
        # 初期状態はウェルカム画面
        self.detail_stack.setCurrentIndex(0)
        
        # スクロール可能ページとして設定
        scroll_page = make_scroll_page(container)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(scroll_page)
        
        # 初期データ読み込み
        self.load_property_tree()
        
        # アクションボタンの初期化
        self.init_action_buttons()
    
    def init_action_buttons(self):
        """アクションボタンを初期化"""
        # このメソッドは既に上で実装済み
        pass
    
    def filter_properties(self):
        """物件一覧をフィルタリング"""
        search_text = self.search_edit.text().lower()
        
        # 物件ツリーの全アイテムをループ
        for i in range(self.property_tree.topLevelItemCount()):
            property_item = self.property_tree.topLevelItem(i)
            property_item.setHidden(False)  # 一旦表示
            
            # 物件名でフィルタリング
            if search_text:
                property_name = property_item.text(0).lower()
                if search_text not in property_name:
                    property_item.setHidden(True)
                    continue
            
            # 部屋アイテムもチェック
            for j in range(property_item.childCount()):
                unit_item = property_item.child(j)
                unit_item.setHidden(False)  # 一旦表示
                
                if search_text:
                    unit_name = unit_item.text(0).lower()
                    if search_text not in unit_name:
                        unit_item.setHidden(True)
    
    def show_property_details(self):
        """物件・部屋の詳細を表示"""
        try:
            if self.current_selection_type == 'property':
                # 物件詳細を表示
                self.detail_stack.setCurrentIndex(1)  # 物件詳細ページ
                # 物件詳細表示を更新
                self.update_property_detail_display()
                
            elif self.current_selection_type == 'unit':
                # 部屋詳細を表示
                self.detail_stack.setCurrentIndex(2)  # 部屋詳細ページ
                # 部屋詳細表示を更新
                self.update_unit_detail_display()
                
            else:
                # ウェルカム画面を表示
                self.detail_stack.setCurrentIndex(0)
                
        except Exception as e:
            print(f"詳細表示切り替えエラー: {str(e)}")
            self.detail_stack.setCurrentIndex(0)  # エラー時はウェルカム画面
    
    def create_welcome_page(self):
        """ウェルカムページ"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # アイコン
        icon_label = QLabel("🏢")
        icon_label.setStyleSheet(f"font-size: {ModernUITheme.TYPOGRAPHY['font_size_4xl']};")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # メッセージ
        message_label = QLabel("物件統合管理へようこそ")
        message_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernUITheme.COLORS['text_primary']};
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_xl']};
                font-weight: 600;
                margin: {ModernUITheme.SPACING['sm']} 0;
            }}
        """)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 説明
        desc_label = QLabel("左の物件一覧から物件を選択するか、\n「新規物件登録」で物件を追加してください。")
        desc_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernUITheme.COLORS['text_secondary']};
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_base']};
                text-align: center;
            }}
        """)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(icon_label)
        layout.addWidget(message_label)
        layout.addWidget(desc_label)
        
        return page
    
    def create_property_detail_page(self):
        """物件詳細ページを作成"""
        page = make_page_container()[0]
        layout = page.layout()
        
        # 物件情報表示
        info_group = QGroupBox("物件情報")
        info_layout = QFormLayout()
        
        self.property_name_label = QLabel()
        self.property_address_label = QLabel()
        self.property_structure_label = QLabel()
        self.property_owner_label = QLabel()
        self.property_management_label = QLabel()
        self.property_notes_label = QLabel()
        
        info_layout.addRow("物件名称:", self.property_name_label)
        info_layout.addRow("住所:", self.property_address_label)
        info_layout.addRow("建物構造:", self.property_structure_label)
        info_layout.addRow("登記所有者:", self.property_owner_label)
        info_layout.addRow("管理形態:", self.property_management_label)
        info_layout.addRow("備考:", self.property_notes_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # 部屋一覧
        rooms_group = QGroupBox("部屋一覧")
        rooms_layout = QVBoxLayout()
        
        self.property_units_table = QTableWidget()
        self.property_units_table.setColumnCount(5)
        self.property_units_table.setHorizontalHeaderLabels([
            "部屋番号", "階数", "面積", "用途制限", "備考"
        ])
        
        rooms_layout.addWidget(self.property_units_table)
        rooms_group.setLayout(rooms_layout)
        layout.addWidget(rooms_group)
        
        # 物件情報を更新
        self.update_property_detail_display()
        
        return page
    
    def update_property_detail_display(self):
        """物件詳細表示を更新"""
        try:
            if not self.current_property_data:
                return
            
            # 基本情報を表示
            self.property_name_label.setText(self.current_property_data.get('name', ''))
            self.property_address_label.setText(self.current_property_data.get('address', ''))
            self.property_structure_label.setText(self.current_property_data.get('structure', ''))
            self.property_owner_label.setText(self.current_property_data.get('registry_owner', ''))
            self.property_management_label.setText(self.current_property_data.get('management_type', ''))
            self.property_notes_label.setText(self.current_property_data.get('notes', ''))
            
            # 部屋一覧を更新
            self.load_property_units_display()
            
        except Exception as e:
            print(f"物件詳細表示更新エラー: {str(e)}")
    
    def load_property_units_display(self):
        """物件の部屋一覧を表示用テーブルに読み込み"""
        try:
            if not self.current_property_id:
                self.property_units_table.setRowCount(0)
                return
            
            units = Unit.get_by_property(self.current_property_id)
            
            self.property_units_table.setRowCount(len(units))
            for i, unit in enumerate(units):
                self.property_units_table.setItem(i, 0, QTableWidgetItem(unit.get('room_number', '')))
                self.property_units_table.setItem(i, 1, QTableWidgetItem(str(unit.get('floor', ''))))
                self.property_units_table.setItem(i, 2, QTableWidgetItem(f"{unit.get('area', 0)}㎡"))
                self.property_units_table.setItem(i, 3, QTableWidgetItem(unit.get('use_restrictions', '')))
                self.property_units_table.setItem(i, 4, QTableWidgetItem(unit.get('notes', '')))
            
        except Exception as e:
            print(f"部屋一覧表示読み込みエラー: {str(e)}")
            self.property_units_table.setRowCount(0)
    
    def create_unit_detail_page(self):
        """部屋詳細ページを作成"""
        page = make_page_container()[0]
        layout = page.layout()
        
        # 部屋情報表示
        info_group = QGroupBox("部屋情報")
        info_layout = QFormLayout()
        
        self.unit_room_number_label = QLabel()
        self.unit_floor_label = QLabel()
        self.unit_area_label = QLabel()
        self.unit_restrictions_label = QLabel()
        self.unit_power_label = QLabel()
        self.unit_pet_label = QLabel()
        self.unit_midnight_label = QLabel()
        self.unit_notes_label = QLabel()
        
        info_layout.addRow("部屋番号:", self.unit_room_number_label)
        info_layout.addRow("階数:", self.unit_floor_label)
        info_layout.addRow("面積:", self.unit_area_label)
        info_layout.addRow("用途制限:", self.unit_restrictions_label)
        info_layout.addRow("電力容量:", self.unit_power_label)
        info_layout.addRow("ペット可:", self.unit_pet_label)
        info_layout.addRow("深夜営業可:", self.unit_midnight_label)
        info_layout.addRow("備考:", self.unit_notes_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # 物件情報
        property_group = QGroupBox("所属物件")
        property_layout = QFormLayout()
        
        self.unit_property_name_label = QLabel()
        self.unit_property_address_label = QLabel()
        
        property_layout.addRow("物件名称:", self.unit_property_name_label)
        property_layout.addRow("住所:", self.unit_property_address_label)
        
        property_group.setLayout(property_layout)
        layout.addWidget(property_group)
        
        # 部屋情報を更新
        self.update_unit_detail_display()
        
        return page
    
    def update_unit_detail_display(self):
        """部屋詳細表示を更新"""
        try:
            if not self.current_unit_data:
                return
            
            # 基本情報を表示
            self.unit_room_number_label.setText(self.current_unit_data.get('room_number', ''))
            self.unit_floor_label.setText(str(self.current_unit_data.get('floor', '')))
            self.unit_area_label.setText(f"{self.current_unit_data.get('area', 0)}㎡")
            self.unit_restrictions_label.setText(self.current_unit_data.get('use_restrictions', ''))
            self.unit_power_label.setText(self.current_unit_data.get('power_capacity', ''))
            self.unit_pet_label.setText("可" if self.current_unit_data.get('pet_allowed') else "不可")
            self.unit_midnight_label.setText("可" if self.current_unit_data.get('midnight_allowed') else "不可")
            self.unit_notes_label.setText(self.current_unit_data.get('notes', ''))
            
            # 物件情報を表示
            if self.current_property_data:
                self.unit_property_name_label.setText(self.current_property_data.get('name', ''))
                self.unit_property_address_label.setText(self.current_property_data.get('address', ''))
            
        except Exception as e:
            print(f"部屋詳細表示更新エラー: {str(e)}")
    
    def create_new_property_page(self):
        """新規物件登録ページを作成"""
        page = make_page_container()[0]
        layout = page.layout()
        
        # ヘッダー
        header = QLabel("🆕 新規物件登録")
        header.setStyleSheet(f"""
            QLabel {{
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_xl']};
                font-weight: 600;
                color: {ModernUITheme.COLORS['text_primary']};
                margin-bottom: {ModernUITheme.SPACING['sm']};
            }}
        """)
        layout.addWidget(header)
        
        # フォーム
        form_frame = QFrame()
        form_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {ModernUITheme.COLORS['bg_primary']};
                border: 1px solid {ModernUITheme.COLORS['border']};
                border-radius: {ModernUITheme.RADIUS['lg']};
                padding: {ModernUITheme.SPACING['sm']};
            }}
        """)
        form_layout = QFormLayout(form_frame)
        
        # 入力フィールド
        self.new_property_name = QLineEdit()
        self.new_property_name.setPlaceholderText("例: ○○マンション")
        
        self.new_property_address = QTextEdit()
        self.new_property_address.setMaximumHeight(60)
        self.new_property_address.setPlaceholderText("例: 東京都渋谷区...")
        
        self.new_property_structure = QComboBox()
        self.new_property_structure.addItems([
            "選択してください", "RC造", "SRC造", "S造", "木造", "軽量鉄骨造", "その他"
        ])
        
        self.new_property_owner = QLineEdit()
        self.new_property_owner.setPlaceholderText("登記簿上の所有者名")
        
        self.new_management_type = QComboBox()
        self.new_management_type.addItems([
            "自社管理", "他社仲介", "共同管理", "その他"
        ])
        
        self.new_management_company = QLineEdit()
        self.new_management_company.setPlaceholderText("管理会社名（他社管理の場合）")
        
        self.new_property_notes = QTextEdit()
        self.new_property_notes.setMaximumHeight(60)
        self.new_property_notes.setPlaceholderText("物件に関する特記事項...")
        
        # 物件種別選択
        property_type_layout = QHBoxLayout()
        self.new_property_type_group = QButtonGroup()
        
        self.multi_unit_radio = QRadioButton("🏢 区分所有（マンション・アパート）")
        self.multi_unit_radio.setChecked(True)
        self.single_building_radio = QRadioButton("🏠 一棟もの（ビル一棟・戸建て）")
        
        self.new_property_type_group.addButton(self.multi_unit_radio, 0)
        self.new_property_type_group.addButton(self.single_building_radio, 1)
        
        property_type_layout.addWidget(self.multi_unit_radio)
        property_type_layout.addWidget(self.single_building_radio)
        
        form_layout.addRow("物件名称 *:", self.new_property_name)
        form_layout.addRow("住所 *:", self.new_property_address)
        form_layout.addRow("物件種別:", property_type_layout)
        form_layout.addRow("建物構造:", self.new_property_structure)
        form_layout.addRow("登記所有者:", self.new_property_owner)
        form_layout.addRow("管理形態:", self.new_management_type)
        form_layout.addRow("管理会社:", self.new_management_company)
        form_layout.addRow("備考:", self.new_property_notes)
        
        layout.addWidget(form_frame)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 物件を登録")
        save_btn.setStyleSheet(ModernStyles.get_button_styles())
        save_btn.clicked.connect(self.save_new_property)
        
        cancel_btn = QPushButton("❌ キャンセル")
        cancel_btn.clicked.connect(self.cancel_new_property)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        return page
    
    def clear_new_property_form(self):
        """新規物件フォームをクリア"""
        self.new_property_name.clear()
        self.new_property_address.clear()
        self.multi_unit_radio.setChecked(True)
        self.new_property_structure.setCurrentIndex(0)
        self.new_property_owner.clear()
        self.new_management_type.setCurrentIndex(0)
        self.new_management_company.clear()
        self.new_property_notes.clear()
    
    def save_new_property(self):
        """新規物件を保存"""
        name = self.new_property_name.text().strip()
        address = self.new_property_address.toPlainText().strip()
        
        if not name:
            QMessageBox.warning(self, "警告", "物件名称を入力してください。")
            return
        
        if not address:
            QMessageBox.warning(self, "警告", "住所を入力してください。")
            return
        
        try:
            structure = self.new_property_structure.currentText()
            if structure == "選択してください":
                structure = None
            
            # 物件種別を取得
            property_type = "区分所有" if self.multi_unit_radio.isChecked() else "一棟もの"
            
            # 備考に物件種別を追加
            notes = self.new_property_notes.toPlainText().strip()
            if notes:
                notes = f"[{property_type}] {notes}"
            else:
                notes = f"[{property_type}]"
            
            property_id = Property.create(
                name=name,
                address=address,
                structure=structure,
                registry_owner=self.new_property_owner.text().strip() or None,
                management_type=self.new_management_type.currentText(),
                management_company=self.new_management_company.text().strip() or None,
                notes=notes
            )
            
            QMessageBox.information(self, "成功", "物件を登録しました。")
            
            # ツリーを更新
            self.load_property_tree()
            
            # ウェルカム画面に戻る
            self.detail_stack.setCurrentIndex(0)
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"物件の保存に失敗しました: {str(e)}")
    
    def cancel_new_property(self):
        """新規物件登録をキャンセル"""
        self.detail_stack.setCurrentIndex(0)
    
    def load_property_units(self, property_id):
        """物件の部屋一覧を読み込み"""
        try:
            units = Unit.get_by_property(property_id)
            
            self.property_units_table.setRowCount(len(units))
            for i, unit in enumerate(units):
                self.property_units_table.setItem(i, 0, QTableWidgetItem(unit.get('room_number', '')))
                self.property_units_table.setItem(i, 1, QTableWidgetItem(str(unit.get('floor', ''))))
                self.property_units_table.setItem(i, 2, QTableWidgetItem(f"{unit.get('area', 0)}㎡"))
                self.property_units_table.setItem(i, 3, QTableWidgetItem(unit.get('use_restrictions', '')))
                
                # 設備情報
                equipment = []
                if unit.get('pet_allowed'):
                    equipment.append("ペット可")
                if unit.get('midnight_allowed'):
                    equipment.append("深夜営業可")
                
                self.property_units_table.setItem(i, 4, QTableWidgetItem(", ".join(equipment)))
                
                # 資料数を表示
                doc_count = self.get_document_count(property_id, unit['id'])
                status_text = f"📄{doc_count}件" if doc_count > 0 else "資料なし"
                self.property_units_table.setItem(i, 5, QTableWidgetItem(status_text))
                
                # 部屋IDを保存
                self.property_units_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, unit['id'])
                
        except Exception as e:
            print(f"部屋一覧読み込みエラー: {e}")
    
    def on_unit_table_clicked(self, item):
        """部屋テーブルクリック時の処理"""
        if item.column() == 0:  # 部屋番号列
            unit_id = item.data(Qt.ItemDataRole.UserRole)
            if unit_id:
                try:
                    unit_data = Unit.get_by_id(unit_id)
                    if unit_data:
                        self.set_unit_selection(unit_id, unit_data, self.current_property_id)
                        self.show_unit_detail(unit_id, unit_data)
                except Exception as e:
                    print(f"部屋詳細読み込みエラー: {e}")
    
    def show_new_property_form(self):
        """新規物件登録フォームを表示"""
        self.clear_new_property_form()
        self.detail_stack.setCurrentIndex(3)
    
    def edit_current_property(self):
        """現在選択されている物件を編集"""
        if not self.current_property_id or not self.current_property_data:
            QMessageBox.warning(self, "警告", "編集する物件を選択してください。")
            return
        
        try:
            dialog = PropertyEditDialog(self, self.current_property_data)
            if dialog.exec() == dialog.DialogCode.Accepted:
                # 物件データを更新
                self.current_property_data = Property.get_by_id(self.current_property_id)
                # 物件ツリーを更新
                self.load_property_tree()
                QMessageBox.information(self, "成功", "物件情報を更新しました。")
                
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"物件編集中にエラーが発生しました: {str(e)}")
    
    def edit_current_unit(self):
        """現在選択されている部屋を編集"""
        if not self.current_unit_id or not self.current_unit_data:
            QMessageBox.warning(self, "警告", "編集する部屋を選択してください。")
            return
        
        try:
            dialog = UnitEditDialog(self, self.current_unit_data)
            if dialog.exec() == dialog.DialogCode.Accepted:
                # 部屋データを更新
                self.current_unit_data = Unit.get_by_id(self.current_unit_id)
                # 物件ツリーを更新
                self.load_property_tree()
                QMessageBox.information(self, "成功", "部屋情報を更新しました。")
                
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"部屋編集中にエラーが発生しました: {str(e)}")
    
    def show_add_unit_form(self):
        """部屋追加フォームを表示"""
        if not self.current_property_id:
            QMessageBox.warning(self, "警告", "部屋を追加する物件を選択してください。")
            return
        
        try:
            dialog = UnitAddDialog(self, self.current_property_id)
            if dialog.exec() == dialog.DialogCode.Accepted:
                # 物件ツリーを更新
                self.load_property_tree()
                QMessageBox.information(self, "成功", "部屋を追加しました。")
                
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"部屋追加中にエラーが発生しました: {str(e)}")
    
    def delete_current_property(self):
        """現在選択されている物件を削除"""
        if not self.current_property_id:
            QMessageBox.warning(self, "警告", "削除する物件を選択してください。")
            return
        
        reply = QMessageBox.question(
            self, "削除確認", 
            f"物件「{self.current_property_data.get('name', '')}」を削除してもよろしいですか？\n\n※関連する部屋や資料もすべて削除されます。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                Property.delete(self.current_property_id)
                self.clear_selection()
                self.load_property_tree()
                QMessageBox.information(self, "成功", "物件を削除しました。")
                
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"物件削除中にエラーが発生しました: {str(e)}")
    
    def delete_current_unit(self):
        """現在選択されている部屋を削除"""
        if not self.current_unit_id:
            QMessageBox.warning(self, "警告", "削除する部屋を選択してください。")
            return
        
        reply = QMessageBox.question(
            self, "削除確認", 
            f"部屋「{self.current_unit_data.get('room_number', '')}」を削除してもよろしいですか？\n\n※関連する資料もすべて削除されます。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                Unit.delete(self.current_unit_id)
                self.clear_selection()
                self.load_property_tree()
                QMessageBox.information(self, "成功", "部屋を削除しました。")
                
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"部屋削除中にエラーが発生しました: {str(e)}")
    
    def show_upload_dialog(self):
        """資料アップロードダイアログを表示"""
        if not self.current_property_id:
            QMessageBox.warning(self, "警告", "資料をアップロードする物件を選択してください。")
            return
        
        try:
            dialog = DocumentUploadDialog(self, self.current_property_id, self.current_unit_id)
            if dialog.exec() == dialog.DialogCode.Accepted:
                QMessageBox.information(self, "成功", "資料をアップロードしました。")
                
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"資料アップロード中にエラーが発生しました: {str(e)}")
    
    def show_documents_list(self):
        """資料一覧を表示"""
        if not self.current_property_id:
            QMessageBox.warning(self, "警告", "資料を確認する物件を選択してください。")
            return
        
        try:
            # 資料保存ディレクトリを開く
            if self.current_unit_id:
                # 部屋固有の資料ディレクトリ
                docs_dir = os.path.join(self.document_storage_path, f"property_{self.current_property_id}", f"unit_{self.current_unit_id}")
            else:
                # 物件全体の資料ディレクトリ
                docs_dir = os.path.join(self.document_storage_path, f"property_{self.current_property_id}", "general")
            
            if not os.path.exists(docs_dir):
                QMessageBox.information(self, "資料なし", "まだ資料がアップロードされていません。")
                return
            
            # 資料一覧ダイアログを表示
            dialog = DocumentListDialog(self, docs_dir, self.current_property_id, self.current_unit_id)
            dialog.exec()
                
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"資料一覧表示中にエラーが発生しました: {str(e)}")
    
    def export_property_data(self):
        QMessageBox.information(self, "機能準備中", "データ出力機能は準備中です。")
    
    def import_property_data(self):
        QMessageBox.information(self, "機能準備中", "一括取込機能は準備中です。")
    
    def load_property_tree(self):
        """物件ツリーを構築"""
        try:
            self.property_tree.clear()
            
            # 物件一覧を取得
            properties = Property.get_all()
            
            for property_data in properties:
                # 物件アイテムを作成
                property_item = QTreeWidgetItem()
                property_item.setText(0, f"🏢 {property_data['name']}")
                
                # 物件データを設定
                property_item.setData(0, Qt.ItemDataRole.UserRole, {
                    'type': 'property',
                    'id': property_data['id'],
                    'data': property_data
                })
                
                # 物件の資料数を表示
                doc_count = self.get_document_count(property_data['id'])
                if doc_count > 0:
                    property_item.setText(0, f"🏢 {property_data['name']} 📄({doc_count})")
                
                self.property_tree.addTopLevelItem(property_item)
                
                # 部屋一覧を取得
                try:
                    units = Unit.get_by_property(property_data['id'])
                    
                    for unit_data in units:
                        # 部屋アイテムを作成
                        unit_item = QTreeWidgetItem()
                        unit_item.setText(0, f"🚪 {unit_data['room_number']}")
                        
                        # 部屋データを設定
                        unit_item.setData(0, Qt.ItemDataRole.UserRole, {
                            'type': 'unit',
                            'id': unit_data['id'],
                            'property_id': property_data['id'],
                            'data': unit_data
                        })
                        
                        # 部屋の資料数を表示
                        unit_doc_count = self.get_document_count(property_data['id'], unit_data['id'])
                        if unit_doc_count > 0:
                            unit_item.setText(0, f"🚪 {unit_data['room_number']} 📄({unit_doc_count})")
                        
                        property_item.addChild(unit_item)
                        
                except Exception as e:
                    print(f"部屋一覧読み込みエラー (物件{property_data['id']}): {str(e)}")
                    continue
            
            # ツリーを展開
            self.property_tree.expandAll()
            
        except Exception as e:
            print(f"物件ツリー構築エラー: {str(e)}")
            QMessageBox.critical(self, "エラー", f"物件一覧の読み込み中にエラーが発生しました: {str(e)}")
    
    def on_tree_item_clicked(self, item, column):
        """ツリーアイテムがクリックされたときの処理"""
        try:
            item_data = item.data(0, Qt.ItemDataRole.UserRole)
            
            if not item_data:
                return
            
            if item_data.get('type') == 'property':
                # 物件が選択された
                property_id = item_data['id']
                property_data = Property.get_by_id(property_id)
                
                if property_data:
                    self.set_property_selection(property_id, property_data)
                    self.show_property_details()
                    
            elif item_data.get('type') == 'unit':
                # 部屋が選択された
                unit_id = item_data['id']
                property_id = item_data['property_id']
                unit_data = Unit.get_by_id(unit_id)
                
                if unit_data:
                    self.set_unit_selection(unit_id, unit_data, property_id)
                    self.show_property_details()
                    
        except Exception as e:
            print(f"ツリーアイテム選択エラー: {str(e)}")
    
    def update_action_buttons(self, selection_type, item_id, property_id=None):
        """アクションボタンの有効化・無効化を更新"""
        try:
            if selection_type == 'property':
                # 物件が選択されている
                self.edit_property_btn.setEnabled(True)
                self.delete_property_btn.setEnabled(True)
                self.add_unit_btn.setEnabled(True)
                self.upload_docs_btn.setEnabled(True)
                self.view_docs_btn.setEnabled(True)
                
                # 部屋関連は無効
                self.edit_unit_btn.setEnabled(False)
                self.delete_unit_btn.setEnabled(False)
                
            elif selection_type == 'unit':
                # 部屋が選択されている
                self.edit_unit_btn.setEnabled(True)
                self.delete_unit_btn.setEnabled(True)
                self.upload_docs_btn.setEnabled(True)
                self.view_docs_btn.setEnabled(True)
                
                # 物件関連も有効（物件の編集・削除は可能）
                self.edit_property_btn.setEnabled(True)
                self.delete_property_btn.setEnabled(True)
                self.add_unit_btn.setEnabled(True)
                
            else:
                # 何も選択されていない
                self.edit_property_btn.setEnabled(False)
                self.delete_property_btn.setEnabled(False)
                self.add_unit_btn.setEnabled(False)
                self.edit_unit_btn.setEnabled(False)
                self.delete_unit_btn.setEnabled(False)
                self.upload_docs_btn.setEnabled(False)
                self.view_docs_btn.setEnabled(False)
                
        except Exception as e:
            print(f"アクションボタン更新エラー: {str(e)}")


class DocumentUploadDialog(QDialog):
    """資料アップロードダイアログ"""
    
    def __init__(self, parent, property_id, unit_id=None):
        super().__init__(parent)
        self.property_id = property_id
        self.unit_id = unit_id
        self.document_storage_path = "property_documents"
        self.init_ui()
    
    def init_ui(self):
        """UIを初期化"""
        self.setWindowTitle("資料アップロード")
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # アップロード対象情報
        info_group = QGroupBox("アップロード対象")
        info_layout = QFormLayout()
        
        property_info = Property.get_by_id(self.property_id)
        property_name = property_info.get('name', '不明') if property_info else '不明'
        
        info_layout.addRow("物件:", QLabel(property_name))
        if self.unit_id:
            info_layout.addRow("部屋:", QLabel(f"部屋番号: {self.unit_id}"))
        else:
            info_layout.addRow("部屋:", QLabel("物件全体"))
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # ファイル選択
        file_group = QGroupBox("ファイル選択")
        file_layout = QVBoxLayout()
        
        file_select_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        self.file_path_edit.setPlaceholderText("アップロードするファイルを選択してください")
        
        browse_btn = QPushButton("ファイル選択")
        browse_btn.clicked.connect(self.browse_file)
        
        file_select_layout.addWidget(self.file_path_edit, 1)
        file_select_layout.addWidget(browse_btn)
        
        file_layout.addLayout(file_select_layout)
        
        # ファイル情報表示
        self.file_info_label = QLabel("ファイルが選択されていません")
        self.file_info_label.setStyleSheet("color: gray;")
        file_layout.addWidget(self.file_info_label)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # 資料種別選択
        category_group = QGroupBox("資料種別")
        category_layout = QVBoxLayout()
        
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "建物登記簿", "土地登記簿", "重要事項説明書", "賃貸契約書",
            "管理規約", "修繕積立金規約", "駐車場規約", "その他"
        ])
        
        category_layout.addWidget(self.category_combo)
        category_group.setLayout(category_layout)
        layout.addWidget(category_group)
        
        # 備考
        notes_group = QGroupBox("備考")
        notes_layout = QVBoxLayout()
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("資料に関する備考があれば入力してください")
        
        notes_layout.addWidget(self.notes_edit)
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        upload_btn = QPushButton("アップロード")
        upload_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px 16px;")
        upload_btn.clicked.connect(self.upload_file)
        
        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(upload_btn)
        
        layout.addLayout(button_layout)
    
    def browse_file(self):
        """ファイル選択ダイアログを表示"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "アップロードするファイルを選択", "",
            "すべてのファイル (*.*);;"
            "PDFファイル (*.pdf);;"
            "画像ファイル (*.png *.jpg *.jpeg *.bmp *.tiff);;"
            "Wordファイル (*.doc *.docx);;"
            "Excelファイル (*.xls *.xlsx);;"
            "テキストファイル (*.txt)"
        )
        
        if file_path:
            self.file_path_edit.setText(file_path)
            self.update_file_info(file_path)
    
    def update_file_info(self, file_path):
        """ファイル情報を更新"""
        try:
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            
            # ファイルサイズを適切な単位で表示
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
            
            self.file_info_label.setText(f"ファイル名: {file_name}\nサイズ: {size_str}")
            self.file_info_label.setStyleSheet("color: black;")
            
        except Exception as e:
            self.file_info_label.setText(f"ファイル情報取得エラー: {str(e)}")
            self.file_info_label.setStyleSheet("color: red;")
    
    def upload_file(self):
        """ファイルをアップロード"""
        file_path = self.file_path_edit.text().strip()
        if not file_path:
            QMessageBox.warning(self, "警告", "ファイルを選択してください。")
            return
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "警告", "選択されたファイルが存在しません。")
            return
        
        try:
            # 保存先ディレクトリを作成
            if self.unit_id:
                # 部屋固有の資料ディレクトリ
                save_dir = os.path.join(self.document_storage_path, f"property_{self.property_id}", f"unit_{self.unit_id}")
            else:
                # 物件全体の資料ディレクトリ
                save_dir = os.path.join(self.document_storage_path, f"property_{self.property_id}", "general")
            
            os.makedirs(save_dir, exist_ok=True)
            
            # ファイル名を取得
            file_name = os.path.basename(file_path)
            category = self.category_combo.currentText()
            notes = self.notes_edit.toPlainText().strip()
            
            # ファイル名にカテゴリとタイムスタンプを追加
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_file_name = f"{category}_{timestamp}_{file_name}"
            
            # ファイルをコピー
            dest_path = os.path.join(save_dir, new_file_name)
            shutil.copy2(file_path, dest_path)
            
            # メタデータファイルを作成
            metadata = {
                "original_name": file_name,
                "category": category,
                "notes": notes,
                "upload_date": datetime.now().isoformat(),
                "file_size": os.path.getsize(file_path)
            }
            
            metadata_path = os.path.join(save_dir, f"{new_file_name}.meta.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                import json
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            QMessageBox.information(self, "成功", f"資料をアップロードしました。\n保存先: {dest_path}")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"ファイルアップロード中にエラーが発生しました: {str(e)}")


class DocumentListDialog(QDialog):
    """資料一覧ダイアログ"""
    
    def __init__(self, parent, docs_dir, property_id, unit_id=None):
        super().__init__(parent)
        self.docs_dir = docs_dir
        self.property_id = property_id
        self.unit_id = unit_id
        self.init_ui()
        self.load_documents()
    
    def init_ui(self):
        """UIを初期化"""
        self.setWindowTitle("資料一覧")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # ヘッダー
        header_layout = QHBoxLayout()
        
        property_info = Property.get_by_id(self.property_id)
        property_name = property_info.get('name', '不明') if property_info else '不明'
        
        if self.unit_id:
            header_label = QLabel(f"物件: {property_name} - 部屋番号: {self.unit_id}")
        else:
            header_label = QLabel(f"物件: {property_name} - 物件全体")
        
        header_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2196F3;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        # 新規アップロードボタン
        upload_btn = QPushButton("📤 新規アップロード")
        upload_btn.clicked.connect(self.upload_new_document)
        header_layout.addWidget(upload_btn)
        
        layout.addLayout(header_layout)
        
        # 資料一覧テーブル
        self.documents_table = QTableWidget()
        self.documents_table.setColumnCount(6)
        self.documents_table.setHorizontalHeaderLabels([
            "資料名", "種別", "アップロード日", "サイズ", "備考", "操作"
        ])
        
        # テーブルの列幅を調整
        header = self.documents_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.documents_table)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 更新")
        refresh_btn.clicked.connect(self.load_documents)
        
        close_btn = QPushButton("閉じる")
        close_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(refresh_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def load_documents(self):
        """資料一覧を読み込み"""
        self.documents_table.setRowCount(0)
        
        try:
            if not os.path.exists(self.docs_dir):
                return
            
            documents = []
            
            # ディレクトリ内のファイルをスキャン
            for item in os.listdir(self.docs_dir):
                item_path = os.path.join(self.docs_dir, item)
                
                # メタデータファイルをスキップ
                if item.endswith('.meta.json'):
                    continue
                
                # メタデータファイルのパス
                metadata_path = os.path.join(self.docs_dir, f"{item}.meta.json")
                
                # ファイル情報を取得
                file_stat = os.stat(item_path)
                file_size = file_stat.st_size
                
                # ファイルサイズを適切な単位で表示
                if file_size < 1024:
                    size_str = f"{file_size} B"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size / 1024:.1f} KB"
                else:
                    size_str = f"{file_size / (1024 * 1024):.1f} MB"
                
                # メタデータを読み込み
                category = "その他"
                notes = ""
                upload_date = datetime.fromtimestamp(file_stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            import json
                            metadata = json.load(f)
                            category = metadata.get('category', 'その他')
                            notes = metadata.get('notes', '')
                            upload_date = metadata.get('upload_date', upload_date)
                    except:
                        pass
                
                documents.append({
                    'name': item,
                    'path': item_path,
                    'category': category,
                    'upload_date': upload_date,
                    'size': size_str,
                    'notes': notes
                })
            
            # アップロード日でソート（新しい順）
            documents.sort(key=lambda x: x['upload_date'], reverse=True)
            
            # テーブルに表示
            self.documents_table.setRowCount(len(documents))
            
            for row, doc in enumerate(documents):
                # 資料名
                name_item = QTableWidgetItem(doc['name'])
                self.documents_table.setItem(row, 0, name_item)
                
                # 種別
                category_item = QTableWidgetItem(doc['category'])
                self.documents_table.setItem(row, 1, category_item)
                
                # アップロード日
                date_item = QTableWidgetItem(doc['upload_date'])
                self.documents_table.setItem(row, 2, date_item)
                
                # サイズ
                size_item = QTableWidgetItem(doc['size'])
                self.documents_table.setItem(row, 3, size_item)
                
                # 備考
                notes_item = QTableWidgetItem(doc['notes'])
                self.documents_table.setItem(row, 4, notes_item)
                
                # 操作ボタン
                button_widget = QWidget()
                button_layout = QHBoxLayout(button_widget)
                button_layout.setContentsMargins(2, 2, 2, 2)
                
                view_btn = QPushButton("👁️")
                view_btn.setToolTip("閲覧")
                view_btn.clicked.connect(lambda checked, path=doc['path']: self.view_document(path))
                
                download_btn = QPushButton("📥")
                download_btn.setToolTip("ダウンロード")
                download_btn.clicked.connect(lambda checked, path=doc['path']: self.download_document(path))
                
                delete_btn = QPushButton("🗑")
                delete_btn.setToolTip("削除")
                delete_btn.clicked.connect(lambda checked, path=doc['path']: self.delete_document(path))
                
                button_layout.addWidget(view_btn)
                button_layout.addWidget(download_btn)
                button_layout.addWidget(delete_btn)
                button_layout.addStretch()
                
                self.documents_table.setCellWidget(row, 5, button_widget)
                
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"資料一覧の読み込み中にエラーが発生しました: {str(e)}")
    
    def upload_new_document(self):
        """新規資料をアップロード"""
        try:
            dialog = DocumentUploadDialog(self, self.property_id, self.unit_id)
            if dialog.exec() == dialog.DialogCode.Accepted:
                self.load_documents()  # 一覧を更新
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"アップロードダイアログの表示中にエラーが発生しました: {str(e)}")
    
    def view_document(self, file_path):
        """資料を閲覧"""
        try:
            # ファイルの種類に応じて適切なアプリケーションで開く
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", file_path])
            else:  # Linux
                subprocess.run(["xdg-open", file_path])
                
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"資料の閲覧中にエラーが発生しました: {str(e)}")
    
    def download_document(self, file_path):
        """資料をダウンロード（別名で保存）"""
        try:
            # 保存先を選択
            file_name = os.path.basename(file_path)
            save_path, _ = QFileDialog.getSaveFileName(
                self, "資料を保存", file_name,
                "すべてのファイル (*.*)"
            )
            
            if save_path:
                shutil.copy2(file_path, save_path)
                QMessageBox.information(self, "成功", f"資料を保存しました。\n保存先: {save_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"資料の保存中にエラーが発生しました: {str(e)}")
    
    def delete_document(self, file_path):
        """資料を削除"""
        try:
            reply = QMessageBox.question(
                self, "削除確認", 
                f"この資料を削除してもよろしいですか？\n{os.path.basename(file_path)}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # ファイルを削除
                os.remove(file_path)
                
                # メタデータファイルも削除
                metadata_path = f"{file_path}.meta.json"
                if os.path.exists(metadata_path):
                    os.remove(metadata_path)
                
                QMessageBox.information(self, "成功", "資料を削除しました。")
                self.load_documents()  # 一覧を更新
                
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"資料の削除中にエラーが発生しました: {str(e)}")


class PropertyEditDialog(QDialog):
    """物件編集ダイアログ"""
    
    def __init__(self, parent, property_data):
        super().__init__(parent)
        self.property_data = property_data
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """UIを初期化"""
        self.setWindowTitle("物件編集")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # フォーム
        form_group = QGroupBox("物件情報")
        form_layout = QFormLayout()
        form_layout.setSpacing(8)
        
        self.name_edit = QLineEdit()
        self.address_edit = QTextEdit()
        self.address_edit.setMaximumHeight(50)
        
        self.structure_combo = QComboBox()
        self.structure_combo.addItems([
            "選択してください", "RC造", "SRC造", "S造", "木造", "軽量鉄骨造", "その他"
        ])
        
        self.owner_edit = QLineEdit()
        
        self.management_type_combo = QComboBox()
        self.management_type_combo.addItems([
            "自社管理", "他社仲介", "共同管理", "その他"
        ])
        
        self.management_company_edit = QLineEdit()
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        
        form_layout.addRow("物件名称 *:", self.name_edit)
        form_layout.addRow("住所 *:", self.address_edit)
        form_layout.addRow("建物構造:", self.structure_combo)
        form_layout.addRow("登記所有者:", self.owner_edit)
        form_layout.addRow("管理形態:", self.management_type_combo)
        form_layout.addRow("管理会社:", self.management_company_edit)
        form_layout.addRow("備考:", self.notes_edit)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept_changes)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
    
    def load_data(self):
        """既存データを読み込み"""
        self.name_edit.setText(self.property_data.get('name', ''))
        self.address_edit.setPlainText(self.property_data.get('address', ''))
        
        structure = self.property_data.get('structure', '')
        structure_index = self.structure_combo.findText(structure)
        if structure_index >= 0:
            self.structure_combo.setCurrentIndex(structure_index)
        
        self.owner_edit.setText(self.property_data.get('registry_owner', ''))
        
        management_type = self.property_data.get('management_type', '')
        management_index = self.management_type_combo.findText(management_type)
        if management_index >= 0:
            self.management_type_combo.setCurrentIndex(management_index)
        
        self.management_company_edit.setText(self.property_data.get('management_company', ''))
        self.notes_edit.setPlainText(self.property_data.get('notes', ''))
    
    def accept_changes(self):
        """変更を保存"""
        name = self.name_edit.text().strip()
        address = self.address_edit.toPlainText().strip()
        
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
            
            Property.update(
                id=self.property_data['id'],
                name=name,
                address=address,
                structure=structure,
                registry_owner=self.owner_edit.text().strip() or None,
                management_type=self.management_type_combo.currentText(),
                management_company=self.management_company_edit.text().strip() or None,
                notes=self.notes_edit.toPlainText().strip() or None
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"物件の更新に失敗しました: {str(e)}")


class UnitEditDialog(QDialog):
    """部屋編集ダイアログ"""
    
    def __init__(self, parent, unit_data):
        super().__init__(parent)
        self.unit_data = unit_data
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """UIを初期化"""
        self.setWindowTitle("部屋編集")
        self.setModal(True)
        self.resize(400, 350)
        
        layout = QVBoxLayout(self)
        
        # フォーム
        form_group = QGroupBox("部屋情報")
        form_layout = QFormLayout()
        form_layout.setSpacing(8)
        
        self.room_number_edit = QLineEdit()
        self.room_number_edit.setPlaceholderText("例: 101, 1F-A")
        
        self.floor_edit = QLineEdit()
        self.floor_edit.setPlaceholderText("例: 1, 1F, B1")
        
        self.area_spin = QDoubleSpinBox()
        self.area_spin.setRange(1.0, 1000.0)
        self.area_spin.setSuffix(" ㎡")
        self.area_spin.setDecimals(2)
        
        self.use_restrictions_edit = QLineEdit()
        self.use_restrictions_edit.setPlaceholderText("例: 事務所専用、飲食不可")
        
        self.power_capacity_spin = QSpinBox()
        self.power_capacity_spin.setRange(0, 1000)
        self.power_capacity_spin.setSuffix(" kW")
        
        self.pet_allowed_check = QCheckBox("ペット可")
        self.midnight_allowed_check = QCheckBox("深夜営業可")
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(50)
        self.notes_edit.setPlaceholderText("部屋の特記事項...")
        
        form_layout.addRow("部屋番号 *:", self.room_number_edit)
        form_layout.addRow("階数:", self.floor_edit)
        form_layout.addRow("面積:", self.area_spin)
        form_layout.addRow("用途制限:", self.use_restrictions_edit)
        form_layout.addRow("電力容量:", self.power_capacity_spin)
        form_layout.addRow("設備:", self.pet_allowed_check)
        form_layout.addRow("", self.midnight_allowed_check)
        form_layout.addRow("備考:", self.notes_edit)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept_changes)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
    
    def load_data(self):
        """既存データを読み込み"""
        self.room_number_edit.setText(self.unit_data.get('room_number', ''))
        self.floor_edit.setText(str(self.unit_data.get('floor', '')))
        self.area_spin.setValue(float(self.unit_data.get('area', 0)))
        self.use_restrictions_edit.setText(self.unit_data.get('use_restrictions', ''))
        
        # 電力容量の解析
        power_capacity = self.unit_data.get('power_capacity', '')
        if power_capacity:
            try:
                # "30kW" → 30 に変換
                power_value = int(''.join(filter(str.isdigit, power_capacity)))
                self.power_capacity_spin.setValue(power_value)
            except:
                self.power_capacity_spin.setValue(0)
        
        self.pet_allowed_check.setChecked(bool(self.unit_data.get('pet_allowed', False)))
        self.midnight_allowed_check.setChecked(bool(self.unit_data.get('midnight_allowed', False)))
        self.notes_edit.setPlainText(self.unit_data.get('notes', ''))
    
    def accept_changes(self):
        """変更を保存"""
        room_number = self.room_number_edit.text().strip()
        
        if not room_number:
            QMessageBox.warning(self, "警告", "部屋番号を入力してください。")
            return
        
        try:
            Unit.update(
                unit_id=self.unit_data['id'],
                room_number=room_number,
                floor=self.floor_edit.text().strip() or None,
                area=self.area_spin.value(),
                use_restrictions=self.use_restrictions_edit.text().strip() or None,
                power_capacity=str(self.power_capacity_spin.value()) + "kW" if self.power_capacity_spin.value() > 0 else None,
                pet_allowed=self.pet_allowed_check.isChecked(),
                midnight_allowed=self.midnight_allowed_check.isChecked(),
                notes=self.notes_edit.toPlainText().strip() or None
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"部屋の更新に失敗しました: {str(e)}")


class UnitAddDialog(QDialog):
    """部屋追加ダイアログ"""
    
    def __init__(self, parent, property_id):
        super().__init__(parent)
        self.property_id = property_id
        self.init_ui()
    
    def init_ui(self):
        """UIを初期化"""
        self.setWindowTitle("部屋追加")
        self.setModal(True)
        self.resize(400, 350)
        
        layout = QVBoxLayout(self)
        
        # フォーム
        form_group = QGroupBox("部屋情報")
        form_layout = QFormLayout()
        form_layout.setSpacing(8)
        
        self.room_number_edit = QLineEdit()
        self.room_number_edit.setPlaceholderText("例: 101, 1F-A")
        
        self.floor_edit = QLineEdit()
        self.floor_edit.setPlaceholderText("例: 1, 1F, B1")
        
        self.area_spin = QDoubleSpinBox()
        self.area_spin.setRange(1.0, 1000.0)
        self.area_spin.setSuffix(" ㎡")
        self.area_spin.setDecimals(2)
        self.area_spin.setValue(20.0)
        
        self.use_restrictions_edit = QLineEdit()
        self.use_restrictions_edit.setPlaceholderText("例: 事務所専用、飲食不可")
        
        self.power_capacity_spin = QSpinBox()
        self.power_capacity_spin.setRange(0, 1000)
        self.power_capacity_spin.setSuffix(" kW")
        
        self.pet_allowed_check = QCheckBox("ペット可")
        self.midnight_allowed_check = QCheckBox("深夜営業可")
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(50)
        self.notes_edit.setPlaceholderText("部屋の特記事項...")
        
        form_layout.addRow("部屋番号 *:", self.room_number_edit)
        form_layout.addRow("階数:", self.floor_edit)
        form_layout.addRow("面積:", self.area_spin)
        form_layout.addRow("用途制限:", self.use_restrictions_edit)
        form_layout.addRow("電力容量:", self.power_capacity_spin)
        form_layout.addRow("設備:", self.pet_allowed_check)
        form_layout.addRow("", self.midnight_allowed_check)
        form_layout.addRow("備考:", self.notes_edit)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept_unit)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
    
    def accept_unit(self):
        """部屋を保存"""
        room_number = self.room_number_edit.text().strip()
        
        if not room_number:
            QMessageBox.warning(self, "警告", "部屋番号を入力してください。")
            return
        
        try:
            Unit.create(
                property_id=self.property_id,
                room_number=room_number,
                floor=self.floor_edit.text().strip() or None,
                area=self.area_spin.value(),
                use_restrictions=self.use_restrictions_edit.text().strip() or None,
                power_capacity=str(self.power_capacity_spin.value()) + "kW" if self.power_capacity_spin.value() > 0 else None,
                pet_allowed=self.pet_allowed_check.isChecked(),
                midnight_allowed=self.midnight_allowed_check.isChecked(),
                notes=self.notes_edit.toPlainText().strip() or None
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"部屋の追加に失敗しました: {str(e)}")