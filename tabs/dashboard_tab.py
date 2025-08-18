"""
ダッシュボード画面 - システム全体の状況を一覧表示
"""
import sys
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QLabel, QTableWidget, QTableWidgetItem, QPushButton,
                             QProgressBar, QFrame, QGridLayout, QScrollArea,
                             QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette
from datetime import datetime, date, timedelta

# プロジェクトルートをPythonパスに追加（tabsフォルダ内のモジュールがルートのモジュールにアクセスできるように）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (Customer, Property, TenantContract, Task, Unit,
                   Document, Communication, ConsistencyCheck, ActivityLog,
                   get_db_connection)
from utils import DateHelper, FormatHelper, StatusColor


class DashboardTab(QWidget):
    """ダッシュボードタブ"""
    
    refresh_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # データベースの状況を確認
        self.check_database_status()
        
        self.load_dashboard_data()
        
        # 自動更新タイマー（5分ごと）
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self.load_dashboard_data)
        self.auto_refresh_timer.start(300000)  # 5分 = 300000ms
    
    def check_database_status(self):
        """データベースの状況を確認"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 各テーブルのレコード数を確認
            tables = ['customers', 'properties', 'units', 'tenant_contracts']
            total_records = 0
            
            for table in tables:
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM {table}')
                    count = cursor.fetchone()[0]
                    total_records += count
                except Exception as e:
                    print(f"テーブル {table} 確認エラー: {str(e)}")
            
            conn.close()
            
            if total_records == 0:
                print("警告: データベースにデータが存在しません")
                print("サンプルデータ作成ボタンを使用してデータを作成してください")
            
        except Exception as e:
            print(f"データベース状況確認エラー: {str(e)}")
    
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
        
        # デバッグボタン（開発用）
        debug_button = QPushButton("デバッグ")
        debug_button.clicked.connect(self.debug_database_status)
        debug_button.setStyleSheet("background-color: #FF9800; color: white; padding: 5px 10px;")
        header_layout.addWidget(debug_button)
        
        # サンプルデータ作成ボタン（テスト用）
        sample_button = QPushButton("サンプルデータ作成")
        sample_button.clicked.connect(self.create_sample_data)
        sample_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px 10px;")
        header_layout.addWidget(sample_button)
        
        # 更新ボタン
        refresh_button = QPushButton("更新")
        refresh_button.clicked.connect(self.load_dashboard_data)
        header_layout.addWidget(refresh_button)
        
        main_layout.addLayout(header_layout)
        
        # 統計情報テーブル
        stats_group = QGroupBox("統計情報")
        stats_layout = QVBoxLayout()
        
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["項目", "値"])
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        self.stats_table.setMaximumHeight(200)
        self.stats_table.setAlternatingRowColors(True)
        
        # 初期データ設定
        stats_items = [
            ("物件数", "0"),
            ("総部屋数", "0"),
            ("入居中", "0"),
            ("空室率", "0%"),
            ("顧客数", "0"),
            ("有効契約", "0")
        ]
        
        self.stats_table.setRowCount(len(stats_items))
        for i, (item, value) in enumerate(stats_items):
            self.stats_table.setItem(i, 0, QTableWidgetItem(item))
            self.stats_table.setItem(i, 1, QTableWidgetItem(value))
            # 項目名を太字に
            item_widget = self.stats_table.item(i, 0)
            font = item_widget.font()
            font.setBold(True)
            item_widget.setFont(font)
        
        stats_layout.addWidget(self.stats_table)
        stats_group.setLayout(stats_layout)
        main_layout.addWidget(stats_group)
        
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
    
    def debug_database_status(self):
        """データベースの状況をデバッグ出力"""
        print("\n=== データベース状況デバッグ ===")
        
        try:
            # 各テーブルのレコード数を確認
            conn = get_db_connection()
            cursor = conn.cursor()
            
            tables = ['customers', 'properties', 'units', 'tenant_contracts', 'tasks', 'communications']
            
            for table in tables:
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM {table}')
                    count = cursor.fetchone()[0]
                    print(f"{table}: {count}件")
                except Exception as e:
                    print(f"{table}: エラー - {str(e)}")
            
            conn.close()
            
        except Exception as e:
            print(f"データベース接続エラー: {str(e)}")
        
        print("=== デバッグ完了 ===\n")
    
    def create_sample_data(self):
        """サンプルデータを作成（テスト用）"""
        try:
            print("サンプルデータ作成開始")
            
            # サンプル物件を作成
            property_id = Property.create(
                name="サンプルマンション",
                address="東京都渋谷区サンプル1-1-1",
                structure="RC造",
                management_type="自社管理"
            )
            print(f"サンプル物件作成: ID={property_id}")
            
            # サンプル部屋を作成
            unit_id = Unit.create(
                property_id=property_id,
                room_number="101",
                floor="1階",
                area=25.0
            )
            print(f"サンプル部屋作成: ID={unit_id}")
            
            # サンプル顧客を作成
            customer_id = Customer.create(
                name="サンプル太郎",
                customer_type="tenant",
                phone="03-1234-5678",
                email="sample@example.com"
            )
            print(f"サンプル顧客作成: ID={customer_id}")
            
            # サンプル契約を作成
            contract_id = TenantContract.create(
                unit_id=unit_id,
                contractor_name="サンプル太郎",
                start_date="2024-01-01",
                end_date="2025-12-31",
                rent=80000,
                maintenance_fee=5000,
                customer_id=customer_id
            )
            print(f"サンプル契約作成: ID={contract_id}")
            
            print("サンプルデータ作成完了")
            
            # データを再読み込み
            self.load_dashboard_data()
            
        except Exception as e:
            print(f"サンプルデータ作成エラー: {str(e)}")
    
    def load_dashboard_data(self):
        """ダッシュボードデータを読み込み"""
        try:
            print("ダッシュボードデータ読み込み開始")
            
            # 最終更新時刻
            self.last_update_label.setText(f"最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
            # 統計情報の収集
            stats_data = {}
            
            # 物件統計
            try:
                properties = Property.get_all()
                print(f"物件データ取得: {len(properties)}件")
                stats_data["物件数"] = f"{len(properties)}件"
            except Exception as e:
                print(f"物件データ取得エラー: {str(e)}")
                stats_data["物件数"] = "0件"
            
            # 部屋統計
            try:
                total_units = 0
                occupied_units = 0
                all_units = Unit.get_all()
                total_units = len(all_units)
                print(f"部屋データ取得: {total_units}件")
                stats_data["総部屋数"] = f"{total_units}室"
            except Exception as e:
                print(f"部屋データ取得エラー: {str(e)}")
                stats_data["総部屋数"] = "0室"
                total_units = 0
            
            # 契約統計
            try:
                contracts = TenantContract.get_all()
                print(f"契約データ取得: {len(contracts)}件")
                
                # 有効契約の判定
                active_contracts = []
                for contract in contracts:
                    end_date = contract.get('end_date')
                    if end_date:
                        try:
                            # 日付文字列を日付オブジェクトに変換
                            if isinstance(end_date, str):
                                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
                            else:
                                end_date_obj = end_date
                            
                            # 今日の日付と比較
                            today = date.today()
                            if end_date_obj >= today:
                                active_contracts.append(contract)
                        except Exception as date_error:
                            print(f"日付変換エラー: {end_date}, {str(date_error)}")
                            # 日付が不正な場合は有効とみなす
                            active_contracts.append(contract)
                    else:
                        # 終了日がない場合は有効とみなす
                        active_contracts.append(contract)
                
                occupied_units = len(active_contracts)
                print(f"有効契約数: {occupied_units}件")
                stats_data["入居中"] = f"{occupied_units}室"
                stats_data["有効契約"] = f"{len(active_contracts)}件"
                
            except Exception as e:
                print(f"契約データ取得エラー: {str(e)}")
                stats_data["入居中"] = "0室"
                stats_data["有効契約"] = "0件"
                occupied_units = 0
            
            # 空室率計算
            try:
                vacancy_rate = 0
                if total_units > 0:
                    vacancy_rate = ((total_units - occupied_units) / total_units) * 100
                
                print(f"空室率計算: {vacancy_rate:.1f}%")
                stats_data["空室率"] = f"{vacancy_rate:.1f}% (空室{total_units - occupied_units}室)"
            except Exception as e:
                print(f"空室率計算エラー: {str(e)}")
                stats_data["空室率"] = "-"
            
            # 顧客統計
            try:
                customers = Customer.get_all()
                print(f"顧客データ取得: {len(customers)}件")
                
                tenants = [c for c in customers if c.get('type') == 'tenant']
                owners = [c for c in customers if c.get('type') == 'owner']
                
                stats_data["顧客数"] = f"{len(customers)}名 (テナント: {len(tenants)} / オーナー: {len(owners)})"
            except Exception as e:
                print(f"顧客データ取得エラー: {str(e)}")
                stats_data["顧客数"] = "0名"
            
            # 統計テーブルを更新
            stats_items = [
                ("物件数", stats_data.get("物件数", "0件")),
                ("総部屋数", stats_data.get("総部屋数", "0室")),
                ("入居中", stats_data.get("入居中", "0室")),
                ("空室率", stats_data.get("空室率", "-")),
                ("顧客数", stats_data.get("顧客数", "0名")),
                ("有効契約", stats_data.get("有効契約", "0件"))
            ]
            
            self.stats_table.setRowCount(len(stats_items))
            for i, (item, value) in enumerate(stats_items):
                self.stats_table.setItem(i, 0, QTableWidgetItem(item))
                self.stats_table.setItem(i, 1, QTableWidgetItem(value))
                # 項目名を太字に
                item_widget = self.stats_table.item(i, 0)
                font = item_widget.font()
                font.setBold(True)
                item_widget.setFont(font)
            
            # アラート読み込み
            try:
                self.load_alerts()
            except Exception as e:
                print(f"アラート読み込みエラー: {str(e)}")
            
            # 契約更新予定読み込み
            try:
                self.load_renewal_contracts()
            except Exception as e:
                print(f"契約更新予定読み込みエラー: {str(e)}")
            
            # 未完了タスク読み込み
            try:
                self.load_pending_tasks()
            except Exception as e:
                print(f"未完了タスク読み込みエラー: {str(e)}")
            
            # 最近の活動読み込み
            try:
                self.load_recent_activities()
            except Exception as e:
                print(f"最近の活動読み込みエラー: {str(e)}")
            
            # 収支サマリー読み込み
            try:
                self.load_income_summary(active_contracts if 'active_contracts' in locals() else [])
            except Exception as e:
                print(f"収支サマリー読み込みエラー: {str(e)}")
            
            print("ダッシュボードデータ読み込み完了")
            
        except Exception as e:
            print(f"ダッシュボードデータ読み込み全体エラー: {str(e)}")
            # エラーが発生した場合でも、カードにエラー表示
            self.total_properties_card.update_value("エラー", "データ取得失敗")
            self.total_units_card.update_value("エラー", "データ取得失敗")
            self.occupied_units_card.update_value("エラー", "データ取得失敗")
            self.vacancy_rate_card.update_value("エラー", "データ取得失敗")
            self.total_customers_card.update_value("エラー", "データ取得失敗")
            self.active_contracts_card.update_value("エラー", "データ取得失敗")
    
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