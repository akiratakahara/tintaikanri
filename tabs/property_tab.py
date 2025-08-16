from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QLineEdit, 
                             QTextEdit, QMessageBox, QGroupBox, QFormLayout, 
                             QSpinBox, QTabWidget, QScrollArea, QFileDialog, QComboBox)
import os
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from models import Property, BuildingRegistry, LandRegistry, RegistryDocument, Customer, FloorDetail, FloorOccupancy, RecruitmentStatus

# OCR機能をオプショナルにする
try:
    from registry_ocr_improved import RegistryOCRImproved
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("注意: OCR機能が利用できません（Google Generative AI未インストール）")

class RegistryOCRWorker(QThread):
    """登記簿OCR処理を非同期で実行するワーカースレッド"""
    finished = pyqtSignal(dict)  # OCR結果
    error = pyqtSignal(str)
    
    def __init__(self, pdf_path: str, document_type: str):
        super().__init__()
        self.pdf_path = pdf_path
        self.document_type = document_type
        if OCR_AVAILABLE:
            self.ocr = RegistryOCRImproved()
        else:
            self.ocr = None
    
    def run(self):
        try:
            if not OCR_AVAILABLE:
                self.error.emit("OCR機能が利用できません")
                return
                
            if self.document_type == "建物登記簿":
                result = self.ocr.extract_building_info(self.pdf_path)
            else:
                result = self.ocr.extract_land_info(self.pdf_path)
            
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(str(e))

class PropertyTab(QWidget):
    def __init__(self):
        super().__init__()
        self.current_property_id = None
        self.building_ocr_result = None
        self.land_ocr_result = None
        self.owner_customers = []
        self.init_ui()
        self.load_properties()
        self.load_owner_customers()
        self.add_sample_data()  # サンプルデータを追加
        
    def add_sample_data(self):
        """テスト用のサンプルデータを追加"""
        try:
            # 既存のデータがあるかチェック
            existing_properties = Property.get_all()
            if not existing_properties:
                # サンプル物件を追加
                property_id = Property.create(
                    name="サンプル物件A",
                    address="東京都渋谷区○○1-2-3",
                    structure="RC造5階建",
                    registry_owner="サンプルオーナー株式会社",
                    management_type="自社管理",
                    available_rooms=2,
                    renewal_rooms=1,
                    notes="テスト用サンプル物件"
                )
                
                # サンプル顧客を追加
                customer_id = Customer.create(
                    name="サンプルテナント株式会社",
                    customer_type="tenant",
                    phone="03-1234-5678",
                    email="sample@example.com",
                    address="東京都新宿区○○4-5-6"
                )
                
                # 物件一覧を再読み込み
                self.load_properties()
                self.load_owner_customers()
                
        except Exception as e:
            print(f"サンプルデータ追加エラー: {str(e)}")
    
    def init_ui(self):
        # メインレイアウトをスクロールエリアで囲む
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        
        # 謄本アップロードタブ（新機能）
        self.upload_tab = self.create_upload_tab()
        self.tab_widget.addTab(self.upload_tab, "謄本アップロード")
        
        # 基本情報タブ
        self.basic_tab = self.create_basic_tab()
        self.tab_widget.addTab(self.basic_tab, "基本情報")
        
        # 建物登記簿タブ
        self.building_tab = self.create_building_tab()
        self.tab_widget.addTab(self.building_tab, "建物登記簿")
        
        # 土地登記簿タブ
        self.land_tab = self.create_land_tab()
        self.tab_widget.addTab(self.land_tab, "土地登記簿")
        
        # 階層詳細タブ（新規追加）
        self.floor_tab = self.create_floor_tab()
        self.tab_widget.addTab(self.floor_tab, "階層詳細")
        
        main_layout.addWidget(self.tab_widget)
        
        # 物件一覧テーブル
        property_list_group = QGroupBox("物件一覧")
        property_list_layout = QVBoxLayout()
        
        self.property_table = QTableWidget()
        self.property_table.setColumnCount(8)
        self.property_table.setHorizontalHeaderLabels([
            "ID", "物件名", "住所", "管理形態", "募集中", "更新予定", "書類状況", "最終更新"
        ])
        
        # テーブルのサイズ調整
        self.property_table.setMinimumHeight(200)
        self.property_table.horizontalHeader().setStretchLastSection(True)
        
        # ダブルクリックで詳細表示
        self.property_table.cellDoubleClicked.connect(self.show_property_detail)
        
        property_list_layout.addWidget(self.property_table)
        property_list_group.setLayout(property_list_layout)
        
        main_layout.addWidget(property_list_group)
        
        # メインウィジェットにレイアウトを設定
        main_widget.setLayout(main_layout)
        
        # スクロールエリアを作成
        scroll_area = QScrollArea()
        scroll_area.setWidget(main_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # メインレイアウトにスクロールエリアを追加
        layout = QVBoxLayout()
        layout.addWidget(scroll_area)
        self.setLayout(layout)
        
    def create_basic_tab(self):
        """基本情報タブを作成"""
        # メインウィジェット
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # 基本情報フォーム
        form_group = QGroupBox("物件基本情報")
        form_layout = QFormLayout()
        
        self.property_name_edit = QLineEdit()
        self.address_edit = QTextEdit()
        self.address_edit.setMaximumHeight(80)
        self.structure_edit = QLineEdit()
        self.registry_owner_edit = QLineEdit()
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        
        form_layout.addRow("物件名:", self.property_name_edit)
        form_layout.addRow("住所:", self.address_edit)
        form_layout.addRow("構造:", self.structure_edit)
        form_layout.addRow("登記所有者:", self.registry_owner_edit)
        form_layout.addRow("備考:", self.notes_edit)
        
        form_group.setLayout(form_layout)
        
        # オーナー情報
        owner_group = QGroupBox("オーナー情報")
        owner_layout = QVBoxLayout()
        
        # オーナー選択
        owner_select_layout = QHBoxLayout()
        self.owner_combo = QComboBox()
        self.owner_combo.setEditable(False)
        self.add_owner_button = QPushButton("オーナー追加")
        self.add_owner_button.clicked.connect(self.add_owner_to_property)
        owner_select_layout.addWidget(QLabel("オーナー選択:"))
        owner_select_layout.addWidget(self.owner_combo, 1)
        owner_select_layout.addWidget(self.add_owner_button)
        
        # オーナー一覧テーブル
        self.owner_table = QTableWidget()
        self.owner_table.setColumnCount(5)
        self.owner_table.setHorizontalHeaderLabels([
            "オーナー名", "所有比率(%)", "主要", "連絡先", "操作"
        ])
        self.owner_table.setMaximumHeight(150)
        
        owner_layout.addLayout(owner_select_layout)
        owner_layout.addWidget(self.owner_table)
        owner_group.setLayout(owner_layout)
        
        # 運用状況
        operation_group = QGroupBox("運用状況")
        operation_layout = QFormLayout()
        
        self.management_type_combo = QComboBox()
        self.management_type_combo.addItems(["自社管理", "他社仲介", "共同管理"])
        
        self.available_rooms_spin = QSpinBox()
        self.available_rooms_spin.setRange(0, 999)
        self.available_rooms_spin.setSuffix(" 室")
        
        self.renewal_rooms_spin = QSpinBox()
        self.renewal_rooms_spin.setRange(0, 999)
        self.renewal_rooms_spin.setSuffix(" 室")
        
        self.management_company_edit = QLineEdit()
        self.management_company_edit.setPlaceholderText("管理会社名（他社仲介の場合）")
        
        operation_layout.addRow("管理形態:", self.management_type_combo)
        operation_layout.addRow("募集中部屋数:", self.available_rooms_spin)
        operation_layout.addRow("更新予定部屋数:", self.renewal_rooms_spin)
        operation_layout.addRow("管理会社:", self.management_company_edit)
        
        operation_group.setLayout(operation_layout)
        
        # 資料管理状況
        document_group = QGroupBox("資料管理状況")
        document_layout = QVBoxLayout()
        
        self.document_status_table = QTableWidget()
        self.document_status_table.setColumnCount(4)
        self.document_status_table.setHorizontalHeaderLabels([
            "書類種別", "有無", "最終更新日", "備考"
        ])
        self.document_status_table.setMaximumHeight(150)
        
        # デフォルトの書類リスト
        default_documents = [
            "建物登記簿", "土地登記簿", "重要事項説明書", "賃貸契約書",
            "管理規約", "修繕積立金規約", "駐車場規約", "その他"
        ]
        
        self.document_status_table.setRowCount(len(default_documents))
        for i, doc_type in enumerate(default_documents):
            self.document_status_table.setItem(i, 0, QTableWidgetItem(doc_type))
            self.document_status_table.setItem(i, 1, QTableWidgetItem("未登録"))
            self.document_status_table.setItem(i, 2, QTableWidgetItem("-"))
            self.document_status_table.setItem(i, 3, QTableWidgetItem(""))
        
        document_layout.addWidget(self.document_status_table)
        document_group.setLayout(document_layout)
        
        # ボタン
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.add_property)
        self.update_button = QPushButton("更新")
        self.update_button.clicked.connect(self.update_property)
        self.delete_button = QPushButton("削除")
        self.delete_button.clicked.connect(self.delete_property)
        self.clear_button = QPushButton("クリア")
        self.clear_button.clicked.connect(self.clear_basic_form)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        
        # メインレイアウトに追加
        main_layout.addWidget(form_group)
        main_layout.addWidget(owner_group)
        main_layout.addWidget(operation_group)
        main_layout.addWidget(document_group)
        main_layout.addLayout(button_layout)
        main_layout.addStretch()
        
        # メインウィジェットにレイアウトを設定
        main_widget.setLayout(main_layout)
        
        # スクロールエリアを作成
        scroll_area = QScrollArea()
        scroll_area.setWidget(main_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # スクロールエリアを返す
        return scroll_area
    
    def create_building_tab(self):
        """建物登記簿タブを作成"""
        # メインウィジェット
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # 建物登記簿フォーム
        form_group = QGroupBox("建物登記簿情報")
        form_layout = QFormLayout()
        
        self.building_owner_edit = QLineEdit()
        self.building_address_edit = QTextEdit()
        self.building_address_edit.setMaximumHeight(60)
        self.building_structure_edit = QLineEdit()
        self.building_floors_spin = QSpinBox()
        self.building_floors_spin.setMaximum(999)
        self.building_area_spin = QSpinBox()
        self.building_area_spin.setMaximum(99999)
        self.building_date_edit = QLineEdit()
        self.building_date_edit.setPlaceholderText("例: 2020年3月")
        self.building_registry_date_edit = QLineEdit()
        self.building_registry_date_edit.setPlaceholderText("例: 2020年3月15日")
        self.building_mortgage_edit = QTextEdit()
        self.building_mortgage_edit.setMaximumHeight(60)
        self.building_notes_edit = QTextEdit()
        self.building_notes_edit.setMaximumHeight(60)
        
        form_layout.addRow("建物所有者:", self.building_owner_edit)
        form_layout.addRow("建物登記住所:", self.building_address_edit)
        form_layout.addRow("建物構造:", self.building_structure_edit)
        form_layout.addRow("建物階数:", self.building_floors_spin)
        form_layout.addRow("建物面積(㎡):", self.building_area_spin)
        form_layout.addRow("建築年月:", self.building_date_edit)
        form_layout.addRow("建物登記年月日:", self.building_registry_date_edit)
        form_layout.addRow("建物抵当権:", self.building_mortgage_edit)
        form_layout.addRow("備考:", self.building_notes_edit)
        
        form_group.setLayout(form_layout)
        
        # ボタン
        button_layout = QHBoxLayout()
        self.add_building_button = QPushButton("建物登記簿登録")
        self.add_building_button.clicked.connect(self.add_building_registry)
        self.clear_building_button = QPushButton("クリア")
        self.clear_building_button.clicked.connect(self.clear_building_form)
        
        button_layout.addWidget(self.add_building_button)
        button_layout.addWidget(self.clear_building_button)
        button_layout.addStretch()
        
        # 建物登記簿一覧
        table_group = QGroupBox("建物登記簿一覧")
        table_layout = QVBoxLayout()
        
        self.building_table = QTableWidget()
        self.building_table.setColumnCount(7)
        self.building_table.setHorizontalHeaderLabels([
            "ID", "所有者", "構造", "階数", "面積", "建築年月", "登記年月日"
        ])
        self.building_table.setMinimumHeight(150)
        
        table_layout.addWidget(self.building_table)
        table_group.setLayout(table_layout)
        
        # メインレイアウトに追加
        main_layout.addWidget(form_group)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(table_group)
        
        # メインウィジェットにレイアウトを設定
        main_widget.setLayout(main_layout)
        
        # スクロールエリアを作成
        scroll_area = QScrollArea()
        scroll_area.setWidget(main_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # スクロールエリアを返す
        return scroll_area
    
    def create_land_tab(self):
        """土地登記簿タブを作成"""
        # メインウィジェット
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # 土地登記簿フォーム
        form_group = QGroupBox("土地登記簿情報")
        form_layout = QFormLayout()
        
        self.land_number_edit = QLineEdit()
        self.land_number_edit.setPlaceholderText("例: 1-2-3")
        self.land_owner_edit = QLineEdit()
        self.land_address_edit = QTextEdit()
        self.land_address_edit.setMaximumHeight(60)
        self.land_area_spin = QSpinBox()
        self.land_area_spin.setMaximum(99999)
        self.land_use_edit = QLineEdit()
        self.land_registry_date_edit = QLineEdit()
        self.land_registry_date_edit.setPlaceholderText("例: 2020年3月15日")
        self.land_mortgage_edit = QTextEdit()
        self.land_mortgage_edit.setMaximumHeight(60)
        self.land_notes_edit = QTextEdit()
        self.land_notes_edit.setMaximumHeight(60)
        
        form_layout.addRow("土地番号:", self.land_number_edit)
        form_layout.addRow("土地所有者:", self.land_owner_edit)
        form_layout.addRow("土地住所:", self.land_address_edit)
        form_layout.addRow("土地面積(㎡):", self.land_area_spin)
        form_layout.addRow("土地用途:", self.land_use_edit)
        form_layout.addRow("土地登記年月日:", self.land_registry_date_edit)
        form_layout.addRow("土地抵当権:", self.land_mortgage_edit)
        form_layout.addRow("備考:", self.land_notes_edit)
        
        form_group.setLayout(form_layout)
        
        # ボタン
        button_layout = QHBoxLayout()
        self.add_land_button = QPushButton("土地登記簿登録")
        self.add_land_button.clicked.connect(self.add_land_registry)
        self.clear_land_button = QPushButton("クリア")
        self.clear_land_button.clicked.connect(self.clear_land_form)
        
        button_layout.addWidget(self.add_land_button)
        button_layout.addWidget(self.clear_land_button)
        button_layout.addStretch()
        
        # 土地登記簿一覧
        table_group = QGroupBox("土地登記簿一覧")
        table_layout = QVBoxLayout()
        
        self.land_table = QTableWidget()
        self.land_table.setColumnCount(7)
        self.land_table.setHorizontalHeaderLabels([
            "ID", "土地番号", "所有者", "住所", "面積", "用途", "登記年月日"
        ])
        self.land_table.setMinimumHeight(150)
        
        table_layout.addWidget(self.land_table)
        table_group.setLayout(table_layout)
        
        # メインレイアウトに追加
        main_layout.addWidget(form_group)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(table_group)
        
        # メインウィジェットにレイアウトを設定
        main_widget.setLayout(main_layout)
        
        # スクロールエリアを作成
        scroll_area = QScrollArea()
        scroll_area.setWidget(main_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # スクロールエリアを返す
        return scroll_area
    
    def create_floor_tab(self):
        """階層詳細タブを作成"""
        # メインウィジェット
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # 階層一覧
        floor_list_group = QGroupBox("階層一覧")
        floor_list_layout = QVBoxLayout()
        
        self.floor_table = QTableWidget()
        self.floor_table.setColumnCount(8)
        self.floor_table.setHorizontalHeaderLabels([
            "階層", "総面積(㎡)", "謄本面積(㎡)", "用途", "空き面積(㎡)", "入居面積(㎡)", "入居テナント", "募集状況"
        ])
        self.floor_table.setMaximumHeight(200)
        
        # ダブルクリックで詳細表示
        self.floor_table.cellDoubleClicked.connect(self.show_floor_detail)
        
        floor_list_layout.addWidget(self.floor_table)
        floor_list_group.setLayout(floor_list_layout)
        
        # 階層詳細フォーム
        floor_form_group = QGroupBox("階層詳細")
        floor_form_layout = QFormLayout()
        
        self.floor_number_edit = QLineEdit()
        self.floor_number_edit.setPlaceholderText("例: 1F, 2F, 3F")
        
        self.floor_name_edit = QLineEdit()
        self.floor_name_edit.setPlaceholderText("例: 1階、2階、3階")
        
        self.floor_total_area_spin = QSpinBox()
        self.floor_total_area_spin.setRange(0, 99999)
        self.floor_total_area_spin.setSuffix(" ㎡")
        
        self.floor_registry_area_spin = QSpinBox()
        self.floor_registry_area_spin.setRange(0, 99999)
        self.floor_registry_area_spin.setSuffix(" ㎡")
        
        self.floor_usage_combo = QComboBox()
        self.floor_usage_combo.addItems(["オフィス", "店舗", "住宅", "倉庫", "駐車場", "その他"])
        self.floor_usage_combo.setEditable(True)
        
        self.floor_available_area_spin = QSpinBox()
        self.floor_available_area_spin.setRange(0, 99999)
        self.floor_available_area_spin.setSuffix(" ㎡")
        
        self.floor_occupied_area_spin = QSpinBox()
        self.floor_occupied_area_spin.setRange(0, 99999)
        self.floor_occupied_area_spin.setSuffix(" ㎡")
        
        self.floor_notes_edit = QTextEdit()
        self.floor_notes_edit.setMaximumHeight(60)
        
        floor_form_layout.addRow("階層番号:", self.floor_number_edit)
        floor_form_layout.addRow("階層名:", self.floor_name_edit)
        floor_form_layout.addRow("総面積(㎡):", self.floor_total_area_spin)
        floor_form_layout.addRow("謄本面積(㎡):", self.floor_registry_area_spin)
        floor_form_layout.addRow("用途:", self.floor_usage_combo)
        floor_form_layout.addRow("空き面積(㎡):", self.floor_available_area_spin)
        floor_form_layout.addRow("入居面積(㎡):", self.floor_occupied_area_spin)
        floor_form_layout.addRow("備考:", self.floor_notes_edit)
        
        floor_form_group.setLayout(floor_form_layout)
        
        # ボタン
        button_layout = QHBoxLayout()
        self.add_floor_button = QPushButton("階層を追加")
        self.add_floor_button.clicked.connect(self.add_floor)
        self.update_floor_button = QPushButton("階層を更新")
        self.update_floor_button.clicked.connect(self.update_floor)
        self.delete_floor_button = QPushButton("階層を削除")
        self.delete_floor_button.clicked.connect(self.delete_floor)
        self.clear_floor_button = QPushButton("クリア")
        self.clear_floor_button.clicked.connect(self.clear_floor_form)
        
        button_layout.addWidget(self.add_floor_button)
        button_layout.addWidget(self.update_floor_button)
        button_layout.addWidget(self.delete_floor_button)
        button_layout.addWidget(self.clear_floor_button)
        button_layout.addStretch()
        
        # 入居状況・募集状況タブ
        detail_tab_widget = QTabWidget()
        
        # 入居状況タブ
        occupancy_tab = self.create_occupancy_tab()
        detail_tab_widget.addTab(occupancy_tab, "入居状況")
        
        # 募集状況タブ
        recruitment_tab = self.create_recruitment_tab()
        detail_tab_widget.addTab(recruitment_tab, "募集状況")
        
        # メインレイアウトに追加
        main_layout.addWidget(floor_list_group)
        main_layout.addWidget(floor_form_group)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(detail_tab_widget)
        
        # メインウィジェットにレイアウトを設定
        main_widget.setLayout(main_layout)
        
        # スクロールエリアを作成
        scroll_area = QScrollArea()
        scroll_area.setWidget(main_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # スクロールエリアを返す
        return scroll_area
    
    def create_occupancy_tab(self):
        """入居状況タブを作成"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 入居状況一覧
        self.occupancy_table = QTableWidget()
        self.occupancy_table.setColumnCount(8)
        self.occupancy_table.setHorizontalHeaderLabels([
            "部屋番号", "テナント名", "入居面積(㎡)", "契約開始日", "契約終了日", "賃料", "管理費", "状況"
        ])
        self.occupancy_table.setMaximumHeight(150)
        
        # 入居状況フォーム
        occupancy_form_group = QGroupBox("入居状況登録")
        occupancy_form_layout = QFormLayout()
        
        self.occupancy_unit_combo = QComboBox()
        self.occupancy_unit_combo.addItem("部屋を選択", None)
        
        self.occupancy_tenant_combo = QComboBox()
        self.occupancy_tenant_combo.addItem("テナントを選択", None)
        
        self.occupancy_area_spin = QSpinBox()
        self.occupancy_area_spin.setRange(0, 99999)
        self.occupancy_area_spin.setSuffix(" ㎡")
        
        self.occupancy_start_date_edit = QLineEdit()
        self.occupancy_start_date_edit.setPlaceholderText("例: 2024-01-01")
        
        self.occupancy_end_date_edit = QLineEdit()
        self.occupancy_end_date_edit.setPlaceholderText("例: 2026-12-31")
        
        self.occupancy_rent_spin = QSpinBox()
        self.occupancy_rent_spin.setRange(0, 9999999)
        self.occupancy_rent_spin.setSuffix(" 円")
        
        self.occupancy_maintenance_spin = QSpinBox()
        self.occupancy_maintenance_spin.setRange(0, 999999)
        self.occupancy_maintenance_spin.setSuffix(" 円")
        
        self.occupancy_status_combo = QComboBox()
        self.occupancy_status_combo.addItems(["入居中", "空室", "予約済み"])
        
        occupancy_form_layout.addRow("部屋:", self.occupancy_unit_combo)
        occupancy_form_layout.addRow("テナント:", self.occupancy_tenant_combo)
        occupancy_form_layout.addRow("入居面積(㎡):", self.occupancy_area_spin)
        occupancy_form_layout.addRow("契約開始日:", self.occupancy_start_date_edit)
        occupancy_form_layout.addRow("契約終了日:", self.occupancy_end_date_edit)
        occupancy_form_layout.addRow("賃料:", self.occupancy_rent_spin)
        occupancy_form_layout.addRow("管理費:", self.occupancy_maintenance_spin)
        occupancy_form_layout.addRow("状況:", self.occupancy_status_combo)
        
        occupancy_form_group.setLayout(occupancy_form_layout)
        
        # ボタン
        occupancy_button_layout = QHBoxLayout()
        self.add_occupancy_button = QPushButton("入居状況を登録")
        self.add_occupancy_button.clicked.connect(self.add_occupancy)
        self.clear_occupancy_button = QPushButton("クリア")
        self.clear_occupancy_button.clicked.connect(self.clear_occupancy_form)
        
        occupancy_button_layout.addWidget(self.add_occupancy_button)
        occupancy_button_layout.addWidget(self.clear_occupancy_button)
        occupancy_button_layout.addStretch()
        
        layout.addWidget(self.occupancy_table)
        layout.addWidget(occupancy_form_group)
        layout.addLayout(occupancy_button_layout)
        
        widget.setLayout(layout)
        return widget
    
    def create_recruitment_tab(self):
        """募集状況タブを作成"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 募集状況一覧
        self.recruitment_table = QTableWidget()
        self.recruitment_table.setColumnCount(8)
        self.recruitment_table.setHorizontalHeaderLabels([
            "部屋番号", "募集種別", "募集面積(㎡)", "想定賃料", "想定管理費", "募集開始日", "募集終了日", "状況"
        ])
        self.recruitment_table.setMaximumHeight(150)
        
        # 募集状況フォーム
        recruitment_form_group = QGroupBox("募集状況登録")
        recruitment_form_layout = QFormLayout()
        
        self.recruitment_unit_combo = QComboBox()
        self.recruitment_unit_combo.addItem("部屋を選択", None)
        
        self.recruitment_type_combo = QComboBox()
        self.recruitment_type_combo.addItems(["新規募集", "更新募集", "転貸募集"])
        
        self.recruitment_area_spin = QSpinBox()
        self.recruitment_area_spin.setRange(0, 99999)
        self.recruitment_area_spin.setSuffix(" ㎡")
        
        self.recruitment_rent_spin = QSpinBox()
        self.recruitment_rent_spin.setRange(0, 9999999)
        self.recruitment_rent_spin.setSuffix(" 円")
        
        self.recruitment_maintenance_spin = QSpinBox()
        self.recruitment_maintenance_spin.setRange(0, 999999)
        self.recruitment_maintenance_spin.setSuffix(" 円")
        
        self.recruitment_start_date_edit = QLineEdit()
        self.recruitment_start_date_edit.setPlaceholderText("例: 2024-01-01")
        
        self.recruitment_end_date_edit = QLineEdit()
        self.recruitment_end_date_edit.setPlaceholderText("例: 2024-12-31")
        
        self.recruitment_status_combo = QComboBox()
        self.recruitment_status_combo.addItems(["募集中", "一時停止", "終了"])
        
        self.recruitment_contact_edit = QLineEdit()
        self.recruitment_contact_edit.setPlaceholderText("担当者名")
        
        recruitment_form_layout.addRow("部屋:", self.recruitment_unit_combo)
        recruitment_form_layout.addRow("募集種別:", self.recruitment_type_combo)
        recruitment_form_layout.addRow("募集面積(㎡):", self.recruitment_area_spin)
        recruitment_form_layout.addRow("想定賃料:", self.recruitment_rent_spin)
        recruitment_form_layout.addRow("想定管理費:", self.recruitment_maintenance_spin)
        recruitment_form_layout.addRow("募集開始日:", self.recruitment_start_date_edit)
        recruitment_form_layout.addRow("募集終了日:", self.recruitment_end_date_edit)
        recruitment_form_layout.addRow("状況:", self.recruitment_status_combo)
        recruitment_form_layout.addRow("担当者:", self.recruitment_contact_edit)
        
        recruitment_form_group.setLayout(recruitment_form_layout)
        
        # ボタン
        recruitment_button_layout = QHBoxLayout()
        self.add_recruitment_button = QPushButton("募集状況を登録")
        self.add_recruitment_button.clicked.connect(self.add_recruitment)
        self.clear_recruitment_button = QPushButton("クリア")
        self.clear_recruitment_button.clicked.connect(self.clear_recruitment_form)
        
        recruitment_button_layout.addWidget(self.add_recruitment_button)
        recruitment_button_layout.addWidget(self.clear_recruitment_button)
        recruitment_button_layout.addStretch()
        
        layout.addWidget(self.recruitment_table)
        layout.addWidget(recruitment_form_group)
        layout.addLayout(recruitment_button_layout)
        
        widget.setLayout(layout)
        return widget
    
    def create_upload_tab(self):
        """謄本アップロードタブを作成（新機能統合）"""
        # メインウィジェット
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # 物件選択・作成
        property_group = QGroupBox("物件選択・作成")
        property_layout = QFormLayout()
        
        self.property_combo = QComboBox()
        self.property_combo.addItem("新規物件を作成", None)
        self.load_property_combo()
        
        self.new_property_name_edit = QLineEdit()
        self.new_property_name_edit.setPlaceholderText("新規物件名（新規作成の場合）")
        
        property_layout.addRow("物件:", self.property_combo)
        property_layout.addRow("新規物件名:", self.new_property_name_edit)
        property_group.setLayout(property_layout)
        
        # 建物登記簿アップロード（複数対応）
        building_group = QGroupBox("建物登記簿アップロード")
        building_layout = QVBoxLayout()
        
        # ファイルリスト
        self.building_files_list = QTableWidget()
        self.building_files_list.setColumnCount(5)
        self.building_files_list.setHorizontalHeaderLabels([
            "ファイル名", "ステータス", "OCR結果", "所有者", "操作"
        ])
        self.building_files_list.setMaximumHeight(150)
        
        # ファイル追加ボタン
        building_file_layout = QHBoxLayout()
        self.building_add_button = QPushButton("建物謄本を追加")
        self.building_add_button.clicked.connect(lambda: self.add_document_files("building"))
        self.building_process_all_button = QPushButton("全てOCR処理")
        self.building_process_all_button.clicked.connect(lambda: self.process_all_documents("building"))
        
        building_file_layout.addWidget(self.building_add_button)
        building_file_layout.addWidget(self.building_process_all_button)
        building_file_layout.addStretch()
        
        building_layout.addWidget(self.building_files_list)
        building_layout.addLayout(building_file_layout)
        building_group.setLayout(building_layout)
        
        # 土地登記簿アップロード（複数対応）
        land_group = QGroupBox("土地登記簿アップロード")
        land_layout = QVBoxLayout()
        
        # ファイルリスト
        self.land_files_list = QTableWidget()
        self.land_files_list.setColumnCount(5)
        self.land_files_list.setHorizontalHeaderLabels([
            "ファイル名", "ステータス", "OCR結果", "所有者", "操作"
        ])
        self.land_files_list.setMaximumHeight(150)
        
        # ファイル追加ボタン
        land_file_layout = QHBoxLayout()
        self.land_add_button = QPushButton("土地謄本を追加")
        self.land_add_button.clicked.connect(lambda: self.add_document_files("land"))
        self.land_process_all_button = QPushButton("全てOCR処理")
        self.land_process_all_button.clicked.connect(lambda: self.process_all_documents("land"))
        
        land_file_layout.addWidget(self.land_add_button)
        land_file_layout.addWidget(self.land_process_all_button)
        land_file_layout.addStretch()
        
        land_layout.addWidget(self.land_files_list)
        land_layout.addLayout(land_file_layout)
        land_group.setLayout(land_layout)
        
        # OCR結果表示・編集エリア
        ocr_group = QGroupBox("OCR結果・編集")
        ocr_layout = QVBoxLayout()
        
        # OCR結果表示
        self.ocr_result_text = QTextEdit()
        self.ocr_result_text.setMaximumHeight(200)
        self.ocr_result_text.setPlaceholderText("OCR結果がここに表示されます。テキストを編集してから自動入力ボタンを押してください。")
        
        # ボタン
        ocr_button_layout = QHBoxLayout()
        self.copy_ocr_button = QPushButton("OCR結果をコピー")
        self.copy_ocr_button.clicked.connect(self.copy_ocr_result)
        self.auto_fill_button = QPushButton("自動入力")
        self.auto_fill_button.clicked.connect(self.auto_fill_from_ocr)
        self.clear_ocr_button = QPushButton("クリア")
        self.clear_ocr_button.clicked.connect(self.clear_ocr_result)
        
        ocr_button_layout.addWidget(self.copy_ocr_button)
        ocr_button_layout.addWidget(self.auto_fill_button)
        ocr_button_layout.addWidget(self.clear_ocr_button)
        ocr_button_layout.addStretch()
        
        ocr_layout.addWidget(self.ocr_result_text)
        ocr_layout.addLayout(ocr_button_layout)
        ocr_group.setLayout(ocr_layout)
        
        # 紐づけ情報
        link_group = QGroupBox("紐づけ情報")
        link_layout = QFormLayout()
        
        # オーナー選択
        self.owner_combo = QComboBox()
        self.owner_combo.addItem("オーナーを選択", None)
        self.load_owner_combo()
        # connectはupload_tabだけ
        self.owner_combo.currentTextChanged.connect(self.on_owner_changed)
        
        # テナント選択
        self.tenant_combo = QComboBox()
        self.tenant_combo.addItem("テナントを選択", None)
        self.tenant_combo.currentTextChanged.connect(self.on_tenant_changed)
        
        # 部屋番号選択
        self.room_combo = QComboBox()
        self.room_combo.addItem("部屋番号を選択", None)
        
        link_layout.addRow("オーナー:", self.owner_combo)
        link_layout.addRow("テナント:", self.tenant_combo)
        link_layout.addRow("部屋番号:", self.room_combo)
        
        link_group.setLayout(link_layout)
        
        # 登録ボタン
        self.register_button = QPushButton("物件登録")
        self.register_button.clicked.connect(self.register_property)
        
        # メインレイアウトに追加
        main_layout.addWidget(property_group)
        main_layout.addWidget(building_group)
        main_layout.addWidget(land_group)
        main_layout.addWidget(ocr_group)
        main_layout.addWidget(link_group)
        main_layout.addWidget(self.register_button)
        main_layout.addStretch()
        
        # メインウィジェットにレイアウトを設定
        main_widget.setLayout(main_layout)
        
        # スクロールエリアを作成
        scroll_area = QScrollArea()
        scroll_area.setWidget(main_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # スクロールエリアを返す
        return scroll_area
    
    def add_property(self):
        """物件を登録"""
        property_name = self.property_name_edit.text().strip()
        if not property_name:
            QMessageBox.warning(self, "警告", "物件名を入力してください。")
            return
        
        try:
            self.current_property_id = Property.create(
                name=property_name,
                address=self.address_edit.toPlainText().strip(),
                structure=self.structure_edit.text().strip() or None,
                registry_owner=self.registry_owner_edit.text().strip() or None,
                management_type=self.management_type_combo.currentText(),
                management_company=self.management_company_edit.text().strip() or None,
                available_rooms=self.available_rooms_spin.value(),
                renewal_rooms=self.renewal_rooms_spin.value(),
                notes=self.notes_edit.toPlainText().strip() or None
            )
            
            QMessageBox.information(self, "成功", "物件を登録しました。")
            self.clear_basic_form()
            self.load_properties()
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"物件の登録に失敗しました: {str(e)}")
    
    def add_building_registry(self):
        """建物登記簿を登録"""
        if not self.current_property_id:
            QMessageBox.warning(self, "警告", "先に物件を登録してください。")
            return
        
        try:
            BuildingRegistry.create(
                property_id=self.current_property_id,
                registry_owner=self.building_owner_edit.text().strip() or None,
                registry_address=self.building_address_edit.toPlainText().strip() or None,
                building_structure=self.building_structure_edit.text().strip() or None,
                building_floors=self.building_floors_spin.value() if self.building_floors_spin.value() > 0 else None,
                building_area=self.building_area_spin.value() if self.building_area_spin.value() > 0 else None,
                building_date=self.building_date_edit.text().strip() or None,
                registry_date=self.building_registry_date_edit.text().strip() or None,
                mortgage_info=self.building_mortgage_edit.toPlainText().strip() or None,
                notes=self.building_notes_edit.toPlainText().strip() or None
            )
            
            QMessageBox.information(self, "成功", "建物登記簿を登録しました。")
            self.clear_building_form()
            self.load_building_registries()
            self.load_properties()  # 物件一覧も更新
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"建物登記簿の登録に失敗しました: {str(e)}")
    
    def add_land_registry(self):
        """土地登記簿を登録"""
        if not self.current_property_id:
            QMessageBox.warning(self, "警告", "先に物件を登録してください。")
            return
        
        try:
            LandRegistry.create(
                property_id=self.current_property_id,
                land_number=self.land_number_edit.text().strip() or None,
                land_owner=self.land_owner_edit.text().strip() or None,
                land_address=self.land_address_edit.toPlainText().strip() or None,
                land_area=self.land_area_spin.value() if self.land_area_spin.value() > 0 else None,
                land_use=self.land_use_edit.text().strip() or None,
                registry_date=self.land_registry_date_edit.text().strip() or None,
                mortgage_info=self.land_mortgage_edit.toPlainText().strip() or None,
                notes=self.land_notes_edit.toPlainText().strip() or None
            )
            
            QMessageBox.information(self, "成功", "土地登記簿を登録しました。")
            self.clear_land_form()
            self.load_land_registries()
            self.load_properties()  # 物件一覧も更新
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"土地登記簿の登録に失敗しました: {str(e)}")
    
    def add_owner_to_property(self):
        """物件にオーナーを追加"""
        if not self.current_property_id:
            QMessageBox.warning(self, "警告", "物件を選択してください")
            return
        
        owner_id = self.owner_combo.currentData()
        if not owner_id:
            # 新規オーナー登録
            from PyQt6.QtWidgets import QInputDialog, QDialog, QDialogButtonBox, QFormLayout
            dialog = QDialog(self)
            dialog.setWindowTitle("新規オーナー登録")
            layout = QFormLayout()
            
            name_edit = QLineEdit()
            phone_edit = QLineEdit()
            email_edit = QLineEdit()
            
            layout.addRow("オーナー名:", name_edit)
            layout.addRow("電話番号:", phone_edit)
            layout.addRow("メールアドレス:", email_edit)
            
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            dialog.setLayout(layout)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                if name_edit.text():
                    owner_id = Customer.create(
                        name=name_edit.text(),
                        customer_type='owner',
                        phone=phone_edit.text(),
                        email=email_edit.text()
                    )
                    self.load_owner_customers()
                else:
                    QMessageBox.warning(self, "警告", "オーナー名を入力してください")
                    return
            else:
                return
        
        # 所有比率を入力
        from PyQt6.QtWidgets import QInputDialog
        ratio, ok = QInputDialog.getDouble(self, "所有比率", "所有比率(%)を入力:", 100.0, 0.0, 100.0, 2)
        if not ok:
            return
        
        try:
            Property.add_owner(self.current_property_id, owner_id, ratio, is_primary=(ratio >= 50))
            self.load_property_owners()
            QMessageBox.information(self, "成功", "オーナーを追加しました")
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"オーナー追加中にエラーが発生しました: {str(e)}")
    
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
                self.owner_table.setItem(row, 2, QTableWidgetItem("主要" if owner.get('is_primary') else ""))
                contact = f"{owner.get('phone', '')} / {owner.get('email', '')}"
                self.owner_table.setItem(row, 3, QTableWidgetItem(contact))
                
                # 削除ボタン
                delete_button = QPushButton("削除")
                delete_button.clicked.connect(lambda checked, oid=owner['owner_id']: self.remove_owner_from_property(oid))
                self.owner_table.setCellWidget(row, 4, delete_button)
                
        except Exception as e:
            print(f"オーナー一覧読み込みエラー: {str(e)}")
    
    def remove_owner_from_property(self, owner_id):
        """物件からオーナーを削除"""
        if not self.current_property_id:
            return
        
        reply = QMessageBox.question(self, "確認", "このオーナーを物件から削除しますか？")
        if reply == QMessageBox.StandardButton.Yes:
            try:
                Property.remove_owner(self.current_property_id, owner_id)
                self.load_property_owners()
                QMessageBox.information(self, "成功", "オーナーを削除しました")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"オーナー削除中にエラーが発生しました: {str(e)}")
    
    def clear_basic_form(self):
        """基本情報フォームをクリア"""
        self.property_name_edit.clear()
        self.address_edit.clear()
        self.structure_edit.clear()
        self.registry_owner_edit.clear()
        self.management_type_combo.setCurrentIndex(0)
        self.management_company_edit.clear()
        self.available_rooms_spin.setValue(0)
        self.renewal_rooms_spin.setValue(0)
        self.notes_edit.clear()
    
    def clear_building_form(self):
        """建物登記簿フォームをクリア"""
        self.building_owner_edit.clear()
        self.building_address_edit.clear()
        self.building_structure_edit.clear()
        self.building_floors_spin.setValue(0)
        self.building_area_spin.setValue(0)
        self.building_date_edit.clear()
        self.building_registry_date_edit.clear()
        self.building_mortgage_edit.clear()
        self.building_notes_edit.clear()
    
    def clear_land_form(self):
        """土地登記簿フォームをクリア"""
        self.land_number_edit.clear()
        self.land_owner_edit.clear()
        self.land_address_edit.clear()
        self.land_area_spin.setValue(0)
        self.land_use_edit.clear()
        self.land_registry_date_edit.clear()
        self.land_mortgage_edit.clear()
        self.land_notes_edit.clear()
    
    def load_properties(self):
        """物件一覧をテーブルに読み込み"""
        try:
            properties = Property.get_all()
            
            self.property_table.setRowCount(len(properties))
            for i, property_obj in enumerate(properties):
                self.property_table.setItem(i, 0, QTableWidgetItem(str(property_obj['id'])))
                self.property_table.setItem(i, 1, QTableWidgetItem(property_obj['name']))
                self.property_table.setItem(i, 2, QTableWidgetItem(property_obj['address'] or ""))
                self.property_table.setItem(i, 3, QTableWidgetItem(property_obj.get('management_type', '自社管理')))
                self.property_table.setItem(i, 4, QTableWidgetItem(str(property_obj.get('available_rooms', 0))))
                self.property_table.setItem(i, 5, QTableWidgetItem(str(property_obj.get('renewal_rooms', 0))))
                
                # 書類状況を取得
                building_count = len(BuildingRegistry.get_by_property(property_obj['id']))
                land_count = len(LandRegistry.get_by_property(property_obj['id']))
                document_status = f"建物:{building_count} 土地:{land_count}"
                self.property_table.setItem(i, 6, QTableWidgetItem(document_status))
                
                # 最終更新日
                updated_at = property_obj.get('updated_at', '')
                if updated_at:
                    # 日付フォーマットを整形
                    if isinstance(updated_at, str):
                        updated_at = updated_at.split(' ')[0]  # 日付部分のみ
                self.property_table.setItem(i, 7, QTableWidgetItem(updated_at or ""))
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"物件一覧の読み込み中にエラーが発生しました: {str(e)}")
    
    def load_building_registries(self):
        """建物登記簿一覧をテーブルに読み込み"""
        if not self.current_property_id:
            return
        
        try:
            registries = BuildingRegistry.get_by_property(self.current_property_id)
            
            self.building_table.setRowCount(len(registries))
            for i, registry in enumerate(registries):
                self.building_table.setItem(i, 0, QTableWidgetItem(str(registry['id'])))
                self.building_table.setItem(i, 1, QTableWidgetItem(registry['registry_owner'] or ""))
                self.building_table.setItem(i, 2, QTableWidgetItem(registry['building_structure'] or ""))
                self.building_table.setItem(i, 3, QTableWidgetItem(str(registry['building_floors']) if registry['building_floors'] else ""))
                self.building_table.setItem(i, 4, QTableWidgetItem(str(registry['building_area']) if registry['building_area'] else ""))
                self.building_table.setItem(i, 5, QTableWidgetItem(registry['building_date'] or ""))
                self.building_table.setItem(i, 6, QTableWidgetItem(registry['registry_date'] or ""))
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"建物登記簿一覧の読み込み中にエラーが発生しました: {str(e)}")
    
    def load_land_registries(self):
        """土地登記簿一覧をテーブルに読み込み"""
        if not self.current_property_id:
            return
        
        try:
            registries = LandRegistry.get_by_property(self.current_property_id)
            
            self.land_table.setRowCount(len(registries))
            for i, registry in enumerate(registries):
                self.land_table.setItem(i, 0, QTableWidgetItem(str(registry['id'])))
                self.land_table.setItem(i, 1, QTableWidgetItem(registry['land_number'] or ""))
                self.land_table.setItem(i, 2, QTableWidgetItem(registry['land_owner'] or ""))
                self.land_table.setItem(i, 3, QTableWidgetItem(registry['land_address'] or ""))
                self.land_table.setItem(i, 4, QTableWidgetItem(str(registry['land_area']) if registry['land_area'] else ""))
                self.land_table.setItem(i, 5, QTableWidgetItem(registry['land_use'] or ""))
                self.land_table.setItem(i, 6, QTableWidgetItem(registry['registry_date'] or ""))
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"土地登記簿一覧の読み込み中にエラーが発生しました: {str(e)}")
    
    def load_owner_customers(self):
        """オーナー顧客一覧を読み込み"""
        try:
            self.owner_customers = Customer.get_all()
            self.owner_combo.clear()
            self.owner_combo.addItem("新規オーナーを登録", None)
            for customer in self.owner_customers:
                self.owner_combo.addItem(f"{customer['name']} ({customer['id']})", customer['id'])
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"オーナー顧客一覧の読み込み中にエラーが発生しました: {str(e)}")
    
    def load_owner_combo(self):
        """オーナーコンボボックスを読み込み"""
        if hasattr(self, 'owner_combo'):
            self.owner_combo.clear()
            self.owner_combo.addItem("新規オーナーを登録", None)
            
            if hasattr(self, 'owner_customers') and self.owner_customers:
                for customer in self.owner_customers:
                    self.owner_combo.addItem(f"{customer['name']} ({customer['id']})", customer['id'])
    
    def show_property_detail(self, row: int, column: int):
        """物件詳細を表示"""
        try:
            property_id = int(self.property_table.item(row, 0).text())
            property_obj = Property.get_by_id(property_id)
            
            if not property_obj:
                QMessageBox.warning(self, "警告", "物件が見つかりません。")
                return
            
            # 現在の物件IDを設定
            self.current_property_id = property_id
            
            # 基本情報タブに情報を設定
            self.property_name_edit.setText(property_obj['name'])
            self.address_edit.setPlainText(property_obj['address'] or "")
            self.structure_edit.setText(property_obj['structure'] or "")
            self.registry_owner_edit.setText(property_obj['registry_owner'] or "")
            self.notes_edit.setPlainText(property_obj['notes'] or "")
            
            # 管理形態を設定
            management_type = property_obj.get('management_type', '自社管理')
            index = self.management_type_combo.findText(management_type)
            if index >= 0:
                self.management_type_combo.setCurrentIndex(index)
            
            self.management_company_edit.setText(property_obj.get('management_company', ''))
            self.available_rooms_spin.setValue(property_obj.get('available_rooms', 0))
            self.renewal_rooms_spin.setValue(property_obj.get('renewal_rooms', 0))
            
            # オーナー情報を読み込み
            self.load_property_owners()
            
            # 建物・土地登記簿を読み込み
            self.load_building_registries()
            self.load_land_registries()
            
            # 階層情報を読み込み
            self.load_floors()
            self.load_occupancies()
            self.load_recruitments()
            
            # 基本情報タブに切り替え
            self.tab_widget.setCurrentIndex(1)
            
            QMessageBox.information(self, "詳細表示", f"物件「{property_obj['name']}」の詳細を表示しました。")
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"物件詳細の表示に失敗しました: {str(e)}")
    
    def update_property(self):
        """物件情報を更新"""
        if not self.current_property_id:
            QMessageBox.warning(self, "警告", "更新する物件が選択されていません。")
            return
        
        try:
            Property.update(
                id=self.current_property_id,
                name=self.property_name_edit.text().strip(),
                address=self.address_edit.toPlainText().strip(),
                structure=self.structure_edit.text().strip() or None,
                registry_owner=self.registry_owner_edit.text().strip() or None,
                management_type=self.management_type_combo.currentText(),
                management_company=self.management_company_edit.text().strip() or None,
                available_rooms=self.available_rooms_spin.value(),
                renewal_rooms=self.renewal_rooms_spin.value(),
                notes=self.notes_edit.toPlainText().strip() or None
            )
            
            QMessageBox.information(self, "成功", "物件情報を更新しました。")
            self.load_properties()  # 物件一覧を更新
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"物件情報の更新に失敗しました: {str(e)}")
    
    def delete_property(self):
        """物件を削除"""
        if not self.current_property_id:
            QMessageBox.warning(self, "警告", "削除する物件が選択されていません。")
            return
        
        reply = QMessageBox.question(
            self, "確認", 
            "この物件を削除しますか？\n関連する登記簿情報も削除されます。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                Property.delete(self.current_property_id)
                QMessageBox.information(self, "成功", "物件を削除しました。")
                self.current_property_id = None
                self.clear_basic_form()
                self.load_properties()
                
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"物件の削除に失敗しました: {str(e)}")
    
    def load_property_combo(self):
        """物件コンボボックスを読み込み"""
        self.property_combo.clear()
        self.property_combo.addItem("新規物件を作成", None)
        
        try:
            properties = Property.get_all()
            for property_obj in properties:
                self.property_combo.addItem(f"{property_obj['name']} ({property_obj['id']})", property_obj['id'])
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"物件一覧の読み込み中にエラーが発生しました: {str(e)}")
    
    def load_tenant_combo(self):
        """テナントコンボボックスを読み込み"""
        if hasattr(self, 'tenant_combo'):
            self.tenant_combo.clear()
            self.tenant_combo.addItem("テナントを選択", None)
            
            # オーナーが選択されている場合のみテナントを読み込む
            owner_id = self.owner_combo.currentData()
            if owner_id:
                try:
                    tenants = Customer.get_by_owner(owner_id)
                    for tenant in tenants:
                        self.tenant_combo.addItem(f"{tenant['name']} ({tenant['id']})", tenant['id'])
                except Exception as e:
                    QMessageBox.critical(self, "エラー", f"テナント一覧の読み込み中にエラーが発生しました: {str(e)}")
    
    def load_room_combo(self):
        """部屋番号コンボボックスを読み込み"""
        if hasattr(self, 'room_combo') and self.room_combo is not None:
            self.room_combo.clear()
            self.room_combo.addItem("部屋番号を選択", None)
            
            # オーナーとテナントが選択されている場合のみ部屋番号を読み込む
            owner_id = self.owner_combo.currentData() if hasattr(self, 'owner_combo') else None
            tenant_id = self.tenant_combo.currentData() if hasattr(self, 'tenant_combo') else None
            
            if owner_id and tenant_id:
                # 実際の実装では、データベースから部屋番号を取得
                # ここでは仮のデータを使用
                rooms = ["101", "102", "201", "202", "301", "302"]
                for room in rooms:
                    self.room_combo.addItem(room, room) 

    def show_floor_detail(self, row: int, column: int):
        """階層詳細を表示"""
        try:
            # 選択された階層のデータを取得
            floor_id = int(self.floor_table.item(row, 0).text()) # 階層ID
            floor_obj = self.get_floor_by_id(floor_id)

            if not floor_obj:
                QMessageBox.warning(self, "警告", "階層が見つかりません。")
                return

            # 階層詳細フォームに情報を設定
            self.floor_number_edit.setText(floor_obj['floor_number'])
            self.floor_name_edit.setText(floor_obj['floor_name'])
            self.floor_total_area_spin.setValue(floor_obj['total_area'])
            self.floor_registry_area_spin.setValue(floor_obj['registry_area'])
            self.floor_usage_combo.setCurrentText(floor_obj['usage'])
            self.floor_available_area_spin.setValue(floor_obj['available_area'])
            self.floor_occupied_area_spin.setValue(floor_obj['occupied_area'])
            self.floor_notes_edit.setPlainText(floor_obj['notes'])

            # 入居状況タブに切り替え
            self.tab_widget.setCurrentIndex(3)
            self.tab_widget.setCurrentIndex(3) # 入居状況タブに切り替え

            QMessageBox.information(self, "詳細表示", f"階層「{floor_obj['floor_name']}」の詳細を表示しました。")

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"階層詳細の表示に失敗しました: {str(e)}")

    def get_floor_by_id(self, floor_id: int):
        """階層IDから階層オブジェクトを取得"""
        # ここでは仮のデータベースアクセスを想定
        # 実際にはデータベースから取得する
        floors = [
            {'id': 1, 'property_id': 1, 'floor_number': '1F', 'floor_name': '1階', 'total_area': 1000, 'registry_area': 1000, 'usage': 'オフィス', 'available_area': 500, 'occupied_area': 500, 'notes': '備考1'},
            {'id': 2, 'property_id': 1, 'floor_number': '2F', 'floor_name': '2階', 'total_area': 1500, 'registry_area': 1500, 'usage': '住宅', 'available_area': 1000, 'occupied_area': 500, 'notes': '備考2'},
            {'id': 3, 'property_id': 1, 'floor_number': '3F', 'floor_name': '3階', 'total_area': 2000, 'registry_area': 2000, 'usage': '店舗', 'available_area': 1500, 'occupied_area': 500, 'notes': '備考3'},
        ]
        for floor in floors:
            if floor['id'] == floor_id:
                return floor
        return None

    def add_floor(self):
        """階層を追加"""
        if not self.current_property_id:
            QMessageBox.warning(self, "警告", "物件を選択してください。")
            return

        try:
            # 階層番号と名前を取得
            floor_number = self.floor_number_edit.text().strip()
            floor_name = self.floor_name_edit.text().strip()

            if not floor_number or not floor_name:
                QMessageBox.warning(self, "警告", "階層番号と名前を入力してください。")
                return

            # 新しい階層を作成
            new_floor = {
                'property_id': self.current_property_id,
                'floor_number': floor_number,
                'floor_name': floor_name,
                'total_area': self.floor_total_area_spin.value(),
                'registry_area': self.floor_registry_area_spin.value(),
                'usage': self.floor_usage_combo.currentText(),
                'available_area': self.floor_available_area_spin.value(),
                'occupied_area': self.floor_occupied_area_spin.value(),
                'notes': self.floor_notes_edit.toPlainText().strip()
            }

            # データベースに保存
            # ここでは仮のデータベースアクセスを想定
            # 実際にはデータベースに保存
            print(f"Adding floor: {new_floor}")
            # 例: self.db.add_floor(new_floor)

            # テーブルを更新
            self.load_floors()
            self.load_property_combo() # 物件一覧も更新
            QMessageBox.information(self, "成功", "階層を追加しました。")

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"階層の追加に失敗しました: {str(e)}")

    def update_floor(self):
        """階層を更新"""
        if not self.current_property_id:
            QMessageBox.warning(self, "警告", "物件を選択してください。")
            return

        try:
            # 選択された階層のデータを取得
            floor_id = int(self.floor_table.item(self.floor_table.currentRow(), 0).text())
            floor_obj = self.get_floor_by_id(floor_id)

            if not floor_obj:
                QMessageBox.warning(self, "警告", "階層が見つかりません。")
                return

            # 階層番号と名前を取得
            floor_number = self.floor_number_edit.text().strip()
            floor_name = self.floor_name_edit.text().strip()

            if not floor_number or not floor_name:
                QMessageBox.warning(self, "警告", "階層番号と名前を入力してください。")
                return

            # 更新するデータを作成
            update_data = {
                'id': floor_id,
                'property_id': self.current_property_id,
                'floor_number': floor_number,
                'floor_name': floor_name,
                'total_area': self.floor_total_area_spin.value(),
                'registry_area': self.floor_registry_area_spin.value(),
                'usage': self.floor_usage_combo.currentText(),
                'available_area': self.floor_available_area_spin.value(),
                'occupied_area': self.floor_occupied_area_spin.value(),
                'notes': self.floor_notes_edit.toPlainText().strip()
            }

            # データベースに保存
            # ここでは仮のデータベースアクセスを想定
            # 実際にはデータベースに保存
            print(f"Updating floor: {update_data}")
            # 例: self.db.update_floor(update_data)

            # テーブルを更新
            self.load_floors()
            self.load_property_combo() # 物件一覧も更新
            QMessageBox.information(self, "成功", "階層を更新しました。")

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"階層の更新に失敗しました: {str(e)}")

    def delete_floor(self):
        """階層を削除"""
        if not self.current_property_id:
            QMessageBox.warning(self, "警告", "物件を選択してください。")
            return

        try:
            # 選択された階層のデータを取得
            floor_id = int(self.floor_table.item(self.floor_table.currentRow(), 0).text())
            floor_obj = self.get_floor_by_id(floor_id)

            if not floor_obj:
                QMessageBox.warning(self, "警告", "階層が見つかりません。")
                return

            reply = QMessageBox.question(
                self, "確認", 
                f"この階層「{floor_obj['floor_name']}」を削除しますか？\n関連する入居状況や募集状況も削除されます。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # データベースから削除
                # ここでは仮のデータベースアクセスを想定
                # 実際にはデータベースから削除
                print(f"Deleting floor: {floor_id}")
                # 例: self.db.delete_floor(floor_id)

                # テーブルを更新
                self.load_floors()
                self.load_property_combo() # 物件一覧も更新
                QMessageBox.information(self, "成功", "階層を削除しました。")

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"階層の削除に失敗しました: {str(e)}")

    def load_floors(self):
        """階層一覧をテーブルに読み込み"""
        if not self.current_property_id:
            return

        try:
            # ここでは仮のデータベースアクセスを想定
            # 実際にはデータベースから取得
            floors = [
                {'id': 1, 'property_id': self.current_property_id, 'floor_number': '1F', 'floor_name': '1階', 'total_area': 1000, 'registry_area': 1000, 'usage': 'オフィス', 'available_area': 500, 'occupied_area': 500, 'notes': '備考1'},
                {'id': 2, 'property_id': self.current_property_id, 'floor_number': '2F', 'floor_name': '2階', 'total_area': 1500, 'registry_area': 1500, 'usage': '住宅', 'available_area': 1000, 'occupied_area': 500, 'notes': '備考2'},
                {'id': 3, 'property_id': self.current_property_id, 'floor_number': '3F', 'floor_name': '3階', 'total_area': 2000, 'registry_area': 2000, 'usage': '店舗', 'available_area': 1500, 'occupied_area': 500, 'notes': '備考3'},
            ]

            self.floor_table.setRowCount(len(floors))
            for i, floor in enumerate(floors):
                self.floor_table.setItem(i, 0, QTableWidgetItem(str(floor['id'])))
                self.floor_table.setItem(i, 1, QTableWidgetItem(floor['floor_number']))
                self.floor_table.setItem(i, 2, QTableWidgetItem(floor['floor_name']))
                self.floor_table.setItem(i, 3, QTableWidgetItem(str(floor['total_area'])))
                self.floor_table.setItem(i, 4, QTableWidgetItem(str(floor['registry_area'])))
                self.floor_table.setItem(i, 5, QTableWidgetItem(floor['usage']))
                self.floor_table.setItem(i, 6, QTableWidgetItem(str(floor['available_area'])))
                self.floor_table.setItem(i, 7, QTableWidgetItem(str(floor['occupied_area'])))
                self.floor_table.setItem(i, 8, QTableWidgetItem(floor['notes'])) # 備考を追加

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"階層一覧の読み込み中にエラーが発生しました: {str(e)}")

    def clear_floor_form(self):
        """階層詳細フォームをクリア"""
        self.floor_number_edit.clear()
        self.floor_name_edit.clear()
        self.floor_total_area_spin.setValue(0)
        self.floor_registry_area_spin.setValue(0)
        self.floor_usage_combo.setCurrentIndex(0)
        self.floor_available_area_spin.setValue(0)
        self.floor_occupied_area_spin.setValue(0)
        self.floor_notes_edit.clear()

    def create_occupancy_tab(self):
        """入居状況タブを作成"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 入居状況一覧
        self.occupancy_table = QTableWidget()
        self.occupancy_table.setColumnCount(8)
        self.occupancy_table.setHorizontalHeaderLabels([
            "部屋番号", "テナント名", "入居面積(㎡)", "契約開始日", "契約終了日", "賃料", "管理費", "状況"
        ])
        self.occupancy_table.setMaximumHeight(150)
        
        # 入居状況フォーム
        occupancy_form_group = QGroupBox("入居状況登録")
        occupancy_form_layout = QFormLayout()
        
        self.occupancy_unit_combo = QComboBox()
        self.occupancy_unit_combo.addItem("部屋を選択", None)
        
        self.occupancy_tenant_combo = QComboBox()
        self.occupancy_tenant_combo.addItem("テナントを選択", None)
        
        self.occupancy_area_spin = QSpinBox()
        self.occupancy_area_spin.setRange(0, 99999)
        self.occupancy_area_spin.setSuffix(" ㎡")
        
        self.occupancy_start_date_edit = QLineEdit()
        self.occupancy_start_date_edit.setPlaceholderText("例: 2024-01-01")
        
        self.occupancy_end_date_edit = QLineEdit()
        self.occupancy_end_date_edit.setPlaceholderText("例: 2026-12-31")
        
        self.occupancy_rent_spin = QSpinBox()
        self.occupancy_rent_spin.setRange(0, 9999999)
        self.occupancy_rent_spin.setSuffix(" 円")
        
        self.occupancy_maintenance_spin = QSpinBox()
        self.occupancy_maintenance_spin.setRange(0, 999999)
        self.occupancy_maintenance_spin.setSuffix(" 円")
        
        self.occupancy_status_combo = QComboBox()
        self.occupancy_status_combo.addItems(["入居中", "空室", "予約済み"])
        
        occupancy_form_layout.addRow("部屋:", self.occupancy_unit_combo)
        occupancy_form_layout.addRow("テナント:", self.occupancy_tenant_combo)
        occupancy_form_layout.addRow("入居面積(㎡):", self.occupancy_area_spin)
        occupancy_form_layout.addRow("契約開始日:", self.occupancy_start_date_edit)
        occupancy_form_layout.addRow("契約終了日:", self.occupancy_end_date_edit)
        occupancy_form_layout.addRow("賃料:", self.occupancy_rent_spin)
        occupancy_form_layout.addRow("管理費:", self.occupancy_maintenance_spin)
        occupancy_form_layout.addRow("状況:", self.occupancy_status_combo)
        
        occupancy_form_group.setLayout(occupancy_form_layout)
        
        # ボタン
        occupancy_button_layout = QHBoxLayout()
        self.add_occupancy_button = QPushButton("入居状況を登録")
        self.add_occupancy_button.clicked.connect(self.add_occupancy)
        self.clear_occupancy_button = QPushButton("クリア")
        self.clear_occupancy_button.clicked.connect(self.clear_occupancy_form)
        
        occupancy_button_layout.addWidget(self.add_occupancy_button)
        occupancy_button_layout.addWidget(self.clear_occupancy_button)
        occupancy_button_layout.addStretch()
        
        layout.addWidget(self.occupancy_table)
        layout.addWidget(occupancy_form_group)
        layout.addLayout(occupancy_button_layout)
        
        widget.setLayout(layout)
        return widget
    
    def create_recruitment_tab(self):
        """募集状況タブを作成"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 募集状況一覧
        self.recruitment_table = QTableWidget()
        self.recruitment_table.setColumnCount(8)
        self.recruitment_table.setHorizontalHeaderLabels([
            "部屋番号", "募集種別", "募集面積(㎡)", "想定賃料", "想定管理費", "募集開始日", "募集終了日", "状況"
        ])
        self.recruitment_table.setMaximumHeight(150)
        
        # 募集状況フォーム
        recruitment_form_group = QGroupBox("募集状況登録")
        recruitment_form_layout = QFormLayout()
        
        self.recruitment_unit_combo = QComboBox()
        self.recruitment_unit_combo.addItem("部屋を選択", None)
        
        self.recruitment_type_combo = QComboBox()
        self.recruitment_type_combo.addItems(["新規募集", "更新募集", "転貸募集"])
        
        self.recruitment_area_spin = QSpinBox()
        self.recruitment_area_spin.setRange(0, 99999)
        self.recruitment_area_spin.setSuffix(" ㎡")
        
        self.recruitment_rent_spin = QSpinBox()
        self.recruitment_rent_spin.setRange(0, 9999999)
        self.recruitment_rent_spin.setSuffix(" 円")
        
        self.recruitment_maintenance_spin = QSpinBox()
        self.recruitment_maintenance_spin.setRange(0, 999999)
        self.recruitment_maintenance_spin.setSuffix(" 円")
        
        self.recruitment_start_date_edit = QLineEdit()
        self.recruitment_start_date_edit.setPlaceholderText("例: 2024-01-01")
        
        self.recruitment_end_date_edit = QLineEdit()
        self.recruitment_end_date_edit.setPlaceholderText("例: 2024-12-31")
        
        self.recruitment_status_combo = QComboBox()
        self.recruitment_status_combo.addItems(["募集中", "一時停止", "終了"])
        
        self.recruitment_contact_edit = QLineEdit()
        self.recruitment_contact_edit.setPlaceholderText("担当者名")
        
        recruitment_form_layout.addRow("部屋:", self.recruitment_unit_combo)
        recruitment_form_layout.addRow("募集種別:", self.recruitment_type_combo)
        recruitment_form_layout.addRow("募集面積(㎡):", self.recruitment_area_spin)
        recruitment_form_layout.addRow("想定賃料:", self.recruitment_rent_spin)
        recruitment_form_layout.addRow("想定管理費:", self.recruitment_maintenance_spin)
        recruitment_form_layout.addRow("募集開始日:", self.recruitment_start_date_edit)
        recruitment_form_layout.addRow("募集終了日:", self.recruitment_end_date_edit)
        recruitment_form_layout.addRow("状況:", self.recruitment_status_combo)
        recruitment_form_layout.addRow("担当者:", self.recruitment_contact_edit)
        
        recruitment_form_group.setLayout(recruitment_form_layout)
        
        # ボタン
        recruitment_button_layout = QHBoxLayout()
        self.add_recruitment_button = QPushButton("募集状況を登録")
        self.add_recruitment_button.clicked.connect(self.add_recruitment)
        self.clear_recruitment_button = QPushButton("クリア")
        self.clear_recruitment_button.clicked.connect(self.clear_recruitment_form)
        
        recruitment_button_layout.addWidget(self.add_recruitment_button)
        recruitment_button_layout.addWidget(self.clear_recruitment_button)
        recruitment_button_layout.addStretch()
        
        layout.addWidget(self.recruitment_table)
        layout.addWidget(recruitment_form_group)
        layout.addLayout(recruitment_button_layout)
        
        widget.setLayout(layout)
        return widget

    def add_occupancy(self):
        """入居状況を登録"""
        if not self.current_property_id:
            QMessageBox.warning(self, "警告", "物件を選択してください。")
            return

        try:
            # 部屋番号を取得
            room_number = self.occupancy_unit_combo.currentText()
            if room_number == "部屋を選択":
                QMessageBox.warning(self, "警告", "部屋を選択してください。")
                return

            # テナントを取得
            tenant_id = self.occupancy_tenant_combo.currentData()
            if tenant_id is None:
                QMessageBox.warning(self, "警告", "テナントを選択してください。")
                return

            # 入居面積を取得
            occupancy_area = self.occupancy_area_spin.value()
            if occupancy_area <= 0:
                QMessageBox.warning(self, "警告", "入居面積を入力してください。")
                return

            # 契約開始日を取得
            start_date = self.occupancy_start_date_edit.text().strip()
            if not start_date:
                QMessageBox.warning(self, "警告", "契約開始日を入力してください。")
                return

            # 契約終了日を取得
            end_date = self.occupancy_end_date_edit.text().strip()
            if not end_date:
                QMessageBox.warning(self, "警告", "契約終了日を入力してください。")
                return

            # 賃料を取得
            rent = self.occupancy_rent_spin.value()
            if rent <= 0:
                QMessageBox.warning(self, "警告", "賃料を入力してください。")
                return

            # 管理費を取得
            maintenance = self.occupancy_maintenance_spin.value()
            if maintenance <= 0:
                QMessageBox.warning(self, "警告", "管理費を入力してください。")
                return

            # 状況を取得
            status = self.occupancy_status_combo.currentText()

            # 新しい入居状況を作成
            new_occupancy = {
                'property_id': self.current_property_id,
                'room_number': room_number,
                'tenant_id': tenant_id,
                'occupancy_area': occupancy_area,
                'start_date': start_date,
                'end_date': end_date,
                'rent': rent,
                'maintenance': maintenance,
                'status': status
            }

            # データベースに保存
            # ここでは仮のデータベースアクセスを想定
            # 実際にはデータベースに保存
            print(f"Adding occupancy: {new_occupancy}")
            # 例: self.db.add_occupancy(new_occupancy)

            # テーブルを更新
            self.load_occupancies()
            self.load_property_combo() # 物件一覧も更新
            QMessageBox.information(self, "成功", "入居状況を登録しました。")

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"入居状況の登録に失敗しました: {str(e)}")

    def load_occupancies(self):
        """入居状況一覧をテーブルに読み込み"""
        if not self.current_property_id:
            return

        try:
            # ここでは仮のデータベースアクセスを想定
            # 実際にはデータベースから取得
            occupancies = [
                {'id': 1, 'property_id': self.current_property_id, 'room_number': '101', 'tenant_id': 1, 'occupancy_area': 50, 'start_date': '2023-01-01', 'end_date': '2023-12-31', 'rent': 50000, 'maintenance': 10000, 'status': '入居中'},
                {'id': 2, 'property_id': self.current_property_id, 'room_number': '102', 'tenant_id': 2, 'occupancy_area': 30, 'start_date': '2023-02-01', 'end_date': '2023-11-30', 'rent': 30000, 'maintenance': 5000, 'status': '空室'},
                {'id': 3, 'property_id': self.current_property_id, 'room_number': '201', 'tenant_id': 1, 'occupancy_area': 70, 'start_date': '2023-03-01', 'end_date': '2023-10-31', 'rent': 70000, 'maintenance': 15000, 'status': '予約済み'},
            ]

            self.occupancy_table.setRowCount(len(occupancies))
            for i, occupancy in enumerate(occupancies):
                self.occupancy_table.setItem(i, 0, QTableWidgetItem(occupancy['room_number']))
                self.occupancy_table.setItem(i, 1, QTableWidgetItem(occupancy['status']))
                self.occupancy_table.setItem(i, 2, QTableWidgetItem(str(occupancy['occupancy_area'])))
                self.occupancy_table.setItem(i, 3, QTableWidgetItem(occupancy['start_date']))
                self.occupancy_table.setItem(i, 4, QTableWidgetItem(occupancy['end_date']))
                self.occupancy_table.setItem(i, 5, QTableWidgetItem(str(occupancy['rent'])))
                self.occupancy_table.setItem(i, 6, QTableWidgetItem(str(occupancy['maintenance'])))
                self.occupancy_table.setItem(i, 7, QTableWidgetItem(occupancy['status']))

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"入居状況一覧の読み込み中にエラーが発生しました: {str(e)}")

    def clear_occupancy_form(self):
        """入居状況フォームをクリア"""
        self.occupancy_unit_combo.setCurrentIndex(0)
        self.occupancy_tenant_combo.setCurrentIndex(0)
        self.occupancy_area_spin.setValue(0)
        self.occupancy_start_date_edit.clear()
        self.occupancy_end_date_edit.clear()
        self.occupancy_rent_spin.setValue(0)
        self.occupancy_maintenance_spin.setValue(0)
        self.occupancy_status_combo.setCurrentIndex(0)

    def add_recruitment(self):
        """募集状況を登録"""
        if not self.current_property_id:
            QMessageBox.warning(self, "警告", "物件を選択してください。")
            return

        try:
            # 部屋番号を取得
            room_number = self.recruitment_unit_combo.currentText()
            if room_number == "部屋を選択":
                QMessageBox.warning(self, "警告", "部屋を選択してください。")
                return

            # 募集種別を取得
            recruitment_type = self.recruitment_type_combo.currentText()

            # 募集面積を取得
            recruitment_area = self.recruitment_area_spin.value()
            if recruitment_area <= 0:
                QMessageBox.warning(self, "警告", "募集面積を入力してください。")
                return

            # 想定賃料を取得
            rent = self.recruitment_rent_spin.value()
            if rent <= 0:
                QMessageBox.warning(self, "警告", "想定賃料を入力してください。")
                return

            # 想定管理費を取得
            maintenance = self.recruitment_maintenance_spin.value()
            if maintenance <= 0:
                QMessageBox.warning(self, "警告", "想定管理費を入力してください。")
                return

            # 募集開始日を取得
            start_date = self.recruitment_start_date_edit.text().strip()
            if not start_date:
                QMessageBox.warning(self, "警告", "募集開始日を入力してください。")
                return

            # 募集終了日を取得
            end_date = self.recruitment_end_date_edit.text().strip()
            if not end_date:
                QMessageBox.warning(self, "警告", "募集終了日を入力してください。")
                return

            # 状況を取得
            status = self.recruitment_status_combo.currentText()

            # 担当者を取得
            contact = self.recruitment_contact_edit.text().strip()

            # 新しい募集状況を作成
            new_recruitment = {
                'property_id': self.current_property_id,
                'room_number': room_number,
                'recruitment_type': recruitment_type,
                'recruitment_area': recruitment_area,
                'expected_rent': rent,
                'expected_maintenance': maintenance,
                'start_date': start_date,
                'end_date': end_date,
                'status': status,
                'contact': contact
            }

            # データベースに保存
            # ここでは仮のデータベースアクセスを想定
            # 実際にはデータベースに保存
            print(f"Adding recruitment: {new_recruitment}")
            # 例: self.db.add_recruitment(new_recruitment)

            # テーブルを更新
            self.load_recruitments()
            self.load_property_combo() # 物件一覧も更新
            QMessageBox.information(self, "成功", "募集状況を登録しました。")

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"募集状況の登録に失敗しました: {str(e)}")

    def load_recruitments(self):
        """募集状況一覧をテーブルに読み込み"""
        if not self.current_property_id:
            return

        try:
            # ここでは仮のデータベースアクセスを想定
            # 実際にはデータベースから取得
            recruitments = [
                {'id': 1, 'property_id': self.current_property_id, 'room_number': '101', 'recruitment_type': '新規募集', 'recruitment_area': 50, 'expected_rent': 50000, 'expected_maintenance': 10000, 'start_date': '2023-01-01', 'end_date': '2023-12-31', 'status': '募集中', 'contact': '山田太郎'},
                {'id': 2, 'property_id': self.current_property_id, 'room_number': '102', 'recruitment_type': '更新募集', 'recruitment_area': 30, 'expected_rent': 30000, 'expected_maintenance': 5000, 'start_date': '2023-02-01', 'end_date': '2023-11-30', 'status': '一時停止', 'contact': '鈴木花子'},
                {'id': 3, 'property_id': self.current_property_id, 'room_number': '201', 'recruitment_type': '転貸募集', 'recruitment_area': 70, 'expected_rent': 70000, 'expected_maintenance': 15000, 'start_date': '2023-03-01', 'end_date': '2023-10-31', 'status': '終了', 'contact': '田中一郎'},
            ]

            self.recruitment_table.setRowCount(len(recruitments))
            for i, recruitment in enumerate(recruitments):
                self.recruitment_table.setItem(i, 0, QTableWidgetItem(recruitment['room_number']))
                self.recruitment_table.setItem(i, 1, QTableWidgetItem(recruitment['recruitment_type']))
                self.recruitment_table.setItem(i, 2, QTableWidgetItem(str(recruitment['recruitment_area'])))
                self.recruitment_table.setItem(i, 3, QTableWidgetItem(str(recruitment['expected_rent'])))
                self.recruitment_table.setItem(i, 4, QTableWidgetItem(str(recruitment['expected_maintenance'])))
                self.recruitment_table.setItem(i, 5, QTableWidgetItem(recruitment['start_date']))
                self.recruitment_table.setItem(i, 6, QTableWidgetItem(recruitment['end_date']))
                self.recruitment_table.setItem(i, 7, QTableWidgetItem(recruitment['status']))
                self.recruitment_table.setItem(i, 8, QTableWidgetItem(recruitment['contact']))

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"募集状況一覧の読み込み中にエラーが発生しました: {str(e)}")

    def clear_recruitment_form(self):
        """募集状況フォームをクリア"""
        self.recruitment_unit_combo.setCurrentIndex(0)
        self.recruitment_type_combo.setCurrentIndex(0)
        self.recruitment_area_spin.setValue(0)
        self.recruitment_rent_spin.setValue(0)
        self.recruitment_maintenance_spin.setValue(0)
        self.recruitment_start_date_edit.clear()
        self.recruitment_end_date_edit.clear()
        self.recruitment_status_combo.setCurrentIndex(0)
        self.recruitment_contact_edit.clear()

    def browse_file(self, document_type: str):
        """ファイル選択"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"{document_type}謄本PDFファイルを選択", "", 
            "PDFファイル (*.pdf)"
        )
        if file_path:
            if document_type == "building":
                self.building_file_edit.setText(file_path)
            elif document_type == "land":
                self.land_file_edit.setText(file_path)
    
    def process_ocr(self, document_type: str):
        """謄本をアップロードしてOCR処理"""
        property_id = self.owner_combo.currentData()
        file_path = self.building_file_edit.text() if document_type == "building" else self.land_file_edit.text()
        
        if not property_id:
            QMessageBox.warning(self, "警告", "物件を選択してください。")
            return
        
        if not file_path:
            QMessageBox.warning(self, "警告", "ファイルを選択してください。")
            return
        
        try:
            # ファイル名を取得
            file_name = os.path.basename(file_path)
            
            # 謄本文書をデータベースに登録
            document_type_db = "building" if document_type == "building" else "land"
            document_id = RegistryDocument.create(
                property_id=property_id,
                document_type=document_type_db,
                file_path=file_path,
                file_name=file_name
            )
            
            # OCR処理を非同期で実行
            self.worker = RegistryOCRWorker(file_path, document_type)
            self.worker.finished.connect(lambda result: self.on_ocr_finished(document_id, result))
            self.worker.error.connect(self.on_ocr_error)
            self.worker.start()
            
            self.upload_result_text.setText("OCR処理を実行中...")
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"アップロードに失敗しました: {str(e)}")
    
    def on_ocr_finished(self, document_id: int, result: dict):
        """OCR処理完了時の処理"""
        self.upload_result_text.setText("OCR処理完了\n\n")
        
        try:
            # OCR結果をデータベースに保存
            ocr_result = str(result)
            RegistryDocument.update_ocr_result(document_id, ocr_result)
            
            # 結果を表示
            result_text = "OCR処理完了\n\n"
            for key, value in result.items():
                if value:
                    result_text += f"{key}: {value}\n"
            
            self.upload_result_text.setText(result_text)
            
            # 自動入力の確認
            if result:
                reply = QMessageBox.question(
                    self, "確認", 
                    "OCR結果を登記簿情報に自動入力しますか？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.auto_fill_registry_info(result)
            
            # テーブルを更新
            self.load_documents()
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"OCR結果の保存に失敗しました: {str(e)}")
    
    def on_ocr_error(self, error: str):
        """OCR処理エラー時の処理"""
        self.upload_result_text.setText(f"OCR処理エラー: {error}")
        QMessageBox.critical(self, "エラー", f"OCR処理中にエラーが発生しました: {error}")
    
    def auto_fill_registry_info(self, result: dict):
        """OCR結果を登記簿情報に自動入力"""
        try:
            if self.owner_combo.currentText() == "新規オーナーを登録":
                # 新規オーナーを登録
                new_owner_name = QLineEdit().text() # ダイアログで入力
                if new_owner_name:
                    new_customer = Customer.create(name=new_owner_name)
                    self.owner_combo.addItem(f"{new_owner_name} ({new_customer['id']})", new_customer['id'])
                    self.owner_combo.setCurrentIndex(self.owner_combo.count() - 1) # 新しいオーナーを選択
                    property_id = self.owner_combo.currentData() # 新しい物件IDを取得
                else:
                    QMessageBox.warning(self, "警告", "オーナー名を入力してください。")
                    return
            else:
                property_id = self.owner_combo.currentData() # 既存オーナーの物件IDを取得

            if self.owner_combo.currentText() == "新規オーナーを登録":
                # 物件基本情報も自動入力
                if result.get('registry_address'):
                    self.address_edit.setPlainText(result['registry_address'])
                if result.get('building_structure'):
                    # 構造情報を基本情報にも反映
                    structure_text = result['building_structure']
                    if result.get('building_floors'):
                        structure_text += f" {result['building_floors']}階建"
                    self.structure_edit.setText(structure_text)
                if result.get('registry_owner'):
                    self.registry_owner_edit.setText(result['registry_owner'])
                
                # 建物登記簿タブに自動入力
                if result.get('registry_owner'):
                    self.building_owner_edit.setText(result['registry_owner'])
                if result.get('registry_address'):
                    self.building_address_edit.setPlainText(result['registry_address'])
                if result.get('building_structure'):
                    self.building_structure_edit.setText(result['building_structure'])
                if result.get('building_floors'):
                    self.building_floors_spin.setValue(result['building_floors'])
                if result.get('building_area'):
                    self.building_area_spin.setValue(int(result['building_area']))
                if result.get('building_date'):
                    self.building_date_edit.setText(result['building_date'])
                if result.get('registry_date'):
                    self.building_registry_date_edit.setText(result['registry_date'])
                if result.get('mortgage_info'):
                    self.building_mortgage_edit.setPlainText(result['mortgage_info'])
                
                # 建物登記簿タブに切り替え
                self.tab_widget.setCurrentIndex(1)
                
            else:
                # 物件基本情報も自動入力（土地の場合）
                if result.get('land_address'):
                    self.address_edit.setPlainText(result['land_address'])
                if result.get('land_owner'):
                    self.registry_owner_edit.setText(result['land_owner'])
                
                # 土地登記簿タブに自動入力
                if result.get('land_number'):
                    self.land_number_edit.setText(result['land_number'])
                if result.get('land_owner'):
                    self.land_owner_edit.setText(result['land_owner'])
                if result.get('land_address'):
                    self.land_address_edit.setPlainText(result['land_address'])
                if result.get('land_area'):
                    self.land_area_spin.setValue(int(result['land_area']))
                if result.get('land_use'):
                    self.land_use_edit.setText(result['land_use'])
                if result.get('registry_date'):
                    self.land_registry_date_edit.setText(result['registry_date'])
                if result.get('mortgage_info'):
                    self.land_mortgage_edit.setPlainText(result['mortgage_info'])
                
                # 土地登記簿タブに切り替え
                self.tab_widget.setCurrentIndex(2)
            
            QMessageBox.information(self, "完了", "OCR結果を自動入力しました。内容を確認してから登録してください。")
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"自動入力に失敗しました: {str(e)}")
    
    def register_property(self):
        """物件を登録（謄本アップロードタブから）"""
        try:
            # 物件の選択・作成
            selected_property_id = self.property_combo.currentData()
            new_property_name = self.new_property_name_edit.text().strip()
            
            if selected_property_id is None:
                # 新規物件を作成
                if not new_property_name:
                    QMessageBox.warning(self, "警告", "新規物件名を入力してください。")
                    return
                
                # オーナー情報を取得
                owner_id = self.owner_combo.currentData()
                if not owner_id:
                    QMessageBox.warning(self, "警告", "オーナーを選択してください。")
                    return
                
                # 物件を作成
                self.current_property_id = Property.create(
                    name=new_property_name,
                    address="",  # 後でOCR結果から設定
                    structure="",
                    registry_owner="",
                    management_type="自社管理",
                    notes="謄本アップロードで作成"
                )
                
                QMessageBox.information(self, "成功", f"物件「{new_property_name}」を作成しました。")
                
            else:
                # 既存物件を選択
                self.current_property_id = selected_property_id
            
            # 謄本ファイルをデータベースに登録
            self.register_documents()
            
            # 物件一覧を更新
            self.load_properties()
            self.load_property_combo()
            
            # フォームをクリア
            self.new_property_name_edit.clear()
            self.property_combo.setCurrentIndex(0)
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"物件登録に失敗しました: {str(e)}")
    
    def register_documents(self):
        """謄本文書をデータベースに登録"""
        if not self.current_property_id:
            return
        
        try:
            # 建物謄本を登録
            for row in range(self.building_files_list.rowCount()):
                file_path = self.building_files_list.item(row, 0).data(Qt.ItemDataRole.UserRole)
                file_name = self.building_files_list.item(row, 0).text()
                status = self.building_files_list.item(row, 1).text()
                
                if file_path and status == "完了":
                    # 既に登録済みかチェック
                    existing_docs = RegistryDocument.get_by_property_and_type(
                        self.current_property_id, "building"
                    )
                    
                    # ファイル名で重複チェック
                    if not any(doc['file_name'] == file_name for doc in existing_docs):
                        RegistryDocument.create(
                            property_id=self.current_property_id,
                            document_type="building",
                            file_path=file_path,
                            file_name=file_name,
                            is_processed=True
                        )
            
            # 土地謄本を登録
            for row in range(self.land_files_list.rowCount()):
                file_path = self.land_files_list.item(row, 0).data(Qt.ItemDataRole.UserRole)
                file_name = self.land_files_list.item(row, 0).text()
                status = self.land_files_list.item(row, 1).text()
                
                if file_path and status == "完了":
                    # 既に登録済みかチェック
                    existing_docs = RegistryDocument.get_by_property_and_type(
                        self.current_property_id, "land"
                    )
                    
                    # ファイル名で重複チェック
                    if not any(doc['file_name'] == file_name for doc in existing_docs):
                        RegistryDocument.create(
                            property_id=self.current_property_id,
                            document_type="land",
                            file_path=file_path,
                            file_name=file_name,
                            is_processed=True
                        )
            
            QMessageBox.information(self, "成功", "謄本文書を登録しました。")
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"謄本文書の登録に失敗しました: {str(e)}")
    
    def clear_upload_form(self):
        """アップロードフォームをクリア"""
        self.owner_combo.setCurrentIndex(0)
        self.building_file_edit.clear()
        self.land_file_edit.clear()
        self.upload_result_text.clear()
    
    def load_documents(self):
        """謄本文書一覧をテーブルに読み込み"""
        try:
            documents = RegistryDocument.get_by_property(self.current_property_id or 0)
            
            self.document_table.setRowCount(len(documents))
            for i, document in enumerate(documents):
                self.document_table.setItem(i, 0, QTableWidgetItem(str(document['id'])))
                
                # 物件名を取得
                property_obj = Property.get_by_id(document['property_id'])
                property_name = property_obj['name'] if property_obj else ""
                self.document_table.setItem(i, 1, QTableWidgetItem(property_name))
                
                document_type = "建物登記簿" if document['document_type'] == 'building' else "土地登記簿"
                self.document_table.setItem(i, 2, QTableWidgetItem(document_type))
                self.document_table.setItem(i, 3, QTableWidgetItem(document['file_name'] or ""))
                
                status = "処理済み" if document['is_processed'] else "未処理"
                self.document_table.setItem(i, 4, QTableWidgetItem(status))
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"謄本文書一覧の読み込み中にエラーが発生しました: {str(e)}") 

    def add_document_files(self, document_type: str):
        """複数の謄本ファイルを追加"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, f"{document_type}謄本PDFファイルを選択", "", 
            "PDFファイル (*.pdf)"
        )
        
        if not file_paths:
            return
        
        # ファイルリストを取得
        files_list = self.building_files_list if document_type == "building" else self.land_files_list
        
        # 既存の行数を取得
        current_row = files_list.rowCount()
        
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            
            # 新しい行を追加
            files_list.insertRow(current_row)
            
            # ファイル名
            files_list.setItem(current_row, 0, QTableWidgetItem(file_name))
            
            # ステータス
            files_list.setItem(current_row, 1, QTableWidgetItem("未処理"))
            
            # OCR結果（空）
            files_list.setItem(current_row, 2, QTableWidgetItem(""))
            
            # 所有者（空）
            files_list.setItem(current_row, 3, QTableWidgetItem(""))
            
            # 操作ボタン
            process_button = QPushButton("OCR処理")
            process_button.clicked.connect(lambda checked, row=current_row, path=file_path, doc_type=document_type: 
                                        self.process_single_document(row, path, doc_type))
            files_list.setCellWidget(current_row, 4, process_button)
            
            # ファイルパスを保存
            files_list.item(current_row, 0).setData(Qt.ItemDataRole.UserRole, file_path)
            
            current_row += 1
    
    def process_single_document(self, row: int, file_path: str, document_type: str):
        """単一の謄本をOCR処理"""
        try:
            # ステータスを更新
            files_list = self.building_files_list if document_type == "building" else self.land_files_list
            files_list.setItem(row, 1, QTableWidgetItem("処理中..."))
            
            # OCR処理を非同期で実行
            self.worker = RegistryOCRWorker(file_path, document_type)
            self.worker.finished.connect(lambda result, r=row, doc_type=document_type: 
                                      self.on_single_ocr_finished(r, result, doc_type))
            self.worker.error.connect(lambda error, r=row, doc_type=document_type: 
                                   self.on_single_ocr_error(r, error, doc_type))
            self.worker.start()
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"OCR処理の開始に失敗しました: {str(e)}")
    
    def process_all_documents(self, document_type: str):
        """全ての謄本をOCR処理"""
        files_list = self.building_files_list if document_type == "building" else self.land_files_list
        
        for row in range(files_list.rowCount()):
            file_path = files_list.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if file_path and files_list.item(row, 1).text() == "未処理":
                self.process_single_document(row, file_path, document_type)
    
    def on_single_ocr_finished(self, row: int, result: dict, document_type: str):
        """単一OCR処理完了時の処理"""
        files_list = self.building_files_list if document_type == "building" else self.land_files_list
        
        try:
            # ステータスを更新
            files_list.setItem(row, 1, QTableWidgetItem("完了"))
            
            # OCR結果を表示
            result_text = ""
            for key, value in result.items():
                if value:
                    result_text += f"{key}: {value}\n"
            
            files_list.setItem(row, 2, QTableWidgetItem(result_text))
            
            # 所有者情報を自動設定
            if document_type == "building" and result.get('registry_owner'):
                files_list.setItem(row, 3, QTableWidgetItem(result['registry_owner']))
            elif document_type == "land" and result.get('land_owner'):
                files_list.setItem(row, 3, QTableWidgetItem(result['land_owner']))
            
            # OCR結果をメインエリアに表示
            self.ocr_result_text.setText(result_text)
            
            # 自動入力の確認
            if result:
                reply = QMessageBox.question(
                    self, "確認", 
                    "OCR結果を登記簿情報に自動入力しますか？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.auto_fill_from_ocr_result(result, document_type)
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"OCR結果の処理に失敗しました: {str(e)}")
    
    def on_single_ocr_error(self, row: int, error: str, document_type: str = None):
        """単一OCR処理エラー時の処理"""
        files_list = self.building_files_list if document_type == "building" else self.land_files_list
        files_list.setItem(row, 1, QTableWidgetItem("エラー"))
        files_list.setItem(row, 2, QTableWidgetItem(f"エラー: {error}"))
        QMessageBox.critical(self, "エラー", f"OCR処理中にエラーが発生しました: {error}")
    
    def copy_ocr_result(self):
        """OCR結果をクリップボードにコピー"""
        from PyQt6.QtWidgets import QApplication
        text = self.ocr_result_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "完了", "OCR結果をクリップボードにコピーしました。")
        else:
            QMessageBox.warning(self, "警告", "コピーするOCR結果がありません。")
    
    def auto_fill_from_ocr(self):
        """OCR結果から自動入力"""
        text = self.ocr_result_text.toPlainText()
        if not text:
            QMessageBox.warning(self, "警告", "OCR結果がありません。")
            return
        
        # 現在選択されているファイルのOCR結果を解析
        # 簡易的な解析（実際の実装ではより詳細な解析が必要）
        lines = text.split('\n')
        result = {}
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                result[key.strip()] = value.strip()
        
        if result:
            self.auto_fill_from_ocr_result(result, "building")  # デフォルトは建物
    
    def auto_fill_from_ocr_result(self, result: dict, document_type: str):
        """OCR結果から登記簿情報に自動入力"""
        try:
            if document_type == "building":
                # 建物登記簿タブに自動入力
                if result.get('registry_owner'):
                    self.building_owner_edit.setText(result['registry_owner'])
                if result.get('registry_address'):
                    self.building_address_edit.setPlainText(result['registry_address'])
                if result.get('building_structure'):
                    self.building_structure_edit.setText(result['building_structure'])
                if result.get('building_floors'):
                    try:
                        self.building_floors_spin.setValue(int(result['building_floors']))
                    except ValueError:
                        pass
                if result.get('building_area'):
                    try:
                        self.building_area_spin.setValue(int(result['building_area']))
                    except ValueError:
                        pass
                if result.get('building_date'):
                    self.building_date_edit.setText(result['building_date'])
                if result.get('registry_date'):
                    self.building_registry_date_edit.setText(result['registry_date'])
                if result.get('mortgage_info'):
                    self.building_mortgage_edit.setPlainText(result['mortgage_info'])
                
                # 建物登記簿タブに切り替え
                self.tab_widget.setCurrentIndex(1)
                
            else:  # land
                # 土地登記簿タブに自動入力
                if result.get('land_number'):
                    self.land_number_edit.setText(result['land_number'])
                if result.get('land_owner'):
                    self.land_owner_edit.setText(result['land_owner'])
                if result.get('land_address'):
                    self.land_address_edit.setPlainText(result['land_address'])
                if result.get('land_area'):
                    try:
                        self.land_area_spin.setValue(int(result['land_area']))
                    except ValueError:
                        pass
                if result.get('land_use'):
                    self.land_use_edit.setText(result['land_use'])
                if result.get('registry_date'):
                    self.land_registry_date_edit.setText(result['registry_date'])
                if result.get('mortgage_info'):
                    self.land_mortgage_edit.setPlainText(result['mortgage_info'])
                
                # 土地登記簿タブに切り替え
                self.tab_widget.setCurrentIndex(2)
            
            QMessageBox.information(self, "完了", "OCR結果を自動入力しました。内容を確認してから登録してください。")
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"自動入力に失敗しました: {str(e)}")
    
    def clear_ocr_result(self):
        """OCR結果をクリア"""
        self.ocr_result_text.clear()
    
    def on_owner_changed(self):
        """オーナー選択変更時の処理"""
        if hasattr(self, 'load_tenant_combo'):
            self.load_tenant_combo()
        if hasattr(self, 'load_room_combo'):
            self.load_room_combo()
    
    def on_tenant_changed(self):
        """テナント選択変更時の処理"""
        if hasattr(self, 'load_room_combo'):
            self.load_room_combo()
    
    def load_room_combo(self):
        """部屋番号コンボボックスを読み込み"""
        self.room_combo.clear()
        self.room_combo.addItem("部屋番号を選択", None)
        
        # オーナーとテナントが選択されている場合のみ部屋番号を読み込む
        owner_id = self.owner_combo.currentData()
        tenant_id = self.tenant_combo.currentData()
        
        if owner_id and tenant_id:
            # 実際の実装では、データベースから部屋番号を取得
            # ここでは仮のデータを使用
            rooms = ["101", "102", "201", "202", "301", "302"]
            for room in rooms:
                self.room_combo.addItem(room, room) 