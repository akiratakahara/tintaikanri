# 契約手続きログクラス（新規）
class ContractProcedureLog:
    @staticmethod
    def create(contract_id: int, procedure_type: str, procedure_date: str = None,
               deadline_date: str = None, status: str = 'pending', notes: str = None) -> int:
        """契約手続きログを作成し、同時にタスクも生成"""
        from models import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 手続きログを作成
            cursor.execute('''
                INSERT INTO contract_procedure_logs (contract_id, procedure_type, procedure_date,
                                                   deadline_date, status, note)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (contract_id, procedure_type, procedure_date, deadline_date, status, notes))
            log_id = cursor.lastrowid
            
            # 手続きに対応するタスクを自動生成
            if deadline_date:
                task_title = f"{procedure_type} - 手続き対応"
                task_description = f"契約手続き「{procedure_type}」の対応が必要です。"
                if notes:
                    task_description += f"\n備考: {notes}"
                
                # 優先度を期限から判定
                from datetime import datetime, date
                try:
                    deadline = datetime.strptime(deadline_date, '%Y-%m-%d').date()
                    today = date.today()
                    days_diff = (deadline - today).days
                    
                    if days_diff <= 3:
                        priority = '高'
                    elif days_diff <= 7:
                        priority = '中'
                    else:
                        priority = '低'
                except:
                    priority = '中'
                
                # タスクを作成
                cursor.execute('''
                    INSERT INTO tasks (contract_id, task_type, title, description, due_date, priority, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (contract_id, '手続き', task_title, task_description, deadline_date, priority, '未完了'))
            
            conn.commit()
            conn.close()
            return log_id
            
        except Exception as e:
            conn.rollback()
            conn.close()
            raise e
    
    @staticmethod
    def get_by_contract(contract_id: int):
        """契約IDに基づく手続きログ一覧を取得"""
        from models import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT cpl.*, tc.contractor_name, p.name as property_name, u.room_number
            FROM contract_procedure_logs cpl
            LEFT JOIN tenant_contracts tc ON cpl.contract_id = tc.id
            LEFT JOIN units u ON tc.unit_id = u.id
            LEFT JOIN properties p ON u.property_id = p.id
            WHERE cpl.contract_id = ?
            ORDER BY cpl.deadline_date ASC, cpl.created_at DESC
        ''', (contract_id,))
        logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return logs
    
    @staticmethod
    def get_all():
        """全ての手続きログを取得"""
        from models import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT cpl.*, tc.contractor_name, p.name as property_name, u.room_number
            FROM contract_procedure_logs cpl
            LEFT JOIN tenant_contracts tc ON cpl.contract_id = tc.id
            LEFT JOIN units u ON tc.unit_id = u.id
            LEFT JOIN properties p ON u.property_id = p.id
            ORDER BY cpl.deadline_date ASC, cpl.created_at DESC
        ''')
        logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return logs
    
    @staticmethod
    def get_pending_procedures():
        """未処理の手続きログを取得"""
        from models import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT cpl.*, tc.contractor_name, p.name as property_name, u.room_number
            FROM contract_procedure_logs cpl
            LEFT JOIN tenant_contracts tc ON cpl.contract_id = tc.id
            LEFT JOIN units u ON tc.unit_id = u.id
            LEFT JOIN properties p ON u.property_id = p.id
            WHERE cpl.status IN ('pending', 'in_progress')
            ORDER BY cpl.deadline_date ASC
        ''')
        logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return logs
    
    @staticmethod
    def update_status(log_id: int, status: str, notes: str = None):
        """手続きログのステータスを更新"""
        from models import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        update_fields = ['status = ?']
        params = [status]
        
        if notes is not None:
            update_fields.append('note = ?')
            params.append(notes)
        
        params.append(log_id)
        
        cursor.execute(f'''
            UPDATE contract_procedure_logs 
            SET {', '.join(update_fields)}
            WHERE id = ?
        ''', params)
        
        # ステータスが完了になった場合、関連タスクも完了にする
        if status == 'completed':
            cursor.execute('''
                UPDATE tasks SET status = '完了'
                WHERE contract_id = (
                    SELECT contract_id FROM contract_procedure_logs WHERE id = ?
                ) AND task_type = '手続き' AND status = '未完了'
            ''', (log_id,))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_calendar_events(start_date: str, end_date: str):
        """カレンダー表示用の手続きイベントを取得"""
        from models import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                cpl.id,
                cpl.procedure_type as title,
                cpl.deadline_date as date,
                cpl.status,
                cpl.note as notes,
                'procedure' as event_type,
                tc.contractor_name,
                p.name as property_name,
                u.room_number,
                CASE 
                    WHEN cpl.status = 'pending' THEN '#f59e0b'
                    WHEN cpl.status = 'in_progress' THEN '#3b82f6'
                    WHEN cpl.status = 'completed' THEN '#10b981'
                    ELSE '#6b7280'
                END as color
            FROM contract_procedure_logs cpl
            LEFT JOIN tenant_contracts tc ON cpl.contract_id = tc.id
            LEFT JOIN units u ON tc.unit_id = u.id
            LEFT JOIN properties p ON u.property_id = p.id
            WHERE cpl.deadline_date BETWEEN ? AND ?
            ORDER BY cpl.deadline_date ASC
        ''', (start_date, end_date))
        events = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return events