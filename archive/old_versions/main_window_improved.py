"""
改良版メインウィンドウ - ダッシュボードと改良版タブを統合
"""
import sys
import os
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTabWidget, QLabel, QMessageBox,
                             QStatusBar, QMenuBar, QMenu, QToolBar, QSplashScreen)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QAction, QPixmap

# モデルとユーティリティ
from models import create_tables
from utils import MessageHelper

# タブモジュール
from dashboard_tab import DashboardTab
from customer_tab_improved import CustomerTabImproved
from property_tab import PropertyTab
from unit_tab import UnitTab
from contract_tab import ContractTab
from document_tab import DocumentTab
from checklist_tab import ChecklistTab
from task_tab import TaskTab
from communication_tab import CommunicationTab
from consistency_check_tab import ConsistencyCheckTab

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

class MainWindowImproved(QMainWindow):
    """改良版メインウィンドウ"""
    
    def __init__(self):
        super().__init__()
        self.init_database()
        self.init_ui()
        self.setup_menu_bar()
        self.setup_tool_bar()
        self.setup_status_bar()
        self.check_environment()
    
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
        self.setWindowTitle("賃貸管理システム v2.0 - Professional Edition")
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
        version_label = QLabel("v2.0 Professional")
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
        
        # ダッシュボードタブ（最初に表示）
        self.dashboard_tab = DashboardTab()
        self.tab_widget.addTab(self.dashboard_tab, "📊 ダッシュボード")
        
        # 顧客管理タブ（改良版）
        self.customer_tab = CustomerTabImproved()
        self.tab_widget.addTab(self.customer_tab, "👥 顧客管理")
        
        # 物件管理タブ
        self.property_tab = PropertyTab()
        self.tab_widget.addTab(self.property_tab, "🏢 物件管理")
        
        # 部屋管理タブ
        self.unit_tab = UnitTab()
        self.tab_widget.addTab(self.unit_tab, "🚪 部屋管理")
        
        # 契約管理タブ
        self.contract_tab = ContractTab()
        self.tab_widget.addTab(self.contract_tab, "📝 契約管理")
        
        # 書類管理タブ
        self.document_tab = DocumentTab()
        self.tab_widget.addTab(self.document_tab, "📁 書類管理")
        
        # チェックリストタブ
        self.checklist_tab = ChecklistTab()
        self.tab_widget.addTab(self.checklist_tab, "✅ チェックリスト")
        
        # タスク管理タブ
        self.task_tab = TaskTab()
        self.tab_widget.addTab(self.task_tab, "📋 タスク管理")
        
        # 接点履歴タブ
        self.communication_tab = CommunicationTab()
        self.tab_widget.addTab(self.communication_tab, "📞 接点履歴")
        
        # 整合性チェックタブ
        self.consistency_check_tab = ConsistencyCheckTab()
        self.tab_widget.addTab(self.consistency_check_tab, "🔍 整合性チェック")
        
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
        
        # 編集メニュー
        edit_menu = menubar.addMenu("編集")
        
        # 検索
        search_action = QAction("検索", self)
        search_action.setShortcut("Ctrl+F")
        search_action.triggered.connect(self.on_search)
        edit_menu.addAction(search_action)
        
        # 表示メニュー
        view_menu = menubar.addMenu("表示")
        
        # 更新
        refresh_action = QAction("更新", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.on_refresh)
        view_menu.addAction(refresh_action)
        
        # フルスクリーン
        fullscreen_action = QAction("フルスクリーン", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        # ツールメニュー
        tools_menu = menubar.addMenu("ツール")
        
        # データベース管理
        db_action = QAction("データベース管理", self)
        db_action.triggered.connect(self.on_database_management)
        tools_menu.addAction(db_action)
        
        # 設定
        settings_action = QAction("設定", self)
        settings_action.triggered.connect(self.on_settings)
        tools_menu.addAction(settings_action)
        
        # ヘルプメニュー
        help_menu = menubar.addMenu("ヘルプ")
        
        # ユーザーマニュアル
        manual_action = QAction("ユーザーマニュアル", self)
        manual_action.setShortcut("F1")
        manual_action.triggered.connect(self.on_manual)
        help_menu.addAction(manual_action)
        
        # バージョン情報
        about_action = QAction("バージョン情報", self)
        about_action.triggered.connect(self.on_about)
        help_menu.addAction(about_action)
    
    def setup_tool_bar(self):
        """ツールバーの設定"""
        toolbar = QToolBar("メインツールバー")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # ダッシュボード
        dashboard_action = QAction("📊 ダッシュボード", self)
        dashboard_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(0))
        toolbar.addAction(dashboard_action)
        
        toolbar.addSeparator()
        
        # 新規登録
        new_customer_action = QAction("➕ 新規顧客", self)
        new_customer_action.triggered.connect(self.on_new_customer)
        toolbar.addAction(new_customer_action)
        
        new_property_action = QAction("➕ 新規物件", self)
        new_property_action.triggered.connect(self.on_new_property)
        toolbar.addAction(new_property_action)
        
        new_contract_action = QAction("➕ 新規契約", self)
        new_contract_action.triggered.connect(self.on_new_contract)
        toolbar.addAction(new_contract_action)
        
        toolbar.addSeparator()
        
        # 更新
        refresh_action = QAction("🔄 更新", self)
        refresh_action.triggered.connect(self.on_refresh)
        toolbar.addAction(refresh_action)
        
        # エクスポート
        export_action = QAction("📤 エクスポート", self)
        export_action.triggered.connect(self.on_export)
        toolbar.addAction(export_action)
    
    def setup_status_bar(self):
        """ステータスバーの設定"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # デフォルトメッセージ
        self.status_bar.showMessage("準備完了")
        
        # 永続的なウィジェット
        self.connection_label = QLabel("DB: 接続済み")
        self.connection_label.setStyleSheet("color: green;")
        self.status_bar.addPermanentWidget(self.connection_label)
        
        self.user_label = QLabel("ユーザー: 管理者")
        self.status_bar.addPermanentWidget(self.user_label)
    
    def check_environment(self):
        """環境チェック"""
        import os
        
        # APIキーチェック
        if not os.getenv('GEMINI_API_KEY'):
            MessageHelper.show_warning(
                self,
                "Gemini APIキーが設定されていません。\n"
                "OCR機能を使用するには、.envファイルにAPIキーを設定してください。"
            )
    
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
        elif current_index == 2:  # 物件管理タブ
            self.on_new_property()
        elif current_index == 4:  # 契約管理タブ
            self.on_new_contract()
    
    def on_new_customer(self):
        """新規顧客登録"""
        self.tab_widget.setCurrentIndex(1)  # 顧客管理タブに切り替え
        if hasattr(self.customer_tab, 'add_customer'):
            self.customer_tab.add_customer()
    
    def on_new_property(self):
        """新規物件登録"""
        self.tab_widget.setCurrentIndex(2)  # 物件管理タブに切り替え
        # PropertyTabの新規登録メソッドを呼び出す
    
    def on_new_contract(self):
        """新規契約登録"""
        self.tab_widget.setCurrentIndex(4)  # 契約管理タブに切り替え
        # ContractTabの新規登録メソッドを呼び出す
    
    def on_export(self):
        """エクスポート処理"""
        current_tab = self.tab_widget.currentWidget()
        if hasattr(current_tab, 'export_to_csv'):
            current_tab.export_to_csv()
        else:
            MessageHelper.show_warning(self, "このタブではエクスポート機能が利用できません")
    
    def on_search(self):
        """検索処理"""
        current_tab = self.tab_widget.currentWidget()
        if hasattr(current_tab, 'search_edit'):
            current_tab.search_edit.setFocus()
    
    def on_refresh(self):
        """更新処理"""
        current_tab = self.tab_widget.currentWidget()
        
        # 各タブの更新メソッドを呼び出す
        if hasattr(current_tab, 'load_dashboard_data'):
            current_tab.load_dashboard_data()
        elif hasattr(current_tab, 'load_customers'):
            current_tab.load_customers()
        elif hasattr(current_tab, 'load_properties'):
            current_tab.load_properties()
        elif hasattr(current_tab, 'load_units'):
            current_tab.load_units()
        elif hasattr(current_tab, 'load_contracts'):
            current_tab.load_contracts()
        elif hasattr(current_tab, 'load_documents'):
            current_tab.load_documents()
        elif hasattr(current_tab, 'load_tasks'):
            current_tab.load_tasks()
        elif hasattr(current_tab, 'load_communications'):
            current_tab.load_communications()
        
        self.status_bar.showMessage("更新完了", 2000)
    
    def toggle_fullscreen(self):
        """フルスクリーン切り替え"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def on_database_management(self):
        """データベース管理"""
        MessageHelper.show_warning(self, "データベース管理機能は現在開発中です")
    
    def on_settings(self):
        """設定画面"""
        MessageHelper.show_warning(self, "設定機能は現在開発中です")
    
    def on_manual(self):
        """ユーザーマニュアル"""
        MessageHelper.show_warning(self, "ユーザーマニュアルは準備中です")
    
    def on_about(self):
        """バージョン情報"""
        QMessageBox.about(
            self,
            "バージョン情報",
            "賃貸管理システム v2.0\n"
            "Professional Edition\n\n"
            "開発: AI Assistant\n"
            "最終更新: 2024年\n\n"
            "このシステムは賃貸不動産管理業務を\n"
            "効率化するために開発されました。"
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
            if hasattr(self.dashboard_tab, 'auto_refresh_timer'):
                self.dashboard_tab.auto_refresh_timer.stop()
            event.accept()
        else:
            event.ignore()

def main():
    """メイン関数"""
    app = QApplication(sys.argv)
    
    # アプリケーションスタイル設定
    app.setStyle('Fusion')
    
    # スプラッシュスクリーン（オプション）
    # splash = QSplashScreen()
    # splash.showMessage("起動中...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter)
    # splash.show()
    
    # メインウィンドウ
    window = MainWindowImproved()
    window.show()
    
    # splash.finish(window)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()