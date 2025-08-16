"""
改良版顧客管理タブ - 検索・編集・削除機能付き
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QPushButton, QLabel, QLineEdit, 
                             QTextEdit, QMessageBox, QGroupBox, QFormLayout, 
                             QComboBox, QCheckBox, QDialog, QDialogButtonBox,
                             QSplitter, QFrame, QScrollArea, QHeaderView, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from models import Customer, OwnerProfile, TenantProfile
from utils import (Validator, TableHelper, MessageHelper, FormatHelper, 
                  SearchHelper, DateHelper, StatusColor)

class CustomerEditDialog(QDialog):
    """顧客編集ダイアログ"""
    
    def __init__(self, parent=None, customer_data=None):
        super().__init__(parent)
        self.customer_data = customer_data
        self.init_ui()
        if customer_data:
            self.load_customer_data()
    
    def init_ui(self):
        self.setWindowTitle("顧客情報編集" if self.customer_data else "顧客新規登録")
        self.setModal(True)
        self.resize(500, 500)  # 高さを増やす
        
        layout = QVBoxLayout()
        
        # スクロール可能なエリアを作成
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # フォーム用のウィジェット
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        
        self.name_edit = QLineEdit()
        self.customer_type_combo = QComboBox()
        self.customer_type_combo.addItems(["テナント", "オーナー"])
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("例: 03-1234-5678")
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("例: example@email.com")
        self.address_edit = QTextEdit()
        self.address_edit.setMaximumHeight(80)
        self.memo_edit = QTextEdit()
        self.memo_edit.setMaximumHeight(60)
        
        # 業種フィールド（テナント用）
        self.industry_edit = QLineEdit()
        self.industry_edit.setPlaceholderText("例: 飲食業、IT、小売業")
        
        # 保証会社フィールド（テナント用）
        self.guarantor_company_edit = QLineEdit()
        
        # 緊急連絡先（テナント用）
        self.emergency_contact_edit = QLineEdit()
        
        form_layout.addRow("顧客名 *:", self.name_edit)
        form_layout.addRow("顧客種別:", self.customer_type_combo)
        form_layout.addRow("電話番号:", self.phone_edit)
        form_layout.addRow("メールアドレス:", self.email_edit)
        form_layout.addRow("住所:", self.address_edit)
        form_layout.addRow("業種:", self.industry_edit)
        form_layout.addRow("保証会社:", self.guarantor_company_edit)
        form_layout.addRow("緊急連絡先:", self.emergency_contact_edit)
        form_layout.addRow("メモ:", self.memo_edit)
        
        # 顧客種別によって表示を切り替え
        self.customer_type_combo.currentTextChanged.connect(self.on_customer_type_changed)
        
        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # スクロールエリアにフォームを設定
        scroll_area.setWidget(form_widget)
        
        layout.addWidget(scroll_area)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
        # 初期表示を設定
        self.on_customer_type_changed(self.customer_type_combo.currentText())
    
    def on_customer_type_changed(self, customer_type):
        """顧客種別が変更されたときの処理"""
        is_tenant = (customer_type == "テナント")
        self.industry_edit.setVisible(is_tenant)
        self.guarantor_company_edit.setVisible(is_tenant)
        self.emergency_contact_edit.setVisible(is_tenant)
        
        # ラベルも動的に変更
        main_layout = self.layout()
        if main_layout and main_layout.count() > 0:
            form_layout_item = main_layout.itemAt(0)
            if form_layout_item and hasattr(form_layout_item, 'layout'):
                form_layout = form_layout_item.layout()
                if form_layout and hasattr(form_layout, 'rowCount'):
                    for i in range(form_layout.rowCount()):
                        label_item = form_layout.itemAt(i, QFormLayout.ItemRole.LabelRole)
                        field_item = form_layout.itemAt(i, QFormLayout.ItemRole.FieldRole)
                        if label_item and field_item:
                            widget = field_item.widget()
                            if widget == self.industry_edit:
                                label_item.widget().setVisible(is_tenant)
                            elif widget == self.guarantor_company_edit:
                                label_item.widget().setVisible(is_tenant)
                            elif widget == self.emergency_contact_edit:
                                label_item.widget().setVisible(is_tenant)
    
    def load_customer_data(self):
        """顧客データを読み込み"""
        if not self.customer_data:
            return
        
        self.name_edit.setText(self.customer_data.get('name', ''))
        
        # 顧客種別
        customer_type = self.customer_data.get('type', 'tenant')
        index = 0 if customer_type == 'tenant' else 1
        self.customer_type_combo.setCurrentIndex(index)
        
        self.phone_edit.setText(self.customer_data.get('phone', ''))
        self.email_edit.setText(self.customer_data.get('email', ''))
        self.address_edit.setPlainText(self.customer_data.get('address', ''))
        self.memo_edit.setPlainText(self.customer_data.get('memo', ''))
        
        # テナントプロフィール情報を読み込み
        if customer_type == 'tenant' and self.customer_data.get('id'):
            profile = TenantProfile.get_by_customer(self.customer_data['id'])
            if profile:
                self.industry_edit.setText(profile.get('industry', ''))
                self.guarantor_company_edit.setText(profile.get('guarantor_company', ''))
                self.emergency_contact_edit.setText(profile.get('emergency_contact', ''))
    
    def get_customer_data(self):
        """入力データを取得"""
        customer_type_map = {"テナント": "tenant", "オーナー": "owner"}
        return {
            'name': self.name_edit.text().strip(),
            'type': customer_type_map.get(self.customer_type_combo.currentText(), 'tenant'),
            'phone': self.phone_edit.text().strip(),
            'email': self.email_edit.text().strip(),
            'address': self.address_edit.toPlainText().strip(),
            'memo': self.memo_edit.toPlainText().strip(),
            'industry': self.industry_edit.text().strip(),
            'guarantor_company': self.guarantor_company_edit.text().strip(),
            'emergency_contact': self.emergency_contact_edit.text().strip()
        }
    
    def validate_input(self):
        """入力値のバリデーション"""
        data = self.get_customer_data()
        
        # 必須項目チェック
        valid, msg = Validator.validate_required(data['name'], '顧客名')
        if not valid:
            MessageHelper.show_warning(self, msg)
            return False
        
        # メールアドレス形式チェック
        if data['email'] and not Validator.validate_email(data['email']):
            MessageHelper.show_warning(self, "メールアドレスの形式が正しくありません")
            return False
        
        # 電話番号形式チェック
        if data['phone'] and not Validator.validate_phone(data['phone']):
            MessageHelper.show_warning(self, "電話番号の形式が正しくありません\n例: 03-1234-5678")
            return False
        
        return True
    
    def accept(self):
        """OKボタンが押されたとき"""
        if self.validate_input():
            super().accept()

class CustomerTabImproved(QWidget):
    """改良版顧客管理タブ"""
    
    customer_updated = pyqtSignal()  # 顧客情報更新シグナル
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_customers()
    
    def init_ui(self):
        # メインコンテナ
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(16, 16, 16, 16)
        
        # 検索バー
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("検索:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("顧客名、電話番号、メールアドレスで検索...")
        self.search_edit.textChanged.connect(self.on_search)
        search_layout.addWidget(self.search_edit)
        
        # フィルターコンボボックス
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全て", "テナント", "オーナー"])
        self.filter_combo.currentTextChanged.connect(self.on_filter_changed)
        search_layout.addWidget(QLabel("種別:"))
        search_layout.addWidget(self.filter_combo)
        
        search_layout.addStretch()
        
        # ボタングループ
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("新規登録")
        self.add_button.clicked.connect(self.add_customer)
        self.add_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        
        self.edit_button = QPushButton("編集")
        self.edit_button.clicked.connect(self.edit_customer)
        self.edit_button.setEnabled(False)
        
        self.delete_button = QPushButton("削除")
        self.delete_button.clicked.connect(self.delete_customer)
        self.delete_button.setEnabled(False)
        self.delete_button.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        
        self.refresh_button = QPushButton("更新")
        self.refresh_button.clicked.connect(self.load_customers)
        
        self.export_button = QPushButton("CSV出力")
        self.export_button.clicked.connect(self.export_to_csv)
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()
        
        # 顧客一覧テーブル
        self.customer_table = QTableWidget()
        self.customer_table.setColumnCount(9)
        self.customer_table.setHorizontalHeaderLabels([
            "ID", "顧客名", "種別", "電話番号", "メールアドレス", 
            "住所", "業種", "保証会社", "最終更新"
        ])
        
        # テーブル設定（レスポンシブ対応）
        self.customer_table.setColumnHidden(0, True)  # IDを非表示
        
        # 列幅の最適化（Stretch対応）
        header = self.customer_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # 重要度の低い列は初期非表示
        self.customer_table.setColumnHidden(8, True)  # 最終更新
        
        # テーブル設定
        self.customer_table.setAlternatingRowColors(True)
        self.customer_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.customer_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.customer_table.verticalHeader().setDefaultSectionSize(40)
        
        # テーブルのダブルクリックと選択イベント
        self.customer_table.doubleClicked.connect(self.edit_customer)
        self.customer_table.itemSelectionChanged.connect(self.on_selection_changed)
        
        # 詳細表示エリア
        self.detail_group = QGroupBox("顧客詳細")
        self.detail_group.setMinimumHeight(250)  # 高さを増やす
        
        # 詳細エリアの内部レイアウト
        detail_container = QWidget()
        detail_main_layout = QVBoxLayout(detail_container)
        detail_main_layout.setContentsMargins(16, 16, 16, 16)
        detail_main_layout.setSpacing(12)
        
        # フォームレイアウト
        detail_layout = QFormLayout()
        detail_layout.setSpacing(12)  # 行間を広げる
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        detail_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        detail_layout.setHorizontalSpacing(16)  # ラベルとフィールドの間隔
        detail_layout.setVerticalSpacing(12)  # 行間
        
        # ラベルのスタイル設定
        self.detail_name_label = QLabel()
        self.detail_name_label.setMinimumHeight(24)
        self.detail_name_label.setStyleSheet("QLabel { padding: 2px; }")
        
        self.detail_type_label = QLabel()
        self.detail_type_label.setMinimumHeight(24)
        self.detail_type_label.setStyleSheet("QLabel { padding: 2px; }")
        
        self.detail_phone_label = QLabel()
        self.detail_phone_label.setMinimumHeight(24)
        self.detail_phone_label.setStyleSheet("QLabel { padding: 2px; }")
        
        self.detail_email_label = QLabel()
        self.detail_email_label.setMinimumHeight(24)
        self.detail_email_label.setStyleSheet("QLabel { padding: 2px; }")
        
        self.detail_address_label = QLabel()
        self.detail_address_label.setMinimumHeight(24)
        self.detail_address_label.setWordWrap(True)
        self.detail_address_label.setStyleSheet("QLabel { padding: 2px; }")
        
        self.detail_memo_label = QLabel()
        self.detail_memo_label.setWordWrap(True)
        self.detail_memo_label.setMinimumHeight(60)
        self.detail_memo_label.setStyleSheet("QLabel { padding: 4px; background-color: #f5f5f5; border-radius: 4px; }")
        
        # フォームフィールドにラベルを作成
        def create_label_row(label_text):
            label = QLabel(label_text)
            label.setStyleSheet("QLabel { font-weight: bold; color: #666; }")
            label.setMinimumHeight(24)
            return label
        
        detail_layout.addRow(create_label_row("顧客名:"), self.detail_name_label)
        detail_layout.addRow(create_label_row("種別:"), self.detail_type_label)
        detail_layout.addRow(create_label_row("電話番号:"), self.detail_phone_label)
        detail_layout.addRow(create_label_row("メール:"), self.detail_email_label)
        detail_layout.addRow(create_label_row("住所:"), self.detail_address_label)
        detail_layout.addRow(create_label_row("メモ:"), self.detail_memo_label)
        
        detail_main_layout.addLayout(detail_layout)
        detail_main_layout.addStretch()  # 下部に余白を追加
        
        self.detail_group.setLayout(QVBoxLayout())
        self.detail_group.layout().addWidget(detail_container)
        
        # レイアウトを単一スクロールに変更
        # 検索・フィルター・ボタンエリア
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(12)
        
        # 検索とボタンをコントロールエリアに移動
        controls_layout.addLayout(search_layout)
        controls_layout.addLayout(button_layout)
        
        # 詳細エリアを折りたたみ可能に
        from ui_helpers import make_collapsible
        collapsible_detail = make_collapsible("顧客詳細", self.detail_group, default_expanded=False)
        
        # レイアウトに追加
        main_layout.addWidget(controls_widget)
        main_layout.addWidget(self.customer_table, 1)  # ストレッチ=1で残りスペースを占有
        main_layout.addWidget(collapsible_detail)
        
        # テーブルをストレッチ
        from ui_helpers import stretch_table
        stretch_table(self.customer_table)
        
        # 単一スクロールページを作成
        from ui_helpers import make_scroll_page
        scroll_page = make_scroll_page(main_container)
        
        # ページレイアウト設定
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(scroll_page)
    
    def load_customers(self):
        """顧客一覧を読み込み"""
        try:
            TableHelper.clear_table(self.customer_table)
            customers = Customer.get_all()
            
            for customer in customers:
                row_position = self.customer_table.rowCount()
                self.customer_table.insertRow(row_position)
                
                # 基本情報
                self.customer_table.setItem(row_position, 0, QTableWidgetItem(str(customer['id'])))
                self.customer_table.setItem(row_position, 1, QTableWidgetItem(customer['name']))
                
                # 種別
                customer_type = "オーナー" if customer['type'] == 'owner' else "テナント"
                type_item = QTableWidgetItem(customer_type)
                if customer['type'] == 'owner':
                    type_item.setBackground(QColor("#E3F2FD"))  # 薄青
                else:
                    type_item.setBackground(QColor("#FFF3E0"))  # 薄オレンジ
                self.customer_table.setItem(row_position, 2, type_item)
                
                self.customer_table.setItem(row_position, 3, QTableWidgetItem(customer.get('phone', '')))
                self.customer_table.setItem(row_position, 4, QTableWidgetItem(customer.get('email', '')))
                self.customer_table.setItem(row_position, 5, QTableWidgetItem(customer.get('address', '')))
                
                # テナントプロフィール情報
                if customer['type'] == 'tenant':
                    profile = TenantProfile.get_by_customer(customer['id'])
                    if profile:
                        self.customer_table.setItem(row_position, 6, QTableWidgetItem(profile.get('industry', '')))
                        self.customer_table.setItem(row_position, 7, QTableWidgetItem(profile.get('guarantor_company', '')))
                
                # 最終更新日
                updated_at = DateHelper.format_date(customer.get('updated_at'))
                self.customer_table.setItem(row_position, 8, QTableWidgetItem(updated_at))
            
        except Exception as e:
            MessageHelper.show_error(self, f"顧客一覧の読み込み中にエラーが発生しました: {str(e)}")
    
    def on_search(self):
        """検索処理"""
        search_text = self.search_edit.text()
        SearchHelper.filter_table(self.customer_table, search_text, columns=[1, 3, 4, 5])
    
    def on_filter_changed(self):
        """フィルター変更処理"""
        filter_type = self.filter_combo.currentText()
        
        for row in range(self.customer_table.rowCount()):
            type_item = self.customer_table.item(row, 2)
            if filter_type == "全て":
                self.customer_table.setRowHidden(row, False)
            elif type_item:
                should_show = (filter_type == type_item.text())
                self.customer_table.setRowHidden(row, not should_show)
    
    def on_selection_changed(self):
        """選択行が変更されたとき"""
        has_selection = self.customer_table.currentRow() >= 0
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        
        if has_selection:
            self.show_customer_detail()
    
    def show_customer_detail(self):
        """選択された顧客の詳細を表示"""
        row = self.customer_table.currentRow()
        if row < 0:
            return
        
        customer_id = int(self.customer_table.item(row, 0).text())
        customer = Customer.get_by_id(customer_id)
        
        if customer:
            self.detail_name_label.setText(customer.get('name', ''))
            self.detail_type_label.setText("オーナー" if customer.get('type') == 'owner' else "テナント")
            self.detail_phone_label.setText(FormatHelper.format_phone(customer.get('phone', '')))
            self.detail_email_label.setText(customer.get('email', ''))
            self.detail_address_label.setText(customer.get('address', ''))
            self.detail_memo_label.setText(customer.get('memo', ''))
    
    def add_customer(self):
        """顧客新規登録"""
        dialog = CustomerEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_customer_data()
            
            try:
                customer_id = Customer.create(
                    name=data['name'],
                    customer_type=data['type'],
                    phone=data['phone'],
                    email=data['email'],
                    address=data['address'],
                    memo=data['memo']
                )
                
                # プロフィール作成
                if data['type'] == 'owner':
                    OwnerProfile.create(customer_id=customer_id)
                else:
                    TenantProfile.create(
                        customer_id=customer_id,
                        industry=data['industry'],
                        guarantor_company=data['guarantor_company'],
                        emergency_contact=data['emergency_contact']
                    )
                
                MessageHelper.show_success(self, "顧客を登録しました")
                self.load_customers()
                self.customer_updated.emit()
                
            except Exception as e:
                MessageHelper.show_error(self, f"顧客登録中にエラーが発生しました: {str(e)}")
    
    def edit_customer(self):
        """顧客編集"""
        row = self.customer_table.currentRow()
        if row < 0:
            return
        
        customer_id = int(self.customer_table.item(row, 0).text())
        customer = Customer.get_by_id(customer_id)
        
        if not customer:
            return
        
        dialog = CustomerEditDialog(self, customer)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_customer_data()
            
            try:
                # 顧客情報更新
                Customer.update(
                    customer_id=customer_id,
                    name=data['name'],
                    customer_type=data['type'],
                    phone=data['phone'],
                    email=data['email'],
                    address=data['address'],
                    memo=data['memo']
                )
                
                # テナントプロフィール更新
                if data['type'] == 'tenant':
                    profile = TenantProfile.get_by_customer(customer_id)
                    if profile:
                        # 更新処理（TenantProfile.updateメソッドが必要）
                        pass
                    else:
                        TenantProfile.create(
                            customer_id=customer_id,
                            industry=data['industry'],
                            guarantor_company=data['guarantor_company'],
                            emergency_contact=data['emergency_contact']
                        )
                
                MessageHelper.show_success(self, "顧客情報を更新しました")
                self.load_customers()
                self.customer_updated.emit()
                
            except Exception as e:
                MessageHelper.show_error(self, f"顧客更新中にエラーが発生しました: {str(e)}")
    
    def delete_customer(self):
        """顧客削除"""
        row = self.customer_table.currentRow()
        if row < 0:
            return
        
        customer_name = self.customer_table.item(row, 1).text()
        
        if MessageHelper.confirm_delete(self, f"顧客「{customer_name}」"):
            customer_id = int(self.customer_table.item(row, 0).text())
            
            try:
                # 顧客削除
                Customer.delete(customer_id)
                
                MessageHelper.show_success(self, "顧客を削除しました")
                self.load_customers()
                self.customer_updated.emit()
                
            except Exception as e:
                MessageHelper.show_error(self, f"顧客削除中にエラーが発生しました: {str(e)}")
    
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
                    for col in range(1, self.customer_table.columnCount()):  # IDを除く
                        headers.append(self.customer_table.horizontalHeaderItem(col).text())
                    writer.writerow(headers)
                    
                    # データ
                    for row in range(self.customer_table.rowCount()):
                        if not self.customer_table.isRowHidden(row):
                            row_data = []
                            for col in range(1, self.customer_table.columnCount()):
                                item = self.customer_table.item(row, col)
                                row_data.append(item.text() if item else "")
                            writer.writerow(row_data)
                
                MessageHelper.show_success(self, f"CSVファイルを出力しました:\n{file_path}")
                
        except Exception as e:
            MessageHelper.show_error(self, f"CSV出力中にエラーが発生しました: {str(e)}")