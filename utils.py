"""
共通ユーティリティモジュール
"""
import re
from datetime import datetime, date
from typing import Optional, Any
from PyQt6.QtWidgets import QTableWidget, QHeaderView, QMessageBox, QWidget
from PyQt6.QtCore import Qt

class Validator:
    """データバリデーションクラス"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """メールアドレスの形式をチェック"""
        if not email:
            return True  # 空の場合はOK（任意項目）
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """電話番号の形式をチェック"""
        if not phone:
            return True  # 空の場合はOK（任意項目）
        # 数字とハイフンのみ、10-11桁
        pattern = r'^[0-9]{2,4}-?[0-9]{2,4}-?[0-9]{3,4}$'
        return re.match(pattern, phone.replace('-', '')) is not None
    
    @staticmethod
    def validate_postal_code(postal_code: str) -> bool:
        """郵便番号の形式をチェック"""
        if not postal_code:
            return True
        pattern = r'^[0-9]{3}-?[0-9]{4}$'
        return re.match(pattern, postal_code) is not None
    
    @staticmethod
    def validate_date_range(start_date: date, end_date: date) -> bool:
        """日付範囲の妥当性をチェック"""
        return start_date <= end_date
    
    @staticmethod
    def validate_required(value: Any, field_name: str) -> tuple[bool, str]:
        """必須項目のチェック"""
        if value is None or (isinstance(value, str) and not value.strip()):
            return False, f"{field_name}は必須項目です"
        return True, ""
    
    @staticmethod
    def validate_positive_number(value: Any, field_name: str) -> tuple[bool, str]:
        """正の数値チェック"""
        try:
            num = float(value) if value else 0
            if num < 0:
                return False, f"{field_name}は0以上の値を入力してください"
            return True, ""
        except (ValueError, TypeError):
            return False, f"{field_name}は数値を入力してください"

class TableHelper:
    """テーブル操作のヘルパークラス"""
    
    @staticmethod
    def setup_table(table: QTableWidget, stretch_columns: list = None):
        """テーブルの初期設定"""
        # ヘッダーの伸縮設定
        header = table.horizontalHeader()
        if stretch_columns:
            for col in stretch_columns:
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        else:
            header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        # 行選択モード
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # 交互の行色
        table.setAlternatingRowColors(True)
        
        # ソート有効化
        table.setSortingEnabled(True)
    
    @staticmethod
    def get_selected_row_data(table: QTableWidget, column_index: int) -> Optional[Any]:
        """選択された行の特定列のデータを取得"""
        current_row = table.currentRow()
        if current_row >= 0:
            item = table.item(current_row, column_index)
            return item.text() if item else None
        return None
    
    @staticmethod
    def get_selected_row_id(table: QTableWidget) -> Optional[int]:
        """選択された行のID（第1列）を取得"""
        id_text = TableHelper.get_selected_row_data(table, 0)
        return int(id_text) if id_text else None
    
    @staticmethod
    def clear_table(table: QTableWidget):
        """テーブルをクリア"""
        table.setRowCount(0)
    
    @staticmethod
    def add_row_with_color(table: QTableWidget, row_data: list, color: str = None):
        """色付きで行を追加"""
        row_position = table.rowCount()
        table.insertRow(row_position)
        
        for col, data in enumerate(row_data):
            item = QTableWidget(str(data) if data is not None else "")
            if color:
                item.setBackground(Qt.GlobalColor.__dict__.get(color, Qt.GlobalColor.white))
            table.setItem(row_position, col, item)

class DateHelper:
    """日付操作のヘルパークラス"""
    
    @staticmethod
    def format_date(date_obj: Any, format_str: str = "%Y年%m月%d日") -> str:
        """日付を指定形式でフォーマット"""
        if not date_obj:
            return ""
        
        if isinstance(date_obj, str):
            try:
                date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
            except:
                return date_obj
        
        if isinstance(date_obj, (date, datetime)):
            return date_obj.strftime(format_str)
        
        return str(date_obj)
    
    @staticmethod
    def days_until(target_date: Any) -> Optional[int]:
        """指定日までの日数を計算"""
        if not target_date:
            return None
        
        if isinstance(target_date, str):
            try:
                target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
            except:
                return None
        
        if isinstance(target_date, datetime):
            target_date = target_date.date()
        
        today = date.today()
        delta = target_date - today
        return delta.days
    
    @staticmethod
    def is_expired(target_date: Any) -> bool:
        """期限切れかチェック"""
        days = DateHelper.days_until(target_date)
        return days is not None and days < 0
    
    @staticmethod
    def is_near_expiry(target_date: Any, threshold_days: int = 30) -> bool:
        """期限が近いかチェック"""
        days = DateHelper.days_until(target_date)
        return days is not None and 0 <= days <= threshold_days

class MessageHelper:
    """メッセージ表示のヘルパークラス"""
    
    @staticmethod
    def show_success(parent: QWidget, message: str, title: str = "成功"):
        """成功メッセージを表示"""
        QMessageBox.information(parent, title, message)
    
    @staticmethod
    def show_error(parent: QWidget, message: str, title: str = "エラー"):
        """エラーメッセージを表示"""
        QMessageBox.critical(parent, title, message)
    
    @staticmethod
    def show_warning(parent: QWidget, message: str, title: str = "警告"):
        """警告メッセージを表示"""
        QMessageBox.warning(parent, title, message)
    
    @staticmethod
    def confirm(parent: QWidget, message: str, title: str = "確認") -> bool:
        """確認ダイアログを表示"""
        reply = QMessageBox.question(parent, title, message,
                                    QMessageBox.StandardButton.Yes | 
                                    QMessageBox.StandardButton.No)
        return reply == QMessageBox.StandardButton.Yes
    
    @staticmethod
    def confirm_delete(parent: QWidget, item_name: str = "このデータ") -> bool:
        """削除確認ダイアログを表示"""
        message = f"{item_name}を削除してもよろしいですか？\nこの操作は取り消せません。"
        return MessageHelper.confirm(parent, message, "削除確認")

class FormatHelper:
    """フォーマット用ヘルパークラス"""
    
    @staticmethod
    def format_currency(amount: Any) -> str:
        """金額を通貨形式でフォーマット"""
        if amount is None:
            return "¥0"
        try:
            amount = int(amount)
            return f"¥{amount:,}"
        except (ValueError, TypeError):
            return "¥0"
    
    @staticmethod
    def format_area(area: Any) -> str:
        """面積をフォーマット"""
        if area is None:
            return "0㎡"
        try:
            area = float(area)
            return f"{area:.2f}㎡"
        except (ValueError, TypeError):
            return "0㎡"
    
    @staticmethod
    def format_percentage(value: Any) -> str:
        """パーセンテージ形式でフォーマット"""
        if value is None:
            return "0%"
        try:
            value = float(value)
            return f"{value:.1f}%"
        except (ValueError, TypeError):
            return "0%"
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 50) -> str:
        """長いテキストを省略"""
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."
    
    @staticmethod
    def format_phone(phone: str) -> str:
        """電話番号をフォーマット"""
        if not phone:
            return ""
        # 数字のみ抽出
        numbers = re.sub(r'\D', '', phone)
        if len(numbers) == 10:  # 03-1234-5678
            return f"{numbers[:2]}-{numbers[2:6]}-{numbers[6:]}"
        elif len(numbers) == 11:  # 090-1234-5678
            return f"{numbers[:3]}-{numbers[3:7]}-{numbers[7:]}"
        return phone
    
    @staticmethod
    def format_postal_code(postal_code: str) -> str:
        """郵便番号をフォーマット"""
        if not postal_code:
            return ""
        # 数字のみ抽出
        numbers = re.sub(r'\D', '', postal_code)
        if len(numbers) == 7:
            return f"{numbers[:3]}-{numbers[3:]}"
        return postal_code

class SearchHelper:
    """検索機能のヘルパークラス"""
    
    @staticmethod
    def filter_table(table: QTableWidget, search_text: str, columns: list = None):
        """テーブルの行をフィルタリング"""
        if not search_text:
            # 検索文字列が空の場合は全行表示
            for row in range(table.rowCount()):
                table.setRowHidden(row, False)
            return
        
        search_text = search_text.lower()
        
        # 検索対象の列を決定
        if columns is None:
            columns = range(table.columnCount())
        
        # 各行をチェック
        for row in range(table.rowCount()):
            row_match = False
            for col in columns:
                item = table.item(row, col)
                if item and search_text in item.text().lower():
                    row_match = True
                    break
            table.setRowHidden(row, not row_match)
    
    @staticmethod
    def highlight_search_results(table: QTableWidget, search_text: str, columns: list = None):
        """検索結果をハイライト"""
        if not search_text:
            return
        
        search_text = search_text.lower()
        
        # 検索対象の列を決定
        if columns is None:
            columns = range(table.columnCount())
        
        # 各セルをチェックしてハイライト
        for row in range(table.rowCount()):
            for col in columns:
                item = table.item(row, col)
                if item and search_text in item.text().lower():
                    item.setBackground(Qt.GlobalColor.yellow)
                elif item:
                    item.setBackground(Qt.GlobalColor.transparent)

class StatusColor:
    """ステータスに応じた色定義"""
    
    # 契約状態
    ACTIVE = "#90EE90"  # 薄緑
    EXPIRING = "#FFD700"  # 金色
    EXPIRED = "#FFB6C1"  # 薄赤
    
    # タスク優先度
    HIGH_PRIORITY = "#FF6B6B"  # 赤
    NORMAL_PRIORITY = "#4ECDC4"  # 青緑
    LOW_PRIORITY = "#95E1D3"  # 薄緑
    
    # 一般ステータス
    COMPLETED = "#90EE90"  # 薄緑
    IN_PROGRESS = "#87CEEB"  # スカイブルー
    PENDING = "#F0E68C"  # カーキ
    
    @staticmethod
    def get_contract_status_color(end_date: Any) -> str:
        """契約終了日に基づいて色を返す"""
        if DateHelper.is_expired(end_date):
            return StatusColor.EXPIRED
        elif DateHelper.is_near_expiry(end_date, 60):
            return StatusColor.EXPIRING
        else:
            return StatusColor.ACTIVE
    
    @staticmethod
    def get_task_priority_color(priority: str) -> str:
        """タスク優先度に基づいて色を返す"""
        priority_map = {
            'high': StatusColor.HIGH_PRIORITY,
            'normal': StatusColor.NORMAL_PRIORITY,
            'low': StatusColor.LOW_PRIORITY
        }
        return priority_map.get(priority, StatusColor.NORMAL_PRIORITY)