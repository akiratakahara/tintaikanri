"""
カレンダービュータブ - タスクと更新管理スケジュール表示
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QCalendarWidget, 
                             QLabel, QListWidget, QListWidgetItem, QPushButton, 
                             QGroupBox, QSplitter, QTextEdit, QComboBox,
                             QScrollArea, QFrame)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QTimer
from PyQt6.QtGui import QTextCharFormat, QColor, QFont
from utils import DateHelper, MessageHelper
from datetime import datetime, timedelta
from ui.ui_styles import ModernStyles

class CalendarTab(QWidget):
    """カレンダービュータブ"""
    
    def __init__(self):
        super().__init__()
        self.tasks = []
        self.renewals = []
        self.procedure_logs = []
        self.selected_date = QDate.currentDate()
        self.calendar = None
        self.splitter = None  # 明示的に初期化
        
        try:
            print("カレンダータブの初期化を開始...")
            self.init_ui()
            print("UI初期化完了")
            self.load_schedule_data()
            print("スケジュールデータ読み込み完了")
            self.update_calendar()
            print("カレンダー更新完了")
            # 自動更新機能は不要のため無効化
            # self.setup_auto_refresh()
        except Exception as e:
            print(f"CalendarTab初期化エラー: {e}")
            import traceback
            traceback.print_exc()
            self.init_error_ui()
    
    def init_ui(self):
        # モダンスタイルを適用
        self.setStyleSheet(ModernStyles.get_all_styles())
        
        # メインレイアウト（全画面対応）
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)
        
        # 左側：カレンダー
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        
        # 月選択コントロール
        month_control_layout = QHBoxLayout()
        
        self.prev_month_btn = QPushButton("◀ 前月")
        self.prev_month_btn.clicked.connect(self.prev_month)
        
        self.next_month_btn = QPushButton("次月 ▶")
        self.next_month_btn.clicked.connect(self.next_month)
        
        self.current_month_label = QLabel()
        self.current_month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_month_label.setStyleSheet("font-weight: bold; font-size: 16px; padding: 5px;")
        
        month_control_layout.addWidget(self.prev_month_btn)
        month_control_layout.addWidget(self.current_month_label, 1)
        month_control_layout.addWidget(self.next_month_btn)
        
        # カレンダーウィジェット（レスポンシブ対応）
        try:
            self.calendar = QCalendarWidget()
            # サイズポリシーを設定してレスポンシブに
            from PyQt6.QtWidgets import QSizePolicy
            self.calendar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.calendar.setMinimumSize(350, 250)
            # 最大サイズを制限してバランスを保つ
            self.calendar.setMaximumSize(800, 600)
            
            # 日本語ロケール設定
            try:
                from PyQt6.QtCore import QLocale
                japanese_locale = QLocale(QLocale.Language.Japanese, QLocale.Country.Japan)
                self.calendar.setLocale(japanese_locale)
            except:
                pass  # ロケール設定に失敗しても続行
            
            # 今日の日付を選択
            self.calendar.setSelectedDate(QDate.currentDate())
            
            self.calendar.clicked.connect(self.safe_on_date_clicked)
            self.calendar.currentPageChanged.connect(self.safe_on_month_changed)
        except Exception as e:
            print(f"カレンダーウィジェット作成エラー: {e}")
            self.calendar = QLabel("カレンダー機能でエラーが発生しました")
            self.calendar.setStyleSheet("color: red; font-weight: bold; text-align: center; border: 2px solid red; padding: 20px;")
            self.calendar.setMinimumSize(400, 300)
        
        # カレンダーのスタイル設定（QCalendarWidgetの場合のみ）
        if isinstance(self.calendar, QCalendarWidget):
            try:
                self.calendar.setStyleSheet("""
                    QCalendarWidget QWidget { 
                        alternate-background-color: #f0f0f0;
                    }
                    QCalendarWidget QAbstractItemView:enabled {
                        font-size: 12px;
                        selection-background-color: #3498db;
                        selection-color: white;
                    }
                """)
            except Exception as e:
                print(f"カレンダースタイル設定エラー: {e}")
        
        # 凡例
        legend_group = QGroupBox("凡例")
        legend_layout = QVBoxLayout()
        
        task_legend = QLabel("🔧 タスク (赤背景)")
        task_legend.setStyleSheet("color: #d32f2f; font-weight: bold;")
        
        renewal_legend = QLabel("🔄 契約更新 (青背景)")
        renewal_legend.setStyleSheet("color: #1976d2; font-weight: bold;")
        
        overdue_legend = QLabel("⚠️ 期限超過 (濃い背景)")
        overdue_legend.setStyleSheet("color: #b71c1c; font-weight: bold;")
        
        procedure_legend = QLabel("📋 契約手続き (オレンジ背景、波線)")
        procedure_legend.setStyleSheet("color: #e65100; font-weight: bold;")
        
        legend_layout.addWidget(task_legend)
        legend_layout.addWidget(renewal_legend)
        legend_layout.addWidget(procedure_legend)
        legend_layout.addWidget(overdue_legend)
        legend_group.setLayout(legend_layout)
        
        left_layout.addLayout(month_control_layout)
        left_layout.addWidget(self.calendar, 1)
        left_layout.addWidget(legend_group)
        left_widget.setLayout(left_layout)
        
        # 右側：選択日の詳細
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        
        # 選択日表示（レスポンシブ対応）
        self.selected_date_label = QLabel()
        self.selected_date_label.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold; 
            padding: 12px; 
            background-color: #e3f2fd; 
            border-radius: 8px;
            margin: 4px;
            min-height: 20px;
        """)
        self.selected_date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.selected_date_label.setWordWrap(True)  # テキストの自動折り返し
        
        # フィルター
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("表示:"))
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全て", "タスクのみ", "契約更新のみ", "手続きのみ"])
        self.filter_combo.currentTextChanged.connect(self.update_daily_schedule)
        
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addStretch()
        
        # 当日のスケジュール一覧（レスポンシブ対応）
        schedule_group = QGroupBox("スケジュール詳細")
        schedule_layout = QVBoxLayout()
        
        # スクロール可能なリスト（サイズ調整）
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(200)
        # 全画面時に適切な高さを設定
        from PyQt6.QtWidgets import QSizePolicy
        scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self.schedule_list = QListWidget()
        self.schedule_list.setStyleSheet("""
            QListWidget::item {
                padding: 8px;
                margin: 2px;
                border-radius: 4px;
                border: 1px solid #ddd;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
            }
        """)
        self.schedule_list.itemDoubleClicked.connect(self.show_item_detail)
        
        scroll_area.setWidget(self.schedule_list)
        
        schedule_layout.addWidget(scroll_area)
        schedule_group.setLayout(schedule_layout)
        
        # アクションボタン
        action_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("更新")
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.refresh_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px; }")
        
        self.today_btn = QPushButton("今日")
        self.today_btn.clicked.connect(self.go_to_today)
        
        action_layout.addWidget(self.refresh_btn)
        action_layout.addWidget(self.today_btn)
        action_layout.addStretch()
        
        right_layout.addWidget(self.selected_date_label)
        right_layout.addLayout(filter_layout)
        right_layout.addWidget(schedule_group, 1)
        right_layout.addLayout(action_layout)
        right_widget.setLayout(right_layout)
        
        # レスポンシブスプリッター設定
        self.splitter = QSplitter(Qt.Orientation.Horizontal)  # selfで参照保持
        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(right_widget)
        
        # 全画面時の最適な比率設定
        self.splitter.setStretchFactor(0, 2)  # カレンダー側を少し大きく
        self.splitter.setStretchFactor(1, 1)  # 詳細側
        
        # 初期サイズを設定
        self.splitter.setSizes([600, 400])  # カレンダー:600px, 詳細:400px
        
        # スプリッターのスタイルを改善
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #e2e8f0;
                width: 3px;
                margin: 2px 4px;
                border-radius: 2px;
            }
            QSplitter::handle:hover {
                background-color: #cbd5e1;
                width: 4px;
            }
            QSplitter::handle:pressed {
                background-color: #94a3b8;
            }
        """)
        
        # スプリッターのサイズ変更を可能に
        self.splitter.setCollapsible(0, False)  # カレンダー側は折りたたみ不可
        self.splitter.setCollapsible(1, False)  # 詳細側も折りたたみ不可
        
        layout.addWidget(self.splitter)
        self.setLayout(layout)
        
        print(f"スプリッター初期化: {self.splitter is not None}")
        
        # 初期選択日を設定
        self.update_selected_date()
        
        # ウィンドウサイズ変更時のリサイズイベントを設定
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        
        print("カレンダーUI初期化完了")
    
    def init_error_ui(self):
        """エラー時の代替UI"""
        # 既存のレイアウトをクリア
        if self.layout():
            while self.layout().count():
                child = self.layout().takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            self.layout().deleteLater()
        
        layout = QVBoxLayout()
        
        error_label = QLabel("カレンダータブでエラーが発生しました")
        error_label.setStyleSheet("color: red; font-weight: bold; text-align: center; padding: 40px; font-size: 16px;")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        detail_label = QLabel("システム管理者に連絡してください")
        detail_label.setStyleSheet("color: #666; text-align: center; padding: 10px;")
        detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(error_label)
        layout.addWidget(detail_label)
        
        self.setLayout(layout)
    
    def safe_on_date_clicked(self, date):
        """安全な日付クリック処理"""
        try:
            self.on_date_clicked(date)
        except Exception as e:
            print(f"日付クリックエラー: {e}")
            MessageHelper.show_error(self, f"日付選択でエラーが発生しました: {str(e)}")
    
    def safe_on_month_changed(self):
        """安全な月変更処理"""
        try:
            self.on_month_changed()
        except Exception as e:
            print(f"月変更エラー: {e}")
    
    def load_schedule_data(self):
        """スケジュールデータを読み込み"""
        self.load_tasks()
        self.load_renewals()
        self.load_procedure_logs()
    
    def load_tasks(self):
        """タスクデータを読み込み"""
        try:
            from models import Task
            db_tasks = Task.get_pending_tasks()
            
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
            # ダミーデータ
            self.tasks = [
                {
                    'id': 1,
                    'type': 'task',
                    'title': 'サンプル更新案内タスク',
                    'description': '契約更新の案内を送付',
                    'due_date': QDate.currentDate().addDays(3).toString("yyyy-MM-dd"),
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
                    'due_date': QDate.currentDate().addDays(7).toString("yyyy-MM-dd"),
                    'priority': '中',
                    'task_type': '修繕',
                    'assigned_to': '担当者B',
                    'status': '未完了'
                }
            ]
            print(f"タスクDB接続エラー（ダミーデータ使用）: {e}")
    
    def load_renewals(self):
        """契約更新データを読み込み"""
        try:
            from models import TenantContract
            contracts = TenantContract.get_all()
            
            self.renewals = []
            for contract in contracts:
                if contract.get('end_date'):
                    end_date = contract.get('end_date')
                    if isinstance(end_date, str):
                        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
                    else:
                        end_date_obj = end_date
                    
                    # 契約終了60日前から表示
                    notification_date = end_date_obj - timedelta(days=60)
                    
                    self.renewals.append({
                        'id': contract.get('id'),
                        'type': 'renewal',
                        'title': f"契約更新: {contract.get('property_name', '')} {contract.get('room_number', '')}",
                        'tenant_name': contract.get('tenant_name', ''),
                        'property_name': contract.get('property_name', ''),
                        'room_number': contract.get('room_number', ''),
                        'end_date': end_date,
                        'notification_date': notification_date.strftime("%Y-%m-%d"),
                        'rent': contract.get('rent', 0),
                        'status': contract.get('status', '')
                    })
        except Exception as e:
            # ダミーデータ
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
            print(f"契約DB接続エラー（ダミーデータ使用）: {e}")
    
    def load_procedure_logs(self):
        """契約手続きログを読み込み"""
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from contract_procedure_log import ContractProcedureLog
            
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
    
    def update_calendar(self):
        """カレンダーにスケジュールを反映"""
        if not isinstance(self.calendar, QCalendarWidget):
            return
        
        try:
            # カレンダーの書式をリセット
            self.calendar.setDateTextFormat(QDate(), QTextCharFormat())
            
            current_date = QDate.currentDate()
        except Exception as e:
            print(f"カレンダー更新エラー: {e}")
            return
        
        # タスクをカレンダーにマーク
        try:
            for task in self.tasks:
                if task.get('due_date'):
                    date = QDate.fromString(task['due_date'], "yyyy-MM-dd")
                    if date.isValid():
                        format = QTextCharFormat()
                        
                        # 期限超過チェック
                        if date < current_date:
                            format.setBackground(QColor("#b71c1c"))  # 濃い赤
                            format.setForeground(QColor("white"))
                        elif task.get('priority') == '高':
                            format.setBackground(QColor("#ffcdd2"))  # 薄い赤
                        else:
                            format.setBackground(QColor("#ffebee"))  # とても薄い赤
                        
                        format.setFontWeight(QFont.Weight.Bold)
                        self.calendar.setDateTextFormat(date, format)
        except Exception as e:
            print(f"タスクマーキングエラー: {e}")
        
        # 契約更新をカレンダーにマーク
        try:
            for renewal in self.renewals:
                # 通知日をマーク
                notification_date = QDate.fromString(renewal.get('notification_date', ''), "yyyy-MM-dd")
                if notification_date.isValid():
                    format = QTextCharFormat()
                    
                    if notification_date < current_date:
                        format.setBackground(QColor("#0d47a1"))  # 濃い青
                        format.setForeground(QColor("white"))
                    else:
                        format.setBackground(QColor("#bbdefb"))  # 薄い青
                    
                    format.setFontWeight(QFont.Weight.Bold)
                    self.calendar.setDateTextFormat(notification_date, format)
                
                # 契約終了日もマーク（オレンジ）
                end_date_str = renewal.get('end_date', '')
                if end_date_str:
                    end_date = QDate.fromString(end_date_str, "yyyy-MM-dd")
                    if end_date.isValid():
                        format = QTextCharFormat()
                        
                        if end_date < current_date:
                            format.setBackground(QColor("#e65100"))  # 濃いオレンジ
                            format.setForeground(QColor("white"))
                        else:
                            format.setBackground(QColor("#ffe0b2"))  # 薄いオレンジ
                        
                        format.setFontWeight(QFont.Weight.Bold)
                        format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)
                        self.calendar.setDateTextFormat(end_date, format)
        except Exception as e:
            print(f"契約更新マーキングエラー: {e}")
        
        # 契約手続きログをカレンダーにマーク
        try:
            if hasattr(self, 'procedure_logs'):
                for procedure in self.procedure_logs:
                    if procedure.get('date'):
                        date = QDate.fromString(procedure['date'], "yyyy-MM-dd")
                        if date.isValid():
                            format = QTextCharFormat()
                            
                            # ステータスに応じた色分け
                            status = procedure.get('status', 'pending')
                            if status == 'completed':
                                format.setBackground(QColor("#c8e6c9"))  # 薄い緑
                            elif status == 'in_progress':
                                format.setBackground(QColor("#bbdefb"))  # 薄い青
                            elif date < current_date:
                                format.setBackground(QColor("#ffab91"))  # 薄いオレンジ
                                format.setForeground(QColor("white"))
                            else:
                                format.setBackground(QColor("#fff3e0"))  # とても薄いオレンジ
                            
                            format.setFontWeight(QFont.Weight.Bold)
                            # 既存のフォーマットと重ならないように下線を追加
                            format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)
                            self.calendar.setDateTextFormat(date, format)
        except Exception as e:
            print(f"手続きログマーキングエラー: {e}")
        
        # 月表示を更新
        try:
            if isinstance(self.calendar, QCalendarWidget):
                current_page = self.calendar.monthShown(), self.calendar.yearShown()
                self.current_month_label.setText(f"{current_page[1]}年 {current_page[0]:02d}月")
        except Exception as e:
            print(f"月表示更新エラー: {e}")
    
    def on_date_clicked(self, date):
        """日付クリック時の処理"""
        self.selected_date = date
        self.update_selected_date()
        self.update_daily_schedule()
    
    def on_month_changed(self):
        """月変更時の処理"""
        self.update_calendar()
    
    def update_selected_date(self):
        """選択日表示を更新"""
        try:
            # PyQt6対応：複数の方法を試行
            try:
                py_date = self.selected_date.toPyDate()
            except AttributeError:
                try:
                    py_date = self.selected_date.toPython()
                except AttributeError:
                    # フォールバック：QDateから直接フォーマット
                    date_str = self.selected_date.toString('yyyy年MM月dd日 (ddd)')
                    self.selected_date_label.setText(f"選択日: {date_str}")
                    return
            
            # 日本語曜日マッピング
            weekdays = ['月', '火', '水', '木', '金', '土', '日']
            weekday_jp = weekdays[py_date.weekday()]
            date_str = f"{py_date.year}年{py_date.month:02d}月{py_date.day:02d}日 ({weekday_jp})"
            self.selected_date_label.setText(f"選択日: {date_str}")
        except Exception as e:
            print(f"選択日表示更新エラー: {e}")
            # 最終フォールバック
            date_str = self.selected_date.toString('yyyy年MM月dd日')
            self.selected_date_label.setText(f"選択日: {date_str}")
    
    def update_daily_schedule(self):
        """選択日のスケジュール一覧を更新"""
        try:
            self.schedule_list.clear()
            
            selected_date_str = self.selected_date.toString("yyyy-MM-dd")
            filter_type = self.filter_combo.currentText()
            current_date = QDate.currentDate()
            
            items = []
            
            # タスクを追加
            if filter_type in ["全て", "タスクのみ"]:
                for task in self.tasks:
                    if task.get('due_date') == selected_date_str:
                        items.append(('task', task))
            
            # 契約更新を追加（通知日と終了日両方）
            if filter_type in ["全て", "契約更新のみ"]:
                for renewal in self.renewals:
                    if renewal.get('notification_date') == selected_date_str:
                        items.append(('renewal_notification', renewal))
                    if renewal.get('end_date') == selected_date_str:
                        items.append(('renewal_end', renewal))
            
            # 契約手続きログを追加
            if filter_type in ["全て", "手続きのみ"] and hasattr(self, 'procedure_logs'):
                for procedure in self.procedure_logs:
                    if procedure.get('date') == selected_date_str:
                        items.append(('procedure', procedure))
            
            # アイテムを表示
            for item_type, item_data in items:
                list_item = QListWidgetItem()
                
                if item_type == 'task':
                    # 期限チェック
                    days_until = current_date.daysTo(self.selected_date)
                    if days_until < 0:
                        icon = "🔴"
                        urgency = f"【期限切れ {abs(days_until)}日】"
                        list_item.setBackground(QColor("#ffcdd2"))
                    elif days_until == 0:
                        icon = "🔥"
                        urgency = "【本日期限】"
                        list_item.setBackground(QColor("#fff3e0"))
                    elif item_data.get('priority') == '高':
                        icon = "⚠️"
                        urgency = "【高優先度】"
                        list_item.setBackground(QColor("#fff3e0"))
                    else:
                        icon = "🔧"
                        urgency = ""
                    
                    title = f"{icon} {urgency} {item_data.get('task_type', 'タスク')}: {item_data.get('title', '無題')}"
                    
                    # 詳細情報
                    details = []
                    if item_data.get('priority'):
                        details.append(f"優先度: {item_data['priority']}")
                    if item_data.get('assigned_to'):
                        details.append(f"担当者: {item_data['assigned_to']}")
                    if item_data.get('description'):
                        details.append(f"内容: {item_data['description'][:50]}{'...' if len(item_data['description']) > 50 else ''}")
                    
                    detail = " | ".join(details) if details else "詳細情報なし"
                    
                elif item_type == 'renewal_notification':
                    icon = "🔔"
                    title = f"{icon} 【契約更新通知】 {item_data.get('property_name', '')} {item_data.get('room_number', '')}"
                    
                    end_date_str = item_data.get('end_date', '')
                    if end_date_str:
                        # 安全な日付フォーマット
                        try:
                            from datetime import datetime
                            date_obj = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                            end_date_formatted = f"{date_obj.year}年{date_obj.month:02d}月{date_obj.day:02d}日"
                        except:
                            end_date_formatted = end_date_str
                        detail = f"契約者: {item_data.get('tenant_name', '未設定')} | 契約終了予定: {end_date_formatted}"
                    else:
                        detail = f"契約者: {item_data.get('tenant_name', '未設定')}"
                    
                    list_item.setBackground(QColor("#e3f2fd"))
                    
                elif item_type == 'renewal_end':
                    # 契約終了のチェック
                    days_until = current_date.daysTo(self.selected_date)
                    if days_until < 0:
                        icon = "🔴"
                        urgency = "【契約終了済み】"
                        list_item.setBackground(QColor("#ffcdd2"))
                    elif days_until == 0:
                        icon = "⏰"
                        urgency = "【本日契約終了】"
                        list_item.setBackground(QColor("#ffe0b2"))
                    else:
                        icon = "⏰"
                        urgency = "【契約終了予定】"
                        list_item.setBackground(QColor("#ffe0b2"))
                    
                    title = f"{icon} {urgency} {item_data.get('property_name', '')} {item_data.get('room_number', '')}"
                    
                    rent = item_data.get('rent', 0)
                    rent_str = f"¥{rent:,}" if rent else "賃料未設定"
                    detail = f"契約者: {item_data.get('tenant_name', '未設定')} | 月額賃料: {rent_str}"
                
                elif item_type == 'procedure':
                    # 契約手続きログ
                    status = item_data.get('status', 'pending')
                    if status == 'completed':
                        icon = "✅"
                        urgency = "【完了済み】"
                        list_item.setBackground(QColor("#c8e6c9"))
                    elif status == 'in_progress':
                        icon = "🔄"
                        urgency = "【処理中】"
                        list_item.setBackground(QColor("#bbdefb"))
                    elif current_date.daysTo(self.selected_date) < 0:
                        icon = "⚠️"
                        urgency = "【期限超過】"
                        list_item.setBackground(QColor("#ffab91"))
                    else:
                        icon = "📋"
                        urgency = "【手続き予定】"
                        list_item.setBackground(QColor("#fff3e0"))
                    
                    title = f"{icon} {urgency} {item_data.get('title', '手続き')}"
                    
                    details = []
                    if item_data.get('contractor_name'):
                        details.append(f"契約者: {item_data['contractor_name']}")
                    if item_data.get('property_name') and item_data.get('room_number'):
                        details.append(f"物件: {item_data['property_name']} {item_data['room_number']}")
                    if item_data.get('notes'):
                        details.append(f"備考: {item_data['notes'][:30]}{'...' if len(item_data['notes']) > 30 else ''}")
                    
                    detail = " | ".join(details) if details else "詳細情報なし"
                
                list_item.setText(f"{title}\n    {detail}")
                list_item.setData(Qt.ItemDataRole.UserRole, (item_type, item_data))
                
                self.schedule_list.addItem(list_item)
            
            if not items:
                try:
                    # PyQt6対応の日付取得
                    try:
                        py_date = self.selected_date.toPyDate()
                    except AttributeError:
                        try:
                            py_date = self.selected_date.toPython()
                        except AttributeError:
                            date_str = self.selected_date.toString("yyyy年MM月dd日")
                            return date_str
                    date_str = f"{py_date.year}年{py_date.month:02d}月{py_date.day:02d}日"
                except:
                    date_str = self.selected_date.toString("yyyy年MM月dd日")
                
                empty_item = QListWidgetItem(f"{date_str} にはスケジュールがありません")
                empty_item.setForeground(QColor("#666"))
                empty_item.setFlags(Qt.ItemFlag.NoItemFlags)  # 選択不可
                self.schedule_list.addItem(empty_item)
                
        except Exception as e:
            print(f"スケジュール更新エラー: {e}")
            error_item = QListWidgetItem("スケジュール表示でエラーが発生しました")
            error_item.setForeground(QColor("#f44336"))
            error_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.schedule_list.addItem(error_item)
    
    def show_item_detail(self, item):
        """アイテム詳細表示"""
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
        
        item_type, item_data = data
        
        if item_type == 'task':
            detail = f"【タスク詳細】\n\n"
            detail += f"種別: {item_data['task_type']}\n"
            detail += f"タイトル: {item_data['title']}\n"
            
            # 安全な日付フォーマット
            try:
                if isinstance(item_data['due_date'], str):
                    from datetime import datetime
                    date_obj = datetime.strptime(item_data['due_date'], '%Y-%m-%d').date()
                    formatted_date = f"{date_obj.year}年{date_obj.month:02d}月{date_obj.day:02d}日"
                else:
                    formatted_date = str(item_data['due_date'])
            except:
                formatted_date = str(item_data['due_date'])
            detail += f"期限: {formatted_date}\n"
            
            detail += f"優先度: {item_data['priority']}\n"
            detail += f"担当者: {item_data['assigned_to']}\n"
            detail += f"状態: {item_data['status']}\n\n"
            if item_data['description']:
                detail += f"説明:\n{item_data['description']}"
        
        elif item_type.startswith('renewal'):
            detail = f"【契約更新詳細】\n\n"
            detail += f"物件: {item_data['property_name']} {item_data['room_number']}\n"
            detail += f"契約者: {item_data['tenant_name']}\n"
            detail += f"月額賃料: ¥{item_data['rent']:,}\n"
            
            # 契約終了日の安全な日付フォーマット
            try:
                if isinstance(item_data['end_date'], str):
                    from datetime import datetime
                    date_obj = datetime.strptime(item_data['end_date'], '%Y-%m-%d').date()
                    end_date_formatted = f"{date_obj.year}年{date_obj.month:02d}月{date_obj.day:02d}日"
                else:
                    end_date_formatted = str(item_data['end_date'])
            except:
                end_date_formatted = str(item_data['end_date'])
            detail += f"契約終了日: {end_date_formatted}\n"
            
            # 通知開始日の安全な日付フォーマット
            try:
                if isinstance(item_data['notification_date'], str):
                    from datetime import datetime
                    date_obj = datetime.strptime(item_data['notification_date'], '%Y-%m-%d').date()
                    notification_date_formatted = f"{date_obj.year}年{date_obj.month:02d}月{date_obj.day:02d}日"
                else:
                    notification_date_formatted = str(item_data['notification_date'])
            except:
                notification_date_formatted = str(item_data['notification_date'])
            detail += f"通知開始日: {notification_date_formatted}\n"
            
            detail += f"ステータス: {item_data['status']}"
        
        elif item_type == 'procedure':
            detail = f"【契約手続き詳細】\n\n"
            detail += f"手続き種別: {item_data['title']}\n"
            
            # 期限日の安全な日付フォーマット
            try:
                if isinstance(item_data['date'], str):
                    from datetime import datetime
                    date_obj = datetime.strptime(item_data['date'], '%Y-%m-%d').date()
                    deadline_formatted = f"{date_obj.year}年{date_obj.month:02d}月{date_obj.day:02d}日"
                else:
                    deadline_formatted = str(item_data['date'])
            except:
                deadline_formatted = str(item_data['date'])
            detail += f"期限日: {deadline_formatted}\n"
            
            detail += f"ステータス: {item_data['status']}\n"
            if item_data['contractor_name']:
                detail += f"契約者: {item_data['contractor_name']}\n"
            if item_data['property_name'] and item_data['room_number']:
                detail += f"物件: {item_data['property_name']} {item_data['room_number']}\n"
            if item_data['notes']:
                detail += f"\n備考:\n{item_data['notes']}"
        
        MessageHelper.show_success(self, detail, "詳細情報")
    
    def prev_month(self):
        """前月に移動"""
        if not isinstance(self.calendar, QCalendarWidget):
            return
        
        try:
            current_date = self.calendar.selectedDate()
            prev_month_date = current_date.addMonths(-1)
            self.calendar.setSelectedDate(prev_month_date)
            self.calendar.showSelectedDate()
        except Exception as e:
            print(f"前月移動エラー: {e}")
    
    def next_month(self):
        """次月に移動"""
        if not isinstance(self.calendar, QCalendarWidget):
            return
        
        try:
            current_date = self.calendar.selectedDate()
            next_month_date = current_date.addMonths(1)
            self.calendar.setSelectedDate(next_month_date)
            self.calendar.showSelectedDate()
        except Exception as e:
            print(f"次月移動エラー: {e}")
    
    def go_to_today(self):
        """今日に移動"""
        if not isinstance(self.calendar, QCalendarWidget):
            return
        
        try:
            today = QDate.currentDate()
            self.calendar.setSelectedDate(today)
            self.calendar.showSelectedDate()
            self.selected_date = today
            self.update_selected_date()
            self.update_daily_schedule()
        except Exception as e:
            print(f"今日移動エラー: {e}")
            MessageHelper.show_error(self, f"今日への移動でエラーが発生しました: {str(e)}")
    
    def refresh_data(self):
        """データを再読み込み"""
        try:
            self.load_schedule_data()
            self.update_calendar()
            self.update_daily_schedule()
            MessageHelper.show_success(self, "スケジュールデータを更新しました")
        except Exception as e:
            print(f"データ再読み込みエラー: {e}")
            MessageHelper.show_error(self, f"データ更新中にエラーが発生しました: {str(e)}")
    
    def setup_auto_refresh(self):
        """自動更新機能を設定（無効化）"""
        # 自動更新機能は不要のため無効化
        pass
    
    def auto_refresh_data(self):
        """自動データ更新（無効化）"""
        # 自動更新機能は不要のため無効化
        pass
    
    def manual_refresh(self):
        """手動更新機能（全体）"""
        try:
            self.load_schedule_data()
            self.update_calendar()
            self.update_daily_schedule()
        except Exception as e:
            print(f"手動更新エラー: {e}")
    
    def quick_refresh_tasks(self):
        """タスクのみの高速更新"""
        try:
            # タスクデータのみを再読み込み
            self.load_tasks()
            # カレンダー表示を即座に更新
            self.update_calendar()
            # 選択日のスケジュールも更新
            self.update_daily_schedule()
            print("タスクデータを高速更新しました")
        except Exception as e:
            print(f"タスク高速更新エラー: {e}")
    
    def quick_refresh_contracts(self):
        """契約データのみの高速更新"""
        try:
            # 契約・更新データのみを再読み込み
            self.load_renewals()
            self.load_procedure_logs()
            # カレンダー表示を即座に更新
            self.update_calendar()
            # 選択日のスケジュールも更新
            self.update_daily_schedule()
            print("契約データを高速更新しました")
        except Exception as e:
            print(f"契約高速更新エラー: {e}")
    
    def showEvent(self, event):
        """タブが表示される際の処理（自動更新なし）"""
        super().showEvent(event)
        # 自動更新は行わない
    
    def closeEvent(self, event):
        """タブを閉じる際の処理"""
        # タイマーが存在する場合のみ停止
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        super().closeEvent(event)
    
    def resizeEvent(self, event):
        """ウィンドウサイズ変更時の処理"""
        super().resizeEvent(event)
        
        # ウィンドウサイズに応じてスプリッターの比率を調整
        if hasattr(self, 'splitter'):
            try:
                window_width = event.size().width()
                
                if window_width > 1400:  # 大画面時
                    # カレンダーを少し小さくして詳細を幅広に
                    self.splitter.setSizes([int(window_width * 0.45), int(window_width * 0.55)])
                elif window_width > 1000:  # 中画面時
                    # バランスよく分割
                    self.splitter.setSizes([int(window_width * 0.5), int(window_width * 0.5)])
                else:  # 小画面時
                    # カレンダーを優先
                    self.splitter.setSizes([int(window_width * 0.6), int(window_width * 0.4)])
                    
            except Exception as e:
                print(f"リサイズ処理エラー: {e}")