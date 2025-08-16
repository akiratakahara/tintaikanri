"""
拡張ダッシュボード - カレンダーとスケジュール統合版
"""
import sys
from datetime import datetime, date, timedelta
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QGroupBox, QGridLayout, QListWidget, QListWidgetItem,
                             QCalendarWidget, QSplitter, QTextEdit, QScrollArea,
                             QFrame, QComboBox)
from PyQt6.QtCore import Qt, QDate, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QTextCharFormat, QColor
from utils import MessageHelper, DateHelper, FormatHelper

class CompactCalendarWidget(QWidget):
    """ダッシュボード用コンパクトカレンダー"""
    
    date_selected = pyqtSignal(QDate)
    
    def __init__(self):
        super().__init__()
        self.tasks = []
        self.renewals = []
        self.calendar = None
        try:
            self.init_ui()
            self.load_schedule_data()
            self.update_calendar()
        except Exception as e:
            print(f"CompactCalendarWidget初期化エラー: {e}")
            self.init_error_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # ヘッダー
        header_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setMaximumWidth(30)
        self.prev_btn.clicked.connect(self.prev_month)
        
        self.month_label = QLabel()
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.month_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.next_btn = QPushButton("▶")
        self.next_btn.setMaximumWidth(30)
        self.next_btn.clicked.connect(self.next_month)
        
        self.today_btn = QPushButton("今日")
        self.today_btn.setMaximumWidth(50)
        self.today_btn.clicked.connect(self.go_to_today)
        self.today_btn.setStyleSheet("QPushButton { font-size: 10px; padding: 2px; }")
        
        header_layout.addWidget(self.prev_btn)
        header_layout.addWidget(self.month_label, 1)
        header_layout.addWidget(self.next_btn)
        header_layout.addWidget(self.today_btn)
        
        # カレンダー
        try:
            self.calendar = QCalendarWidget()
            self.calendar.setMaximumHeight(200)
            self.calendar.clicked.connect(self.safe_on_date_clicked)
            self.calendar.currentPageChanged.connect(self.safe_on_month_changed)
        except Exception as e:
            print(f"カレンダーウィジェット作成エラー: {e}")
            self.calendar = QLabel("カレンダー表示エラー")
            self.calendar.setStyleSheet("color: red; font-weight: bold; text-align: center;")
            self.calendar.setMaximumHeight(200)
        
        # コンパクトなスタイル（カレンダーが正常に作成された場合のみ）
        if isinstance(self.calendar, QCalendarWidget):
            try:
                self.calendar.setStyleSheet("""
                    QCalendarWidget {
                        font-size: 10px;
                    }
                    QCalendarWidget QWidget { 
                        alternate-background-color: #f0f0f0;
                    }
                    QCalendarWidget QAbstractItemView:enabled {
                        font-size: 9px;
                        selection-background-color: #3498db;
                        selection-color: white;
                    }
                    QCalendarWidget QToolButton {
                        height: 20px;
                        width: 20px;
                        font-size: 10px;
                    }
                """)
            except Exception as e:
                print(f"カレンダースタイル設定エラー: {e}")
        
        layout.addLayout(header_layout)
        layout.addWidget(self.calendar)
        
        self.setLayout(layout)
        self.update_month_label()
    
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
        
        error_label = QLabel("カレンダー機能でエラーが発生しました")
        error_label.setStyleSheet("color: red; font-weight: bold; text-align: center; padding: 20px;")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(error_label)
        self.setLayout(layout)
    
    def load_schedule_data(self):
        """スケジュールデータを読み込み"""
        self.load_tasks()
        self.load_renewals()
    
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
                        'due_date': task.get('due_date'),
                        'priority': task.get('priority', '中'),
                        'task_type': task.get('task_type', ''),
                        'status': task.get('status', '未完了')
                    })
        except Exception as e:
            # ダミーデータ
            current_date = QDate.currentDate()
            self.tasks = [
                {
                    'id': 1,
                    'type': 'task',
                    'title': '更新案内送付',
                    'due_date': current_date.addDays(3).toString("yyyy-MM-dd"),
                    'priority': '高',
                    'task_type': '更新案内',
                    'status': '未完了'
                },
                {
                    'id': 2,
                    'type': 'task',
                    'title': 'エアコン修理手配',
                    'due_date': current_date.addDays(-2).toString("yyyy-MM-dd"),
                    'priority': '高',
                    'task_type': '修繕',
                    'status': '未完了'
                },
                {
                    'id': 3,
                    'type': 'task',
                    'title': '請求書発行',
                    'due_date': current_date.addDays(7).toString("yyyy-MM-dd"),
                    'priority': '中',
                    'task_type': '請求',
                    'status': '未完了'
                }
            ]
    
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
                    
                    notification_date = end_date_obj - timedelta(days=60)
                    
                    self.renewals.append({
                        'id': contract.get('id'),
                        'type': 'renewal',
                        'property_name': contract.get('property_name', ''),
                        'room_number': contract.get('room_number', ''),
                        'tenant_name': contract.get('tenant_name', ''),
                        'end_date': end_date,
                        'notification_date': notification_date.strftime("%Y-%m-%d")
                    })
        except Exception as e:
            # ダミーデータ
            current_date = QDate.currentDate()
            self.renewals = [
                {
                    'id': 1,
                    'type': 'renewal',
                    'property_name': 'サンプル物件',
                    'room_number': '101',
                    'tenant_name': 'サンプル契約者',
                    'end_date': current_date.addDays(45).toString("yyyy-MM-dd"),
                    'notification_date': current_date.addDays(-15).toString("yyyy-MM-dd")
                }
            ]
    
    def safe_on_date_clicked(self, date):
        """安全な日付クリック処理"""
        try:
            self.on_date_clicked(date)
        except Exception as e:
            print(f"日付クリックエラー: {e}")
    
    def safe_on_month_changed(self):
        """安全な月変更処理"""
        try:
            self.on_month_changed()
        except Exception as e:
            print(f"月変更エラー: {e}")
    
    def update_calendar(self):
        """カレンダーにスケジュールをマーク"""
        if not isinstance(self.calendar, QCalendarWidget):
            return
        
        try:
            # カレンダーの書式をリセット
            self.calendar.setDateTextFormat(QDate(), QTextCharFormat())
            
            current_date = QDate.currentDate()
        except Exception as e:
            print(f"カレンダー更新エラー: {e}")
            return
        
        # タスクをマーク
        try:
            for task in self.tasks:
                if task.get('due_date'):
                    date = QDate.fromString(task['due_date'], "yyyy-MM-dd")
                    if date.isValid():
                        format = QTextCharFormat()
                        
                        if date < current_date:
                            format.setBackground(QColor("#b71c1c"))  # 濃い赤（期限切れ）
                            format.setForeground(QColor("white"))
                        elif task.get('priority') == '高':
                            format.setBackground(QColor("#ffcdd2"))  # 薄い赤
                        else:
                            format.setBackground(QColor("#ffebee"))  # とても薄い赤
                        
                        format.setFontWeight(QFont.Weight.Bold)
                        self.calendar.setDateTextFormat(date, format)
        except Exception as e:
            print(f"タスクマーキングエラー: {e}")
        
        # 契約更新をマーク
        try:
            for renewal in self.renewals:
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
                
                # 契約終了日もマーク
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
    
    def on_date_clicked(self, date):
        """日付クリック時の処理"""
        try:
            self.date_selected.emit(date)
        except Exception as e:
            print(f"日付クリック処理エラー: {e}")
    
    def on_month_changed(self):
        """月変更時の処理"""
        self.update_month_label()
        self.update_calendar()
    
    def update_month_label(self):
        """月表示ラベルを更新"""
        if not isinstance(self.calendar, QCalendarWidget):
            self.month_label.setText("カレンダーエラー")
            return
        
        try:
            current_page = self.calendar.monthShown(), self.calendar.yearShown()
            self.month_label.setText(f"{current_page[1]}年{current_page[0]}月")
        except Exception as e:
            print(f"月ラベル更新エラー: {e}")
            self.month_label.setText("月表示エラー")
    
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
        except Exception as e:
            print(f"今日移動エラー: {e}")
    
    def refresh_data(self):
        """データを再読み込み"""
        try:
            self.load_schedule_data()
            self.update_calendar()
        except Exception as e:
            print(f"データ再読み込みエラー: {e}")

class UpcomingScheduleWidget(QWidget):
    """今後のスケジュール一覧"""
    
    def __init__(self):
        super().__init__()
        try:
            self.init_ui()
            self.load_upcoming_items()
        except Exception as e:
            print(f"UpcomingScheduleWidget初期化エラー: {e}")
            self.init_error_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # ヘッダー
        header_layout = QHBoxLayout()
        
        header_label = QLabel("直近のスケジュール")
        header_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["7日以内", "14日以内", "30日以内", "全て"])
        self.filter_combo.setMaximumWidth(100)
        self.filter_combo.currentTextChanged.connect(self.load_upcoming_items)
        
        refresh_btn = QPushButton("更新")
        refresh_btn.setMaximumWidth(60)
        refresh_btn.clicked.connect(self.load_upcoming_items)
        refresh_btn.setStyleSheet("QPushButton { font-size: 10px; padding: 2px; }")
        
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        header_layout.addWidget(self.filter_combo)
        header_layout.addWidget(refresh_btn)
        
        # スケジュールリスト
        self.schedule_list = QListWidget()
        self.schedule_list.setMaximumHeight(200)
        self.schedule_list.setStyleSheet("""
            QListWidget::item {
                padding: 5px;
                margin: 1px;
                border-radius: 3px;
                border: 1px solid #ddd;
                font-size: 11px;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
            }
        """)
        self.schedule_list.itemDoubleClicked.connect(self.show_item_detail)
        
        layout.addLayout(header_layout)
        layout.addWidget(self.schedule_list)
        
        self.setLayout(layout)
    
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
        
        error_label = QLabel("スケジュール表示でエラーが発生しました")
        error_label.setStyleSheet("color: red; font-weight: bold; text-align: center; padding: 20px;")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(error_label)
        self.setLayout(layout)
    
    def load_upcoming_items(self):
        """今後のスケジュールを読み込み"""
        self.schedule_list.clear()
        
        # フィルター日数を取得
        filter_text = self.filter_combo.currentText()
        if filter_text == "7日以内":
            days = 7
        elif filter_text == "14日以内":
            days = 14
        elif filter_text == "30日以内":
            days = 30
        else:
            days = 365  # 全て
        
        current_date = QDate.currentDate()
        end_date = current_date.addDays(days)
        
        # タスクを読み込み
        try:
            from models import Task
            db_tasks = Task.get_pending_tasks()
            tasks = []
            for task in db_tasks:
                if task.get('due_date'):
                    due_date = QDate.fromString(task.get('due_date'), "yyyy-MM-dd")
                    if due_date.isValid():
                        days_until = current_date.daysTo(due_date)
                        
                        # 期限切れタスクも含めて表示（期限切れ30日以内）
                        if days_until <= days and days_until >= -30:
                            tasks.append({
                                'type': 'task',
                                'title': task.get('title', ''),
                                'due_date': task.get('due_date'),
                                'priority': task.get('priority', '中'),
                                'task_type': task.get('task_type', ''),
                                'days_until': days_until,
                                'description': task.get('description', ''),
                                'assigned_to': task.get('assigned_to', '')
                            })
        except Exception:
            # ダミーデータ（フィルター期間に応じて生成）
            tasks = []
            
            # 複数のダミータスクを生成して、フィルター期間内のものだけ追加
            dummy_tasks = [
                {'days': 1, 'title': '家賃請求書送付', 'priority': '高', 'type': '請求', 'assigned': '田中'},
                {'days': 3, 'title': '契約更新案内送付', 'priority': '高', 'type': '更新案内', 'assigned': '佐藤'},
                {'days': -2, 'title': 'エアコン修理手配', 'priority': '高', 'type': '修繕', 'assigned': '山田'},
                {'days': 7, 'title': '入居審査完了', 'priority': '中', 'type': 'その他', 'assigned': '鈴木'},
                {'days': 14, 'title': '設備点検実施', 'priority': '中', 'type': '修繕', 'assigned': '田中'},
                {'days': -7, 'title': '滞納督促連絡', 'priority': '高', 'type': '請求', 'assigned': '佐藤'},
                {'days': 45, 'title': '年次報告書作成', 'priority': '低', 'type': 'その他', 'assigned': '山田'}
            ]
            
            for dummy in dummy_tasks:
                if dummy['days'] <= days and dummy['days'] >= -30:  # フィルター条件に合致
                    tasks.append({
                        'type': 'task',
                        'title': dummy['title'],
                        'due_date': current_date.addDays(dummy['days']).toString("yyyy-MM-dd"),
                        'priority': dummy['priority'],
                        'task_type': dummy['type'],
                        'days_until': dummy['days'],
                        'description': f"{dummy['title']}の詳細説明",
                        'assigned_to': dummy['assigned']
                    })
        
        # 契約更新を読み込み
        try:
            from models import TenantContract
            contracts = TenantContract.get_all()
            renewals = []
            for contract in contracts:
                if contract.get('end_date'):
                    end_date_str = contract.get('end_date')
                    if isinstance(end_date_str, str):
                        contract_end_date = QDate.fromString(end_date_str, "yyyy-MM-dd")
                    else:
                        contract_end_date = QDate(end_date_str)
                    
                    if contract_end_date.isValid():
                        days_until = current_date.daysTo(contract_end_date)
                        
                        # 日数フィルターに基づいて判定
                        # 期限切れも含めて表示するため、負の値も考慮
                        if (days_until <= days and days_until >= -30):  # 期限切れ30日以内も表示
                            renewals.append({
                                'type': 'renewal',
                                'title': f"{contract.get('property_name', '')} {contract.get('room_number', '')}",
                                'tenant_name': contract.get('tenant_name', ''),
                                'end_date': end_date_str,
                                'days_until': days_until,
                                'property_name': contract.get('property_name', ''),
                                'room_number': contract.get('room_number', ''),
                                'rent': contract.get('rent', 0)
                            })
        except Exception:
            # ダミーデータ（フィルター期間に応じて生成）
            renewals = []
            
            # 複数のダミーデータを生成して、フィルター期間内のものだけ追加
            dummy_renewals = [
                {'days': 3, 'name': 'サンプル物件A 101', 'tenant': 'サンプル契約者A', 'rent': 80000},
                {'days': 15, 'name': 'サンプル物件B 202', 'tenant': 'サンプル契約者B', 'rent': 95000},
                {'days': 45, 'name': 'サンプル物件C 301', 'tenant': 'サンプル契約者C', 'rent': 120000},
                {'days': -5, 'name': 'サンプル物件D 102', 'tenant': 'サンプル契約者D', 'rent': 75000},
                {'days': 90, 'name': 'サンプル物件E 203', 'tenant': 'サンプル契約者E', 'rent': 110000}
            ]
            
            for dummy in dummy_renewals:
                if dummy['days'] <= days and dummy['days'] >= -30:  # フィルター条件に合致
                    renewals.append({
                        'type': 'renewal',
                        'title': dummy['name'],
                        'tenant_name': dummy['tenant'],
                        'end_date': current_date.addDays(dummy['days']).toString("yyyy-MM-dd"),
                        'days_until': dummy['days'],
                        'property_name': dummy['name'].split()[0],
                        'room_number': dummy['name'].split()[-1],
                        'rent': dummy['rent']
                    })
        
        # 全てをまとめて日数順にソート
        all_items = tasks + renewals
        all_items.sort(key=lambda x: x['days_until'])
        
        # リストに追加
        for item in all_items:
            list_item = QListWidgetItem()
            
            if item['type'] == 'task':
                if item['days_until'] < 0:
                    icon = "🔴"
                    status = f"期限切れ{abs(item['days_until'])}日"
                    list_item.setBackground(QColor("#ffcdd2"))
                elif item['days_until'] == 0:
                    icon = "🔥"
                    status = "今日期限"
                    list_item.setBackground(QColor("#fff3e0"))
                else:
                    icon = "🔧"
                    status = f"あと{item['days_until']}日"
                    if item['priority'] == '高':
                        list_item.setBackground(QColor("#fff3e0"))
                
                text = f"{icon} [{item['task_type']}] {item['title']}\n    {status}"
            
            elif item['type'] == 'renewal':
                if item['days_until'] < 0:
                    icon = "🔴"
                    status = f"期限切れ{abs(item['days_until'])}日"
                    list_item.setBackground(QColor("#ffcdd2"))
                elif item['days_until'] <= 30:
                    icon = "⏰"
                    status = f"あと{item['days_until']}日で契約終了"
                    list_item.setBackground(QColor("#ffe0b2"))
                else:
                    icon = "🔄"
                    status = f"あと{item['days_until']}日で契約終了"
                
                text = f"{icon} [契約更新] {item['title']}\n    {item['tenant_name']} - {status}"
            
            list_item.setText(text)
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            
            self.schedule_list.addItem(list_item)
        
        if not all_items:
            empty_item = QListWidgetItem("指定期間内にスケジュールはありません")
            empty_item.setForeground(QColor("#666"))
            empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.schedule_list.addItem(empty_item)
    
    def show_item_detail(self, item):
        """アイテム詳細を表示"""
        try:
            data = item.data(Qt.ItemDataRole.UserRole)
            if not data:
                return
            
            if data['type'] == 'task':
                detail = f"【タスク詳細】\n\n"
                detail += f"種別: {data.get('task_type', '未設定')}\n"
                detail += f"タイトル: {data.get('title', '無題')}\n"
                detail += f"期限: {DateHelper.format_date(data.get('due_date'), '%Y年%m月%d日')}\n"
                detail += f"優先度: {data.get('priority', '未設定')}\n"
                
                if data.get('assigned_to'):
                    detail += f"担当者: {data['assigned_to']}\n"
                
                if data.get('description'):
                    detail += f"説明: {data['description']}\n"
                
                days_until = data.get('days_until', 0)
                if days_until < 0:
                    detail += f"\n🔴 {abs(days_until)}日期限切れです！緊急対応が必要です。"
                elif days_until == 0:
                    detail += f"\n🔥 本日が期限です！今日中に完了してください。"
                elif days_until <= 3:
                    detail += f"\n⚠️ あと{days_until}日です。早めの対応をお願いします。"
                else:
                    detail += f"\n📅 あと{days_until}日の余裕があります。"
            
            elif data['type'] == 'renewal':
                detail = f"【契約更新詳細】\n\n"
                detail += f"物件: {data.get('title', '未設定')}\n"
                detail += f"契約者: {data.get('tenant_name', '未設定')}\n"
                detail += f"契約終了日: {DateHelper.format_date(data.get('end_date'), '%Y年%m月%d日')}\n"
                
                if data.get('rent'):
                    detail += f"月額賃料: ¥{data['rent']:,}\n"
                
                days_until = data.get('days_until', 0)
                if days_until < 0:
                    detail += f"\n🔴 契約終了から{abs(days_until)}日経過しています！"
                    detail += f"\n至急、退去手続きや新規契約の対応が必要です。"
                elif days_until == 0:
                    detail += f"\n⏰ 本日契約終了です！"
                    detail += f"\n退去確認や引き渡し作業を完了してください。"
                elif days_until <= 30:
                    detail += f"\n⚠️ あと{days_until}日で契約終了です。"
                    detail += f"\n更新手続きまたは退去準備を進めてください。"
                elif days_until <= 60:
                    detail += f"\n📋 あと{days_until}日で契約終了予定です。"
                    detail += f"\n契約者への更新意向確認を開始してください。"
                else:
                    detail += f"\n📅 契約終了まであと{days_until}日です。"
            
            MessageHelper.show_success(self, detail, "詳細情報")
            
        except Exception as e:
            print(f"詳細表示エラー: {e}")
            MessageHelper.show_error(self, f"詳細表示でエラーが発生しました: {str(e)}")

class EnhancedDashboard(QWidget):
    """拡張ダッシュボード"""
    
    def __init__(self):
        super().__init__()
        try:
            self.init_ui()
            self.setup_auto_refresh()
        except Exception as e:
            print(f"EnhancedDashboard初期化エラー: {e}")
            self.init_error_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # タイトル
        title_label = QLabel("賃貸管理システム ダッシュボード")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 上部：統計とアラート
        top_layout = QHBoxLayout()
        
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
        stats_group.setMaximumWidth(300)
        
        # 重要なアラート
        alert_group = QGroupBox("⚠️ 重要な通知")
        alert_layout = QVBoxLayout()
        
        self.alert_list = QListWidget()
        self.alert_list.setMaximumHeight(120)
        self.alert_list.setStyleSheet("""
            QListWidget::item {
                padding: 3px;
                margin: 1px;
                border-radius: 2px;
                font-size: 11px;
            }
        """)
        
        alert_layout.addWidget(self.alert_list)
        alert_group.setLayout(alert_layout)
        
        top_layout.addWidget(stats_group)
        top_layout.addWidget(alert_group, 1)
        
        # 中央：カレンダーとスケジュール
        main_layout = QHBoxLayout()
        
        # カレンダー
        calendar_group = QGroupBox("📅 スケジュールカレンダー")
        calendar_layout = QVBoxLayout()
        
        self.compact_calendar = CompactCalendarWidget()
        self.compact_calendar.date_selected.connect(self.show_date_schedule)
        
        # 凡例
        legend_layout = QHBoxLayout()
        legend_items = [
            ("🔧 タスク", "#ffebee"),
            ("🔔 更新通知", "#bbdefb"), 
            ("⏰ 契約終了", "#ffe0b2"),
            ("🔴 期限切れ", "#ffcdd2")
        ]
        
        for text, color in legend_items:
            legend_label = QLabel(text)
            legend_label.setStyleSheet(f"background-color: {color}; padding: 2px; font-size: 10px; border-radius: 2px;")
            legend_layout.addWidget(legend_label)
        
        calendar_layout.addWidget(self.compact_calendar)
        calendar_layout.addLayout(legend_layout)
        calendar_group.setLayout(calendar_layout)
        
        # 今後のスケジュール
        schedule_group = QGroupBox("📋 今後のスケジュール")
        schedule_layout = QVBoxLayout()
        
        self.upcoming_schedule = UpcomingScheduleWidget()
        schedule_layout.addWidget(self.upcoming_schedule)
        schedule_group.setLayout(schedule_layout)
        
        main_layout.addWidget(calendar_group)
        main_layout.addWidget(schedule_group)
        
        # 下部：アクションボタン
        action_layout = QHBoxLayout()
        
        refresh_all_btn = QPushButton("全データ更新")
        refresh_all_btn.clicked.connect(self.refresh_all_data)
        refresh_all_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px; }")
        
        calendar_btn = QPushButton("詳細カレンダー")
        calendar_btn.clicked.connect(self.open_detailed_calendar)
        calendar_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 8px; }")
        
        action_layout.addWidget(refresh_all_btn)
        action_layout.addWidget(calendar_btn)
        action_layout.addStretch()
        
        # レイアウト組み立て
        layout.addLayout(top_layout)
        layout.addLayout(main_layout)
        layout.addLayout(action_layout)
        
        self.setLayout(layout)
        
        # 初期データ読み込み
        self.load_stats()
        self.load_alerts()
    
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
        
        error_label = QLabel("ダッシュボードでエラーが発生しました")
        error_label.setStyleSheet("color: red; font-weight: bold; text-align: center; padding: 40px; font-size: 16px;")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        detail_label = QLabel("基本的なシステム情報のみ表示されます")
        detail_label.setStyleSheet("color: #666; text-align: center; padding: 10px;")
        detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(error_label)
        layout.addWidget(detail_label)
        
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
    
    def load_alerts(self):
        """重要なアラートを読み込み"""
        self.alert_list.clear()
        
        current_date = QDate.currentDate()
        alerts = []
        
        # 期限切れタスクを確認
        try:
            from models import Task
            db_tasks = Task.get_pending_tasks()
            overdue_count = 0
            for task in db_tasks:
                if task.get('due_date'):
                    due_date = QDate.fromString(task.get('due_date'), "yyyy-MM-dd")
                    if due_date.isValid() and due_date < current_date:
                        overdue_count += 1
            
            if overdue_count > 0:
                alerts.append(f"🔴 期限切れタスク: {overdue_count}件")
        except Exception:
            pass
        
        # 近日中の契約終了を確認
        try:
            from models import TenantContract
            contracts = TenantContract.get_all()
            expiring_soon = 0
            for contract in contracts:
                if contract.get('end_date'):
                    end_date_str = contract.get('end_date')
                    if isinstance(end_date_str, str):
                        end_date = QDate.fromString(end_date_str, "yyyy-MM-dd")
                    else:
                        end_date = QDate(end_date_str)
                    
                    if end_date.isValid():
                        days_until = current_date.daysTo(end_date)
                        if 0 <= days_until <= 30:
                            expiring_soon += 1
            
            if expiring_soon > 0:
                alerts.append(f"⏰ 30日以内契約終了: {expiring_soon}件")
        except Exception:
            pass
        
        # アラートがない場合
        if not alerts:
            alerts.append("✅ 現在、重要な通知はありません")
        
        # リストに追加
        for alert in alerts:
            list_item = QListWidgetItem(alert)
            if alert.startswith("🔴"):
                list_item.setBackground(QColor("#ffcdd2"))
            elif alert.startswith("⏰"):
                list_item.setBackground(QColor("#fff3e0"))
            else:
                list_item.setBackground(QColor("#e8f5e8"))
            
            self.alert_list.addItem(list_item)
    
    def show_date_schedule(self, date):
        """選択した日のスケジュールを表示"""
        try:
            if not date or not date.isValid():
                MessageHelper.show_warning(self, "無効な日付が選択されました")
                return
            
            try:
                date_str = DateHelper.format_date(date.toPyDate(), "%Y年%m月%d日")
            except:
                date_str = date.toString("yyyy年MM月dd日")
            
            # 選択された日のスケジュールを簡易表示
            selected_date_str = date.toString("yyyy-MM-dd")
            current_date = QDate.currentDate()
            
            schedule_items = []
            
            # タスクをチェック
            for task in self.compact_calendar.tasks:
                if task.get('due_date') == selected_date_str:
                    days_until = current_date.daysTo(date)
                    if days_until < 0:
                        status = f"期限切れ{abs(days_until)}日"
                    elif days_until == 0:
                        status = "本日期限"
                    else:
                        status = f"あと{days_until}日"
                    
                    schedule_items.append(f"🔧 {task.get('task_type', 'タスク')}: {task.get('title', '無題')} ({status})")
            
            # 契約更新をチェック
            for renewal in self.compact_calendar.renewals:
                if renewal.get('notification_date') == selected_date_str:
                    schedule_items.append(f"🔔 契約更新通知: {renewal.get('property_name', '')} {renewal.get('room_number', '')}")
                if renewal.get('end_date') == selected_date_str:
                    schedule_items.append(f"⏰ 契約終了: {renewal.get('property_name', '')} {renewal.get('room_number', '')}")
            
            if schedule_items:
                schedule_text = f"{date_str}のスケジュール:\n\n" + "\n".join(schedule_items)
                schedule_text += f"\n\n詳細は「カレンダー」タブで確認できます。"
                MessageHelper.show_success(self, schedule_text, "スケジュール詳細")
            else:
                MessageHelper.show_success(self, f"{date_str}にはスケジュールがありません。\n詳細カレンダーは「カレンダー」タブで確認できます。", "日付選択")
                
        except Exception as e:
            print(f"日付スケジュール表示エラー: {e}")
            MessageHelper.show_error(self, f"スケジュール表示でエラーが発生しました: {str(e)}")
    
    def open_detailed_calendar(self):
        """詳細カレンダータブを開く"""
        # 親ウィンドウのタブを切り替える
        parent_widget = self.parent()
        while parent_widget and not hasattr(parent_widget, 'tab_widget'):
            parent_widget = parent_widget.parent()
        
        if parent_widget and hasattr(parent_widget, 'tab_widget'):
            # カレンダータブを探して切り替え
            tab_widget = parent_widget.tab_widget
            for i in range(tab_widget.count()):
                if "カレンダー" in tab_widget.tabText(i):
                    tab_widget.setCurrentIndex(i)
                    break
    
    def refresh_all_data(self):
        """全データを更新"""
        try:
            self.load_stats()
            self.load_alerts()
            if hasattr(self, 'compact_calendar'):
                self.compact_calendar.refresh_data()
            if hasattr(self, 'upcoming_schedule'):
                self.upcoming_schedule.load_upcoming_items()
            MessageHelper.show_success(self, "ダッシュボードデータを更新しました")
        except Exception as e:
            print(f"データ更新エラー: {e}")
            MessageHelper.show_error(self, f"データ更新中にエラーが発生しました: {str(e)}")
    
    def setup_auto_refresh(self):
        """自動更新タイマーを設定"""
        try:
            self.refresh_timer = QTimer()
            self.refresh_timer.timeout.connect(self.refresh_all_data)
            self.refresh_timer.start(300000)  # 5分ごとに自動更新
        except Exception as e:
            print(f"自動更新タイマー設定エラー: {e}")