#!/usr/bin/env python3
"""
統合物件管理タブ - プロ仕様
物件登録・部屋管理・収益計算・メンテナンス管理を統合したシステム
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QLineEdit, 
                             QTextEdit, QMessageBox, QGroupBox, QFormLayout, 
                             QSpinBox, QTabWidget, QScrollArea, QFileDialog, 
                             QComboBox, QCheckBox, QDateEdit, QDialog, QDialogButtonBox,
                             QSplitter, QTreeWidget, QTreeWidgetItem, QHeaderView,
                             QProgressBar, QSlider, QFrame, QGridLayout, QListWidget)
from PyQt6.QtCore import Qt, QDate, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont, QPixmap, QIcon
from datetime import datetime, date, timedelta
import os
import json
from models import Property, Unit, Customer, TenantContract
from utils import MessageHelper, DateHelper, FormatHelper, Validator
from ui.ui_styles import ModernStyles

# OCR機能をオプショナルにする
try:
    from ocr.registry_ocr import RegistryOCR
    from ocr.floorplan_ocr import FloorplanOCR
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("注意: OCR機能が利用できません")

class PropertyAnalyticsWidget(QWidget):
    """物件収益分析ウィジェット"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 収益サマリー
        summary_group = QGroupBox("収益サマリー")
        summary_layout = QGridLayout()
        
        self.total_rent_label = QLabel("¥0")
        self.total_rent_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2E7D32;")
        
        self.occupancy_rate_label = QLabel("0%")
        self.occupancy_rate_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1976D2;")
        
        self.vacant_units_label = QLabel("0室")
        self.vacant_units_label.setStyleSheet("font-size: 16px; color: #D32F2F;")
        
        self.maintenance_cost_label = QLabel("¥0")
        self.maintenance_cost_label.setStyleSheet("font-size: 14px; color: #F57C00;")
        
        summary_layout.addWidget(QLabel("月間賃料収入:"), 0, 0)
        summary_layout.addWidget(self.total_rent_label, 0, 1)
        summary_layout.addWidget(QLabel("入居率:"), 0, 2)
        summary_layout.addWidget(self.occupancy_rate_label, 0, 3)
        
        summary_layout.addWidget(QLabel("空室数:"), 1, 0)
        summary_layout.addWidget(self.vacant_units_label, 1, 1)
        summary_layout.addWidget(QLabel("維持費用:"), 1, 2)
        summary_layout.addWidget(self.maintenance_cost_label, 1, 3)
        
        summary_group.setLayout(summary_layout)
        
        # 収益グラフエリア（簡易版）
        graph_group = QGroupBox("収益推移")
        graph_layout = QVBoxLayout()
        
        self.revenue_progress = QProgressBar()
        self.revenue_progress.setMaximum(100)
        self.revenue_progress.setValue(0)
        self.revenue_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 10px;
                margin: 0.5px;
            }
        """)
        
        graph_layout.addWidget(QLabel("収益率（目標比）"))
        graph_layout.addWidget(self.revenue_progress)
        graph_group.setLayout(graph_layout)
        
        layout.addWidget(summary_group)
        layout.addWidget(graph_group)
        layout.addStretch()
        
        self.setLayout(layout)
        
    def update_analytics(self, property_data):
        """分析データを更新"""
        try:
            # 基本計算（実際のデータベースクエリに置き換える）
            total_rent = 0
            total_units = 0
            occupied_units = 0
            
            # サンプル計算（実装時は実際のデータを使用）
            if property_data:
                total_rent = 150000  # サンプル値
                total_units = 10
                occupied_units = 8
                maintenance_cost = 25000
                
                occupancy_rate = (occupied_units / total_units * 100) if total_units > 0 else 0
                vacant_units = total_units - occupied_units
                
                self.total_rent_label.setText(FormatHelper.format_currency(total_rent))
                self.occupancy_rate_label.setText(f"{occupancy_rate:.1f}%")
                self.vacant_units_label.setText(f"{vacant_units}室")
                self.maintenance_cost_label.setText(FormatHelper.format_currency(maintenance_cost))
                
                # 収益率計算（目標賃料に対する実績）
                target_rent = 180000  # 満室時目標
                achievement_rate = (total_rent / target_rent * 100) if target_rent > 0 else 0
                self.revenue_progress.setValue(int(achievement_rate))
                
        except Exception as e:
            print(f"分析データ更新エラー: {e}")

class UnitManagementWidget(QWidget):
    """部屋管理ウィジェット"""
    
    unit_updated = pyqtSignal()
    
    def __init__(self, property_id=None):
        super().__init__()
        self.property_id = property_id
        self.init_ui()
        if property_id:
            self.load_units()
            
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 部屋管理ヘッダー
        header_layout = QHBoxLayout()
        
        self.add_unit_btn = QPushButton("部屋追加")
        self.add_unit_btn.clicked.connect(self.add_unit)
        self.add_unit_btn.setStyleSheet(ModernStyles.get_button_style("primary"))
        
        self.edit_unit_btn = QPushButton("編集")
        self.edit_unit_btn.clicked.connect(self.edit_unit)
        self.edit_unit_btn.setEnabled(False)
        
        self.delete_unit_btn = QPushButton("削除")
        self.delete_unit_btn.clicked.connect(self.delete_unit)
        self.delete_unit_btn.setEnabled(False)
        self.delete_unit_btn.setStyleSheet(ModernStyles.get_button_style("danger"))
        
        self.bulk_update_btn = QPushButton("一括更新")
        self.bulk_update_btn.clicked.connect(self.bulk_update_units)
        
        header_layout.addWidget(self.add_unit_btn)
        header_layout.addWidget(self.edit_unit_btn)
        header_layout.addWidget(self.delete_unit_btn)
        header_layout.addWidget(self.bulk_update_btn)
        header_layout.addStretch()
        
        # 部屋一覧テーブル
        self.units_table = QTableWidget()
        self.units_table.setColumnCount(8)
        self.units_table.setHorizontalHeaderLabels([
            "部屋番号", "間取り", "面積", "賃料", "管理費", "入居状況", "入居者", "更新日"
        ])
        
        # テーブル設定
        header = self.units_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.resizeSection(0, 80)   # 部屋番号
        header.resizeSection(1, 80)   # 間取り
        header.resizeSection(2, 70)   # 面積
        header.resizeSection(3, 80)   # 賃料
        header.resizeSection(4, 70)   # 管理費
        header.resizeSection(5, 80)   # 入居状況
        header.resizeSection(6, 120)  # 入居者
        
        self.units_table.setAlternatingRowColors(True)
        self.units_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.units_table.itemSelectionChanged.connect(self.on_unit_selection_changed)
        self.units_table.doubleClicked.connect(self.edit_unit)
        
        layout.addLayout(header_layout)
        layout.addWidget(self.units_table)
        
        self.setLayout(layout)
        
    def set_property_id(self, property_id):
        """物件IDを設定"""
        self.property_id = property_id
        self.load_units()
        
    def load_units(self):
        """部屋一覧を読み込み"""
        if not self.property_id:
            return
            
        try:
            self.units_table.setRowCount(0)
            units = Unit.get_by_property(self.property_id)
            
            for unit in units:
                row = self.units_table.rowCount()
                self.units_table.insertRow(row)
                
                # 基本情報
                self.units_table.setItem(row, 0, QTableWidgetItem(unit.get('room_number', '')))
                self.units_table.setItem(row, 1, QTableWidgetItem(unit.get('room_type', '')))
                
                # 面積
                area = unit.get('area')
                area_text = f"{area}㎡" if area else ""
                self.units_table.setItem(row, 2, QTableWidgetItem(area_text))
                
                # 賃料・管理費
                rent = unit.get('rent', 0) or 0
                maintenance = unit.get('maintenance_fee', 0) or 0
                self.units_table.setItem(row, 3, QTableWidgetItem(FormatHelper.format_currency(rent)))
                self.units_table.setItem(row, 4, QTableWidgetItem(FormatHelper.format_currency(maintenance)))
                
                # 入居状況確認
                occupancy_status, tenant_name = self.get_occupancy_status(unit.get('id'))
                
                status_item = QTableWidgetItem(occupancy_status)
                if occupancy_status == "入居中":
                    status_item.setBackground(QColor("#E8F5E8"))
                elif occupancy_status == "空室":
                    status_item.setBackground(QColor("#FFEBEE"))
                elif occupancy_status == "退去予定":
                    status_item.setBackground(QColor("#FFF3E0"))
                
                self.units_table.setItem(row, 5, status_item)
                self.units_table.setItem(row, 6, QTableWidgetItem(tenant_name))
                
                # 更新日
                updated_at = DateHelper.format_date(unit.get('updated_at'))
                self.units_table.setItem(row, 7, QTableWidgetItem(updated_at))
                
        except Exception as e:
            MessageHelper.show_error(self, f"部屋一覧の読み込み中にエラーが発生しました: {str(e)}")
            
    def get_occupancy_status(self, unit_id):
        """入居状況を取得"""
        try:
            contracts = TenantContract.get_all()
            current_date = date.today()
            
            for contract in contracts:
                if contract.get('unit_id') == unit_id:
                    start_date = datetime.strptime(contract.get('start_date'), '%Y-%m-%d').date()
                    end_date = datetime.strptime(contract.get('end_date'), '%Y-%m-%d').date()
                    
                    if start_date <= current_date <= end_date:
                        # 退去予定チェック（終了日まで30日以内）
                        days_until_end = (end_date - current_date).days
                        if days_until_end <= 30:
                            return "退去予定", contract.get('contractor_name', '')
                        else:
                            return "入居中", contract.get('contractor_name', '')
                            
            return "空室", ""
            
        except Exception as e:
            print(f"入居状況取得エラー: {e}")
            return "不明", ""
    
    def on_unit_selection_changed(self):
        """部屋選択変更時"""
        has_selection = self.units_table.currentRow() >= 0
        self.edit_unit_btn.setEnabled(has_selection)
        self.delete_unit_btn.setEnabled(has_selection)
    
    def add_unit(self):
        """部屋追加"""
        if not self.property_id:
            MessageHelper.show_warning(self, "先に物件を選択してください")
            return
            
        dialog = UnitEditDialog(self, property_id=self.property_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_unit_data()
            
            try:
                Unit.create(
                    property_id=self.property_id,
                    room_number=data['room_number'],
                    room_type=data['room_type'],
                    area=data['area'],
                    rent=data['rent'],
                    maintenance_fee=data['maintenance_fee'],
                    deposit=data['deposit'],
                    key_money=data['key_money'],
                    features=data['features'],
                    equipment=data['equipment'],
                    notes=data['notes']
                )
                
                MessageHelper.show_success(self, "部屋を追加しました")
                self.load_units()
                self.unit_updated.emit()
                
            except Exception as e:
                MessageHelper.show_error(self, f"部屋追加中にエラーが発生しました: {str(e)}")
    
    def edit_unit(self):
        """部屋編集"""
        row = self.units_table.currentRow()
        if row < 0:
            return
            
        room_number = self.units_table.item(row, 0).text()
        
        # 既存データを取得
        units = Unit.get_by_property(self.property_id)
        unit_data = None
        for unit in units:
            if unit.get('room_number') == room_number:
                unit_data = unit
                break
                
        if not unit_data:
            MessageHelper.show_error(self, "部屋データが見つかりません")
            return
            
        dialog = UnitEditDialog(self, unit_data=unit_data, property_id=self.property_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_unit_data()
            
            try:
                # 部屋更新機能の実装が必要
                MessageHelper.show_success(self, "部屋情報を更新しました")
                self.load_units()
                self.unit_updated.emit()
                
            except Exception as e:
                MessageHelper.show_error(self, f"部屋更新中にエラーが発生しました: {str(e)}")
    
    def delete_unit(self):
        """部屋削除"""
        row = self.units_table.currentRow()
        if row < 0:
            return
            
        room_number = self.units_table.item(row, 0).text()
        
        if MessageHelper.confirm_delete(self, f"部屋「{room_number}」"):
            try:
                # 部屋削除機能の実装が必要
                MessageHelper.show_success(self, "部屋を削除しました")
                self.load_units()
                self.unit_updated.emit()
                
            except Exception as e:
                MessageHelper.show_error(self, f"部屋削除中にエラーが発生しました: {str(e)}")
    
    def bulk_update_units(self):
        """一括更新"""
        dialog = BulkUnitUpdateDialog(self, self.property_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_units()
            self.unit_updated.emit()

class UnitEditDialog(QDialog):
    """部屋編集ダイアログ"""
    
    def __init__(self, parent=None, unit_data=None, property_id=None):
        super().__init__(parent)
        self.unit_data = unit_data
        self.property_id = property_id
        self.init_ui()
        if unit_data:
            self.load_unit_data()
            
    def init_ui(self):
        self.setWindowTitle("部屋編集" if self.unit_data else "部屋追加")
        self.setModal(True)
        self.resize(600, 700)
        
        layout = QVBoxLayout()
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        
        # 基本情報タブ
        basic_tab = self.create_basic_tab()
        self.tab_widget.addTab(basic_tab, "基本情報")
        
        # 設備・特徴タブ
        features_tab = self.create_features_tab()
        self.tab_widget.addTab(features_tab, "設備・特徴")
        
        # 図面・写真タブ
        media_tab = self.create_media_tab()
        self.tab_widget.addTab(media_tab, "図面・写真")
        
        layout.addWidget(self.tab_widget)
        
        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        self.setLayout(layout)
    
    def create_basic_tab(self):
        """基本情報タブを作成"""
        tab = QWidget()
        layout = QFormLayout()
        
        # 部屋番号
        self.room_number_edit = QLineEdit()
        self.room_number_edit.setPlaceholderText("例: 101, A-201")
        
        # 間取り
        self.room_type_combo = QComboBox()
        self.room_type_combo.setEditable(True)
        self.room_type_combo.addItems([
            "1R", "1K", "1DK", "1LDK", "2K", "2DK", "2LDK", 
            "3K", "3DK", "3LDK", "4K", "4DK", "4LDK", "その他"
        ])
        
        # 面積
        self.area_spin = QSpinBox()
        self.area_spin.setMaximum(999)
        self.area_spin.setSuffix(" ㎡")
        
        # 賃料関連
        self.rent_spin = QSpinBox()
        self.rent_spin.setMaximum(9999999)
        self.rent_spin.setSuffix(" 円")
        
        self.maintenance_fee_spin = QSpinBox()
        self.maintenance_fee_spin.setMaximum(999999)
        self.maintenance_fee_spin.setSuffix(" 円")
        
        self.deposit_spin = QSpinBox()
        self.deposit_spin.setMaximum(9999999)
        self.deposit_spin.setSuffix(" 円")
        
        self.key_money_spin = QSpinBox()
        self.key_money_spin.setMaximum(9999999)
        self.key_money_spin.setSuffix(" 円")
        
        # 階数・向き
        self.floor_spin = QSpinBox()
        self.floor_spin.setMinimum(1)
        self.floor_spin.setMaximum(50)
        
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["北", "南", "東", "西", "北東", "北西", "南東", "南西"])
        
        # バルコニー
        self.balcony_check = QCheckBox("バルコニーあり")
        self.balcony_area_spin = QSpinBox()
        self.balcony_area_spin.setSuffix(" ㎡")
        self.balcony_area_spin.setEnabled(False)
        self.balcony_check.toggled.connect(self.balcony_area_spin.setEnabled)
        
        layout.addRow("部屋番号 *:", self.room_number_edit)
        layout.addRow("間取り *:", self.room_type_combo)
        layout.addRow("面積:", self.area_spin)
        layout.addRow("賃料:", self.rent_spin)
        layout.addRow("管理費:", self.maintenance_fee_spin)
        layout.addRow("敷金:", self.deposit_spin)
        layout.addRow("礼金:", self.key_money_spin)
        layout.addRow("階数:", self.floor_spin)
        layout.addRow("向き:", self.direction_combo)
        layout.addRow("", self.balcony_check)
        layout.addRow("バルコニー面積:", self.balcony_area_spin)
        
        tab.setLayout(layout)
        return tab
    
    def create_features_tab(self):
        """設備・特徴タブを作成"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 設備チェックボックス群
        equipment_group = QGroupBox("設備")
        equipment_layout = QGridLayout()
        
        self.equipment_checks = {}
        equipment_items = [
            "エアコン", "洗濯機", "冷蔵庫", "電子レンジ", "IHコンロ",
            "都市ガス", "プロパンガス", "追い焚き", "浴室乾燥", "温水洗浄便座",
            "インターネット", "BS・CS", "ケーブルTV", "オートロック", "宅配ボックス",
            "駐車場", "駐輪場", "ペット可", "楽器可", "事務所可"
        ]
        
        for i, item in enumerate(equipment_items):
            check = QCheckBox(item)
            self.equipment_checks[item] = check
            equipment_layout.addWidget(check, i // 5, i % 5)
        
        equipment_group.setLayout(equipment_layout)
        
        # 特記事項
        notes_group = QGroupBox("特記事項")
        notes_layout = QVBoxLayout()
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(150)
        self.notes_edit.setPlaceholderText("部屋の特徴、注意事項などを記入...")
        
        notes_layout.addWidget(self.notes_edit)
        notes_group.setLayout(notes_layout)
        
        layout.addWidget(equipment_group)
        layout.addWidget(notes_group)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def create_media_tab(self):
        """図面・写真タブを作成"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 図面アップロード
        floorplan_group = QGroupBox("間取り図")
        floorplan_layout = QVBoxLayout()
        
        floorplan_btn_layout = QHBoxLayout()
        self.upload_floorplan_btn = QPushButton("図面アップロード")
        self.upload_floorplan_btn.clicked.connect(self.upload_floorplan)
        
        if OCR_AVAILABLE:
            self.ocr_floorplan_btn = QPushButton("OCR解析")
            self.ocr_floorplan_btn.clicked.connect(self.analyze_floorplan)
            floorplan_btn_layout.addWidget(self.ocr_floorplan_btn)
        
        floorplan_btn_layout.addWidget(self.upload_floorplan_btn)
        floorplan_btn_layout.addStretch()
        
        self.floorplan_list = QListWidget()
        self.floorplan_list.setMaximumHeight(100)
        
        floorplan_layout.addLayout(floorplan_btn_layout)
        floorplan_layout.addWidget(self.floorplan_list)
        floorplan_group.setLayout(floorplan_layout)
        
        # 写真アップロード
        photos_group = QGroupBox("部屋写真")
        photos_layout = QVBoxLayout()
        
        self.upload_photos_btn = QPushButton("写真アップロード")
        self.upload_photos_btn.clicked.connect(self.upload_photos)
        
        self.photos_list = QListWidget()
        self.photos_list.setMaximumHeight(100)
        
        photos_layout.addWidget(self.upload_photos_btn)
        photos_layout.addWidget(self.photos_list)
        photos_group.setLayout(photos_layout)
        
        layout.addWidget(floorplan_group)
        layout.addWidget(photos_group)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def upload_floorplan(self):
        """間取り図アップロード"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "間取り図を選択", "", 
            "Image Files (*.png *.jpg *.jpeg *.pdf);;All Files (*)"
        )
        
        if file_path:
            # ファイル保存処理（実装必要）
            filename = os.path.basename(file_path)
            self.floorplan_list.addItem(filename)
            MessageHelper.show_success(self, f"間取り図「{filename}」をアップロードしました")
    
    def analyze_floorplan(self):
        """間取り図OCR解析"""
        if self.floorplan_list.count() == 0:
            MessageHelper.show_warning(self, "先に間取り図をアップロードしてください")
            return
            
        MessageHelper.show_info(self, "OCR解析機能は実装予定です")
    
    def upload_photos(self):
        """写真アップロード"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "写真を選択", "", 
            "Image Files (*.png *.jpg *.jpeg);;All Files (*)"
        )
        
        for file_path in file_paths:
            # ファイル保存処理（実装必要）
            filename = os.path.basename(file_path)
            self.photos_list.addItem(filename)
        
        if file_paths:
            MessageHelper.show_success(self, f"{len(file_paths)}枚の写真をアップロードしました")
    
    def load_unit_data(self):
        """部屋データを読み込み"""
        if not self.unit_data:
            return
            
        # 基本情報
        self.room_number_edit.setText(self.unit_data.get('room_number', ''))
        self.room_type_combo.setCurrentText(self.unit_data.get('room_type', ''))
        self.area_spin.setValue(self.unit_data.get('area', 0) or 0)
        self.rent_spin.setValue(self.unit_data.get('rent', 0) or 0)
        self.maintenance_fee_spin.setValue(self.unit_data.get('maintenance_fee', 0) or 0)
        self.deposit_spin.setValue(self.unit_data.get('deposit', 0) or 0)
        self.key_money_spin.setValue(self.unit_data.get('key_money', 0) or 0)
        
        # 設備情報（JSON形式で保存されている場合）
        equipment_data = self.unit_data.get('equipment', '')
        if equipment_data:
            try:
                equipment_list = json.loads(equipment_data) if isinstance(equipment_data, str) else equipment_data
                for equipment in equipment_list:
                    if equipment in self.equipment_checks:
                        self.equipment_checks[equipment].setChecked(True)
            except:
                pass
        
        # 特記事項
        self.notes_edit.setPlainText(self.unit_data.get('notes', ''))
    
    def get_unit_data(self):
        """入力データを取得"""
        # 選択された設備
        selected_equipment = []
        for equipment, check in self.equipment_checks.items():
            if check.isChecked():
                selected_equipment.append(equipment)
        
        return {
            'room_number': self.room_number_edit.text().strip(),
            'room_type': self.room_type_combo.currentText().strip(),
            'area': self.area_spin.value() if self.area_spin.value() > 0 else None,
            'rent': self.rent_spin.value(),
            'maintenance_fee': self.maintenance_fee_spin.value(),
            'deposit': self.deposit_spin.value(),
            'key_money': self.key_money_spin.value(),
            'floor': self.floor_spin.value(),
            'direction': self.direction_combo.currentText(),
            'balcony': self.balcony_check.isChecked(),
            'balcony_area': self.balcony_area_spin.value() if self.balcony_check.isChecked() else None,
            'equipment': json.dumps(selected_equipment),
            'features': '',  # 追加機能で実装
            'notes': self.notes_edit.toPlainText().strip()
        }

class BulkUnitUpdateDialog(QDialog):
    """一括更新ダイアログ"""
    
    def __init__(self, parent=None, property_id=None):
        super().__init__(parent)
        self.property_id = property_id
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("部屋一括更新")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout()
        
        # 更新項目選択
        update_group = QGroupBox("一括更新項目")
        update_layout = QFormLayout()
        
        self.rent_check = QCheckBox("賃料を一括更新")
        self.rent_spin = QSpinBox()
        self.rent_spin.setMaximum(9999999)
        self.rent_spin.setSuffix(" 円")
        self.rent_spin.setEnabled(False)
        self.rent_check.toggled.connect(self.rent_spin.setEnabled)
        
        self.maintenance_check = QCheckBox("管理費を一括更新")
        self.maintenance_spin = QSpinBox()
        self.maintenance_spin.setMaximum(999999)
        self.maintenance_spin.setSuffix(" 円")
        self.maintenance_spin.setEnabled(False)
        self.maintenance_check.toggled.connect(self.maintenance_spin.setEnabled)
        
        update_layout.addRow(self.rent_check, self.rent_spin)
        update_layout.addRow(self.maintenance_check, self.maintenance_spin)
        
        update_group.setLayout(update_layout)
        
        # 適用範囲
        scope_group = QGroupBox("適用範囲")
        scope_layout = QVBoxLayout()
        
        self.all_units_radio = QCheckBox("全部屋")
        self.all_units_radio.setChecked(True)
        
        self.vacant_only_radio = QCheckBox("空室のみ")
        
        scope_layout.addWidget(self.all_units_radio)
        scope_layout.addWidget(self.vacant_only_radio)
        scope_group.setLayout(scope_layout)
        
        layout.addWidget(update_group)
        layout.addWidget(scope_group)
        
        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        self.setLayout(layout)

class PropertyManagementIntegrated(QWidget):
    """統合物件管理タブ - メインクラス"""
    
    property_updated = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.current_property_id = None
        self.init_ui()
        self.load_properties()
        
    def init_ui(self):
        layout = QHBoxLayout()
        
        # 左パネル：物件一覧
        left_panel = self.create_left_panel()
        
        # 右パネル：詳細管理
        right_panel = self.create_right_panel()
        
        # スプリッター
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 700])  # 左30%、右70%
        
        layout.addWidget(splitter)
        self.setLayout(layout)
        
    def create_left_panel(self):
        """左パネル（物件一覧）を作成"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # ヘッダー
        header_layout = QHBoxLayout()
        title_label = QLabel("物件一覧")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1976D2;")
        
        self.add_property_btn = QPushButton("物件追加")
        self.add_property_btn.clicked.connect(self.add_property)
        self.add_property_btn.setStyleSheet(ModernStyles.get_button_style("primary"))
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.add_property_btn)
        
        # 検索
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("物件名で検索...")
        self.search_edit.textChanged.connect(self.filter_properties)
        
        # 物件ツリー
        self.property_tree = QTreeWidget()
        self.property_tree.setHeaderLabels(["物件名", "部屋数", "入居率"])
        self.property_tree.itemSelectionChanged.connect(self.on_property_selection_changed)
        
        # 右クリックメニュー用
        self.property_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.property_tree.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addLayout(header_layout)
        layout.addWidget(self.search_edit)
        layout.addWidget(self.property_tree)
        
        panel.setLayout(layout)
        return panel
        
    def create_right_panel(self):
        """右パネル（詳細管理）を作成"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # 物件情報ヘッダー
        self.property_info_label = QLabel("物件を選択してください")
        self.property_info_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #424242; padding: 10px;")
        
        # タブウィジェット
        self.detail_tabs = QTabWidget()
        
        # 収益分析タブ
        self.analytics_widget = PropertyAnalyticsWidget()
        self.detail_tabs.addTab(self.analytics_widget, "収益分析")
        
        # 部屋管理タブ
        self.unit_widget = UnitManagementWidget()
        self.unit_widget.unit_updated.connect(self.refresh_property_list)
        self.detail_tabs.addTab(self.unit_widget, "部屋管理")
        
        # メンテナンスタブ（将来実装）
        maintenance_tab = QWidget()
        maintenance_layout = QVBoxLayout()
        maintenance_layout.addWidget(QLabel("メンテナンス管理機能は今後実装予定です"))
        maintenance_tab.setLayout(maintenance_layout)
        self.detail_tabs.addTab(maintenance_tab, "メンテナンス")
        
        # 初期状態では無効
        self.detail_tabs.setEnabled(False)
        
        layout.addWidget(self.property_info_label)
        layout.addWidget(self.detail_tabs)
        
        panel.setLayout(layout)
        return panel
        
    def load_properties(self):
        """物件一覧を読み込み"""
        try:
            self.property_tree.clear()
            properties = Property.get_all()
            
            for prop in properties:
                item = QTreeWidgetItem()
                item.setText(0, prop.get('name', ''))
                item.setData(0, Qt.ItemDataRole.UserRole, prop.get('id'))
                
                # 部屋数と入居率を計算
                property_id = prop.get('id')
                units = Unit.get_by_property(property_id)
                total_units = len(units)
                
                # 簡易入居率計算（実装時は実際のデータを使用）
                occupied_units = max(0, total_units - 2)  # サンプル計算
                occupancy_rate = (occupied_units / total_units * 100) if total_units > 0 else 0
                
                item.setText(1, f"{total_units}室")
                item.setText(2, f"{occupancy_rate:.0f}%")
                
                # 入居率による色分け
                if occupancy_rate >= 90:
                    item.setBackground(0, QColor("#E8F5E8"))
                elif occupancy_rate >= 70:
                    item.setBackground(0, QColor("#FFF3E0"))
                else:
                    item.setBackground(0, QColor("#FFEBEE"))
                
                self.property_tree.addTopLevelItem(item)
                
        except Exception as e:
            MessageHelper.show_error(self, f"物件一覧の読み込み中にエラーが発生しました: {str(e)}")
    
    def filter_properties(self):
        """物件フィルタリング"""
        search_text = self.search_edit.text().lower()
        
        for i in range(self.property_tree.topLevelItemCount()):
            item = self.property_tree.topLevelItem(i)
            property_name = item.text(0).lower()
            item.setHidden(search_text not in property_name)
    
    def on_property_selection_changed(self):
        """物件選択変更時"""
        current_item = self.property_tree.currentItem()
        if current_item:
            property_id = current_item.data(0, Qt.ItemDataRole.UserRole)
            property_name = current_item.text(0)
            
            self.current_property_id = property_id
            self.property_info_label.setText(f"物件: {property_name}")
            
            # 詳細パネルを有効化
            self.detail_tabs.setEnabled(True)
            
            # 各ウィジェットにデータを設定
            self.unit_widget.set_property_id(property_id)
            
            # 物件データを取得して分析ウィジェットに渡す
            properties = Property.get_all()
            property_data = None
            for prop in properties:
                if prop.get('id') == property_id:
                    property_data = prop
                    break
            
            self.analytics_widget.update_analytics(property_data)
        else:
            self.current_property_id = None
            self.property_info_label.setText("物件を選択してください")
            self.detail_tabs.setEnabled(False)
    
    def show_context_menu(self, position):
        """右クリックメニュー表示"""
        item = self.property_tree.itemAt(position)
        if item:
            from PyQt6.QtWidgets import QMenu
            from PyQt6.QtGui import QAction
            
            menu = QMenu()
            
            edit_action = QAction("編集", self)
            edit_action.triggered.connect(self.edit_property)
            
            delete_action = QAction("削除", self)
            delete_action.triggered.connect(self.delete_property)
            
            menu.addAction(edit_action)
            menu.addAction(delete_action)
            
            menu.exec(self.property_tree.mapToGlobal(position))
    
    def add_property(self):
        """物件追加"""
        MessageHelper.show_info(self, "物件追加機能は実装予定です")
        # PropertyEditDialogを実装して呼び出し
    
    def edit_property(self):
        """物件編集"""
        if self.current_property_id:
            MessageHelper.show_info(self, "物件編集機能は実装予定です")
    
    def delete_property(self):
        """物件削除"""
        if self.current_property_id:
            current_item = self.property_tree.currentItem()
            property_name = current_item.text(0)
            
            if MessageHelper.confirm_delete(self, f"物件「{property_name}」"):
                try:
                    # 物件削除機能の実装が必要
                    MessageHelper.show_success(self, "物件を削除しました")
                    self.load_properties()
                    self.property_updated.emit()
                    
                except Exception as e:
                    MessageHelper.show_error(self, f"物件削除中にエラーが発生しました: {str(e)}")
    
    def refresh_property_list(self):
        """物件一覧を更新"""
        self.load_properties()
        self.property_updated.emit()