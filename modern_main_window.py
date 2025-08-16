"""
モダンメインウィンドウ - 完全刷新版
直感的で使いやすいダッシュボード形式のUI
"""
import sys
import os
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

# プロジェクトルートをPythonパスに追加（srcフォルダ内のモジュールがルートのモジュールにアクセスできるように）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# モダンUIシステム
from modern_ui_system import ModernUITheme, ModernButton, ModernCard, ModernSidebar, ModernInput

# 既存のタブ（オーナー機能対応版）
from tabs.customer_tab import CustomerTab
from tabs.property_unified_management import PropertyUnifiedManagement
# from tabs.unit_tab import UnitTab  # 統合管理に移行
from tabs.contract_tab_improved import ContractTabImproved
from tabs.task_tab_basic import TaskTabBasic
from tabs.communication_tab_basic import CommunicationTabBasic
from tabs.dashboard_tab import DashboardTab

# モダンタブ
try:
    from tabs.calendar_tab import CalendarTab
except ImportError:
    from tabs.modern_calendar_tab import ModernCalendarTab as CalendarTab

# その他
from models import create_tables
from utils import MessageHelper

class ModernDashboard(QWidget):
    """モダンなダッシュボードウィジェット"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_dashboard_data()
        
    def setup_ui(self):
        """ダッシュボードUIを構築"""
        # ページコンテナを作成
        from ui.ui_helpers import make_page_container, make_scroll_page
        container, layout = make_page_container()
        
        # 中央寄せコンテナ（最大幅1200px）
        center_container = QWidget()
        center_container.setMaximumWidth(1200)
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(16)
        
        # ページタイトル
        title_label = QLabel("📊 ダッシュボード")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernUITheme.COLORS['text_primary']};
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_3xl']};
                font-weight: {ModernUITheme.TYPOGRAPHY['font_weight_bold']};
                margin-bottom: {ModernUITheme.SPACING['lg']};
            }}
        """)
        center_layout.addWidget(title_label)
        
        # メインコンテンツエリア（左右並列）
        main_content_layout = QHBoxLayout()
        main_content_layout.setSpacing(20)
        
        # 左側: 統計カード群
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(12)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 統計カードを縦並びで作成
        self.stat_cards = [
            self.create_compact_stat_card("👥", "顧客数", "0", ModernUITheme.COLORS['info']),
            self.create_compact_stat_card("🏢", "物件数", "0", ModernUITheme.COLORS['success']),
            self.create_compact_stat_card("📝", "契約数", "0", ModernUITheme.COLORS['warning']),
            self.create_compact_stat_card("📋", "未完了タスク", "0", ModernUITheme.COLORS['danger'])
        ]
        
        for card in self.stat_cards:
            left_layout.addWidget(card)
        
        left_layout.addStretch()  # 下部に余白
        
        # 右側: タスク一覧
        task_list = self.create_task_list()
        
        # 並列レイアウトに追加
        main_content_layout.addWidget(left_widget, 1)  # 統計カードエリア
        main_content_layout.addWidget(task_list, 2)    # タスク一覧エリア（より幅を取る）
        
        center_layout.addLayout(main_content_layout)
        
        # 最近のアクティビティ（折りたたみ）
        from ui.ui_helpers import make_collapsible
        recent_activity = self.create_recent_activity()
        collapsible_activity = make_collapsible("📈 最近のアクティビティ", recent_activity, default_expanded=False)
        center_layout.addWidget(collapsible_activity)
        
        center_layout.addStretch()
        
        # 中央寄せ
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(center_container)
        
        # 単一スクロールページを作成
        scroll_page = make_scroll_page(container)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(scroll_page)
    
    def create_compact_stat_card(self, icon, title, value, color):
        """コンパクトな統計カードを作成"""
        card = QFrame()
        card.setObjectName("CompactStatCard")
        card.setFixedHeight(70)  # コンパクトな高さ
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {ModernUITheme.COLORS['bg_primary']};
                border: 1px solid {ModernUITheme.COLORS['border']};
                border-radius: {ModernUITheme.RADIUS['base']};
                border-left: 4px solid {color};
            }}
            QFrame:hover {{
                background-color: {ModernUITheme.COLORS['bg_secondary']};
            }}
        """)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # アイコン
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_xl']};
            }}
        """)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setFixedSize(32, 32)
        
        # タイトルと値
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernUITheme.COLORS['text_secondary']};
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_sm']};
                font-weight: {ModernUITheme.TYPOGRAPHY['font_weight_medium']};
            }}
        """)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernUITheme.COLORS['text_primary']};
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_2xl']};
                font-weight: {ModernUITheme.TYPOGRAPHY['font_weight_bold']};
            }}
        """)
        
        text_layout.addWidget(title_label)
        text_layout.addWidget(value_label)
        
        layout.addWidget(icon_label)
        layout.addLayout(text_layout)
        layout.addStretch()
        
        # 値を更新するためのラベルを保存
        if title == "顧客数":
            self.customer_value_label = value_label
        elif title == "物件数":
            self.property_value_label = value_label
        elif title == "契約数":
            self.contract_value_label = value_label
        elif title == "未完了タスク":
            self.task_value_label = value_label
        
        return card
    
    def create_task_list(self):
        """タスク一覧を作成"""
        card = ModernCard("📋 未完了タスク")
        layout = card.layout()
        
        # タスクテーブル
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(4)
        self.task_table.setHorizontalHeaderLabels(["タスク種別", "タイトル", "期限", "優先度"])
        
        # テーブルの設定
        self.task_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.task_table.setAlternatingRowColors(True)
        self.task_table.setMinimumHeight(200)
        self.task_table.setMaximumHeight(300)
        
        # 列幅設定
        header = self.task_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.task_table.verticalHeader().setDefaultSectionSize(32)
        
        # スタイル設定
        self.task_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {ModernUITheme.COLORS['bg_primary']};
                border: 1px solid {ModernUITheme.COLORS['border']};
                border-radius: 8px;
                gridline-color: {ModernUITheme.COLORS['border']};
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {ModernUITheme.COLORS['border_light']};
            }}
            QTableWidget::item:selected {{
                background-color: {ModernUITheme.COLORS['primary_lighter']};
            }}
            QHeaderView::section {{
                background-color: {ModernUITheme.COLORS['bg_secondary']};
                padding: 8px;
                border: none;
                font-weight: bold;
            }}
        """)
        
        layout.addWidget(self.task_table)
        
        # タスク一覧へのリンク
        view_all_btn = ModernButton("📄 すべてのタスクを表示", "outline", "sm")
        view_all_btn.clicked.connect(self.show_tasks_page)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(view_all_btn)
        layout.addLayout(btn_layout)
        
        return card
    
    def create_recent_activity(self):
        """最近のアクティビティを作成"""
        card = ModernCard("📈 最近のアクティビティ")
        layout = card.layout()
        
        # アクティビティリスト（サンプル）
        activities = [
            ("🆕", "新規顧客「田中太郎」を登録", "5分前"),
            ("📝", "サンプルマンション 101号室の契約を更新", "1時間前"),
            ("📋", "修繕対応タスクを完了", "2時間前"),
            ("🏢", "新物件「○○アパート」を追加", "3時間前"),
        ]
        
        for icon, description, time in activities:
            activity_layout = QHBoxLayout()
            activity_layout.setContentsMargins(0, 4, 0, 4)  # 垂直マージン追加
            
            icon_label = QLabel(icon)
            icon_label.setMinimumSize(20, 20)  # 固定サイズを最小サイズに変更
            
            desc_label = QLabel(description)
            desc_label.setStyleSheet(f"""
                QLabel {{
                    color: {ModernUITheme.COLORS['text_primary']};
                    font-size: {ModernUITheme.TYPOGRAPHY['font_size_base']};
                }}
            """)
            
            time_label = QLabel(time)
            time_label.setStyleSheet(f"""
                QLabel {{
                    color: {ModernUITheme.COLORS['text_muted']};
                    font-size: {ModernUITheme.TYPOGRAPHY['font_size_sm']};
                }}
            """)
            
            activity_layout.addWidget(icon_label)
            activity_layout.addWidget(desc_label)
            activity_layout.addStretch()
            activity_layout.addWidget(time_label)
            
            layout.addLayout(activity_layout)
        
        return card
    
    def load_dashboard_data(self):
        """ダッシュボードデータを読み込み"""
        try:
            from models import Customer, Property, TenantContract, Task
            
            # 各データの件数を取得
            customers = Customer.get_all() or []
            properties = Property.get_all() or []
            contracts = TenantContract.get_all() or []
            
            # タスクを取得
            tasks = Task.get_pending_tasks() or []
            
            # 統計を更新
            self.customer_value_label.setText(str(len(customers)))
            self.property_value_label.setText(str(len(properties)))
            self.contract_value_label.setText(str(len(contracts)))
            self.task_value_label.setText(str(len(tasks)))
            
            # タスクデータを取得してテーブルに表示
            self.load_tasks_to_table()
            
        except Exception as e:
            # エラー時はデフォルト値を設定
            print(f"ダッシュボードデータ読み込みエラー: {e}")
            if hasattr(self, 'customer_value_label'):
                self.customer_value_label.setText("0")
            if hasattr(self, 'property_value_label'):
                self.property_value_label.setText("0")
            if hasattr(self, 'contract_value_label'):
                self.contract_value_label.setText("0")
            if hasattr(self, 'task_value_label'):
                self.task_value_label.setText("0")
            
    def load_tasks_to_table(self):
        """タスクデータをテーブルに読み込み"""
        try:
            from models import Task
            
            # 未完了タスクを取得（最大5件）
            tasks = Task.get_pending_tasks() or []
            display_tasks = tasks[:5]  # 最初の5件のみ表示
            
            # テーブル設定
            self.task_table.setRowCount(len(display_tasks))
            
            for row, task in enumerate(display_tasks):
                # タスク種別
                type_item = QTableWidgetItem(task.get('task_type', ''))
                self.task_table.setItem(row, 0, type_item)
                
                # タイトル
                title_item = QTableWidgetItem(task.get('title', ''))
                self.task_table.setItem(row, 1, title_item)
                
                # 期限
                due_date = task.get('due_date', '')
                due_item = QTableWidgetItem(due_date)
                # 期限が近い場合は色を変える
                from datetime import datetime, date
                if due_date:
                    try:
                        due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
                        today = date.today()
                        days_diff = (due_date_obj - today).days
                        if days_diff <= 0:
                            due_item.setBackground(QColor("#ffebee"))  # 期限切れ（薄赤）
                        elif days_diff <= 3:
                            due_item.setBackground(QColor("#fff3e0"))  # 期限間近（薄オレンジ）
                    except:
                        pass
                self.task_table.setItem(row, 2, due_item)
                
                # 優先度
                priority = task.get('priority', '中')
                priority_item = QTableWidgetItem(priority)
                # 優先度に応じて色を設定
                if priority == '高':
                    priority_item.setBackground(QColor("#ffebee"))
                elif priority == '中':
                    priority_item.setBackground(QColor("#f3e5f5"))
                else:  # 低
                    priority_item.setBackground(QColor("#e8f5e8"))
                self.task_table.setItem(row, 3, priority_item)
                
        except Exception as e:
            # エラー時はサンプルデータを表示
            print(f"タスクデータ読み込みエラー: {e}")
            sample_tasks = [
                {'task_type': '更新案内', 'title': 'サンプルタスク', 'due_date': '2024-12-31', 'priority': '高'}
            ]
            
            self.task_table.setRowCount(1)
            self.task_table.setItem(0, 0, QTableWidgetItem('更新案内'))
            self.task_table.setItem(0, 1, QTableWidgetItem('サンプルタスク'))
            self.task_table.setItem(0, 2, QTableWidgetItem('2024-12-31'))
            priority_item = QTableWidgetItem('高')
            priority_item.setBackground(QColor("#ffebee"))
            self.task_table.setItem(0, 3, priority_item)
    
    def show_tasks_page(self):
        """タスク管理ページを表示"""
        # メインウィンドウを取得してshow_pageを呼び出す
        main_window = self.window()
        if hasattr(main_window, 'show_page'):
            main_window.show_page("tasks")
    
class ModernMainWindow(QMainWindow):
    """完全刷新されたメインウィンドウ"""
    
    def __init__(self):
        super().__init__()
        self.current_page = "dashboard"
        self.pages = {}
        self.init_database()
        self.setup_ui()
        self.setup_connections()
        
    def init_database(self):
        """データベース初期化"""
        try:
            create_tables()
            print("データベース初期化完了")
        except Exception as e:
            print(f"データベース初期化エラー: {e}")
    
    def setup_ui(self):
        """UIを構築"""
        self.setWindowTitle("賃貸管理システム v2.0 - Modern Edition ✅")
        self.setMinimumSize(1000, 600)  # 最小サイズを小さく調整
        
        # ウィンドウサイズを画面に合わせて調整（全画面対応）
        screen = QGuiApplication.primaryScreen().availableGeometry()
        width = min(1400, int(screen.width() * 0.85))  # 少し小さめに調整
        height = min(900, int(screen.height() * 0.85))  # 少し小さめに調整
        self.resize(width, height)
        
        # 画面中央に配置
        self.move(
            (screen.width() - width) // 2,
            (screen.height() - height) // 2
        )
        
        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # メインレイアウト（QSplitter使用）
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # スプリッターでサイドバーとコンテンツを分離
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)
        
        # サイドバーナビゲーション
        self.sidebar = ModernSidebar()
        self.sidebar.setMinimumWidth(200)
        self.sidebar.setMaximumWidth(300)
        self.splitter.addWidget(self.sidebar)
        
        # メインコンテンツエリア
        self.content_area = QStackedWidget()
        self.content_area.setStyleSheet(f"""
            QStackedWidget {{
                background-color: {ModernUITheme.COLORS['bg_secondary']};
            }}
        """)
        
        self.splitter.addWidget(self.content_area)
        
        # スプリッターの初期サイズ設定
        self.splitter.setSizes([240, 960])
        
        # スプリッターのサイズ保存/復元
        from ui.ui_helpers import save_restore_splitter
        self.save_splitter, self.restore_splitter = save_restore_splitter(
            self.splitter, "main", [240, 960]
        )
        
        # ページを初期化
        self.init_pages()
        
        # 初期ページを表示
        self.show_page("dashboard")
    
    def init_pages(self):
        """各ページを初期化"""
        try:
            # ダッシュボード（アクティビティログ対応）
            self.pages["dashboard"] = DashboardTab()
            self.content_area.addWidget(self.pages["dashboard"])
            
            # タブを順次追加（統合版）
            tabs_config = [
                ("customers", CustomerTab, "顧客管理"),
                ("properties", PropertyUnifiedManagement, "物件・部屋管理"),
                ("contracts", ContractTabImproved, "契約管理"),
                ("tasks", TaskTabBasic, "タスク管理"),
                ("communications", CommunicationTabBasic, "接点履歴"),
                ("calendar", CalendarTab, "カレンダー"),
            ]
            
            for key, tab_class, name in tabs_config:
                try:
                    self.pages[key] = tab_class()
                    self.content_area.addWidget(self.pages[key])
                except Exception as e:
                    print(f"{name}タブ初期化エラー: {e}")
                    # エラー時は代替ページを表示
                    error_page = self.create_error_page(f"{name}の読み込みに失敗しました")
                    self.pages[key] = error_page
                    self.content_area.addWidget(error_page)
                    
        except Exception as e:
            print(f"ページ初期化エラー: {e}")
    
    def create_error_page(self, message):
        """エラーページを作成"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_label = QLabel("⚠️")
        icon_label.setStyleSheet(f"font-size: {ModernUITheme.TYPOGRAPHY['font_size_4xl']};")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        message_label = QLabel(message)
        message_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernUITheme.COLORS['danger']};
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_lg']};
                font-weight: {ModernUITheme.TYPOGRAPHY['font_weight_medium']};
            }}
        """)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(icon_label)
        layout.addWidget(message_label)
        
        return page
    
    def setup_connections(self):
        """シグナル・スロット接続"""
        self.sidebar.nav_clicked.connect(self.show_page)
    
    def show_page(self, page_key):
        """指定されたページを表示"""
        if page_key in self.pages:
            self.content_area.setCurrentWidget(self.pages[page_key])
            self.sidebar.set_active(page_key)
            self.current_page = page_key
            
            # ダッシュボードの場合はデータを更新
            if page_key == "dashboard" and hasattr(self.pages["dashboard"], 'load_dashboard_data'):
                self.pages["dashboard"].load_dashboard_data()
    
    def resizeEvent(self, event):
        """リサイズイベント処理"""
        super().resizeEvent(event)
        
        # 現在のページがカレンダーの場合、リサイズイベントを転送
        if (self.current_page == "calendar" and 
            self.current_page in self.pages and 
            hasattr(self.pages[self.current_page], 'resizeEvent')):
            try:
                self.pages[self.current_page].resizeEvent(event)
            except Exception as e:
                print(f"カレンダーリサイズエラー: {e}")

def main():
    """メイン関数"""
    # Windows文字化け対策
    if os.name == 'nt':
        try:
            os.system('chcp 65001 >nul 2>&1')
            import sys
            import codecs
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'ignore')
        except:
            pass
    
    app = QApplication(sys.argv)
    
    # DPI対応（アプリ起動前に設定）
    from ui.ui_helpers import apply_high_dpi
    apply_high_dpi(app)
    
    # フォント設定
    if os.name == 'nt':
        font = QFont("Yu Gothic UI", 9)
        if not font.exactMatch():
            font = QFont("Segoe UI", 9)
        app.setFont(font)
    
    try:
        print("========================================")
        print("🏢 賃貸管理システム v2.0 - Modern Edition ✅")
        print("========================================")
        print("✨ モダンUIで全面刷新しました")
        print("🚀 起動中...")
        print()
        
        window = ModernMainWindow()
        window.show()
        
        print("[SUCCESS] アプリケーションが正常に起動しました")
        print("💡 左のサイドバーからページを切り替えてください")
        
        sys.exit(app.exec())
        
    except Exception as e:
        error_msg = f"アプリケーション起動エラー: {e}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        
        try:
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Icon.Critical)
            error_dialog.setWindowTitle("起動エラー")
            error_dialog.setText("アプリケーションの起動に失敗しました")
            error_dialog.setDetailedText(str(e))
            error_dialog.exec()
        except:
            pass
        
        input("エラーが発生しました。Enterキーで終了...")

if __name__ == "__main__":
    main()