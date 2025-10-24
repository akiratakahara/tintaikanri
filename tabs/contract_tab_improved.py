"""
改良版契約管理タブ - 書類管理・更新期限管理・手続きログ機能付き
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QPushButton, QLabel, QLineEdit,
                             QTextEdit, QMessageBox, QGroupBox, QFormLayout,
                             QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QCheckBox, QDialog,
                             QDialogButtonBox, QSplitter, QFrame, QTabWidget,
                             QTreeWidget, QTreeWidgetItem, QFileDialog, QListWidget,
                             QListWidgetItem, QProgressBar, QScrollArea, QMenu, QInputDialog)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from datetime import datetime, date, timedelta
import shutil
from models import TenantContract, Unit, Property, Customer
from utils import (Validator, TableHelper, MessageHelper, FormatHelper, 
                  SearchHelper, DateHelper, StatusColor)
from commission_manager import CommissionManager

# マウスホイール無効化SpinBox
class NoWheelSpinBox(QSpinBox):
    """マウスホイールによる値変更を無効化したSpinBox"""
    def wheelEvent(self, event):
        event.ignore()  # ホイールイベントを無視

class NoWheelDoubleSpinBox(QSpinBox):
    """マウスホイールによる値変更を無効化したDoubleSpinBox"""
    def wheelEvent(self, event):
        event.ignore()  # ホイールイベントを無視

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
        # デフォルトを「その他書類」に設定
        self.doc_type_combo.setCurrentText("その他書類")

        upload_btn = QPushButton("ファイル選択")
        upload_btn.clicked.connect(self.upload_document)

        bulk_upload_btn = QPushButton("一括アップロード")
        bulk_upload_btn.clicked.connect(self.bulk_upload_documents)
        bulk_upload_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")

        upload_layout.addWidget(QLabel("書類種別:"))
        upload_layout.addWidget(self.doc_type_combo)
        upload_layout.addWidget(upload_btn)
        upload_layout.addWidget(bulk_upload_btn)
        upload_layout.addStretch()
        
        upload_group.setLayout(upload_layout)
        layout.addWidget(upload_group)
        
        # 書類一覧
        self.document_list = QListWidget()
        self.document_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)  # 複数選択可能
        self.document_list.itemDoubleClicked.connect(self.open_document)
        self.document_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.document_list.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(QLabel("保管書類一覧（複数選択可、右クリックでメニュー）"))
        layout.addWidget(self.document_list)
        
        # 書類操作ボタン
        doc_button_layout = QHBoxLayout()

        open_btn = QPushButton("開く")
        open_btn.clicked.connect(self.open_selected_document)

        edit_type_btn = QPushButton("種別変更")
        edit_type_btn.clicked.connect(self.edit_document_type)
        edit_type_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; }")

        delete_btn = QPushButton("削除")
        delete_btn.clicked.connect(self.delete_document)
        delete_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")

        doc_button_layout.addWidget(open_btn)
        doc_button_layout.addWidget(edit_type_btn)
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

    def bulk_upload_documents(self):
        """複数の書類を一括アップロード"""
        if not self.contract_id:
            MessageHelper.show_warning(self, "先に契約を保存してから書類をアップロードしてください")
            return

        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "書類ファイルを選択（複数選択可）", "",
            "All Files (*);;PDF Files (*.pdf);;Image Files (*.png *.jpg *.jpeg)"
        )

        if file_paths:
            try:
                doc_type = self.doc_type_combo.currentText()
                success_count = 0
                error_count = 0

                for file_path in file_paths:
                    try:
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

                        success_count += 1

                    except Exception as e:
                        print(f"ファイルアップロードエラー ({original_name}): {e}")
                        error_count += 1

                # 結果を表示
                if success_count > 0:
                    self.load_documents()

                if error_count == 0:
                    MessageHelper.show_success(self, f"{success_count}件の書類をアップロードしました")
                else:
                    MessageHelper.show_warning(self, f"{success_count}件成功、{error_count}件失敗しました")

            except Exception as e:
                MessageHelper.show_error(self, f"一括アップロード中にエラーが発生しました: {str(e)}")
    
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
                SELECT id, document_type, filename, file_path, uploaded_at
                FROM contract_documents
                WHERE contract_id = ?
                ORDER BY uploaded_at DESC
            ''', (self.contract_id,))

            documents = cursor.fetchall()
            conn.close()

            for doc in documents:
                doc_id, doc_type, filename, file_path, uploaded_at = doc

                item = QListWidgetItem()
                item.setText(f"[{doc_type}] {filename}")
                # UserRoleにfile_path、UserRole+1にdoc_id、UserRole+2にdoc_typeを保存
                item.setData(Qt.ItemDataRole.UserRole, file_path)
                item.setData(Qt.ItemDataRole.UserRole + 1, doc_id)
                item.setData(Qt.ItemDataRole.UserRole + 2, doc_type)

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
        """書類を削除（複数選択対応）"""
        selected_items = self.document_list.selectedItems()
        if not selected_items:
            MessageHelper.show_warning(self, "削除する書類を選択してください")
            return

        count = len(selected_items)
        if MessageHelper.confirm_delete(self, f"{count}件の書類"):
            try:
                import sqlite3
                conn = sqlite3.connect("tintai_management.db")
                cursor = conn.cursor()

                success_count = 0
                error_count = 0

                for item in selected_items:
                    try:
                        file_path = item.data(Qt.ItemDataRole.UserRole)
                        doc_id = item.data(Qt.ItemDataRole.UserRole + 1)

                        # ファイル削除
                        if file_path and os.path.exists(file_path):
                            os.remove(file_path)

                        # データベースから削除
                        cursor.execute('''
                            DELETE FROM contract_documents
                            WHERE id = ?
                        ''', (doc_id,))

                        success_count += 1

                    except Exception as e:
                        print(f"書類削除エラー: {e}")
                        error_count += 1

                conn.commit()
                conn.close()

                if error_count == 0:
                    MessageHelper.show_success(self, f"{success_count}件の書類を削除しました")
                else:
                    MessageHelper.show_warning(self, f"{success_count}件成功、{error_count}件失敗しました")

                self.load_documents()

            except Exception as e:
                MessageHelper.show_error(self, f"書類削除中にエラーが発生しました: {str(e)}")

    def show_context_menu(self, position):
        """右クリックメニューを表示"""
        selected_items = self.document_list.selectedItems()
        if not selected_items:
            return

        menu = QMenu(self)

        # 開く
        if len(selected_items) == 1:
            open_action = menu.addAction("📂 開く")
            open_action.triggered.connect(self.open_selected_document)
        else:
            open_action = menu.addAction(f"📂 開く ({len(selected_items)}件)")
            open_action.triggered.connect(self.open_multiple_documents)

        menu.addSeparator()

        # 種別変更
        if len(selected_items) == 1:
            edit_type_action = menu.addAction("✏️ 種別変更")
            edit_type_action.triggered.connect(self.edit_document_type)

        # 削除
        delete_action = menu.addAction(f"🗑️ 削除 ({len(selected_items)}件)")
        delete_action.triggered.connect(self.delete_document)

        # メニューを表示
        menu.exec(self.document_list.mapToGlobal(position))

    def open_multiple_documents(self):
        """複数の書類を開く"""
        selected_items = self.document_list.selectedItems()
        for item in selected_items:
            self.open_document(item)

    def edit_document_type(self):
        """書類種別を変更"""
        current_item = self.document_list.currentItem()
        if not current_item:
            MessageHelper.show_warning(self, "種別を変更する書類を選択してください")
            return

        doc_id = current_item.data(Qt.ItemDataRole.UserRole + 1)
        current_type = current_item.data(Qt.ItemDataRole.UserRole + 2)

        # 書類種別選択ダイアログ
        doc_types = [
            "契約書", "重要事項説明書", "申込書", "身分証明書",
            "収入証明書", "保証人関連書類", "火災保険証券",
            "その他書類"
        ]

        new_type, ok = QInputDialog.getItem(
            self, "書類種別変更",
            f"現在の種別: {current_type}\n\n新しい書類種別を選択してください:",
            doc_types, 0, False
        )

        if ok and new_type:
            try:
                # データベースの書類種別を更新
                import sqlite3
                conn = sqlite3.connect("tintai_management.db")
                cursor = conn.cursor()

                cursor.execute('''
                    UPDATE contract_documents
                    SET document_type = ?
                    WHERE id = ?
                ''', (new_type, doc_id))

                conn.commit()
                conn.close()

                MessageHelper.show_success(self, f"書類種別を「{current_type}」から「{new_type}」に変更しました")
                self.load_documents()

            except Exception as e:
                MessageHelper.show_error(self, f"書類種別変更中にエラーが発生しました: {str(e)}")
    
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

class ScheduleEditDialog(QDialog):
    """スケジュール編集ダイアログ"""

    def __init__(self, parent=None, item_data=None):
        super().__init__(parent)
        self.item_data = item_data
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("スケジュール編集")
        self.setModal(True)
        self.resize(400, 200)

        layout = QFormLayout()

        # 項目名（読み取り専用）
        self.item_label = QLabel(self.item_data.get('name', ''))
        self.item_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        # 予定日
        self.scheduled_date_edit = QDateEdit()
        self.scheduled_date_edit.setCalendarPopup(True)
        scheduled_date = self.item_data.get('scheduled')
        if isinstance(scheduled_date, date):
            self.scheduled_date_edit.setDate(QDate(scheduled_date))
        else:
            self.scheduled_date_edit.setDate(QDate.currentDate())

        # 期限日
        self.deadline_date_edit = QDateEdit()
        self.deadline_date_edit.setCalendarPopup(True)
        deadline_date = self.item_data.get('deadline')
        if isinstance(deadline_date, date):
            self.deadline_date_edit.setDate(QDate(deadline_date))
        else:
            self.deadline_date_edit.setDate(QDate.currentDate())

        layout.addRow("項目:", self.item_label)
        layout.addRow("予定日:", self.scheduled_date_edit)
        layout.addRow("期限日:", self.deadline_date_edit)

        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addRow(button_box)
        self.setLayout(layout)

    def get_data(self):
        """入力データを取得"""
        return {
            'scheduled': self.scheduled_date_edit.date().toPyDate(),
            'deadline': self.deadline_date_edit.date().toPyDate()
        }

class RenewalManager(QWidget):
    """契約更新管理ウィジェット"""
    
    # タスク完了時のシグナル
    task_completed = pyqtSignal()
    
    def __init__(self, contract_data=None):
        super().__init__()
        self.contract_data = contract_data
        self.custom_schedule = {}  # カスタムスケジュールを保存
        self.init_ui()
        if contract_data:
            self.calculate_renewal_schedule()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 契約情報表示
        info_group = QGroupBox("契約更新・解約通知情報")
        info_layout = QFormLayout()

        self.contract_end_label = QLabel("未設定")
        self.days_remaining_label = QLabel("未設定")
        self.owner_cancellation_deadline_label = QLabel("未設定")
        self.tenant_cancellation_deadline_label = QLabel("未設定")
        self.renewal_deadline_label = QLabel("未設定")
        self.renewal_status_label = QLabel("未設定")

        info_layout.addRow("契約終了日:", self.contract_end_label)
        info_layout.addRow("残り日数:", self.days_remaining_label)
        info_layout.addRow("貸主（甲）解約通知期限:", self.owner_cancellation_deadline_label)
        info_layout.addRow("借主（乙）解約通知期限:", self.tenant_cancellation_deadline_label)
        info_layout.addRow("更新手続き期限:", self.renewal_deadline_label)
        info_layout.addRow("更新ステータス:", self.renewal_status_label)

        info_group.setLayout(info_layout)
        
        # 更新スケジュール
        schedule_group = QGroupBox("更新手続きスケジュール")
        self.schedule_tree = QTreeWidget()
        self.schedule_tree.setHeaderLabels(["項目", "予定日", "期限", "ステータス"])
        self.schedule_tree.itemDoubleClicked.connect(self.edit_schedule_item)

        schedule_layout = QVBoxLayout()
        schedule_layout.addWidget(self.schedule_tree)

        # スケジュール編集ボタン
        schedule_button_layout = QHBoxLayout()
        self.edit_schedule_btn = QPushButton("📝 スケジュール編集")
        self.edit_schedule_btn.clicked.connect(self.edit_selected_schedule)
        self.reset_schedule_btn = QPushButton("🔄 デフォルトに戻す")
        self.reset_schedule_btn.clicked.connect(self.reset_schedule)

        schedule_button_layout.addWidget(self.edit_schedule_btn)
        schedule_button_layout.addWidget(self.reset_schedule_btn)
        schedule_button_layout.addStretch()

        schedule_layout.addLayout(schedule_button_layout)
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
            
            # 貸主（甲）解約通知期限
            owner_cancellation_days = self.contract_data.get('owner_cancellation_notice_days', 180)
            owner_cancellation_deadline = end_date - timedelta(days=owner_cancellation_days)
            self.owner_cancellation_deadline_label.setText(
                DateHelper.format_date(owner_cancellation_deadline, "%Y年%m月%d日") +
                f" (契約満了の{self._days_to_relative_text(owner_cancellation_days)}前)"
            )

            # 借主（乙）解約通知期限
            tenant_cancellation_days = self.contract_data.get('tenant_cancellation_notice_days', 30)
            tenant_cancellation_deadline = end_date - timedelta(days=tenant_cancellation_days)
            self.tenant_cancellation_deadline_label.setText(
                DateHelper.format_date(tenant_cancellation_deadline, "%Y年%m月%d日") +
                f" (契約満了の{self._days_to_relative_text(tenant_cancellation_days)}前)"
            )

            # 更新手続き期限
            renewal_deadline_days = self.contract_data.get('renewal_deadline_days', 30)
            renewal_deadline = end_date - timedelta(days=renewal_deadline_days)
            self.renewal_deadline_label.setText(
                DateHelper.format_date(renewal_deadline, "%Y年%m月%d日") +
                f" (契約満了の{self._days_to_relative_text(renewal_deadline_days)}前)"
            )

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

        # 契約データから解約通知期限と更新手続き期限を取得
        owner_cancellation_days = self.contract_data.get('owner_cancellation_notice_days', 180)
        tenant_cancellation_days = self.contract_data.get('tenant_cancellation_notice_days', 30)
        renewal_deadline_days = self.contract_data.get('renewal_deadline_days', 30)

        # より長い解約通知期限を基準にスケジュールを作成
        notice_start_days = max(owner_cancellation_days, tenant_cancellation_days)

        # 標準的な更新スケジュール（契約設定に基づいて計算）
        default_schedule = [
            ("更新通知送付", end_date - timedelta(days=notice_start_days), end_date - timedelta(days=notice_start_days - 30)),
            ("更新意思確認", end_date - timedelta(days=notice_start_days - 30), end_date - timedelta(days=renewal_deadline_days + 30)),
            ("更新契約書作成", end_date - timedelta(days=renewal_deadline_days + 30), end_date - timedelta(days=renewal_deadline_days)),
            ("契約書締結", end_date - timedelta(days=renewal_deadline_days), end_date - timedelta(days=1)),
            ("新契約開始", end_date, end_date + timedelta(days=1))
        ]

        # 契約IDを取得
        contract_id = self.contract_data.get('id') if self.contract_data else None

        for item_name, default_scheduled, default_deadline in default_schedule:
            # カスタムスケジュールがあればそちらを優先
            if item_name in self.custom_schedule:
                scheduled_date = self.custom_schedule[item_name]['scheduled']
                deadline_date = self.custom_schedule[item_name]['deadline']
            else:
                scheduled_date = default_scheduled
                deadline_date = default_deadline

            # 契約満了日からの日数を計算
            scheduled_days_before = (end_date - scheduled_date).days
            deadline_days_before = (end_date - deadline_date).days

            item = QTreeWidgetItem()
            item.setText(0, item_name)
            # 予定日に相対表記を追加
            item.setText(1,
                DateHelper.format_date(scheduled_date, "%Y年%m月%d日") +
                f" (満了の{self._days_to_relative_text(scheduled_days_before)}前)"
            )
            # 期限に相対表記を追加
            item.setText(2,
                DateHelper.format_date(deadline_date, "%Y年%m月%d日") +
                f" (満了の{self._days_to_relative_text(deadline_days_before)}前)"
            )
            # データを保存（編集時に使用）
            item.setData(0, Qt.ItemDataRole.UserRole, {
                'name': item_name,
                'scheduled': scheduled_date,
                'deadline': deadline_date
            })
            
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

    def _days_to_relative_text(self, days):
        """日数を分かりやすい相対表記に変換"""
        if days == 365:
            return "1年"
        elif days == 180:
            return "6ヶ月"
        elif days == 90:
            return "3ヶ月"
        elif days == 60:
            return "2ヶ月"
        elif days == 45:
            return "45日"
        elif days == 30:
            return "1ヶ月"
        elif days == 21:
            return "3週間"
        elif days == 14:
            return "2週間"
        elif days == 7:
            return "1週間"
        else:
            return f"{days}日"

    def edit_schedule_item(self, item, column):
        """スケジュール項目をダブルクリックで編集"""
        self.edit_selected_schedule()

    def edit_selected_schedule(self):
        """選択されたスケジュール項目を編集"""
        current_item = self.schedule_tree.currentItem()
        if not current_item:
            MessageHelper.show_warning(self, "編集する項目を選択してください")
            return

        item_data = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not item_data:
            return

        # 編集ダイアログを表示
        dialog = ScheduleEditDialog(self, item_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_data()
            # カスタムスケジュールに保存
            self.custom_schedule[item_data['name']] = {
                'scheduled': new_data['scheduled'],
                'deadline': new_data['deadline']
            }
            # スケジュールを再描画
            self.calculate_renewal_schedule()
            MessageHelper.show_success(self, "スケジュールを更新しました")

    def reset_schedule(self):
        """スケジュールをデフォルトに戻す"""
        reply = QMessageBox.question(
            self,
            "確認",
            "スケジュールをデフォルトに戻しますか？\nカスタム設定は失われます。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.custom_schedule.clear()
            self.calculate_renewal_schedule()
            MessageHelper.show_success(self, "スケジュールをデフォルトに戻しました")

class ContractEditDialog(QDialog):
    """契約編集ダイアログ"""
    
    def __init__(self, parent=None, contract_data=None):
        super().__init__(parent)
        self.contract_data = contract_data
        self.init_ui()
        if contract_data:
            self.load_contract_data()
    
    def load_tenants_to_combo(self):
        """テナント（借主）データをコンボボックスに読み込み"""
        try:
            self.tenant_combo.clear()
            self.tenant_combo.addItem("--- テナントを選択 ---", "")
            
            customers = Customer.get_all()
            for customer in customers:
                if customer.get('type') == 'tenant':
                    display_name = customer.get('name', '')
                    if customer.get('phone'):
                        display_name += f" ({customer['phone']})"
                    self.tenant_combo.addItem(display_name, customer.get('id'))
                
        except Exception as e:
            print(f"テナントデータ読み込みエラー: {e}")
            # エラー時はダミーデータを表示
            self.tenant_combo.addItem("サンプルテナントA (090-1234-5678)", 1)
            self.tenant_combo.addItem("サンプルテナントB (080-9876-5432)", 2)
    
    def load_owners_to_combo(self):
        """オーナー（貸主）データをコンボボックスに読み込み"""
        try:
            self.owner_combo.clear()
            self.owner_combo.addItem("--- オーナーを選択 ---", "")
            
            customers = Customer.get_all()
            for customer in customers:
                if customer.get('type') == 'owner':
                    display_name = customer.get('name', '')
                    if customer.get('phone'):
                        display_name += f" ({customer['phone']})"
                    self.owner_combo.addItem(display_name, customer.get('id'))
                
        except Exception as e:
            print(f"オーナーデータ読み込みエラー: {e}")
            # エラー時はダミーデータを表示
            self.owner_combo.addItem("サンプルオーナーA (090-1111-2222)", 1)
            self.owner_combo.addItem("サンプルオーナーB (080-3333-4444)", 2)
    
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
        layout = QVBoxLayout()  # FormLayoutからVBoxLayoutに変更

        # OCRアップロードセクション（新規契約時のみ表示）
        if not self.contract_data:
            ocr_section = QGroupBox("契約書から自動入力")
            ocr_layout = QHBoxLayout()

            ocr_label = QLabel("契約書ファイルをアップロードして情報を自動抽出:\n※Word形式が最も正確です。PDFやスキャン画像も対応しています。")
            ocr_label.setWordWrap(True)
            self.ocr_upload_btn = QPushButton("📄 契約書をアップロード")
            self.ocr_upload_btn.clicked.connect(self.upload_and_ocr_contract)

            ocr_layout.addWidget(ocr_label)
            ocr_layout.addWidget(self.ocr_upload_btn)
            ocr_layout.addStretch()

            ocr_section.setLayout(ocr_layout)
            layout.addWidget(ocr_section)

        # フォーム用のコンテナ
        form_container = QWidget()
        form_layout = QFormLayout(form_container)

        # 物件・部屋選択セクション
        property_section = QGroupBox("物件・部屋選択")
        property_layout = QFormLayout()
        
        # 物件選択
        self.property_combo = QComboBox()
        self.property_combo.currentTextChanged.connect(self.on_property_changed)
        self.load_properties()
        
        # 部屋選択
        self.unit_combo = QComboBox()
        self.unit_combo.currentTextChanged.connect(self.on_unit_changed)
        
        # 物件全体選択チェックボックス
        self.whole_property_check = QCheckBox("物件全体を借り受ける（一棟貸し）")
        self.whole_property_check.toggled.connect(self.on_whole_property_toggled)
        
        property_layout.addRow("物件 *:", self.property_combo)
        property_layout.addRow("部屋:", self.unit_combo)
        property_layout.addRow("", self.whole_property_check)
        property_section.setLayout(property_layout)
        
        # 契約者選択セクション
        contractor_section = QGroupBox("契約者情報")
        contractor_layout = QFormLayout()
        
        # 仲介種別選択
        self.mediation_type_combo = QComboBox()
        self.mediation_type_combo.addItems(["片手仲介", "両手仲介"])
        self.mediation_type_combo.currentTextChanged.connect(self.on_mediation_type_changed)
        
        # 片手仲介時の当事者選択
        self.party_type_combo = QComboBox()
        self.party_type_combo.addItems(["テナント（借主）", "オーナー（貸主）"])
        self.party_type_combo.currentTextChanged.connect(self.on_party_type_changed)
        self.party_type_combo.setVisible(True)  # 片手仲介時は表示
        
        # テナント（借主）選択
        self.tenant_combo = QComboBox()
        self.tenant_combo.setEditable(True)  # 手動入力も可能
        self.tenant_combo.setMaximumWidth(300)
        self.load_tenants_to_combo()
        
        # オーナー（貸主）選択
        self.owner_combo = QComboBox()
        self.owner_combo.setEditable(True)  # 手動入力も可能
        self.owner_combo.setMaximumWidth(300)
        self.load_owners_to_combo()

        # 借主電話番号（顧客登録していない借主用）
        self.tenant_phone_edit = QLineEdit()
        self.tenant_phone_edit.setPlaceholderText("例: 090-1234-5678")
        self.tenant_phone_edit.setMaximumWidth(200)

        contractor_layout.addRow("仲介種別 *:", self.mediation_type_combo)
        contractor_layout.addRow("当事者選択:", self.party_type_combo)
        contractor_layout.addRow("テナント（借主）*:", self.tenant_combo)
        contractor_layout.addRow("借主電話番号:", self.tenant_phone_edit)
        contractor_layout.addRow("オーナー（貸主）*:", self.owner_combo)
        contractor_section.setLayout(contractor_layout)
        
        # 契約種別
        self.contract_type_combo = QComboBox()
        self.contract_type_combo.addItems(["普通借家契約", "定期借家契約"])

        # 契約ステータス
        self.contract_status_combo = QComboBox()
        self.contract_status_combo.addItem("下書き", "draft")
        self.contract_status_combo.addItem("申込中（申込あり）", "pending")
        self.contract_status_combo.addItem("契約中（賃貸中）", "active")
        self.contract_status_combo.addItem("期限切れ", "expired")
        self.contract_status_combo.addItem("解約済み", "cancelled")
        self.contract_status_combo.setCurrentIndex(2)  # デフォルト: 契約中（active）
        self.contract_status_combo.setToolTip("契約の現在の状態を選択してください")

        # 契約期間
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate())
        
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate().addYears(2))
        
        # 賃料関連（マウスホイール無効化版）
        self.rent_spin = NoWheelSpinBox()
        self.rent_spin.setMaximum(9999999)
        self.rent_spin.setSuffix(" 円")

        self.maintenance_fee_spin = NoWheelSpinBox()
        self.maintenance_fee_spin.setMaximum(999999)
        self.maintenance_fee_spin.setSuffix(" 円")

        self.security_deposit_spin = NoWheelSpinBox()
        self.security_deposit_spin.setMaximum(9999999)
        self.security_deposit_spin.setSuffix(" 円")

        self.key_money_spin = NoWheelSpinBox()
        self.key_money_spin.setMaximum(9999999)
        self.key_money_spin.setSuffix(" 円")
        
        # 更新関連
        self.renewal_method_combo = QComboBox()
        self.renewal_method_combo.addItems(["自動更新", "合意更新", "定期契約（更新なし）"])
        
        self.renewal_fee_spin = NoWheelSpinBox()
        self.renewal_fee_spin.setMaximum(999999)
        self.renewal_fee_spin.setSuffix(" 円")
        
        # 保険・保証関連
        self.insurance_flag_check = QCheckBox("火災保険加入")
        self.guarantee_company_edit = QLineEdit()
        
        # 解約通知期限設定（甲乙別）
        # 貸主（甲・オーナー）からの解約通知期限
        self.owner_cancellation_notice_combo = QComboBox()
        self.owner_cancellation_notice_combo.addItem("契約満了の1年前", 365)
        self.owner_cancellation_notice_combo.addItem("契約満了の6ヶ月前", 180)
        self.owner_cancellation_notice_combo.addItem("契約満了の3ヶ月前", 90)
        self.owner_cancellation_notice_combo.addItem("契約満了の2ヶ月前", 60)
        self.owner_cancellation_notice_combo.addItem("契約満了の1ヶ月前", 30)
        self.owner_cancellation_notice_combo.setCurrentIndex(1)  # デフォルト: 6ヶ月前（180日）
        self.owner_cancellation_notice_combo.setToolTip("貸主（オーナー）が解約する場合の通知期限")

        # 借主（乙・テナント）からの解約通知期限
        self.tenant_cancellation_notice_combo = QComboBox()
        self.tenant_cancellation_notice_combo.addItem("契約満了の3ヶ月前", 90)
        self.tenant_cancellation_notice_combo.addItem("契約満了の2ヶ月前", 60)
        self.tenant_cancellation_notice_combo.addItem("契約満了の1ヶ月前", 30)
        self.tenant_cancellation_notice_combo.addItem("契約満了の3週間前", 21)
        self.tenant_cancellation_notice_combo.addItem("契約満了の2週間前", 14)
        self.tenant_cancellation_notice_combo.addItem("契約満了の1週間前", 7)
        self.tenant_cancellation_notice_combo.setCurrentIndex(2)  # デフォルト: 1ヶ月前（30日）
        self.tenant_cancellation_notice_combo.setToolTip("借主（テナント）が解約する場合の通知期限")

        # 更新通知期限（タスク作成用）
        self.renewal_notice_period_combo = QComboBox()
        self.renewal_notice_period_combo.addItem("契約満了の4ヶ月前", 120)
        self.renewal_notice_period_combo.addItem("契約満了の3ヶ月前", 90)
        self.renewal_notice_period_combo.addItem("契約満了の2ヶ月前", 60)
        self.renewal_notice_period_combo.addItem("契約満了の1ヶ月前", 30)
        self.renewal_notice_period_combo.setCurrentIndex(1)  # デフォルト: 2ヶ月前（60日）
        self.renewal_notice_period_combo.setToolTip("更新案内を開始すべき期限（タスク作成用）")

        # 更新手続き期限
        self.renewal_deadline_period_combo = QComboBox()
        self.renewal_deadline_period_combo.addItem("契約満了の2ヶ月前", 60)
        self.renewal_deadline_period_combo.addItem("契約満了の1ヶ月前", 30)
        self.renewal_deadline_period_combo.addItem("契約満了の3週間前", 21)
        self.renewal_deadline_period_combo.addItem("契約満了の2週間前", 14)
        self.renewal_deadline_period_combo.setCurrentIndex(1)  # デフォルト: 1ヶ月前（30日）
        self.renewal_deadline_period_combo.setToolTip("更新手続きを完了すべき期限")

        self.auto_create_tasks_check = QCheckBox("自動でタスクを作成")
        self.auto_create_tasks_check.setChecked(True)
        self.auto_create_tasks_check.setToolTip("契約登録時に更新通知タスクを自動作成する")

        # 更新・期間条件（自由記入欄）
        self.renewal_terms_edit = QTextEdit()
        self.renewal_terms_edit.setMinimumHeight(80)
        self.renewal_terms_edit.setPlaceholderText("契約書に記載されている更新や契約期間に関する条件を入力してください\n例：本契約は2年間の定期借家契約とし、更新はありません。")

        # 特記事項
        self.memo_edit = QTextEdit()
        self.memo_edit.setMinimumHeight(80)
        self.memo_edit.setPlaceholderText("その他特記事項を入力してください")

        # 注意事項（自由記入欄・一覧表示用）
        self.notes_edit = QTextEdit()
        self.notes_edit.setMinimumHeight(80)
        self.notes_edit.setPlaceholderText("契約に関する重要な注意事項を入力してください\n（例：ペット不可、楽器不可、夜間騒音注意など）")

        # セクションをフォームレイアウトに追加
        form_layout.addRow(property_section)
        form_layout.addRow(contractor_section)
        
        # 契約詳細セクション
        contract_section = QGroupBox("契約詳細")
        contract_layout = QFormLayout()
        
        contract_layout.addRow("契約種別:", self.contract_type_combo)
        contract_layout.addRow("契約ステータス *:", self.contract_status_combo)
        contract_layout.addRow("契約開始日:", self.start_date_edit)
        contract_layout.addRow("契約終了日:", self.end_date_edit)
        contract_layout.addRow("賃料:", self.rent_spin)
        contract_layout.addRow("管理費:", self.maintenance_fee_spin)
        contract_layout.addRow("敷金:", self.security_deposit_spin)
        contract_layout.addRow("礼金:", self.key_money_spin)
        contract_layout.addRow("更新方法:", self.renewal_method_combo)
        contract_layout.addRow("更新料:", self.renewal_fee_spin)
        contract_layout.addRow("保険:", self.insurance_flag_check)
        contract_layout.addRow("保証会社:", self.guarantee_company_edit)
        
        contract_section.setLayout(contract_layout)
        
        # 解約・更新通知設定セクション
        renewal_section = QGroupBox("解約・更新通知設定")
        renewal_layout = QFormLayout()

        renewal_layout.addRow("貸主（甲）解約通知期限:", self.owner_cancellation_notice_combo)
        renewal_layout.addRow("借主（乙）解約通知期限:", self.tenant_cancellation_notice_combo)
        renewal_layout.addRow("更新通知期限:", self.renewal_notice_period_combo)
        renewal_layout.addRow("更新手続き期限:", self.renewal_deadline_period_combo)
        renewal_layout.addRow("", self.auto_create_tasks_check)
        renewal_layout.addRow("更新・期間条件:", self.renewal_terms_edit)

        renewal_section.setLayout(renewal_layout)
        
        # 特記事項セクション
        memo_section = QGroupBox("特記事項")
        memo_layout = QFormLayout()
        memo_layout.addRow("", self.memo_edit)
        memo_section.setLayout(memo_layout)

        # 注意事項セクション
        notes_section = QGroupBox("注意事項")
        notes_layout = QFormLayout()
        notes_layout.addRow("", self.notes_edit)
        notes_section.setLayout(notes_layout)

        # すべてのセクションをフォームレイアウトに追加
        form_layout.addRow(contract_section)
        form_layout.addRow(renewal_section)
        form_layout.addRow(memo_section)
        form_layout.addRow(notes_section)

        # フォームコンテナをメインレイアウトに追加
        layout.addWidget(form_container)

        tab.setLayout(layout)
        return tab
    
    def load_properties(self):
        """物件一覧を読み込み"""
        self.property_combo.clear()
        self.property_combo.addItem("物件を選択", None)
        
        try:
            properties = Property.get_all()
            for property_data in properties:
                display_text = f"{property_data['name']} ({property_data.get('address', '')})"
                self.property_combo.addItem(display_text, property_data['id'])
        except Exception as e:
            print(f"物件読み込みエラー: {e}")
    
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
    
    def load_units_by_property(self, property_id):
        """指定物件の部屋一覧を読み込み"""
        self.unit_combo.clear()
        self.unit_combo.addItem("部屋を選択", None)
        
        if not property_id:
            return
            
        try:
            units = Unit.get_by_property(property_id)
            for unit in units:
                display_text = f"{unit['room_number']}"
                self.unit_combo.addItem(display_text, unit['id'])
        except Exception as e:
            print(f"部屋読み込みエラー: {e}")
    
    def on_property_changed(self, property_text):
        """物件選択変更時の処理"""
        # unit_comboが初期化されているかチェック
        if not hasattr(self, 'unit_combo'):
            return
            
        if property_text == "物件を選択":
            self.unit_combo.clear()
            self.unit_combo.addItem("部屋を選択", None)
            return
            
        property_id = self.property_combo.currentData()
        if property_id:
            self.load_units_by_property(property_id)
    
    def on_unit_changed(self, unit_text):
        """部屋選択変更時の処理"""
        # 部屋選択時の特別な処理があればここに追加
        pass
    
    def on_whole_property_toggled(self, checked):
        """物件全体選択チェックボックスの処理"""
        # unit_comboが初期化されているかチェック
        if not hasattr(self, 'unit_combo'):
            return
            
        if checked:
            # 物件全体選択時は部屋選択を無効化
            self.unit_combo.setEnabled(False)
            self.unit_combo.clear()
            self.unit_combo.addItem("物件全体", None)
        else:
            # 部屋選択を有効化
            self.unit_combo.setEnabled(True)
            property_id = self.property_combo.currentData()
            if property_id:
                self.load_units_by_property(property_id)
    
    def on_mediation_type_changed(self, mediation_type):
        """仲介種別変更時の処理"""
        # 必要なコンボボックスが初期化されているかチェック
        if not hasattr(self, 'party_type_combo') or not hasattr(self, 'tenant_combo') or not hasattr(self, 'owner_combo'):
            return
            
        if mediation_type == "両手仲介":
            # 両手仲介時は当事者選択を非表示、両方のコンボボックスを表示
            self.party_type_combo.setVisible(False)
            self.tenant_combo.setVisible(True)
            self.owner_combo.setVisible(True)
            # 両方必須にする
            self.tenant_combo.setStyleSheet("QComboBox { border: 2px solid #ff9800; }")
            self.owner_combo.setStyleSheet("QComboBox { border: 2px solid #ff9800; }")
        else:
            # 片手仲介時は当事者選択を表示
            self.party_type_combo.setVisible(True)
            self.on_party_type_changed(self.party_type_combo.currentText())
    
    def on_party_type_changed(self, party_type):
        """当事者選択変更時の処理"""
        # 必要なコンボボックスが初期化されているかチェック
        if not hasattr(self, 'tenant_combo') or not hasattr(self, 'owner_combo'):
            return

        # テナント、オーナー、借主電話番号は常に表示
        self.tenant_combo.setVisible(True)
        self.owner_combo.setVisible(True)
        if hasattr(self, 'tenant_phone_edit'):
            self.tenant_phone_edit.setVisible(True)

        if party_type == "テナント（借主）":
            # テナント側代理：テナントが顧客
            self.tenant_combo.setStyleSheet("QComboBox { border: 2px solid #ff9800; }")
            self.owner_combo.setStyleSheet("")
        else:
            # オーナー側代理：オーナーが顧客、テナントは手入力可能
            self.tenant_combo.setStyleSheet("")
            self.owner_combo.setStyleSheet("QComboBox { border: 2px solid #ff9800; }")
    
    def _set_unit(self, unit_id):
        """部屋を設定するヘルパーメソッド"""
        for i in range(self.unit_combo.count()):
            if self.unit_combo.itemData(i) == unit_id:
                self.unit_combo.setCurrentIndex(i)
                break

    def load_contract_data(self):
        """契約データを読み込み"""
        if not self.contract_data:
            return

        # 基本情報設定
        # 物件・部屋設定（先に設定する必要がある）
        unit_id = self.contract_data.get('unit_id')
        property_id = self.contract_data.get('property_id')

        # 物件を設定
        if property_id:
            for i in range(self.property_combo.count()):
                if self.property_combo.itemData(i) == property_id:
                    self.property_combo.setCurrentIndex(i)
                    # 物件選択により部屋リストが更新される
                    break

        # 部屋を設定（物件選択後に設定）
        if unit_id:
            # 少し待ってから部屋を設定（物件変更イベントが完了するまで）
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, lambda: self._set_unit(unit_id))

        # 既存契約者名・借主名をコンボボックスに設定
        existing_contractor = self.contract_data.get('contractor_name', '')
        existing_tenant = self.contract_data.get('tenant_name', '')
        existing_customer_id = self.contract_data.get('customer_id')

        # customer_idから契約者がテナントかオーナーかを判定
        # customer_idがある場合、それがテナントコンボかオーナーコンボのどちらにマッチするか確認
        is_owner_customer = False
        is_tenant_customer = False

        if existing_customer_id:
            # オーナーコンボボックスでcustomer_idを検索
            for i in range(self.owner_combo.count()):
                if self.owner_combo.itemData(i) == existing_customer_id:
                    is_owner_customer = True
                    self.owner_combo.setCurrentIndex(i)
                    break

            # テナントコンボボックスでcustomer_idを検索
            if not is_owner_customer:
                for i in range(self.tenant_combo.count()):
                    if self.tenant_combo.itemData(i) == existing_customer_id:
                        is_tenant_customer = True
                        self.tenant_combo.setCurrentIndex(i)
                        break

        # customer_idで判定できなかった場合は名前で検索
        if not is_owner_customer and not is_tenant_customer:
            if existing_contractor:
                # まずテナントコンボボックスから検索
                index = self.tenant_combo.findText(existing_contractor, Qt.MatchFlag.MatchContains)
                if index >= 0:
                    self.tenant_combo.setCurrentIndex(index)
                else:
                    # オーナーコンボボックスから検索
                    index = self.owner_combo.findText(existing_contractor, Qt.MatchFlag.MatchContains)
                    if index >= 0:
                        self.owner_combo.setCurrentIndex(index)
                    else:
                        # どちらにもない場合は手入力として設定
                        self.tenant_combo.setEditText(existing_contractor)

        # 借主名（tenant_name）が存在する場合はテナントコンボボックスに追加設定
        # オーナー側代理の場合に使用される
        if existing_tenant and not is_tenant_customer:
            # テナントコンボボックスから検索
            index = self.tenant_combo.findText(existing_tenant, Qt.MatchFlag.MatchContains)
            if index >= 0:
                self.tenant_combo.setCurrentIndex(index)
            else:
                # リストにない場合は手入力として設定
                self.tenant_combo.setEditText(existing_tenant)
        
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
        self.renewal_terms_edit.setPlainText(self.contract_data.get('renewal_terms', ''))
        self.tenant_phone_edit.setText(self.contract_data.get('tenant_phone', ''))
        self.memo_edit.setPlainText(self.contract_data.get('memo', ''))
        self.notes_edit.setPlainText(self.contract_data.get('notes', ''))

        # 解約通知期限・更新手続き期限の設定（日数から適切な項目を選択）
        owner_cancellation_days = self.contract_data.get('owner_cancellation_notice_days', 180)
        for i in range(self.owner_cancellation_notice_combo.count()):
            if self.owner_cancellation_notice_combo.itemData(i) == owner_cancellation_days:
                self.owner_cancellation_notice_combo.setCurrentIndex(i)
                break

        tenant_cancellation_days = self.contract_data.get('tenant_cancellation_notice_days', 30)
        for i in range(self.tenant_cancellation_notice_combo.count()):
            if self.tenant_cancellation_notice_combo.itemData(i) == tenant_cancellation_days:
                self.tenant_cancellation_notice_combo.setCurrentIndex(i)
                break

        # 更新通知期限の設定
        renewal_notice_days = self.contract_data.get('renewal_notice_days', 60)
        for i in range(self.renewal_notice_period_combo.count()):
            if self.renewal_notice_period_combo.itemData(i) == renewal_notice_days:
                self.renewal_notice_period_combo.setCurrentIndex(i)
                break

        renewal_deadline_days = self.contract_data.get('renewal_deadline_days', 30)
        for i in range(self.renewal_deadline_period_combo.count()):
            if self.renewal_deadline_period_combo.itemData(i) == renewal_deadline_days:
                self.renewal_deadline_period_combo.setCurrentIndex(i)
                break

        # 契約ステータス設定
        contract_status = self.contract_data.get('contract_status', 'active')
        for i in range(self.contract_status_combo.count()):
            if self.contract_status_combo.itemData(i) == contract_status:
                self.contract_status_combo.setCurrentIndex(i)
                break

        # 仲介種別・当事者選択の復元
        mediation_type = self.contract_data.get('mediation_type', '片手仲介')
        if mediation_type:
            self.mediation_type_combo.setCurrentText(mediation_type)

        party_type = self.contract_data.get('party_type', 'テナント（借主）')
        if party_type:
            self.party_type_combo.setCurrentText(party_type)

        self.auto_create_tasks_check.setChecked(self.contract_data.get('auto_create_tasks', True))

        # サブタブにデータ設定
        contract_id = self.contract_data.get('id')
        if contract_id:
            self.document_tab.set_contract_id(contract_id)
            self.procedure_tab.set_contract_id(contract_id)
            self.renewal_tab.set_contract_data(self.contract_data)
            self.commission_tab.set_contract_data(self.contract_data)
    
    def get_contract_data(self):
        """入力データを取得"""
        # 物件・部屋情報の取得
        property_id = self.property_combo.currentData() if hasattr(self, 'property_combo') else None
        unit_id = self.unit_combo.currentData() if hasattr(self, 'unit_combo') else None
        is_whole_property = self.whole_property_check.isChecked() if hasattr(self, 'whole_property_check') else False
        
        # 仲介種別の取得
        mediation_type = self.mediation_type_combo.currentText() if hasattr(self, 'mediation_type_combo') else "片手仲介"
        
        # 当事者情報の取得
        customer_id = None
        tenant_name = ""  # 借主名（常に取得）
        owner_name = ""   # オーナー名

        if mediation_type == "両手仲介":
            # 両手仲介の場合はテナントとオーナー両方
            tenant_name = self.tenant_combo.currentText().strip() if hasattr(self, 'tenant_combo') else ""
            owner_name = self.owner_combo.currentText().strip() if hasattr(self, 'owner_combo') else ""
            contractor_name = tenant_name  # 契約者はテナント
            # テナントのIDを取得
            if hasattr(self, 'tenant_combo'):
                customer_id = self.tenant_combo.currentData()
        else:
            # 片手仲介の場合は当事者選択に応じて
            party_type = self.party_type_combo.currentText() if hasattr(self, 'party_type_combo') else "テナント（借主）"
            if party_type == "テナント（借主）":
                # テナント側代理：テナントが顧客
                tenant_name = self.tenant_combo.currentText().strip() if hasattr(self, 'tenant_combo') else ""
                owner_name = ""
                contractor_name = tenant_name
                # テナントのIDを取得
                if hasattr(self, 'tenant_combo'):
                    customer_id = self.tenant_combo.currentData()
            else:
                # オーナー側代理：オーナーが顧客、借主は別途入力
                tenant_name = self.tenant_combo.currentText().strip() if hasattr(self, 'tenant_combo') else ""
                owner_name = self.owner_combo.currentText().strip() if hasattr(self, 'owner_combo') else ""
                contractor_name = owner_name
                # オーナーのIDを取得
                if hasattr(self, 'owner_combo'):
                    customer_id = self.owner_combo.currentData()

        data = {
            'property_id': property_id,
            'unit_id': unit_id if not is_whole_property else None,
            'is_whole_property': is_whole_property,
            'mediation_type': mediation_type,
            'party_type': party_type if mediation_type == "片手仲介" else None,
            'contractor_name': contractor_name,
            'tenant_name': tenant_name,
            'owner_name': owner_name,
            'customer_id': customer_id,
            'contract_type': self.contract_type_combo.currentText(),
            'contract_status': self.contract_status_combo.currentData(),
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
            # 解約通知期限・更新手続き期限（ComboBoxから日数を取得）
            'owner_cancellation_notice_days': self.owner_cancellation_notice_combo.currentData(),
            'tenant_cancellation_notice_days': self.tenant_cancellation_notice_combo.currentData(),
            'renewal_notice_days': self.renewal_notice_period_combo.currentData(),
            'renewal_deadline_days': self.renewal_deadline_period_combo.currentData(),
            'auto_create_tasks': self.auto_create_tasks_check.isChecked(),
            'renewal_terms': self.renewal_terms_edit.toPlainText().strip(),
            'tenant_phone': self.tenant_phone_edit.text().strip(),
            'memo': self.memo_edit.toPlainText().strip(),
            'notes': self.notes_edit.toPlainText().strip()
        }
        
        # 手数料データを追加
        commission_data = self.commission_tab.get_commission_data()
        data.update(commission_data)
        
        return data

    def upload_and_ocr_contract(self):
        """契約書をアップロードしてOCR処理"""
        try:
            from contract_ocr import ContractOCR
            from PyQt6.QtWidgets import QFileDialog, QProgressDialog
            from PyQt6.QtCore import QCoreApplication

            # ファイル選択ダイアログ
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "契約書ファイルを選択",
                "",
                "契約書ファイル (*.pdf *.docx *.doc);;PDFファイル (*.pdf);;Wordファイル (*.docx *.doc);;すべてのファイル (*.*)"
            )

            if not file_path:
                return

            # プログレスダイアログ表示
            progress = QProgressDialog("契約書を読み取り中...", None, 0, 0, self)
            progress.setWindowTitle("ファイル読み取り中")
            progress.setModal(True)
            progress.show()
            QCoreApplication.processEvents()

            # OCR実行
            ocr = ContractOCR()

            # 利用可能な機能をチェック
            has_basic = ocr.pdfplumber_available
            has_ocr = ocr.tesseract_available and ocr.pdf2image_available

            if not has_basic and not has_ocr:
                progress.close()
                MessageHelper.show_error(
                    self,
                    "PDF読み取りに必要なライブラリがインストールされていません\n\n"
                    "以下のコマンドでインストールしてください:\n"
                    "pip install pdfplumber pytesseract pdf2image Pillow opencv-python"
                )
                return

            # 契約情報を抽出
            info = ocr.extract_contract_info(file_path)
            progress.close()

            # 抽出した情報をフォームに自動入力
            self._fill_form_from_ocr(info)

            MessageHelper.show_success(
                self,
                f"契約書から情報を抽出しました\n\n"
                f"抽出件数: {sum(1 for v in info.values() if v)}/{len(info)}\n\n"
                f"内容を確認して、必要に応じて修正してください"
            )

        except ImportError as e:
            MessageHelper.show_error(
                self,
                f"OCRモジュールの読み込みエラー:\n{e}\n\n"
                f"contract_ocr.py が見つかりません"
            )
        except Exception as e:
            MessageHelper.show_error(self, f"OCR処理エラー:\n{e}")

    def _fill_form_from_ocr(self, info):
        """OCRで抽出した情報をフォームに入力"""
        # 契約者名
        if info.get('contractor_name'):
            self.tenant_combo.setEditText(info['contractor_name'])

        # 物件住所（完全一致する物件を探す）
        if info.get('property_address'):
            address = info['property_address']
            for i in range(self.property_combo.count()):
                property_data = self.property_combo.itemData(i)
                if property_data:
                    # 物件データから住所を取得して比較
                    # ここでは簡易的に、コンボボックスのテキストに住所が含まれているかチェック
                    if address in self.property_combo.itemText(i):
                        self.property_combo.setCurrentIndex(i)
                        break

        # 契約期間
        if info.get('start_date'):
            try:
                date_obj = datetime.strptime(info['start_date'], "%Y-%m-%d").date()
                self.start_date_edit.setDate(QDate(date_obj))
            except:
                pass

        if info.get('end_date'):
            try:
                date_obj = datetime.strptime(info['end_date'], "%Y-%m-%d").date()
                self.end_date_edit.setDate(QDate(date_obj))
            except:
                pass

        # 金額
        if info.get('rent'):
            self.rent_spin.setValue(info['rent'])

        if info.get('maintenance_fee'):
            self.maintenance_fee_spin.setValue(info['maintenance_fee'])

        if info.get('security_deposit'):
            self.security_deposit_spin.setValue(info['security_deposit'])

        if info.get('key_money'):
            self.key_money_spin.setValue(info['key_money'])

        # 契約種別
        if info.get('contract_type'):
            index = self.contract_type_combo.findText(info['contract_type'])
            if index >= 0:
                self.contract_type_combo.setCurrentIndex(index)

        # 期間内解約：甲（貸主）の解約予告期間
        if info.get('owner_cancellation_notice_days'):
            days = info['owner_cancellation_notice_days']
            # コンボボックスから最も近い値を探す
            best_index = -1
            min_diff = float('inf')
            for i in range(self.owner_cancellation_notice_combo.count()):
                combo_days = self.owner_cancellation_notice_combo.itemData(i)
                if combo_days is not None:
                    diff = abs(combo_days - days)
                    if diff < min_diff:
                        min_diff = diff
                        best_index = i
            if best_index >= 0:
                self.owner_cancellation_notice_combo.setCurrentIndex(best_index)

        # 期間内解約：乙（借主）の解約予告期間
        if info.get('tenant_cancellation_notice_days'):
            days = info['tenant_cancellation_notice_days']
            # コンボボックスから最も近い値を探す
            best_index = -1
            min_diff = float('inf')
            for i in range(self.tenant_cancellation_notice_combo.count()):
                combo_days = self.tenant_cancellation_notice_combo.itemData(i)
                if combo_days is not None:
                    diff = abs(combo_days - days)
                    if diff < min_diff:
                        min_diff = diff
                        best_index = i
            if best_index >= 0:
                self.tenant_cancellation_notice_combo.setCurrentIndex(best_index)

    def validate_input(self):
        """入力値のバリデーション"""
        data = self.get_contract_data()
        
        # 必須項目チェック
        if not data['property_id']:
            MessageHelper.show_warning(self, "物件を選択してください")
            return False
        
        if not data['is_whole_property'] and not data['unit_id']:
            MessageHelper.show_warning(self, "部屋を選択するか、物件全体を選択してください")
            return False
        
        valid, msg = Validator.validate_required(data['contractor_name'], '契約者名')
        if not valid:
            MessageHelper.show_warning(self, msg)
            return False
        
        # 両手仲介の場合はテナントとオーナー両方必須
        if data['mediation_type'] == "両手仲介":
            valid, msg = Validator.validate_required(data['tenant_name'], 'テナント（借主）名')
            if not valid:
                MessageHelper.show_warning(self, msg)
                return False
            valid, msg = Validator.validate_required(data['owner_name'], 'オーナー（貸主）名')
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
    
    # シグナル定義
    contract_updated = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_contracts()
    
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
        self.contract_table.setColumnCount(16)
        self.contract_table.setHorizontalHeaderLabels([
            "ID", "物件名", "部屋", "契約者", "借主", "契約期間", "終了日",
            "賃料", "手数料合計", "更新まで", "契約書", "重説", "ステータス", "最終更新", "広告費", "注意事項"
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
        header.resizeSection(4, 120)   # 借主
        header.resizeSection(5, 80)    # 契約期間
        header.resizeSection(6, 80)    # 終了日
        header.resizeSection(7, 80)    # 賃料
        header.resizeSection(8, 90)    # 手数料合計
        header.resizeSection(9, 60)    # 更新まで
        header.resizeSection(10, 40)   # 契約書
        header.resizeSection(11, 40)   # 重説
        header.resizeSection(12, 80)   # ステータス
        header.resizeSection(13, 80)   # 最終更新
        header.resizeSection(14, 70)   # 広告費
        header.resizeSection(15, 150)  # 注意事項

        # 重要でない列は初期状態で非表示
        self.contract_table.setColumnHidden(14, True)  # 広告費は詳細時のみ表示
        self.contract_table.setColumnHidden(13, True)  # 最終更新も詳細時のみ
        self.contract_table.setColumnHidden(15, True)  # 注意事項も詳細時のみ
        
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

                # 借主名（tenant_nameを表示、なければ空欄）
                tenant_name = contract.get('tenant_name', '') or ''
                self.contract_table.setItem(row_position, 4, QTableWidgetItem(tenant_name))

                # 契約期間
                start_date = DateHelper.format_date(contract.get('start_date'), "%Y年%m月%d日")
                end_date = DateHelper.format_date(contract.get('end_date'), "%Y年%m月%d日")
                period = f"{start_date} ～ {end_date}"
                self.contract_table.setItem(row_position, 5, QTableWidgetItem(period))

                # 終了日
                end_date_item = QTableWidgetItem(DateHelper.format_date(contract.get('end_date'), "%Y年%m月%d日"))
                self.contract_table.setItem(row_position, 6, end_date_item)

                # 賃料
                rent = contract.get('rent', 0) or 0
                maintenance = contract.get('maintenance_fee', 0) or 0
                total_rent = rent + maintenance
                rent_item = QTableWidgetItem(FormatHelper.format_currency(total_rent))
                self.contract_table.setItem(row_position, 7, rent_item)

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
                self.contract_table.setItem(row_position, 8, commission_item)
                
                # 契約書・重説のアップロード状況
                contract_id = contract['id']
                has_contract = self.check_document_uploaded(contract_id, "契約書")
                has_important_doc = self.check_document_uploaded(contract_id, "重要事項説明書")

                # 契約書の○×表示
                contract_doc_item = QTableWidgetItem("○" if has_contract else "×")
                contract_doc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if has_contract:
                    contract_doc_item.setForeground(QColor("#4CAF50"))  # 緑
                    contract_doc_item.setBackground(QColor("#E8F5E9"))
                else:
                    contract_doc_item.setForeground(QColor("#f44336"))  # 赤
                    contract_doc_item.setBackground(QColor("#FFEBEE"))
                self.contract_table.setItem(row_position, 10, contract_doc_item)

                # 重説の○×表示
                important_doc_item = QTableWidgetItem("○" if has_important_doc else "×")
                important_doc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if has_important_doc:
                    important_doc_item.setForeground(QColor("#4CAF50"))  # 緑
                    important_doc_item.setBackground(QColor("#E8F5E9"))
                else:
                    important_doc_item.setForeground(QColor("#f44336"))  # 赤
                    important_doc_item.setBackground(QColor("#FFEBEE"))
                self.contract_table.setItem(row_position, 11, important_doc_item)

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
                        self.contract_table.setItem(row_position, 9, days_item)

                        status_item = QTableWidgetItem(status)
                        status_item.setBackground(color)
                        self.contract_table.setItem(row_position, 12, status_item)
                    else:
                        self.contract_table.setItem(row_position, 9, QTableWidgetItem("不明"))
                        self.contract_table.setItem(row_position, 12, QTableWidgetItem("不明"))
                else:
                    self.contract_table.setItem(row_position, 9, QTableWidgetItem("未設定"))
                    self.contract_table.setItem(row_position, 12, QTableWidgetItem("未設定"))

                # 最終更新
                updated_at = DateHelper.format_date(contract.get('updated_at'))
                self.contract_table.setItem(row_position, 13, QTableWidgetItem(updated_at))

                # 広告費（詳細表示時のみ）
                ad_fee_item = QTableWidgetItem(FormatHelper.format_currency(advertising_fee))
                if advertising_fee > 0:
                    ad_fee_item.setBackground(QColor("#FFF3E0"))  # 薄オレンジ
                self.contract_table.setItem(row_position, 14, ad_fee_item)

                # 注意事項（詳細表示時のみ）
                notes = contract.get('notes', '') or ''
                notes_item = QTableWidgetItem(notes)
                if notes:
                    notes_item.setBackground(QColor("#FFF9C4"))  # 薄黄色（注意喚起）
                self.contract_table.setItem(row_position, 15, notes_item)

            # アラート更新
            self.update_alerts(alert_count, expiring_contracts)
            
        except Exception as e:
            MessageHelper.show_error(self, f"契約一覧の読み込み中にエラーが発生しました: {str(e)}")
    
    def check_document_uploaded(self, contract_id, document_type):
        """指定された種別の書類がアップロードされているかチェック"""
        try:
            import sqlite3
            conn = sqlite3.connect("tintai_management.db")
            cursor = conn.cursor()

            cursor.execute('''
                SELECT COUNT(*) FROM contract_documents
                WHERE contract_id = ? AND document_type = ?
            ''', (contract_id, document_type))

            count = cursor.fetchone()[0]
            conn.close()

            return count > 0

        except Exception as e:
            print(f"書類チェックエラー: {e}")
            return False

    def toggle_detail_view(self):
        """詳細表示の切り替え"""
        is_detailed = self.detail_view_button.isChecked()

        # 詳細列の表示/非表示切り替え
        self.contract_table.setColumnHidden(13, not is_detailed)  # 最終更新
        self.contract_table.setColumnHidden(14, not is_detailed)  # 広告費
        self.contract_table.setColumnHidden(15, not is_detailed)  # 注意事項

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
                # ダイアログから顧客IDを取得
                customer_id = data.get('customer_id')

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
                    memo=data['memo'],
                    contract_status=data.get('contract_status', 'active'),
                    renewal_terms=data.get('renewal_terms'),
                    tenant_phone=data.get('tenant_phone'),
                    tenant_name=data.get('tenant_name'),
                    notes=data.get('notes'),
                    mediation_type=data.get('mediation_type', '片手仲介'),
                    party_type=data.get('party_type', 'テナント（借主）')
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
                # 契約基本情報を更新
                TenantContract.update(
                    contract_id=contract_id,
                    unit_id=data.get('unit_id'),
                    contractor_name=data.get('contractor_name'),
                    start_date=data.get('start_date'),
                    end_date=data.get('end_date'),
                    rent=data.get('rent'),
                    maintenance_fee=data.get('maintenance_fee'),
                    security_deposit=data.get('security_deposit'),
                    key_money=data.get('key_money'),
                    renewal_method=data.get('renewal_method'),
                    insurance_flag=data.get('insurance_flag'),
                    owner_cancellation_notice_days=data.get('owner_cancellation_notice_days'),
                    tenant_cancellation_notice_days=data.get('tenant_cancellation_notice_days'),
                    renewal_notice_days=data.get('renewal_notice_days'),
                    renewal_deadline_days=data.get('renewal_deadline_days'),
                    auto_create_tasks=data.get('auto_create_tasks'),
                    memo=data.get('memo'),
                    customer_id=data.get('customer_id'),
                    contract_status=data.get('contract_status'),
                    renewal_terms=data.get('renewal_terms'),
                    tenant_phone=data.get('tenant_phone'),
                    tenant_name=data.get('tenant_name'),
                    notes=data.get('notes'),
                    mediation_type=data.get('mediation_type'),
                    party_type=data.get('party_type'),
                    # 手数料情報も含める
                    tenant_commission_months=data.get('tenant_commission_months'),
                    landlord_commission_months=data.get('landlord_commission_months'),
                    tenant_commission_amount=data.get('tenant_commission_amount'),
                    landlord_commission_amount=data.get('landlord_commission_amount'),
                    advertising_fee=data.get('advertising_fee'),
                    advertising_fee_included=data.get('advertising_fee_included'),
                    commission_notes=data.get('commission_notes')
                )

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
                print(f"契約削除完了: contract_id={contract_id}, シグナル発信")
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