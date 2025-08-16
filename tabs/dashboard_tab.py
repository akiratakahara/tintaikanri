"""
ダッシュボード画面 - システム全体の状況を一覧表示
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QTableWidget, QTableWidgetItem, QPushButton,
                             QProgressBar, QFrame, QGridLayout, QScrollArea,
                             QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette
from datetime import datetime, date, timedelta
from models import (Customer, Property, TenantContract, Task, Unit,
                   Document, Communication, ConsistencyCheck, ActivityLog)
from utils import DateHelper, FormatHelper, StatusColor

class StatCard(QFrame):
    """統計カード"""
    
    def __init__(self, title: str, value: str, sub_text: str = "", color: str = "#2196F3"):
        super().__init__()
        self.color = color
        self.init_ui(title, value, sub_text, color)
    
    def init_ui(self, title, value, sub_text, color):
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {color};
                border-radius: 10px;
                background-color: white;
                padding: 16px;
                min-width: 250px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # タイトル
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 14px;")
        
        # 値
        self.value_label = QLabel(value)
        self.value_label.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setWordWrap(True)  # 長いテキストの折り返し
        
        # サブテキスト
        self.sub_label = QLabel(sub_text)
        self.sub_label.setStyleSheet("color: gray; font-size: 12px;")
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sub_label.setWordWrap(True)  # 長いテキストの折り返し
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.sub_label)
        
        self.setLayout(layout)
        self.setMinimumWidth(250)  # 最小幅を250pxに増加
        self.setMaximumHeight(160)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    
    def update_value(self, value: str, sub_text: str = "", color: str = None):
        """カードの値を更新"""
        self.value_label.setText(value)
        self.sub_label.setText(sub_text)
        
        if color and color != self.color:
            self.color = color
            self.setStyleSheet(f"""
                QFrame {{
                    border: 2px solid {color};
                    border-radius: 10px;
                    background-color: white;
                    padding: 16px;
                    min-width: 250px;
                }}
            """)
            self.title_label.setStyleSheet(f"color: {color}; font-weight: bold;")

class DashboardTab(QWidget):
    """ダッシュボードタブ"""
    
    refresh_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_dashboard_data()
        
        # 自動更新タイマー（5分ごと）
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self.load_dashboard_data)
        self.auto_refresh_timer.start(300000)  # 5分 = 300000ms
    
    def init_ui(self):
        # スクロールエリア
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # ヘッダー
        header_layout = QHBoxLayout()
        
        title_label = QLabel("ダッシュボード")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        # 最終更新時刻
        self.last_update_label = QLabel()
        self.last_update_label.setStyleSheet("color: gray;")
        header_layout.addWidget(self.last_update_label)
        
        header_layout.addStretch()
        
        # 更新ボタン
        refresh_button = QPushButton("更新")
        refresh_button.clicked.connect(self.load_dashboard_data)
        header_layout.addWidget(refresh_button)
        
        main_layout.addLayout(header_layout)
        
        # 統計カードエリア
        stats_layout = QGridLayout()
        stats_layout.setSpacing(20)  # カード間のスペーシングを増加
        
        # 統計カード
        self.total_properties_card = StatCard("物件数", "0", "", "#2196F3")
        self.total_units_card = StatCard("総部屋数", "0", "", "#4CAF50")
        self.occupied_units_card = StatCard("入居中", "0", "", "#FF9800")
        self.vacancy_rate_card = StatCard("空室率", "0%", "", "#f44336")
        self.total_customers_card = StatCard("顧客数", "0", "", "#9C27B0")
        self.active_contracts_card = StatCard("有効契約", "0", "", "#00BCD4")
        
        # グリッドレイアウトに追加（2行3列のレイアウトに変更）
        stats_layout.addWidget(self.total_properties_card, 0, 0)
        stats_layout.addWidget(self.total_units_card, 0, 1)
        stats_layout.addWidget(self.occupied_units_card, 0, 2)
        stats_layout.addWidget(self.vacancy_rate_card, 1, 0)
        stats_layout.addWidget(self.total_customers_card, 1, 1)
        stats_layout.addWidget(self.active_contracts_card, 1, 2)
        
        # 列の伸縮設定（3列に変更）
        for i in range(3):
            stats_layout.setColumnStretch(i, 1)
        
        main_layout.addLayout(stats_layout)
        
        # 区切り線
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line1)
        
        # アラートエリア
        alert_group = QGroupBox("重要なお知らせ")
        alert_layout = QVBoxLayout()
        
        self.alert_list = QTableWidget()
        self.alert_list.setColumnCount(4)
        self.alert_list.setHorizontalHeaderLabels(["種別", "内容", "期限", "アクション"])
        self.alert_list.horizontalHeader().setStretchLastSection(True)
        self.alert_list.setMaximumHeight(200)
        
        alert_layout.addWidget(self.alert_list)
        alert_group.setLayout(alert_layout)
        main_layout.addWidget(alert_group)
        
        # 契約更新予定
        renewal_group = QGroupBox("契約更新予定（60日以内）")
        renewal_layout = QVBoxLayout()
        
        self.renewal_table = QTableWidget()
        self.renewal_table.setColumnCount(6)
        self.renewal_table.setHorizontalHeaderLabels([
            "物件名", "部屋番号", "契約者", "契約終了日", "残日数", "状態"
        ])
        self.renewal_table.horizontalHeader().setStretchLastSection(True)
        self.renewal_table.setMaximumHeight(250)
        
        renewal_layout.addWidget(self.renewal_table)
        renewal_group.setLayout(renewal_layout)
        main_layout.addWidget(renewal_group)
        
        # 未完了タスク
        task_group = QGroupBox("未完了タスク")
        task_layout = QVBoxLayout()
        
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(5)
        self.task_table.setHorizontalHeaderLabels([
            "タスク", "物件", "期限", "優先度", "担当者"
        ])
        self.task_table.horizontalHeader().setStretchLastSection(True)
        self.task_table.setMaximumHeight(250)
        
        task_layout.addWidget(self.task_table)
        task_group.setLayout(task_layout)
        main_layout.addWidget(task_group)
        
        # 最近の活動
        activity_group = QGroupBox("最近の活動")
        activity_layout = QVBoxLayout()
        
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(4)
        self.activity_table.setHorizontalHeaderLabels([
            "日時", "種別", "内容", "関連"
        ])
        self.activity_table.horizontalHeader().setStretchLastSection(True)
        self.activity_table.setMaximumHeight(250)
        
        activity_layout.addWidget(self.activity_table)
        activity_group.setLayout(activity_layout)
        main_layout.addWidget(activity_group)
        
        # 収支サマリー
        income_group = QGroupBox("今月の収支サマリー")
        income_layout = QGridLayout()
        
        self.total_income_label = QLabel("収入: ¥0")
        self.total_income_label.setFont(QFont("Arial", 14))
        self.expected_income_label = QLabel("予定収入: ¥0")
        self.occupancy_progress = QProgressBar()
        self.occupancy_progress.setFormat("入居率: %p%")
        
        income_layout.addWidget(self.total_income_label, 0, 0)
        income_layout.addWidget(self.expected_income_label, 0, 1)
        income_layout.addWidget(QLabel("入居率:"), 1, 0)
        income_layout.addWidget(self.occupancy_progress, 1, 1)
        
        income_group.setLayout(income_layout)
        main_layout.addWidget(income_group)
        
        # スクロールエリアの設定
        scroll_widget.setLayout(main_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        # メインレイアウト
        layout = QVBoxLayout()
        layout.addWidget(scroll_area)
        self.setLayout(layout)
    
    def load_dashboard_data(self):
        """ダッシュボードデータを読み込み"""
        try:
            # 最終更新時刻
            self.last_update_label.setText(f"最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
            # 物件統計
            properties = Property.get_all()
            self.total_properties_card.update_value(str(len(properties)))
            
            # 部屋統計
            total_units = 0
            occupied_units = 0
            all_units = Unit.get_all()
            total_units = len(all_units)
            
            # 契約統計
            contracts = TenantContract.get_all()
            active_contracts = [c for c in contracts if not DateHelper.is_expired(c.get('end_date'))]
            occupied_units = len(active_contracts)
            
            self.total_units_card.update_value(str(total_units))
            self.occupied_units_card.update_value(str(occupied_units))
            
            # 空室率計算
            vacancy_rate = 0
            if total_units > 0:
                vacancy_rate = ((total_units - occupied_units) / total_units) * 100
            
            color = "#4CAF50" if vacancy_rate < 10 else "#FF9800" if vacancy_rate < 20 else "#f44336"
            self.vacancy_rate_card.update_value(f"{vacancy_rate:.1f}%", color=color)
            
            # 顧客統計
            customers = Customer.get_all()
            tenants = [c for c in customers if c.get('type') == 'tenant']
            owners = [c for c in customers if c.get('type') == 'owner']
            
            self.total_customers_card.update_value(
                str(len(customers)),
                sub_text=f"テナント: {len(tenants)} / オーナー: {len(owners)}"
            )
            
            self.active_contracts_card.update_value(str(len(active_contracts)))
            
            # アラート読み込み
            self.load_alerts()
            
            # 契約更新予定読み込み
            self.load_renewal_contracts()
            
            # 未完了タスク読み込み
            self.load_pending_tasks()
            
            # 最近の活動読み込み
            self.load_recent_activities()
            
            # 収支サマリー読み込み
            self.load_income_summary(active_contracts)
            
        except Exception as e:
            print(f"ダッシュボードデータ読み込みエラー: {str(e)}")
    
    def load_alerts(self):
        """アラートを読み込み"""
        self.alert_list.setRowCount(0)
        
        # 期限切れ契約
        contracts = TenantContract.get_all()
        for contract in contracts:
            if DateHelper.is_expired(contract.get('end_date')):
                row = self.alert_list.rowCount()
                self.alert_list.insertRow(row)
                self.alert_list.setItem(row, 0, QTableWidgetItem("契約期限切れ"))
                self.alert_list.setItem(row, 1, QTableWidgetItem(
                    f"{contract.get('property_name', '')} - {contract.get('room_number', '')}"
                ))
                self.alert_list.setItem(row, 2, QTableWidgetItem(
                    DateHelper.format_date(contract.get('end_date'))
                ))
                self.alert_list.setItem(row, 3, QTableWidgetItem("要対応"))
                
                # 行を赤色に
                for col in range(4):
                    item = self.alert_list.item(row, col)
                    if item:
                        item.setBackground(QColor("#FFEBEE"))
        
        # 期限切れタスク
        tasks = Task.get_pending_tasks()
        for task in tasks:
            if DateHelper.is_expired(task.get('due_date')):
                row = self.alert_list.rowCount()
                self.alert_list.insertRow(row)
                self.alert_list.setItem(row, 0, QTableWidgetItem("タスク期限切れ"))
                self.alert_list.setItem(row, 1, QTableWidgetItem(task.get('title', '')))
                self.alert_list.setItem(row, 2, QTableWidgetItem(
                    DateHelper.format_date(task.get('due_date'))
                ))
                self.alert_list.setItem(row, 3, QTableWidgetItem("要対応"))
                
                # 行を黄色に
                for col in range(4):
                    item = self.alert_list.item(row, col)
                    if item:
                        item.setBackground(QColor("#FFF9C4"))
    
    def load_renewal_contracts(self):
        """契約更新予定を読み込み"""
        self.renewal_table.setRowCount(0)
        
        contracts = TenantContract.get_expiring_contracts(60)
        for contract in contracts:
            row = self.renewal_table.rowCount()
            self.renewal_table.insertRow(row)
            
            self.renewal_table.setItem(row, 0, QTableWidgetItem(contract.get('property_name', '')))
            self.renewal_table.setItem(row, 1, QTableWidgetItem(contract.get('room_number', '')))
            self.renewal_table.setItem(row, 2, QTableWidgetItem(contract.get('contractor_name', '')))
            self.renewal_table.setItem(row, 3, QTableWidgetItem(
                DateHelper.format_date(contract.get('end_date'))
            ))
            
            # 残日数
            days = DateHelper.days_until(contract.get('end_date'))
            days_item = QTableWidgetItem(f"{days}日" if days else "期限切れ")
            if days and days <= 30:
                days_item.setForeground(QColor("red"))
            elif days and days <= 60:
                days_item.setForeground(QColor("orange"))
            self.renewal_table.setItem(row, 4, days_item)
            
            # 状態
            status = "期限切れ" if days and days < 0 else "要更新" if days and days <= 30 else "予定"
            status_item = QTableWidgetItem(status)
            if status == "期限切れ":
                status_item.setBackground(QColor("#FFCDD2"))
            elif status == "要更新":
                status_item.setBackground(QColor("#FFE0B2"))
            self.renewal_table.setItem(row, 5, status_item)
    
    def load_pending_tasks(self):
        """未完了タスクを読み込み"""
        self.task_table.setRowCount(0)
        
        tasks = Task.get_pending_tasks()
        for task in tasks[:10]:  # 最大10件表示
            row = self.task_table.rowCount()
            self.task_table.insertRow(row)
            
            self.task_table.setItem(row, 0, QTableWidgetItem(task.get('title', '')))
            self.task_table.setItem(row, 1, QTableWidgetItem(
                f"{task.get('property_name', '')} - {task.get('room_number', '')}"
            ))
            self.task_table.setItem(row, 2, QTableWidgetItem(
                DateHelper.format_date(task.get('due_date'))
            ))
            
            # 優先度
            priority = task.get('priority', 'normal')
            priority_item = QTableWidgetItem(
                "高" if priority == 'high' else "中" if priority == 'normal' else "低"
            )
            color = StatusColor.get_task_priority_color(priority)
            priority_item.setBackground(QColor(color))
            self.task_table.setItem(row, 3, priority_item)
            
            self.task_table.setItem(row, 4, QTableWidgetItem(task.get('assigned_to', '')))
    
    def load_recent_activities(self):
        """最近の活動を読み込み"""
        self.activity_table.setRowCount(0)
        
        try:
            # 最近のアクティビティログを取得
            activities = ActivityLog.get_recent(limit=20)
            
            # テーブルに追加
            for activity in activities[:10]:  # 最大10件表示
                row = self.activity_table.rowCount()
                self.activity_table.insertRow(row)
                
                # 日時
                created_at = activity.get('created_at', '')
                if created_at:
                    try:
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        formatted_date = dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        formatted_date = created_at[:16] if len(created_at) >= 16 else created_at
                else:
                    formatted_date = ''
                    
                self.activity_table.setItem(row, 0, QTableWidgetItem(formatted_date))
                
                # 種別（アクティビティタイプを日本語に変換）
                activity_type = activity.get('activity_type', '')
                type_map = {
                    'CREATE': '新規登録',
                    'UPDATE': '更新',
                    'DELETE': '削除',
                    'VIEW': '閲覧',
                    'LOGIN': 'ログイン',
                    'COMPLETE': '完了'
                }
                type_display = type_map.get(activity_type, activity_type)
                self.activity_table.setItem(row, 1, QTableWidgetItem(type_display))
                
                # 内容
                description = activity.get('description', '')
                if not description:
                    # descriptionがない場合は自動生成
                    entity_type = activity.get('entity_type', '')
                    entity_name = activity.get('entity_name', '')
                    type_name_map = {
                        'customer': '顧客',
                        'property': '物件',
                        'contract': '契約',
                        'task': 'タスク',
                        'document': '書類',
                        'communication': '接点履歴'
                    }
                    entity_display = type_name_map.get(entity_type, entity_type)
                    if entity_name:
                        description = f'{entity_display}「{entity_name}」を{type_display}'
                    else:
                        description = f'{entity_display}を{type_display}'
                
                self.activity_table.setItem(row, 2, QTableWidgetItem(
                    FormatHelper.truncate_text(description, 40)
                ))
                
                # 関連（エンティティ名）
                entity_name = activity.get('entity_name', '')
                self.activity_table.setItem(row, 3, QTableWidgetItem(entity_name))
                
        except Exception as e:
            print(f"最近の活動読み込みエラー: {str(e)}")
    
    def load_income_summary(self, active_contracts):
        """収支サマリーを読み込み"""
        try:
            # 今月の収入計算
            total_income = 0
            expected_income = 0
            
            for contract in active_contracts:
                rent = contract.get('rent', 0) or 0
                maintenance = contract.get('maintenance_fee', 0) or 0
                expected_income += (rent + maintenance)
                
                # 実際の収入（簡略化のため、有効契約はすべて支払済みと仮定）
                if not DateHelper.is_expired(contract.get('end_date')):
                    total_income += (rent + maintenance)
            
            self.total_income_label.setText(f"収入: {FormatHelper.format_currency(total_income)}")
            self.expected_income_label.setText(f"予定収入: {FormatHelper.format_currency(expected_income)}")
            
            # 入居率
            all_units = Unit.get_all()
            occupancy_rate = 0
            if len(all_units) > 0:
                occupancy_rate = (len(active_contracts) / len(all_units)) * 100
            
            self.occupancy_progress.setValue(int(occupancy_rate))
            
        except Exception as e:
            print(f"収支サマリー読み込みエラー: {str(e)}")