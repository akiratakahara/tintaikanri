"""
契約書・重説生成タブ

過去の書類からテンプレートを作成し、自動で新しい書類を生成する機能
"""
import os
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QLineEdit,
    QTextEdit, QMessageBox, QGroupBox, QFormLayout,
    QComboBox, QFileDialog, QDialog, QDialogButtonBox,
    QTabWidget, QProgressDialog, QSplitter, QListWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from document_ai import DocumentAI, DocumentTemplate
from models import TenantContract, Property


class AnalysisWorker(QThread):
    """書類解析を非同期で実行するワーカースレッド"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, file_path: str, document_type: str):
        super().__init__()
        self.file_path = file_path
        self.document_type = document_type

    def run(self):
        try:
            ai = DocumentAI()
            result = ai.analyze_document_structure(self.file_path, self.document_type)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class ApplicationExtractionWorker(QThread):
    """申込書データ抽出を非同期で実行するワーカースレッド"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            ai = DocumentAI()
            result = ai.extract_data_from_application(self.file_path)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class DocumentGeneratorTab(QWidget):
    """契約書・重説生成タブ"""

    def __init__(self):
        super().__init__()
        self.template_manager = DocumentTemplate()
        self.current_template = None
        self.current_analysis_result = None
        self.init_ui()
        self.load_templates_list()

    def init_ui(self):
        """UIの初期化"""
        main_layout = QVBoxLayout()

        # タイトル
        title_label = QLabel("📝 契約書・重説 自動生成システム")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        # タブウィジェット
        tab_widget = QTabWidget()

        # タブ1: テンプレート作成
        template_creation_tab = self.create_template_creation_tab()
        tab_widget.addTab(template_creation_tab, "📄 テンプレート作成")

        # タブ2: 書類生成
        document_generation_tab = self.create_document_generation_tab()
        tab_widget.addTab(document_generation_tab, "✨ 書類生成")

        # タブ3: テンプレート管理
        template_management_tab = self.create_template_management_tab()
        tab_widget.addTab(template_management_tab, "🗂️ テンプレート管理")

        main_layout.addWidget(tab_widget)
        self.setLayout(main_layout)

    def create_template_creation_tab(self) -> QWidget:
        """テンプレート作成タブのUI"""
        widget = QWidget()
        layout = QVBoxLayout()

        # 説明
        info_label = QLabel(
            "💡 過去の契約書や重説をアップロードすると、AIが自動でテンプレート化します。\n"
            "変数部分（テナント名、賃料など）を自動で識別し、再利用可能なテンプレートを作成します。"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("background-color: #e3f2fd; padding: 10px; border-radius: 5px;")
        layout.addWidget(info_label)

        # フォームグループ
        form_group = QGroupBox("書類アップロード")
        form_layout = QFormLayout()

        self.template_doc_type_combo = QComboBox()
        self.template_doc_type_combo.addItem("賃貸借契約書", "contract")
        self.template_doc_type_combo.addItem("重要事項説明書", "explanation")
        self.template_doc_type_combo.addItem("入居申込書", "application")

        self.template_file_path_edit = QLineEdit()
        self.template_file_path_edit.setReadOnly(True)

        self.template_name_edit = QLineEdit()
        self.template_name_edit.setPlaceholderText("例: 標準契約書_2024")

        form_layout.addRow("書類種別:", self.template_doc_type_combo)
        form_layout.addRow("ファイル:", self.template_file_path_edit)
        form_layout.addRow("テンプレート名:", self.template_name_edit)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # ボタン
        button_layout = QHBoxLayout()
        browse_button = QPushButton("📁 ファイル選択")
        browse_button.clicked.connect(self.browse_template_file)

        analyze_button = QPushButton("🔍 AI解析実行")
        analyze_button.clicked.connect(self.analyze_document)
        analyze_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)

        button_layout.addWidget(browse_button)
        button_layout.addWidget(analyze_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # 解析結果表示エリア
        result_group = QGroupBox("解析結果")
        result_layout = QVBoxLayout()

        self.analysis_result_text = QTextEdit()
        self.analysis_result_text.setReadOnly(True)
        self.analysis_result_text.setPlaceholderText(
            "AI解析結果がここに表示されます...\n\n"
            "・抽出された変数リスト\n"
            "・テンプレート化されたテキスト\n"
            "・セクション情報"
        )
        result_layout.addWidget(self.analysis_result_text)

        # 保存ボタン
        save_template_button = QPushButton("💾 テンプレートとして保存")
        save_template_button.clicked.connect(self.save_analyzed_template)
        save_template_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        result_layout.addWidget(save_template_button)

        result_group.setLayout(result_layout)
        layout.addWidget(result_group)

        widget.setLayout(layout)
        return widget

    def create_document_generation_tab(self) -> QWidget:
        """書類生成タブのUI"""
        widget = QWidget()
        layout = QVBoxLayout()

        # 説明
        info_label = QLabel(
            "✨ テンプレートを選択して、契約データから自動で書類を生成します。\n"
            "申込書をアップロードすると、自動でデータを抽出して入力できます。"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("background-color: #f3e5f5; padding: 10px; border-radius: 5px;")
        layout.addWidget(info_label)

        # スプリッター（左右分割）
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左側: 設定パネル
        left_panel = QWidget()
        left_layout = QVBoxLayout()

        # テンプレート選択
        template_group = QGroupBox("テンプレート選択")
        template_layout = QFormLayout()

        self.gen_template_combo = QComboBox()
        template_layout.addRow("テンプレート:", self.gen_template_combo)

        template_group.setLayout(template_layout)
        left_layout.addWidget(template_group)

        # データ入力方法選択
        data_source_group = QGroupBox("データ入力方法")
        data_source_layout = QVBoxLayout()

        # 方法1: 契約データから
        contract_radio_layout = QHBoxLayout()
        self.contract_data_button = QPushButton("📋 契約データから選択")
        self.contract_data_button.clicked.connect(self.select_contract_data)
        contract_radio_layout.addWidget(self.contract_data_button)
        data_source_layout.addLayout(contract_radio_layout)

        self.selected_contract_label = QLabel("契約未選択")
        self.selected_contract_label.setStyleSheet("color: gray; font-style: italic;")
        data_source_layout.addWidget(self.selected_contract_label)

        # 方法2: 申込書から自動抽出
        application_radio_layout = QHBoxLayout()
        self.application_upload_button = QPushButton("📤 申込書をアップロード")
        self.application_upload_button.clicked.connect(self.upload_application)
        application_radio_layout.addWidget(self.application_upload_button)
        data_source_layout.addLayout(application_radio_layout)

        self.application_file_label = QLabel("申込書未選択")
        self.application_file_label.setStyleSheet("color: gray; font-style: italic;")
        data_source_layout.addWidget(self.application_file_label)

        data_source_group.setLayout(data_source_layout)
        left_layout.addWidget(data_source_group)

        # 生成ボタン
        generate_button = QPushButton("✨ 書類生成")
        generate_button.clicked.connect(self.generate_document)
        generate_button.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                padding: 12px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        left_layout.addWidget(generate_button)

        left_layout.addStretch()
        left_panel.setLayout(left_layout)

        # 右側: プレビューパネル
        right_panel = QWidget()
        right_layout = QVBoxLayout()

        preview_label = QLabel("📄 生成プレビュー")
        preview_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        right_layout.addWidget(preview_label)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText("生成された書類がここに表示されます...")
        right_layout.addWidget(self.preview_text)

        # 保存ボタン
        save_button_layout = QHBoxLayout()
        save_word_button = QPushButton("💾 Word保存")
        save_word_button.clicked.connect(self.save_as_word)
        save_pdf_button = QPushButton("📄 PDF保存")
        save_pdf_button.clicked.connect(self.save_as_pdf)

        save_button_layout.addWidget(save_word_button)
        save_button_layout.addWidget(save_pdf_button)
        save_button_layout.addStretch()
        right_layout.addLayout(save_button_layout)

        right_panel.setLayout(right_layout)

        # スプリッターに追加
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)
        widget.setLayout(layout)
        return widget

    def create_template_management_tab(self) -> QWidget:
        """テンプレート管理タブのUI"""
        widget = QWidget()
        layout = QVBoxLayout()

        # 説明
        info_label = QLabel("🗂️ 保存されているテンプレートを管理します")
        info_label.setStyleSheet("background-color: #fff3e0; padding: 10px; border-radius: 5px;")
        layout.addWidget(info_label)

        # テンプレートリスト
        list_label = QLabel("保存済みテンプレート:")
        layout.addWidget(list_label)

        self.template_list_widget = QListWidget()
        self.template_list_widget.itemClicked.connect(self.preview_template)
        layout.addWidget(self.template_list_widget)

        # ボタン
        button_layout = QHBoxLayout()
        refresh_button = QPushButton("🔄 更新")
        refresh_button.clicked.connect(self.load_templates_list)

        delete_button = QPushButton("🗑️ 削除")
        delete_button.clicked.connect(self.delete_selected_template)
        delete_button.setStyleSheet("background-color: #f44336; color: white;")

        button_layout.addWidget(refresh_button)
        button_layout.addWidget(delete_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # プレビューエリア
        preview_group = QGroupBox("テンプレート詳細")
        preview_layout = QVBoxLayout()

        self.template_preview_text = QTextEdit()
        self.template_preview_text.setReadOnly(True)
        preview_layout.addWidget(self.template_preview_text)

        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        widget.setLayout(layout)
        return widget

    # === イベントハンドラ ===

    def browse_template_file(self):
        """テンプレート作成用ファイル選択"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "書類ファイルを選択", "",
            "すべてのファイル (*.*);;"
            "PDFファイル (*.pdf);;"
            "画像ファイル (*.png *.jpg *.jpeg)"
        )
        if file_path:
            self.template_file_path_edit.setText(file_path)

    def analyze_document(self):
        """書類をAIで解析"""
        file_path = self.template_file_path_edit.text().strip()
        if not file_path:
            QMessageBox.warning(self, "警告", "ファイルを選択してください")
            return

        if not os.path.exists(file_path):
            QMessageBox.warning(self, "警告", "ファイルが見つかりません")
            return

        document_type = self.template_doc_type_combo.currentData()

        # プログレスダイアログ
        progress = QProgressDialog("AI解析中...", "キャンセル", 0, 0, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()

        # ワーカースレッドで解析実行
        self.analysis_worker = AnalysisWorker(file_path, document_type)
        self.analysis_worker.finished.connect(lambda result: self.on_analysis_finished(result, progress))
        self.analysis_worker.error.connect(lambda error: self.on_analysis_error(error, progress))
        self.analysis_worker.start()

    def on_analysis_finished(self, result: dict, progress: QProgressDialog):
        """解析完了時の処理"""
        progress.close()

        if not result.get("success", False):
            QMessageBox.critical(
                self, "エラー",
                f"解析に失敗しました:\n{result.get('error', '不明なエラー')}"
            )
            return

        self.current_analysis_result = result

        # 結果を表示
        display_text = f"【書類種別】 {result.get('document_type', 'N/A')}\n\n"
        display_text += f"【タイトル】 {result.get('title', 'N/A')}\n\n"

        display_text += "【抽出された変数】\n"
        for var in result.get("variables", []):
            display_text += f"  • {var.get('name', 'N/A')} (例: {var.get('example_value', 'N/A')})\n"
            display_text += f"    → {var.get('description', '')}\n"

        display_text += f"\n【セクション数】 {len(result.get('sections', []))}\n\n"

        display_text += "【テンプレート（一部）】\n"
        template_preview = result.get("template_text", "")[:500]
        display_text += template_preview + "..."

        self.analysis_result_text.setPlainText(display_text)

        QMessageBox.information(
            self, "解析完了",
            f"解析が完了しました！\n\n"
            f"変数数: {len(result.get('variables', []))}\n"
            f"セクション数: {len(result.get('sections', []))}"
        )

    def on_analysis_error(self, error: str, progress: QProgressDialog):
        """解析エラー時の処理"""
        progress.close()
        QMessageBox.critical(self, "エラー", f"解析中にエラーが発生しました:\n{error}")

    def save_analyzed_template(self):
        """解析結果をテンプレートとして保存"""
        if not self.current_analysis_result:
            QMessageBox.warning(self, "警告", "解析結果がありません。先にAI解析を実行してください。")
            return

        template_name = self.template_name_edit.text().strip()
        if not template_name:
            QMessageBox.warning(self, "警告", "テンプレート名を入力してください")
            return

        # テンプレート保存
        success = self.template_manager.save_template(template_name, self.current_analysis_result)

        if success:
            QMessageBox.information(self, "保存完了", f"テンプレート「{template_name}」を保存しました")
            self.load_templates_list()
            self.template_name_edit.clear()
            self.template_file_path_edit.clear()
            self.analysis_result_text.clear()
            self.current_analysis_result = None
        else:
            QMessageBox.critical(self, "エラー", "テンプレートの保存に失敗しました")

    def load_templates_list(self):
        """テンプレート一覧を読み込み"""
        templates = self.template_manager.list_templates()

        # 生成タブのコンボボックスを更新
        self.gen_template_combo.clear()
        for template_name in templates:
            self.gen_template_combo.addItem(template_name)

        # 管理タブのリストを更新
        self.template_list_widget.clear()
        self.template_list_widget.addItems(templates)

    def preview_template(self, item):
        """テンプレートをプレビュー"""
        template_name = item.text()
        template = self.template_manager.load_template(template_name)

        if template:
            preview_text = f"【テンプレート名】 {template_name}\n\n"
            preview_text += f"【書類種別】 {template.get('document_type', 'N/A')}\n\n"
            preview_text += f"【変数数】 {len(template.get('variables', []))}\n\n"
            preview_text += "【変数リスト】\n"
            for var in template.get("variables", []):
                preview_text += f"  • {var.get('name', 'N/A')}\n"

            self.template_preview_text.setPlainText(preview_text)

    def delete_selected_template(self):
        """選択されたテンプレートを削除"""
        current_item = self.template_list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "削除するテンプレートを選択してください")
            return

        template_name = current_item.text()
        reply = QMessageBox.question(
            self, "確認",
            f"テンプレート「{template_name}」を削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success = self.template_manager.delete_template(template_name)
            if success:
                QMessageBox.information(self, "削除完了", "テンプレートを削除しました")
                self.load_templates_list()
            else:
                QMessageBox.critical(self, "エラー", "テンプレートの削除に失敗しました")

    def select_contract_data(self):
        """契約データを選択"""
        try:
            contracts = TenantContract.get_all()
            if not contracts:
                QMessageBox.information(self, "情報", "契約データがありません")
                return

            # 契約選択ダイアログ
            dialog = ContractSelectionDialog(contracts, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                selected_contract = dialog.get_selected_contract()
                self.selected_contract_data = selected_contract
                self.selected_contract_label.setText(
                    f"✅ {selected_contract.get('contractor_name', 'N/A')} - "
                    f"{selected_contract.get('property_name', 'N/A')}"
                )
                self.selected_contract_label.setStyleSheet("color: green; font-weight: bold;")

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"契約データの読み込みに失敗しました:\n{str(e)}")

    def upload_application(self):
        """申込書をアップロード"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "申込書を選択", "",
            "すべてのファイル (*.*);;"
            "PDFファイル (*.pdf);;"
            "画像ファイル (*.png *.jpg *.jpeg)"
        )

        if not file_path:
            return

        # プログレスダイアログ
        progress = QProgressDialog("申込書を解析中...", "キャンセル", 0, 0, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()

        # ワーカースレッドでデータ抽出
        self.extraction_worker = ApplicationExtractionWorker(file_path)
        self.extraction_worker.finished.connect(lambda result: self.on_extraction_finished(result, progress))
        self.extraction_worker.error.connect(lambda error: self.on_extraction_error(error, progress))
        self.extraction_worker.start()

        self.application_file_label.setText(f"📄 {os.path.basename(file_path)}")

    def on_extraction_finished(self, result: dict, progress: QProgressDialog):
        """申込書データ抽出完了時の処理"""
        progress.close()

        if not result.get("success", False):
            QMessageBox.critical(
                self, "エラー",
                f"データ抽出に失敗しました:\n{result.get('error', '不明なエラー')}"
            )
            return

        self.application_data = result.get("data", {})
        self.application_file_label.setStyleSheet("color: green; font-weight: bold;")

        QMessageBox.information(
            self, "抽出完了",
            "申込書からデータを抽出しました！\n\n書類生成ボタンを押してください。"
        )

    def on_extraction_error(self, error: str, progress: QProgressDialog):
        """申込書データ抽出エラー時の処理"""
        progress.close()
        QMessageBox.critical(self, "エラー", f"データ抽出中にエラーが発生しました:\n{error}")

    def generate_document(self):
        """書類を生成"""
        template_name = self.gen_template_combo.currentText()
        if not template_name:
            QMessageBox.warning(self, "警告", "テンプレートを選択してください")
            return

        # テンプレート読み込み
        template = self.template_manager.load_template(template_name)
        if not template:
            QMessageBox.critical(self, "エラー", "テンプレートの読み込みに失敗しました")
            return

        # データソースを確認
        if hasattr(self, 'selected_contract_data') and self.selected_contract_data:
            # 契約データから生成
            data = self.selected_contract_data
        elif hasattr(self, 'application_data') and self.application_data:
            # 申込書データから生成
            data = self.application_data
        else:
            QMessageBox.warning(self, "警告", "契約データまたは申込書を選択してください")
            return

        # 書類生成
        ai = DocumentAI()
        generated_text = ai.generate_document_from_contract(template, data)

        # プレビューに表示
        self.preview_text.setPlainText(generated_text)
        self.generated_document_text = generated_text

        QMessageBox.information(self, "生成完了", "書類を生成しました！")

    def save_as_word(self):
        """Wordファイルとして保存"""
        if not hasattr(self, 'generated_document_text') or not self.generated_document_text:
            QMessageBox.warning(self, "警告", "生成された書類がありません")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Word保存", "", "Word文書 (*.docx)"
        )

        if file_path:
            try:
                from docx import Document
                doc = Document()
                doc.add_paragraph(self.generated_document_text)
                doc.save(file_path)
                QMessageBox.information(self, "保存完了", f"Wordファイルを保存しました:\n{file_path}")
            except ImportError:
                QMessageBox.critical(
                    self, "エラー",
                    "python-docxライブラリがインストールされていません。\n"
                    "pip install python-docx を実行してください。"
                )
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"保存に失敗しました:\n{str(e)}")

    def save_as_pdf(self):
        """PDFファイルとして保存"""
        if not hasattr(self, 'generated_document_text') or not self.generated_document_text:
            QMessageBox.warning(self, "警告", "生成された書類がありません")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "PDF保存", "", "PDFファイル (*.pdf)"
        )

        if file_path:
            try:
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import A4
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont

                # 日本語フォント設定（環境に応じて調整が必要）
                # pdfmetrics.registerFont(TTFont('Japanese', 'path/to/font.ttf'))

                c = canvas.Canvas(file_path, pagesize=A4)
                text_object = c.beginText(40, 800)
                # text_object.setFont('Japanese', 10)

                for line in self.generated_document_text.split('\n'):
                    text_object.textLine(line)

                c.drawText(text_object)
                c.save()

                QMessageBox.information(self, "保存完了", f"PDFファイルを保存しました:\n{file_path}")
            except ImportError:
                QMessageBox.critical(
                    self, "エラー",
                    "reportlabライブラリがインストールされていません。\n"
                    "pip install reportlab を実行してください。"
                )
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"PDF保存に失敗しました:\n{str(e)}")


class ContractSelectionDialog(QDialog):
    """契約選択ダイアログ"""

    def __init__(self, contracts: list, parent=None):
        super().__init__(parent)
        self.contracts = contracts
        self.selected_contract = None
        self.init_ui()

    def init_ui(self):
        """UIの初期化"""
        self.setWindowTitle("契約データ選択")
        self.resize(600, 400)

        layout = QVBoxLayout()

        # 説明
        label = QLabel("書類を生成する契約を選択してください:")
        layout.addWidget(label)

        # 契約テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "契約者名", "物件名", "賃料", "契約期間"])
        self.table.setRowCount(len(self.contracts))

        for i, contract in enumerate(self.contracts):
            self.table.setItem(i, 0, QTableWidgetItem(str(contract.get('id', ''))))
            self.table.setItem(i, 1, QTableWidgetItem(contract.get('contractor_name', '')))
            self.table.setItem(i, 2, QTableWidgetItem(contract.get('property_name', '')))
            self.table.setItem(i, 3, QTableWidgetItem(f"¥{contract.get('rent', 0):,}"))
            self.table.setItem(
                i, 4,
                QTableWidgetItem(f"{contract.get('start_date', '')} ～ {contract.get('end_date', '')}")
            )

        self.table.doubleClicked.connect(self.on_row_double_clicked)
        layout.addWidget(self.table)

        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept_selection)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def on_row_double_clicked(self):
        """行をダブルクリック"""
        self.accept_selection()

    def accept_selection(self):
        """選択を確定"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.selected_contract = self.contracts[current_row]
            self.accept()

    def get_selected_contract(self):
        """選択された契約を取得"""
        return self.selected_contract
