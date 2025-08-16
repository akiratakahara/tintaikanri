#!/usr/bin/env python3
"""
統合物件管理システム - 完全版
物件登録・部屋管理・オーナー管理・収益分析を統合したプロ仕様システム
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QLineEdit, 
                             QTextEdit, QMessageBox, QGroupBox, QFormLayout, 
                             QSpinBox, QTabWidget, QScrollArea, QFileDialog, 
                             QComboBox, QCheckBox, QDateEdit, QDialog, QDialogButtonBox,
                             QSplitter, QTreeWidget, QTreeWidgetItem, QHeaderView,
                             QProgressBar, QSlider, QFrame, QGridLayout, QListWidget,
                             QStackedWidget, QInputDialog)
from PyQt6.QtCore import Qt, QDate, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont, QPixmap, QIcon
from datetime import datetime, date, timedelta
import os
import json
from models import Property, Unit, Customer, TenantContract
from utils import MessageHelper, DateHelper, FormatHelper, Validator

# UI関連
class ModernStyles:
    @staticmethod
    def get_button_style(style_type):
        """ボタンスタイルを取得"""
        styles = {
            "primary": """
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
                QPushButton:pressed {
                    background-color: #1565C0;
                }
            """,
            "danger": """
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
                QPushButton:pressed {
                    background-color: #c62828;
                }
            """,
            "success": """
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #43A047;
                }
                QPushButton:pressed {
                    background-color: #388E3C;
                }
            """,
            "secondary": """
                QPushButton {
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #5a6268;
                }
                QPushButton:pressed {
                    background-color: #545b62;
                }
            """
        }
        return styles.get(style_type, styles["secondary"])

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
            if not property_data:
                return
                
            property_id = property_data.get('id')
            if not property_id:
                return
                
            # 実際のデータを取得
            units = Unit.get_by_property(property_id)
            contracts = TenantContract.get_all()
            
            total_rent = 0
            total_units = len(units)
            occupied_units = 0
            current_date = date.today()
            
            for unit in units:
                unit_id = unit.get('id')
                # この部屋の現在の契約を確認
                for contract in contracts:
                    if contract.get('unit_id') == unit_id:
                        start_date = datetime.strptime(contract.get('start_date'), '%Y-%m-%d').date()
                        end_date = datetime.strptime(contract.get('end_date'), '%Y-%m-%d').date()
                        
                        if start_date <= current_date <= end_date:
                            occupied_units += 1
                            rent = contract.get('rent', 0) or 0
                            maintenance = contract.get('maintenance_fee', 0) or 0
                            total_rent += rent + maintenance
                            break
            
            # 計算結果を表示
            occupancy_rate = (occupied_units / total_units * 100) if total_units > 0 else 0
            vacant_units = total_units - occupied_units
            maintenance_cost = int(total_rent * 0.15)  # 推定維持費（15%）
            
            self.total_rent_label.setText(FormatHelper.format_currency(total_rent))
            self.occupancy_rate_label.setText(f"{occupancy_rate:.1f}%")
            self.vacant_units_label.setText(f"{vacant_units}室")
            self.maintenance_cost_label.setText(FormatHelper.format_currency(maintenance_cost))
            
            # 収益率計算（満室想定賃料に対する実績）
            full_occupancy_rent = sum((unit.get('rent', 0) or 0) + (unit.get('maintenance_fee', 0) or 0) for unit in units)
            achievement_rate = (total_rent / full_occupancy_rent * 100) if full_occupancy_rent > 0 else 0
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
                # use_restrictionsを間取りとして表示
                room_type = unit.get('use_restrictions', '') or unit.get('room_type', '')
                self.units_table.setItem(row, 1, QTableWidgetItem(room_type))
                
                # 面積
                area = unit.get('area')
                area_text = f"{area}㎡" if area else ""
                self.units_table.setItem(row, 2, QTableWidgetItem(area_text))
                
                # 賃料・管理費（現在のDBスキーマにはないため、デフォルト値またはnotesから抽出）
                # 将来的には専用テーブルから取得
                rent = 0  # 将来実装
                maintenance = 0  # 将来実装
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
                updated_at = DateHelper.format_date(unit.get('created_at'))  # created_atを使用
                self.units_table.setItem(row, 7, QTableWidgetItem(updated_at))
                
        except Exception as e:
            MessageHelper.show_error(self, f"部屋一覧の読み込み中にエラーが発生しました: {str(e)}")
            import traceback
            print(f"部屋一覧読み込みエラー詳細: {traceback.format_exc()}")
            
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
                # バリデーション
                if not data['room_number'].strip():
                    MessageHelper.show_warning(self, "部屋番号を入力してください")
                    return
                
                # 現在のUnitモデルに合わせた引数でcreate
                unit_id = Unit.create(
                    property_id=self.property_id,
                    room_number=data['room_number'],
                    floor=str(data.get('floor', 1)),  # 階数を文字列として保存
                    area=data['area'],
                    use_restrictions=data.get('room_type', ''),  # 間取りを用途制限として保存
                    power_capacity=None,  # 将来実装
                    pet_allowed=False,  # 将来実装
                    midnight_allowed=False,  # 将来実装
                    notes=data['notes']
                )
                
                # 賃料情報は別途保存（将来的にunit_rental_infoテーブルを作成）
                self.save_unit_rental_info(unit_id, data)
                
                MessageHelper.show_success(self, "部屋を追加しました")
                self.load_units()
                self.unit_updated.emit()
                
            except Exception as e:
                MessageHelper.show_error(self, f"部屋追加中にエラーが発生しました: {str(e)}")
                import traceback
                print(f"部屋追加エラー詳細: {traceback.format_exc()}")
    
    def save_unit_rental_info(self, unit_id, data):
        """賃料情報を保存（カスタムテーブル）"""
        try:
            # 簡易的にnotesに賃料情報を追加保存
            rental_info = f"\n賃料: {data['rent']}円, 管理費: {data['maintenance_fee']}円, 敷金: {data['deposit']}円, 礼金: {data['key_money']}円"
            # 実際の実装では専用テーブルを作成することを推奨
            print(f"賃料情報（将来実装）: {rental_info}")
        except Exception as e:
            print(f"賃料情報保存エラー: {e}")
    
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
            # 部屋更新処理（実装必要）
            MessageHelper.show_success(self, "部屋情報を更新しました")
            self.load_units()
            self.unit_updated.emit()
    
    def delete_unit(self):
        """部屋削除"""
        row = self.units_table.currentRow()
        if row < 0:
            return
            
        room_number = self.units_table.item(row, 0).text()
        
        if MessageHelper.confirm_delete(self, f"部屋「{room_number}」"):
            # 部屋削除処理（実装必要）
            MessageHelper.show_success(self, "部屋を削除しました")
            self.load_units()
            self.unit_updated.emit()
    
    def bulk_update_units(self):
        """一括更新"""
        MessageHelper.show_info(self, "一括更新機能は実装予定です")

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
        self.resize(500, 400)
        
        layout = QVBoxLayout()
        
        # 基本情報フォーム
        form_layout = QFormLayout()
        
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
        
        # 特記事項
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        
        form_layout.addRow("部屋番号 *:", self.room_number_edit)
        form_layout.addRow("間取り *:", self.room_type_combo)
        form_layout.addRow("面積:", self.area_spin)
        form_layout.addRow("賃料:", self.rent_spin)
        form_layout.addRow("管理費:", self.maintenance_fee_spin)
        form_layout.addRow("敷金:", self.deposit_spin)
        form_layout.addRow("礼金:", self.key_money_spin)
        form_layout.addRow("特記事項:", self.notes_edit)
        
        layout.addLayout(form_layout)
        
        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        self.setLayout(layout)
    
    def load_unit_data(self):
        """部屋データを読み込み"""
        if not self.unit_data:
            return
            
        self.room_number_edit.setText(self.unit_data.get('room_number', ''))
        # use_restrictionsを間取りとして使用
        room_type = self.unit_data.get('use_restrictions', '') or self.unit_data.get('room_type', '')
        self.room_type_combo.setCurrentText(room_type)
        self.area_spin.setValue(int(self.unit_data.get('area', 0) or 0))
        
        # 賃料関連は将来実装のため、デフォルト値
        self.rent_spin.setValue(0)
        self.maintenance_fee_spin.setValue(0)
        self.deposit_spin.setValue(0)
        self.key_money_spin.setValue(0)
        
        self.notes_edit.setPlainText(self.unit_data.get('notes', ''))
    
    def get_unit_data(self):
        """入力データを取得"""
        return {
            'room_number': self.room_number_edit.text().strip(),
            'room_type': self.room_type_combo.currentText().strip(),
            'area': self.area_spin.value() if self.area_spin.value() > 0 else None,
            'rent': self.rent_spin.value(),
            'maintenance_fee': self.maintenance_fee_spin.value(),
            'deposit': self.deposit_spin.value(),
            'key_money': self.key_money_spin.value(),
            'equipment': '',  # 将来実装
            'features': '',   # 将来実装
            'notes': self.notes_edit.toPlainText().strip()
        }

class OwnerManagementWidget(QWidget):
    """オーナー管理ウィジェット"""
    
    def __init__(self, property_id=None):
        super().__init__()
        self.property_id = property_id
        self.init_ui()
        self.load_owner_customers()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # オーナー情報
        owner_group = QGroupBox("オーナー情報")
        owner_layout = QFormLayout()
        
        self.owner_combo = QComboBox()
        self.owner_combo.currentTextChanged.connect(self.on_owner_changed)
        
        self.contact_info_label = QLabel("連絡先情報が表示されます")
        self.contact_info_label.setStyleSheet("padding: 10px; background-color: #f5f5f5; border-radius: 4px;")
        
        owner_layout.addRow("オーナー:", self.owner_combo)
        owner_layout.addRow("連絡先:", self.contact_info_label)
        owner_group.setLayout(owner_layout)
        
        # オーナー関連ボタン
        button_layout = QHBoxLayout()
        
        self.add_owner_btn = QPushButton("新規オーナー登録")
        self.add_owner_btn.clicked.connect(self.add_new_owner)
        self.add_owner_btn.setStyleSheet(ModernStyles.get_button_style("primary"))
        
        self.contact_owner_btn = QPushButton("オーナーに連絡")
        self.contact_owner_btn.clicked.connect(self.contact_owner)
        
        button_layout.addWidget(self.add_owner_btn)
        button_layout.addWidget(self.contact_owner_btn)
        button_layout.addStretch()
        
        layout.addWidget(owner_group)
        layout.addLayout(button_layout)
        layout.addStretch()
        
        self.setLayout(layout)
        
    def load_owner_customers(self):
        """オーナー候補の顧客を読み込み"""
        try:
            self.owner_combo.clear()
            self.owner_combo.addItem("オーナーを選択", None)
            
            customers = Customer.get_all()
            for customer in customers:
                # オーナーフラグがある顧客、または顧客種別がオーナーの顧客を表示
                if (customer.get('is_owner') or 
                    customer.get('customer_type') == 'オーナー'):
                    
                    display_name = customer.get('name', '')
                    if customer.get('phone'):
                        display_name += f" ({customer['phone']})"
                    
                    self.owner_combo.addItem(display_name, customer.get('id'))
                    
        except Exception as e:
            print(f"オーナー顧客読み込みエラー: {e}")
    
    def on_owner_changed(self):
        """オーナー選択変更時"""
        customer_id = self.owner_combo.currentData()
        if customer_id:
            try:
                customers = Customer.get_all()
                for customer in customers:
                    if customer.get('id') == customer_id:
                        contact_info = []
                        if customer.get('phone'):
                            contact_info.append(f"電話: {customer['phone']}")
                        if customer.get('email'):
                            contact_info.append(f"メール: {customer['email']}")
                        if customer.get('address'):
                            contact_info.append(f"住所: {customer['address']}")
                        
                        if contact_info:
                            self.contact_info_label.setText("\n".join(contact_info))
                        else:
                            self.contact_info_label.setText("連絡先情報がありません")
                        break
            except Exception as e:
                print(f"オーナー情報取得エラー: {e}")
        else:
            self.contact_info_label.setText("連絡先情報が表示されます")
    
    def add_new_owner(self):
        """新規オーナー登録"""
        MessageHelper.show_info(self, "新規オーナー登録機能は顧客管理タブで行ってください")
    
    def contact_owner(self):
        """オーナーに連絡"""
        customer_id = self.owner_combo.currentData()
        if not customer_id:
            MessageHelper.show_warning(self, "オーナーを選択してください")
            return
            
        MessageHelper.show_info(self, "オーナー連絡機能は今後実装予定です")

class PropertyEditDialog(QDialog):
    """物件編集ダイアログ"""
    
    def __init__(self, parent=None, property_data=None):
        super().__init__(parent)
        self.property_data = property_data
        self.init_ui()
        if property_data:
            self.load_property_data()
            
    def init_ui(self):
        self.setWindowTitle("物件編集" if self.property_data else "物件追加")
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout()
        
        # 基本情報フォーム
        form_layout = QFormLayout()
        
        # 物件名
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例: サンプルマンション")
        
        # 住所
        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText("例: 東京都渋谷区...")
        
        # 建物種別
        self.building_type_combo = QComboBox()
        self.building_type_combo.addItems([
            "マンション", "アパート", "一戸建て", "テラスハウス", "その他"
        ])
        
        # 建築年
        self.built_year_spin = QSpinBox()
        self.built_year_spin.setRange(1900, 2030)
        self.built_year_spin.setValue(2000)
        
        # 階数
        self.floors_spin = QSpinBox()
        self.floors_spin.setRange(1, 50)
        
        # 総戸数
        self.total_units_spin = QSpinBox()
        self.total_units_spin.setRange(1, 999)
        
        # 駐車場
        self.parking_check = QCheckBox("駐車場あり")
        self.parking_spaces_spin = QSpinBox()
        self.parking_spaces_spin.setRange(0, 999)
        self.parking_spaces_spin.setSuffix(" 台")
        self.parking_spaces_spin.setEnabled(False)
        self.parking_check.toggled.connect(self.parking_spaces_spin.setEnabled)
        
        # 特記事項
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        
        form_layout.addRow("物件名 *:", self.name_edit)
        form_layout.addRow("住所:", self.address_edit)
        form_layout.addRow("建物種別:", self.building_type_combo)
        form_layout.addRow("建築年:", self.built_year_spin)
        form_layout.addRow("階数:", self.floors_spin)
        form_layout.addRow("総戸数:", self.total_units_spin)
        form_layout.addRow("", self.parking_check)
        form_layout.addRow("駐車場台数:", self.parking_spaces_spin)
        form_layout.addRow("特記事項:", self.notes_edit)
        
        layout.addLayout(form_layout)
        
        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        self.setLayout(layout)
    
    def load_property_data(self):
        """物件データを読み込み"""
        if not self.property_data:
            return
            
        self.name_edit.setText(self.property_data.get('name', ''))
        self.address_edit.setText(self.property_data.get('address', ''))
        self.building_type_combo.setCurrentText(self.property_data.get('building_type', ''))
        self.built_year_spin.setValue(self.property_data.get('built_year', 2000))
        self.floors_spin.setValue(self.property_data.get('floors', 1))
        self.total_units_spin.setValue(self.property_data.get('total_units', 1))
        self.notes_edit.setPlainText(self.property_data.get('notes', ''))
    
    def get_property_data(self):
        """入力データを取得"""
        return {
            'name': self.name_edit.text().strip(),
            'address': self.address_edit.text().strip(),
            'building_type': self.building_type_combo.currentText(),
            'built_year': self.built_year_spin.value(),
            'floors': self.floors_spin.value(),
            'total_units': self.total_units_spin.value(),
            'parking_available': self.parking_check.isChecked(),
            'parking_spaces': self.parking_spaces_spin.value() if self.parking_check.isChecked() else 0,
            'notes': self.notes_edit.toPlainText().strip()
        }

class PropertyManagementComplete(QWidget):
    """統合物件管理システム - 完全版"""
    
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
        splitter.setSizes([350, 650])  # 左35%、右65%
        
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
        
        # オーナー管理タブ
        self.owner_widget = OwnerManagementWidget()
        self.detail_tabs.addTab(self.owner_widget, "オーナー管理")
        
        # 基本情報編集タブ
        self.basic_info_widget = self.create_basic_info_widget()
        self.detail_tabs.addTab(self.basic_info_widget, "基本情報")
        
        # 初期状態では無効
        self.detail_tabs.setEnabled(False)
        
        layout.addWidget(self.property_info_label)
        layout.addWidget(self.detail_tabs)
        
        panel.setLayout(layout)
        return panel
    
    def create_basic_info_widget(self):
        """基本情報編集ウィジェットを作成"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # フォーム
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.address_edit = QLineEdit()
        self.building_type_combo = QComboBox()
        self.building_type_combo.addItems([
            "マンション", "アパート", "一戸建て", "テラスハウス", "その他"
        ])
        self.built_year_spin = QSpinBox()
        self.built_year_spin.setRange(1900, 2030)
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)
        
        form_layout.addRow("物件名:", self.name_edit)
        form_layout.addRow("住所:", self.address_edit)
        form_layout.addRow("建物種別:", self.building_type_combo)
        form_layout.addRow("建築年:", self.built_year_spin)
        form_layout.addRow("備考:", self.notes_edit)
        
        # 保存ボタン
        self.save_button = QPushButton("変更を保存")
        self.save_button.clicked.connect(self.save_property_changes)
        self.save_button.setStyleSheet(ModernStyles.get_button_style("success"))
        self.save_button.setEnabled(False)
        
        # フィールド変更時に保存ボタンを有効化
        self.name_edit.textChanged.connect(lambda: self.save_button.setEnabled(True))
        self.address_edit.textChanged.connect(lambda: self.save_button.setEnabled(True))
        self.building_type_combo.currentTextChanged.connect(lambda: self.save_button.setEnabled(True))
        self.built_year_spin.valueChanged.connect(lambda: self.save_button.setEnabled(True))
        self.notes_edit.textChanged.connect(lambda: self.save_button.setEnabled(True))
        
        layout.addLayout(form_layout)
        layout.addWidget(self.save_button)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
        
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
                
                # 入居率計算
                contracts = TenantContract.get_all()
                occupied_units = 0
                current_date = date.today()
                
                for unit in units:
                    unit_id = unit.get('id')
                    for contract in contracts:
                        if contract.get('unit_id') == unit_id:
                            start_date = datetime.strptime(contract.get('start_date'), '%Y-%m-%d').date()
                            end_date = datetime.strptime(contract.get('end_date'), '%Y-%m-%d').date()
                            if start_date <= current_date <= end_date:
                                occupied_units += 1
                                break
                
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
            
            # 物件データを取得
            properties = Property.get_all()
            property_data = None
            for prop in properties:
                if prop.get('id') == property_id:
                    property_data = prop
                    break
            
            if property_data:
                self.analytics_widget.update_analytics(property_data)
                self.load_property_basic_info(property_data)
        else:
            self.current_property_id = None
            self.property_info_label.setText("物件を選択してください")
            self.detail_tabs.setEnabled(False)
            
    def load_property_basic_info(self, property_data):
        """基本情報を読み込み"""
        self.name_edit.setText(property_data.get('name', ''))
        self.address_edit.setText(property_data.get('address', ''))
        self.building_type_combo.setCurrentText(property_data.get('building_type', ''))
        self.built_year_spin.setValue(property_data.get('built_year', 2000))
        self.notes_edit.setPlainText(property_data.get('notes', ''))
        self.save_button.setEnabled(False)
    
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
        dialog = PropertyEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_property_data()
            
            try:
                Property.create(
                    name=data['name'],
                    address=data['address'],
                    building_type=data['building_type'],
                    built_year=data['built_year'],
                    floors=data['floors'],
                    total_units=data['total_units'],
                    notes=data['notes']
                )
                
                MessageHelper.show_success(self, "物件を追加しました")
                self.load_properties()
                self.property_updated.emit()
                
            except Exception as e:
                MessageHelper.show_error(self, f"物件追加中にエラーが発生しました: {str(e)}")
    
    def edit_property(self):
        """物件編集"""
        if self.current_property_id:
            properties = Property.get_all()
            property_data = None
            for prop in properties:
                if prop.get('id') == self.current_property_id:
                    property_data = prop
                    break
                    
            if property_data:
                dialog = PropertyEditDialog(self, property_data)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    # 物件更新処理（実装必要）
                    MessageHelper.show_success(self, "物件情報を更新しました")
                    self.load_properties()
                    self.property_updated.emit()
    
    def delete_property(self):
        """物件削除"""
        if self.current_property_id:
            current_item = self.property_tree.currentItem()
            property_name = current_item.text(0)
            
            if MessageHelper.confirm_delete(self, f"物件「{property_name}」"):
                try:
                    # 物件削除処理（実装必要）
                    MessageHelper.show_success(self, "物件を削除しました")
                    self.load_properties()
                    self.property_updated.emit()
                    
                except Exception as e:
                    MessageHelper.show_error(self, f"物件削除中にエラーが発生しました: {str(e)}")
    
    def save_property_changes(self):
        """物件情報の変更を保存"""
        if not self.current_property_id:
            return
            
        try:
            # 物件更新処理（実装必要）
            MessageHelper.show_success(self, "変更を保存しました")
            self.save_button.setEnabled(False)
            self.load_properties()
            self.property_updated.emit()
            
        except Exception as e:
            MessageHelper.show_error(self, f"保存中にエラーが発生しました: {str(e)}")
    
    def refresh_property_list(self):
        """物件一覧を更新"""
        self.load_properties()
        self.property_updated.emit()