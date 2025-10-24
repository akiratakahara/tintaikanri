
"""
モダンカレンダータブ - 完全刷新版
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QGridLayout, QScrollArea, QFrame, QComboBox)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime, timedelta
import calendar

from modern_ui_system import ModernUITheme, ModernCard, ModernButton

class ModernCalendarWidget(QWidget):
    """モダンなカレンダーウィジェット"""
    
    date_clicked = pyqtSignal(QDate)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_date = QDate.currentDate()
        self.selected_date = QDate.currentDate()
        self.events = {}
        self.setup_ui()
    
    def setup_ui(self):
        """UIを構築"""
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # ヘッダー（月移動ボタン）
        header_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("◀")
        self.prev_btn.clicked.connect(self.prev_month)
        self.prev_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernUITheme.COLORS['bg_primary']};
                border: 1px solid {ModernUITheme.COLORS['border']};
                border-radius: {ModernUITheme.RADIUS['base']};
                padding: 8px 12px;
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_lg']};
            }}
            QPushButton:hover {{
                background-color: {ModernUITheme.COLORS['primary_lighter']};
            }}
        """)
        
        self.month_label = QLabel()
        self.month_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernUITheme.COLORS['text_primary']};
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_xl']};
                font-weight: {ModernUITheme.TYPOGRAPHY['font_weight_bold']};
            }}
        """)
        
        self.next_btn = QPushButton("▶")
        self.next_btn.clicked.connect(self.next_month)
        self.next_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernUITheme.COLORS['bg_primary']};
                border: 1px solid {ModernUITheme.COLORS['border']};
                border-radius: {ModernUITheme.RADIUS['base']};
                padding: 8px 12px;
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_lg']};
            }}
            QPushButton:hover {{
                background-color: {ModernUITheme.COLORS['primary_lighter']};
            }}
        """)
        
        self.today_btn = QPushButton("今日")
        self.today_btn.clicked.connect(self.go_to_today)
        self.today_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernUITheme.COLORS['primary']};
                color: {ModernUITheme.COLORS['text_light']};
                border: none;
                border-radius: {ModernUITheme.RADIUS['base']};
                padding: 8px 16px;
                font-weight: {ModernUITheme.TYPOGRAPHY['font_weight_semibold']};
            }}
            QPushButton:hover {{
                background-color: {ModernUITheme.COLORS['primary_darker']};
            }}
        """)
        
        header_layout.addWidget(self.prev_btn)
        header_layout.addWidget(self.month_label)
        header_layout.addWidget(self.next_btn)
        header_layout.addStretch()
        header_layout.addWidget(self.today_btn)
        
        # 曜日ヘッダー
        weekday_layout = QHBoxLayout()
        weekdays = ['月', '火', '水', '木', '金', '土', '日']
        for day in weekdays:
            label = QLabel(day)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(f"""
                QLabel {{
                    color: {ModernUITheme.COLORS['text_secondary']};
                    font-weight: {ModernUITheme.TYPOGRAPHY['font_weight_semibold']};
                    padding: 8px;
                    border-right: 1px solid {ModernUITheme.COLORS['border']};
                }}
            """)
            weekday_layout.addWidget(label)
        
        # カレンダーグリッド
        self.calendar_grid = QGridLayout()
        self.calendar_grid.setSpacing(1)
        self.day_buttons = {}
        
        # 6週間分のボタンを作成
        for week in range(6):
            for day in range(7):
                btn = self.create_day_button()
                self.calendar_grid.addWidget(btn, week, day)
                self.day_buttons[(week, day)] = btn
        
        calendar_widget = QWidget()
        calendar_widget.setLayout(self.calendar_grid)
        calendar_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {ModernUITheme.COLORS['bg_primary']};
                border: 1px solid {ModernUITheme.COLORS['border']};
                border-radius: {ModernUITheme.RADIUS['base']};
            }}
        """)
        
        layout.addLayout(header_layout)
        layout.addLayout(weekday_layout)
        layout.addWidget(calendar_widget)
        
        self.setLayout(layout)
        self.update_calendar()
    
    def create_day_button(self):
        """日付ボタンを作成"""
        btn = QPushButton()
        btn.setFixedSize(60, 50)
        btn.clicked.connect(lambda: self.day_clicked(btn))
        
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernUITheme.COLORS['bg_primary']};
                color: {ModernUITheme.COLORS['text_primary']};
                border: 1px solid {ModernUITheme.COLORS['border']};
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_base']};
                font-weight: {ModernUITheme.TYPOGRAPHY['font_weight_medium']};
            }}
            
            QPushButton:hover {{
                background-color: {ModernUITheme.COLORS['primary_lighter']};
                border-color: {ModernUITheme.COLORS['primary']};
            }}
            
            QPushButton[isToday="true"] {{
                background-color: {ModernUITheme.COLORS['primary']};
                color: {ModernUITheme.COLORS['text_light']};
                font-weight: {ModernUITheme.TYPOGRAPHY['font_weight_bold']};
            }}
            
            QPushButton[isSelected="true"] {{
                background-color: {ModernUITheme.COLORS['accent']};
                color: {ModernUITheme.COLORS['text_light']};
                border-color: {ModernUITheme.COLORS['accent']};
            }}
            
            QPushButton[hasEvents="true"] {{
                border-left: 4px solid {ModernUITheme.COLORS['warning']};
            }}
            
            QPushButton[otherMonth="true"] {{
                color: {ModernUITheme.COLORS['text_muted']};
                background-color: {ModernUITheme.COLORS['bg_tertiary']};
            }}
        """)
        
        return btn
    
    def update_calendar(self):
        """カレンダー表示を更新"""
        # 月ラベル更新
        self.month_label.setText(f"{self.current_date.year()}年 {self.current_date.month():02d}月")
        
        # 月の最初の日と最後の日を取得
        first_day = QDate(self.current_date.year(), self.current_date.month(), 1)
        last_day = QDate(self.current_date.year(), self.current_date.month(), 
                        calendar.monthrange(self.current_date.year(), self.current_date.month())[1])
        
        # 月曜日から始まる週の最初の日を計算
        start_date = first_day.addDays(-(first_day.dayOfWeek() - 1))
        
        # カレンダーグリッドを更新
        current_date = start_date
        today = QDate.currentDate()
        
        for week in range(6):
            for day in range(7):
                btn = self.day_buttons[(week, day)]
                btn.setText(str(current_date.day()))
                
                # 日付をボタンに保存
                btn.date = current_date
                
                # 属性をリセット
                btn.setProperty("isToday", "false")
                btn.setProperty("isSelected", "false")
                btn.setProperty("hasEvents", "false")
                btn.setProperty("otherMonth", "false")
                
                # 今日の日付かチェック
                if current_date == today:
                    btn.setProperty("isToday", "true")
                
                # 選択日かチェック
                if current_date == self.selected_date:
                    btn.setProperty("isSelected", "true")
                
                # 当月以外かチェック
                if current_date.month() != self.current_date.month():
                    btn.setProperty("otherMonth", "true")
                
                # イベントがあるかチェック
                if current_date.toString("yyyy-MM-dd") in self.events:
                    btn.setProperty("hasEvents", "true")
                
                # スタイルを再適用
                btn.style().unpolish(btn)
                btn.style().polish(btn)
                
                current_date = current_date.addDays(1)
    
    def day_clicked(self, btn):
        """日付クリック処理"""
        self.selected_date = btn.date
        self.date_clicked.emit(self.selected_date)
        self.update_calendar()
    
    def prev_month(self):
        """前月に移動"""
        self.current_date = self.current_date.addMonths(-1)
        self.update_calendar()
    
    def next_month(self):
        """次月に移動"""
        self.current_date = self.current_date.addMonths(1)
        self.update_calendar()
    
    def go_to_today(self):
        """今日に移動"""
        today = QDate.currentDate()
        self.current_date = today
        self.selected_date = today
        self.update_calendar()
        self.date_clicked.emit(self.selected_date)
    
    def set_events(self, events_dict):
        """イベント辞書を設定"""
        self.events = events_dict
        self.update_calendar()

class ModernEventList(QWidget):
    """モダンなイベントリスト"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """イベントリストUIを構築"""
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # ヘッダー
        header_layout = QHBoxLayout()
        
        self.date_label = QLabel("選択日のスケジュール")
        self.date_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernUITheme.COLORS['text_primary']};
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_lg']};
                font-weight: {ModernUITheme.TYPOGRAPHY['font_weight_semibold']};
            }}
        """)
        
        self.add_event_btn = ModernButton("+ 追加", "primary", "sm")
        
        header_layout.addWidget(self.date_label)
        header_layout.addStretch()
        header_layout.addWidget(self.add_event_btn)
        
        # フィルター
        filter_layout = QHBoxLayout()
        
        filter_label = QLabel("表示:")
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全て", "タスク", "契約更新", "その他"])
        self.filter_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {ModernUITheme.COLORS['bg_primary']};
                border: 1px solid {ModernUITheme.COLORS['border']};
                border-radius: {ModernUITheme.RADIUS['base']};
                padding: 6px 12px;
                min-width: 100px;
            }}
        """)
        
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addStretch()
        
        # イベントリスト
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarNever)
        
        self.event_list_widget = QWidget()
        self.event_list_layout = QVBoxLayout(self.event_list_widget)
        self.event_list_layout.setSpacing(8)
        
        self.scroll_area.setWidget(self.event_list_widget)
        
        layout.addLayout(header_layout)
        layout.addLayout(filter_layout)
        layout.addWidget(self.scroll_area)
        
        self.setLayout(layout)
    
    def update_events(self, date, events):
        """指定日のイベントを更新表示"""
        # 既存のイベントをクリア
        for i in reversed(range(self.event_list_layout.count())):
            child = self.event_list_layout.takeAt(i)
            if child.widget():
                child.widget().deleteLater()
        
        # 日付ラベル更新
        try:
            py_date = date.toPyDate()
            weekdays = ['月', '火', '水', '木', '金', '土', '日']
            weekday = weekdays[py_date.weekday()]
            date_str = f"{py_date.year}年{py_date.month:02d}月{py_date.day:02d}日 ({weekday})"
        except:
            date_str = date.toString("yyyy年MM月dd日")
        
        self.date_label.setText(f"📅 {date_str}")
        
        # イベントが存在する場合
        if events:
            for event in events:
                event_card = self.create_event_card(event)
                self.event_list_layout.addWidget(event_card)
        else:
            # イベントがない場合
            empty_label = QLabel("📝 この日にはスケジュールがありません")
            empty_label.setStyleSheet(f"""
                QLabel {{
                    color: {ModernUITheme.COLORS['text_muted']};
                    font-size: {ModernUITheme.TYPOGRAPHY['font_size_base']};
                    padding: 40px;
                    text-align: center;
                }}
            """)
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.event_list_layout.addWidget(empty_label)
        
        self.event_list_layout.addStretch()
    
    def create_event_card(self, event):
        """イベントカードを作成"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {ModernUITheme.COLORS['bg_primary']};
                border: 1px solid {ModernUITheme.COLORS['border']};
                border-radius: {ModernUITheme.RADIUS['base']};
                border-left: 4px solid {self.get_event_color(event)};
                padding: 12px;
                margin: 4px 0;
            }}
            QFrame:hover {{
                border-color: {ModernUITheme.COLORS['border_hover']};
                background-color: {ModernUITheme.COLORS['bg_secondary']};
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)
        
        # タイトル行
        title_layout = QHBoxLayout()
        
        icon_label = QLabel(self.get_event_icon(event))
        title_label = QLabel(event.get('title', '無題'))
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernUITheme.COLORS['text_primary']};
                font-weight: {ModernUITheme.TYPOGRAPHY['font_weight_semibold']};
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_base']};
            }}
        """)
        
        priority_label = QLabel(event.get('priority', ''))
        priority_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernUITheme.COLORS['text_muted']};
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_sm']};
            }}
        """)
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(priority_label)
        
        # 詳細情報
        if event.get('description'):
            desc_label = QLabel(event['description'][:100] + "..." if len(event['description']) > 100 else event['description'])
            desc_label.setStyleSheet(f"""
                QLabel {{
                    color: {ModernUITheme.COLORS['text_secondary']};
                    font-size: {ModernUITheme.TYPOGRAPHY['font_size_sm']};
                }}
            """)
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)
        
        layout.addLayout(title_layout)
        
        return card
    
    def get_event_color(self, event):
        """イベントタイプに応じた色を取得"""
        event_type = event.get('type', '')
        if event_type == 'task':
            return ModernUITheme.COLORS['danger']
        elif event_type in ['renewal', 'renewal_notification']:
            return ModernUITheme.COLORS['info']
        elif event_type == 'procedure':
            return event.get('color', ModernUITheme.COLORS['warning'])
        else:
            return ModernUITheme.COLORS['accent']
    
    def get_event_icon(self, event):
        """イベントタイプに応じたアイコンを取得"""
        event_type = event.get('type', '')
        if event_type == 'task':
            return '📋'
        elif event_type in ['renewal', 'renewal_notification']:
            return '🔄'
        elif event_type == 'procedure':
            return '📝'
        else:
            return '📌'

class ModernCalendarTab(QWidget):
    """完全刷新されたカレンダータブ"""
    
    def __init__(self):
        super().__init__()
        self.tasks = []
        self.renewals = []
        self.procedure_logs = []
        self.setup_ui()
        self.load_schedule_data()
        self.update_events()
        
    def setup_ui(self):
        """UIを構築"""
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # ページタイトル
        title_label = QLabel("📅 カレンダー")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernUITheme.COLORS['text_primary']};
                font-size: {ModernUITheme.TYPOGRAPHY['font_size_3xl']};
                font-weight: {ModernUITheme.TYPOGRAPHY['font_weight_bold']};
                margin-bottom: {ModernUITheme.SPACING['lg']};
            }}
        """)
        
        # メインコンテンツ
        content_layout = QHBoxLayout()
        content_layout.setSpacing(24)
        
        # 左側：カレンダー
        calendar_card = ModernCard()
        calendar_layout = calendar_card.layout()
        
        self.calendar_widget = ModernCalendarWidget()
        self.calendar_widget.date_clicked.connect(self.on_date_selected)
        calendar_layout.addWidget(self.calendar_widget)
        
        # 右側：イベントリスト
        self.event_list = ModernEventList()
        
        # 比率設定
        content_layout.addWidget(calendar_card, 2)  # カレンダー側を大きく
        content_layout.addWidget(self.event_list, 1)  # イベントリスト側
        
        layout.addWidget(title_label)
        layout.addLayout(content_layout)
        
        self.setLayout(layout)
        
        # 初期選択日を設定
        self.on_date_selected(QDate.currentDate())
    
    def load_schedule_data(self):
        """スケジュールデータを読み込み"""
        self.load_tasks()
        self.load_renewals()
        self.load_procedure_logs()
    
    def load_tasks(self):
        """タスクを読み込み"""
        try:
            from models import Task
            db_tasks = Task.get_pending_tasks() or []
            
            self.tasks = []
            for task in db_tasks:
                if task.get('due_date'):
                    self.tasks.append({
                        'id': task.get('id'),
                        'type': 'task',
                        'title': task.get('title', ''),
                        'description': task.get('description', ''),
                        'due_date': task.get('due_date'),
                        'priority': task.get('priority', '中'),
                        'task_type': task.get('task_type', ''),
                        'assigned_to': task.get('assigned_to', ''),
                        'status': task.get('status', '未完了')
                    })
        except Exception as e:
            print(f"タスク読み込みエラー: {e}")
            # ダミーデータを追加（テスト用）
            from PyQt6.QtCore import QDate
            current_date = QDate.currentDate()
            self.tasks = [
                {
                    'id': 1,
                    'type': 'task',
                    'title': 'サンプル更新案内タスク',
                    'description': '契約更新の案内を送付',
                    'due_date': current_date.addDays(3).toString("yyyy-MM-dd"),
                    'priority': '高',
                    'task_type': '更新案内',
                    'assigned_to': '担当者A',
                    'status': '未完了'
                },
                {
                    'id': 2,
                    'type': 'task',
                    'title': '修繕対応',
                    'description': 'エアコン修理手配',
                    'due_date': current_date.addDays(7).toString("yyyy-MM-dd"),
                    'priority': '中',
                    'task_type': '修繕',
                    'assigned_to': '担当者B',
                    'status': '未完了'
                }
            ]
            print("ダミータスクデータを使用")
    
    def load_renewals(self):
        """契約更新を読み込み"""
        try:
            from models import TenantContract
            contracts = TenantContract.get_all() or []
            
            self.renewals = []
            for contract in contracts:
                if contract.get('end_date'):
                    end_date = contract.get('end_date')
                    if isinstance(end_date, str):
                        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
                    else:
                        end_date_obj = end_date
                    
                    # 通知日を計算
                    notification_date = end_date_obj - timedelta(days=60)
                    
                    self.renewals.append({
                        'id': contract.get('id'),
                        'type': 'renewal',
                        'title': f"契約更新: {contract.get('property_name', '')} {contract.get('room_number', '')}",
                        'tenant_name': contract.get('tenant_name', ''),
                        'property_name': contract.get('property_name', ''),
                        'room_number': contract.get('room_number', ''),
                        'end_date': end_date_obj.strftime("%Y-%m-%d"),
                        'notification_date': notification_date.strftime("%Y-%m-%d"),
                        'rent': contract.get('rent', 0),
                        'status': contract.get('status', '')
                    })
        except Exception as e:
            print(f"契約更新読み込みエラー: {e}")
            # ダミーデータを追加（テスト用）
            from PyQt6.QtCore import QDate
            current_date = QDate.currentDate()
            self.renewals = [
                {
                    'id': 1,
                    'type': 'renewal',
                    'title': 'サンプル物件 101号室 契約更新',
                    'tenant_name': 'サンプル契約者',
                    'property_name': 'サンプル物件',
                    'room_number': '101',
                    'end_date': current_date.addDays(45).toString("yyyy-MM-dd"),
                    'notification_date': current_date.addDays(-15).toString("yyyy-MM-dd"),
                    'rent': 80000,
                    'status': 'アクティブ'
                },
                {
                    'id': 2,
                    'type': 'renewal',
                    'title': 'サンプル物件 202号室 契約更新',
                    'tenant_name': 'サンプル契約者B',
                    'property_name': 'サンプル物件',
                    'room_number': '202',
                    'end_date': current_date.addDays(80).toString("yyyy-MM-dd"),
                    'notification_date': current_date.addDays(20).toString("yyyy-MM-dd"),
                    'rent': 95000,
                    'status': 'アクティブ'
                }
            ]
            print("ダミー契約データを使用")
    
    def load_procedure_logs(self):
        """契約手続きログを読み込み"""
        try:
            from models import ContractProcedureLog
            from PyQt6.QtCore import QDate
            
            # カレンダー表示用の手続きログイベントを取得
            current_date = QDate.currentDate()
            start_date = current_date.addMonths(-2).toString("yyyy-MM-dd")  # 2ヶ月前から
            end_date = current_date.addMonths(3).toString("yyyy-MM-dd")     # 3ヶ月後まで
            
            procedure_events = ContractProcedureLog.get_calendar_events(start_date, end_date)
            
            # カレンダー表示用にフォーマット
            self.procedure_logs = []
            for event in procedure_events:
                self.procedure_logs.append({
                    'id': event.get('id'),
                    'type': 'procedure',
                    'title': event.get('title', '手続き'),
                    'date': event.get('date'),
                    'status': event.get('status', 'pending'),
                    'notes': event.get('notes', ''),
                    'contractor_name': event.get('contractor_name', ''),
                    'property_name': event.get('property_name', ''),
                    'room_number': event.get('room_number', ''),
                    'color': event.get('color', '#f59e0b')
                })
        except Exception as e:
            print(f"手続きログ読み込みエラー: {e}")
            self.procedure_logs = []
    
    def update_events(self):
        """イベント情報をカレンダーに反映"""
        events_dict = {}
        
        # タスクを追加
        for task in self.tasks:
            date_key = task['due_date']
            if date_key not in events_dict:
                events_dict[date_key] = []
            events_dict[date_key].append(task)
        
        # 契約更新を追加
        for renewal in self.renewals:
            # 通知日
            notif_date = renewal['notification_date']
            if notif_date not in events_dict:
                events_dict[notif_date] = []
            events_dict[notif_date].append({
                **renewal,
                'type': 'renewal_notification',
                'title': f"更新通知: {renewal['property_name']} {renewal['room_number']}"
            })
            
            # 契約終了日
            end_date = renewal['end_date']
            if end_date not in events_dict:
                events_dict[end_date] = []
            events_dict[end_date].append(renewal)
        
        # 手続きログを追加
        for procedure in self.procedure_logs:
            date_key = procedure['date']
            if date_key not in events_dict:
                events_dict[date_key] = []
            events_dict[date_key].append(procedure)
        
        # カレンダーに反映
        self.calendar_widget.set_events(events_dict)
        self.events_dict = events_dict
    
    def on_date_selected(self, date):
        """日付選択時の処理"""
        date_key = date.toString("yyyy-MM-dd")
        events = self.events_dict.get(date_key, [])
        self.event_list.update_events(date, events)
    
    def resizeEvent(self, event):
        """リサイズイベント処理"""
        super().resizeEvent(event)
        # 必要に応じてレイアウト調整
    
    def quick_refresh_tasks(self):
        """タスクのみの高速更新"""
        try:
            # タスクデータのみを再読み込み
            self.load_tasks()
            # イベント情報を更新
            self.update_events()
            print("モダンカレンダーのタスクデータを高速更新しました")
        except Exception as e:
            print(f"モダンカレンダータスク高速更新エラー: {e}")
    
    def quick_refresh_contracts(self):
        """契約データのみの高速更新"""
        try:
            print("モダンカレンダー契約データ高速更新開始")
            # 契約・更新データのみを再読み込み
            self.load_renewals()
            print(f"契約データ読み込み完了: {len(self.renewals)}件")
            # イベント情報を更新
            self.update_events()
            print("モダンカレンダーの契約データを高速更新しました")
        except Exception as e:
            print(f"モダンカレンダー契約高速更新エラー: {e}")
            import traceback
            traceback.print_exc()
    
    def quick_refresh_procedures(self):
        """手続きログのみの高速更新"""
        try:
            print("モダンカレンダー手続きログ高速更新開始")
            # 手続きログデータのみを再読み込み
            self.load_procedure_logs()
            print(f"手続きログデータ読み込み完了: {len(self.procedure_logs)}件")
            # イベント情報を更新
            self.update_events()
            print("モダンカレンダーの手続きログを高速更新しました")
        except Exception as e:
            print(f"モダンカレンダー手続きログ高速更新エラー: {e}")
            import traceback
            traceback.print_exc()