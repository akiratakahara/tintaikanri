"""
モダンUIデザインシステム v2.0
直感的で使いやすいインターフェースを提供
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

class ModernUITheme:
    """モダンUIテーマ定義"""
    
    # カラーパレット - より洗練された配色
    COLORS = {
        # プライマリ - 深いブルー系
        'primary': '#1e40af',           # Blue-800
        'primary_hover': '#1d4ed8',     # Blue-700  
        'primary_light': '#3b82f6',     # Blue-500
        'primary_lighter': '#dbeafe',   # Blue-100
        'primary_dark': '#1e3a8a',      # Blue-900
        
        # セカンダリ - グレー系
        'secondary': '#64748b',         # Slate-500
        'secondary_light': '#94a3b8',   # Slate-400
        'secondary_lighter': '#f1f5f9', # Slate-100
        'secondary_dark': '#475569',    # Slate-600
        
        # アクセント - エメラルド系
        'accent': '#10b981',            # Emerald-500
        'accent_hover': '#059669',      # Emerald-600
        'accent_light': '#d1fae5',      # Emerald-100
        
        # ステータス色
        'success': '#22c55e',           # Green-500
        'success_light': '#dcfce7',     # Green-100
        'warning': '#f59e0b',           # Amber-500
        'warning_light': '#fef3c7',     # Amber-100
        'danger': '#ef4444',            # Red-500
        'danger_light': '#fee2e2',      # Red-100
        'info': '#06b6d4',              # Cyan-500
        'info_light': '#cffafe',        # Cyan-100
        
        # 背景色
        'bg_primary': '#ffffff',        # White
        'bg_secondary': '#f8fafc',      # Slate-50
        'bg_tertiary': '#f1f5f9',       # Slate-100
        'bg_dark': '#0f172a',           # Slate-900
        
        # テキスト色
        'text_primary': '#0f172a',      # Slate-900
        'text_secondary': '#475569',    # Slate-600
        'text_muted': '#94a3b8',        # Slate-400
        'text_light': '#ffffff',        # White
        
        # ボーダー色
        'border': '#e2e8f0',            # Slate-200
        'border_light': '#f1f5f9',      # Slate-100
        'border_focus': '#3b82f6',      # Blue-500
        'border_hover': '#cbd5e1',      # Slate-300
    }
    
    # タイポグラフィ（全画面対応で小さめに調整）
    TYPOGRAPHY = {
        'font_family': '"Segoe UI", "Yu Gothic UI", "Meiryo UI", "MS UI Gothic", sans-serif',
        'font_size_xs': '10px',
        'font_size_sm': '11px',
        'font_size_base': '12px',
        'font_size_lg': '14px',
        'font_size_xl': '16px',
        'font_size_2xl': '18px',
        'font_size_3xl': '20px',
        'font_size_4xl': '24px',
        
        'font_weight_normal': 400,
        'font_weight_medium': 500,
        'font_weight_semibold': 600,
        'font_weight_bold': 700,
    }
    
    # スペーシング
    SPACING = {
        'xs': '4px',
        'sm': '8px',
        'base': '12px',
        'md': '16px',
        'lg': '20px',
        'xl': '24px',
        '2xl': '32px',
        '3xl': '48px',
        '4xl': '64px',
    }
    
    # 角丸
    RADIUS = {
        'sm': '6px',
        'base': '8px',
        'lg': '12px',
        'xl': '16px',
        'full': '9999px',
    }
    
    # シャドウ
    SHADOWS = {
        'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        'base': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    }

class ModernButton(QPushButton):
    """モダンなボタンコンポーネント"""
    
    def __init__(self, text="", button_type="default", size="base", parent=None):
        super().__init__(text, parent)
        self.button_type = button_type
        self.size = size
        self.setup_style()
        
    def setup_style(self):
        """ボタンスタイルを設定"""
        # サイズ設定
        size_config = {
            'sm': {'height': 32, 'padding': '6px 12px', 'font_size': '13px'},
            'base': {'height': 40, 'padding': '8px 16px', 'font_size': '14px'},
            'lg': {'height': 48, 'padding': '12px 24px', 'font_size': '16px'},
        }
        
        config = size_config.get(self.size, size_config['base'])
        
        # タイプ別スタイル
        if self.button_type == "primary":
            bg_color = ModernUITheme.COLORS['primary']
            hover_color = ModernUITheme.COLORS['primary_hover']
            text_color = ModernUITheme.COLORS['text_light']
        elif self.button_type == "success":
            bg_color = ModernUITheme.COLORS['success']
            hover_color = ModernUITheme.COLORS['accent_hover']
            text_color = ModernUITheme.COLORS['text_light']
        elif self.button_type == "danger":
            bg_color = ModernUITheme.COLORS['danger']
            hover_color = '#dc2626'
            text_color = ModernUITheme.COLORS['text_light']
        elif self.button_type == "outline":
            bg_color = 'transparent'
            hover_color = ModernUITheme.COLORS['bg_tertiary']
            text_color = ModernUITheme.COLORS['primary']
        else:  # default
            bg_color = ModernUITheme.COLORS['bg_primary']
            hover_color = ModernUITheme.COLORS['bg_tertiary']
            text_color = ModernUITheme.COLORS['text_primary']
        
        style = f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {ModernUITheme.COLORS['border']};
                border-radius: {ModernUITheme.RADIUS['base']};
                padding: {config['padding']};
                font-family: {ModernUITheme.TYPOGRAPHY['font_family']};
                font-size: {config['font_size']};
                font-weight: {ModernUITheme.TYPOGRAPHY['font_weight_medium']};
                min-height: {config['height']}px;
                text-align: center;
            }}
            
            QPushButton:hover {{
                background-color: {hover_color};
                border-color: {ModernUITheme.COLORS['border_hover']};
            }}
            
            QPushButton:pressed {{
                background-color: {hover_color};
            }}
            
            QPushButton:disabled {{
                background-color: {ModernUITheme.COLORS['bg_tertiary']};
                color: {ModernUITheme.COLORS['text_muted']};
                border-color: {ModernUITheme.COLORS['border_light']};
            }}
        """
        
        if self.button_type in ["primary", "success", "danger"]:
            style += f"""
                QPushButton {{
                    border-color: {bg_color};
                }}
                QPushButton:hover {{
                    border-color: {hover_color};
                }}
            """
        
        self.setStyleSheet(style)

class ModernCard(QFrame):
    """モダンなカードコンポーネント"""
    
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setup_ui(title)
        
    def setup_ui(self, title):
        """カードUIを設定"""
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {ModernUITheme.COLORS['bg_primary']};
                border: 1px solid {ModernUITheme.COLORS['border']};
                border-radius: {ModernUITheme.RADIUS['lg']};
                padding: {ModernUITheme.SPACING['md']};
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet(f"""
                QLabel {{
                    color: {ModernUITheme.COLORS['text_primary']};
                    font-size: {ModernUITheme.TYPOGRAPHY['font_size_lg']};
                    font-weight: {ModernUITheme.TYPOGRAPHY['font_weight_semibold']};
                    margin-bottom: {ModernUITheme.SPACING['sm']};
                }}
            """)
            layout.addWidget(title_label)
        
        self.setLayout(layout)

class ModernSidebar(QFrame):
    """モダンなサイドバーナビゲーション"""
    
    nav_clicked = pyqtSignal(str)  # ナビゲーションクリックシグナル
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.nav_buttons = {}
        self.setup_ui()
        
    def setup_ui(self):
        """サイドバーUIを設定"""
        self.setMinimumWidth(200)  # 固定幅を最小幅に変更
        self.setObjectName("SidebarFrame")
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {ModernUITheme.COLORS['bg_primary']};
                border-right: 1px solid #E5E7EB;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # ロゴ・タイトル部分
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {ModernUITheme.COLORS['bg_primary']};
                padding: {ModernUITheme.SPACING['xl']};
                border-bottom: 1px solid #E5E7EB;
            }}
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 16)
        
        logo_label = QLabel("🏢 賃貸管理")
        logo_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernUITheme.COLORS['text_primary']};
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_xl']};
                font-weight: {ModernUITheme.TYPOGRAPHY['font_weight_bold']};
            }}
        """)
        
        version_label = QLabel("v2.0 Modern")
        version_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernUITheme.COLORS['text_secondary']};
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_sm']};
                margin-top: {ModernUITheme.SPACING['xs']};
            }}
        """)
        
        header_layout.addWidget(logo_label)
        header_layout.addWidget(version_label)
        
        # ナビゲーションメニュー
        nav_frame = QFrame()
        nav_frame.setStyleSheet("QFrame { background-color: transparent; }")
        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setContentsMargins(12, 16, 12, 16)
        nav_layout.setSpacing(4)
        
        # ナビゲーション項目
        nav_items = [
            ("📊", "ダッシュボード", "dashboard"),
            ("👥", "顧客管理", "customers"),
            ("🏢", "物件・部屋管理", "properties"),
            ("📝", "契約管理", "contracts"),
            ("📋", "タスク管理", "tasks"),
            ("📞", "接点履歴", "communications"),
            ("📅", "カレンダー", "calendar"),
        ]
        
        for icon, title, key in nav_items:
            btn = self.create_nav_button(icon, title, key)
            nav_layout.addWidget(btn)
            self.nav_buttons[key] = btn
        
        nav_layout.addStretch()
        
        layout.addWidget(header)
        layout.addWidget(nav_frame)
        
        self.setLayout(layout)
    
    def create_nav_button(self, icon, title, key):
        """ナビゲーションボタンを作成"""
        btn = QPushButton(f"{icon}  {title}")
        btn.setObjectName(key)
        btn.clicked.connect(lambda: self.nav_clicked.emit(key))
        
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {ModernUITheme.COLORS['text_primary']};
                border: none;
                border-radius: {ModernUITheme.RADIUS['base']};
                padding: 12px 16px;
                text-align: left;
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_base']};
                font-weight: {ModernUITheme.TYPOGRAPHY['font_weight_medium']};
                min-height: 44px;
            }}
            
            QPushButton:hover {{
                background-color: {ModernUITheme.COLORS['bg_secondary']};
                color: {ModernUITheme.COLORS['primary']};
            }}
            
            QPushButton:pressed {{
                background-color: {ModernUITheme.COLORS['bg_tertiary']};
            }}
            
            QPushButton[selected="true"] {{
                background-color: {ModernUITheme.COLORS['primary']};
                color: {ModernUITheme.COLORS['text_light']};
            }}
        """)
        
        return btn
    
    def set_active(self, key):
        """アクティブなナビゲーション項目を設定"""
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.setProperty("selected", "true")
            else:
                btn.setProperty("selected", "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

class ModernInput(QLineEdit):
    """モダンな入力フィールド"""
    
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        if placeholder:
            self.setPlaceholderText(placeholder)
        self.setup_style()
    
    def setup_style(self):
        """入力フィールドスタイルを設定"""
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {ModernUITheme.COLORS['bg_primary']};
                border: 2px solid {ModernUITheme.COLORS['border']};
                border-radius: {ModernUITheme.RADIUS['base']};
                padding: 12px 16px;
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_base']};
                color: {ModernUITheme.COLORS['text_primary']};
                selection-background-color: {ModernUITheme.COLORS['primary_lighter']};
                min-height: 16px;
            }}
            
            QLineEdit:focus {{
                border-color: {ModernUITheme.COLORS['border_focus']};
                background-color: {ModernUITheme.COLORS['bg_primary']};
            }}
            
            QLineEdit:disabled {{
                background-color: {ModernUITheme.COLORS['bg_tertiary']};
                color: {ModernUITheme.COLORS['text_muted']};
                border-color: {ModernUITheme.COLORS['border_light']};
            }}
        """)