#!/usr/bin/env python3
"""
部屋管理タブ
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QLineEdit, 
                             QTextEdit, QMessageBox, QGroupBox, QFormLayout, 
                             QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QDialog, QDialogButtonBox, QTabWidget, QFileDialog)
from PyQt6.QtCore import Qt, QDate, QThread, pyqtSignal
import sys
import os

# プロジェクトルートをPythonパスに追加（tabsフォルダ内のモジュールがルートのモジュールにアクセスできるように）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Unit, Property, Customer

# OCR機能をオプショナルにする
try:
    from ocr.floorplan_ocr import FloorplanOCR
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("注意: 図面OCR機能が利用できません")

class FloorplanOCRWorker(QThread):
    """募集図面OCR処理を非同期で実行するワーカースレッド"""
    finished = pyqtSignal(list)  # OCR結果
    error = pyqtSignal(str)
    
    def __init__(self, image_path: str):
        super().__init__()
        self.image_path = image_path
        if OCR_AVAILABLE:
            self.ocr = FloorplanOCR()
        else:
            self.ocr = None
    
    def run(self):
        try:
            if not OCR_AVAILABLE:
                self.error.emit("OCR機能が利用できません")
                return
                
            result = self.ocr.extract_room_info(self.image_path)
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(str(e))

class UnitTab(QWidget):
    def __init__(self):
        super().__init__()
        self.current_unit_id = None
        self.init_ui()
    
    def init_ui(self):
        """UIを初期化"""
        layout = QVBoxLayout()
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        
        # 手動入力タブ
        self.manual_tab = self.create_manual_tab()
        self.tab_widget.addTab(self.manual_tab, "手動入力")
        
        # 募集図面アップロードタブ
        self.upload_tab = self.create_upload_tab()
        self.tab_widget.addTab(self.upload_tab, "募集図面アップロード")
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
    
    def create_manual_tab(self):
        """手動入力タブを作成"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # フォームグループ
        form_group = QGroupBox("部屋情報入力")
        form_layout = QFormLayout()
        
        # 物件選択
        self.property_combo = QComboBox()
        self.load_property_combo()
        form_layout.addRow("物件:", self.property_combo)
        
        # 基本情報
        self.room_number_edit = QLineEdit()
        self.floor_spin = QSpinBox()
        self.floor_spin.setRange(1, 100)
        self.area_spin = QSpinBox()
        self.area_spin.setRange(1, 1000)
        self.area_spin.setSuffix(" ㎡")
        
        form_layout.addRow("部屋番号:", self.room_number_edit)
        form_layout.addRow("階数:", self.floor_spin)
        form_layout.addRow("面積:", self.area_spin)
        
        # 使用制限
        self.use_restrictions_edit = QTextEdit()
        self.use_restrictions_edit.setMaximumHeight(60)
        form_layout.addRow("使用制限:", self.use_restrictions_edit)
        
        # 設備・条件
        self.power_capacity_spin = QSpinBox()
        self.power_capacity_spin.setRange(0, 1000)
        self.power_capacity_spin.setSuffix(" kW")
        
        self.pet_allowed_check = QCheckBox("ペット可")
        self.midnight_allowed_check = QCheckBox("深夜営業可")
        
        form_layout.addRow("電力容量:", self.power_capacity_spin)
        form_layout.addRow("", self.pet_allowed_check)
        form_layout.addRow("", self.midnight_allowed_check)
        
        # 備考
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        form_layout.addRow("備考:", self.notes_edit)
        
        form_group.setLayout(form_layout)
        
        # オーナー情報グループ（区分所有対応）
        owner_group = QGroupBox("オーナー情報（区分所有）")
        owner_layout = QVBoxLayout()
        
        # オーナー選択
        owner_select_layout = QHBoxLayout()
        self.owner_combo = QComboBox()
        self.owner_combo.setEditable(False)
        self.load_owner_combo()
        self.add_owner_button = QPushButton("オーナー追加")
        self.add_owner_button.clicked.connect(self.add_owner_to_unit)
        owner_select_layout.addWidget(QLabel("オーナー選択:"))
        owner_select_layout.addWidget(self.owner_combo, 1)
        owner_select_layout.addWidget(self.add_owner_button)
        
        # オーナー一覧テーブル
        self.owner_table = QTableWidget()
        self.owner_table.setColumnCount(5)
        self.owner_table.setHorizontalHeaderLabels([
            "オーナー名", "所有比率(%)", "主要", "連絡先", "操作"
        ])
        self.owner_table.setMaximumHeight(120)
        
        owner_layout.addLayout(owner_select_layout)
        owner_layout.addWidget(self.owner_table)
        owner_group.setLayout(owner_layout)
        
        # ボタン
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("登録")
        self.add_button.clicked.connect(self.add_unit)
        self.update_button = QPushButton("更新")
        self.update_button.clicked.connect(self.update_unit)
        self.clear_button = QPushButton("クリア")
        self.clear_button.clicked.connect(self.clear_form)
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        
        # テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "物件名", "部屋番号", "階数", "面積", "使用制限", "設備", "備考"
        ])
        self.table.cellClicked.connect(self.on_unit_selected)
        
        layout.addWidget(form_group)
        layout.addWidget(owner_group)
        layout.addLayout(button_layout)
        layout.addWidget(QLabel("部屋一覧"))
        layout.addWidget(self.table)
        
        widget.setLayout(layout)
        self.load_units()
        return widget
    
    def create_upload_tab(self):
        """募集図面アップロードタブを作成"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 物件選択
        form_group = QGroupBox("物件選択")
        form_layout = QFormLayout()
        
        self.upload_property_combo = QComboBox()
        self.load_upload_property_combo()
        
        form_layout.addRow("物件:", self.upload_property_combo)
        form_group.setLayout(form_layout)
        
        # 図面アップロード
        upload_group = QGroupBox("募集図面アップロード")
        upload_layout = QFormLayout()
        
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        
        upload_layout.addRow("図面ファイル:", self.file_path_edit)
        upload_group.setLayout(upload_layout)
        
        # ボタン
        button_layout = QHBoxLayout()
        self.browse_button = QPushButton("ファイル選択")
        self.browse_button.clicked.connect(self.browse_file)
        self.upload_button = QPushButton("アップロード・OCR処理")
        self.upload_button.clicked.connect(self.upload_and_process)
        self.clear_upload_button = QPushButton("クリア")
        self.clear_upload_button.clicked.connect(self.clear_upload_form)
        
        button_layout.addWidget(self.browse_button)
        button_layout.addWidget(self.upload_button)
        button_layout.addWidget(self.clear_upload_button)
        button_layout.addStretch()
        
        # 処理結果表示
        self.result_text = QTextEdit()
        self.result_text.setMaximumHeight(200)
        self.result_text.setPlaceholderText("OCR処理結果がここに表示されます")
        
        # 抽出された部屋一覧
        self.extracted_rooms_table = QTableWidget()
        self.extracted_rooms_table.setColumnCount(7)
        self.extracted_rooms_table.setHorizontalHeaderLabels([
            "部屋番号", "階数", "面積", "賃料", "管理費", "敷金", "礼金"
        ])
        
        layout.addWidget(form_group)
        layout.addWidget(upload_group)
        layout.addLayout(button_layout)
        layout.addWidget(QLabel("処理結果"))
        layout.addWidget(self.result_text)
        layout.addWidget(QLabel("抽出された部屋一覧"))
        layout.addWidget(self.extracted_rooms_table)
        
        widget.setLayout(layout)
        return widget
    
    def load_property_combo(self):
        """物件コンボボックスを読み込み"""
        self.property_combo.clear()
        self.property_combo.addItem("物件を選択", None)
        
        properties = Property.get_all()
        for property_obj in properties:
            self.property_combo.addItem(property_obj['name'], property_obj['id'])

    def load_upload_property_combo(self):
        """アップロード用物件コンボボックスを読み込み"""
        self.upload_property_combo.clear()
        self.upload_property_combo.addItem("物件を選択", None)
        
        properties = Property.get_all()
        for property_obj in properties:
            self.upload_property_combo.addItem(property_obj['name'], property_obj['id'])
    
    def add_unit(self):
        """部屋を登録"""
        property_id = self.property_combo.currentData()
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
                floor=self.floor_spin.value(),
                area=self.area_spin.value(),
                use_restrictions=self.use_restrictions_edit.toPlainText().strip() or None,
                power_capacity=self.power_capacity_spin.value() if self.power_capacity_spin.value() > 0 else None,
                pet_allowed=self.pet_allowed_check.isChecked(),
                midnight_allowed=self.midnight_allowed_check.isChecked(),
                notes=self.notes_edit.toPlainText().strip() or None
            )
            
            QMessageBox.information(self, "成功", "部屋を登録しました。")
            self.clear_form()
            self.load_units()
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"部屋の登録に失敗しました: {str(e)}")
    
    def clear_form(self):
        """フォームをクリア"""
        self.property_combo.setCurrentIndex(0)
        self.room_number_edit.clear()
        self.floor_spin.setValue(1)
        self.area_spin.setValue(1)
        self.use_restrictions_edit.clear()
        self.power_capacity_spin.setValue(0)
        self.pet_allowed_check.setChecked(False)
        self.midnight_allowed_check.setChecked(False)
        self.notes_edit.clear()
    
    def load_units(self):
        """部屋一覧をテーブルに読み込み"""
        try:
            units = Unit.get_all()
            
            self.table.setRowCount(len(units))
            for i, unit in enumerate(units):
                self.table.setItem(i, 0, QTableWidgetItem(str(unit['id'])))
                
                # 物件名を取得
                property_obj = Property.get_by_id(unit['property_id'])
                property_name = property_obj['name'] if property_obj else ""
                self.table.setItem(i, 1, QTableWidgetItem(property_name))
                
                self.table.setItem(i, 2, QTableWidgetItem(unit['room_number'] or ""))
                self.table.setItem(i, 3, QTableWidgetItem(str(unit['floor']) if unit['floor'] else ""))
                self.table.setItem(i, 4, QTableWidgetItem(f"{unit['area']}㎡" if unit['area'] else ""))
                self.table.setItem(i, 5, QTableWidgetItem(unit['use_restrictions'] or ""))
                
                # 設備情報
                equipment = []
                if unit['power_capacity']:
                    equipment.append(f"電力{unit['power_capacity']}kW")
                if unit['pet_allowed']:
                    equipment.append("ペット可")
                if unit['midnight_allowed']:
                    equipment.append("深夜営業可")
                
                self.table.setItem(i, 6, QTableWidgetItem(", ".join(equipment)))
                self.table.setItem(i, 7, QTableWidgetItem(unit['notes'] or ""))
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"部屋一覧の読み込み中にエラーが発生しました: {str(e)}")
    
    def load_owner_combo(self):
        """オーナーコンボボックスを読み込み"""
        try:
            owners = Customer.get_all()
            owner_customers = [c for c in owners if c.get('type') == 'owner']
            
            self.owner_combo.clear()
            self.owner_combo.addItem("新規オーナーを登録", None)
            for owner in owner_customers:
                self.owner_combo.addItem(f"{owner['name']} ({owner['id']})", owner['id'])
        except Exception as e:
            print(f"オーナー一覧読み込みエラー: {str(e)}")
    
    def add_owner_to_unit(self):
        """部屋にオーナーを追加（区分所有対応）"""
        if not self.current_unit_id:
            QMessageBox.warning(self, "警告", "部屋を選択してください")
            return
        
        owner_id = self.owner_combo.currentData()
        if not owner_id:
            # 新規オーナー登録
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
                    self.load_owner_combo()
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
            Unit.add_owner(self.current_unit_id, owner_id, ratio, is_primary=(ratio >= 50))
            self.load_unit_owners()
            QMessageBox.information(self, "成功", "オーナーを追加しました")
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"オーナー追加中にエラーが発生しました: {str(e)}")
    
    def load_unit_owners(self):
        """部屋のオーナー一覧を読み込み"""
        if not self.current_unit_id:
            self.owner_table.setRowCount(0)
            return
        
        try:
            owners = Unit.get_owners(self.current_unit_id)
            self.owner_table.setRowCount(len(owners))
            
            for row, owner in enumerate(owners):
                self.owner_table.setItem(row, 0, QTableWidgetItem(owner.get('owner_name', '')))
                self.owner_table.setItem(row, 1, QTableWidgetItem(f"{owner.get('ownership_ratio', 0):.1f}"))
                self.owner_table.setItem(row, 2, QTableWidgetItem("主要" if owner.get('is_primary') else ""))
                contact = f"{owner.get('phone', '')} / {owner.get('email', '')}"
                self.owner_table.setItem(row, 3, QTableWidgetItem(contact))
                
                # 削除ボタン
                delete_button = QPushButton("削除")
                delete_button.clicked.connect(lambda checked, oid=owner['owner_id']: self.remove_owner_from_unit(oid))
                self.owner_table.setCellWidget(row, 4, delete_button)
                
        except Exception as e:
            print(f"オーナー一覧読み込みエラー: {str(e)}")
    
    def remove_owner_from_unit(self, owner_id):
        """部屋からオーナーを削除"""
        if not self.current_unit_id:
            return
        
        reply = QMessageBox.question(self, "確認", "このオーナーを部屋から削除しますか？")
        if reply == QMessageBox.StandardButton.Yes:
            try:
                Unit.remove_owner(self.current_unit_id, owner_id)
                self.load_unit_owners()
                QMessageBox.information(self, "成功", "オーナーを削除しました")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"オーナー削除中にエラーが発生しました: {str(e)}")
    
    def on_unit_selected(self, row, column):
        """部屋が選択されたときの処理"""
        try:
            unit_id = int(self.table.item(row, 0).text())
            self.current_unit_id = unit_id
            
            # 部屋情報をフォームに読み込み
            unit = Unit.get_by_id(unit_id)
            if unit:
                # 物件選択
                property_index = self.property_combo.findData(unit['property_id'])
                if property_index >= 0:
                    self.property_combo.setCurrentIndex(property_index)
                
                # 基本情報
                self.room_number_edit.setText(unit.get('room_number', ''))
                self.floor_spin.setValue(int(unit.get('floor', 0)) if unit.get('floor') else 0)
                self.area_spin.setValue(int(unit.get('area', 0)) if unit.get('area') else 0)
                
                # 使用制限
                self.use_restrictions_edit.setPlainText(unit.get('use_restrictions', ''))
                
                # 設備・条件
                power = unit.get('power_capacity', '')
                if power and power.replace('kW', '').strip().isdigit():
                    self.power_capacity_spin.setValue(int(power.replace('kW', '').strip()))
                else:
                    self.power_capacity_spin.setValue(0)
                
                self.pet_allowed_check.setChecked(bool(unit.get('pet_allowed', False)))
                self.midnight_allowed_check.setChecked(bool(unit.get('midnight_allowed', False)))
                
                # 備考
                self.notes_edit.setPlainText(unit.get('notes', ''))
                
                # オーナー情報を読み込み
                self.load_unit_owners()
                
        except Exception as e:
            print(f"部屋選択エラー: {str(e)}")
    
    def update_unit(self):
        """部屋情報を更新"""
        if not self.current_unit_id:
            QMessageBox.warning(self, "警告", "更新する部屋を選択してください")
            return
        
        # 既存のadd_unitメソッドのロジックを流用して更新処理を実装
        QMessageBox.information(self, "情報", "更新機能は実装準備中です")
    
    def browse_file(self):
        """ファイル選択"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "募集図面ファイルを選択", "", 
            "画像ファイル (*.png *.jpg *.jpeg *.bmp *.tiff);;PDFファイル (*.pdf)"
        )
        if file_path:
            self.file_path_edit.setText(file_path)
    
    def upload_and_process(self):
        """募集図面をアップロードしてOCR処理"""
        property_id = self.upload_property_combo.currentData()
        file_path = self.file_path_edit.text().strip()
        
        if not property_id:
            QMessageBox.warning(self, "警告", "物件を選択してください。")
            return
        
        if not file_path:
            QMessageBox.warning(self, "警告", "ファイルを選択してください。")
            return
        
        try:
            # OCR処理を非同期で実行
            self.worker = FloorplanOCRWorker(file_path)
            self.worker.finished.connect(self.on_ocr_finished)
            self.worker.error.connect(self.on_ocr_error)
            self.worker.start()
            
            self.upload_button.setEnabled(False)
            self.result_text.setText("OCR処理を実行中...")
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"アップロードに失敗しました: {str(e)}")
    
    def on_ocr_finished(self, rooms: list):
        """OCR処理完了時の処理"""
        self.upload_button.setEnabled(True)
        
        try:
            # 結果を表示
            result_text = f"OCR処理完了\n{len(rooms)}件の部屋情報を抽出しました\n\n"
            
            for room in rooms:
                result_text += f"部屋番号: {room['room_number']}\n"
                if room['area']:
                    result_text += f"  面積: {room['area']}㎡\n"
                if room['rent']:
                    result_text += f"  賃料: {room['rent']:,}円\n"
                if room['management_fee']:
                    result_text += f"  管理費: {room['management_fee']:,}円\n"
                if room['deposit']:
                    result_text += f"  敷金: {room['deposit']:,}円\n"
                if room['key_money']:
                    result_text += f"  礼金: {room['key_money']:,}円\n"
                result_text += "\n"
            
            self.result_text.setText(result_text)
            
            # 抽出された部屋一覧をテーブルに表示
            self.extracted_rooms_table.setRowCount(len(rooms))
            for i, room in enumerate(rooms):
                self.extracted_rooms_table.setItem(i, 0, QTableWidgetItem(room['room_number']))
                self.extracted_rooms_table.setItem(i, 1, QTableWidgetItem(str(room['floor']) if room['floor'] else ""))
                self.extracted_rooms_table.setItem(i, 2, QTableWidgetItem(f"{room['area']}㎡" if room['area'] else ""))
                self.extracted_rooms_table.setItem(i, 3, QTableWidgetItem(f"{room['rent']:,}円" if room['rent'] else ""))
                self.extracted_rooms_table.setItem(i, 4, QTableWidgetItem(f"{room['management_fee']:,}円" if room['management_fee'] else ""))
                self.extracted_rooms_table.setItem(i, 5, QTableWidgetItem(f"{room['deposit']:,}円" if room['deposit'] else ""))
                self.extracted_rooms_table.setItem(i, 6, QTableWidgetItem(f"{room['key_money']:,}円" if room['key_money'] else ""))
            
            # 自動登録の確認
            if rooms:
                reply = QMessageBox.question(
                    self, "確認", 
                    f"{len(rooms)}件の部屋情報を自動登録しますか？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.auto_register_rooms(rooms)
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"OCR結果の処理に失敗しました: {str(e)}")
    
    def on_ocr_error(self, error: str):
        """OCR処理エラー時の処理"""
        self.upload_button.setEnabled(True)
        self.result_text.setText(f"OCR処理エラー: {error}")
        QMessageBox.critical(self, "エラー", f"OCR処理中にエラーが発生しました: {error}")
    
    def auto_register_rooms(self, rooms: list):
        """抽出された部屋情報を自動登録"""
        try:
            property_id = self.upload_property_combo.currentData()
            registered_count = 0
            
            for room in rooms:
                try:
                    Unit.create(
                        property_id=property_id,
                        room_number=room['room_number'],
                        floor=room['floor'] or 1,
                        area=room['area'] or 1,
                        use_restrictions=None,
                        power_capacity=None,
                        pet_allowed=False,
                        midnight_allowed=False,
                        notes=f"OCR自動抽出: 賃料{room['rent']:,}円" if room['rent'] else "OCR自動抽出"
                    )
                    registered_count += 1
                    
                except Exception as e:
                    print(f"部屋 {room['room_number']} の登録に失敗: {e}")
                    continue
            
            QMessageBox.information(self, "完了", f"{registered_count}件の部屋を登録しました。")
            
            # 手動入力タブのテーブルを更新
            self.load_units()
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"自動登録に失敗しました: {str(e)}")
    
    def clear_upload_form(self):
        """アップロードフォームをクリア"""
        self.load_upload_property_combo()  # 物件リストを再読み込み
        self.upload_property_combo.setCurrentIndex(0)
        self.file_path_edit.clear()
        self.result_text.clear()
        self.extracted_rooms_table.setRowCount(0) 