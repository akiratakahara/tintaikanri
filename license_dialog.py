"""
ライセンス認証ダイアログ
賃貸管理システム v2.0
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QTabWidget, QWidget, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from license_manager import LicenseManager


class LicenseDialog(QDialog):
    """ライセンス認証ダイアログ"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = LicenseManager()
        self.init_ui()

    def init_ui(self):
        """UIの初期化"""
        self.setWindowTitle("賃貸管理システム v2.0 - ライセンス認証")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        layout = QVBoxLayout()

        # タイトル
        title = QLabel("賃貸管理システム v2.0")
        title.setFont(QFont("", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Professional Edition")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 20px;")
        layout.addWidget(subtitle)

        # タブウィジェット
        tabs = QTabWidget()

        # ライセンス認証タブ
        license_tab = self.create_license_tab()
        tabs.addTab(license_tab, "ライセンス認証")

        # トライアルタブ
        trial_tab = self.create_trial_tab()
        tabs.addTab(trial_tab, "無料トライアル")

        layout.addWidget(tabs)

        self.setLayout(layout)

    def create_license_tab(self):
        """ライセンス認証タブを作成"""
        tab = QWidget()
        layout = QVBoxLayout()

        # 説明
        desc = QLabel(
            "製品をご購入いただきありがとうございます。\n"
            "メールで送付されたライセンスキーを入力してください。"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("margin: 10px; padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        layout.addWidget(desc)

        # 顧客名
        layout.addWidget(QLabel("顧客名（会社名）:"))
        self.customer_name_edit = QLineEdit()
        self.customer_name_edit.setPlaceholderText("例: 株式会社サンプル不動産")
        layout.addWidget(self.customer_name_edit)

        # メールアドレス
        layout.addWidget(QLabel("メールアドレス:"))
        self.customer_email_edit = QLineEdit()
        self.customer_email_edit.setPlaceholderText("例: info@example.com")
        layout.addWidget(self.customer_email_edit)

        # ライセンスキー
        layout.addWidget(QLabel("ライセンスキー:"))
        self.license_key_edit = QLineEdit()
        self.license_key_edit.setPlaceholderText("XXXX-XXXX-XXXX-XXXX")
        self.license_key_edit.setFont(QFont("Courier New", 10))
        layout.addWidget(self.license_key_edit)

        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        activate_button = QPushButton("認証")
        activate_button.clicked.connect(self.activate_license)
        activate_button.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 30px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        button_layout.addWidget(activate_button)

        cancel_button = QPushButton("キャンセル")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 30px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        layout.addStretch()

        tab.setLayout(layout)
        return tab

    def create_trial_tab(self):
        """トライアルタブを作成"""
        tab = QWidget()
        layout = QVBoxLayout()

        # 説明
        desc = QLabel(
            f"購入前に{self.manager.trial_days}日間、無料で製品をお試しいただけます。\n\n"
            "トライアル期間中は全ての機能をご利用いただけます。\n"
            "期間終了後、引き続きご利用いただくには製品版のライセンスキーが必要です。"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("margin: 10px; padding: 10px; background-color: #eff6ff; border-radius: 5px;")
        layout.addWidget(desc)

        # 注意事項
        notes = QTextEdit()
        notes.setReadOnly(True)
        notes.setMaximumHeight(150)
        notes.setHtml("""
            <h4>トライアルのご利用にあたって</h4>
            <ul>
                <li>トライアルはこのPC専用です</li>
                <li>トライアル期間は延長できません</li>
                <li>作成したデータは製品版でも引き続きご利用いただけます</li>
                <li>トライアル期間終了後、製品版ライセンスの購入が必要です</li>
            </ul>
        """)
        layout.addWidget(notes)

        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        trial_button = QPushButton(f"{self.manager.trial_days}日間トライアルを開始")
        trial_button.clicked.connect(self.start_trial)
        trial_button.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 30px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        button_layout.addWidget(trial_button)

        cancel_button = QPushButton("キャンセル")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 30px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        layout.addStretch()

        tab.setLayout(layout)
        return tab

    def activate_license(self):
        """ライセンスを認証"""
        customer_name = self.customer_name_edit.text().strip()
        customer_email = self.customer_email_edit.text().strip()
        license_key = self.license_key_edit.text().strip()

        # 入力チェック
        if not customer_name:
            QMessageBox.warning(self, "入力エラー", "顧客名を入力してください。")
            return

        if not customer_email:
            QMessageBox.warning(self, "入力エラー", "メールアドレスを入力してください。")
            return

        if not license_key:
            QMessageBox.warning(self, "入力エラー", "ライセンスキーを入力してください。")
            return

        # ライセンス認証
        success, message = self.manager.activate_license(
            license_key, customer_name, customer_email
        )

        if success:
            QMessageBox.information(
                self,
                "認証成功",
                f"{message}\n\n賃貸管理システムをご利用いただけます。"
            )
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "認証失敗",
                f"{message}\n\nライセンスキーを確認して再度お試しください。"
            )

    def start_trial(self):
        """トライアルを開始"""
        reply = QMessageBox.question(
            self,
            "トライアル開始",
            f"{self.manager.trial_days}日間の無料トライアルを開始しますか？\n\n"
            "このPCでのみ有効です。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.manager.start_trial()

            if success:
                QMessageBox.information(
                    self,
                    "トライアル開始",
                    f"{message}\n\n賃貸管理システムをお試しください。"
                )
                self.accept()
            else:
                QMessageBox.warning(self, "トライアル開始失敗", message)


# テスト用コード
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    dialog = LicenseDialog()

    if dialog.exec() == QDialog.DialogCode.Accepted:
        print("ライセンス認証成功")
    else:
        print("ライセンス認証キャンセル")

    sys.exit()
