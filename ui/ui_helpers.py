"""
UIレイアウト最適化ヘルパー関数
単一スクロール、レスポンシブレイアウト、一貫したデザインを提供
"""

# Qt imports (compat)
try:
    from PyQt6.QtWidgets import *
    from PyQt6.QtCore import *
    from PyQt6.QtGui import *
except ImportError:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *

from modern_ui_system import ModernUITheme

def make_scroll_page(widget):
    """
    単一スクロールページを作成
    
    Args:
        widget: スクロールするウィジェット
        
    Returns:
        QScrollArea: スクロール可能なエリア
    """
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setWidget(widget)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    
    # スクロールバーのスタイル
    scroll.setStyleSheet(f"""
        QScrollArea {{
            border: none;
            background-color: {ModernUITheme.COLORS['bg_secondary']};
        }}
        
        QScrollBar:vertical {{
            background-color: {ModernUITheme.COLORS['bg_tertiary']};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {ModernUITheme.COLORS['border_hover']};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {ModernUITheme.COLORS['secondary']};
        }}
        
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
    """)
    
    return scroll

def make_page_container():
    """
    ページコンテナを作成（標準的な余白とスペーシング）
    
    Returns:
        tuple: (container_widget, layout)
    """
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(16, 8, 16, 16)  # 上部の余白を16から8に削減
    layout.setSpacing(12)                      # スペーシングを16から12に削減
    
    return container, layout

def make_collapsible(title, content, default_expanded=False):
    """
    折りたたみ可能なセクションを作成
    
    Args:
        title: セクションタイトル
        content: 折りたたみ内容
        default_expanded: デフォルトで展開するか
        
    Returns:
        QWidget: 折りたたみ可能なセクション
    """
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    
    # ヘッダー（クリック可能）
    header = QPushButton()
    header.setCheckable(True)
    header.setChecked(default_expanded)
    header.setMinimumHeight(44)
    header.setStyleSheet(f"""
        QPushButton {{
            background-color: {ModernUITheme.COLORS['bg_primary']};
            border: 1px solid {ModernUITheme.COLORS['border']};
            border-radius: {ModernUITheme.RADIUS['base']};
            padding: 0px;
            text-align: left;
        }}
        
        QPushButton:hover {{
            background-color: {ModernUITheme.COLORS['bg_secondary']};
        }}
        
        QPushButton:checked {{
            background-color: {ModernUITheme.COLORS['primary_lighter']};
            border-color: {ModernUITheme.COLORS['primary']};
        }}
    """)
    
    # ヘッダー内容（アイコン + タイトル）
    header_widget = QWidget()
    header_layout = QHBoxLayout(header_widget)
    header_layout.setContentsMargins(16, 12, 16, 12)
    header_layout.setSpacing(8)
    
    # アイコン（展開/折りたたみ）
    icon_label = QLabel("▼" if default_expanded else "▶")
    icon_label.setStyleSheet(f"""
        QLabel {{
            color: {ModernUITheme.COLORS['text_secondary']};
            font-size: {ModernUITheme.TYPOGRAPHY['font_size_base']};
        }}
    """)
    
    # タイトルラベル
    title_label = QLabel(title)
    title_label.setStyleSheet(f"""
        QLabel {{
            color: {ModernUITheme.COLORS['text_primary']};
            font-size: {ModernUITheme.TYPOGRAPHY['font_size_lg']};
            font-weight: {ModernUITheme.TYPOGRAPHY['font_weight_semibold']};
        }}
    """)
    
    header_layout.addWidget(icon_label)
    header_layout.addWidget(title_label)
    header_layout.addStretch()
    
    # ボタンのレイアウトを設定
    button_layout = QVBoxLayout(header)
    button_layout.setContentsMargins(0, 0, 0, 0)
    button_layout.addWidget(header_widget)
    
    # コンテンツエリア
    content_widget = QWidget()
    content_widget.setVisible(default_expanded)
    content_widget.setStyleSheet(f"""
        QWidget {{
            background-color: {ModernUITheme.COLORS['bg_primary']};
            border: 1px solid {ModernUITheme.COLORS['border']};
            border-top: none;
            border-radius: 0 0 {ModernUITheme.RADIUS['base']} {ModernUITheme.RADIUS['base']};
            padding: 16px;
        }}
    """)
    
    content_layout = QVBoxLayout(content_widget)
    content_layout.setContentsMargins(16, 16, 16, 16)
    content_layout.setSpacing(12)
    
    if isinstance(content, QWidget):
        content_layout.addWidget(content)
    elif isinstance(content, QLayout):
        content_layout.addLayout(content)
    
    # クリックイベント
    def toggle_content(checked):
        content_widget.setVisible(checked)
        icon_label.setText("▼" if checked else "▶")
    
    header.clicked.connect(toggle_content)
    
    layout.addWidget(header)
    layout.addWidget(content_widget)
    
    return container

def attach_density_switch(table, parent_layout):
    """
    テーブルの行高密度切り替えスイッチを追加
    
    Args:
        table: QTableView または QTableWidget
        parent_layout: 親レイアウト
    """
    density_widget = QWidget()
    density_layout = QHBoxLayout(density_widget)
    density_layout.setContentsMargins(0, 0, 0, 0)
    density_layout.setSpacing(8)
    
    # 密度切り替えボタン
    compact_btn = QPushButton("コンパクト")
    compact_btn.setCheckable(True)
    compact_btn.setChecked(False)
    
    normal_btn = QPushButton("標準")
    normal_btn.setCheckable(True)
    normal_btn.setChecked(True)
    
    # ボタングループ
    button_group = QButtonGroup()
    button_group.addButton(compact_btn)
    button_group.addButton(normal_btn)
    button_group.setExclusive(True)
    
    # スタイル
    for btn in [compact_btn, normal_btn]:
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernUITheme.COLORS['bg_primary']};
                border: 1px solid {ModernUITheme.COLORS['border']};
                border-radius: {ModernUITheme.RADIUS['sm']};
                padding: 6px 12px;
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_sm']};
                min-height: 28px;
            }}
            
            QPushButton:checked {{
                background-color: {ModernUITheme.COLORS['primary']};
                color: {ModernUITheme.COLORS['text_light']};
                border-color: {ModernUITheme.COLORS['primary']};
            }}
            
            QPushButton:hover:!checked {{
                background-color: {ModernUITheme.COLORS['bg_secondary']};
            }}
        """)
    
    # イベント
    def set_compact_density():
        table.verticalHeader().setDefaultSectionSize(28)
        table.setStyleSheet(f"""
            QTableView {{
                gridline-color: {ModernUITheme.COLORS['border']};
            }}
        """)
    
    def set_normal_density():
        table.verticalHeader().setDefaultSectionSize(40)
        table.setStyleSheet(f"""
            QTableView {{
                gridline-color: {ModernUITheme.COLORS['border']};
            }}
        """)
    
    compact_btn.clicked.connect(set_compact_density)
    normal_btn.clicked.connect(set_normal_density)
    
    density_layout.addWidget(compact_btn)
    density_layout.addWidget(normal_btn)
    density_layout.addStretch()
    
    # 親レイアウトに追加
    parent_layout.addWidget(density_widget)

def save_restore_splitter(splitter, settings_key, default_sizes=None):
    """
    スプリッターのサイズを保存/復元
    
    Args:
        splitter: QSplitter
        settings_key: 設定キー
        default_sizes: デフォルトサイズ
    """
    settings = QSettings()
    
    def save_splitter():
        settings.setValue(f"splitter/{settings_key}", splitter.sizes())
    
    def restore_splitter():
        sizes = settings.value(f"splitter/{settings_key}")
        if sizes:
            splitter.setSizes([int(x) for x in sizes])
        elif default_sizes:
            splitter.setSizes(default_sizes)
    
    # サイズ変更時に自動保存
    splitter.splitterMoved.connect(save_splitter)
    
    # 初期復元
    restore_splitter()
    
    return save_splitter, restore_splitter

def make_form_field(label_text, widget, required=False, error_text=""):
    """
    フォームフィールドを作成（ラベル、入力、エラー表示）
    
    Args:
        label_text: ラベルテキスト
        widget: 入力ウィジェット
        required: 必須フィールドか
        error_text: エラーテキスト
        
    Returns:
        QWidget: フォームフィールドコンテナ
    """
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    
    # ラベル
    label = QLabel(f"{label_text}{' *' if required else ''}")
    label.setStyleSheet(f"""
        QLabel {{
            color: {ModernUITheme.COLORS['text_primary']};
            font-size: {ModernUITheme.TYPOGRAPHY['font_size_base']};
            font-weight: {ModernUITheme.TYPOGRAPHY['font_weight_medium']};
        }}
    """)
    
    # エラーテキスト
    error_label = QLabel(error_text)
    error_label.setVisible(bool(error_text))
    error_label.setStyleSheet(f"""
        QLabel {{
            color: {ModernUITheme.COLORS['danger']};
            font-size: {ModernUITheme.TYPOGRAPHY['font_size_sm']};
        }}
    """)
    
    # 入力ウィジェットの最小高さ設定
    if hasattr(widget, 'setMinimumHeight'):
        widget.setMinimumHeight(40)
    
    layout.addWidget(label)
    layout.addWidget(widget)
    layout.addWidget(error_label)
    
    return container

def make_action_buttons(actions, parent_layout):
    """
    アクションボタン群を作成
    
    Args:
        actions: [("テキスト", "タイプ", "アクション"), ...]
        parent_layout: 親レイアウト
    """
    button_widget = QWidget()
    button_layout = QHBoxLayout(button_widget)
    button_layout.setContentsMargins(0, 0, 0, 0)
    button_layout.setSpacing(8)
    
    # 左側（戻る/キャンセル系）
    left_buttons = []
    for text, btn_type, action in actions:
        if btn_type in ["secondary", "outline", "danger"]:
            left_buttons.append((text, btn_type, action))
    
    # 右側（保存/OK系）
    right_buttons = []
    for text, btn_type, action in actions:
        if btn_type in ["primary", "success"]:
            right_buttons.append((text, btn_type, action))
    
    # 左側ボタン
    for text, btn_type, action in left_buttons:
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernUITheme.COLORS['bg_primary']};
                border: 1px solid {ModernUITheme.COLORS['border']};
                border-radius: {ModernUITheme.RADIUS['base']};
                padding: 8px 16px;
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_base']};
                min-height: 40px;
            }}
            
            QPushButton:hover {{
                background-color: {ModernUITheme.COLORS['bg_secondary']};
            }}
        """)
        button_layout.addWidget(btn)
    
    button_layout.addStretch()
    
    # 右側ボタン
    for text, btn_type, action in right_buttons:
        if btn_type == "primary":
            bg_color = ModernUITheme.COLORS['primary']
            text_color = ModernUITheme.COLORS['text_light']
        elif btn_type == "success":
            bg_color = ModernUITheme.COLORS['success']
            text_color = ModernUITheme.COLORS['text_light']
        else:
            bg_color = ModernUITheme.COLORS['bg_primary']
            text_color = ModernUITheme.COLORS['text_primary']
        
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid {bg_color};
                border-radius: {ModernUITheme.RADIUS['base']};
                padding: 8px 16px;
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_base']};
                min-height: 40px;
            }}
            
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """)
        button_layout.addWidget(btn)
    
    parent_layout.addWidget(button_widget)
    return button_widget


def stretch_table(table):
    """
    テーブルを残りスペース全体に拡張
    
    Args:
        table: QTableWidget or QTableView
    """
    # サイズポリシー設定
    table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    
    # 水平ヘッダーをストレッチ
    if hasattr(table, 'horizontalHeader'):
        header = table.horizontalHeader()
        # PyQt6/PyQt5 互換
        try:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        except AttributeError:
            header.setSectionResizeMode(QHeaderView.Stretch)
    
    # 垂直ヘッダーの行高さ設定
    if hasattr(table, 'verticalHeader'):
        table.verticalHeader().setDefaultSectionSize(40)
        table.verticalHeader().setMinimumSectionSize(40)


def set_form_min_heights(root, h=40):
    """
    フォーム要素の最小高さを統一設定
    
    Args:
        root: ルートウィジェット
        h: 最小高さ（デフォルト40px）
    """
    # 対象ウィジェットタイプ
    widget_types = (QLineEdit, QComboBox, QDateEdit, QTimeEdit, 
                    QSpinBox, QDoubleSpinBox, QPushButton)
    
    # 再帰的に全子要素を探索
    for widget in root.findChildren(QWidget):
        if isinstance(widget, widget_types):
            widget.setMinimumHeight(h)
        elif isinstance(widget, QTextEdit):
            widget.setMinimumHeight(h * 2)  # テキストエリアは倍の高さ


def apply_high_dpi(app):
    """
    高DPI対応を有効化
    
    Args:
        app: QApplication
    """
    # PyQt6では自動的に有効だが、念のため設定
    try:
        # Qt6
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        try:
            # Qt5
            app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
            app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        except:
            pass  # 既に有効または未対応


