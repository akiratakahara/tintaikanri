"""
最小版メインウィンドウ - OCR機能完全除去
"""
import sys
import os
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTabWidget, QLabel, QMessageBox,
                             QStatusBar, QMenuBar, QMenu, QToolBar, QPushButton)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QAction

# モデルとユーティリティ
from models import create_tables
from utils import MessageHelper
from ui_styles import ModernStyles

# 基本タブモジュール（OCR機能完全除去）
from customer_tab_improved import CustomerTabImproved
from property_tab_basic import PropertyTabBasic
from contract_tab_improved import ContractTabImproved
from task_tab_basic import TaskTabBasic
from communication_tab_basic import CommunicationTabBasic
from calendar_tab import CalendarTab
from dashboard_enhanced import EnhancedDashboard

class DatabaseInitWorker(QThread):
    """データベース初期化ワーカー"""
    finished = pyqtSignal(bool, str)
    
    def run(self):
        try:
            create_tables()
            self.finished.emit(True, "データベースが正常に初期化されました")
        except Exception as e:
            self.finished.emit(False, f"データベース初期化エラー: {str(e)}")

class StatsWidget(QWidget):
    """統計ウィジェット"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_stats()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # タイトル
        title_label = QLabel("賃貸管理システム ダッシュボード")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 統計表示エリア
        from PyQt6.QtWidgets import QGroupBox, QGridLayout
        
        # システム統計
        stats_group = QGroupBox("システム統計")
        stats_layout = QGridLayout()
        
        self.customer_label = QLabel("顧客数: 0")
        self.property_label = QLabel("物件数: 0")
        self.contract_label = QLabel("契約数: 0")
        self.update_label = QLabel("最終更新: -")
        
        stats_layout.addWidget(self.customer_label, 0, 0)
        stats_layout.addWidget(self.property_label, 0, 1)
        stats_layout.addWidget(self.contract_label, 1, 0)
        stats_layout.addWidget(self.update_label, 1, 1)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # 機能説明
        info_group = QGroupBox("利用可能な機能")
        info_layout = QVBoxLayout()
        
        features = [
            "✅ 顧客管理（検索・編集・削除・CSV出力）",
            "✅ 物件管理（物件登録・編集・部屋追加）",
            "✅ 契約管理（契約情報の登録・管理）",
            "✅ タスク管理（期限・優先度管理）",
            "✅ 接点履歴管理（顧客とのコミュニケーション記録）",
            "✅ カレンダー表示（タスク・更新スケジュール一覧）",
            "✅ データエクスポート（CSV形式）",
            "",
            "⚠️ この版ではOCR機能は利用できません",
            "   （物件管理・書類管理・整合性チェック機能を除く）"
        ]
        
        for feature in features:
            feature_label = QLabel(feature)
            if feature.startswith("⚠️"):
                feature_label.setStyleSheet("color: orange;")
            info_layout.addWidget(feature_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # 更新ボタン
        refresh_btn = QPushButton("統計を更新")
        refresh_btn.clicked.connect(self.load_stats)
        refresh_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 10px; }")
        layout.addWidget(refresh_btn)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def load_stats(self):
        """統計データを読み込み"""
        try:
            from models import Customer, Property, TenantContract
            
            customers = Customer.get_all()
            properties = Property.get_all()
            contracts = TenantContract.get_all()
            
            self.customer_label.setText(f"顧客数: {len(customers)}件")
            self.property_label.setText(f"物件数: {len(properties)}件")
            self.contract_label.setText(f"契約数: {len(contracts)}件")
            self.update_label.setText(f"最終更新: {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            self.customer_label.setText(f"エラー: {str(e)}")

class MainWindowMinimal(QMainWindow):
    """最小版メインウィンドウ"""
    
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
            # statusBar()メソッドでアクセスする必要がある
            if hasattr(self, 'statusBar'):
                self.statusBar().showMessage(message, 3000)
            else:
                print(f"データベース初期化成功: {message}")
        else:
            MessageHelper.show_error(self, message)
    
    def init_ui(self):
        """UIの初期化"""
        self.setWindowTitle("賃貸管理システム v2.0 - Minimal Edition")
        
        # ウィンドウサイズの最適化（スクリーン解像度に応じて調整）
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        
        # スクリーンの85%のサイズで開始（全画面に近いサイズ）
        width = min(1600, int(screen_geometry.width() * 0.85))
        height = min(1000, int(screen_geometry.height() * 0.85))
        
        # 中央に配置
        x = (screen_geometry.width() - width) // 2
        y = (screen_geometry.height() - height) // 2
        
        self.setGeometry(x, y, width, height)
        
        # 最小サイズ設定（小さな画面でも使用可能）
        self.setMinimumSize(1000, 700)
        
        # 全画面モードのサポートを有効化
        self.setWindowState(Qt.WindowState.WindowMaximized if screen_geometry.width() > 1920 else Qt.WindowState.WindowNoState)
        
        # モダンスタイル適用
        self.setStyleSheet(ModernStyles.get_all_styles())
        
        # メインウィジェット
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # レイアウト（全画面対応）
        layout = QVBoxLayout()
        # 全画面時はマージンを小さくしてコンテンツ領域を最大化
        layout.setContentsMargins(8, 8, 8, 8)
        
        # モダンヘッダー
        header_widget = QWidget()
        header_widget.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                          stop: 0 #2563eb,
                                          stop: 1 #3b82f6);
                border-radius: 16px;
                margin: 8px;
                padding: 16px;
            }}
        """)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(24, 16, 24, 16)
        
        # タイトルエリア
        title_container = QWidget()
        title_container_layout = QVBoxLayout(title_container)
        title_container_layout.setSpacing(4)
        title_container_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("🏢 賃貸管理システム")
        # 日本語対応フォントを使用
        title_font = QFont()
        title_font.setPointSize(28)
        title_font.setWeight(QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: white;")
        
        version_label = QLabel("v2.0 Minimal Edition - モダンUI対応")
        version_font = QFont()
        version_font.setPointSize(12)
        version_label.setFont(version_font)
        version_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        
        title_container_layout.addWidget(title_label)
        title_container_layout.addWidget(version_label)
        
        header_layout.addWidget(title_container)
        header_layout.addStretch()
        
        # ステータスエリア
        status_container = QWidget()
        status_container_layout = QVBoxLayout(status_container)
        status_container_layout.setSpacing(4)
        status_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # 現在日時
        self.datetime_label = QLabel()
        datetime_font = QFont()
        datetime_font.setPointSize(11)
        self.datetime_label.setFont(datetime_font)
        self.datetime_label.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        self.datetime_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # システム状態表示
        system_status_label = QLabel("🟢 システム正常稼働中")
        status_font = QFont()
        status_font.setPointSize(10)
        system_status_label.setFont(status_font)
        system_status_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        system_status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        status_container_layout.addWidget(self.datetime_label)
        status_container_layout.addWidget(system_status_label)
        
        header_layout.addWidget(status_container)
        
        layout.addWidget(header_widget)
        
        # タブウィジェット（コンテナー）—全画面対応
        tab_container = QWidget()
        tab_container.setStyleSheet(f"""
            QWidget {{
                background-color: white;
                border-radius: 12px;
                margin: 4px;
            }}
        """)
        tab_layout = QVBoxLayout(tab_container)
        # 全画面時はパディングを減らしてコンテンツ領域を広く
        tab_layout.setContentsMargins(12, 12, 12, 12)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(ModernStyles.get_tab_widget_style())
        
        # 拡張ダッシュボード
        try:
            self.dashboard = EnhancedDashboard()
            self.tab_widget.addTab(self.dashboard, "📊  ダッシュボード")
        except Exception as e:
            # フォールバック：基本ダッシュボード
            self.stats_widget = StatsWidget()
            self.tab_widget.addTab(self.stats_widget, "📊  ダッシュボード")
        
        # 顧客管理タブ
        try:
            self.customer_tab = CustomerTabImproved()
            self.tab_widget.addTab(self.customer_tab, "👥  顧客管理")
        except Exception as e:
            error_widget = self.create_error_widget(f"顧客管理タブ読み込みエラー: {str(e)}")
            self.tab_widget.addTab(error_widget, "❌  顧客管理")
        
        # 物件管理タブ
        try:
            self.property_tab = PropertyTabBasic()
            self.tab_widget.addTab(self.property_tab, "🏢  物件管理")
        except Exception as e:
            error_widget = self.create_error_widget(f"物件管理タブ読み込みエラー: {str(e)}")
            self.tab_widget.addTab(error_widget, "❌  物件管理")
        
        # 契約管理タブ
        try:
            self.contract_tab = ContractTabImproved()
            self.tab_widget.addTab(self.contract_tab, "📝  契約管理")
        except Exception as e:
            error_widget = self.create_error_widget(f"契約管理タブ読み込みエラー: {str(e)}")
            self.tab_widget.addTab(error_widget, "❌  契約管理")
        
        # タスク管理タブ
        try:
            self.task_tab = TaskTabBasic()
            self.tab_widget.addTab(self.task_tab, "📋  タスク管理")
        except Exception as e:
            error_widget = self.create_error_widget(f"タスク管理タブ読み込みエラー: {str(e)}")
            self.tab_widget.addTab(error_widget, "❌  タスク管理")
        
        # 接点履歴タブ
        try:
            self.communication_tab = CommunicationTabBasic()
            self.tab_widget.addTab(self.communication_tab, "📞  接点履歴")
        except Exception as e:
            error_widget = self.create_error_widget(f"接点履歴タブ読み込みエラー: {str(e)}")
            self.tab_widget.addTab(error_widget, "❌  接点履歴")
        
        # カレンダータブ
        try:
            self.calendar_tab = CalendarTab()
            self.tab_widget.addTab(self.calendar_tab, "📅  カレンダー")
            
            # タスク更新時のカレンダー自動反映設定
            self.setup_task_calendar_sync()
        except Exception as e:
            error_widget = self.create_error_widget(f"カレンダータブ読み込みエラー: {str(e)}")
            self.tab_widget.addTab(error_widget, "❌  カレンダー")
        
        # タブ変更時の自動更新は不要のため無効化
        # self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        tab_layout.addWidget(self.tab_widget)
        layout.addWidget(tab_container)
        main_widget.setLayout(layout)
        
        # 日時更新タイマー
        self.datetime_timer = QTimer()
        self.datetime_timer.timeout.connect(self.update_datetime)
        self.datetime_timer.start(1000)
        self.update_datetime()
    
    def create_error_widget(self, error_message):
        """エラー表示用ウィジェットを作成"""
        error_widget = QWidget()
        error_layout = QVBoxLayout(error_widget)
        error_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        error_icon = QLabel("⚠️")
        icon_font = QFont()
        icon_font.setPointSize(48)
        error_icon.setFont(icon_font)
        error_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        error_title = QLabel("エラーが発生しました")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setWeight(QFont.Weight.Bold)
        error_title.setFont(title_font)
        error_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_title.setStyleSheet("color: #ef4444; margin: 16px;")
        
        error_detail = QLabel(error_message)
        detail_font = QFont()
        detail_font.setPointSize(11)
        error_detail.setFont(detail_font)
        error_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_detail.setWordWrap(True)
        error_detail.setStyleSheet("color: #64748b; margin: 8px; max-width: 400px;")
        
        error_layout.addWidget(error_icon)
        error_layout.addWidget(error_title)
        error_layout.addWidget(error_detail)
        
        return error_widget
    
    def setup_menu_bar(self):
        """メニューバー設定"""
        menubar = self.menuBar()
        
        # ファイルメニュー
        file_menu = menubar.addMenu("ファイル")
        
        new_action = QAction("新規作成", self)
        new_action.setShortcut("Ctrl+N")
        file_menu.addAction(new_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("終了", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # ヘルプメニュー
        help_menu = menubar.addMenu("ヘルプ")
        
        about_action = QAction("バージョン情報", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_status_bar(self):
        """ステータスバー設定"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        status_bar.showMessage("準備完了 - Minimal Edition")
        
        # 状態表示
        mode_label = QLabel("モード: 最小版")
        mode_label.setStyleSheet("color: blue;")
        status_bar.addPermanentWidget(mode_label)
    
    def update_datetime(self):
        """日時更新"""
        now = datetime.now()
        self.datetime_label.setText(now.strftime("%Y年%m月%d日 %H:%M:%S"))
    
    def on_tab_changed(self, index):
        """タブが変更されたときの処理（無効化）"""
        # 自動更新機能は不要のため無効化
        pass
    
    def setup_task_calendar_sync(self):
        """タスク更新時のカレンダー自動反映を設定"""
        try:
            # タスク管理タブとカレンダータブを接続
            if hasattr(self, 'task_tab') and hasattr(self, 'calendar_tab'):
                # タスクが更新された時にカレンダーを更新
                if hasattr(self.task_tab, 'task_updated'):
                    self.task_tab.task_updated.connect(self.update_calendar_from_task)
            
            # 契約管理タブとカレンダータブを接続
            if hasattr(self, 'contract_tab') and hasattr(self, 'calendar_tab'):
                # 契約が更新された時にカレンダーを更新
                if hasattr(self.contract_tab, 'contract_updated'):
                    self.contract_tab.contract_updated.connect(self.update_calendar_from_contract)
                    
        except Exception as e:
            print(f"タスク-カレンダー同期設定エラー: {e}")
    
    def update_calendar_from_task(self):
        """タスク更新時にカレンダーを即座に更新"""
        try:
            if hasattr(self, 'calendar_tab'):
                # タスクのみの高速更新を使用
                self.calendar_tab.quick_refresh_tasks()
                print("カレンダーをタスク更新に応じて即座に更新しました")
        except Exception as e:
            print(f"タスク更新時のカレンダー更新エラー: {e}")
    
    def update_calendar_from_contract(self):
        """契約更新時にカレンダーを即座に更新"""
        try:
            if hasattr(self, 'calendar_tab'):
                # 契約データのみの高速更新を使用
                self.calendar_tab.quick_refresh_contracts()
                print("カレンダーを契約更新に応じて即座に更新しました")
        except Exception as e:
            print(f"契約更新時のカレンダー更新エラー: {e}")
    
    def show_about(self):
        """バージョン情報表示"""
        QMessageBox.about(
            self,
            "バージョン情報",
            "賃貸管理システム v2.0\n"
            "Minimal Edition\n\n"
            "利用可能な機能:\n"
            "• 顧客管理\n"
            "• 物件管理\n"
            "• 契約管理\n"
            "• タスク管理\n"
            "• 接点履歴管理\n"
            "• カレンダー表示\n"
            "• データエクスポート\n\n"
            "開発: AI Assistant\n"
            "最終更新: 2024年"
        )
    
    def resizeEvent(self, event):
        """ウィンドウサイズ変更時の処理"""
        super().resizeEvent(event)
        
        # 全画面時のレイアウト調整
        try:
            window_width = event.size().width()
            window_height = event.size().height()
            
            # ヘッダーの高さをサイズに応じて調整
            if hasattr(self, 'datetime_label'):
                if window_width > 1600:  # 大画面
                    header_font_size = "14px"
                    title_font_size = "32px"
                elif window_width > 1200:  # 中画面  
                    header_font_size = "12px"
                    title_font_size = "28px"
                else:  # 小画面
                    header_font_size = "11px"
                    title_font_size = "24px"
                
                # 日時ラベルのサイズ調整
                self.datetime_label.setStyleSheet(f"color: rgba(255, 255, 255, 0.9); font-size: {header_font_size};")
            
            # タブウィジェットのサイズ調整
            if hasattr(self, 'tab_widget'):
                # カレンダータブのリサイズイベントを発火
                current_widget = self.tab_widget.currentWidget()
                if current_widget and hasattr(current_widget, 'resizeEvent'):
                    try:
                        current_widget.resizeEvent(event)
                    except Exception as resize_error:
                        print(f"タブリサイズエラー: {resize_error}")
                    
        except Exception as e:
            print(f"リサイズイベントエラー: {e}")
    
    def changeEvent(self, event):
        """ウィンドウ状態変更時の処理"""
        super().changeEvent(event)
        
        # 最大化/最小化時の処理
        if event.type() == event.Type.WindowStateChange:
            if self.isMaximized():
                print("ウィンドウが最大化されました")
                # 最大化時の特別な処理があればここに追加
            elif self.isMinimized():
                print("ウィンドウが最小化されました")
    
    def closeEvent(self, event):
        """終了処理"""
        if hasattr(self, 'datetime_timer'):
            self.datetime_timer.stop()
        event.accept()

def main():
    """メイン関数"""
    # Windowsでの文字化け対策を強化
    if os.name == 'nt':  # Windows
        try:
            # システムのデフォルトエンコーディングをUTF-8に設定
            import sys
            import codecs
            
            # 標準出力をUTF-8エンコーディングでラップ
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'ignore')
            if hasattr(sys.stderr, 'buffer'):
                sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'ignore')
            
            # 環境変数を設定
            os.environ['PYTHONIOENCODING'] = 'utf-8'
            
            # ロケール設定
            import locale
            try:
                locale.setlocale(locale.LC_ALL, 'ja_JP.UTF-8')
            except:
                try:
                    locale.setlocale(locale.LC_ALL, 'Japanese_Japan.65001')  # UTF-8
                except:
                    try:
                        locale.setlocale(locale.LC_ALL, 'Japanese_Japan.932')  # Shift_JIS
                    except:
                        try:
                            locale.setlocale(locale.LC_ALL, '')  # システムデフォルト
                        except:
                            pass
        except ImportError:
            pass
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # 日本語フォントの設定
    try:
        # Windowsの場合は日本語フォントを明示的に設定
        if os.name == 'nt':
            font = QFont("Yu Gothic UI", 9)  # Windows 10のデフォルト日本語フォント
            if not font.exactMatch():
                font = QFont("Meiryo UI", 9)  # フォールバック
                if not font.exactMatch():
                    font = QFont("MS UI Gothic", 9)  # 最終フォールバック
            app.setFont(font)
    except:
        pass
    
    # アプリケーションの文字エンコーディング設定
    app.setApplicationName("賃貸管理システム v2.0")
    app.setApplicationDisplayName("賃貸管理システム v2.0 - Minimal Edition")
    
    try:
        # UTF-8での出力を試みる
        # コンソール出力の文字化け対策
        try:
            # WindowsのコンソールでUTF-8を有効化
            if os.name == 'nt':
                os.system('chcp 65001 >nul 2>&1')  # UTF-8コードページに変更
            
            print("=" * 56)
            print("賃貸管理システム v2.0 - Minimal Edition")
            print("=" * 56)
            print("OCR機能を完全に除去した軽量版です")
            print("システムPythonでの起動を学習中...")
            print()
        except UnicodeEncodeError:
            # エンコードエラーの場合はASCIIで表示
            print("=" * 56)
            print("Tintai Management System v2.0 - Minimal Edition")
            print("=" * 56)
            print("Light version with OCR functionality removed")
            print("Starting with system Python...")
            print()
        except Exception as e:
            print(f"Console encoding error: {e}")
        
        window = MainWindowMinimal()
        window.show()
        
        try:
            print("[SUCCESS] アプリケーションが正常に起動しました")
        except UnicodeEncodeError:
            print("[SUCCESS] Application started successfully")
        except Exception as e:
            print(f"[SUCCESS] App started (encoding issue: {e})")
        
        sys.exit(app.exec())
    except Exception as e:
        error_msg = f"アプリケーション起動エラー: {e}"
        print(error_msg)
        try:
            # GUI環境が利用可能な場合はメッセージボックスを表示
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Icon.Critical)
            error_dialog.setWindowTitle("起動エラー")
            error_dialog.setText("アプリケーションの起動に失敗しました")
            error_dialog.setDetailedText(str(e))
            error_dialog.exec()
        except:
            pass
        try:
            input("エラーが発生しました。Enterキーで終了...")
        except:
            input("Error occurred. Press Enter to exit...")

if __name__ == "__main__":
    main()