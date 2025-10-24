"""
接点履歴管理タブ - 基本版
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QLineEdit, 
                             QComboBox, QTextEdit, QDateEdit, QFormLayout, 
                             QGroupBox, QMessageBox, QHeaderView, QSplitter, QScrollArea, 
                             QSizePolicy, QFrame)
from PyQt6.QtCore import Qt, QDate
from utils import MessageHelper, DateHelper, FormatHelper
from models import Customer, Communication
from ui.ui_styles import ModernStyles, ButtonHelper

class CommunicationTabBasic(QWidget):
    """接点履歴管理タブ - 基本版"""
    
    def __init__(self):
        super().__init__()
        self.communications = []
        self.customers = []  # 簡易顧客リスト
        self.init_ui()
        self.load_communications()
    
    def load_customers_to_combo(self):
        """顧客データをコンボボックスに読み込み"""
        try:
            self.customer_combo.clear()
            self.customer_combo.addItem("--- 顧客を選択 ---", "")
            
            customers = Customer.get_all()
            for customer in customers:
                display_name = customer.get('name', '')
                if customer.get('phone'):
                    display_name += f" ({customer['phone']})"
                self.customer_combo.addItem(display_name, customer.get('id'))
                
        except Exception as e:
            print(f"顧客データ読み込みエラー: {e}")
            # エラー時はダミーデータを表示
            self.customer_combo.addItem("サンプル顧客A (090-1234-5678)", 1)
            self.customer_combo.addItem("サンプル顧客B (080-9876-5432)", 2)
        
    def init_ui(self):
        # モダンスタイルを適用
        self.setStyleSheet(ModernStyles.get_all_styles())
        
        # ページコンテナを作成
        from ui.ui_helpers import make_page_container
        container, layout = make_page_container()
        
        # ヘッダー
        header_widget = self.create_header()
        layout.addWidget(header_widget)
        
        # 顧客情報入力（幅制限）
        customer_group = QGroupBox("👤 顧客情報")
        customer_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 16px;
                font-weight: 600;
                color: #1f2937;
                padding-top: 20px;
                margin-top: 16px;
            }}
        """)
        customer_layout = QFormLayout()
        customer_layout.setSpacing(12)
        customer_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        customer_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        customer_layout.setHorizontalSpacing(12)
        
        # 顧客選択コンボボックス
        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(True)  # 手動入力も可能
        self.customer_combo.setMinimumWidth(200)
        self.customer_combo.setMinimumHeight(36)
        self.load_customers_to_combo()
        
        self.customer_phone_edit = QLineEdit()
        self.customer_phone_edit.setPlaceholderText("電話番号（任意）")
        self.customer_phone_edit.setMinimumWidth(150)
        self.customer_phone_edit.setMinimumHeight(36)
        
        self.customer_email_edit = QLineEdit()
        self.customer_email_edit.setPlaceholderText("メールアドレス（任意）")
        self.customer_email_edit.setMinimumWidth(200)
        self.customer_email_edit.setMinimumHeight(36)
        
        customer_layout.addRow("顧客名:", self.customer_combo)
        customer_layout.addRow("電話:", self.customer_phone_edit)
        customer_layout.addRow("メール:", self.customer_email_edit)
        
        customer_group.setLayout(customer_layout)
        customer_group.setMinimumWidth(300)
        
        # 接点履歴入力フォーム（幅制限）
        form_group = QGroupBox("接点履歴登録")
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form_layout.setHorizontalSpacing(12)
        
        self.communication_type_combo = QComboBox()
        self.communication_type_combo.addItems(["電話", "メール", "面談", "LINE", "SMS", "その他"])
        self.communication_type_combo.setMinimumWidth(100)
        self.communication_type_combo.setMinimumHeight(36)
        
        self.subject_edit = QLineEdit()
        self.subject_edit.setPlaceholderText("件名・概要")
        self.subject_edit.setMinimumWidth(250)
        self.subject_edit.setMinimumHeight(36)
        
        self.content_edit = QTextEdit()
        self.content_edit.setMinimumHeight(80)
        self.content_edit.setMaximumHeight(120)
        self.content_edit.setMinimumWidth(300)
        self.content_edit.setPlaceholderText("詳細内容を入力...")
        
        self.contact_date_edit = QDateEdit()
        self.contact_date_edit.setDate(QDate.currentDate())
        self.contact_date_edit.setCalendarPopup(True)
        self.contact_date_edit.setMinimumWidth(120)
        self.contact_date_edit.setMinimumHeight(36)
        
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["受信", "発信"])
        self.direction_combo.setMinimumWidth(80)
        self.direction_combo.setMinimumHeight(36)
        
        # 入電/架電トグル（方向と連動）
        self.direction_toggle = QPushButton("受信")
        self.direction_toggle.setCheckable(True)
        self.direction_toggle.setChecked(False)  # デフォルト：受信
        self.direction_toggle.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 16px;
                padding: 6px 12px;
                font-size: 12px;
                min-height: 24px;
            }
            QPushButton:checked {
                background-color: #f59e0b;
            }
        """)
        
        # 方向とトグルを連動
        def on_direction_changed(text):
            self.direction_toggle.setText(text)
            self.direction_toggle.setChecked(text == "発信")
        
        def on_toggle_changed(checked):
            text = "発信" if checked else "受信"
            index = self.direction_combo.findText(text)
            if index >= 0:
                self.direction_combo.setCurrentIndex(index)
        
        self.direction_combo.currentTextChanged.connect(on_direction_changed)
        self.direction_toggle.clicked.connect(on_toggle_changed)
        
        self.next_action_edit = QTextEdit()
        self.next_action_edit.setMinimumHeight(50)
        self.next_action_edit.setMaximumHeight(70)
        self.next_action_edit.setMinimumWidth(300)
        self.next_action_edit.setPlaceholderText("次回アクション・備考（任意）")
        
        form_layout.addRow("接点種別:", self.communication_type_combo)
        form_layout.addRow("件名:", self.subject_edit)
        form_layout.addRow("内容:", self.content_edit)
        form_layout.addRow("接触日:", self.contact_date_edit)
        # 方向とトグルを横並びに
        direction_layout = QHBoxLayout()
        direction_layout.addWidget(self.direction_combo)
        direction_layout.addWidget(self.direction_toggle)
        direction_layout.addStretch()
        
        form_layout.addRow("方向:", direction_layout)
        form_layout.addRow("次回アクション:", self.next_action_edit)
        
        form_group.setLayout(form_layout)
        form_group.setMaximumWidth(550)  # グループボックス幅を縮小

        # ボタン定義（レイアウトへの追加は後で行う）
        self.add_button = QPushButton("💾 登録")
        self.add_button.clicked.connect(self.add_communication)
        ButtonHelper.set_success(self.add_button)

        self.edit_button = QPushButton("✏️ 編集")
        self.edit_button.clicked.connect(self.edit_communication)
        self.edit_button.setEnabled(False)

        self.delete_button = QPushButton("🗑️ 削除")
        self.delete_button.clicked.connect(self.delete_communication)
        self.delete_button.setEnabled(False)
        ButtonHelper.set_danger(self.delete_button)

        self.clear_button = QPushButton("クリア")
        self.clear_button.clicked.connect(self.clear_form)

        self.export_button = QPushButton("📊 CSV出力")
        self.export_button.clicked.connect(self.export_to_csv)

        # 検索・フィルター
        search_layout = QHBoxLayout()
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("顧客名、件名、内容で検索...")
        self.search_edit.textChanged.connect(self.apply_filters)
        self.search_edit.setMinimumWidth(250)
        self.search_edit.setMinimumHeight(36)
        
        self.type_filter_combo = QComboBox()
        self.type_filter_combo.addItems(["全ての種別", "電話", "メール", "面談", "LINE", "SMS", "その他"])
        self.type_filter_combo.currentTextChanged.connect(self.apply_filters)
        self.type_filter_combo.setMinimumWidth(130)
        self.type_filter_combo.setMinimumHeight(36)
        
        search_layout.addWidget(QLabel("検索:"))
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(QLabel("種別:"))
        search_layout.addWidget(self.type_filter_combo)
        search_layout.addStretch()
        
        # テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "顧客名", "接点種別", "件名", "接触日", "方向", "次回アクション", "登録日"
        ])
        
        # テーブル設定
        self.table.setColumnHidden(0, True)  # IDを非表示
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.itemDoubleClicked.connect(self.show_detail)
        
        # テーブルの列幅調整（柱ごとに適切な幅を設定）
        header = self.table.horizontalHeader()
        # 列幅を個別に設定
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)      # 顧客名
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # 接点種別
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)      # 件名  
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # 接触日
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # 方向
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)      # 次回アクション
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # 登録日
        
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table.verticalHeader().setDefaultSectionSize(36)  # 行高を少し縮小して情報密度を上げる
        
        # テーブルのスタイルを改善
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #dee2e6;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #f1f3f4;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #dee2e6;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        
        # 詳細表示エリア
        self.detail_group = QGroupBox("詳細内容")
        self.detail_group.setMinimumHeight(250)
        detail_layout = QVBoxLayout()
        detail_layout.setSpacing(8)
        detail_layout.setContentsMargins(16, 16, 16, 16)
        
        self.detail_content = QTextEdit()
        self.detail_content.setReadOnly(True)
        self.detail_content.setMinimumHeight(200)
        self.detail_content.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
                line-height: 1.4;
            }
        """)
        
        detail_layout.addWidget(self.detail_content)
        self.detail_group.setLayout(detail_layout)
        
        # 整理された入力フォームエリア
        form_container = QWidget()
        form_container_layout = QVBoxLayout(form_container)
        form_container_layout.setContentsMargins(20, 16, 20, 16)  # 適度な余白
        form_container_layout.setSpacing(20)
        
        # セクションタイトル
        section_title = QLabel("📝 新しい接点履歴を登録")
        section_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2563eb;
                padding: 8px 0;
                border-bottom: 2px solid #e5e7eb;
                margin-bottom: 8px;
            }
        """)
        form_container_layout.addWidget(section_title)
        
        # 顧客情報と接点履歴を横並びに
        input_row_layout = QHBoxLayout()
        input_row_layout.setSpacing(24)
        
        # 顧客情報エリアのスタイル改善
        customer_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                color: #374151;
                padding-top: 16px;
                margin-top: 12px;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                background-color: #f9fafb;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                background-color: #f9fafb;
            }
        """)
        
        # 接点履歴エリアのスタイル改善
        form_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                color: #374151;
                padding-top: 16px;
                margin-top: 12px;
                border: 2px solid #3b82f6;
                border-radius: 8px;
                background-color: #eff6ff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                background-color: #eff6ff;
            }
        """)
        
        input_row_layout.addWidget(customer_group, 1)
        input_row_layout.addWidget(form_group, 2)
        form_container_layout.addLayout(input_row_layout)
        
        # ボタンエリアを整理
        button_section = QWidget()
        button_section_layout = QVBoxLayout(button_section)
        button_section_layout.setSpacing(12)
        button_section_layout.setContentsMargins(0, 0, 0, 0)
        
        # アクションボタンタイトル
        button_title = QLabel("⚙️ 操作")
        button_title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 600;
                color: #6b7280;
                padding: 4px 0;
            }
        """)
        button_section_layout.addWidget(button_title)
        
        # メインアクションボタン（左寄せ）
        main_buttons_layout = QHBoxLayout()
        
        # 登録ボタンを強調
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: 600;
                min-height: 36px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:pressed {
                background-color: #047857;
            }
        """)
        
        # 編集ボタンのスタイル
        self.edit_button.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: 500;
                min-height: 32px;
            }
            QPushButton:hover:enabled {
                background-color: #2563eb;
            }
            QPushButton:disabled {
                background-color: #9ca3af;
                color: #d1d5db;
            }
        """)
        
        # 削除ボタンのスタイル
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: 500;
                min-height: 32px;
            }
            QPushButton:hover:enabled {
                background-color: #dc2626;
            }
            QPushButton:disabled {
                background-color: #9ca3af;
                color: #d1d5db;
            }
        """)
        
        # クリアボタンのスタイル
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

        # CSV出力ボタンのスタイル
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

        main_buttons_layout.addWidget(self.add_button)
        main_buttons_layout.addWidget(self.edit_button)
        main_buttons_layout.addWidget(self.delete_button)
        main_buttons_layout.addWidget(self.clear_button)
        main_buttons_layout.addWidget(self.export_button)
        main_buttons_layout.addStretch()
        
        button_section_layout.addLayout(main_buttons_layout)
        form_container_layout.addWidget(button_section)
        
        # 区切り線
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("QFrame { color: #e5e7eb; margin: 8px 0; }")
        form_container_layout.addWidget(separator)
        
        # 検索エリア
        search_section = QWidget()
        search_section_layout = QVBoxLayout(search_section)
        search_section_layout.setSpacing(8)
        search_section_layout.setContentsMargins(0, 0, 0, 0)
        
        search_title = QLabel("🔍 検索・フィルター")
        search_title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 600;
                color: #6b7280;
                padding: 4px 0;
            }
        """)
        search_section_layout.addWidget(search_title)
        search_section_layout.addLayout(search_layout)
        
        form_container_layout.addWidget(search_section)
        
        # フォームエリアを折りたたみ可能に
        from ui.ui_helpers import make_collapsible
        collapsible_form = make_collapsible("📝 接点履歴の登録・管理", form_container, default_expanded=True)
        
        # テーブルのスタイルを改善
        self.table.setMinimumHeight(400)  # テーブルの最小高さを大幅に増加
        
        # 詳細表示エリア（折りたたみ）
        collapsible_detail = make_collapsible("📝 詳細内容", self.detail_group, default_expanded=False)
        
        # レイアウトに追加（テーブルに最大のスペースを割り当て）
        layout.addWidget(collapsible_form)
        layout.addWidget(self.table, 3)  # ストレッチを大幅に増加
        layout.addWidget(collapsible_detail, 0)  # 詳細エリアは必要最小限
        
        # テーブルをストレッチ
        from ui.ui_helpers import stretch_table
        stretch_table(self.table)
        
        # 単一スクロールページを作成
        from ui.ui_helpers import make_scroll_page
        scroll_page = make_scroll_page(container)
        
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
                                          stop: 0 #8b5cf6,
                                          stop: 1 #7c3aed);
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
        
        title_label = QLabel("📞 接点履歴管理")
        title_label.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
        
        subtitle_label = QLabel("顧客との連絡履歴とコミュニケーション記録")
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
        
        self.comm_count_label = QLabel("総接点: 0件")
        self.comm_count_label.setStyleSheet("color: rgba(255, 255, 255, 0.9); font-size: 11px; text-align: right;")
        self.comm_count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.recent_comm_label = QLabel("今日の接点: 0件")
        self.recent_comm_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 10px; text-align: right;")
        self.recent_comm_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        stats_layout.addWidget(self.comm_count_label)
        stats_layout.addWidget(self.recent_comm_label)
        
        layout.addWidget(stats_container)
        
        return header
    
    def update_header_stats(self):
        """ヘッダーの統計を更新"""
        total_comms = len(self.communications)
        from datetime import date
        today = date.today().strftime("%Y-%m-%d")
        today_comms = len([comm for comm in self.communications 
                          if comm.get('contact_date', '').startswith(today)])
        
        self.comm_count_label.setText(f"総接点: {total_comms}件")
        self.recent_comm_label.setText(f"今日の接点: {today_comms}件")
    
    def load_communications(self):
        """接点履歴を読み込み"""
        try:
            from models import Communication
            # データベースから接点履歴を取得
            self.communications = Communication.get_all()

        except Exception as e:
            # データベース接続エラーを明示的に表示
            self.communications = []
            import traceback
            traceback.print_exc()
            MessageHelper.show_error(
                self,
                f"接点履歴の読み込みに失敗しました\n\nエラー詳細: {str(e)}\n\nデータベース接続を確認してください。"
            )
            return

        self.apply_filters()
        self.update_header_stats()
    
    def apply_filters(self):
        """フィルターを適用してテーブルを更新"""
        search_text = self.search_edit.text().lower()
        type_filter = self.type_filter_combo.currentText()
        
        # フィルタリング
        filtered_comms = []
        for comm in self.communications:
            # 検索フィルター
            if search_text:
                if (search_text not in comm.get('customer_name', '').lower() and
                    search_text not in comm.get('subject', '').lower() and
                    search_text not in comm.get('content', '').lower()):
                    continue
            
            # 種別フィルター
            if type_filter != "全ての種別" and comm.get('communication_type') != type_filter:
                continue
            
            filtered_comms.append(comm)
        
        # テーブル更新
        self.table.setRowCount(len(filtered_comms))
        
        for row, comm in enumerate(filtered_comms):
            self.table.setItem(row, 0, QTableWidgetItem(str(comm.get('id', ''))))
            self.table.setItem(row, 1, QTableWidgetItem(comm.get('customer_name', '')))
            self.table.setItem(row, 2, QTableWidgetItem(comm.get('communication_type', '')))
            self.table.setItem(row, 3, QTableWidgetItem(comm.get('subject', '')))
            self.table.setItem(row, 4, QTableWidgetItem(comm.get('contact_date', '')))
            self.table.setItem(row, 5, QTableWidgetItem(comm.get('direction', '')))
            self.table.setItem(row, 6, QTableWidgetItem(comm.get('next_action', '')))
            self.table.setItem(row, 7, QTableWidgetItem(comm.get('created_at', '')))
            
            # 方向による色分け
            if comm.get('direction') == '発信':
                from PyQt6.QtGui import QColor
                for col in range(8):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(QColor("#E3F2FD"))  # 薄青
            elif comm.get('direction') == '受信':
                from PyQt6.QtGui import QColor
                for col in range(8):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(QColor("#E8F5E8"))  # 薄緑
    
    def on_selection_changed(self):
        """選択変更時の処理"""
        has_selection = len(self.table.selectedItems()) > 0
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        
        # 詳細表示
        if has_selection:
            self.show_detail()
        else:
            self.detail_content.clear()
    
    def show_detail(self):
        """詳細内容を表示"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            comm_id = self.get_selected_communication_id()
            comm = next((c for c in self.communications if c.get('id') == comm_id), None)
            if comm:
                detail_text = f"【{comm.get('communication_type', '')}】 {comm.get('subject', '')}\n"
                detail_text += f"日時: {comm.get('contact_date', '')} ({comm.get('direction', '')})\n"
                detail_text += f"顧客: {comm.get('customer_name', '')}\n\n"
                detail_text += f"内容:\n{comm.get('content', '')}\n"
                if comm.get('next_action'):
                    detail_text += f"\n次回アクション:\n{comm.get('next_action', '')}"
                
                self.detail_content.setPlainText(detail_text)
    
    def get_selected_communication_id(self):
        """選択された接点履歴IDを取得"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            id_item = self.table.item(current_row, 0)
            if id_item:
                try:
                    return int(id_item.text())
                except ValueError:
                    return None
        return None
    
    def add_communication(self):
        """接点履歴を追加"""
        customer_name = self.customer_combo.currentText().strip()
        # 選択された顧客のIDを取得
        customer_data = self.customer_combo.currentData()
        if customer_name.startswith('---'):
            customer_name = ''
        if not customer_name:
            MessageHelper.show_warning(self, "顧客名を入力してください")
            return
        
        subject = self.subject_edit.text().strip()
        if not subject:
            MessageHelper.show_warning(self, "件名を入力してください")
            return
        
        try:
            # データベースに保存を試行
            from models import Communication, Customer

            # コンボボックスから顧客IDを取得
            if customer_data:
                # 既存顧客が選択されている場合
                customer_id = customer_data
            else:
                # 手動入力の場合は、既存顧客を検索
                customers = Customer.get_all()
                customer = next((c for c in customers if c['name'] == customer_name), None)
                if customer:
                    # 既存顧客が見つかった
                    customer_id = customer['id']
                else:
                    # 新規顧客として追加
                    customer_id = Customer.create(
                        name=customer_name,
                        phone=self.customer_phone_edit.text().strip() or None,
                        email=self.customer_email_edit.text().strip() or None
                    )

            # データベースに保存（IDが自動生成される）
            comm_id = Communication.create(
                customer_id=customer_id,
                contract_id=None,
                communication_type=self.communication_type_combo.currentText(),
                subject=subject,
                content=self.content_edit.toPlainText().strip() or None,
                contact_date=self.contact_date_edit.date().toString("yyyy-MM-dd"),
                direction=self.direction_combo.currentText(),
                next_action=self.next_action_edit.toPlainText().strip() or None
            )

            MessageHelper.show_success(self, "接点履歴を登録しました")
            self.clear_form()
            self.load_communications()  # データベースから再読み込み
            self.apply_filters()
            self.update_header_stats()

        except Exception as e:
            print(f"DB保存エラー: {e}")
            import traceback
            traceback.print_exc()
            MessageHelper.show_error(self, f"接点履歴の登録に失敗しました: {str(e)}")
    
    def edit_communication(self):
        """接点履歴を編集"""
        comm_id = self.get_selected_communication_id()
        if not comm_id:
            return
        
        comm = next((c for c in self.communications if c.get('id') == comm_id), None)
        if not comm:
            return
        
        # フォームに読み込み
        # 既存の顧客名をコンボボックスに設定
        existing_customer = comm.get('customer_name', '')
        if existing_customer:
            index = self.customer_combo.findText(existing_customer, Qt.MatchFlag.MatchContains)
            if index >= 0:
                self.customer_combo.setCurrentIndex(index)
            else:
                self.customer_combo.setEditText(existing_customer)
        
        type_index = self.communication_type_combo.findText(comm.get('communication_type', ''))
        if type_index >= 0:
            self.communication_type_combo.setCurrentIndex(type_index)
        
        self.subject_edit.setText(comm.get('subject', ''))
        self.content_edit.setPlainText(comm.get('content', ''))
        
        if comm.get('contact_date'):
            date = QDate.fromString(comm.get('contact_date'), "yyyy-MM-dd")
            if date.isValid():
                self.contact_date_edit.setDate(date)
        
        direction_index = self.direction_combo.findText(comm.get('direction', ''))
        if direction_index >= 0:
            self.direction_combo.setCurrentIndex(direction_index)
        
        self.next_action_edit.setPlainText(comm.get('next_action', ''))
        
        # 編集モードに変更
        self.add_button.setText("更新")
        self.add_button.clicked.disconnect()
        self.add_button.clicked.connect(lambda: self.update_communication(comm_id))
    
    def update_communication(self, comm_id):
        """接点履歴を更新"""
        customer_name = self.customer_combo.currentText().strip()
        # 選択された顧客のIDを取得
        customer_data = self.customer_combo.currentData()
        if customer_name.startswith('---'):
            customer_name = ''
        if not customer_name:
            MessageHelper.show_warning(self, "顧客名を入力してください")
            return

        subject = self.subject_edit.text().strip()
        if not subject:
            MessageHelper.show_warning(self, "件名を入力してください")
            return

        # customer_idを取得
        customer_id = customer_data if customer_data else None
        if not customer_id:
            MessageHelper.show_warning(self, "有効な顧客を選択してください")
            return

        try:
            # データベースを更新
            Communication.update(
                comm_id,
                customer_id=customer_id,
                communication_type=self.communication_type_combo.currentText(),
                subject=subject,
                content=self.content_edit.toPlainText().strip() or None,
                contact_date=self.contact_date_edit.date().toString("yyyy-MM-dd"),
                direction=self.direction_combo.currentText(),
                next_action=self.next_action_edit.toPlainText().strip() or None
            )

            MessageHelper.show_success(self, "接点履歴を更新しました")
            self.reset_add_mode()
            self.load_communications()  # データベースから再読み込み
            self.update_header_stats()
        except Exception as e:
            import traceback
            traceback.print_exc()
            MessageHelper.show_error(self, f"接点履歴の更新に失敗しました: {str(e)}")
    
    def delete_communication(self):
        """接点履歴を削除"""
        comm_id = self.get_selected_communication_id()
        if not comm_id:
            return

        comm = next((c for c in self.communications if c.get('id') == comm_id), None)
        if not comm:
            return

        if MessageHelper.confirm_delete(self, f"接点履歴「{comm.get('subject', '')}」"):
            try:
                # データベースから削除
                Communication.delete(comm_id)
                MessageHelper.show_success(self, "接点履歴を削除しました")
                self.load_communications()  # データベースから再読み込み
                self.update_header_stats()
            except Exception as e:
                import traceback
                traceback.print_exc()
                MessageHelper.show_error(self, f"接点履歴の削除に失敗しました: {str(e)}")
    
    def clear_form(self):
        """フォームをクリア"""
        self.customer_combo.setCurrentIndex(0)  # デフォルト選択にリセット
        self.customer_phone_edit.clear()
        self.customer_email_edit.clear()
        self.communication_type_combo.setCurrentIndex(0)
        self.subject_edit.clear()
        self.content_edit.clear()
        self.contact_date_edit.setDate(QDate.currentDate())
        self.direction_combo.setCurrentIndex(0)
        self.next_action_edit.clear()
        self.reset_add_mode()
    
    def reset_add_mode(self):
        """追加モードに戻す"""
        self.add_button.setText("登録")
        self.add_button.clicked.disconnect()
        self.add_button.clicked.connect(self.add_communication)

    def export_to_csv(self):
        """接点履歴をCSV出力"""
        try:
            import csv
            from PyQt6.QtWidgets import QFileDialog
            from models import Communication

            file_path, _ = QFileDialog.getSaveFileName(
                self, "CSVファイルの保存", "接点履歴.csv", "CSV Files (*.csv)"
            )

            if file_path:
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                    writer = csv.writer(csvfile)

                    # ヘッダー（内容列を追加）
                    writer.writerow([
                        "ID", "顧客名", "接点種別", "件名", "内容", "接触日",
                        "方向", "次回アクション", "登録日"
                    ])

                    # データ（表示されている行から元データを取得）
                    for row in range(self.table.rowCount()):
                        if not self.table.isRowHidden(row):
                            # テーブルからIDを取得
                            id_item = self.table.item(row, 0)
                            if id_item:
                                comm_id = int(id_item.text())
                                # 元データから該当レコードを検索
                                comm = next((c for c in self.communications if c.get('id') == comm_id), None)
                                if comm:
                                    row_data = [
                                        comm.get('id', ''),
                                        comm.get('customer_name', ''),
                                        comm.get('communication_type', ''),
                                        comm.get('subject', ''),
                                        comm.get('content', ''),  # 内容を追加
                                        comm.get('contact_date', ''),
                                        comm.get('direction', ''),
                                        comm.get('next_action', ''),
                                        comm.get('created_at', '')
                                    ]
                                    writer.writerow(row_data)

                MessageHelper.show_success(self, f"CSVファイルを出力しました:\n{file_path}")

        except Exception as e:
            MessageHelper.show_error(self, f"CSV出力中にエラーが発生しました: {str(e)}")