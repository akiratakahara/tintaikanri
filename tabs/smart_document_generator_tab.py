"""
スマート契約書・重説生成タブ（改良版）

機能:
1. テンプレート選択（2段階: 用途 → 契約種別）
2. 契約データから変数を自動抽出・補完
3. プレビュー＆編集
4. Word/PDF出力
"""
import os
import sys
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QLineEdit,
    QTextEdit, QMessageBox, QGroupBox, QFormLayout,
    QComboBox, QFileDialog, QDialog, QDialogButtonBox,
    QTabWidget, QProgressDialog, QSplitter, QListWidget,
    QRadioButton, QButtonGroup, QScrollArea, QCheckBox, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import get_db_connection, TenantContract
from utils.document_engine import get_document_engine
from utils.application_form_ocr import get_application_form_ocr
from utils.contract_template_filler import get_contract_filler
from utils.additional_document_filler import get_additional_document_filler


class VariableExtractor:
    """変数抽出クラス - データベースから契約書に必要な変数を抽出"""

    def __init__(self, contract_id: int):
        self.contract_id = contract_id

    def extract_all_variables(self):
        """全変数を抽出（定期借家契約書用の全50フィールドを含む）"""

        conn = get_db_connection()
        try:
            # 契約情報を取得
            cursor = conn.cursor()
            cursor.execute('''
                SELECT tc.*,
                       COALESCE(p.name, p2.name) as property_name,
                       COALESCE(p.address, p2.address) as property_address,
                       u.room_number, u.floor, u.layout,
                       COALESCE(u.property_id, tc.property_id) as property_id
                FROM tenant_contracts tc
                LEFT JOIN units u ON tc.unit_id = u.id
                LEFT JOIN properties p ON u.property_id = p.id
                LEFT JOIN properties p2 ON tc.property_id = p2.id
                WHERE tc.id = ?
            ''', (self.contract_id,))
            row = cursor.fetchone()

            if not row:
                raise ValueError(f"契約ID {self.contract_id} が見つかりません")

            contract = dict(row)

            # 変数マップを作成
            variables = {}

            # === テーブル1: 物件情報（12フィールド） ===
            variables['建物名称'] = contract.get('property_name', '')
            variables['建物所在地_住居表示'] = contract.get('property_address', '')
            variables['建物所在地_登記簿'] = contract.get('property_address', '')  # 通常は同じ
            variables['建物構造'] = '鉄筋コンクリート造'  # デフォルト値
            variables['建物種類'] = '共同住宅'  # デフォルト値
            variables['新築年月'] = ''  # 物件マスタから取得予定
            variables['間取り'] = contract.get('layout', '')
            variables['専有面積'] = str(contract.get('area', '')) if contract.get('area') else ''
            variables['駐車場'] = '無'
            variables['バイク置場'] = '無'
            variables['駐輪場'] = '無'
            variables['物置'] = '無'
            variables['専用庭'] = '無'

            # === テーブル2: 契約期間（2フィールド） ===
            variables['契約開始日'] = self._format_date(contract.get('start_date'))
            variables['契約終了日'] = self._format_date(contract.get('end_date'))
            variables['契約年数'] = self._calculate_contract_years(contract.get('start_date'), contract.get('end_date'))
            variables['鍵引渡し日'] = self._format_date(contract.get('start_date'))  # 通常は契約開始日と同じ

            # === テーブル3: 賃料等（10+フィールド） ===
            rent = contract.get('monthly_rent', 0) or contract.get('rent', 0)
            common_fee = contract.get('common_fee', 0)
            deposit = contract.get('deposit', 0)
            key_money = contract.get('key_money', 0)

            variables['賃料'] = f"{int(rent):,}" if rent else '0'
            variables['共益費'] = f"{int(common_fee):,}" if common_fee else '0'
            variables['敷金'] = f"{int(deposit):,}" if deposit else '0'
            variables['礼金'] = f"{int(key_money):,}" if key_money else '0'
            variables['賃料_支払日'] = '当月末日まで'
            variables['賃料_支払方法'] = '銀行振込'
            variables['保証金'] = '0'
            variables['償却額'] = '0'
            variables['仲介手数料'] = f"{int(rent):,}" if rent else '0'
            variables['火災保険料'] = '20,000'
            variables['保証委託料'] = f"{int(rent * 0.5):,}" if rent else '0'

            # === テーブル4: 賃借人・緊急連絡先（15+フィールド） ===
            variables['賃借人氏名'] = contract.get('contractor_name', '') or contract.get('tenant_name', '') or contract.get('customer_name', '')
            variables['賃借人関係'] = '本人'
            variables['賃借人生年月日'] = ''
            variables['賃借人現住所'] = ''
            variables['賃借人電話'] = ''
            variables['賃借人携帯'] = ''
            variables['賃借人勤務先'] = ''
            variables['賃借人勤務先住所'] = ''
            variables['賃借人勤務先電話'] = ''
            variables['賃借人メール'] = ''

            variables['緊急連絡先氏名'] = ''
            variables['緊急連絡先続柄'] = ''
            variables['緊急連絡先住所'] = ''
            variables['緊急連絡先電話'] = ''
            variables['緊急連絡先携帯'] = ''

            # === テーブル5: 賃貸人（2フィールド） ===
            variables['賃貸人氏名'] = contract.get('owner_name', '') or '株式会社久松'
            variables['賃貸人住所'] = '福岡県福岡市博多区博多駅前'

            # === テーブル6: 管理者等（5フィールド） ===
            variables['管理者名称'] = '株式会社久松'
            variables['管理者所在地'] = '福岡県福岡市博多区博多駅前'
            variables['管理者電話'] = '092-XXX-XXXX'
            variables['管理者FAX'] = '092-XXX-XXXX'
            variables['管理者免許番号'] = '福岡県知事(X)第XXXXX号'

            # === その他の情報 ===
            variables['契約ID'] = str(contract['id'])
            variables['契約日'] = self._format_date(datetime.now())
            variables['物件所在'] = contract.get('property_address', '')
            variables['物件名称'] = contract.get('property_name', '')
            variables['貸室'] = contract.get('room_number', '')
            variables['面積'] = f"{contract.get('area', '')}㎡" if contract.get('area') else ''

            return variables

        finally:
            conn.close()

    def _format_date(self, date):
        """日付をフォーマット"""
        if not date:
            return ''
        if isinstance(date, str):
            # YYYY-MM-DD形式を日本語形式に変換
            try:
                dt = datetime.strptime(date, '%Y-%m-%d')
                return dt.strftime('%Y年%m月%d日')
            except:
                return date
        return date.strftime('%Y年%m月%d日')

    def _calculate_contract_years(self, start_date, end_date):
        """契約年数を計算"""
        if not start_date or not end_date:
            return '2'  # デフォルト値

        try:
            if isinstance(start_date, str):
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                start_dt = start_date

            if isinstance(end_date, str):
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            else:
                end_dt = end_date

            # 年数を計算（月数 / 12）
            months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
            years = months / 12

            # 整数または小数第1位まで
            if years == int(years):
                return str(int(years))
            else:
                return f"{years:.1f}"
        except:
            return '2'  # エラー時はデフォルト値


class CustomerSelector(QDialog):
    """顧客選択ダイアログ"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_customer = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("賃借人を選択")
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout()

        # 説明
        label = QLabel("賃借人（顧客）を選択してください:")
        layout.addWidget(label)

        # 顧客一覧テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "顧客ID", "氏名", "電話番号", "メールアドレス", "住所"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.doubleClicked.connect(self.accept)

        layout.addWidget(self.table)

        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

        # データをロード
        self.load_customers()

    def load_customers(self):
        """顧客データをロード"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, phone, email, address
                FROM customers
                ORDER BY name
            ''')
            rows = cursor.fetchall()
            conn.close()

            self.table.setRowCount(len(rows))

            for row_idx, row in enumerate(rows):
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(row['id'])))
                self.table.setItem(row_idx, 1, QTableWidgetItem(row['name'] or ''))
                self.table.setItem(row_idx, 2, QTableWidgetItem(row['phone'] or ''))
                self.table.setItem(row_idx, 3, QTableWidgetItem(row['email'] or ''))
                self.table.setItem(row_idx, 4, QTableWidgetItem(row['address'] or ''))

            self.table.resizeColumnsToContents()

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"顧客データの読み込みに失敗しました:\n{str(e)}")

    def accept(self):
        """OK時の処理"""
        selected_rows = self.table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            customer_id = int(self.table.item(row, 0).text())
            self.selected_customer = customer_id
            super().accept()
        else:
            QMessageBox.warning(self, "選択してください", "顧客を選択してください")


class PropertySelector(QDialog):
    """物件・部屋選択ダイアログ"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_property = None
        self.selected_unit = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("物件・部屋を選択")
        self.setMinimumSize(900, 600)

        layout = QVBoxLayout()

        # 説明
        label = QLabel("物件と部屋を選択してください:")
        layout.addWidget(label)

        # 物件・部屋一覧テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "物件ID", "部屋ID", "物件名", "部屋番号", "間取り", "面積(㎡)", "賃料"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.doubleClicked.connect(self.accept)

        layout.addWidget(self.table)

        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

        # データをロード
        self.load_properties()

    def load_properties(self):
        """物件・部屋データをロード"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT
                    p.id as property_id,
                    u.id as unit_id,
                    p.name as property_name,
                    u.room_number,
                    u.layout,
                    u.area,
                    u.rent
                FROM properties p
                LEFT JOIN units u ON u.property_id = p.id
                WHERE u.id IS NOT NULL AND u.status = '空室'
                ORDER BY p.name, u.room_number
            ''')
            rows = cursor.fetchall()
            conn.close()

            self.table.setRowCount(len(rows))

            for row_idx, row in enumerate(rows):
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(row['property_id'])))
                self.table.setItem(row_idx, 1, QTableWidgetItem(str(row['unit_id'])))
                self.table.setItem(row_idx, 2, QTableWidgetItem(row['property_name'] or ''))
                self.table.setItem(row_idx, 3, QTableWidgetItem(row['room_number'] or ''))
                self.table.setItem(row_idx, 4, QTableWidgetItem(row['layout'] or ''))
                self.table.setItem(row_idx, 5, QTableWidgetItem(str(row['area']) if row['area'] else ''))
                self.table.setItem(row_idx, 6, QTableWidgetItem(f"¥{row['rent']:,}" if row['rent'] else ''))

            self.table.resizeColumnsToContents()

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"物件データの読み込みに失敗しました:\n{str(e)}")

    def accept(self):
        """OK時の処理"""
        selected_rows = self.table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            property_id = int(self.table.item(row, 0).text())
            unit_id = int(self.table.item(row, 1).text())
            self.selected_property = property_id
            self.selected_unit = unit_id
            super().accept()
        else:
            QMessageBox.warning(self, "選択してください", "物件・部屋を選択してください")


class ContractSelector(QDialog):
    """契約選択ダイアログ"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_contract = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("契約を選択")
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout()

        # 説明
        label = QLabel("書類を生成する契約を選択してください:")
        layout.addWidget(label)

        # 契約一覧テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "契約ID", "賃借人", "物件名", "賃料", "契約開始日", "契約終了日"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.doubleClicked.connect(self.accept)

        layout.addWidget(self.table)

        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

        # データをロード
        self.load_contracts()

    def load_contracts(self):
        """契約データをロード"""
        try:
            # SQLite3で全契約を取得
            contracts = TenantContract.get_all()

            self.table.setRowCount(len(contracts))

            for row, contract in enumerate(contracts):
                # ID
                self.table.setItem(row, 0, QTableWidgetItem(str(contract['id'])))

                # 賃借人
                customer_name = contract.get('contractor_name', '') or contract.get('tenant_name', '')
                self.table.setItem(row, 1, QTableWidgetItem(customer_name))

                # 物件名
                property_name = ''
                if contract.get('property_name'):
                    room_number = contract.get('room_number', '')
                    property_name = f"{contract['property_name']}"
                    if room_number:
                        property_name += f" {room_number}"
                self.table.setItem(row, 2, QTableWidgetItem(property_name))

                # 賃料
                rent = contract.get('rent', 0)
                rent_str = f"¥{rent:,}" if rent else ''
                self.table.setItem(row, 3, QTableWidgetItem(rent_str))

                # 開始日
                start_date = contract.get('start_date', '')
                self.table.setItem(row, 4, QTableWidgetItem(start_date or ''))

                # 終了日
                end_date = contract.get('end_date', '')
                self.table.setItem(row, 5, QTableWidgetItem(end_date or ''))

            self.table.resizeColumnsToContents()

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"契約データの読み込みに失敗しました:\n{str(e)}")

    def accept(self):
        """OK時の処理"""
        selected_rows = self.table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            contract_id = int(self.table.item(row, 0).text())
            self.selected_contract = contract_id
            super().accept()
        else:
            QMessageBox.warning(self, "選択してください", "契約を選択してください")


class SmartDocumentGeneratorTab(QWidget):
    """スマート契約書・重説生成タブ"""

    def __init__(self):
        super().__init__()
        self.selected_contract_id = None
        self.selected_template_type = None
        self.selected_customer_id = None  # 選択された顧客ID
        self.selected_property_id = None  # 選択された物件ID
        self.selected_unit_id = None  # 選択された部屋ID
        self.selected_owner_id = None  # 選択された賃貸人（オーナー）ID
        self.variables = {}
        self.evidence_documents = {}  # エビデンス資料を保存 {資料名: ファイルパス}
        self.init_ui()

    def init_ui(self):
        """UIの初期化"""
        main_layout = QVBoxLayout()

        # タイトル
        title_label = QLabel("📝 スマート契約書・重説生成システム")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        desc_label = QLabel("契約データから自動で契約書・重説を生成します")
        main_layout.addWidget(desc_label)

        # ステップ表示
        steps_layout = QHBoxLayout()

        self.step1_label = self._create_step_label("1️⃣ 契約選択", True)
        self.step2_label = self._create_step_label("2️⃣ テンプレート選択", False)
        self.step3_label = self._create_step_label("3️⃣ 変数確認", False)
        self.step4_label = self._create_step_label("4️⃣ 生成", False)

        steps_layout.addWidget(self.step1_label)
        steps_layout.addWidget(QLabel("→"))
        steps_layout.addWidget(self.step2_label)
        steps_layout.addWidget(QLabel("→"))
        steps_layout.addWidget(self.step3_label)
        steps_layout.addWidget(QLabel("→"))
        steps_layout.addWidget(self.step4_label)
        steps_layout.addStretch()

        main_layout.addLayout(steps_layout)

        # コンテンツエリア（スクロール可能）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.content_layout = QVBoxLayout(scroll_widget)

        # ステップ1: 契約選択（オプション）
        self.step1_group = self._create_contract_selection_group()
        self.content_layout.addWidget(self.step1_group)

        # ステップ2: テンプレート選択（最初から有効）
        self.step2_group = self._create_template_selection_group()
        self.step2_group.setEnabled(True)
        self.content_layout.addWidget(self.step2_group)

        # ステップ3: 変数確認
        self.step3_group = self._create_variable_review_group()
        self.step3_group.setEnabled(False)
        self.content_layout.addWidget(self.step3_group)

        # ステップ4: 生成
        self.step4_group = self._create_generation_group()
        self.step4_group.setEnabled(False)
        self.content_layout.addWidget(self.step4_group)

        self.content_layout.addStretch()
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

        self.setLayout(main_layout)

    def _create_step_label(self, text, active=False):
        """ステップラベルを作成"""
        label = QLabel(text)
        font = QFont()
        font.setBold(active)
        label.setFont(font)
        if active:
            label.setStyleSheet("color: #0066CC; font-size: 12pt;")
        else:
            label.setStyleSheet("color: #999999; font-size: 12pt;")
        return label

    def _update_step_status(self, step):
        """ステップのステータスを更新"""
        steps = [self.step1_label, self.step2_label, self.step3_label, self.step4_label]
        for i, label in enumerate(steps, 1):
            if i == step:
                label.setStyleSheet("color: #0066CC; font-size: 12pt; font-weight: bold;")
            elif i < step:
                label.setStyleSheet("color: #00AA00; font-size: 12pt; font-weight: bold;")
            else:
                label.setStyleSheet("color: #999999; font-size: 12pt;")

    def _create_contract_selection_group(self):
        """ステップ1: 契約選択グループ"""
        group = QGroupBox("ステップ1: 契約を選択（オプション）")

        layout = QVBoxLayout()

        # 説明
        desc = QLabel("既存の契約から自動入力する場合は契約を選択してください。\n契約がない場合はそのまま次のステップへ進めます。")
        desc.setStyleSheet("color: #666;")
        layout.addWidget(desc)

        # 選択した契約の表示
        info_layout = QFormLayout()
        self.contract_id_label = QLabel("未選択")
        self.contract_customer_label = QLabel("―")
        self.contract_property_label = QLabel("―")
        self.contract_rent_label = QLabel("―")

        info_layout.addRow("契約ID:", self.contract_id_label)
        info_layout.addRow("賃借人:", self.contract_customer_label)
        info_layout.addRow("物件:", self.contract_property_label)
        info_layout.addRow("賃料:", self.contract_rent_label)

        layout.addLayout(info_layout)

        # 選択ボタン
        select_btn = QPushButton("📋 契約を選択")
        select_btn.clicked.connect(self.select_contract)
        layout.addWidget(select_btn)

        group.setLayout(layout)
        return group

    def _create_template_selection_group(self):
        """ステップ2: テンプレート選択グループ"""
        group = QGroupBox("ステップ2: テンプレートを選択")

        layout = QVBoxLayout()

        # 説明
        desc = QLabel("生成する書類の種類を選択してください。")
        layout.addWidget(desc)

        # 書類種別
        doc_type_layout = QHBoxLayout()
        doc_type_label = QLabel("書類種別:")
        self.doc_type_combo = QComboBox()
        self.doc_type_combo.addItems(["契約書", "重要事項説明書", "契約金明細書", "預かり証"])
        self.doc_type_combo.currentTextChanged.connect(self.on_doc_type_changed)
        doc_type_layout.addWidget(doc_type_label)
        doc_type_layout.addWidget(self.doc_type_combo)
        doc_type_layout.addStretch()
        layout.addLayout(doc_type_layout)

        # 用途選択
        usage_label = QLabel("【用途を選択】")
        usage_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(usage_label)

        self.usage_group = QButtonGroup(self)
        usage_layout = QHBoxLayout()

        self.residential_radio = QRadioButton("🏠 居住用")
        self.office_radio = QRadioButton("🏢 事務所・店舗")

        self.usage_group.addButton(self.residential_radio, 1)
        self.usage_group.addButton(self.office_radio, 2)

        usage_layout.addWidget(self.residential_radio)
        usage_layout.addWidget(self.office_radio)
        usage_layout.addStretch()

        layout.addLayout(usage_layout)

        # 契約種別選択
        contract_type_label = QLabel("【契約種別を選択】")
        contract_type_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(contract_type_label)

        self.contract_type_group = QButtonGroup(self)
        contract_type_layout = QHBoxLayout()

        self.teiki_radio = QRadioButton("📅 定期借家（更新なし）")
        self.futsu_radio = QRadioButton("🔄 普通借家（更新あり）")

        self.contract_type_group.addButton(self.teiki_radio, 1)
        self.contract_type_group.addButton(self.futsu_radio, 2)

        contract_type_layout.addWidget(self.teiki_radio)
        contract_type_layout.addWidget(self.futsu_radio)
        contract_type_layout.addStretch()

        layout.addLayout(contract_type_layout)

        # 選択確定ボタン
        confirm_btn = QPushButton("✓ テンプレート選択を確定")
        confirm_btn.clicked.connect(self.confirm_template_selection)
        layout.addWidget(confirm_btn)

        group.setLayout(layout)
        return group

    def _create_variable_review_group(self):
        """ステップ3: 変数確認グループ（エビデンス資料管理統合版）"""
        group = QGroupBox("ステップ3: 変数入力とエビデンス資料管理")

        layout = QVBoxLayout()

        # 説明
        desc = QLabel("📋 契約書作成に必要な情報を入力し、エビデンス資料をアップロードしてください")
        desc.setStyleSheet("font-size: 11pt; font-weight: bold; color: #0066CC; margin-bottom: 10px;")
        layout.addWidget(desc)

        # エビデンス資料の完全性チェック表示
        self.evidence_status_label = QLabel("📊 エビデンス資料: 0/6 準備完了")
        self.evidence_status_label.setStyleSheet("""
            background-color: #FFF3CD;
            color: #856404;
            padding: 10px;
            border-radius: 5px;
            font-weight: bold;
            border: 1px solid #FFE69C;
        """)
        layout.addWidget(self.evidence_status_label)

        # タブウィジェットでエビデンス資料別に分類
        self.evidence_tabs = QTabWidget()
        self.evidence_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #DDD;
                background: white;
            }
            QTabBar::tab {
                background: #F5F5F5;
                border: 1px solid #DDD;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 2px solid #0066CC;
                font-weight: bold;
            }
        """)

        # タブ1: 申込書
        self.evidence_tabs.addTab(self._create_evidence_tab_application(), "📄 申込書")

        # タブ2: 本人確認書類
        self.evidence_tabs.addTab(self._create_evidence_tab_identification(), "🪪 本人確認書類")

        # タブ3: 物件資料
        self.evidence_tabs.addTab(self._create_evidence_tab_property(), "🏢 物件資料")

        # タブ4: 賃貸人情報
        self.evidence_tabs.addTab(self._create_evidence_tab_landlord(), "👤 賃貸人情報")

        # タブ5: 管理会社情報
        self.evidence_tabs.addTab(self._create_evidence_tab_manager(), "🏦 管理会社情報")

        # タブ6: その他資料
        self.evidence_tabs.addTab(self._create_evidence_tab_others(), "📎 その他資料")

        layout.addWidget(self.evidence_tabs)

        # 申込書アップロード機能（旧版、後で削除可能）
        upload_frame = QFrame()
        upload_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #D0D0D0;
                border-radius: 6px;
                padding: 20px;
                margin: 10px 0px;
            }
        """)
        upload_layout = QVBoxLayout(upload_frame)
        upload_layout.setSpacing(12)

        # タイトルと説明を横並び
        header_layout = QHBoxLayout()

        upload_icon_title = QLabel("📤 申込書から自動入力")
        upload_icon_title.setStyleSheet("""
            font-size: 11pt;
            font-weight: bold;
            color: #333;
            margin: 0px;
            padding: 0px;
        """)
        header_layout.addWidget(upload_icon_title)

        optional_badge = QLabel("オプション")
        optional_badge.setStyleSheet("""
            background-color: #E8F4FD;
            color: #0066CC;
            border-radius: 3px;
            padding: 2px 8px;
            font-size: 8pt;
            font-weight: bold;
        """)
        optional_badge.setMaximumHeight(20)
        header_layout.addWidget(optional_badge)
        header_layout.addStretch()

        upload_layout.addLayout(header_layout)

        upload_desc = QLabel("Word/PDFの申込書をアップロードすると、賃借人情報を自動で読み取って入力できます")
        upload_desc.setStyleSheet("color: #666; font-size: 9pt; margin: 0px; padding: 0px;")
        upload_desc.setWordWrap(True)
        upload_layout.addWidget(upload_desc)

        # ボタンとステータスを横並び
        button_status_layout = QHBoxLayout()

        self.upload_application_btn = QPushButton("📄 ファイルを選択")
        self.upload_application_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066CC;
                color: white;
                border: none;
                padding: 10px 24px;
                border-radius: 5px;
                font-size: 10pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0052A3;
            }
        """)
        self.upload_application_btn.clicked.connect(self.upload_application_form)
        button_status_layout.addWidget(self.upload_application_btn)

        self.upload_status_label = QLabel("")
        self.upload_status_label.setStyleSheet("""
            color: #28A745;
            font-size: 9pt;
            margin-left: 15px;
            padding: 0px;
        """)
        button_status_layout.addWidget(self.upload_status_label)
        button_status_layout.addStretch()

        upload_layout.addLayout(button_status_layout)

        layout.addWidget(upload_frame)

        # 変数テーブル（サイズを大きく）
        table_label = QLabel("📝 変数一覧（クリックして直接編集できます）")
        table_label.setStyleSheet("font-size: 10pt; font-weight: bold; margin-top: 10px;")
        layout.addWidget(table_label)

        self.variables_table = QTableWidget()
        self.variables_table.setColumnCount(3)
        self.variables_table.setHorizontalHeaderLabels(["変数名", "値", "データソース"])

        # テーブルのスタイリング
        self.variables_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #DDD;
                gridline-color: #E0E0E0;
                font-size: 10pt;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                padding: 10px;
                border: 1px solid #DDD;
                font-weight: bold;
            }
        """)

        # 列幅の調整
        self.variables_table.setColumnWidth(0, 180)
        self.variables_table.setColumnWidth(1, 400)
        self.variables_table.setColumnWidth(2, 150)

        # 列のリサイズモードを設定
        header = self.variables_table.horizontalHeader()
        header.setStretchLastSection(False)
        from PyQt6.QtWidgets import QHeaderView
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        # 最小高さを設定（より大きく）
        self.variables_table.setMinimumHeight(400)

        # 行の高さを自動調整
        self.variables_table.verticalHeader().setDefaultSectionSize(35)

        layout.addWidget(self.variables_table)

        # ボタン行
        btn_layout = QHBoxLayout()

        update_btn = QPushButton("🔄 変数を再取得")
        update_btn.setStyleSheet("""
            QPushButton {
                background-color: #6C757D;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5A6268;
            }
        """)
        update_btn.clicked.connect(self.update_variables)
        btn_layout.addWidget(update_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 特記事項入力欄
        layout.addSpacing(15)
        special_label = QLabel("📝 特記事項（任意）")
        special_label.setStyleSheet("font-size: 10pt; font-weight: bold;")
        layout.addWidget(special_label)

        special_desc = QLabel("契約書に追加する特記事項を入力してください。空白の場合は追加されません。")
        special_desc.setStyleSheet("color: #666; font-size: 9pt;")
        layout.addWidget(special_desc)

        self.special_notes_edit = QTextEdit()
        self.special_notes_edit.setPlaceholderText("例：\n・ペット飼育可（小型犬1匹まで）\n・楽器使用可（防音対策必須）\n・駐車場1台分込み")
        self.special_notes_edit.setMinimumHeight(120)
        self.special_notes_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #DDD;
                border-radius: 4px;
                padding: 10px;
                font-size: 10pt;
            }
        """)
        layout.addWidget(self.special_notes_edit)

        # 次へボタン
        next_btn = QPushButton("→ 次へ（書類生成）")
        next_btn.setStyleSheet("""
            QPushButton {
                background-color: #28A745;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 5px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        next_btn.clicked.connect(self.proceed_to_generation)
        layout.addWidget(next_btn)

        group.setLayout(layout)
        return group

    def _create_evidence_tab_application(self):
        """賃借人（顧客）選択タブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # タイトル
        title = QLabel("👥 賃借人情報")
        title.setStyleSheet("font-size: 12pt; font-weight: bold; color: #333; margin-bottom: 5px;")
        layout.addWidget(title)

        desc = QLabel("顧客データベースから賃借人を選択するか、申込書をアップロードして自動入力してください。")
        desc.setStyleSheet("color: #666; font-size: 9pt; margin-bottom: 15px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # 顧客選択ボタン
        select_customer_btn = QPushButton("📋 顧客データベースから選択")
        select_customer_btn.setStyleSheet("""
            QPushButton {
                background-color: #28A745;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        select_customer_btn.clicked.connect(self.select_customer)
        layout.addWidget(select_customer_btn)

        # 選択された顧客情報表示
        self.selected_customer_label = QLabel("顧客: 未選択")
        self.selected_customer_label.setStyleSheet("font-size: 10pt; color: #999; padding: 10px; background-color: #F8F9FA; border-radius: 4px;")
        layout.addWidget(self.selected_customer_label)

        # 区切り線
        separator1 = QLabel("または")
        separator1.setStyleSheet("text-align: center; color: #999; font-size: 9pt; margin: 10px 0px;")
        separator1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(separator1)

        # 申込書アップロードボタン
        upload_btn = QPushButton("📤 申込書をアップロード（OCR自動入力）")
        upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066CC;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0052A3;
            }
        """)
        upload_btn.clicked.connect(lambda: self.upload_evidence_document("申込書"))
        layout.addWidget(upload_btn)

        self.application_status_label = QLabel("未アップロード")
        self.application_status_label.setStyleSheet("color: #999; font-size: 9pt;")
        layout.addWidget(self.application_status_label)

        layout.addStretch()
        return widget

    def _create_evidence_tab_identification(self):
        """本人確認書類タブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        title = QLabel("🪪 本人確認書類")
        title.setStyleSheet("font-size: 12pt; font-weight: bold; color: #333;")
        layout.addWidget(title)

        desc = QLabel("運転免許証、健康保険証、マイナンバーカード等の本人確認書類をアップロードしてください。")
        desc.setStyleSheet("color: #666; font-size: 9pt;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        upload_btn = QPushButton("📤 本人確認書類をアップロード")
        upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066CC;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0052A3;
            }
        """)
        upload_btn.clicked.connect(lambda: self.upload_evidence_document("本人確認書類"))
        layout.addWidget(upload_btn)

        self.identification_status_label = QLabel("未アップロード")
        self.identification_status_label.setStyleSheet("color: #999; font-size: 9pt;")
        layout.addWidget(self.identification_status_label)

        layout.addStretch()
        return widget

    def _create_evidence_tab_property(self):
        """物件・部屋選択タブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        title = QLabel("🏢 物件・部屋情報")
        title.setStyleSheet("font-size: 12pt; font-weight: bold; color: #333;")
        layout.addWidget(title)

        desc = QLabel("物件データベースから物件・部屋を選択してください。物件情報が自動で入力されます。")
        desc.setStyleSheet("color: #666; font-size: 9pt;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # 物件選択ボタン
        select_property_btn = QPushButton("🏠 物件・部屋データベースから選択")
        select_property_btn.setStyleSheet("""
            QPushButton {
                background-color: #28A745;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        select_property_btn.clicked.connect(self.select_property)
        layout.addWidget(select_property_btn)

        # 選択された物件情報表示
        self.selected_property_label = QLabel("物件: 未選択")
        self.selected_property_label.setStyleSheet("font-size: 10pt; color: #999; padding: 10px; background-color: #F8F9FA; border-radius: 4px;")
        layout.addWidget(self.selected_property_label)

        self.property_status_label = QLabel("")
        layout.addWidget(self.property_status_label)

        layout.addStretch()
        return widget

    def _create_evidence_tab_landlord(self):
        """賃貸人情報タブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        title = QLabel("👤 賃貸人情報")
        title.setStyleSheet("font-size: 12pt; font-weight: bold; color: #333;")
        layout.addWidget(title)

        desc = QLabel("賃貸人(オーナー)の情報資料をアップロードしてください。")
        desc.setStyleSheet("color: #666; font-size: 9pt;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        upload_btn = QPushButton("📤 賃貸人情報をアップロード")
        upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066CC;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0052A3;
            }
        """)
        upload_btn.clicked.connect(lambda: self.upload_evidence_document("賃貸人情報"))
        layout.addWidget(upload_btn)

        self.landlord_status_label = QLabel("未アップロード")
        self.landlord_status_label.setStyleSheet("color: #999; font-size: 9pt;")
        layout.addWidget(self.landlord_status_label)

        # 賃貸人情報入力フォーム
        form_layout = QFormLayout()
        self.landlord_name = QLineEdit()
        self.landlord_address = QLineEdit()

        form_layout.addRow("賃貸人氏名:", self.landlord_name)
        form_layout.addRow("賃貸人住所:", self.landlord_address)

        layout.addLayout(form_layout)
        layout.addStretch()
        return widget

    def _create_evidence_tab_manager(self):
        """管理会社情報タブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        title = QLabel("🏦 管理会社情報")
        title.setStyleSheet("font-size: 12pt; font-weight: bold; color: #333;")
        layout.addWidget(title)

        desc = QLabel("管理会社の情報資料をアップロードしてください。")
        desc.setStyleSheet("color: #666; font-size: 9pt;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        upload_btn = QPushButton("📤 管理会社情報をアップロード")
        upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066CC;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0052A3;
            }
        """)
        upload_btn.clicked.connect(lambda: self.upload_evidence_document("管理会社情報"))
        layout.addWidget(upload_btn)

        self.manager_status_label = QLabel("未アップロード")
        self.manager_status_label.setStyleSheet("color: #999; font-size: 9pt;")
        layout.addWidget(self.manager_status_label)

        # 管理会社情報入力フォーム
        form_layout = QFormLayout()
        self.manager_name = QLineEdit()
        self.manager_name.setText("株式会社久松")
        self.manager_address = QLineEdit()
        self.manager_phone = QLineEdit()
        self.manager_fax = QLineEdit()
        self.manager_license = QLineEdit()

        form_layout.addRow("管理者名称:", self.manager_name)
        form_layout.addRow("管理者所在地:", self.manager_address)
        form_layout.addRow("管理者電話:", self.manager_phone)
        form_layout.addRow("管理者FAX:", self.manager_fax)
        form_layout.addRow("管理者免許番号:", self.manager_license)

        layout.addLayout(form_layout)
        layout.addStretch()
        return widget

    def _create_evidence_tab_others(self):
        """その他資料タブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        title = QLabel("📎 その他資料・契約条件")
        title.setStyleSheet("font-size: 12pt; font-weight: bold; color: #333;")
        layout.addWidget(title)

        desc = QLabel("契約期間、賃料、敷金・礼金などの契約条件を入力してください。")
        desc.setStyleSheet("color: #666; font-size: 9pt;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # 契約条件入力フォーム
        form_layout = QFormLayout()

        self.contract_start_date = QLineEdit()
        self.contract_end_date = QLineEdit()
        self.contract_years = QLineEdit()
        self.contract_years.setText("2")
        self.key_delivery_date = QLineEdit()

        self.rent = QLineEdit()
        self.common_fee = QLineEdit()
        self.deposit = QLineEdit()
        self.key_money = QLineEdit()
        self.rent_payment_day = QLineEdit()
        self.rent_payment_day.setText("当月末日まで")
        self.rent_payment_method = QLineEdit()
        self.rent_payment_method.setText("銀行振込")

        form_layout.addRow("契約開始日:", self.contract_start_date)
        form_layout.addRow("契約終了日:", self.contract_end_date)
        form_layout.addRow("契約年数:", self.contract_years)
        form_layout.addRow("鍵引渡し日:", self.key_delivery_date)
        form_layout.addRow("賃料:", self.rent)
        form_layout.addRow("共益費:", self.common_fee)
        form_layout.addRow("敷金:", self.deposit)
        form_layout.addRow("礼金:", self.key_money)
        form_layout.addRow("賃料支払日:", self.rent_payment_day)
        form_layout.addRow("賃料支払方法:", self.rent_payment_method)

        layout.addLayout(form_layout)
        layout.addStretch()
        return widget

    def select_customer(self):
        """顧客を選択して賃借人情報を自動入力"""
        dialog = CustomerSelector(self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.selected_customer_id = dialog.selected_customer

            # 顧客情報を取得
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM customers WHERE id = ?
                ''', (self.selected_customer_id,))
                customer = cursor.fetchone()
                conn.close()

                if customer:
                    # 表示を更新
                    self.selected_customer_label.setText(
                        f"✓ 顧客選択済: {customer['name']} ({customer['phone'] or '電話番号なし'})"
                    )
                    self.selected_customer_label.setStyleSheet("font-size: 10pt; color: #28A745; font-weight: bold; padding: 10px; background-color: #D4EDDA; border-radius: 4px;")

                    QMessageBox.information(self, "顧客選択完了", f"賃借人: {customer['name']}\n顧客情報が設定されました。")

            except Exception as e:
                QMessageBox.critical(self, "エラー", f"顧客情報の取得に失敗しました:\n{str(e)}")

    def select_property(self):
        """物件・部屋を選択して物件情報を自動入力"""
        dialog = PropertySelector(self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.selected_property_id = dialog.selected_property
            self.selected_unit_id = dialog.selected_unit

            # 物件・部屋情報を取得
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT
                        p.*,
                        u.room_number, u.layout, u.area, u.rent
                    FROM properties p
                    LEFT JOIN units u ON u.property_id = p.id
                    WHERE p.id = ? AND u.id = ?
                ''', (self.selected_property_id, self.selected_unit_id))
                property_unit = cursor.fetchone()
                conn.close()

                if property_unit:
                    # 表示を更新
                    self.selected_property_label.setText(
                        f"✓ 物件選択済: {property_unit['name']} {property_unit['room_number']} ({property_unit['layout']}, {property_unit['area']}㎡)"
                    )
                    self.selected_property_label.setStyleSheet("font-size: 10pt; color: #28A745; font-weight: bold; padding: 10px; background-color: #D4EDDA; border-radius: 4px;")

                    QMessageBox.information(self, "物件選択完了", f"物件: {property_unit['name']} {property_unit['room_number']}\n物件情報が設定されました。")

            except Exception as e:
                QMessageBox.critical(self, "エラー", f"物件情報の取得に失敗しました:\n{str(e)}")

    def upload_evidence_document(self, doc_type):
        """エビデンス資料をアップロード"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                f"{doc_type}を選択",
                "",
                "すべてのファイル (*.pdf *.doc *.docx *.jpg *.jpeg *.png);;PDF (*.pdf);;Word (*.doc *.docx);;画像 (*.jpg *.jpeg *.png)"
            )

            if not file_path:
                return

            # ファイルパスを保存
            self.evidence_documents[doc_type] = file_path

            # ステータスラベルを更新
            file_name = os.path.basename(file_path)
            status_labels = {
                "申込書": self.application_status_label,
                "本人確認書類": self.identification_status_label,
                "物件資料": self.property_status_label,
                "賃貸人情報": self.landlord_status_label,
                "管理会社情報": self.manager_status_label,
            }

            if doc_type in status_labels:
                status_labels[doc_type].setText(f"✓ {file_name}")
                status_labels[doc_type].setStyleSheet("color: #28A745; font-weight: bold; font-size: 9pt;")

            # 申込書の場合はOCR処理
            if doc_type == "申込書":
                self.process_application_ocr(file_path)

            # エビデンス資料の完全性チェックを更新
            self.update_evidence_status()

            QMessageBox.information(self, "アップロード完了", f"{doc_type}をアップロードしました:\n{file_name}")

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"ファイルのアップロードに失敗しました:\n{str(e)}")

    def process_application_ocr(self, file_path):
        """申込書をOCR処理して自動入力"""
        try:
            ocr = get_application_form_ocr()
            extracted_vars = ocr.extract_from_file(file_path)

            # フィールドにマッピング
            field_mapping = {
                '賃借人氏名': self.app_tenant_name,
                '賃借人生年月日': self.app_tenant_birthday,
                '賃借人現住所': self.app_tenant_address,
                '賃借人電話': self.app_tenant_phone,
                '賃借人携帯': self.app_tenant_mobile,
                '賃借人メール': self.app_tenant_email,
                '賃借人勤務先': self.app_tenant_workplace,
                '賃借人勤務先住所': self.app_tenant_workplace_address,
                '賃借人勤務先電話': self.app_tenant_workplace_phone,
                '緊急連絡先氏名': self.app_emergency_name,
                '緊急連絡先続柄': self.app_emergency_relation,
                '緊急連絡先住所': self.app_emergency_address,
                '緊急連絡先電話': self.app_emergency_phone,
                '緊急連絡先携帯': self.app_emergency_mobile,
            }

            for var_name, field in field_mapping.items():
                if var_name in extracted_vars:
                    field.setText(extracted_vars[var_name])

            QMessageBox.information(self, "OCR完了", f"{len(extracted_vars)}個の項目を自動入力しました")

        except Exception as e:
            QMessageBox.warning(self, "OCRエラー", f"OCR処理中にエラーが発生しました:\n{str(e)}")

    def update_evidence_status(self):
        """エビデンス資料の完全性チェックを更新"""
        total = 6
        uploaded = len(self.evidence_documents)

        self.evidence_status_label.setText(f"📊 エビデンス資料: {uploaded}/{total} 準備完了")

        if uploaded == total:
            self.evidence_status_label.setStyleSheet("""
                background-color: #D4EDDA;
                color: #155724;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                border: 1px solid #C3E6CB;
            """)
        elif uploaded > 0:
            self.evidence_status_label.setStyleSheet("""
                background-color: #FFF3CD;
                color: #856404;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                border: 1px solid #FFE69C;
            """)
        else:
            self.evidence_status_label.setStyleSheet("""
                background-color: #F8D7DA;
                color: #721C24;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                border: 1px solid #F5C6CB;
            """)

    def _create_generation_group(self):
        """ステップ4: 生成グループ"""
        group = QGroupBox("ステップ4: 書類を生成")

        layout = QVBoxLayout()

        # 説明
        desc = QLabel("書類を生成します。プレビューを確認してから出力できます。")
        layout.addWidget(desc)

        # プレビューエリア
        preview_label = QLabel("プレビュー:")
        layout.addWidget(preview_label)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(300)
        layout.addWidget(self.preview_text)

        # 生成ボタン
        btn_layout = QHBoxLayout()

        generate_btn = QPushButton("✨ プレビュー生成")
        generate_btn.clicked.connect(self.generate_preview)
        btn_layout.addWidget(generate_btn)

        export_word_btn = QPushButton("📄 Word出力")
        export_word_btn.clicked.connect(self.export_word)
        btn_layout.addWidget(export_word_btn)

        export_pdf_btn = QPushButton("📕 PDF出力")
        export_pdf_btn.clicked.connect(self.export_pdf)
        btn_layout.addWidget(export_pdf_btn)

        layout.addLayout(btn_layout)

        group.setLayout(layout)
        return group

    def select_contract(self):
        """契約を選択"""
        dialog = ContractSelector(self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.selected_contract_id = dialog.selected_contract

            # 契約情報を表示
            conn = get_db_connection()
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT tc.*,
                           COALESCE(p.name, p2.name) as property_name,
                           u.room_number, u.floor,
                           COALESCE(u.property_id, tc.property_id) as property_id
                    FROM tenant_contracts tc
                    LEFT JOIN units u ON tc.unit_id = u.id
                    LEFT JOIN properties p ON u.property_id = p.id
                    LEFT JOIN properties p2 ON tc.property_id = p2.id
                    WHERE tc.id = ?
                ''', (self.selected_contract_id,))
                row = cursor.fetchone()

                if row:
                    contract = dict(row)
                    self.contract_id_label.setText(str(contract['id']))

                    customer_name = contract.get('contractor_name', '') or contract.get('tenant_name', '')
                    self.contract_customer_label.setText(customer_name or '―')

                    property_text = ''
                    if contract.get('property_name'):
                        property_text = contract['property_name']
                        if contract.get('room_number'):
                            property_text += f" {contract['room_number']}"
                    self.contract_property_label.setText(property_text or '―')

                    rent = contract.get('rent', 0)
                    rent_text = f"¥{rent:,}/月" if rent else '―'
                    self.contract_rent_label.setText(rent_text)

                    # 既にテンプレートが選択されている場合は変数を更新
                    if self.selected_template_type and self.variables:
                        self.load_template_variables()
                        QMessageBox.information(self, "選択完了", "契約が選択され、変数が更新されました。")
                    else:
                        QMessageBox.information(self, "選択完了", "契約が選択されました。\nテンプレートを選択すると自動で値が入力されます。")
            finally:
                conn.close()

    def on_doc_type_changed(self, doc_type):
        """書類種別が変更された時の処理"""
        # 契約金明細書と預かり証の場合は用途・契約種別の選択を非表示
        is_simple_doc = doc_type in ["契約金明細書", "預かり証"]

        self.usage_group.buttons()[0].setVisible(not is_simple_doc)
        self.usage_group.buttons()[1].setVisible(not is_simple_doc)
        self.contract_type_group.buttons()[0].setVisible(not is_simple_doc)
        self.contract_type_group.buttons()[1].setVisible(not is_simple_doc)

    def confirm_template_selection(self):
        """テンプレート選択を確定"""
        doc_type = self.doc_type_combo.currentText()

        # 契約金明細書と預かり証は用途・契約種別不要
        if doc_type in ["契約金明細書", "預かり証"]:
            self.selected_template_type = doc_type

            # ステップ3を有効化
            self.step3_group.setEnabled(True)
            self._update_step_status(3)

            # テンプレートに応じた変数リストを表示
            self.load_template_variables()

            QMessageBox.information(
                self,
                "テンプレート選択完了",
                f"選択されたテンプレート:\n\n{doc_type}\n\n必要な情報を入力してください。"
            )
            return

        # 契約書・重説の場合は従来通り
        # 用途チェック
        if not self.usage_group.checkedButton():
            QMessageBox.warning(self, "選択してください", "用途を選択してください。")
            return

        # 契約種別チェック
        if not self.contract_type_group.checkedButton():
            QMessageBox.warning(self, "選択してください", "契約種別を選択してください。")
            return

        # 選択内容を保存
        usage = "居住用" if self.usage_group.checkedId() == 1 else "事務所"
        contract_type = "定期借家" if self.contract_type_group.checkedId() == 1 else "普通借家"

        self.selected_template_type = f"{doc_type}_{contract_type}_{usage}"

        # ステップ3を有効化
        self.step3_group.setEnabled(True)
        self._update_step_status(3)

        # テンプレートに応じた変数リストを表示（契約データなしでも表示）
        self.load_template_variables()

        QMessageBox.information(
            self,
            "テンプレート選択完了",
            f"選択されたテンプレート:\n\n{doc_type} - {contract_type} - {usage}\n\n変数を入力してください。\n契約を選択している場合は自動で値が入力されます。"
        )

    def load_template_variables(self):
        """テンプレートに応じた変数リストを読み込み（契約データなしでも表示）"""
        # 定期借家契約書の変数定義
        template_variables = self._get_template_variable_definitions()

        # 契約が選択されている場合はデータを取得
        if self.selected_contract_id:
            try:
                extractor = VariableExtractor(self.selected_contract_id)
                contract_data = extractor.extract_all_variables()
            except:
                contract_data = {}
        else:
            contract_data = {}

        # 変数を統合（テンプレート定義 + 契約データ）
        self.variables = {}
        for var_name, default_value in template_variables.items():
            # 契約データがあればそれを使用、なければデフォルト値
            self.variables[var_name] = contract_data.get(var_name, default_value)

        # テーブルに表示
        self.variables_table.setRowCount(len(self.variables))

        for row, (key, value) in enumerate(self.variables.items()):
            # 変数名
            var_name_item = QTableWidgetItem(key)
            var_name_item.setFlags(var_name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # 編集不可
            self.variables_table.setItem(row, 0, var_name_item)

            # 値（編集可能）
            self.variables_table.setItem(row, 1, QTableWidgetItem(str(value)))

            # データソース
            if self.selected_contract_id and value and value != '':
                source = "契約データ"
            else:
                source = "手動入力"
            source_item = QTableWidgetItem(source)
            source_item.setFlags(source_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # 編集不可
            self.variables_table.setItem(row, 2, source_item)

        self.variables_table.resizeColumnsToContents()

    def _get_template_variable_definitions(self):
        """テンプレートに必要な変数定義を取得"""

        # 契約金明細書の場合
        if self.selected_template_type == "契約金明細書":
            return {
                # 日付と賃借人
                '日付': '',
                '賃借人氏名': '',

                # テーブル1: 物件情報
                '物件名': '',
                '号室': '',
                '所在地': '',

                # テーブル2: 賃貸条件
                '月額賃料': '',
                '敷金': '',
                '月額共益費': '',
                '礼金': '',
                '契約開始日': '',
                '契約終了日': '',
                '契約年数': '',

                # テーブル3: 契約金明細
                '初月': '',
                '賃料': '',
                '共益費': '',
                '敷金額': '',
                '礼金額': '',
                '保証会社委託料': '',
                '仲介手数料': '',

                # テーブル4: 振込先情報
                '銀行名': '',
                '支店名': '',
                '口座番号': '',
                '口座名義人': '',
            }

        # 預かり証の場合
        elif self.selected_template_type == "預かり証":
            return {
                '賃借人氏名': '',
                '物件住所': '',
                '日付': '',
            }

        # 定期借家契約書の全変数リスト（デフォルト値付き）
        return {
            # テーブル1: 物件情報
            '建物名称': '',
            '建物所在地_住居表示': '',
            '建物所在地_登記簿': '',
            '建物構造': '鉄筋コンクリート造',
            '建物種類': '共同住宅',
            '新築年月': '',
            '間取り': '',
            '専有面積': '',
            '駐車場': '無',
            'バイク置場': '無',
            '駐輪場': '無',
            '物置': '無',
            '専用庭': '無',

            # テーブル2: 契約期間
            '契約開始日': '',
            '契約終了日': '',
            '契約年数': '2',
            '鍵引渡し日': '',

            # テーブル3: 賃料等
            '賃料': '',
            '共益費': '',
            '敷金': '',
            '礼金': '',
            '賃料_支払日': '当月末日まで',
            '賃料_支払方法': '銀行振込',
            '保証金': '0',
            '償却額': '0',
            '仲介手数料': '',
            '火災保険料': '20,000',
            '保証委託料': '',

            # テーブル4: 賃借人情報
            '賃借人氏名': '',
            '賃借人関係': '本人',
            '賃借人生年月日': '',
            '賃借人現住所': '',
            '賃借人電話': '',
            '賃借人携帯': '',
            '賃借人勤務先': '',
            '賃借人勤務先住所': '',
            '賃借人勤務先電話': '',
            '賃借人メール': '',

            # 緊急連絡先
            '緊急連絡先氏名': '',
            '緊急連絡先続柄': '',
            '緊急連絡先住所': '',
            '緊急連絡先電話': '',
            '緊急連絡先携帯': '',

            # テーブル5: 賃貸人
            '賃貸人氏名': '',
            '賃貸人住所': '',

            # テーブル6: 管理者
            '管理者名称': '株式会社久松',
            '管理者所在地': '',
            '管理者電話': '',
            '管理者FAX': '',
            '管理者免許番号': '',
        }

    def update_variables(self):
        """変数を更新（契約データから再取得）"""
        if not self.selected_contract_id:
            QMessageBox.warning(self, "契約未選択", "契約を選択してください。")
            return

        try:
            # 変数を抽出
            extractor = VariableExtractor(self.selected_contract_id)
            contract_data = extractor.extract_all_variables()

            # 既存の変数テーブルを更新
            for row in range(self.variables_table.rowCount()):
                var_name_item = self.variables_table.item(row, 0)
                if var_name_item:
                    var_name = var_name_item.text()

                    # 契約データに該当する値があれば更新
                    if var_name in contract_data:
                        value_item = self.variables_table.item(row, 1)
                        if value_item:
                            value_item.setText(str(contract_data[var_name]))

                            # データソースを更新
                            source_item = self.variables_table.item(row, 2)
                            if source_item:
                                source_item.setText("契約データ")

            QMessageBox.information(self, "更新完了", f"契約データから変数を更新しました。")

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"変数の更新に失敗しました:\n{str(e)}")

    def _get_data_source(self, variable_name):
        """データソースを取得"""
        sources = {
            '契約ID': '契約マスタ',
            '契約日': 'システム',
            '賃借人名': '顧客マスタ',
            '賃借人住所': '顧客マスタ',
            '賃借人電話': '顧客マスタ',
            '賃貸人名': '物件マスタ',
            '物件所在': '物件マスタ',
            '物件名称': '物件マスタ',
            '貸室': '部屋マスタ',
            '面積': '部屋マスタ',
            '賃料': '契約マスタ',
            '共益費': '契約マスタ',
            '敷金': '契約マスタ',
            '礼金': '契約マスタ',
            '契約開始日': '契約マスタ',
            '契約終了日': '契約マスタ',
            '賃料_税込': '計算（賃料×1.1）',
            '消費税額': '計算（賃料×0.1）',
        }
        return sources.get(variable_name, 'デフォルト値')

    def proceed_to_generation(self):
        """生成ステップへ進む"""
        self.step4_group.setEnabled(True)
        self._update_step_status(4)
        QMessageBox.information(self, "準備完了", "書類を生成する準備が整いました。\nプレビューを生成してください。")

    def generate_preview(self):
        """プレビューを生成"""
        if not self.variables:
            QMessageBox.warning(self, "データがありません", "変数データがありません。")
            return

        # 簡易的なプレビュー生成（実際にはテンプレートを使用）
        preview_text = f"""
{self.selected_template_type}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
契約書プレビュー
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

契約日: {self.variables.get('契約日', '')}

賃貸人: {self.variables.get('賃貸人名', '')}
賃借人: {self.variables.get('賃借人名', '')}

物件所在: {self.variables.get('物件所在', '')}
物件名称: {self.variables.get('物件名称', '')}
貸室: {self.variables.get('貸室', '')}
面積: {self.variables.get('面積', '')}

賃料: {self.variables.get('賃料', '')}
共益費: {self.variables.get('共益費', '')}
敷金: {self.variables.get('敷金', '')}
礼金: {self.variables.get('礼金', '')}

契約期間: {self.variables.get('契約開始日', '')} ～ {self.variables.get('契約終了日', '')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

※ これはプレビューです。実際の契約書はWord/PDF出力で生成されます。
※ 全ての条文と特約事項が含まれます。
        """

        self.preview_text.setPlainText(preview_text)
        QMessageBox.information(self, "プレビュー生成", "プレビューを生成しました。\n内容を確認してWord/PDF出力してください。")

    def export_word(self):
        """Word形式で出力"""
        if not self.variables or not self.selected_template_type:
            QMessageBox.warning(self, "データ不足", "テンプレートと変数を選択してください。")
            return

        try:
            # 保存先を選択
            default_filename = f"{self.selected_template_type}_{self.variables.get('賃借人名', '契約書')}_{datetime.now().strftime('%Y%m%d')}.docx"
            output_path, _ = QFileDialog.getSaveFileName(
                self,
                "Word文書を保存",
                default_filename,
                "Word Documents (*.docx)"
            )

            if not output_path:
                return

            # 変数を収集（新しいフォームベースの入力から）
            current_variables = self.collect_variables_from_forms()

            # 特記事項を取得（もしあれば）
            special_notes = None
            if hasattr(self, 'special_notes_edit') and self.special_notes_edit.toPlainText().strip():
                special_notes = self.special_notes_edit.toPlainText()

            # 契約金明細書の場合
            if self.selected_template_type == "契約金明細書":
                filler = get_additional_document_filler()
                result_path = filler.fill_contract_statement(current_variables, output_path)

                QMessageBox.information(
                    self,
                    "出力完了",
                    f"契約金明細書を生成しました！\n\n{result_path}"
                )
            # 預かり証の場合（Excelファイル）
            elif self.selected_template_type == "預かり証":
                # Excel用に拡張子を変更
                output_path = output_path.replace('.docx', '.xlsx')

                filler = get_additional_document_filler()
                result_path = filler.fill_deposit_receipt(current_variables, output_path)

                QMessageBox.information(
                    self,
                    "出力完了",
                    f"預かり証を生成しました！\n\n{result_path}"
                )
            # 定期借家契約書の場合は、ContractTemplateFillerを使用
            elif "定期借家" in self.selected_template_type and "契約書" in self.selected_template_type:
                filler = get_contract_filler()
                result_path = filler.fill_teiki_shakuya_keiyaku(current_variables, output_path)

                QMessageBox.information(
                    self,
                    "出力完了",
                    f"定期借家契約書を生成しました！\n\n書式を保持したまま値が入力されています。\n\n{result_path}"
                )
            else:
                # その他のテンプレートの場合は従来通り
                template_filename = f"{self.selected_template_type}.docx"
                template_path = os.path.join("templates", "contracts", template_filename)

                # テンプレートが存在するか確認
                if not os.path.exists(template_path):
                    QMessageBox.warning(
                        self,
                        "テンプレート未作成",
                        f"テンプレートファイルが見つかりません:\n{template_path}\n\nデフォルトテンプレートを作成します。"
                    )
                    # デフォルトテンプレートを作成
                    engine = get_document_engine()
                    engine.create_blank_template(self.selected_template_type, template_path)

                # ドキュメント生成
                engine = get_document_engine()
                result_path = engine.generate_from_template(
                    template_path=template_path,
                    variables=current_variables,
                    output_path=output_path,
                    special_notes=special_notes
                )

                QMessageBox.information(
                    self,
                    "出力完了",
                    f"Word文書を出力しました:\n\n{result_path}"
                )

            # エビデンス資料を契約管理タブに保存
            if self.selected_contract_id and self.evidence_documents:
                self.save_evidence_documents_to_contract()

            # ファイルを開く
            os.startfile(result_path)

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            QMessageBox.critical(self, "出力エラー", f"Word出力に失敗しました:\n{str(e)}\n\n詳細:\n{error_details}")

    def collect_variables_from_forms(self):
        """各フォームとデータベースから変数を収集"""
        variables = {}

        # 変数テーブルから手動入力された値を取得
        for row in range(self.variables_table.rowCount()):
            var_name_item = self.variables_table.item(row, 0)
            var_value_item = self.variables_table.item(row, 1)
            if var_name_item and var_value_item:
                var_name = var_name_item.text()
                var_value = var_value_item.text()
                if var_value:  # 空でない場合のみ設定
                    variables[var_name] = var_value

        # 賃借人情報（顧客データベースから）
        if self.selected_customer_id:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM customers WHERE id = ?', (self.selected_customer_id,))
                customer = cursor.fetchone()
                conn.close()

                if customer:
                    variables['賃借人氏名'] = customer.get('name', '')
                    variables['賃借人現住所'] = customer.get('address', '')
                    variables['賃借人電話'] = customer.get('phone', '')
                    variables['賃借人携帯'] = customer.get('phone', '')  # 同じ電話番号を使用
                    variables['賃借人メール'] = customer.get('email', '')
                    variables['賃借人生年月日'] = customer.get('birth_date', '')
            except:
                pass

        # 物件情報（物件データベースから）
        if self.selected_property_id and self.selected_unit_id:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT p.*, u.room_number, u.layout, u.area, u.rent
                    FROM properties p
                    LEFT JOIN units u ON u.property_id = p.id
                    WHERE p.id = ? AND u.id = ?
                ''', (self.selected_property_id, self.selected_unit_id))
                property_unit = cursor.fetchone()
                conn.close()

                if property_unit:
                    variables['建物名称'] = property_unit.get('name', '')
                    variables['建物所在地_住居表示'] = property_unit.get('address', '')
                    variables['建物所在地_登記簿'] = property_unit.get('address', '')
                    variables['建物構造'] = property_unit.get('structure', '鉄筋コンクリート造')
                    variables['建物種類'] = '共同住宅'
                    variables['新築年月'] = property_unit.get('built_date', '')
                    variables['間取り'] = property_unit.get('layout', '')
                    variables['専有面積'] = str(property_unit.get('area', ''))
            except:
                pass

        # 賃貸人情報タブ（フォームから）
        if hasattr(self, 'landlord_name'):
            variables['賃貸人氏名'] = self.landlord_name.text()
            variables['賃貸人住所'] = self.landlord_address.text()

        # 管理会社情報タブ（フォームから）
        if hasattr(self, 'manager_name'):
            variables['管理者名称'] = self.manager_name.text()
            variables['管理者所在地'] = self.manager_address.text()
            variables['管理者電話'] = self.manager_phone.text()
            variables['管理者FAX'] = self.manager_fax.text()
            variables['管理者免許番号'] = self.manager_license.text()

        # その他資料・契約条件タブ（フォームから）
        if hasattr(self, 'contract_start_date'):
            variables['契約開始日'] = self.contract_start_date.text()
            variables['契約終了日'] = self.contract_end_date.text()
            variables['契約年数'] = self.contract_years.text()
            variables['鍵引渡し日'] = self.key_delivery_date.text()
            variables['賃料'] = self.rent.text()
            variables['共益費'] = self.common_fee.text()
            variables['敷金'] = self.deposit.text()
            variables['礼金'] = self.key_money.text()
            variables['賃料_支払日'] = self.rent_payment_day.text()
            variables['賃料_支払方法'] = self.rent_payment_method.text()

        # 契約金明細書用のデータ整形
        if self.selected_template_type == "契約金明細書":
            # 日付
            variables['日付'] = datetime.now().strftime('%Y年%m月%d日')

            # 物件情報（物件データから）
            if self.selected_property_id and self.selected_unit_id:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT p.name, p.address, u.room_number
                        FROM properties p
                        JOIN units u ON u.property_id = p.id
                        WHERE p.id = ? AND u.id = ?
                    ''', (self.selected_property_id, self.selected_unit_id))
                    prop = cursor.fetchone()
                    conn.close()

                    if prop:
                        variables['物件名'] = prop['name']
                        variables['号室'] = prop['room_number']
                        variables['所在地'] = prop['address']
                except:
                    pass

            # テーブル2用: 金額データ（円付き）
            variables['月額賃料'] = f"{variables.get('賃料', '0')}円" if variables.get('賃料') else ''
            variables['月額共益費'] = f"{variables.get('共益費', '0')}円" if variables.get('共益費') else ''
            variables['敷金'] = f"{variables.get('敷金', '0')}円" if variables.get('敷金') else ''
            variables['礼金'] = f"{variables.get('礼金', '0')}円" if variables.get('礼金') else ''

            # テーブル3用: 金額データ（円なし）
            variables['敷金額'] = variables.get('敷金', '0').replace('円', '')
            variables['礼金額'] = variables.get('礼金', '0').replace('円', '')

            # 保証会社委託料と仲介手数料（デフォルト計算）
            try:
                rent = int(variables.get('賃料', '0').replace(',', '').replace('円', ''))
                variables.setdefault('保証会社委託料', str(int(rent * 0.5)))
                variables.setdefault('仲介手数料', str(int(rent * 1.1)))
            except:
                pass

            # 振込先情報（オーナー情報から）
            variables.setdefault('銀行名', '')
            variables.setdefault('支店名', '')
            variables.setdefault('口座番号', '')
            variables.setdefault('口座名義人', '')

        # 預かり証用のデータ整形
        elif self.selected_template_type == "預かり証":
            # 物件住所
            if self.selected_property_id and self.selected_unit_id:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT p.address, u.room_number
                        FROM properties p
                        JOIN units u ON u.property_id = p.id
                        WHERE p.id = ? AND u.id = ?
                    ''', (self.selected_property_id, self.selected_unit_id))
                    prop = cursor.fetchone()
                    conn.close()

                    if prop:
                        variables['物件住所'] = f"{prop['address']}　{prop['room_number']}"
                except:
                    pass

            # 鍵リスト（デフォルトで空リスト）
            variables.setdefault('鍵リスト', [
                {'番号': '', '数量': 1},
                {'番号': '', '数量': 1},
            ])

            # 日付
            today = datetime.now()
            variables['日付'] = f"令和　 　　{today.year - 2018}年　　　{today.month}月　 　　{today.day}日"

        # デフォルト値を設定
        variables.setdefault('駐車場', '無')
        variables.setdefault('バイク置場', '無')
        variables.setdefault('駐輪場', '無')
        variables.setdefault('物置', '無')
        variables.setdefault('専用庭', '無')
        variables.setdefault('賃借人関係', '本人')

        return variables

    def save_evidence_documents_to_contract(self):
        """アップロードしたエビデンス資料を契約管理タブの書類管理に保存"""
        if not self.selected_contract_id:
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # 保存ディレクトリを作成
            documents_dir = os.path.join("documents", "contracts", str(self.selected_contract_id))
            os.makedirs(documents_dir, exist_ok=True)

            saved_count = 0
            for doc_type, file_path in self.evidence_documents.items():
                if not os.path.exists(file_path):
                    continue

                # ファイルを契約書類フォルダにコピー
                file_name = os.path.basename(file_path)
                dest_path = os.path.join(documents_dir, f"{doc_type}_{file_name}")

                # ファイルをコピー
                import shutil
                shutil.copy2(file_path, dest_path)

                # データベースに登録（contract_documentsテーブルがあると仮定）
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO contract_documents
                        (contract_id, document_type, file_name, file_path, upload_date)
                        VALUES (?, ?, ?, ?, datetime('now'))
                    ''', (self.selected_contract_id, doc_type, file_name, dest_path))
                    saved_count += 1
                except:
                    # テーブルが存在しない場合はスキップ
                    pass

            conn.commit()
            conn.close()

            if saved_count > 0:
                QMessageBox.information(
                    self,
                    "エビデンス資料保存完了",
                    f"{saved_count}件のエビデンス資料を契約管理タブに保存しました。\n\n保存先: {documents_dir}"
                )

        except Exception as e:
            QMessageBox.warning(
                self,
                "エビデンス資料保存エラー",
                f"エビデンス資料の保存中にエラーが発生しました:\n{str(e)}"
            )

    def export_pdf(self):
        """PDF形式で出力"""
        if not self.variables or not self.selected_template_type:
            QMessageBox.warning(self, "データ不足", "テンプレートと変数を選択してください。")
            return

        try:
            # 保存先を選択
            default_filename = f"{self.selected_template_type}_{self.variables.get('賃借人名', '契約書')}_{datetime.now().strftime('%Y%m%d')}.pdf"
            pdf_path, _ = QFileDialog.getSaveFileName(
                self,
                "PDF文書を保存",
                default_filename,
                "PDF Documents (*.pdf)"
            )

            if not pdf_path:
                return

            # 進捗ダイアログを表示
            progress = QProgressDialog("PDF生成中...", None, 0, 3, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)

            # Step 1: まずWordファイルを生成
            progress.setLabelText("Wordファイルを生成中...")
            progress.setValue(1)

            temp_word_path = pdf_path.replace('.pdf', '_temp.docx')

            # テンプレートパスを決定
            template_filename = f"{self.selected_template_type}.docx"
            template_path = os.path.join("templates", "contracts", template_filename)

            # テンプレートが存在するか確認
            if not os.path.exists(template_path):
                engine = get_document_engine()
                engine.create_blank_template(self.selected_template_type, template_path)

            # 変数テーブルから最新の値を取得
            current_variables = {}
            for row in range(self.variables_table.rowCount()):
                var_name = self.variables_table.item(row, 0).text().strip('{}')
                var_value = self.variables_table.item(row, 1).text()
                current_variables[var_name] = var_value

            # 特記事項を取得
            special_notes = None
            if hasattr(self, 'special_notes_edit') and self.special_notes_edit.toPlainText().strip():
                special_notes = self.special_notes_edit.toPlainText()

            # Wordファイルを生成
            engine = get_document_engine()
            engine.generate_from_template(
                template_path=template_path,
                variables=current_variables,
                output_path=temp_word_path,
                special_notes=special_notes
            )

            # Step 2: PDFに変換
            progress.setLabelText("PDFに変換中...")
            progress.setValue(2)

            engine.convert_to_pdf(temp_word_path, pdf_path)

            # Step 3: 一時ファイルを削除
            progress.setLabelText("完了処理中...")
            progress.setValue(3)

            if os.path.exists(temp_word_path):
                os.remove(temp_word_path)

            progress.close()

            QMessageBox.information(
                self,
                "出力完了",
                f"PDF文書を出力しました:\n\n{pdf_path}"
            )

            # ファイルを開く
            os.startfile(pdf_path)

        except Exception as e:
            QMessageBox.critical(self, "出力エラー", f"PDF出力に失敗しました:\n{str(e)}")

    def upload_application_form(self):
        """申込書をアップロードして自動入力"""
        try:
            # ファイル選択ダイアログ
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "申込書ファイルを選択",
                "",
                "Word/PDF Files (*.doc *.docx *.pdf);;All Files (*.*)"
            )

            if not file_path:
                return

            # 進捗ダイアログを表示
            progress = QProgressDialog("申込書を解析中...", "キャンセル", 0, 3, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)

            # Step 1: ファイル読み込み
            progress.setLabelText("ファイルを読み込んでいます...")
            progress.setValue(1)

            # Step 2: OCR処理
            progress.setLabelText("申込書内容をOCR解析中...")
            progress.setValue(2)

            ocr = get_application_form_ocr()
            extracted_vars = ocr.extract_from_file(file_path)

            # Step 3: 変数テーブルに反映
            progress.setLabelText("変数に反映中...")
            progress.setValue(3)

            # 変数名マッピング（OCRの変数名 → テンプレートの変数名）
            variable_mapping = {
                '賃借人名': '賃借人氏名',
                '物件名称': '物件名',
                '貸室': '号室',
                '賃借人住所': '所在地',
            }

            # マッピングを適用
            mapped_vars = {}
            for ocr_var_name, ocr_value in extracted_vars.items():
                # マッピングがあればそれを使用、なければそのまま
                template_var_name = variable_mapping.get(ocr_var_name, ocr_var_name)
                mapped_vars[template_var_name] = ocr_value

            # 既存の変数テーブルを更新
            merged_count = 0
            for row in range(self.variables_table.rowCount()):
                var_name_item = self.variables_table.item(row, 0)
                if var_name_item:
                    var_name = var_name_item.text()

                    # 抽出された変数に該当するものがあれば更新
                    if var_name in mapped_vars:
                        value_item = self.variables_table.item(row, 1)
                        if value_item:
                            old_value = value_item.text()
                            new_value = mapped_vars[var_name]

                            # 空の場合のみ上書き、または確認
                            if not old_value or old_value == '':
                                value_item.setText(new_value)
                                merged_count += 1
                            else:
                                # 既に値がある場合は上書きするか確認
                                reply = QMessageBox.question(
                                    self,
                                    "上書き確認",
                                    f"変数「{var_name}」は既に値が入力されています。\n\n"
                                    f"現在の値: {old_value}\n"
                                    f"新しい値: {new_value}\n\n"
                                    f"上書きしますか？",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                                )
                                if reply == QMessageBox.StandardButton.Yes:
                                    value_item.setText(new_value)
                                    merged_count += 1

            progress.close()

            # ステータス表示
            self.upload_status_label.setText(
                f"✅ 申込書から {len(extracted_vars)} 個の項目を抽出し、{merged_count} 個の変数を更新しました"
            )

            QMessageBox.information(
                self,
                "アップロード完了",
                f"申込書の解析が完了しました。\n\n"
                f"抽出された項目: {len(extracted_vars)}個\n"
                f"変数テーブルに反映: {merged_count}個\n\n"
                f"抽出された項目:\n" + "\n".join([f"・{k}: {v}" for k, v in list(extracted_vars.items())[:10]])
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "エラー",
                f"申込書の処理中にエラーが発生しました:\n\n{str(e)}"
            )
            self.upload_status_label.setText("❌ エラーが発生しました")
