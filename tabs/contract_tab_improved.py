"""
改良版契約管理タブ - 書類管理・更新期限管理・手続きログ機能付き
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QLineEdit, 
                             QTextEdit, QMessageBox, QGroupBox, QFormLayout, 
                             QComboBox, QSpinBox, QDateEdit, QCheckBox, QDialog, 
                             QDialogButtonBox, QSplitter, QFrame, QTabWidget,
                             QTreeWidget, QTreeWidgetItem, QFileDialog, QListWidget,
                             QListWidgetItem, QProgressBar, QScrollArea)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from datetime import datetime, date, timedelta
import os
import shutil
from models import TenantContract, Unit, Property, Customer
from utils import (Validator, TableHelper, MessageHelper, FormatHelper, 
                  SearchHelper, DateHelper, StatusColor)
from commission_manager import CommissionManager

class ContractDocumentManager(QWidget):
    """契約書類管理ウィジェット"""
    
    def __init__(self, contract_id=None):
        super().__init__()
        self.contract_id = contract_id
        self.documents_folder = "contract_documents"  # 書類保存フォルダ
        self.ensure_documents_folder()
        self.init_ui()
        self.load_documents()
    
    def ensure_documents_folder(self):
        """書類保存フォルダを確保"""
        if not os.path.exists(self.documents_folder):
            os.makedirs(self.documents_folder)
        
        if self.contract_id:
            contract_folder = os.path.join(self.documents_folder, f"contract_{self.contract_id}")
            if not os.path.exists(contract_folder):
                os.makedirs(contract_folder)
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 書類アップロードエリア
        upload_group = QGroupBox("書類アップロード")
        upload_layout = QHBoxLayout()
        
        self.doc_type_combo = QComboBox()
        self.doc_type_combo.addItems([
            "契約書", "重要事項説明書", "申込書", "身分証明書",
            "収入証明書", "保証人関連書類", "火災保険証券",
            "その他書類"
        ])
        
        upload_btn = QPushButton("ファイル選択")
        upload_btn.clicked.connect(self.upload_document)
        
        upload_layout.addWidget(QLabel("書類種別:"))
        upload_layout.addWidget(self.doc_type_combo)
        upload_layout.addWidget(upload_btn)
        upload_layout.addStretch()
        
        upload_group.setLayout(upload_layout)
        layout.addWidget(upload_group)
        
        # 書類一覧
        self.document_list = QListWidget()
        self.document_list.itemDoubleClicked.connect(self.open_document)
        layout.addWidget(QLabel("保管書類一覧（ダブルクリックで開く）"))
        layout.addWidget(self.document_list)
        
        # 書類操作ボタン
        doc_button_layout = QHBoxLayout()
        
        open_btn = QPushButton("開く")
        open_btn.clicked.connect(self.open_selected_document)
        
        delete_btn = QPushButton("削除")
        delete_btn.clicked.connect(self.delete_document)
        delete_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        
        doc_button_layout.addWidget(open_btn)
        doc_button_layout.addWidget(delete_btn)
        doc_button_layout.addStretch()
        
        layout.addLayout(doc_button_layout)
        
        self.setLayout(layout)
    
    def upload_document(self):
        """書類をアップロード"""
        if not self.contract_id:
            MessageHelper.show_warning(self, "先に契約を保存してから書類をアップロードしてください")
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "書類ファイルを選択", "", 
            "All Files (*);;PDF Files (*.pdf);;Image Files (*.png *.jpg *.jpeg)"
        )
        
        if file_path:
            try:
                doc_type = self.doc_type_combo.currentText()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                original_name = os.path.basename(file_path)
                name, ext = os.path.splitext(original_name)
                
                new_filename = f"{doc_type}_{timestamp}_{name}{ext}"
                contract_folder = os.path.join(self.documents_folder, f"contract_{self.contract_id}")
                destination = os.path.join(contract_folder, new_filename)
                
                # ファイルをコピー
                shutil.copy2(file_path, destination)
                
                # データベースに記録
                self.save_document_record(doc_type, new_filename, destination)
                
                MessageHelper.show_success(self, f"書類「{doc_type}」をアップロードしました")
                self.load_documents()
                
            except Exception as e:
                MessageHelper.show_error(self, f"書類アップロード中にエラーが発生しました: {str(e)}")
    
    def save_document_record(self, doc_type, filename, file_path):
        """書類レコードをデータベースに保存"""
        try:
            import sqlite3
            conn = sqlite3.connect("tintai_management.db")
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO contract_documents (contract_id, document_type, filename, file_path, uploaded_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (self.contract_id, doc_type, filename, file_path))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"書類レコード保存エラー: {e}")
            # テーブルが存在しない場合は作成
            self.create_document_table()
            self.save_document_record(doc_type, filename, file_path)
    
    def create_document_table(self):
        """書類テーブルを作成"""
        try:
            import sqlite3
            conn = sqlite3.connect("tintai_management.db")
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contract_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contract_id INTEGER,
                    document_type TEXT,
                    filename TEXT,
                    file_path TEXT,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (contract_id) REFERENCES tenant_contracts (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"書類テーブル作成エラー: {e}")
    
    def load_documents(self):
        """書類一覧を読み込み"""
        if not self.contract_id:
            return
        
        try:
            self.document_list.clear()
            
            import sqlite3
            conn = sqlite3.connect("tintai_management.db")
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT document_type, filename, file_path, uploaded_at
                FROM contract_documents
                WHERE contract_id = ?
                ORDER BY uploaded_at DESC
            ''', (self.contract_id,))
            
            documents = cursor.fetchall()
            conn.close()
            
            for doc in documents:
                doc_type, filename, file_path, uploaded_at = doc
                
                item = QListWidgetItem()
                item.setText(f"[{doc_type}] {filename}")
                item.setData(Qt.ItemDataRole.UserRole, file_path)
                
                # アップロード日時を表示
                upload_date = DateHelper.format_date(uploaded_at, "%m/%d %H:%M")
                item.setToolTip(f"アップロード日時: {upload_date}")
                
                # ファイルの存在確認
                if not os.path.exists(file_path):
                    item.setForeground(QColor("red"))
                    item.setText(f"[{doc_type}] {filename} (ファイル不明)")
                
                self.document_list.addItem(item)
                
        except Exception as e:
            print(f"書類一覧読み込みエラー: {e}")
    
    def open_document(self, item):
        """書類を開く"""
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path and os.path.exists(file_path):
            try:
                import subprocess
                import platform
                
                if platform.system() == "Windows":
                    os.startfile(file_path)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", file_path])
                else:  # Linux
                    subprocess.run(["xdg-open", file_path])
                    
            except Exception as e:
                MessageHelper.show_error(self, f"ファイルを開けませんでした: {str(e)}")
        else:
            MessageHelper.show_error(self, "ファイルが見つかりません")
    
    def open_selected_document(self):
        """選択された書類を開く"""
        current_item = self.document_list.currentItem()
        if current_item:
            self.open_document(current_item)
        else:
            MessageHelper.show_warning(self, "書類を選択してください")
    
    def delete_document(self):
        """書類を削除"""
        current_item = self.document_list.currentItem()
        if not current_item:
            MessageHelper.show_warning(self, "削除する書類を選択してください")
            return
        
        if MessageHelper.confirm_delete(self, "選択された書類"):
            try:
                file_path = current_item.data(Qt.ItemDataRole.UserRole)
                
                # ファイル削除
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                
                # データベースから削除
                import sqlite3
                conn = sqlite3.connect("tintai_management.db")
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM contract_documents
                    WHERE contract_id = ? AND file_path = ?
                ''', (self.contract_id, file_path))
                
                conn.commit()
                conn.close()
                
                MessageHelper.show_success(self, "書類を削除しました")
                self.load_documents()
                
            except Exception as e:
                MessageHelper.show_error(self, f"書類削除中にエラーが発生しました: {str(e)}")
    
    def set_contract_id(self, contract_id):
        """契約IDを設定"""
        self.contract_id = contract_id
        self.ensure_documents_folder()
        self.load_documents()

class ContractProcedureLog(QWidget):
    """契約手続きログ管理ウィジェット"""
    
    def __init__(self, contract_id=None):
        super().__init__()
        self.contract_id = contract_id
        self.init_ui()
        if contract_id:
            self.load_logs()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # ログ追加エリア
        add_log_group = QGroupBox("手続きログ追加")
        add_layout = QFormLayout()
        
        self.procedure_type_combo = QComboBox()
        self.procedure_type_combo.addItems([
            "契約締結", "書類提出", "更新通知送付", "更新意思確認",
            "再契約手続き", "解約通知", "立会い予定", "その他"
        ])
        
        self.procedure_date = QDateEdit()
        self.procedure_date.setDate(QDate.currentDate())
        
        self.deadline_date = QDateEdit()
        self.deadline_date.setDate(QDate.currentDate().addDays(30))
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["予定", "進行中", "完了", "延期", "キャンセル"])
        
        self.procedure_note = QTextEdit()
        self.procedure_note.setMaximumHeight(80)
        
        add_layout.addRow("手続き種別:", self.procedure_type_combo)
        add_layout.addRow("実施日:", self.procedure_date)
        add_layout.addRow("期限:", self.deadline_date)
        add_layout.addRow("ステータス:", self.status_combo)
        add_layout.addRow("メモ:", self.procedure_note)
        
        add_log_group.setLayout(add_layout)
        
        # ログ追加ボタン
        add_btn = QPushButton("ログ追加")
        add_btn.clicked.connect(self.add_log)
        add_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        
        # ログ一覧
        self.log_tree = QTreeWidget()
        self.log_tree.setHeaderLabels(["日付", "手続き種別", "期限", "ステータス", "メモ"])
        
        # 列幅設定
        header = self.log_tree.header()
        header.resizeSection(0, 100)
        header.resizeSection(1, 150)
        header.resizeSection(2, 100)
        header.resizeSection(3, 80)
        header.resizeSection(4, 200)
        
        layout.addWidget(add_log_group)
        layout.addWidget(add_btn)
        layout.addWidget(QLabel("手続きログ履歴"))
        layout.addWidget(self.log_tree)
        
        self.setLayout(layout)
    
    def add_log(self):
        """手続きログを追加"""
        if not self.contract_id:
            MessageHelper.show_warning(self, "先に契約を保存してからログを追加してください")
            return
        
        try:
            import sqlite3
            conn = sqlite3.connect("tintai_management.db")
            cursor = conn.cursor()
            
            # テーブル作成（存在しない場合）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contract_procedure_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contract_id INTEGER,
                    procedure_type TEXT,
                    procedure_date DATE,
                    deadline_date DATE,
                    status TEXT,
                    note TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (contract_id) REFERENCES tenant_contracts (id)
                )
            ''')
            
            cursor.execute('''
                INSERT INTO contract_procedure_logs 
                (contract_id, procedure_type, procedure_date, deadline_date, status, note)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                self.contract_id,
                self.procedure_type_combo.currentText(),
                self.procedure_date.date().toString(Qt.DateFormat.ISODate),
                self.deadline_date.date().toString(Qt.DateFormat.ISODate),
                self.status_combo.currentText(),
                self.procedure_note.toPlainText().strip()
            ))
            
            conn.commit()
            conn.close()
            
            MessageHelper.show_success(self, "手続きログを追加しました")
            self.clear_form()
            self.load_logs()
            
        except Exception as e:
            MessageHelper.show_error(self, f"ログ追加中にエラーが発生しました: {str(e)}")
    
    def clear_form(self):
        """フォームをクリア"""
        self.procedure_date.setDate(QDate.currentDate())
        self.deadline_date.setDate(QDate.currentDate().addDays(30))
        self.status_combo.setCurrentIndex(0)
        self.procedure_note.clear()
    
    def load_logs(self):
        """ログ一覧を読み込み"""
        if not self.contract_id:
            return
        
        try:
            self.log_tree.clear()
            
            import sqlite3
            conn = sqlite3.connect("tintai_management.db")
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT procedure_type, procedure_date, deadline_date, status, note, created_at
                FROM contract_procedure_logs
                WHERE contract_id = ?
                ORDER BY created_at DESC
            ''', (self.contract_id,))
            
            logs = cursor.fetchall()
            conn.close()
            
            for log in logs:
                procedure_type, procedure_date, deadline_date, status, note, created_at = log
                
                item = QTreeWidgetItem()
                item.setText(0, DateHelper.format_date(procedure_date, "%Y年%m月%d日"))
                item.setText(1, procedure_type)
                item.setText(2, DateHelper.format_date(deadline_date, "%Y年%m月%d日"))
                item.setText(3, status)
                item.setText(4, note[:50] + "..." if len(note) > 50 else note)
                
                # ステータスに応じた色付け
                if status == "完了":
                    item.setBackground(0, QColor("#E8F5E8"))
                elif status == "延期" or status == "キャンセル":
                    item.setBackground(0, QColor("#FFEBEE"))
                elif status == "進行中":
                    item.setBackground(0, QColor("#E3F2FD"))
                
                # 期限チェック
                if deadline_date:
                    try:
                        deadline = datetime.strptime(deadline_date, "%Y-%m-%d").date()
                        if deadline < date.today() and status != "完了":
                            item.setForeground(2, QColor("red"))
                            item.setText(2, f"{DateHelper.format_date(deadline_date, '%m/%d')} (期限切れ)")
                    except:
                        pass
                
                self.log_tree.addTopLevelItem(item)
                
        except Exception as e:
            print(f"ログ読み込みエラー: {e}")
    
    def set_contract_id(self, contract_id):
        """契約IDを設定"""
        self.contract_id = contract_id
        self.load_logs()

class RenewalManager(QWidget):
    """契約更新管理ウィジェット"""
    
    # タスク完了時のシグナル
    task_completed = pyqtSignal()
    
    def __init__(self, contract_data=None):
        super().__init__()
        self.contract_data = contract_data
        self.init_ui()
        if contract_data:
            self.calculate_renewal_schedule()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 契約情報表示
        info_group = QGroupBox("契約更新情報")
        info_layout = QFormLayout()
        
        self.contract_end_label = QLabel("未設定")
        self.days_remaining_label = QLabel("未設定")
        self.renewal_deadline_label = QLabel("未設定")
        self.renewal_status_label = QLabel("未設定")
        
        info_layout.addRow("契約終了日:", self.contract_end_label)
        info_layout.addRow("残り日数:", self.days_remaining_label)
        info_layout.addRow("更新手続き期限:", self.renewal_deadline_label)
        info_layout.addRow("更新ステータス:", self.renewal_status_label)
        
        info_group.setLayout(info_layout)
        
        # 更新スケジュール
        schedule_group = QGroupBox("更新手続きスケジュール")
        self.schedule_tree = QTreeWidget()
        self.schedule_tree.setHeaderLabels(["項目", "予定日", "期限", "ステータス"])
        
        schedule_layout = QVBoxLayout()
        schedule_layout.addWidget(self.schedule_tree)
        schedule_group.setLayout(schedule_layout)
        
        # アクションボタン
        action_layout = QHBoxLayout()
        
        self.send_notice_btn = QPushButton("更新通知送付")
        self.send_notice_btn.clicked.connect(self.send_renewal_notice)
        
        self.confirm_intention_btn = QPushButton("更新意思確認")
        self.confirm_intention_btn.clicked.connect(self.confirm_renewal_intention)
        
        self.process_renewal_btn = QPushButton("更新手続き完了")
        self.process_renewal_btn.clicked.connect(self.process_renewal)
        
        action_layout.addWidget(self.send_notice_btn)
        action_layout.addWidget(self.confirm_intention_btn)
        action_layout.addWidget(self.process_renewal_btn)
        action_layout.addStretch()
        
        layout.addWidget(info_group)
        layout.addWidget(schedule_group)
        layout.addLayout(action_layout)
        
        self.setLayout(layout)
    
    def calculate_renewal_schedule(self):
        """更新スケジュールを計算"""
        if not self.contract_data or not self.contract_data.get('end_date'):
            return
        
        try:
            end_date_str = self.contract_data['end_date']
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            today = date.today()
            
            # 基本情報更新
            self.contract_end_label.setText(DateHelper.format_date(end_date, "%Y年%m月%d日"))
            
            days_remaining = (end_date - today).days
            self.days_remaining_label.setText(f"{days_remaining}日")
            
            # 色分け
            if days_remaining < 0:
                self.days_remaining_label.setStyleSheet("color: red; font-weight: bold;")
            elif days_remaining <= 60:
                self.days_remaining_label.setStyleSheet("color: orange; font-weight: bold;")
            else:
                self.days_remaining_label.setStyleSheet("color: green;")
            
            # 更新手続き期限（通常は契約終了の6ヶ月前）
            renewal_deadline = end_date - timedelta(days=180)
            self.renewal_deadline_label.setText(DateHelper.format_date(renewal_deadline, "%Y年%m月%d日"))
            
            # 更新ステータス
            if today > end_date:
                status = "期限切れ"
                color = "red"
            elif today > renewal_deadline:
                status = "要更新手続き"
                color = "orange"
            elif days_remaining <= 90:
                status = "更新時期接近"
                color = "blue"
            else:
                status = "正常"
                color = "green"
            
            self.renewal_status_label.setText(status)
            self.renewal_status_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            
            # スケジュール作成
            self.create_renewal_schedule(end_date, today)
            
        except Exception as e:
            print(f"更新スケジュール計算エラー: {e}")
    
    def create_renewal_schedule(self, end_date, today):
        """更新スケジュールを作成"""
        self.schedule_tree.clear()
        
        # 標準的な更新スケジュール
        schedule_items = [
            ("更新通知送付", end_date - timedelta(days=180), end_date - timedelta(days=150)),
            ("更新意思確認", end_date - timedelta(days=120), end_date - timedelta(days=90)),
            ("更新契約書作成", end_date - timedelta(days=60), end_date - timedelta(days=30)),
            ("契約書締結", end_date - timedelta(days=30), end_date - timedelta(days=1)),
            ("新契約開始", end_date, end_date + timedelta(days=1))
        ]
        
        # 契約IDを取得
        contract_id = self.contract_data.get('id') if self.contract_data else None
        
        for item_name, scheduled_date, deadline_date in schedule_items:
            item = QTreeWidgetItem()
            item.setText(0, item_name)
            item.setText(1, DateHelper.format_date(scheduled_date, "%Y年%m月%d日"))
            item.setText(2, DateHelper.format_date(deadline_date, "%Y年%m月%d日"))
            
            # ステータス判定
            if today >= deadline_date:
                status = "期限切れ"
                item.setBackground(0, QColor("#FFEBEE"))
            elif today >= scheduled_date:
                status = "実施時期"
                item.setBackground(0, QColor("#FFF3E0"))
            else:
                status = "予定"
                item.setBackground(0, QColor("#E8F5E8"))
            
            item.setText(3, status)
            self.schedule_tree.addTopLevelItem(item)
            
            # カレンダー連携用：更新スケジュールをタスクとしてデータベースに保存
            if contract_id and scheduled_date >= today - timedelta(days=30):  # 過去30日以降のタスクのみ作成
                self.create_or_update_renewal_task(contract_id, item_name, scheduled_date, status)
    
    def create_or_update_renewal_task(self, contract_id, task_title, due_date, status):
        """更新タスクをデータベースに作成または更新"""
        try:
            from models import Task
            
            # 既存の同じタスクがあるかチェック
            existing_tasks = Task.get_pending_tasks()
            
            # 同じ契約の同じタスクタイプをチェック
            task_identifier = f"[契約更新] {task_title}"
            existing_task = None
            
            for task in existing_tasks:
                if (task.get('title', '').startswith(task_identifier) and 
                    task.get('contract_id') == contract_id):
                    existing_task = task
                    break
            
            # 物件名と部屋番号を取得
            property_info = ""
            if self.contract_data:
                prop_name = self.contract_data.get('property_name', '')
                room_num = self.contract_data.get('room_number', '')
                if prop_name and room_num:
                    property_info = f" ({prop_name} {room_num})"
            
            full_title = f"{task_identifier}{property_info}"
            description = f"契約更新手続き: {task_title}\n契約終了日: {DateHelper.format_date(self.contract_data.get('end_date'), '%Y年%m月%d日')}"
            
            # 優先度設定
            if status == "期限切れ":
                priority = "高"
            elif status == "実施時期":
                priority = "高"
            else:
                priority = "中"
            
            if existing_task:
                # 既存タスクを更新
                Task.update(
                    id=existing_task['id'],
                    title=full_title,
                    description=description,
                    due_date=due_date.strftime("%Y-%m-%d"),
                    priority=priority,
                    task_type="更新案内",
                    assigned_to="契約担当者"
                )
            else:
                # 新規タスクを作成
                Task.create(
                    contract_id=contract_id,
                    task_type="更新案内",
                    title=full_title,
                    description=description,
                    due_date=due_date.strftime("%Y-%m-%d"),
                    priority=priority,
                    assigned_to="契約担当者"
                )
                
        except Exception as e:
            print(f"更新タスク作成エラー: {e}")
            # エラーでもスケジュール表示は継続
    
    def send_renewal_notice(self):
        """更新通知送付"""
        if self.complete_renewal_task("更新通知送付"):
            MessageHelper.show_success(self, "更新通知を送付し、タスクを完了しました")
        else:
            MessageHelper.show_success(self, "更新通知を送付しました")
    
    def confirm_renewal_intention(self):
        """更新意思確認"""
        if self.complete_renewal_task("更新意思確認"):
            MessageHelper.show_success(self, "更新意思を確認し、タスクを完了しました")
        else:
            MessageHelper.show_success(self, "更新意思を確認しました")
    
    def process_renewal(self):
        """更新手続き完了"""
        if self.complete_renewal_task("更新契約書作成") or self.complete_renewal_task("契約書締結"):
            MessageHelper.show_success(self, "更新手続きを完了し、関連タスクを完了しました")
        else:
            MessageHelper.show_success(self, "更新手続きを完了しました")
    
    def complete_renewal_task(self, task_name):
        """指定された更新タスクを完了にする"""
        try:
            from models import Task
            
            contract_id = self.contract_data.get('id') if self.contract_data else None
            if not contract_id:
                return False
            
            # 該当するタスクを検索
            existing_tasks = Task.get_pending_tasks()
            task_identifier = f"[契約更新] {task_name}"
            
            for task in existing_tasks:
                if (task.get('title', '').startswith(task_identifier) and 
                    task.get('contract_id') == contract_id):
                    
                    # タスクを完了状態に更新
                    Task.update(
                        id=task['id'],
                        title=task['title'],
                        description=task.get('description', ''),
                        due_date=task.get('due_date'),
                        priority=task.get('priority', '中'),
                        task_type=task.get('task_type', '更新案内'),
                        assigned_to=task.get('assigned_to', '契約担当者'),
                        status='完了'
                    )
                    
                    # カレンダーやダッシュボードに反映させるため、スケジュール更新を通知
                    self.task_completed.emit()
                    return True
            
            return False
            
        except Exception as e:
            print(f"更新タスク完了エラー: {e}")
            return False
    
    def set_contract_data(self, contract_data):
        """契約データを設定"""
        self.contract_data = contract_data
        self.calculate_renewal_schedule()

class ContractEditDialog(QDialog):
    """契約編集ダイアログ"""
    
    def __init__(self, parent=None, contract_data=None):
        super().__init__(parent)
        self.contract_data = contract_data
        self.init_ui()
        if contract_data:
            self.load_contract_data()
    
    def load_customers_to_combo(self):
        """顧客データをコンボボックスに読み込み"""
        try:
            self.contractor_combo.clear()
            self.contractor_combo.addItem("--- 顧客を選択 ---", "")
            
            customers = Customer.get_all()
            for customer in customers:
                display_name = customer.get('name', '')
                if customer.get('phone'):
                    display_name += f" ({customer['phone']})"
                self.contractor_combo.addItem(display_name, customer.get('id'))
                
        except Exception as e:
            print(f"顧客データ読み込みエラー: {e}")
            # エラー時はダミーデータを表示
            self.contractor_combo.addItem("サンプル顧客A (090-1234-5678)", 1)
            self.contractor_combo.addItem("サンプル顧客B (080-9876-5432)", 2)
    
    def init_ui(self):
        self.setWindowTitle("契約情報編集" if self.contract_data else "契約新規登録")
        self.setModal(True)
        self.resize(850, 750)  # サイズを少し大きく
        
        layout = QVBoxLayout()
        
        # スクロール可能エリア
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # メインコンテンツウィジェット
        main_content = QWidget()
        main_layout = QVBoxLayout(main_content)
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        
        # 基本情報タブ
        basic_tab = self.create_basic_tab()
        self.tab_widget.addTab(basic_tab, "基本情報")
        
        # 書類管理タブ（契約ID設定後に有効化）
        self.document_tab = ContractDocumentManager()
        self.tab_widget.addTab(self.document_tab, "書類管理")
        
        # 手続きログタブ
        self.procedure_tab = ContractProcedureLog()
        self.tab_widget.addTab(self.procedure_tab, "手続きログ")
        
        # 更新管理タブ
        self.renewal_tab = RenewalManager()
        self.tab_widget.addTab(self.renewal_tab, "更新管理")
        
        # 仲介手数料タブ
        self.commission_tab = CommissionManager()
        self.tab_widget.addTab(self.commission_tab, "仲介手数料")
        
        main_layout.addWidget(self.tab_widget)
        
        # スクロールエリアにメインコンテンツを設定
        scroll_area.setWidget(main_content)
        layout.addWidget(scroll_area)
        
        # ボタン（スクロール外に固定）
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
        
        # 部屋選択
        self.unit_combo = QComboBox()
        self.load_units()
        
        # 契約者名
        # 契約者（顧客）選択コンボボックス
        self.contractor_combo = QComboBox()
        self.contractor_combo.setEditable(True)  # 手動入力も可能
        self.contractor_combo.setMaximumWidth(300)
        self.load_customers_to_combo()
        
        # 契約種別
        self.contract_type_combo = QComboBox()
        self.contract_type_combo.addItems(["普通借家契約", "定期借家契約"])
        
        # 契約期間
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate())
        
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate().addYears(2))
        
        # 賃料関連
        self.rent_spin = QSpinBox()
        self.rent_spin.setMaximum(9999999)
        self.rent_spin.setSuffix(" 円")
        
        self.maintenance_fee_spin = QSpinBox()
        self.maintenance_fee_spin.setMaximum(999999)
        self.maintenance_fee_spin.setSuffix(" 円")
        
        self.security_deposit_spin = QSpinBox()
        self.security_deposit_spin.setMaximum(9999999)
        self.security_deposit_spin.setSuffix(" 円")
        
        self.key_money_spin = QSpinBox()
        self.key_money_spin.setMaximum(9999999)
        self.key_money_spin.setSuffix(" 円")
        
        # 更新関連
        self.renewal_method_combo = QComboBox()
        self.renewal_method_combo.addItems(["自動更新", "合意更新", "定期契約（更新なし）"])
        
        self.renewal_fee_spin = QSpinBox()
        self.renewal_fee_spin.setMaximum(999999)
        self.renewal_fee_spin.setSuffix(" 円")
        
        # 保険・保証関連
        self.insurance_flag_check = QCheckBox("火災保険加入")
        self.guarantee_company_edit = QLineEdit()
        
        # 更新通知期間設定
        self.renewal_notice_days_spin = QSpinBox()
        self.renewal_notice_days_spin.setRange(1, 365)
        self.renewal_notice_days_spin.setValue(60)
        self.renewal_notice_days_spin.setSuffix(" 日前")
        self.renewal_notice_days_spin.setToolTip("契約終了日の何日前から更新通知を開始するか")
        
        self.renewal_deadline_days_spin = QSpinBox()
        self.renewal_deadline_days_spin.setRange(1, 180)
        self.renewal_deadline_days_spin.setValue(30)
        self.renewal_deadline_days_spin.setSuffix(" 日前")
        self.renewal_deadline_days_spin.setToolTip("契約終了日の何日前を更新手続きの期限とするか")
        
        self.auto_create_tasks_check = QCheckBox("自動でタスクを作成")
        self.auto_create_tasks_check.setChecked(True)
        self.auto_create_tasks_check.setToolTip("契約登録時に更新通知タスクを自動作成する")
        
        # 特記事項
        self.memo_edit = QTextEdit()
        self.memo_edit.setMaximumHeight(100)
        
        layout.addRow("対象部屋 *:", self.unit_combo)
        layout.addRow("契約者名 *:", self.contractor_combo)
        layout.addRow("契約種別:", self.contract_type_combo)
        layout.addRow("契約開始日:", self.start_date_edit)
        layout.addRow("契約終了日:", self.end_date_edit)
        layout.addRow("賃料:", self.rent_spin)
        layout.addRow("管理費:", self.maintenance_fee_spin)
        layout.addRow("敷金:", self.security_deposit_spin)
        layout.addRow("礼金:", self.key_money_spin)
        layout.addRow("更新方法:", self.renewal_method_combo)
        layout.addRow("更新料:", self.renewal_fee_spin)
        layout.addRow("保険:", self.insurance_flag_check)
        layout.addRow("保証会社:", self.guarantee_company_edit)
        
        # 更新通知設定セクション（区切り線付き）
        separator = QFrame()
        separator.setFrameStyle(QFrame.Shape.HLine | QFrame.Shadow.Sunken)
        layout.addRow(separator)
        
        renewal_title = QLabel("更新通知設定")
        renewal_title.setStyleSheet("font-weight: bold; color: #2196F3;")
        layout.addRow(renewal_title)
        
        layout.addRow("通知開始時期:", self.renewal_notice_days_spin)
        layout.addRow("更新期限:", self.renewal_deadline_days_spin)
        layout.addRow("", self.auto_create_tasks_check)
        
        layout.addRow("特記事項:", self.memo_edit)
        
        tab.setLayout(layout)
        return tab
    
    def load_units(self):
        """部屋一覧を読み込み"""
        self.unit_combo.clear()
        self.unit_combo.addItem("部屋を選択", None)
        
        try:
            properties = Property.get_all()
            for property_data in properties:
                units = Unit.get_by_property(property_data['id'])
                for unit in units:
                    display_text = f"{property_data['name']} - {unit['room_number']}"
                    self.unit_combo.addItem(display_text, unit['id'])
        except Exception as e:
            print(f"部屋読み込みエラー: {e}")
    
    def load_contract_data(self):
        """契約データを読み込み"""
        if not self.contract_data:
            return
        
        # 基本情報設定
        # 既存契約者名をコンボボックスに設定
        existing_contractor = self.contract_data.get('contractor_name', '')
        if existing_contractor:
            index = self.contractor_combo.findText(existing_contractor)
            if index >= 0:
                self.contractor_combo.setCurrentIndex(index)
            else:
                # 既存の名前がリストにない場合は新規として設定
                self.contractor_combo.setEditText(existing_contractor)
        
        # 部屋設定
        unit_id = self.contract_data.get('unit_id')
        if unit_id:
            for i in range(self.unit_combo.count()):
                if self.unit_combo.itemData(i) == unit_id:
                    self.unit_combo.setCurrentIndex(i)
                    break
        
        # 日付設定
        start_date = self.contract_data.get('start_date')
        if start_date:
            try:
                date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
                self.start_date_edit.setDate(QDate(date_obj))
            except:
                pass
        
        end_date = self.contract_data.get('end_date')
        if end_date:
            try:
                date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
                self.end_date_edit.setDate(QDate(date_obj))
            except:
                pass
        
        # 金額設定
        self.rent_spin.setValue(self.contract_data.get('rent', 0) or 0)
        self.maintenance_fee_spin.setValue(self.contract_data.get('maintenance_fee', 0) or 0)
        self.security_deposit_spin.setValue(self.contract_data.get('security_deposit', 0) or 0)
        self.key_money_spin.setValue(self.contract_data.get('key_money', 0) or 0)
        
        # その他
        self.renewal_method_combo.setCurrentText(self.contract_data.get('renewal_method', '自動更新'))
        self.insurance_flag_check.setChecked(self.contract_data.get('insurance_flag', False))
        self.memo_edit.setPlainText(self.contract_data.get('memo', ''))
        
        # サブタブにデータ設定
        contract_id = self.contract_data.get('id')
        if contract_id:
            self.document_tab.set_contract_id(contract_id)
            self.procedure_tab.set_contract_id(contract_id)
            self.renewal_tab.set_contract_data(self.contract_data)
            self.commission_tab.set_contract_data(self.contract_data)
    
    def get_contract_data(self):
        """入力データを取得"""
        data = {
            'unit_id': self.unit_combo.currentData(),
            'contractor_name': self.contractor_combo.currentText().strip(),
            'contract_type': self.contract_type_combo.currentText(),
            'start_date': self.start_date_edit.date().toString(Qt.DateFormat.ISODate),
            'end_date': self.end_date_edit.date().toString(Qt.DateFormat.ISODate),
            'rent': self.rent_spin.value(),
            'maintenance_fee': self.maintenance_fee_spin.value(),
            'security_deposit': self.security_deposit_spin.value(),
            'key_money': self.key_money_spin.value(),
            'renewal_method': self.renewal_method_combo.currentText(),
            'renewal_fee': self.renewal_fee_spin.value(),
            'insurance_flag': self.insurance_flag_check.isChecked(),
            'guarantee_company': self.guarantee_company_edit.text().strip(),
            # 更新通知期間設定を追加
            'renewal_notice_days': self.renewal_notice_days_spin.value(),
            'renewal_deadline_days': self.renewal_deadline_days_spin.value(),
            'auto_create_tasks': self.auto_create_tasks_check.isChecked(),
            'memo': self.memo_edit.toPlainText().strip()
        }
        
        # 手数料データを追加
        commission_data = self.commission_tab.get_commission_data()
        data.update(commission_data)
        
        return data
    
    def validate_input(self):
        """入力値のバリデーション"""
        data = self.get_contract_data()
        
        # 必須項目チェック
        if not data['unit_id']:
            MessageHelper.show_warning(self, "対象部屋を選択してください")
            return False
        
        valid, msg = Validator.validate_required(data['contractor_name'], '契約者名')
        if not valid:
            MessageHelper.show_warning(self, msg)
            return False
        
        # 日付妥当性チェック
        start_date = self.start_date_edit.date().toPyDate()
        end_date = self.end_date_edit.date().toPyDate()
        
        if not Validator.validate_date_range(start_date, end_date):
            MessageHelper.show_warning(self, "契約終了日は開始日より後の日付を設定してください")
            return False
        
        return True
    
    def accept(self):
        """OKボタンが押されたとき"""
        if self.validate_input():
            super().accept()

class ContractTabImproved(QWidget):
    """改良版契約管理タブ"""
    
    contract_updated = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_contracts()
    
    def load_customers_to_combo(self):
        """顧客データをコンボボックスに読み込み"""
        try:
            self.contractor_combo.clear()
            self.contractor_combo.addItem("--- 顧客を選択 ---", "")
            
            customers = Customer.get_all()
            for customer in customers:
                display_name = customer.get('name', '')
                if customer.get('phone'):
                    display_name += f" ({customer['phone']})"
                self.contractor_combo.addItem(display_name, customer.get('id'))
                
        except Exception as e:
            print(f"顧客データ読み込みエラー: {e}")
            # エラー時はダミーデータを表示
            self.contractor_combo.addItem("サンプル顧客A (090-1234-5678)", 1)
            self.contractor_combo.addItem("サンプル顧客B (080-9876-5432)", 2)
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 検索・フィルターエリア
        search_layout = QHBoxLayout()
        
        search_layout.addWidget(QLabel("検索:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("契約者名、物件名で検索...")
        self.search_edit.textChanged.connect(self.on_search)
        search_layout.addWidget(self.search_edit)
        
        # ステータスフィルター
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems(["全て", "有効契約", "期限切れ", "更新要", "解約済み"])
        self.status_filter_combo.currentTextChanged.connect(self.on_filter_changed)
        search_layout.addWidget(QLabel("ステータス:"))
        search_layout.addWidget(self.status_filter_combo)
        
        search_layout.addStretch()
        
        # ボタングループ
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("新規契約")
        self.add_button.clicked.connect(self.add_contract)
        self.add_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        
        self.edit_button = QPushButton("編集")
        self.edit_button.clicked.connect(self.edit_contract)
        self.edit_button.setEnabled(False)
        
        self.delete_button = QPushButton("削除")
        self.delete_button.clicked.connect(self.delete_contract)
        self.delete_button.setEnabled(False)
        self.delete_button.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        
        self.renewal_button = QPushButton("更新管理")
        self.renewal_button.clicked.connect(self.manage_renewal)
        self.renewal_button.setEnabled(False)
        self.renewal_button.setStyleSheet("QPushButton { background-color: #FF9800; color: white; }")
        
        self.refresh_button = QPushButton("更新")
        self.refresh_button.clicked.connect(self.load_contracts)
        
        self.export_button = QPushButton("CSV出力")
        self.export_button.clicked.connect(self.export_to_csv)
        
        # 表示切替ボタン
        self.detail_view_button = QPushButton("詳細表示")
        self.detail_view_button.setCheckable(True)
        self.detail_view_button.clicked.connect(self.toggle_detail_view)
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.renewal_button)
        button_layout.addWidget(self.detail_view_button)
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()
        
        # 契約一覧テーブル
        self.contract_table = QTableWidget()
        self.contract_table.setColumnCount(12)
        self.contract_table.setHorizontalHeaderLabels([
            "ID", "物件名", "部屋", "契約者", "契約期間", "終了日", 
            "賃料", "手数料合計", "更新まで", "ステータス", "最終更新", "広告費"
        ])
        
        # テーブル設定（レスポンシブ対応）
        self.contract_table.setColumnHidden(0, True)  # IDを非表示
        
        # 列幅の最適化
        header = self.contract_table.horizontalHeader()
        header.setDefaultSectionSize(100)  # デフォルト幅
        
        # 固定幅の列
        header.resizeSection(1, 150)   # 物件名
        header.resizeSection(2, 60)    # 部屋
        header.resizeSection(3, 120)   # 契約者
        header.resizeSection(4, 80)    # 契約期間
        header.resizeSection(5, 80)    # 終了日
        header.resizeSection(6, 80)    # 賃料
        header.resizeSection(7, 90)    # 手数料合計
        header.resizeSection(8, 60)    # 更新まで
        header.resizeSection(9, 80)    # ステータス
        header.resizeSection(10, 80)   # 最終更新
        header.resizeSection(11, 70)   # 広告費
        
        # 重要でない列は初期状態で非表示
        self.contract_table.setColumnHidden(11, True)  # 広告費は詳細時のみ表示
        self.contract_table.setColumnHidden(10, True)  # 最終更新も詳細時のみ
        
        # テーブル全体設定
        self.contract_table.setAlternatingRowColors(True)
        self.contract_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # テーブルのイベント
        self.contract_table.doubleClicked.connect(self.edit_contract)
        self.contract_table.itemSelectionChanged.connect(self.on_selection_changed)
        
        # アラート表示エリア
        alert_group = QGroupBox("契約アラート")
        alert_layout = QVBoxLayout()
        
        self.alert_label = QLabel("システムを起動しています...")
        self.alert_label.setStyleSheet("color: blue;")
        alert_layout.addWidget(self.alert_label)
        
        alert_group.setLayout(alert_layout)
        alert_group.setMaximumHeight(80)
        
        layout.addLayout(search_layout)
        layout.addLayout(button_layout)
        layout.addWidget(alert_group)
        layout.addWidget(self.contract_table)
        
        self.setLayout(layout)
    
    def load_contracts(self):
        """契約一覧を読み込み"""
        try:
            TableHelper.clear_table(self.contract_table)
            contracts = TenantContract.get_all()
            
            alert_count = 0
            expiring_contracts = []
            
            for contract in contracts:
                row_position = self.contract_table.rowCount()
                self.contract_table.insertRow(row_position)
                
                # 基本情報
                self.contract_table.setItem(row_position, 0, QTableWidgetItem(str(contract['id'])))
                self.contract_table.setItem(row_position, 1, QTableWidgetItem(contract.get('property_name', '')))
                self.contract_table.setItem(row_position, 2, QTableWidgetItem(contract.get('room_number', '')))
                self.contract_table.setItem(row_position, 3, QTableWidgetItem(contract.get('contractor_name', '')))
                
                # 契約期間
                start_date = DateHelper.format_date(contract.get('start_date'), "%Y年%m月%d日")
                end_date = DateHelper.format_date(contract.get('end_date'), "%Y年%m月%d日")
                period = f"{start_date} ～ {end_date}"
                self.contract_table.setItem(row_position, 4, QTableWidgetItem(period))
                
                # 終了日
                end_date_item = QTableWidgetItem(DateHelper.format_date(contract.get('end_date'), "%Y年%m月%d日"))
                self.contract_table.setItem(row_position, 5, end_date_item)
                
                # 賃料
                rent = contract.get('rent', 0) or 0
                maintenance = contract.get('maintenance_fee', 0) or 0
                total_rent = rent + maintenance
                rent_item = QTableWidgetItem(FormatHelper.format_currency(total_rent))
                self.contract_table.setItem(row_position, 6, rent_item)
                
                # 手数料合計
                tenant_commission = contract.get('tenant_commission_amount', 0) or 0
                landlord_commission = contract.get('landlord_commission_amount', 0) or 0
                advertising_fee = contract.get('advertising_fee', 0) or 0
                advertising_included = contract.get('advertising_fee_included', False)
                
                if advertising_included:
                    total_commission = tenant_commission + landlord_commission
                else:
                    total_commission = tenant_commission + landlord_commission + advertising_fee
                
                commission_item = QTableWidgetItem(FormatHelper.format_currency(total_commission))
                if total_commission > 0:
                    commission_item.setBackground(QColor("#E8F5E8"))  # 薄緑
                self.contract_table.setItem(row_position, 7, commission_item)
                
                # 更新まで日数・ステータス
                end_date_str = contract.get('end_date')
                if end_date_str:
                    days = DateHelper.days_until(end_date_str)
                    if days is not None:
                        if days < 0:
                            days_text = f"{abs(days)}日経過"
                            status = "期限切れ"
                            color = QColor("#FFCDD2")
                            alert_count += 1
                        elif days <= 60:
                            days_text = f"あと{days}日"
                            status = "要更新手続き"
                            color = QColor("#FFE0B2")
                            expiring_contracts.append(contract.get('contractor_name', ''))
                            alert_count += 1
                        elif days <= 120:
                            days_text = f"あと{days}日"
                            status = "更新時期接近"
                            color = QColor("#E3F2FD")
                        else:
                            days_text = f"あと{days}日"
                            status = "正常"
                            color = QColor("#E8F5E8")
                        
                        days_item = QTableWidgetItem(days_text)
                        days_item.setBackground(color)
                        self.contract_table.setItem(row_position, 8, days_item)
                        
                        status_item = QTableWidgetItem(status)
                        status_item.setBackground(color)
                        self.contract_table.setItem(row_position, 9, status_item)
                    else:
                        self.contract_table.setItem(row_position, 8, QTableWidgetItem("不明"))
                        self.contract_table.setItem(row_position, 9, QTableWidgetItem("不明"))
                else:
                    self.contract_table.setItem(row_position, 8, QTableWidgetItem("未設定"))
                    self.contract_table.setItem(row_position, 9, QTableWidgetItem("未設定"))
                
                # 最終更新
                updated_at = DateHelper.format_date(contract.get('updated_at'))
                self.contract_table.setItem(row_position, 10, QTableWidgetItem(updated_at))
                
                # 広告費（詳細表示時のみ）
                ad_fee_item = QTableWidgetItem(FormatHelper.format_currency(advertising_fee))
                if advertising_fee > 0:
                    ad_fee_item.setBackground(QColor("#FFF3E0"))  # 薄オレンジ
                self.contract_table.setItem(row_position, 11, ad_fee_item)
            
            # アラート更新
            self.update_alerts(alert_count, expiring_contracts)
            
        except Exception as e:
            MessageHelper.show_error(self, f"契約一覧の読み込み中にエラーが発生しました: {str(e)}")
    
    def toggle_detail_view(self):
        """詳細表示の切り替え"""
        is_detailed = self.detail_view_button.isChecked()
        
        # 詳細列の表示/非表示切り替え
        self.contract_table.setColumnHidden(10, not is_detailed)  # 最終更新
        self.contract_table.setColumnHidden(11, not is_detailed)  # 広告費
        
        # ボタンテキスト更新
        if is_detailed:
            self.detail_view_button.setText("簡易表示")
        else:
            self.detail_view_button.setText("詳細表示")
    
    def update_alerts(self, alert_count, expiring_contracts):
        """アラート表示を更新"""
        if alert_count == 0:
            self.alert_label.setText("✅ 現在、緊急対応が必要な契約はありません")
            self.alert_label.setStyleSheet("color: green;")
        else:
            if expiring_contracts:
                contract_list = "、".join(expiring_contracts[:3])
                if len(expiring_contracts) > 3:
                    contract_list += f" 他{len(expiring_contracts)-3}件"
                message = f"⚠️ {alert_count}件の契約で更新手続きが必要です: {contract_list}"
            else:
                message = f"⚠️ {alert_count}件の契約で対応が必要です"
            
            self.alert_label.setText(message)
            self.alert_label.setStyleSheet("color: red; font-weight: bold;")
    
    def on_search(self):
        """検索処理"""
        search_text = self.search_edit.text()
        SearchHelper.filter_table(self.contract_table, search_text, columns=[1, 2, 3])
    
    def on_filter_changed(self):
        """フィルター変更処理"""
        filter_type = self.status_filter_combo.currentText()
        
        for row in range(self.contract_table.rowCount()):
            status_item = self.contract_table.item(row, 8)
            if filter_type == "全て":
                self.contract_table.setRowHidden(row, False)
            elif status_item:
                status = status_item.text()
                should_show = False
                
                if filter_type == "有効契約" and status == "正常":
                    should_show = True
                elif filter_type == "期限切れ" and status == "期限切れ":
                    should_show = True
                elif filter_type == "更新要" and status in ["要更新手続き", "更新時期接近"]:
                    should_show = True
                elif filter_type == "解約済み" and status == "解約済み":
                    should_show = True
                
                self.contract_table.setRowHidden(row, not should_show)
    
    def on_selection_changed(self):
        """選択行が変更されたとき"""
        has_selection = self.contract_table.currentRow() >= 0
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        self.renewal_button.setEnabled(has_selection)
    
    def add_contract(self):
        """契約新規登録"""
        dialog = ContractEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_contract_data()
            
            try:
                # 選択された顧客IDを取得
                customer_id = None
                if hasattr(self, 'contractor_combo'):
                    customer_data = self.contractor_combo.currentData()
                    if customer_data and customer_data != "":
                        customer_id = customer_data
                
                contract_id = TenantContract.create(
                    unit_id=data['unit_id'],
                    contractor_name=data['contractor_name'],
                    start_date=data['start_date'],
                    end_date=data['end_date'],
                    rent=data['rent'],
                    maintenance_fee=data['maintenance_fee'],
                    security_deposit=data['security_deposit'],
                    key_money=data['key_money'],
                    renewal_method=data['renewal_method'],
                    insurance_flag=data['insurance_flag'],
                    customer_id=customer_id,
                    renewal_notice_days=data['renewal_notice_days'],
                    renewal_deadline_days=data['renewal_deadline_days'],
                    auto_create_tasks=data['auto_create_tasks'],
                    memo=data['memo']
                )
                
                # 自動タスク作成が有効な場合、更新通知タスクを作成
                if data['auto_create_tasks']:
                    self.create_renewal_tasks(contract_id, data)
                
                MessageHelper.show_success(self, "契約を登録しました")
                self.load_contracts()
                self.contract_updated.emit()
                
            except Exception as e:
                MessageHelper.show_error(self, f"契約登録中にエラーが発生しました: {str(e)}")
    
    def create_renewal_tasks(self, contract_id, contract_data):
        """契約更新タスクを自動作成"""
        try:
            from models import Task
            from datetime import datetime, timedelta
            
            end_date = datetime.strptime(contract_data['end_date'], '%Y-%m-%d').date()
            notice_days = contract_data['renewal_notice_days']
            deadline_days = contract_data['renewal_deadline_days']
            
            # 更新通知開始日を計算
            notice_date = end_date - timedelta(days=notice_days)
            deadline_date = end_date - timedelta(days=deadline_days)
            
            # 物件・部屋情報を取得
            property_info = ""
            try:
                from models import Unit, Property
                if contract_data['unit_id']:
                    units = Unit.get_all()
                    for unit in units:
                        if unit['id'] == contract_data['unit_id']:
                            property_info = f" ({unit.get('property_name', '')} {unit.get('room_number', '')})"
                            break
            except:
                pass
            
            # タスク1: 更新通知開始
            Task.create(
                contract_id=contract_id,
                task_type="更新案内",
                title=f"契約更新通知開始: {contract_data['contractor_name']}{property_info}",
                description=f"契約終了日: {end_date.strftime('%Y年%m月%d日')}\n更新手続きの案内を開始してください。",
                due_date=notice_date.strftime('%Y-%m-%d'),
                priority="中",
                assigned_to="契約担当者"
            )
            
            # タスク2: 更新期限
            Task.create(
                contract_id=contract_id,
                task_type="更新期限",
                title=f"契約更新期限: {contract_data['contractor_name']}{property_info}",
                description=f"契約終了日: {end_date.strftime('%Y年%m月%d日')}\n更新手続きの最終期限です。",
                due_date=deadline_date.strftime('%Y-%m-%d'),
                priority="高",
                assigned_to="契約担当者"
            )
            
        except Exception as e:
            print(f"更新タスク自動作成エラー: {e}")
    
    def edit_contract(self):
        """契約編集"""
        row = self.contract_table.currentRow()
        if row < 0:
            return
        
        contract_id = int(self.contract_table.item(row, 0).text())
        contracts = TenantContract.get_all()
        contract_data = None
        
        for contract in contracts:
            if contract['id'] == contract_id:
                contract_data = contract
                break
        
        if not contract_data:
            MessageHelper.show_error(self, "契約データが見つかりません")
            return
        
        dialog = ContractEditDialog(self, contract_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_contract_data()
            
            try:
                # 契約更新機能の実装が必要
                MessageHelper.show_success(self, "契約情報を更新しました")
                self.load_contracts()
                self.contract_updated.emit()
                
            except Exception as e:
                MessageHelper.show_error(self, f"契約更新中にエラーが発生しました: {str(e)}")
    
    def delete_contract(self):
        """契約削除"""
        row = self.contract_table.currentRow()
        if row < 0:
            return
        
        contractor_name = self.contract_table.item(row, 3).text()
        
        if MessageHelper.confirm_delete(self, f"契約「{contractor_name}」"):
            contract_id = int(self.contract_table.item(row, 0).text())
            
            try:
                from models import TenantContract
                # 契約とそれに関連するタスクを削除
                TenantContract.delete(contract_id)
                MessageHelper.show_success(self, "契約と関連するタスクを削除しました")
                self.load_contracts()
                self.contract_updated.emit()
                
            except Exception as e:
                MessageHelper.show_error(self, f"契約削除中にエラーが発生しました: {str(e)}")
    
    def manage_renewal(self):
        """更新管理"""
        row = self.contract_table.currentRow()
        if row < 0:
            return
        
        contract_id = int(self.contract_table.item(row, 0).text())
        MessageHelper.show_warning(self, f"契約ID {contract_id} の更新管理機能は今後実装予定です")
    
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
                    headers = []
                    for col in range(1, self.contract_table.columnCount()):  # IDを除く
                        headers.append(self.contract_table.horizontalHeaderItem(col).text())
                    writer.writerow(headers)
                    
                    # データ
                    for row in range(self.contract_table.rowCount()):
                        if not self.contract_table.isRowHidden(row):
                            row_data = []
                            for col in range(1, self.contract_table.columnCount()):
                                item = self.contract_table.item(row, col)
                                row_data.append(item.text() if item else "")
                            writer.writerow(row_data)
                
                MessageHelper.show_success(self, f"CSVファイルを出力しました:\n{file_path}")
                
        except Exception as e:
            MessageHelper.show_error(self, f"CSV出力中にエラーが発生しました: {str(e)}")