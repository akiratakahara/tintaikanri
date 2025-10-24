"""
タスク管理タブ - 基本版
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QLineEdit, 
                             QComboBox, QTextEdit, QDateEdit, QFormLayout, 
                             QGroupBox, QMessageBox, QHeaderView, QScrollArea, QSizePolicy)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from utils import MessageHelper, DateHelper, FormatHelper
from ui.ui_styles import ModernStyles, ButtonHelper

class TaskTabBasic(QWidget):
    """タスク管理タブ - 基本版"""
    
    task_updated = pyqtSignal()  # タスク更新シグナル
    
    def __init__(self):
        super().__init__()
        self.tasks = []  # 基本的なタスクリスト
        self.init_ui()
        self.load_tasks()
        
    def init_ui(self):
        # モダンスタイルを適用
        self.setStyleSheet(ModernStyles.get_all_styles())
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # ヘッダー
        header_widget = self.create_header()
        layout.addWidget(header_widget)
        
        # 入力フォーム
        form_group = QGroupBox("📝 新しいタスクを作成")
        form_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 16px;
                font-weight: 600;
                color: #1f2937;
                padding-top: 20px;
                margin-top: 16px;
            }}
        """)
        form_layout = QFormLayout()
        form_layout.setSpacing(16)
        
        self.task_type_combo = QComboBox()
        self.task_type_combo.addItems(["更新案内", "請求", "通知", "修繕", "その他"])
        self.task_type_combo.setMaximumWidth(150)
        
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("タスクのタイトルを入力")
        self.title_edit.setMaximumWidth(400)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setMaximumWidth(500)
        self.description_edit.setPlaceholderText("詳細説明（任意）")
        
        self.due_date_edit = QDateEdit()
        self.due_date_edit.setDate(QDate.currentDate())
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setMinimumDate(QDate.currentDate())  # 最小値を今日に設定
        self.due_date_edit.setMaximumWidth(150)
        
        # 優先度をチップ形式に変更
        priority_widget = QWidget()
        priority_layout = QHBoxLayout(priority_widget)
        priority_layout.setContentsMargins(0, 0, 0, 0)
        priority_layout.setSpacing(8)
        
        self.priority_buttons = {}
        priorities = [("低", "success"), ("中", "warning"), ("高", "danger")]
        
        for text, color_type in priorities:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setChecked(text == "中")  # デフォルト：中
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #f3f4f6;
                    border: 1px solid #d1d5db;
                    border-radius: 16px;
                    padding: 6px 12px;
                    font-size: 12px;
                    min-height: 24px;
                }}
                QPushButton:checked {{
                    background-color: {'#10b981' if color_type == 'success' else '#f59e0b' if color_type == 'warning' else '#ef4444'};
                    color: white;
                    border-color: {'#10b981' if color_type == 'success' else '#f59e0b' if color_type == 'warning' else '#ef4444'};
                }}
            """)
            self.priority_buttons[text] = btn
            priority_layout.addWidget(btn)
        
        # ボタングループ
        from PyQt6.QtWidgets import QButtonGroup
        self.priority_group = QButtonGroup()
        for btn in self.priority_buttons.values():
            self.priority_group.addButton(btn)
        self.priority_group.setExclusive(True)
        
        self.assigned_to_edit = QLineEdit()
        self.assigned_to_edit.setPlaceholderText("担当者名（任意）")
        self.assigned_to_edit.setMaximumWidth(200)
        
        form_layout.addRow("タスク種別:", self.task_type_combo)
        form_layout.addRow("タイトル:", self.title_edit)
        form_layout.addRow("説明:", self.description_edit)
        form_layout.addRow("期限:", self.due_date_edit)
        form_layout.addRow("優先度:", priority_widget)
        form_layout.addRow("担当者:", self.assigned_to_edit)
        
        form_group.setLayout(form_layout)
        form_group.setMaximumWidth(600)  # フォームグループの幅制限
        
        # ボタン
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("✅ 登録")
        self.add_button.clicked.connect(self.add_task)
        ButtonHelper.set_success(self.add_button)
        
        self.edit_button = QPushButton("✏️ 編集")
        self.edit_button.clicked.connect(self.edit_task)
        self.edit_button.setEnabled(False)
        
        self.complete_button = QPushButton("✔️ 完了")
        self.complete_button.clicked.connect(self.complete_task)
        self.complete_button.setEnabled(False)
        ButtonHelper.set_primary(self.complete_button)
        
        self.delete_button = QPushButton("🗑️ 削除")
        self.delete_button.clicked.connect(self.delete_task)
        self.delete_button.setEnabled(False)
        ButtonHelper.set_danger(self.delete_button)
        
        self.clear_button = QPushButton("🔄 クリア")
        self.clear_button.clicked.connect(self.clear_form)

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
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.complete_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()
        
        # フィルター（2つに整理）
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("状態:"))
        
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems(["全て", "未完了", "完了"])
        self.status_filter_combo.currentTextChanged.connect(self.apply_filters)
        self.status_filter_combo.setMaximumWidth(120)
        
        filter_layout.addWidget(self.status_filter_combo)
        filter_layout.addWidget(QLabel("優先度:"))
        
        self.priority_filter_combo = QComboBox()
        self.priority_filter_combo.addItems(["全て", "低", "中", "高"])
        self.priority_filter_combo.currentTextChanged.connect(self.apply_filters)
        self.priority_filter_combo.setMaximumWidth(120)
        
        filter_layout.addWidget(self.priority_filter_combo)
        filter_layout.addStretch()
        
        # テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "タスク種別", "タイトル", "期限", "優先度", "担当者", "状態"
        ])
        
        # テーブルの設定
        self.table.setColumnHidden(0, True)  # IDを非表示
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.itemDoubleClicked.connect(self.edit_task)
        
        # テーブルの列幅調整（Stretch対応）
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table.verticalHeader().setDefaultSectionSize(40)
        
        # メインコンテンツウィジェット
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(16, 16, 16, 16)
        
        # コンテンツを順序よく配置
        main_layout.addWidget(form_group)
        main_layout.addLayout(button_layout)
        main_layout.addLayout(filter_layout)
        
        # タスク一覧ラベル
        list_label = QLabel("タスク一覧")
        list_label.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; margin: 8px 0; }")
        main_layout.addWidget(list_label)
        
        # テーブルを固定高さで設定（スクロール可能）
        self.table.setMinimumHeight(300)  # 最小高さを設定
        self.table.setMaximumHeight(600)  # 最大高さを制限
        
        # テーブルをストレッチ設定
        from ui.ui_helpers import stretch_table
        stretch_table(self.table)
        
        main_layout.addWidget(self.table)
        
        # 全体を単一スクロールページとして設定
        from ui.ui_helpers import make_scroll_page
        scroll_page = make_scroll_page(main_container)
        
        # ページレイアウト設定
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(scroll_page)
    
    def create_header(self):
        """ヘッダーウィジェットを作成"""
        header = QWidget()
        header.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                          stop: 0 #10b981,
                                          stop: 1 #059669);
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 16, 20, 16)
        
        # タイトル部分
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setSpacing(4)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("📋 タスク管理")
        title_label.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
        
        subtitle_label = QLabel("効率的なタスクトラッキングとスケジュール管理")
        subtitle_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 12px;")
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        
        layout.addWidget(title_container)
        layout.addStretch()
        
        # ステータス表示
        stats_container = QWidget()
        stats_layout = QVBoxLayout(stats_container)
        stats_layout.setSpacing(4)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        
        self.task_count_label = QLabel("総タスク: 0件")
        self.task_count_label.setStyleSheet("color: rgba(255, 255, 255, 0.9); font-size: 11px; text-align: right;")
        self.task_count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.pending_count_label = QLabel("未完了: 0件")
        self.pending_count_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 10px; text-align: right;")
        self.pending_count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        stats_layout.addWidget(self.task_count_label)
        stats_layout.addWidget(self.pending_count_label)
        
        layout.addWidget(stats_container)
        
        return header
    
    def update_header_stats(self):
        """ヘッダーの統計を更新"""
        total_tasks = len(self.tasks)
        pending_tasks = len([task for task in self.tasks if task.get('status') != '完了'])
        
        self.task_count_label.setText(f"総タスク: {total_tasks}件")
        self.pending_count_label.setText(f"未完了: {pending_tasks}件")
    
    def load_tasks(self):
        """タスク一覧をテーブルに読み込み"""
        try:
            from models import Task
            # 全てのタスクを取得（完了・未完了両方）
            db_tasks = Task.get_all_tasks()
            
            # データベースからの読み込みが成功した場合
            self.tasks = []
            for task in db_tasks:
                # statusをcompletedから完了に変換
                status = '完了' if task.get('status') == 'completed' else '未完了'
                self.tasks.append({
                    'id': task.get('id', len(self.tasks) + 1),
                    'task_type': task.get('task_type', ''),
                    'title': task.get('title', ''),
                    'description': task.get('description', ''),
                    'due_date': task.get('due_date', ''),
                    'priority': task.get('priority', '中'),
                    'assigned_to': task.get('assigned_to', ''),
                    'status': status
                })
        except Exception as e:
            # データベースに接続できない場合
            if not hasattr(self, 'dummy_loaded') or not self.dummy_loaded:
                # 既存のタスクがあれば保持、なければダミーデータ
                if not hasattr(self, 'tasks') or len(self.tasks) == 0:
                    self.tasks = [
                        {
                            'id': 1,
                            'task_type': '更新案内',
                            'title': 'サンプル更新案内タスク',
                            'description': '契約更新の案内を送付',
                            'due_date': '2024-12-31',
                            'priority': '高',
                            'assigned_to': '担当者A',
                            'status': '未完了'
                        }
                    ]
                self.dummy_loaded = True
                print(f"タスクDB接続エラー（メモリデータ使用）: {e}")
        
        self.apply_filters()
        self.update_header_stats()
    
    def apply_filters(self):
        """フィルターを適用してテーブルを更新"""
        status_filter = self.status_filter_combo.currentText()
        priority_filter = self.priority_filter_combo.currentText()
        
        # フィルタリング
        filtered_tasks = []
        for task in self.tasks:
            # 状態フィルター
            if status_filter != "全て" and task['status'] != status_filter:
                continue
            
            # 優先度フィルター
            if priority_filter != "全て" and task['priority'] != priority_filter:
                continue
            
            filtered_tasks.append(task)
        
        # テーブル更新
        self.table.setRowCount(len(filtered_tasks))
        
        for row, task in enumerate(filtered_tasks):
            self.table.setItem(row, 0, QTableWidgetItem(str(task['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(task['task_type']))
            self.table.setItem(row, 2, QTableWidgetItem(task['title']))
            self.table.setItem(row, 3, QTableWidgetItem(task['due_date']))
            self.table.setItem(row, 4, QTableWidgetItem(task['priority']))
            self.table.setItem(row, 5, QTableWidgetItem(task['assigned_to']))
            self.table.setItem(row, 6, QTableWidgetItem(task['status']))
            
            # 行の色分け
            if task['status'] == '完了':
                # 完了済みは薄いグレー
                from PyQt6.QtGui import QColor
                for col in range(7):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(QColor("#F0F0F0"))
            elif task['priority'] == '高':
                # 優先度高は薄い赤
                from PyQt6.QtGui import QColor
                for col in range(7):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(QColor("#FFEBEE"))
            elif task['due_date'] and task['due_date'] < QDate.currentDate().toString("yyyy-MM-dd"):
                # 期限過ぎは赤
                from PyQt6.QtGui import QColor
                for col in range(7):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(QColor("#FFCDD2"))
    
    def on_selection_changed(self):
        """選択変更時の処理"""
        has_selection = len(self.table.selectedItems()) > 0
        self.edit_button.setEnabled(has_selection)
        self.complete_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        
        if not has_selection:
            # 選択がない場合は新規作成モード
            self.reset_add_mode()
    
    def get_selected_task_id(self):
        """選択されたタスクIDを取得"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            id_item = self.table.item(current_row, 0)
            if id_item:
                return int(id_item.text())
        return None
    
    def add_task(self):
        """タスクを追加"""
        title = self.title_edit.text().strip()
        if not title:
            MessageHelper.show_warning(self, "タイトルを入力してください")
            return
        
        task_data = {
            'id': max([task['id'] for task in self.tasks], default=0) + 1,
            'task_type': self.task_type_combo.currentText(),
            'title': title,
            'description': self.description_edit.toPlainText().strip(),
            'due_date': self.due_date_edit.date().toString("yyyy-MM-dd"),
            'priority': self.get_selected_priority(),
            'assigned_to': self.assigned_to_edit.text().strip(),
            'status': '未完了'
        }
        
        try:
            # データベースに保存を試行
            from models import Task
            task_id = Task.create(
                contract_id=None,  # 基本版では契約IDはなし
                task_type=task_data['task_type'],
                title=task_data['title'],
                description=task_data['description'] if task_data['description'] else None,
                due_date=task_data['due_date'],
                priority=task_data['priority'],
                assigned_to=task_data['assigned_to'] if task_data['assigned_to'] else None
            )
            task_data['id'] = task_id  # DBから返されたIDを設定
        except Exception as e:
            print(f"DB保存エラー（メモリのみ保存）: {e}")
        
        # メモリに追加
        self.tasks.append(task_data)
        MessageHelper.show_success(self, "タスクを登録しました")
        self.clear_form()
        # 表示を更新
        self.apply_filters()
        self.update_header_stats()
        self.task_updated.emit()  # タスク更新シグナル発信
    
    def edit_task(self):
        """タスクを編集"""
        task_id = self.get_selected_task_id()
        if not task_id:
            return
        
        # 対象タスクを検索
        task = next((t for t in self.tasks if t['id'] == task_id), None)
        if not task:
            return
        
        # フォームに読み込み
        type_index = self.task_type_combo.findText(task['task_type'])
        if type_index >= 0:
            self.task_type_combo.setCurrentIndex(type_index)
        
        self.title_edit.setText(task['title'])
        self.description_edit.setPlainText(task['description'])
        
        if task['due_date']:
            date = QDate.fromString(task['due_date'], "yyyy-MM-dd")
            if date.isValid():
                self.due_date_edit.setDate(date)
        
        # 優先度ボタンを設定
        priority = task.get('priority', '中')
        for text, btn in self.priority_buttons.items():
            btn.setChecked(text == priority)
        
        self.assigned_to_edit.setText(task['assigned_to'])
        
        # 編集モードに変更
        self.add_button.setText("更新")
        self.add_button.clicked.disconnect()
        self.add_button.clicked.connect(lambda: self.update_task(task_id))
    
    def update_task(self, task_id):
        """タスクを更新"""
        title = self.title_edit.text().strip()
        if not title:
            MessageHelper.show_warning(self, "タイトルを入力してください")
            return
        
        # データベースを更新
        try:
            from models import Task
            Task.update(
                task_id,
                task_type=self.task_type_combo.currentText(),
                title=title,
                description=self.description_edit.toPlainText().strip() or None,
                due_date=self.due_date_edit.date().toString("yyyy-MM-dd"),
                priority=self.get_selected_priority(),
                assigned_to=self.assigned_to_edit.text().strip() or None
            )
        except Exception as e:
            print(f"DB更新エラー: {e}")
        
        # メモリ上のデータも更新
        for task in self.tasks:
            if task['id'] == task_id:
                task['task_type'] = self.task_type_combo.currentText()
                task['title'] = title
                task['description'] = self.description_edit.toPlainText().strip()
                task['due_date'] = self.due_date_edit.date().toString("yyyy-MM-dd")
                task['priority'] = self.get_selected_priority()
                task['assigned_to'] = self.assigned_to_edit.text().strip()
                break
        
        MessageHelper.show_success(self, "タスクを更新しました")
        self.reset_add_mode()
        self.apply_filters()
        self.update_header_stats()
        self.task_updated.emit()  # タスク更新シグナル発信
    
    def complete_task(self):
        """タスクを完了にする"""
        task_id = self.get_selected_task_id()
        if not task_id:
            return
        
        # データベースを更新
        try:
            from models import Task
            Task.update(task_id, status='completed')
        except Exception as e:
            print(f"DB更新エラー: {e}")
        
        # メモリ上のデータも更新
        for task in self.tasks:
            if task['id'] == task_id:
                task['status'] = '完了'
                break
        
        MessageHelper.show_success(self, "タスクを完了しました")
        self.apply_filters()
        self.update_header_stats()
        self.task_updated.emit()  # タスク更新シグナル発信
    
    def delete_task(self):
        """タスクを削除"""
        task_id = self.get_selected_task_id()
        if not task_id:
            return
        
        task = next((t for t in self.tasks if t['id'] == task_id), None)
        if not task:
            return
        
        if MessageHelper.confirm_delete(self, f"タスク「{task['title']}」"):
            # データベースから削除
            try:
                from models import Task
                Task.delete(task_id)
            except Exception as e:
                print(f"DB削除エラー: {e}")
            
            # メモリからも削除
            self.tasks = [t for t in self.tasks if t['id'] != task_id]
            MessageHelper.show_success(self, "タスクを削除しました")
            self.apply_filters()
            self.update_header_stats()
            self.task_updated.emit()  # タスク更新シグナル発信
    
    def get_selected_priority(self):
        """選択されている優先度を取得"""
        for text, btn in self.priority_buttons.items():
            if btn.isChecked():
                return text
        return "中"  # デフォルト
    
    def clear_form(self):
        """フォームをクリア"""
        self.task_type_combo.setCurrentIndex(0)
        self.title_edit.clear()
        self.description_edit.clear()
        self.due_date_edit.setDate(QDate.currentDate())
        # 優先度を中にリセット
        for text, btn in self.priority_buttons.items():
            btn.setChecked(text == "中")
        self.assigned_to_edit.clear()
        self.reset_add_mode()
    
    def reset_add_mode(self):
        """追加モードに戻す"""
        self.add_mode = True
        self.current_task_id = None
        self.add_button.setText("✅ 登録")
        self.add_button.clicked.disconnect()
        self.add_button.clicked.connect(self.add_task)

        # 新規作成時は完了/削除ボタンを無効化
        self.edit_button.setEnabled(False)
        self.complete_button.setEnabled(False)
        self.delete_button.setEnabled(False)

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
                    writer.writerow([
                        "ID", "顧客名", "物件名", "部屋番号", "タスク種別",
                        "タイトル", "説明", "期限", "優先度", "担当者", "状態", "登録日"
                    ])

                    # データ（表示されている行から元データを取得）
                    for row in range(self.table.rowCount()):
                        if not self.table.isRowHidden(row):
                            # テーブルからIDを取得
                            id_item = self.table.item(row, 0)
                            if id_item:
                                task_id = int(id_item.text())
                                # 元データから該当レコードを検索
                                task = next((t for t in self.tasks if t.get('id') == task_id), None)
                                if task:
                                    row_data = [
                                        task.get('id', ''),
                                        task.get('customer_name', ''),
                                        task.get('property_name', ''),
                                        task.get('unit_number', ''),
                                        task.get('task_type', ''),
                                        task.get('title', ''),
                                        task.get('description', ''),
                                        task.get('due_date', ''),
                                        task.get('priority', ''),
                                        task.get('assigned_to', ''),
                                        task.get('status', ''),
                                        task.get('created_at', '')
                                    ]
                                    writer.writerow(row_data)

                MessageHelper.show_success(self, f"CSVファイルを出力しました:\n{file_path}")

        except Exception as e:
            MessageHelper.show_error(self, f"CSV出力中にエラーが発生しました: {str(e)}")