from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QLineEdit, 
                             QTextEdit, QMessageBox, QGroupBox, QFormLayout, 
                             QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QDialog, QDialogButtonBox)
from PyQt6.QtCore import Qt, QDate
import sys
import os

# プロジェクトルートをPythonパスに追加（tabsフォルダ内のモジュールがルートのモジュールにアクセスできるように）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Task, TenantContract, Customer, Unit, Property

# マウスホイール無効化SpinBox
class NoWheelSpinBox(QSpinBox):
    """マウスホイールによる値変更を無効化したSpinBox"""
    def wheelEvent(self, event):
        event.ignore()

class NoWheelDoubleSpinBox(QDoubleSpinBox):
    """マウスホイールによる値変更を無効化したDoubleSpinBox"""
    def wheelEvent(self, event):
        event.ignore()


class TaskTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_tasks()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 入力フォーム
        form_group = QGroupBox("タスク登録")
        form_layout = QFormLayout()
        
        self.contract_combo = QComboBox()
        self.task_type_combo = QComboBox()
        self.task_type_combo.addItems(["更新案内", "請求", "通知", "その他"])
        self.title_edit = QLineEdit()
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.due_date_edit = QDateEdit()
        self.due_date_edit.setDate(QDate.currentDate())
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["high", "normal", "low"])
        self.assigned_to_edit = QLineEdit()
        
        form_layout.addRow("契約:", self.contract_combo)
        form_layout.addRow("タスク種別:", self.task_type_combo)
        form_layout.addRow("タイトル:", self.title_edit)
        form_layout.addRow("説明:", self.description_edit)
        form_layout.addRow("期限:", self.due_date_edit)
        form_layout.addRow("優先度:", self.priority_combo)
        form_layout.addRow("担当者:", self.assigned_to_edit)
        
        form_group.setLayout(form_layout)
        
        # ボタン
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("💾 登録")
        self.add_button.clicked.connect(self.add_task)
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
                min-height: 32px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)

        self.clear_button = QPushButton("クリア")
        self.clear_button.clicked.connect(self.clear_form)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
                min-height: 32px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)

        self.export_button = QPushButton("📊 CSV出力")
        self.export_button.clicked.connect(self.export_to_csv)
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
                min-height: 32px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()
        
        # テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "顧客名", "物件名", "部屋番号", "タスク種別", 
            "タイトル", "期限", "優先度", "担当者", "状態"
        ])
        
        # テーブルの列幅を調整
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(form_group)
        layout.addLayout(button_layout)
        layout.addWidget(QLabel("タスク一覧"))
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        self.load_contracts()
        
    def load_contracts(self):
        """契約一覧をコンボボックスに読み込み"""
        self.contract_combo.clear()
        self.contract_combo.addItem("契約を選択", None)
        
        contracts = TenantContract.get_all()
        for contract in contracts:
            display_text = f"{contract['customer_name']} - {contract['property_name']} {contract['unit_number']}"
            self.contract_combo.addItem(display_text, contract['id'])
    
    def load_tasks(self):
        """タスク一覧をテーブルに読み込み"""
        self.table.setRowCount(0)
        
        tasks = Task.get_pending_tasks()
        self.table.setRowCount(len(tasks))
        
        for row, task in enumerate(tasks):
            self.table.setItem(row, 0, QTableWidgetItem(str(task['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(task['customer_name'] or ''))
            self.table.setItem(row, 2, QTableWidgetItem(task['property_name'] or ''))
            self.table.setItem(row, 3, QTableWidgetItem(task['unit_number'] or ''))
            self.table.setItem(row, 4, QTableWidgetItem(task['task_type']))
            self.table.setItem(row, 5, QTableWidgetItem(task['title']))
            self.table.setItem(row, 6, QTableWidgetItem(task['due_date'] or ''))
            self.table.setItem(row, 7, QTableWidgetItem(task['priority']))
            self.table.setItem(row, 8, QTableWidgetItem(task['assigned_to'] or ''))
            self.table.setItem(row, 9, QTableWidgetItem(task['status']))
            
            # 期限が過ぎているタスクは赤色で表示
            if task['due_date'] and task['due_date'] < QDate.currentDate().toString("yyyy-MM-dd"):
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(Qt.GlobalColor.red)
    
    def add_task(self):
        """タスクを登録"""
        contract_id = self.contract_combo.currentData()
        if not contract_id:
            QMessageBox.warning(self, "警告", "契約を選択してください。")
            return
        
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "警告", "タイトルを入力してください。")
            return
        
        try:
            Task.create(
                contract_id=contract_id,
                task_type=self.task_type_combo.currentText(),
                title=title,
                description=self.description_edit.toPlainText().strip() or None,
                due_date=self.due_date_edit.date().toString("yyyy-MM-dd"),
                priority=self.priority_combo.currentText(),
                assigned_to=self.assigned_to_edit.text().strip() or None
            )
            
            QMessageBox.information(self, "成功", "タスクを登録しました。")
            self.clear_form()
            self.load_tasks()
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"タスクの登録に失敗しました: {str(e)}")
    
    def clear_form(self):
        """フォームをクリア"""
        self.contract_combo.setCurrentIndex(0)
        self.task_type_combo.setCurrentIndex(0)
        self.title_edit.clear()
        self.description_edit.clear()
        self.due_date_edit.setDate(QDate.currentDate())
        self.priority_combo.setCurrentIndex(1)  # normal
        self.assigned_to_edit.clear()

    def export_to_csv(self):
        """タスク一覧をCSV出力"""
        try:
            import csv
            from PyQt6.QtWidgets import QFileDialog

            file_path, _ = QFileDialog.getSaveFileName(
                self, "CSVファイルの保存", "タスク一覧.csv", "CSV Files (*.csv)"
            )

            if file_path:
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                    writer = csv.writer(csvfile)

                    # ヘッダー
                    headers = []
                    for col in range(self.table.columnCount()):
                        headers.append(self.table.horizontalHeaderItem(col).text())
                    writer.writerow(headers)

                    # データ
                    for row in range(self.table.rowCount()):
                        row_data = []
                        for col in range(self.table.columnCount()):
                            item = self.table.item(row, col)
                            row_data.append(item.text() if item else "")
                        writer.writerow(row_data)

                from utils import MessageHelper
                MessageHelper.show_success(self, f"CSVファイルを出力しました:\n{file_path}")

        except Exception as e:
            from utils import MessageHelper
            MessageHelper.show_error(self, f"CSV出力中にエラーが発生しました: {str(e)}")