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

# モダンUIシステム
from modern_ui_system import ModernUITheme, ModernButton, ModernCard, ModernSidebar, ModernInput

# 既存のタブ（順次モダン化）
from customer_tab_improved import CustomerTabImproved
from property_tab_basic import PropertyTabBasic
from contract_tab_improved import ContractTabImproved
from task_tab_basic import TaskTabBasic
from communication_tab_basic import CommunicationTabBasic

# モダンタブ
try:
    from modern_calendar_tab import ModernCalendarTab as CalendarTab
except ImportError:
    from calendar_tab import CalendarTab

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
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
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
        layout.addWidget(title_label)
        
        # 統計カード群（レスポンシブグリッド）
        self.stats_widget = QWidget()
        self.stats_layout = QGridLayout(self.stats_widget)
        self.stats_layout.setSpacing(16)
        
        # 統計カードを作成
        self.stat_cards = [
            self.create_stat_card("👥", "顧客数", "0", ModernUITheme.COLORS['info']),
            self.create_stat_card("🏢", "物件数", "0", ModernUITheme.COLORS['success']),
            self.create_stat_card("📝", "契約数", "0", ModernUITheme.COLORS['warning']),
            self.create_stat_card("📋", "未完了タスク", "0", ModernUITheme.COLORS['danger'])
        ]
        
        # 初期レイアウト設定
        self.update_stats_grid()
        
        layout.addWidget(self.stats_widget)
        
        # クイックアクション
        quick_actions = self.create_quick_actions()
        layout.addWidget(quick_actions)
        
        # 最近のアクティビティ
        recent_activity = self.create_recent_activity()
        layout.addWidget(recent_activity)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def create_stat_card(self, icon, title, value, color):
        """統計カードを作成"""
        card = QFrame()
        card.setObjectName("StatCard")
        card.setFixedHeight(120)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {ModernUITheme.COLORS['bg_primary']};
                border: 1px solid {ModernUITheme.COLORS['border']};
                border-radius: {ModernUITheme.RADIUS['lg']};
                border-left: 4px solid {color};
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        # アイコンとタイトル
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_2xl']};
            }}
        """)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernUITheme.COLORS['text_secondary']};
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_sm']};
                font-weight: {ModernUITheme.TYPOGRAPHY['font_weight_medium']};
            }}
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_layout.addWidget(icon_label)
        header_layout.addStretch()
        header_layout.addWidget(title_label)
        
        # 値
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernUITheme.COLORS['text_primary']};
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_3xl']};
                font-weight: {ModernUITheme.TYPOGRAPHY['font_weight_bold']};
            }}
        """)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addLayout(header_layout)
        layout.addWidget(value_label)
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
    
    def create_quick_actions(self):
        """クイックアクション部分を作成"""
        card = ModernCard("🚀 クイックアクション")
        layout = card.layout()
        
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)
        
        # アクションボタン
        actions = [
            ("新規顧客", "customer", "primary"),
            ("物件登録", "property", "success"),
            ("契約作成", "contract", "warning"),
            ("タスク追加", "task", "info")
        ]
        
        for title, action, btn_type in actions:
            btn = ModernButton(title, btn_type, "base")
            btn.clicked.connect(lambda checked, a=action: self.quick_action(a))
            actions_layout.addWidget(btn)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
        
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
            
            icon_label = QLabel(icon)
            icon_label.setFixedSize(24, 24)
            
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
            tasks = Task.get_pending_tasks() or []
            
            # 統計を更新
            self.customer_value_label.setText(str(len(customers)))
            self.property_value_label.setText(str(len(properties)))
            self.contract_value_label.setText(str(len(contracts)))
            self.task_value_label.setText(str(len(tasks)))
            
        except Exception as e:
            print(f"ダッシュボードデータ読み込みエラー: {e}")
    
    def update_stats_grid(self):
        """ウィンドウ幅に応じてカードを 4/2/1 列に再配置"""
        if not hasattr(self, 'stat_cards'):
            return
            
        # 既存のカードを一旦削除
        for i in reversed(range(self.stats_layout.count())):
            item = self.stats_layout.takeAt(i)
            if item.widget():
                item.widget().setParent(None)
        
        # ウィンドウ幅を取得（親ウィジェットから）
        parent_width = self.parent().width() if self.parent() else 1200
        
        # 列数を決定
        if parent_width >= 1400:
            cols = 4
        elif parent_width >= 900:
            cols = 2
        else:
            cols = 1
        
        # カードを再配置
        for i, card in enumerate(self.stat_cards):
            row = i // cols
            col = i % cols
            self.stats_layout.addWidget(card, row, col)
    
    def quick_action(self, action):
        """クイックアクション処理"""
        # TODO: 各アクションの実装
        print(f"クイックアクション: {action}")

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
        self.setMinimumSize(1200, 800)
        
        # ウィンドウサイズを画面に合わせて調整
        screen = QGuiApplication.primaryScreen().availableGeometry()
        width = min(1600, int(screen.width() * 0.9))
        height = min(1000, int(screen.height() * 0.9))
        self.resize(width, height)
        
        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # メインレイアウト（サイドバー + コンテンツ）
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # サイドバーナビゲーション
        self.sidebar = ModernSidebar()
        main_layout.addWidget(self.sidebar)
        
        # メインコンテンツエリア
        self.content_area = QStackedWidget()
        self.content_area.setStyleSheet(f"""
            QStackedWidget {{
                background-color: {ModernUITheme.COLORS['bg_secondary']};
            }}
        """)
        
        main_layout.addWidget(self.content_area)
        
        # ページを初期化
        self.init_pages()
        
        # 初期ページを表示
        self.show_page("dashboard")
    
    def init_pages(self):\n        \"\"\"各ページを初期化\"\"\"\n        try:\n            # ダッシュボード\n            self.pages[\"dashboard\"] = ModernDashboard()\n            self.content_area.addWidget(self.pages[\"dashboard\"])\n            \n            # タブを順次追加（モダン版を優先使用）\n            tabs_config = [\n                (\"customers\", CustomerTabImproved, \"顧客管理\"),\n                (\"properties\", PropertyTabBasic, \"物件管理\"), \n                (\"contracts\", ContractTabImproved, \"契約管理\"),\n                (\"tasks\", TaskTabBasic, \"タスク管理\"),\n                (\"communications\", CommunicationTabBasic, \"接点履歴\"),\n                (\"calendar\", CalendarTab, \"カレンダー\"),\n            ]\n            \n            for key, tab_class, name in tabs_config:\n                try:\n                    self.pages[key] = tab_class()\n                    self.content_area.addWidget(self.pages[key])\n                except Exception as e:\n                    print(f\"{name}タブ初期化エラー: {e}\")\n                    # エラー時は代替ページを表示\n                    error_page = self.create_error_page(f\"{name}の読み込みに失敗しました\")\n                    self.pages[key] = error_page\n                    self.content_area.addWidget(error_page)\n                    \n        except Exception as e:\n            print(f\"ページ初期化エラー: {e}\")\n    \n    def create_error_page(self, message):\n        \"\"\"エラーページを作成\"\"\"\n        page = QWidget()\n        layout = QVBoxLayout(page)\n        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)\n        \n        icon_label = QLabel(\"⚠️\")\n        icon_label.setStyleSheet(f\"font-size: {ModernUITheme.TYPOGRAPHY['font_size_4xl']};\")\n        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)\n        \n        message_label = QLabel(message)\n        message_label.setStyleSheet(f\"\"\"\n            QLabel {{\n                color: {ModernUITheme.COLORS['danger']};\n                font-size: {ModernUITheme.TYPOGRAPHY['font_size_lg']};\n                font-weight: {ModernUITheme.TYPOGRAPHY['font_weight_medium']};\n            }}\n        \"\"\")\n        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)\n        \n        layout.addWidget(icon_label)\n        layout.addWidget(message_label)\n        \n        return page\n    \n    def setup_connections(self):\n        \"\"\"シグナル・スロット接続\"\"\"\n        self.sidebar.nav_clicked.connect(self.show_page)\n    \n    def show_page(self, page_key):\n        \"\"\"指定されたページを表示\"\"\"\n        if page_key in self.pages:\n            self.content_area.setCurrentWidget(self.pages[page_key])\n            self.sidebar.set_active(page_key)\n            self.current_page = page_key\n            \n            # ダッシュボードの場合はデータを更新\n            if page_key == \"dashboard\" and hasattr(self.pages[\"dashboard\"], 'load_dashboard_data'):\n                self.pages[\"dashboard\"].load_dashboard_data()\n    \n    def resizeEvent(self, event):\n        \"\"\"リサイズイベント処理\"\"\"\n        super().resizeEvent(event)\n        \n        # 現在のページがカレンダーの場合、リサイズイベントを転送\n        if (self.current_page == \"calendar\" and \n            self.current_page in self.pages and \n            hasattr(self.pages[self.current_page], 'resizeEvent')):\n            try:\n                self.pages[self.current_page].resizeEvent(event)\n            except Exception as e:\n                print(f\"カレンダーリサイズエラー: {e}\")\n\ndef main():\n    \"\"\"メイン関数\"\"\"\n    # Windows文字化け対策\n    if os.name == 'nt':\n        try:\n            os.system('chcp 65001 >nul 2>&1')\n            import sys\n            import codecs\n            if hasattr(sys.stdout, 'buffer'):\n                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'ignore')\n        except:\n            pass\n    \n    app = QApplication(sys.argv)\n    \n    # 高DPI対応\n    app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)\n    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)\n    \n    # フォント設定\n    if os.name == 'nt':\n        font = QFont(\"Yu Gothic UI\", 9)\n        if not font.exactMatch():\n            font = QFont(\"Segoe UI\", 9)\n        app.setFont(font)\n    \n    try:\n        print(\"========================================\")\n        print(\"🏢 賃貸管理システム v2.0 - Modern Edition\")\n        print(\"========================================\")\n        print(\"✨ モダンUIで全面刷新しました\")\n        print(\"🚀 起動中...\")\n        print()\n        \n        window = ModernMainWindow()\n        window.show()\n        \n        print(\"[SUCCESS] アプリケーションが正常に起動しました\")\n        print(\"💡 左のサイドバーからページを切り替えてください\")\n        \n        sys.exit(app.exec())\n        \n    except Exception as e:\n        error_msg = f\"アプリケーション起動エラー: {e}\"\n        print(error_msg)\n        import traceback\n        traceback.print_exc()\n        \n        try:\n            error_dialog = QMessageBox()\n            error_dialog.setIcon(QMessageBox.Icon.Critical)\n            error_dialog.setWindowTitle(\"起動エラー\")\n            error_dialog.setText(\"アプリケーションの起動に失敗しました\")\n            error_dialog.setDetailedText(str(e))\n            error_dialog.exec()\n        except:\n            pass\n        \n        input(\"エラーが発生しました。Enterキーで終了...\")\n\nif __name__ == \"__main__\":\n    main()"