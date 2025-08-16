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
    
    def init_ui(self):
        """UIを初期化"""
        # ページコンテナを作成
        container, layout = make_page_container()
        
        # タイトル
        title = QLabel("🏢 物件統合管理")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_2xl']};
                font-weight: 600;
                color: {ModernUITheme.COLORS['text_primary']};
                margin: 0;
                padding: 0;
            }}
        """)
        layout.addWidget(title)
        
        # メインコンテンツ - 3分割
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左側：物件ツリー（200px固定）
        left_widget = self.create_property_tree_panel()
        left_widget.setMinimumWidth(200)
        left_widget.setMaximumWidth(300)
        main_splitter.addWidget(left_widget)
        
        # 中央：詳細表示・編集エリア（可変）
        center_widget = self.create_detail_panel()
        main_splitter.addWidget(center_widget)
        
        # 右側：クイックアクション（250px固定）
        right_widget = self.create_action_panel()
        right_widget.setMinimumWidth(250)
        right_widget.setMaximumWidth(300)
        main_splitter.addWidget(right_widget)
        
        # スプリッターの初期サイズ設定（20% : 60% : 20%）
        main_splitter.setSizes([250, 700, 250])
        
        layout.addWidget(main_splitter)
        
        # スクロール可能ページとして設定
        scroll_page = make_scroll_page(container)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(scroll_page)
        
        # 初期データ読み込み
        self.load_property_tree()
    
    def create_property_tree_panel(self):
        """物件ツリーパネル"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # ヘッダー
        header = QLabel("📋 物件一覧")
        header.setStyleSheet(f"""
            QLabel {{
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_lg']};
                font-weight: 600;
                color: {ModernUITheme.COLORS['text_primary']};
                margin-bottom: {ModernUITheme.SPACING['xs']};
            }}
        """)
        layout.addWidget(header)
        
        # 物件ツリー
        self.property_tree = QTreeWidget()
        self.property_tree.setHeaderHidden(True)
        self.property_tree.itemClicked.connect(self.on_tree_item_clicked)
        
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
        
        layout.addWidget(self.property_tree)
        
        # 新規作成ボタン
        new_property_btn = QPushButton("➕ 新規物件登録")
        new_property_btn.setStyleSheet(ModernStyles.get_button_styles())
        new_property_btn.clicked.connect(self.show_new_property_form)
        
        refresh_btn = QPushButton("🔄 更新")
        refresh_btn.clicked.connect(self.load_property_tree)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(new_property_btn)
        button_layout.addWidget(refresh_btn)
        
        layout.addLayout(button_layout)
        
        return widget
    
    def create_detail_panel(self):
        """詳細表示・編集パネル"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
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
        
        layout.addWidget(self.detail_stack)
        
        # 初期状態はウェルカム画面
        self.detail_stack.setCurrentIndex(0)
        
        return widget
    
    def create_action_panel(self):
        """アクションパネル"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # ヘッダー
        header = QLabel("⚡ クイックアクション")
        header.setStyleSheet(f"""
            QLabel {{
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_lg']};
                font-weight: 600;
                color: {ModernUITheme.COLORS['text_primary']};
                margin-bottom: {ModernUITheme.SPACING['xs']};
            }}
        """)
        layout.addWidget(header)
        
        # アクションボタン群
        actions_frame = QFrame()
        actions_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {ModernUITheme.COLORS['bg_primary']};
                border: 1px solid {ModernUITheme.COLORS['border']};
                border-radius: {ModernUITheme.RADIUS['lg']};
                padding: {ModernUITheme.SPACING['sm']};
            }}
        """)
        actions_layout = QVBoxLayout(actions_frame)
        actions_layout.setSpacing(6)
        
        # 物件関連アクション
        property_section = QLabel("🏢 物件操作")
        property_section.setStyleSheet(f"font-weight: 600; color: {ModernUITheme.COLORS['text_secondary']};")
        actions_layout.addWidget(property_section)
        
        self.edit_property_btn = QPushButton("✏️ 物件編集")
        self.edit_property_btn.clicked.connect(self.edit_current_property)
        self.edit_property_btn.setEnabled(False)
        
        self.delete_property_btn = QPushButton("🗑 物件削除")
        self.delete_property_btn.clicked.connect(self.delete_current_property)
        self.delete_property_btn.setEnabled(False)
        
        actions_layout.addWidget(self.edit_property_btn)
        actions_layout.addWidget(self.delete_property_btn)
        
        # 部屋関連アクション
        unit_section = QLabel("🏠 部屋操作")
        unit_section.setStyleSheet(f"font-weight: 600; color: {ModernUITheme.COLORS['text_secondary']};")
        actions_layout.addWidget(unit_section)
        
        self.add_unit_btn = QPushButton("➕ 部屋追加")
        self.add_unit_btn.clicked.connect(self.show_add_unit_form)
        self.add_unit_btn.setEnabled(False)
        
        self.edit_unit_btn = QPushButton("✏️ 部屋編集")
        self.edit_unit_btn.clicked.connect(self.edit_current_unit)
        self.edit_unit_btn.setEnabled(False)
        
        self.delete_unit_btn = QPushButton("🗑 部屋削除")
        self.delete_unit_btn.clicked.connect(self.delete_current_unit)
        self.delete_unit_btn.setEnabled(False)
        
        actions_layout.addWidget(self.add_unit_btn)
        actions_layout.addWidget(self.edit_unit_btn)
        actions_layout.addWidget(self.delete_unit_btn)
        
        # 資料関連アクション
        docs_section = QLabel("📄 資料管理")
        docs_section.setStyleSheet(f"font-weight: 600; color: {ModernUITheme.COLORS['text_secondary']};")
        actions_layout.addWidget(docs_section)
        
        self.upload_docs_btn = QPushButton("📤 資料アップロード")
        self.upload_docs_btn.clicked.connect(self.show_upload_dialog)
        self.upload_docs_btn.setEnabled(False)
        
        self.view_docs_btn = QPushButton("📋 資料一覧")
        self.view_docs_btn.clicked.connect(self.show_documents_list)
        self.view_docs_btn.setEnabled(False)
        
        actions_layout.addWidget(self.upload_docs_btn)
        actions_layout.addWidget(self.view_docs_btn)
        
        # データ操作
        data_section = QLabel("💾 データ操作")
        data_section.setStyleSheet(f"font-weight: 600; color: {ModernUITheme.COLORS['text_secondary']};")
        actions_layout.addWidget(data_section)
        
        self.export_data_btn = QPushButton("📤 データ出力")
        self.export_data_btn.clicked.connect(self.export_property_data)
        
        self.import_data_btn = QPushButton("📥 一括取込")
        self.import_data_btn.clicked.connect(self.import_property_data)
        
        actions_layout.addWidget(self.export_data_btn)
        actions_layout.addWidget(self.import_data_btn)
        
        actions_layout.addStretch()
        
        layout.addWidget(actions_frame)
        layout.addStretch()
        
        return widget
    
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
        """物件詳細ページ"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # ヘッダー
        self.property_header = QLabel("物件詳細")
        self.property_header.setStyleSheet(f"""
            QLabel {{
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_xl']};
                font-weight: 600;
                color: {ModernUITheme.COLORS['text_primary']};
                margin-bottom: {ModernUITheme.SPACING['sm']};
            }}
        """)
        layout.addWidget(self.property_header)
        
        # 基本情報表示
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {ModernUITheme.COLORS['bg_primary']};
                border: 1px solid {ModernUITheme.COLORS['border']};
                border-radius: {ModernUITheme.RADIUS['lg']};
                padding: {ModernUITheme.SPACING['sm']};
            }}
        """)
        info_layout = QFormLayout(info_frame)
        
        # 情報表示ラベル
        self.property_name_display = QLabel()
        self.property_address_display = QLabel()
        self.property_structure_display = QLabel()
        self.property_management_display = QLabel()
        
        info_layout.addRow("物件名:", self.property_name_display)
        info_layout.addRow("住所:", self.property_address_display)
        info_layout.addRow("構造:", self.property_structure_display)
        info_layout.addRow("管理形態:", self.property_management_display)
        
        layout.addWidget(info_frame)
        
        # 部屋一覧
        units_group = QGroupBox("部屋一覧")
        units_layout = QVBoxLayout()
        
        self.property_units_table = QTableWidget()
        self.property_units_table.setColumnCount(6)
        self.property_units_table.setHorizontalHeaderLabels([
            "部屋番号", "階数", "面積", "用途制限", "設備", "資料数"
        ])
        self.property_units_table.itemClicked.connect(self.on_unit_table_clicked)
        
        units_layout.addWidget(self.property_units_table)
        units_group.setLayout(units_layout)
        
        layout.addWidget(units_group)
        layout.addStretch()
        
        return page
    
    def create_unit_detail_page(self):
        """部屋詳細ページ"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # ヘッダー
        self.unit_header = QLabel("部屋詳細")
        self.unit_header.setStyleSheet(f"""
            QLabel {{
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_xl']};
                font-weight: 600;
                color: {ModernUITheme.COLORS['text_primary']};
                margin-bottom: {ModernUITheme.SPACING['sm']};
            }}
        """)
        layout.addWidget(self.unit_header)
        
        # 詳細情報フレーム
        detail_frame = QFrame()
        detail_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {ModernUITheme.COLORS['bg_primary']};
                border: 1px solid {ModernUITheme.COLORS['border']};
                border-radius: {ModernUITheme.RADIUS['lg']};
                padding: {ModernUITheme.SPACING['sm']};
            }}
        """)
        detail_layout = QFormLayout(detail_frame)
        
        # 部屋情報表示ラベル
        self.unit_room_number_display = QLabel()
        self.unit_floor_display = QLabel()
        self.unit_area_display = QLabel()
        self.unit_restrictions_display = QLabel()
        self.unit_equipment_display = QLabel()
        self.unit_notes_display = QLabel()
        
        detail_layout.addRow("部屋番号:", self.unit_room_number_display)
        detail_layout.addRow("階数:", self.unit_floor_display)
        detail_layout.addRow("面積:", self.unit_area_display)
        detail_layout.addRow("用途制限:", self.unit_restrictions_display)
        detail_layout.addRow("設備:", self.unit_equipment_display)
        detail_layout.addRow("備考:", self.unit_notes_display)
        
        layout.addWidget(detail_frame)
        layout.addStretch()
        
        return page
    
    def create_new_property_page(self):
        """新規物件登録ページ"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
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
    
    def load_property_tree(self):
        """物件ツリーを読み込み"""
        try:
            self.property_tree.clear()
            
            properties = Property.get_all()
            for property_obj in properties:
                # 物件ノード（資料数付き）
                property_doc_count = self.get_document_count(property_obj['id'])
                property_display = f"🏢 {property_obj['name']}"
                if property_doc_count > 0:
                    property_display += f" 📄{property_doc_count}"
                
                property_item = QTreeWidgetItem([property_display])
                property_item.setData(0, Qt.ItemDataRole.UserRole, {
                    'type': 'property',
                    'id': property_obj['id'],
                    'data': property_obj
                })
                
                # 部屋ノード（資料数付き）
                units = Unit.get_by_property(property_obj['id'])
                for unit in units:
                    unit_doc_count = self.get_document_count(property_obj['id'], unit['id'])
                    unit_display = f"🏠 {unit['room_number']} ({unit.get('area', 0)}㎡)"
                    if unit_doc_count > 0:
                        unit_display += f" 📄{unit_doc_count}"
                    
                    unit_item = QTreeWidgetItem([unit_display])
                    unit_item.setData(0, Qt.ItemDataRole.UserRole, {
                        'type': 'unit',
                        'id': unit['id'],
                        'property_id': property_obj['id'],
                        'data': unit
                    })
                    property_item.addChild(unit_item)
                
                self.property_tree.addTopLevelItem(property_item)
                property_item.setExpanded(True)
                
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"物件一覧の読み込みに失敗しました: {str(e)}")
    
    def on_tree_item_clicked(self, item, column):
        """ツリーアイテムクリック時の処理"""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        
        if data['type'] == 'property':
            self.set_property_selection(data['id'], data['data'])
            self.show_property_detail(data['id'], data['data'])
            
        elif data['type'] == 'unit':
            self.set_unit_selection(data['id'], data['data'], data['property_id'])
            self.show_unit_detail(data['id'], data['data'])
    
    def show_property_detail(self, property_id, property_data):
        """物件詳細を表示"""
        # 選択状態は既に set_property_selection で設定済み
        
        # ヘッダー更新
        self.property_header.setText(f"🏢 {property_data['name']}")
        
        # 基本情報表示
        self.property_name_display.setText(property_data['name'])
        self.property_address_display.setText(property_data.get('address', ''))
        self.property_structure_display.setText(property_data.get('structure', ''))
        self.property_management_display.setText(property_data.get('management_type', ''))
        
        # 部屋一覧を更新
        self.load_property_units(property_id)
        
        # 詳細ページを表示
        self.detail_stack.setCurrentIndex(1)
    
    def show_unit_detail(self, unit_id, unit_data):
        """部屋詳細を表示"""
        # 選択状態は既に set_unit_selection で設定済み
        
        # ヘッダー更新
        self.unit_header.setText(f"🏠 {unit_data['room_number']}")
        
        # 詳細情報表示
        self.unit_room_number_display.setText(unit_data['room_number'])
        self.unit_floor_display.setText(str(unit_data.get('floor', '')))
        self.unit_area_display.setText(f"{unit_data.get('area', 0)}㎡")
        self.unit_restrictions_display.setText(unit_data.get('use_restrictions', ''))
        
        # 設備情報
        equipment = []
        if unit_data.get('pet_allowed'):
            equipment.append("ペット可")
        if unit_data.get('midnight_allowed'):
            equipment.append("深夜営業可")
        self.unit_equipment_display.setText(", ".join(equipment) if equipment else "なし")
        
        self.unit_notes_display.setText(unit_data.get('notes', ''))
        
        # 詳細ページを表示
        self.detail_stack.setCurrentIndex(2)
    
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
    
    def update_action_buttons(self, selected_type, selected_id, property_id=None):
        """アクションボタンの状態を更新"""
        if selected_type == 'property':
            self.edit_property_btn.setEnabled(True)
            self.delete_property_btn.setEnabled(True)
            self.add_unit_btn.setEnabled(True)
            self.edit_unit_btn.setEnabled(False)
            self.delete_unit_btn.setEnabled(False)
            self.upload_docs_btn.setEnabled(True)
            self.view_docs_btn.setEnabled(True)
            
        elif selected_type == 'unit':
            self.edit_property_btn.setEnabled(True)
            self.delete_property_btn.setEnabled(True)
            self.add_unit_btn.setEnabled(True)
            self.edit_unit_btn.setEnabled(True)
            self.delete_unit_btn.setEnabled(True)
            self.upload_docs_btn.setEnabled(True)
            self.view_docs_btn.setEnabled(True)
            
        else:
            # 何も選択されていない
            self.edit_property_btn.setEnabled(False)
            self.delete_property_btn.setEnabled(False)
            self.add_unit_btn.setEnabled(False)
            self.edit_unit_btn.setEnabled(False)
            self.delete_unit_btn.setEnabled(False)
            self.upload_docs_btn.setEnabled(False)
            self.view_docs_btn.setEnabled(False)
    
    def show_new_property_form(self):
        """新規物件登録フォームを表示"""
        self.clear_new_property_form()
        self.detail_stack.setCurrentIndex(3)
    
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
    
    # アクションボタンの実装
    def edit_current_property(self):
        """物件編集ダイアログを表示"""
        if not self.current_property_id:
            QMessageBox.warning(self, "警告", "編集する物件を選択してください。")
            return
        
        try:
            # 現在の物件データを取得
            property_data = Property.get_by_id(self.current_property_id)
            if not property_data:
                QMessageBox.critical(self, "エラー", "物件データが見つかりません。")
                return
            
            # 編集ダイアログを作成
            dialog = PropertyEditDialog(self, property_data)
            if dialog.exec() == dialog.DialogCode.Accepted:
                # 物件ツリーと詳細表示を更新
                self.load_property_tree()
                self.show_property_detail(self.current_property_id, Property.get_by_id(self.current_property_id))
                QMessageBox.information(self, "成功", "物件情報を更新しました。")
                
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"物件編集中にエラーが発生しました: {str(e)}")
    
    def delete_current_property(self):
        """物件削除"""
        if not self.current_property_id:
            QMessageBox.warning(self, "警告", "削除する物件を選択してください。")
            return
        
        try:
            property_data = Property.get_by_id(self.current_property_id)
            if not property_data:
                QMessageBox.critical(self, "エラー", "物件データが見つかりません。")
                return
            
            # 確認ダイアログ
            reply = QMessageBox.question(
                self, "確認", 
                f"物件「{property_data['name']}」を削除しますか？\n\n注意: この操作は取り消せません。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # 関連する部屋も確認
                units = Unit.get_by_property(self.current_property_id)
                if units:
                    unit_count = len(units)
                    confirm_reply = QMessageBox.question(
                        self, "確認", 
                        f"この物件には{unit_count}個の部屋が登録されています。\nすべて一緒に削除されますが、よろしいですか？",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if confirm_reply != QMessageBox.StandardButton.Yes:
                        return
                
                # 物件削除（関連部屋も自動削除されるはず）
                Property.delete(self.current_property_id)
                
                # UI更新
                self.clear_selection()
                self.load_property_tree()
                
                QMessageBox.information(self, "成功", "物件を削除しました。")
                
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"物件削除中にエラーが発生しました: {str(e)}")
    
    def show_add_unit_form(self):
        """部屋追加ダイアログを表示"""
        if not self.current_property_id:
            QMessageBox.warning(self, "警告", "部屋を追加する物件を選択してください。")
            return
        
        try:
            dialog = UnitAddDialog(self, self.current_property_id)
            if dialog.exec() == dialog.DialogCode.Accepted:
                # 物件ツリーと詳細表示を更新
                self.load_property_tree()
                if self.current_property_id:
                    property_data = Property.get_by_id(self.current_property_id)
                    self.show_property_detail(self.current_property_id, property_data)
                QMessageBox.information(self, "成功", "部屋を追加しました。")
                
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"部屋追加中にエラーが発生しました: {str(e)}")
    
    def edit_current_unit(self):
        """部屋編集ダイアログを表示"""
        if not self.current_unit_id:
            QMessageBox.warning(self, "警告", "編集する部屋を選択してください。")
            return
        
        try:
            unit_data = Unit.get_by_id(self.current_unit_id)
            if not unit_data:
                QMessageBox.critical(self, "エラー", "部屋データが見つかりません。")
                return
            
            # 完全編集ダイアログを表示
            dialog = UnitEditDialog(self, unit_data)
            if dialog.exec() == dialog.DialogCode.Accepted:
                # UI更新
                self.load_property_tree()
                updated_unit_data = Unit.get_by_id(self.current_unit_id)
                self.show_unit_detail(self.current_unit_id, updated_unit_data)
                
                # 物件詳細の部屋一覧も更新
                if self.current_property_id:
                    self.load_property_units(self.current_property_id)
                
                QMessageBox.information(self, "成功", "部屋情報を更新しました。")
                
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"部屋編集中にエラーが発生しました: {str(e)}")
    
    def delete_current_unit(self):
        """部屋削除"""
        if not self.current_unit_id:
            QMessageBox.warning(self, "警告", "削除する部屋を選択してください。")
            return
        
        try:
            unit_data = Unit.get_by_id(self.current_unit_id)
            if not unit_data:
                QMessageBox.critical(self, "エラー", "部屋データが見つかりません。")
                return
            
            # 確認ダイアログ
            reply = QMessageBox.question(
                self, "確認", 
                f"部屋「{unit_data.get('room_number', '')}」を削除しますか？\n\n注意: この操作は取り消せません。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                Unit.delete(self.current_unit_id)
                
                # UI更新
                self.load_property_tree()
                
                # 物件詳細画面に戻る
                if self.current_property_id and self.current_property_data:
                    self.set_property_selection(self.current_property_id, self.current_property_data)
                    self.show_property_detail(self.current_property_id, self.current_property_data)
                
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


class DocumentUploadDialog(QDialog):
    """資料アップロードダイアログ"""
    
    def __init__(self, parent, property_id, unit_id=None):
        super().__init__(parent)
        self.property_id = property_id
        self.unit_id = unit_id
        self.document_storage_path = parent.document_storage_path
        self.init_ui()
    
    def init_ui(self):
        """UIを初期化"""
        self.setWindowTitle("資料アップロード")
        self.setModal(True)
        self.resize(500, 300)
        
        layout = QVBoxLayout(self)
        
        # 対象表示
        target_group = QGroupBox("アップロード対象")
        target_layout = QVBoxLayout()
        
        # 物件・部屋名を取得して表示
        try:
            property_data = Property.get_by_id(self.property_id)
            property_name = property_data.get('name', f'物件ID:{self.property_id}') if property_data else f'物件ID:{self.property_id}'
            
            if self.unit_id:
                unit_data = Unit.get_by_id(self.unit_id)
                room_number = unit_data.get('room_number', f'部屋ID:{self.unit_id}') if unit_data else f'部屋ID:{self.unit_id}'
                target_text = f"📍 {property_name} - {room_number} の資料"
            else:
                target_text = f"📍 {property_name} (物件全体) の資料"
        except:
            # エラー時のフォールバック
            if self.unit_id:
                target_text = f"📍 部屋ID: {self.unit_id} の資料"
            else:
                target_text = f"📍 物件ID: {self.property_id} 全体の資料"
        
        target_label = QLabel(target_text)
        target_label.setStyleSheet("font-weight: 600; color: #1e40af;")
        target_layout.addWidget(target_label)
        target_group.setLayout(target_layout)
        
        # ファイル選択
        file_group = QGroupBox("ファイル選択")
        file_layout = QVBoxLayout()
        
        file_select_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("ファイルを選択...")
        self.file_path_edit.setReadOnly(True)
        
        browse_btn = QPushButton("📁 参照")
        browse_btn.clicked.connect(self.browse_file)
        
        file_select_layout.addWidget(self.file_path_edit, 1)
        file_select_layout.addWidget(browse_btn)
        
        file_layout.addLayout(file_select_layout)
        file_group.setLayout(file_layout)
        
        # 資料種別
        type_group = QGroupBox("資料情報")
        type_layout = QFormLayout()
        
        self.document_type_combo = QComboBox()
        self.document_type_combo.addItems([
            "募集図面", "契約書", "重要事項説明書", "登記簿謄本", 
            "申込書", "見積書", "鍵預り証", "写真", "その他書類"
        ])
        
        self.document_memo_edit = QTextEdit()
        self.document_memo_edit.setMaximumHeight(60)
        self.document_memo_edit.setPlaceholderText("資料の説明・メモ")
        
        type_layout.addRow("資料種別:", self.document_type_combo)
        type_layout.addRow("説明・メモ:", self.document_memo_edit)
        
        type_group.setLayout(type_layout)
        
        # レイアウト追加
        layout.addWidget(target_group)
        layout.addWidget(file_group)
        layout.addWidget(type_group)
        
        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.upload_document)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
    
    def browse_file(self):
        """ファイル選択"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "資料ファイルを選択", "", 
            "すべてのファイル (*);;画像ファイル (*.png *.jpg *.jpeg *.bmp);;PDFファイル (*.pdf);;Officeファイル (*.doc *.docx *.xls *.xlsx)"
        )
        if file_path:
            self.file_path_edit.setText(file_path)
    
    def upload_document(self):
        """資料をアップロード"""
        file_path = self.file_path_edit.text().strip()
        
        if not file_path:
            QMessageBox.warning(self, "警告", "ファイルを選択してください。")
            return
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "警告", "選択されたファイルが存在しません。")
            return
        
        try:
            # ファイルを資料保存ディレクトリにコピー
            file_name = os.path.basename(file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            doc_type = self.document_type_combo.currentText()
            
            if self.unit_id:
                # 部屋固有の資料
                target_dir = os.path.join(self.document_storage_path, f"property_{self.property_id}", f"unit_{self.unit_id}")
                target_name = f"{timestamp}_{doc_type}_{file_name}"
            else:
                # 物件全体の資料
                target_dir = os.path.join(self.document_storage_path, f"property_{self.property_id}", "general")
                target_name = f"{timestamp}_{doc_type}_{file_name}"
            
            os.makedirs(target_dir, exist_ok=True)
            target_path = os.path.join(target_dir, target_name)
            
            shutil.copy2(file_path, target_path)
            
            # TODO: データベースに資料情報を保存（将来の拡張）
            
            QMessageBox.information(self, "成功", f"資料をアップロードしました。\n保存先: {target_path}")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"資料のアップロードに失敗しました: {str(e)}")


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
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # ヘッダー
        if self.unit_id:
            header_text = f"📍 部屋 {self.unit_id} の資料一覧"
        else:
            header_text = f"📍 物件 {self.property_id} の資料一覧"
        
        header = QLabel(header_text)
        header.setStyleSheet("font-size: 16px; font-weight: 600; color: #1e40af; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # 資料テーブル
        self.documents_table = QTableWidget()
        self.documents_table.setColumnCount(4)
        self.documents_table.setHorizontalHeaderLabels([
            "資料種別", "ファイル名", "サイズ", "更新日時"
        ])
        
        # テーブル設定
        self.documents_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.documents_table.setAlternatingRowColors(True)
        
        # 列幅調整
        header = self.documents_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.documents_table)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        open_btn = QPushButton("📂 ファイルを開く")
        open_btn.clicked.connect(self.open_selected_file)
        
        open_folder_btn = QPushButton("📁 フォルダを開く")
        open_folder_btn.clicked.connect(self.open_folder)
        
        close_btn = QPushButton("閉じる")
        close_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(open_btn)
        button_layout.addWidget(open_folder_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def load_documents(self):
        """資料一覧を読み込み"""
        try:
            if not os.path.exists(self.docs_dir):
                return
            
            files = []
            for file_name in os.listdir(self.docs_dir):
                file_path = os.path.join(self.docs_dir, file_name)
                if os.path.isfile(file_path):
                    # ファイル情報を取得
                    stat = os.stat(file_path)
                    size = stat.st_size
                    mtime = datetime.fromtimestamp(stat.st_mtime)
                    
                    # ファイル名から資料種別を推定
                    doc_type = "その他"
                    if "募集図面" in file_name:
                        doc_type = "募集図面"
                    elif "契約書" in file_name:
                        doc_type = "契約書"
                    elif "重要事項説明書" in file_name:
                        doc_type = "重要事項説明書"
                    elif "登記簿謄本" in file_name:
                        doc_type = "登記簿謄本"
                    elif "写真" in file_name:
                        doc_type = "写真"
                    
                    files.append({
                        'name': file_name,
                        'path': file_path,
                        'type': doc_type,
                        'size': size,
                        'mtime': mtime
                    })
            
            # テーブルに追加
            self.documents_table.setRowCount(len(files))
            for i, file_info in enumerate(files):
                self.documents_table.setItem(i, 0, QTableWidgetItem(file_info['type']))
                self.documents_table.setItem(i, 1, QTableWidgetItem(file_info['name']))
                
                # サイズを人間が読みやすい形式に
                size_str = self.format_file_size(file_info['size'])
                self.documents_table.setItem(i, 2, QTableWidgetItem(size_str))
                
                # 日時をフォーマット
                mtime_str = file_info['mtime'].strftime("%Y/%m/%d %H:%M")
                self.documents_table.setItem(i, 3, QTableWidgetItem(mtime_str))
                
                # ファイルパスを保存
                self.documents_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, file_info['path'])
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"資料一覧の読み込みに失敗しました: {str(e)}")
    
    def format_file_size(self, size_bytes):
        """ファイルサイズを人間が読みやすい形式に変換"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 ** 3:
            return f"{size_bytes / (1024 ** 2):.1f} MB"
        else:
            return f"{size_bytes / (1024 ** 3):.1f} GB"
    
    def open_selected_file(self):
        """選択されたファイルを開く"""
        current_row = self.documents_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "ファイルを選択してください。")
            return
        
        try:
            file_path = self.documents_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
            if file_path and os.path.exists(file_path):
                # システムのデフォルトアプリケーションでファイルを開く
                import subprocess
                import platform
                
                if platform.system() == 'Windows':
                    os.startfile(file_path)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.run(['open', file_path])
                else:  # Linux
                    subprocess.run(['xdg-open', file_path])
            else:
                QMessageBox.warning(self, "警告", "ファイルが見つかりません。")
                
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"ファイルを開く際にエラーが発生しました: {str(e)}")
    
    def open_folder(self):
        """資料フォルダを開く"""
        try:
            if os.path.exists(self.docs_dir):
                import subprocess
                import platform
                
                if platform.system() == 'Windows':
                    os.startfile(self.docs_dir)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.run(['open', self.docs_dir])
                else:  # Linux
                    subprocess.run(['xdg-open', self.docs_dir])
            else:
                QMessageBox.warning(self, "警告", "フォルダが見つかりません。")
                
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"フォルダを開く際にエラーが発生しました: {str(e)}")