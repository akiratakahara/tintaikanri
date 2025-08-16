"""
モダンUIスタイル定義
現代的で視認性の高いUIテーマ
"""

class ModernTheme:
    """モダンUIテーマのカラーパレットと設定"""
    
    # カラーパレット
    COLORS = {
        # プライマリカラー（青系）
        'primary': '#2563eb',           # Blue-600
        'primary_hover': '#1d4ed8',     # Blue-700
        'primary_light': '#3b82f6',     # Blue-500
        'primary_lighter': '#dbeafe',   # Blue-100
        
        # セカンダリカラー（グレー系）
        'secondary': '#64748b',         # Slate-500
        'secondary_light': '#94a3b8',   # Slate-400
        'secondary_lighter': '#f1f5f9', # Slate-100
        
        # 成功・警告・エラー
        'success': '#10b981',           # Emerald-500
        'success_light': '#d1fae5',     # Emerald-100
        'warning': '#f59e0b',           # Amber-500
        'warning_light': '#fef3c7',     # Amber-100
        'danger': '#ef4444',            # Red-500
        'danger_light': '#fee2e2',      # Red-100
        
        # 背景色
        'bg_primary': '#ffffff',        # White
        'bg_secondary': '#f8fafc',      # Slate-50
        'bg_tertiary': '#f1f5f9',       # Slate-100
        
        # テキスト色
        'text_primary': '#0f172a',      # Slate-900
        'text_secondary': '#475569',    # Slate-600
        'text_muted': '#94a3b8',        # Slate-400
        
        # ボーダー色
        'border': '#e2e8f0',            # Slate-200
        'border_light': '#f1f5f9',      # Slate-100
        'border_focus': '#2563eb',      # Blue-600
        
        # シャドウ
        'shadow': 'rgba(0, 0, 0, 0.1)',
        'shadow_hover': 'rgba(0, 0, 0, 0.15)',
    }
    
    # フォント設定
    FONTS = {
        'primary': '"Yu Gothic UI", "Meiryo UI", "MS UI Gothic", "Segoe UI", sans-serif',
        'size_xs': '12px',
        'size_sm': '14px',
        'size_base': '16px',
        'size_lg': '18px',
        'size_xl': '20px',
        'size_2xl': '24px',
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
    }
    
    # 角丸
    RADIUS = {
        'sm': '6px',
        'base': '8px',
        'lg': '12px',
        'xl': '16px',
        'full': '9999px',
    }

class ModernStyles:
    """モダンなスタイルシート定義"""
    
    @staticmethod
    def get_main_window_style():
        """メインウィンドウのスタイル"""
        return f"""
        QMainWindow {{
            background-color: {ModernTheme.COLORS['bg_secondary']};
            font-family: {ModernTheme.FONTS['primary']};
            font-size: {ModernTheme.FONTS['size_base']};
            color: {ModernTheme.COLORS['text_primary']};
        }}
        
        QWidget {{
            font-family: {ModernTheme.FONTS['primary']};
            font-size: {ModernTheme.FONTS['size_base']};
        }}
        """
    
    @staticmethod
    def get_tab_widget_style():
        """タブウィジェットのスタイル"""
        return f"""
        QTabWidget::pane {{
            border: 1px solid {ModernTheme.COLORS['border']};
            background-color: {ModernTheme.COLORS['bg_primary']};
            border-radius: {ModernTheme.RADIUS['base']};
            margin-top: 2px;
            /* 全画面時のスペース最適化 */
            padding: 4px;
        }}
        
        QTabBar::tab {{
            background-color: {ModernTheme.COLORS['bg_tertiary']};
            color: {ModernTheme.COLORS['text_secondary']};
            border: 1px solid {ModernTheme.COLORS['border']};
            border-bottom: none;
            padding: {ModernTheme.SPACING['base']} {ModernTheme.SPACING['lg']};
            margin-right: 2px;
            border-top-left-radius: {ModernTheme.RADIUS['base']};
            border-top-right-radius: {ModernTheme.RADIUS['base']};
            font-weight: 500;
            font-size: {ModernTheme.FONTS['size_sm']};
            min-width: 100px;
            /* 全画面時のタブサイズ調整 */
            max-width: 180px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {ModernTheme.COLORS['bg_primary']};
            color: {ModernTheme.COLORS['primary']};
            border-bottom: 2px solid {ModernTheme.COLORS['primary']};
            font-weight: 600;
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {ModernTheme.COLORS['primary_lighter']};
            color: {ModernTheme.COLORS['primary']};
        }}
        """
    
    @staticmethod
    def get_button_styles():
        """ボタンのスタイル"""
        return f"""
        QPushButton {{
            background-color: {ModernTheme.COLORS['bg_primary']};
            color: {ModernTheme.COLORS['text_primary']};
            border: 1px solid {ModernTheme.COLORS['border']};
            border-radius: {ModernTheme.RADIUS['base']};
            padding: {ModernTheme.SPACING['sm']} {ModernTheme.SPACING['md']};
            font-weight: 500;
            font-size: {ModernTheme.FONTS['size_sm']};
            min-height: 36px;
            min-width: 80px;
        }}
        
        QPushButton:hover {{
            background-color: {ModernTheme.COLORS['bg_tertiary']};
            border-color: {ModernTheme.COLORS['secondary']};
        }}
        
        QPushButton:pressed {{
            background-color: {ModernTheme.COLORS['border']};
        }}
        
        QPushButton:disabled {{
            background-color: {ModernTheme.COLORS['bg_tertiary']};
            color: {ModernTheme.COLORS['text_muted']};
            border-color: {ModernTheme.COLORS['border_light']};
        }}
        
        /* プライマリボタン */
        QPushButton[buttonType="primary"] {{
            background-color: {ModernTheme.COLORS['primary']};
            color: white;
            border: 1px solid {ModernTheme.COLORS['primary']};
            font-weight: 600;
        }}
        
        QPushButton[buttonType="primary"]:hover {{
            background-color: {ModernTheme.COLORS['primary_hover']};
            border-color: {ModernTheme.COLORS['primary_hover']};
        }}
        
        /* 成功ボタン */
        QPushButton[buttonType="success"] {{
            background-color: {ModernTheme.COLORS['success']};
            color: white;
            border: 1px solid {ModernTheme.COLORS['success']};
            font-weight: 600;
        }}
        
        QPushButton[buttonType="success"]:hover {{
            background-color: #059669;
            border-color: #059669;
        }}
        
        /* 危険ボタン */
        QPushButton[buttonType="danger"] {{
            background-color: {ModernTheme.COLORS['danger']};
            color: white;
            border: 1px solid {ModernTheme.COLORS['danger']};
            font-weight: 600;
        }}
        
        QPushButton[buttonType="danger"]:hover {{
            background-color: #dc2626;
            border-color: #dc2626;
        }}
        
        /* 警告ボタン */
        QPushButton[buttonType="warning"] {{
            background-color: {ModernTheme.COLORS['warning']};
            color: white;
            border: 1px solid {ModernTheme.COLORS['warning']};
            font-weight: 600;
        }}
        
        QPushButton[buttonType="warning"]:hover {{
            background-color: #d97706;
            border-color: #d97706;
        }}
        """
    
    @staticmethod
    def get_input_styles():
        """入力フィールドのスタイル"""
        return f"""
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {ModernTheme.COLORS['bg_primary']};
            border: 1px solid {ModernTheme.COLORS['border']};
            border-radius: {ModernTheme.RADIUS['base']};
            padding: {ModernTheme.SPACING['sm']} {ModernTheme.SPACING['base']};
            font-size: {ModernTheme.FONTS['size_base']};
            color: {ModernTheme.COLORS['text_primary']};
            selection-background-color: {ModernTheme.COLORS['primary_lighter']};
            min-height: 36px;
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {ModernTheme.COLORS['border_focus']};
            border-width: 2px;
        }}
        
        QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
            background-color: {ModernTheme.COLORS['bg_tertiary']};
            color: {ModernTheme.COLORS['text_muted']};
            border-color: {ModernTheme.COLORS['border_light']};
        }}
        """
    
    @staticmethod
    def get_combo_box_style():
        """コンボボックスのスタイル"""
        return f"""
        QComboBox {{
            background-color: {ModernTheme.COLORS['bg_primary']};
            border: 1px solid {ModernTheme.COLORS['border']};
            border-radius: {ModernTheme.RADIUS['base']};
            padding: {ModernTheme.SPACING['sm']} {ModernTheme.SPACING['base']};
            padding-right: 32px;
            font-size: {ModernTheme.FONTS['size_base']};
            color: {ModernTheme.COLORS['text_primary']};
            min-height: 36px;
        }}
        
        QComboBox:hover {{
            border-color: {ModernTheme.COLORS['secondary']};
        }}
        
        QComboBox:focus {{
            border-color: {ModernTheme.COLORS['border_focus']};
        }}
        
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 32px;
            border-left: 1px solid {ModernTheme.COLORS['border']};
            border-top-right-radius: {ModernTheme.RADIUS['base']};
            border-bottom-right-radius: {ModernTheme.RADIUS['base']};
            background-color: {ModernTheme.COLORS['bg_tertiary']};
        }}
        
        QComboBox::down-arrow {{
            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik02IDhMMCAwaDEyTDYgOHoiIGZpbGw9IiM2NDc0OGIiLz4KPHN2Zz4K);
            width: 12px;
            height: 8px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {ModernTheme.COLORS['bg_primary']};
            border: 1px solid {ModernTheme.COLORS['border']};
            border-radius: {ModernTheme.RADIUS['base']};
            selection-background-color: {ModernTheme.COLORS['primary_lighter']};
            selection-color: {ModernTheme.COLORS['primary']};
            font-size: {ModernTheme.FONTS['size_base']};
            padding: {ModernTheme.SPACING['xs']};
        }}
        
        QComboBox QAbstractItemView::item {{
            padding: {ModernTheme.SPACING['sm']} {ModernTheme.SPACING['base']};
            border-radius: {ModernTheme.RADIUS['sm']};
            margin: 1px;
        }}
        
        QComboBox QAbstractItemView::item:hover {{
            background-color: {ModernTheme.COLORS['primary_lighter']};
        }}
        """
    
    @staticmethod
    def get_table_style():
        """テーブルのスタイル"""
        return f"""
        QTableWidget {{
            background-color: {ModernTheme.COLORS['bg_primary']};
            alternate-background-color: {ModernTheme.COLORS['bg_secondary']};
            border: 1px solid {ModernTheme.COLORS['border']};
            border-radius: {ModernTheme.RADIUS['base']};
            gridline-color: {ModernTheme.COLORS['border_light']};
            selection-background-color: {ModernTheme.COLORS['primary_lighter']};
            selection-color: {ModernTheme.COLORS['primary']};
            font-size: {ModernTheme.FONTS['size_sm']};
        }}
        
        QTableWidget::item {{
            padding: {ModernTheme.SPACING['sm']} {ModernTheme.SPACING['base']};
            border: none;
        }}
        
        QTableWidget::item:selected {{
            background-color: {ModernTheme.COLORS['primary_lighter']};
            color: {ModernTheme.COLORS['primary']};
        }}
        
        QHeaderView::section {{
            background-color: {ModernTheme.COLORS['bg_tertiary']};
            color: {ModernTheme.COLORS['text_secondary']};
            padding: {ModernTheme.SPACING['sm']} {ModernTheme.SPACING['base']};
            border: none;
            border-right: 1px solid {ModernTheme.COLORS['border']};
            font-weight: 600;
            font-size: {ModernTheme.FONTS['size_sm']};
        }}
        
        QHeaderView::section:first {{
            border-top-left-radius: {ModernTheme.RADIUS['base']};
        }}
        
        QHeaderView::section:last {{
            border-top-right-radius: {ModernTheme.RADIUS['base']};
            border-right: none;
        }}
        """
    
    @staticmethod
    def get_group_box_style():
        """グループボックスのスタイル"""
        return f"""
        QGroupBox {{
            background-color: {ModernTheme.COLORS['bg_primary']};
            border: 1px solid {ModernTheme.COLORS['border']};
            border-radius: {ModernTheme.RADIUS['lg']};
            font-weight: 600;
            font-size: {ModernTheme.FONTS['size_base']};
            color: {ModernTheme.COLORS['text_primary']};
            padding-top: {ModernTheme.SPACING['lg']};
            margin-top: {ModernTheme.SPACING['base']};
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: {ModernTheme.SPACING['md']};
            padding: 0 {ModernTheme.SPACING['sm']};
            background-color: {ModernTheme.COLORS['bg_primary']};
            color: {ModernTheme.COLORS['text_primary']};
        }}
        """
    
    @staticmethod
    def get_list_widget_style():
        """リストウィジェットのスタイル"""
        return f"""
        QListWidget {{
            background-color: {ModernTheme.COLORS['bg_primary']};
            border: 1px solid {ModernTheme.COLORS['border']};
            border-radius: {ModernTheme.RADIUS['base']};
            padding: {ModernTheme.SPACING['xs']};
            font-size: {ModernTheme.FONTS['size_sm']};
        }}
        
        QListWidget::item {{
            background-color: transparent;
            border: none;
            border-radius: {ModernTheme.RADIUS['sm']};
            padding: {ModernTheme.SPACING['sm']} {ModernTheme.SPACING['base']};
            margin: 1px;
        }}
        
        QListWidget::item:hover {{
            background-color: {ModernTheme.COLORS['primary_lighter']};
        }}
        
        QListWidget::item:selected {{
            background-color: {ModernTheme.COLORS['primary']};
            color: white;
        }}
        """
    
    @staticmethod
    def get_scroll_bar_style():
        """スクロールバーのスタイル"""
        return f"""
        QScrollBar:vertical {{
            background-color: {ModernTheme.COLORS['bg_tertiary']};
            width: 12px;
            border-radius: 6px;
            margin: 0;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {ModernTheme.COLORS['secondary_light']};
            border-radius: 6px;
            min-height: 20px;
            margin: 2px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {ModernTheme.COLORS['secondary']};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
            border: none;
        }}
        
        QScrollBar:horizontal {{
            background-color: {ModernTheme.COLORS['bg_tertiary']};
            height: 12px;
            border-radius: 6px;
            margin: 0;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {ModernTheme.COLORS['secondary_light']};
            border-radius: 6px;
            min-width: 20px;
            margin: 2px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {ModernTheme.COLORS['secondary']};
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
            border: none;
        }}
        """
    
    @staticmethod
    def get_all_styles():
        """すべてのスタイルを結合"""
        return '\n'.join([
            ModernStyles.get_main_window_style(),
            ModernStyles.get_tab_widget_style(),
            ModernStyles.get_button_styles(),
            ModernStyles.get_input_styles(),
            ModernStyles.get_combo_box_style(),
            ModernStyles.get_table_style(),
            ModernStyles.get_group_box_style(),
            ModernStyles.get_list_widget_style(),
            ModernStyles.get_scroll_bar_style(),
        ])

class ButtonHelper:
    """ボタンスタイルヘルパー"""
    
    @staticmethod
    def set_primary(button):
        """プライマリボタンスタイルを設定"""
        button.setProperty("buttonType", "primary")
        button.style().unpolish(button)
        button.style().polish(button)
    
    @staticmethod
    def set_success(button):
        """成功ボタンスタイルを設定"""
        button.setProperty("buttonType", "success")
        button.style().unpolish(button)
        button.style().polish(button)
    
    @staticmethod
    def set_danger(button):
        """危険ボタンスタイルを設定"""
        button.setProperty("buttonType", "danger")
        button.style().unpolish(button)
        button.style().polish(button)
    
    @staticmethod
    def set_warning(button):
        """警告ボタンスタイルを設定"""
        button.setProperty("buttonType", "warning")
        button.style().unpolish(button)
        button.style().polish(button)