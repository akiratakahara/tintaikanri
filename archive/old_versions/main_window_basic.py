"""
基本版メインウィンドウ - OCR機能なし版
"""
import sys
import os
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTabWidget, QLabel, QMessageBox,
                             QStatusBar, QMenuBar, QMenu, QToolBar)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QAction

# モデルとユーティリティ
from models import create_tables
from utils import MessageHelper

# 基本タブモジュール（OCR機能なし）
from customer_tab_improved import CustomerTabImproved
from unit_tab import UnitTab
from contract_tab import ContractTab
from task_tab import TaskTab
from communication_tab import CommunicationTab

# 環境変数チェック
from dotenv import load_dotenv
load_dotenv()

class DatabaseInitWorker(QThread):
    """データベース初期化ワーカー"""
    finished = pyqtSignal(bool, str)
    
    def run(self):
        try:
            create_tables()
            self.finished.emit(True, "データベースが正常に初期化されました")
        except Exception as e:
            self.finished.emit(False, f"データベース初期化エラー: {str(e)}")

class BasicStatsWidget(QWidget):
    """基本統計ウィジェット"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_stats()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # タイトル
        title_label = QLabel("システム統計")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # 統計ラベル
        self.stats_label = QLabel("統計を読み込み中...")
        layout.addWidget(self.stats_label)
        
        # 更新ボタン
        from PyQt6.QtWidgets import QPushButton
        refresh_btn = QPushButton("更新")
        refresh_btn.clicked.connect(self.load_stats)
        layout.addWidget(refresh_btn)
        
        self.setLayout(layout)
    
    def load_stats(self):
        """統計データを読み込み"""
        try:
            from models import Customer, Property, TenantContract
            
            customers = Customer.get_all()
            properties = Property.get_all()
            contracts = TenantContract.get_all()
            
            stats_text = f"""
顧客数: {len(customers)}件
物件数: {len(properties)}件
契約数: {len(contracts)}件

最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            """
            
            self.stats_label.setText(stats_text)
            
        except Exception as e:
            self.stats_label.setText(f"統計取得エラー: {str(e)}")

class MainWindowBasic(QMainWindow):
    """基本版メインウィンドウ（OCR機能なし）"""
    
    def __init__(self):
        super().__init__()
        self.init_database()
        self.init_ui()
        self.setup_menu_bar()
        self.setup_status_bar()
    
    def init_database(self):
        """データベースの初期化"""
        self.db_worker = DatabaseInitWorker()
        self.db_worker.finished.connect(self.on_database_initialized)
        self.db_worker.start()
    
    def on_database_initialized(self, success, message):
        """データベース初期化完了時の処理"""
        if success:
            self.status_bar.showMessage(message, 3000)
        else:
            MessageHelper.show_error(self, message)
    
    def init_ui(self):
        """UIの初期化"""
        self.setWindowTitle("賃貸管理システム v2.0 - Basic Edition")
        self.setGeometry(100, 50, 1400, 900)
        
        # アプリケーションスタイル設定
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: white;
            }
            QTabBar::tab {
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #2196F3;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        # メインウィジェット
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # メインレイアウト
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # ヘッダー
        header_layout = QHBoxLayout()
        
        # タイトル
        title_label = QLabel("賃貸管理システム")
        title_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2196F3;")
        header_layout.addWidget(title_label)
        
        # バージョン情報
        version_label = QLabel("v2.0 Basic Edition (OCR機能無効)")
        version_label.setStyleSheet("color: gray;")
        header_layout.addWidget(version_label)
        
        header_layout.addStretch()
        
        # 現在日時
        self.datetime_label = QLabel()
        self.datetime_label.setStyleSheet("color: #666;")
        header_layout.addWidget(self.datetime_label)
        
        # 日時更新タイマー
        self.datetime_timer = QTimer()
        self.datetime_timer.timeout.connect(self.update_datetime)
        self.datetime_timer.start(1000)  # 1秒ごとに更新
        self.update_datetime()
        
        layout.addLayout(header_layout)
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        
        # 統計ダッシュボード（簡易版）
        self.stats_widget = BasicStatsWidget()
        self.tab_widget.addTab(self.stats_widget, "📊 統計")
        
        # 顧客管理タブ（改良版）
        self.customer_tab = CustomerTabImproved()
        self.tab_widget.addTab(self.customer_tab, "👥 顧客管理")
        
        # 部屋管理タブ
        self.unit_tab = UnitTab()
        self.tab_widget.addTab(self.unit_tab, "🚪 部屋管理")
        
        # 契約管理タブ
        self.contract_tab = ContractTab()
        self.tab_widget.addTab(self.contract_tab, "📝 契約管理")
        
        # タスク管理タブ
        self.task_tab = TaskTab()
        self.tab_widget.addTab(self.task_tab, "📋 タスク管理")
        
        # 接点履歴タブ
        self.communication_tab = CommunicationTab()
        self.tab_widget.addTab(self.communication_tab, "📞 接点履歴")
        
        # タブ変更時のイベント
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        layout.addWidget(self.tab_widget)
        main_widget.setLayout(layout)
    
    def setup_menu_bar(self):
        """メニューバーの設定"""
        menubar = self.menuBar()
        
        # ファイルメニュー
        file_menu = menubar.addMenu("ファイル")
        
        # 新規作成
        new_action = QAction("新規作成", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.on_new)
        file_menu.addAction(new_action)
        
        # エクスポート
        export_action = QAction("エクスポート", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.on_export)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # 終了
        exit_action = QAction("終了", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 表示メニュー
        view_menu = menubar.addMenu("表示")
        
        # 更新
        refresh_action = QAction("更新", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.on_refresh)
        view_menu.addAction(refresh_action)
        
        # ヘルプメニュー
        help_menu = menubar.addMenu("ヘルプ")
        
        # バージョン情報
        about_action = QAction("バージョン情報", self)
        about_action.triggered.connect(self.on_about)
        help_menu.addAction(about_action)
    
    def setup_status_bar(self):
        """ステータスバーの設定"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # デフォルトメッセージ
        self.status_bar.showMessage("準備完了 (Basic Edition)")
        
        # 永続的なウィジェット
        self.connection_label = QLabel("DB: 接続済み")
        self.connection_label.setStyleSheet("color: green;")
        self.status_bar.addPermanentWidget(self.connection_label)
        
        self.mode_label = QLabel("モード: Basic (OCRなし)")
        self.mode_label.setStyleSheet("color: orange;")
        self.status_bar.addPermanentWidget(self.mode_label)
    
    def update_datetime(self):
        """日時表示を更新"""
        now = datetime.now()
        self.datetime_label.setText(now.strftime("%Y年%m月%d日 %H:%M:%S"))
    
    def on_tab_changed(self, index):
        """タブが変更されたときの処理"""
        tab_name = self.tab_widget.tabText(index)
        self.status_bar.showMessage(f"{tab_name}を表示中", 2000)
    
    def on_new(self):
        """新規作成"""
        current_index = self.tab_widget.currentIndex()
        if current_index == 1:  # 顧客管理タブ
            self.on_new_customer()
        elif current_index == 3:  # 契約管理タブ
            self.on_new_contract()
    
    def on_new_customer(self):
        """新規顧客登録"""
        self.tab_widget.setCurrentIndex(1)  # 顧客管理タブに切り替え
        if hasattr(self.customer_tab, 'add_customer'):
            self.customer_tab.add_customer()
    
    def on_new_contract(self):
        """新規契約登録"""
        self.tab_widget.setCurrentIndex(3)  # 契約管理タブに切り替え
    
    def on_export(self):
        """エクスポート処理"""
        current_tab = self.tab_widget.currentWidget()
        if hasattr(current_tab, 'export_to_csv'):
            current_tab.export_to_csv()
        else:
            MessageHelper.show_warning(self, "このタブではエクスポート機能が利用できません")
    
    def on_refresh(self):
        """更新処理"""
        current_tab = self.tab_widget.currentWidget()
        
        # 各タブの更新メソッドを呼び出す
        if hasattr(current_tab, 'load_stats'):
            current_tab.load_stats()
        elif hasattr(current_tab, 'load_customers'):
            current_tab.load_customers()
        elif hasattr(current_tab, 'load_units'):
            current_tab.load_units()
        elif hasattr(current_tab, 'load_contracts'):
            current_tab.load_contracts()
        elif hasattr(current_tab, 'load_tasks'):
            current_tab.load_tasks()
        elif hasattr(current_tab, 'load_communications'):
            current_tab.load_communications()
        
        self.status_bar.showMessage("更新完了", 2000)
    
    def on_about(self):
        """バージョン情報"""
        QMessageBox.about(
            self,
            "バージョン情報",
            "賃貸管理システム v2.0\n"
            "Basic Edition (OCR機能無効版)\n\n"
            "開発: AI Assistant\n"
            "最終更新: 2024年\n\n"
            "この版では以下の機能が利用可能です:\n"
            "- 顧客管理（検索・編集・削除・CSV出力）\n"
            "- 部屋管理\n"
            "- 契約管理\n"
            "- タスク管理\n"
            "- 接点履歴管理\n\n"
            "OCR機能を使用するには、Google AI\n"
            "ライブラリをインストールしてください。"
        )
    
    def closeEvent(self, event):
        """終了時の処理"""
        reply = MessageHelper.confirm(
            self,
            "システムを終了してもよろしいですか？",
            "終了確認"
        )
        
        if reply:
            # タイマー停止
            if hasattr(self, 'datetime_timer'):
                self.datetime_timer.stop()
            event.accept()
        else:
            event.ignore()

def main():
    """メイン関数"""
    app = QApplication(sys.argv)
    
    # アプリケーションスタイル設定
    app.setStyle('Fusion')
    
    # メインウィンドウ
    window = MainWindowBasic()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()