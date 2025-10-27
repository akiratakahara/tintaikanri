import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any
from enum import Enum
from pathlib import Path

# データベースファイルの保存場所をユーザーのドキュメントフォルダに設定
def get_data_directory():
    """アプリケーションのデータディレクトリを取得（ユーザーのドキュメントフォルダ内）"""
    # ユーザーのドキュメントフォルダを取得
    if os.name == 'nt':  # Windows
        documents = Path(os.path.expanduser("~")) / "Documents"
    else:  # Mac/Linux
        documents = Path(os.path.expanduser("~")) / "Documents"

    # アプリケーション専用フォルダを作成
    app_data_dir = documents / "賃貸管理システム"
    app_data_dir.mkdir(parents=True, exist_ok=True)

    # 書類保存用のサブフォルダも作成
    (app_data_dir / "property_documents").mkdir(exist_ok=True)
    (app_data_dir / "contract_documents").mkdir(exist_ok=True)

    return app_data_dir

# データベースファイルのパス
DATA_DIR = get_data_directory()
DATABASE_FILE = str(DATA_DIR / "tintai_management.db")

# Document Type の定義
class DocumentType(str, Enum):
    CONTRACT = "contract"              # 契約書（定期・普通含む）
    EXPLANATION = "explanation"        # 重要事項説明書
    REGISTRY = "registry"              # 登記簿謄本（建物・土地）
    APPLICATION = "application"        # 申込書
    ESTIMATE = "estimate"              # リフォーム等の見積書
    KEY_RECEIPT = "key_receipt"        # 鍵の預り証
    EMAIL_LOG = "email_log"            # メール履歴（txtなど）
    GOVERNMENT_DOC = "government_doc"  # 都市計画・用途地域資料
    OTHERS = "others"

def get_db_connection():
    """データベース接続を取得"""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row  # 辞書形式でアクセス可能にする
    return conn

def create_tables():
    """テーブルを作成"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 顧客テーブル（拡張版）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT DEFAULT 'tenant',  -- 'owner' or 'tenant'
            phone TEXT,
            email TEXT,
            address TEXT,
            memo TEXT,                   -- メモ
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # オーナープロフィールテーブル（新規）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS owner_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            is_landowner BOOLEAN DEFAULT 1,      -- 土地所有者フラグ
            has_decision_authority BOOLEAN DEFAULT 1,  -- 決定権限フラグ
            title TEXT,                          -- 役職
            bank_account TEXT,                   -- 銀行口座
            commission_rate REAL,                -- 手数料率
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    ''')
    
    # テナントプロフィールテーブル（新規）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tenant_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            industry TEXT,                       -- 業種
            guarantor_company TEXT,              -- 保証会社
            emergency_contact TEXT,              -- 緊急連絡先
            submitted_documents TEXT,            -- 提出書類（JSON形式）
            last_contact_date DATE,              -- 最終接触日
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    ''')
    
    # 物件テーブル（基本情報）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            structure TEXT,         -- 建物構造
            registry_owner TEXT,    -- 登記所有者
            management_type TEXT DEFAULT '自社管理',  -- 管理形態（自社管理/他社仲介/共同管理）
            management_company TEXT, -- 管理会社名
            available_rooms INTEGER DEFAULT 0,  -- 募集中部屋数
            renewal_rooms INTEGER DEFAULT 0,    -- 更新予定部屋数
            notes TEXT,             -- 備考
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 建物登記簿テーブル（新規）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS building_registries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER,
            registry_owner TEXT,    -- 建物所有者
            registry_address TEXT,  -- 建物登記簿上の住所
            building_structure TEXT, -- 建物の構造
            building_floors INTEGER, -- 建物の階数
            building_area REAL,     -- 建物面積
            building_date TEXT,     -- 建築年月
            registry_date TEXT,     -- 建物登記年月日
            mortgage_info TEXT,     -- 建物抵当権情報
            notes TEXT,             -- 備考
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (property_id) REFERENCES properties (id)
        )
    ''')
    
    # 土地登記簿テーブル（新規・複数対応）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS land_registries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER,
            land_number TEXT,       -- 土地番号
            land_owner TEXT,        -- 土地所有者
            land_address TEXT,      -- 土地の住所
            land_area REAL,         -- 土地面積
            land_use TEXT,          -- 土地の用途
            registry_date TEXT,     -- 土地登記年月日
            mortgage_info TEXT,     -- 土地抵当権情報
            notes TEXT,             -- 備考
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (property_id) REFERENCES properties (id)
        )
    ''')
    
    # 謄本ファイルテーブル（新規）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registry_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER,
            document_type TEXT,     -- 'building' or 'land'
            file_path TEXT,         -- PDFファイルパス
            file_name TEXT,         -- ファイル名
            ocr_result TEXT,        -- OCR結果
            is_processed BOOLEAN DEFAULT 0,  -- 処理済みフラグ
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (property_id) REFERENCES properties (id)
        )
    ''')
    
    # 部屋・階層テーブル（拡張版）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER,
            room_number TEXT NOT NULL,      -- 部屋番号
            floor TEXT,                     -- 階層
            area REAL,                      -- 面積（㎡）
            use_restrictions TEXT,          -- 用途制限
            power_capacity TEXT,            -- 電力容量
            pet_allowed BOOLEAN DEFAULT 0,  -- ペット可
            midnight_allowed BOOLEAN DEFAULT 0, -- 深夜営業可
            notes TEXT,                     -- 備考
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (property_id) REFERENCES properties (id)
        )
    ''')
    
    # 階層詳細テーブル（新規追加）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS floor_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER,
            floor_number TEXT NOT NULL,     -- 階層番号（1F, 2F, 3F等）
            floor_name TEXT,                -- 階層名（1階、2階等）
            total_area REAL,                -- 階層総面積（㎡）
            registry_area REAL,             -- 謄本記載面積（㎡）
            floor_usage TEXT,               -- 階層用途（オフィス、店舗、住宅等）
            available_area REAL,            -- 空き面積（㎡）
            occupied_area REAL,             -- 入居面積（㎡）
            notes TEXT,                     -- 備考
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (property_id) REFERENCES properties (id)
        )
    ''')
    
    # 階層入居状況テーブル（新規追加）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS floor_occupancy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            floor_detail_id INTEGER,
            unit_id INTEGER,                -- 部屋ID
            tenant_id INTEGER,              -- テナントID
            tenant_name TEXT,               -- テナント名
            occupied_area REAL,             -- 入居面積（㎡）
            contract_start_date DATE,       -- 契約開始日
            contract_end_date DATE,         -- 契約終了日
            rent_amount INTEGER,            -- 賃料
            maintenance_fee INTEGER,        -- 管理費
            occupancy_status TEXT DEFAULT 'occupied', -- 入居状況（occupied, vacant, reserved）
            notes TEXT,                     -- 備考
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (floor_detail_id) REFERENCES floor_details (id),
            FOREIGN KEY (unit_id) REFERENCES units (id),
            FOREIGN KEY (tenant_id) REFERENCES customers (id)
        )
    ''')
    
    # 募集状況テーブル（新規追加）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recruitment_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            floor_detail_id INTEGER,
            unit_id INTEGER,                -- 部屋ID
            recruitment_type TEXT,          -- 募集種別（新規募集、更新募集、転貸募集）
            available_area REAL,            -- 募集面積（㎡）
            expected_rent INTEGER,          -- 想定賃料
            expected_maintenance_fee INTEGER, -- 想定管理費
            recruitment_start_date DATE,    -- 募集開始日
            recruitment_end_date DATE,      -- 募集終了日
            recruitment_status TEXT DEFAULT 'active', -- 募集状況（active, paused, closed）
            contact_person TEXT,            -- 担当者
            notes TEXT,                     -- 備考
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (floor_detail_id) REFERENCES floor_details (id),
            FOREIGN KEY (unit_id) REFERENCES units (id)
        )
    ''')
    
    # 賃貸契約テーブル（拡張版）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tenant_contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_id INTEGER,
            contractor_name TEXT NOT NULL,  -- 契約者名
            start_date DATE,
            end_date DATE,
            rent INTEGER,
            maintenance_fee INTEGER,        -- 管理費
            security_deposit INTEGER,       -- 敷金
            key_money INTEGER,              -- 礼金
            renewal_method TEXT,            -- 更新方法
            insurance_flag BOOLEAN DEFAULT 0,  -- 保険フラグ
            -- 更新通知期間設定
            renewal_notice_days INTEGER DEFAULT 60,      -- 更新通知期間（日数）
            renewal_deadline_days INTEGER DEFAULT 30,    -- 更新期限（日数）
            auto_create_tasks BOOLEAN DEFAULT 1,         -- 自動タスク作成フラグ
            -- 仲介手数料関連
            tenant_commission_months REAL DEFAULT 0,    -- 借主仲介手数料（月数）
            landlord_commission_months REAL DEFAULT 0,   -- 貸主仲介手数料（月数）
            tenant_commission_amount INTEGER DEFAULT 0,  -- 借主仲介手数料（円）
            landlord_commission_amount INTEGER DEFAULT 0, -- 貸主仲介手数料（円）
            advertising_fee INTEGER DEFAULT 0,           -- 広告宣伝費（円）
            advertising_fee_included BOOLEAN DEFAULT 0,   -- 広告費込みフラグ
            commission_notes TEXT,                       -- 手数料備考
            memo TEXT,                      -- メモ
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (unit_id) REFERENCES units (id)
        )
    ''')
    
    # 書類テーブル（拡張版）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id INTEGER,
            document_type TEXT NOT NULL,  -- DocumentType Enum
            file_path TEXT,
            file_name TEXT,
            ocr_result TEXT,
            ocr_edited TEXT,             -- 手動編集されたOCR結果
            is_verified BOOLEAN DEFAULT 0, -- OCR結果の検証済みフラグ
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contract_id) REFERENCES tenant_contracts (id)
        )
    ''')
    
    # 対応タスクテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id INTEGER,
            task_type TEXT NOT NULL,      -- 更新案内、請求、通知
            title TEXT NOT NULL,
            description TEXT,
            due_date DATE,
            priority TEXT DEFAULT 'normal', -- high, normal, low
            status TEXT DEFAULT 'pending',  -- pending, in_progress, completed
            assigned_to TEXT,             -- 担当者
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contract_id) REFERENCES tenant_contracts (id)
        )
    ''')
    
    # 重説チェック項目テーブル（拡張版）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checklist_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id INTEGER,
            item_name TEXT NOT NULL,
            item_category TEXT,           -- 必須項目、任意項目
            is_required BOOLEAN DEFAULT 1,
            is_completed BOOLEAN DEFAULT 0,
            auto_detected BOOLEAN DEFAULT 0, -- 自動判定フラグ
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contract_id) REFERENCES tenant_contracts (id)
        )
    ''')
    
    # 顧客との接点履歴テーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS communications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            contract_id INTEGER,
            communication_type TEXT NOT NULL, -- 電話、メール、面談、その他
            subject TEXT,
            content TEXT,
            contact_date DATE,
            direction TEXT DEFAULT '受信',   -- 受信/発信
            next_action TEXT,             -- 次回アクション
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers (id),
            FOREIGN KEY (contract_id) REFERENCES tenant_contracts (id)
        )
    ''')
    
    # 契約手続きログテーブル（新規追加）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contract_procedure_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id INTEGER,
            procedure_type TEXT NOT NULL,     -- 手続き種別
            procedure_date DATE,              -- 手続き実施日
            deadline_date DATE,               -- 期限日
            status TEXT DEFAULT 'pending',    -- pending, in_progress, completed, cancelled
            notes TEXT,                       -- 備考
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contract_id) REFERENCES tenant_contracts (id)
        )
    ''')
    
    # 参考物件テーブル（新規）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reference_properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT NOT NULL,
            area REAL,                    -- 面積
            rent INTEGER,                 -- 賃料
            maintenance_fee INTEGER,      -- 管理費
            unit_price REAL,              -- 単価
            source_document_id INTEGER,   -- OCR元のPDF
            ocr_extracted BOOLEAN DEFAULT 0, -- OCR抽出済みフラグ
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_document_id) REFERENCES documents (id)
        )
    ''')
    
    # 整合性チェック結果テーブル（新規）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS consistency_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id INTEGER,
            check_item TEXT NOT NULL,     -- チェック項目名
            document_type TEXT NOT NULL,  -- 書類種別
            extracted_value TEXT,         -- 抽出結果
            db_value TEXT,                -- DB登録値
            is_consistent BOOLEAN,        -- 一致フラグ
            notes TEXT,                   -- 備考
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contract_id) REFERENCES tenant_contracts (id)
        )
    ''')
    
    # 既存テーブルに手数料関連カラムを追加（ALTER TABLE）
    try:
        # 手数料カラムの追加
        cursor.execute('ALTER TABLE tenant_contracts ADD COLUMN tenant_commission_months REAL DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # カラムが既に存在する場合はスキップ
    
    # 契約テーブルに顧客IDカラムを追加
    try:
        cursor.execute('ALTER TABLE tenant_contracts ADD COLUMN customer_id INTEGER')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE tenant_contracts ADD COLUMN landlord_commission_months REAL DEFAULT 0')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE tenant_contracts ADD COLUMN tenant_commission_amount INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE tenant_contracts ADD COLUMN landlord_commission_amount INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE tenant_contracts ADD COLUMN advertising_fee INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE tenant_contracts ADD COLUMN advertising_fee_included BOOLEAN DEFAULT 0')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE tenant_contracts ADD COLUMN commission_notes TEXT')
    except sqlite3.OperationalError:
        pass
    
    # 更新通知期間関連カラムの追加
    try:
        cursor.execute('ALTER TABLE tenant_contracts ADD COLUMN renewal_notice_days INTEGER DEFAULT 60')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE tenant_contracts ADD COLUMN renewal_deadline_days INTEGER DEFAULT 30')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE tenant_contracts ADD COLUMN auto_create_tasks BOOLEAN DEFAULT 1')
    except sqlite3.OperationalError:
        pass
    
    # communicationsテーブルにdirectionフィールドを追加
    try:
        cursor.execute("ALTER TABLE communications ADD COLUMN direction TEXT DEFAULT '受信'")
    except sqlite3.OperationalError:
        pass
    
    # 物件オーナー関連テーブル（新規）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS property_owners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER NOT NULL,
            owner_id INTEGER NOT NULL,
            ownership_ratio REAL DEFAULT 100.0,  -- 所有比率（%）
            is_primary BOOLEAN DEFAULT 0,        -- 主要オーナーフラグ
            start_date DATE,                     -- 所有開始日
            end_date DATE,                       -- 所有終了日（売却時など）
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (property_id) REFERENCES properties (id),
            FOREIGN KEY (owner_id) REFERENCES customers (id),
            UNIQUE(property_id, owner_id)
        )
    ''')
    
    # 部屋オーナー関連テーブル（新規・区分所有対応）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS unit_owners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_id INTEGER NOT NULL,
            owner_id INTEGER NOT NULL,
            ownership_ratio REAL DEFAULT 100.0,  -- 所有比率（%）
            is_primary BOOLEAN DEFAULT 0,        -- 主要オーナーフラグ
            start_date DATE,                     -- 所有開始日
            end_date DATE,                       -- 所有終了日（売却時など）
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (unit_id) REFERENCES units (id),
            FOREIGN KEY (owner_id) REFERENCES customers (id),
            UNIQUE(unit_id, owner_id)
        )
    ''')
    
    # アクティビティログテーブル（新規）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_type TEXT NOT NULL,     -- CREATE, UPDATE, DELETE, VIEW, LOGIN, etc.
            entity_type TEXT NOT NULL,       -- customer, property, contract, task, etc.
            entity_id INTEGER,               -- 関連エンティティのID
            entity_name TEXT,                -- エンティティの名前（表示用）
            description TEXT,                -- 活動の説明
            user_name TEXT,                  -- 実行ユーザー（将来的な拡張用）
            metadata TEXT,                   -- 追加メタデータ（JSON形式）
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # アクティビティログのインデックス
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_activity_logs_created_at 
        ON activity_logs(created_at DESC)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_activity_logs_entity 
        ON activity_logs(entity_type, entity_id)
    ''')

    conn.commit()
    conn.close()

# 顧客クラス（拡張版）
class Customer:
    @staticmethod
    def create(name: str, customer_type: str = 'tenant', phone: str = None, 
               email: str = None, address: str = None, memo: str = None) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO customers (name, type, phone, email, address, memo)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, customer_type, phone, email, address, memo))
        customer_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # アクティビティログを記録
        ActivityLog.log(
            activity_type='CREATE',
            entity_type='customer',
            entity_id=customer_id,
            entity_name=name,
            description=f'{customer_type}顧客「{name}」を登録しました'
        )
        
        return customer_id
    
    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers ORDER BY created_at DESC')
        customers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return customers
    
    @staticmethod
    def get_by_id(customer_id: int) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        row = cursor.fetchone()
        customer = dict(row) if row else None
        conn.close()
        return customer
    
    @staticmethod
    def update(customer_id: int, name: str = None, customer_type: str = None,
               phone: str = None, email: str = None, address: str = None, memo: str = None):
        """顧客情報を更新"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 更新するフィールドを動的に構築
        update_fields = []
        params = []
        
        if name is not None:
            update_fields.append("name = ?")
            params.append(name)
        if customer_type is not None:
            update_fields.append("type = ?")
            params.append(customer_type)
        if phone is not None:
            update_fields.append("phone = ?")
            params.append(phone)
        if email is not None:
            update_fields.append("email = ?")
            params.append(email)
        if address is not None:
            update_fields.append("address = ?")
            params.append(address)
        if memo is not None:
            update_fields.append("memo = ?")
            params.append(memo)
        
        # updated_atを追加
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        
        if update_fields:
            params.append(customer_id)
            query = f"UPDATE customers SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
        
        conn.close()
    
    @staticmethod
    def get_related_data_count(customer_id: int) -> Dict[str, int]:
        """顧客に関連するデータの件数を取得"""
        conn = get_db_connection()
        cursor = conn.cursor()

        counts = {}

        # 接点履歴の件数
        cursor.execute('SELECT COUNT(*) FROM communications WHERE customer_id = ?', (customer_id,))
        counts['communications'] = cursor.fetchone()[0]

        # 契約の件数
        cursor.execute('SELECT COUNT(*) FROM tenant_contracts WHERE customer_id = ?', (customer_id,))
        counts['contracts'] = cursor.fetchone()[0]

        # オーナープロフィール
        cursor.execute('SELECT COUNT(*) FROM owner_profiles WHERE customer_id = ?', (customer_id,))
        counts['owner_profiles'] = cursor.fetchone()[0]

        # テナントプロフィール
        cursor.execute('SELECT COUNT(*) FROM tenant_profiles WHERE customer_id = ?', (customer_id,))
        counts['tenant_profiles'] = cursor.fetchone()[0]

        conn.close()
        return counts

    @staticmethod
    def delete(customer_id: int):
        """顧客を削除（関連データも削除）"""
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # 関連するプロフィールを削除
            cursor.execute('DELETE FROM owner_profiles WHERE customer_id = ?', (customer_id,))
            cursor.execute('DELETE FROM tenant_profiles WHERE customer_id = ?', (customer_id,))

            # 関連する接点履歴を削除
            cursor.execute('DELETE FROM communications WHERE customer_id = ?', (customer_id,))

            # 顧客を削除
            cursor.execute('DELETE FROM customers WHERE id = ?', (customer_id,))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def update_last_contact(customer_id: int):
        """最終接触日を更新（テナントプロフィール）"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE tenant_profiles SET last_contact_date = CURRENT_DATE WHERE customer_id = ?', (customer_id,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_by_owner(owner_id: int) -> List[Dict[str, Any]]:
        """オーナーに紐づくテナントを取得"""
        conn = get_db_connection()
        cursor = conn.cursor()
        # 実際の実装では、オーナーとテナントの関係を管理するテーブルが必要
        # ここでは簡易的にtype='tenant'の顧客を返す
        cursor.execute('SELECT * FROM customers WHERE type = "tenant" ORDER BY name')
        tenants = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return tenants

# オーナープロフィールクラス（新規）
class OwnerProfile:
    @staticmethod
    def create(customer_id: int, is_landowner: bool = True, has_decision_authority: bool = True,
               title: str = None, bank_account: str = None, commission_rate: float = None) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO owner_profiles (customer_id, is_landowner, has_decision_authority, title, bank_account, commission_rate)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (customer_id, is_landowner, has_decision_authority, title, bank_account, commission_rate))
        profile_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return profile_id
    
    @staticmethod
    def get_by_customer(customer_id: int) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM owner_profiles WHERE customer_id = ?', (customer_id,))
        row = cursor.fetchone()
        profile = dict(row) if row else None
        conn.close()
        return profile

# テナントプロフィールクラス（新規）
class TenantProfile:
    @staticmethod
    def create(customer_id: int, industry: str = None, guarantor_company: str = None,
               emergency_contact: str = None, submitted_documents: str = None) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tenant_profiles (customer_id, industry, guarantor_company, emergency_contact, submitted_documents)
            VALUES (?, ?, ?, ?, ?)
        ''', (customer_id, industry, guarantor_company, emergency_contact, submitted_documents))
        profile_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return profile_id
    
    @staticmethod
    def get_by_customer(customer_id: int) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tenant_profiles WHERE customer_id = ?', (customer_id,))
        row = cursor.fetchone()
        profile = dict(row) if row else None
        conn.close()
        return profile

# 建物登記簿クラス（新規）
class BuildingRegistry:
    @staticmethod
    def create(property_id: int, registry_owner: str = None, registry_address: str = None,
               building_structure: str = None, building_floors: int = None, building_area: float = None,
               building_date: str = None, registry_date: str = None, mortgage_info: str = None,
               notes: str = None) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO building_registries (property_id, registry_owner, registry_address,
                                           building_structure, building_floors, building_area,
                                           building_date, registry_date, mortgage_info, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (property_id, registry_owner, registry_address, building_structure,
              building_floors, building_area, building_date, registry_date, mortgage_info, notes))
        registry_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return registry_id
    
    @staticmethod
    def get_by_property(property_id: int) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM building_registries WHERE property_id = ? ORDER BY created_at', (property_id,))
        registries = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return registries

# 謄本文書クラス（新規）
class RegistryDocument:
    @staticmethod
    def create(property_id: int, document_type: str, file_path: str, file_name: str, is_processed: bool = False) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO registry_documents (property_id, document_type, file_path, file_name, is_processed)
            VALUES (?, ?, ?, ?, ?)
        ''', (property_id, document_type, file_path, file_name, is_processed))
        document_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return document_id
    
    @staticmethod
    def update_ocr_result(document_id: int, ocr_result: str):
        """OCR結果を更新"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE registry_documents SET ocr_result = ?, is_processed = 1 WHERE id = ?
        ''', (ocr_result, document_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_by_property(property_id: int) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM registry_documents WHERE property_id = ? ORDER BY created_at DESC', (property_id,))
        documents = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return documents
    
    @staticmethod
    def get_unprocessed() -> List[Dict[str, Any]]:
        """未処理の謄本文書を取得"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM registry_documents WHERE is_processed = 0 ORDER BY created_at')
        documents = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return documents
    
    @staticmethod
    def get_by_property_and_type(property_id: int, document_type: str) -> List[Dict[str, Any]]:
        """物件IDとドキュメントタイプで謄本文書を取得"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM registry_documents WHERE property_id = ? AND document_type = ? ORDER BY created_at DESC', 
                      (property_id, document_type))
        documents = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return documents

# 土地登記簿クラス（新規・複数対応）
class LandRegistry:
    @staticmethod
    def create(property_id: int, land_number: str = None, land_owner: str = None,
               land_address: str = None, land_area: float = None, land_use: str = None,
               registry_date: str = None, mortgage_info: str = None, notes: str = None) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO land_registries (property_id, land_number, land_owner, land_address,
                                       land_area, land_use, registry_date, mortgage_info, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (property_id, land_number, land_owner, land_address, land_area,
              land_use, registry_date, mortgage_info, notes))
        registry_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return registry_id
    
    @staticmethod
    def get_by_property(property_id: int) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM land_registries WHERE property_id = ? ORDER BY land_number, created_at', (property_id,))
        registries = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return registries
    
    @staticmethod
    def get_total_land_area(property_id: int) -> float:
        """物件の総土地面積を取得"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT SUM(land_area) as total_area FROM land_registries WHERE property_id = ?', (property_id,))
        result = cursor.fetchone()
        total_area = result['total_area'] if result and result['total_area'] else 0.0
        conn.close()
        return total_area

# 物件クラス（拡張版）
class Property:
    @staticmethod
    def create(name: str, address: str, structure: str = None, registry_owner: str = None,
               management_type: str = '自社管理', management_company: str = None,
               available_rooms: int = 0, renewal_rooms: int = 0, notes: str = None) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO properties (name, address, structure, registry_owner, 
                                   management_type, management_company, available_rooms, 
                                   renewal_rooms, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, address, structure, registry_owner, management_type, 
              management_company, available_rooms, renewal_rooms, notes))
        property_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return property_id
    
    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM properties ORDER BY created_at DESC')
        properties = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return properties
    
    @staticmethod
    def get_by_id(property_id: int) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM properties WHERE id = ?', (property_id,))
        row = cursor.fetchone()
        property_obj = dict(row) if row else None
        conn.close()
        return property_obj
    
    @staticmethod
    def update(id: int, name: str = None, address: str = None, structure: str = None, 
               registry_owner: str = None, management_type: str = None, 
               management_company: str = None, available_rooms: int = None, 
               renewal_rooms: int = None, notes: str = None):
        """物件情報を更新"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 更新するフィールドを動的に構築
        update_fields = []
        params = []
        
        if name is not None:
            update_fields.append("name = ?")
            params.append(name)
        if address is not None:
            update_fields.append("address = ?")
            params.append(address)
        if structure is not None:
            update_fields.append("structure = ?")
            params.append(structure)
        if registry_owner is not None:
            update_fields.append("registry_owner = ?")
            params.append(registry_owner)
        if management_type is not None:
            update_fields.append("management_type = ?")
            params.append(management_type)
        if management_company is not None:
            update_fields.append("management_company = ?")
            params.append(management_company)
        if available_rooms is not None:
            update_fields.append("available_rooms = ?")
            params.append(available_rooms)
        if renewal_rooms is not None:
            update_fields.append("renewal_rooms = ?")
            params.append(renewal_rooms)
        if notes is not None:
            update_fields.append("notes = ?")
            params.append(notes)
        
        # updated_atを追加
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        
        if update_fields:
            params.append(id)
            query = f"UPDATE properties SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
        
        conn.close()
    
    @staticmethod
    def delete(property_id: int):
        """物件を削除（関連する登記簿情報も削除）"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 関連する建物登記簿を削除
            cursor.execute('DELETE FROM building_registries WHERE property_id = ?', (property_id,))
            
            # 関連する土地登記簿を削除
            cursor.execute('DELETE FROM land_registries WHERE property_id = ?', (property_id,))
            
            # 関連する謄本文書を削除
            cursor.execute('DELETE FROM registry_documents WHERE property_id = ?', (property_id,))
            
            # 関連する部屋を削除
            cursor.execute('DELETE FROM units WHERE property_id = ?', (property_id,))
            
            # 物件を削除
            cursor.execute('DELETE FROM properties WHERE id = ?', (property_id,))
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def add_owner(property_id: int, owner_id: int, ownership_ratio: float = 100.0,
                  is_primary: bool = False, start_date: str = None, notes: str = None) -> int:
        """物件にオーナーを追加"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # 既に削除済みのレコードがあるか確認
            cursor.execute('''
                SELECT id FROM property_owners
                WHERE property_id = ? AND owner_id = ? AND end_date IS NOT NULL
            ''', (property_id, owner_id))
            existing = cursor.fetchone()

            if existing:
                # 削除済みレコードを再利用（復活）
                owner_relation_id = existing[0]
                cursor.execute('''
                    UPDATE property_owners
                    SET end_date = NULL, ownership_ratio = ?, is_primary = ?,
                        start_date = ?, notes = ?
                    WHERE id = ?
                ''', (ownership_ratio, is_primary, start_date, notes, owner_relation_id))
            else:
                # 新規作成
                cursor.execute('''
                    INSERT INTO property_owners (property_id, owner_id, ownership_ratio,
                                                is_primary, start_date, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (property_id, owner_id, ownership_ratio, is_primary, start_date, notes))
                owner_relation_id = cursor.lastrowid
            conn.commit()
            
            # アクティビティログを記録
            property = Property.get_by_id(property_id)
            owner = Customer.get_by_id(owner_id)
            if property and owner:
                ActivityLog.log(
                    activity_type='UPDATE',
                    entity_type='property',
                    entity_id=property_id,
                    entity_name=property.get('name'),
                    description=f'物件「{property.get("name")}」にオーナー「{owner.get("name")}」を追加しました'
                )
            
            return owner_relation_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def get_owners(property_id: int) -> List[Dict[str, Any]]:
        """物件のオーナー一覧を取得"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT po.*, c.name as owner_name, c.phone, c.email, c.type
            FROM property_owners po
            JOIN customers c ON po.owner_id = c.id
            WHERE po.property_id = ? AND (po.end_date IS NULL OR po.end_date > date('now'))
            ORDER BY po.is_primary DESC, po.ownership_ratio DESC
        ''', (property_id,))
        owners = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return owners
    
    @staticmethod
    def remove_owner(property_id: int, owner_id: int, end_date: str = None):
        """物件からオーナーを削除（論理削除）"""
        conn = get_db_connection()
        cursor = conn.cursor()
        if not end_date:
            from datetime import date
            end_date = date.today().isoformat()

        cursor.execute('''
            UPDATE property_owners
            SET end_date = ?
            WHERE property_id = ? AND owner_id = ? AND end_date IS NULL
        ''', (end_date, property_id, owner_id))
        conn.commit()
        conn.close()

# 部屋・階層クラス（拡張版）
class Unit:
    @staticmethod
    def create(property_id: int, room_number: str, floor: str = None, 
               area: float = None, use_restrictions: str = None, power_capacity: str = None,
               pet_allowed: bool = False, midnight_allowed: bool = False, notes: str = None) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO units (property_id, room_number, floor, area, use_restrictions, power_capacity,
                              pet_allowed, midnight_allowed, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (property_id, room_number, floor, area, use_restrictions, power_capacity,
              pet_allowed, midnight_allowed, notes))
        unit_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return unit_id
    
    @staticmethod
    def get_by_property(property_id: int) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM units WHERE property_id = ? ORDER BY room_number', (property_id,))
        units = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return units
    
    @staticmethod
    def get_available() -> List[Dict[str, Any]]:
        """利用可能な部屋を取得（契約が終了している部屋）"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.*, p.name as property_name 
            FROM units u 
            JOIN properties p ON u.property_id = p.id 
            WHERE u.id NOT IN (
                SELECT unit_id FROM tenant_contracts 
                WHERE end_date IS NULL OR end_date > date('now')
            )
            ORDER BY p.name, u.room_number
        ''')
        units = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return units
    
    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        """すべての部屋を取得"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.*, p.name as property_name 
            FROM units u 
            JOIN properties p ON u.property_id = p.id 
            ORDER BY p.name, u.room_number
        ''')
        units = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return units
    
    @staticmethod
    def get_by_id(unit_id: int) -> Dict[str, Any]:
        """部屋を取得"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.*, p.name as property_name 
            FROM units u 
            JOIN properties p ON u.property_id = p.id 
            WHERE u.id = ?
        ''', (unit_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else {}
    
    @staticmethod
    def update(unit_id: int, room_number: str, floor: str = None, 
               area: float = None, use_restrictions: str = None, power_capacity: str = None,
               pet_allowed: bool = False, midnight_allowed: bool = False, notes: str = None):
        """部屋情報を更新"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE units SET room_number = ?, floor = ?, area = ?, use_restrictions = ?, 
                           power_capacity = ?, pet_allowed = ?, midnight_allowed = ?, notes = ?
            WHERE id = ?
        ''', (room_number, floor, area, use_restrictions, power_capacity, 
              pet_allowed, midnight_allowed, notes, unit_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def delete(unit_id: int):
        """部屋を削除"""
        conn = get_db_connection()
        cursor = conn.cursor()
        # 関連する契約がないか確認
        cursor.execute('SELECT COUNT(*) FROM tenant_contracts WHERE unit_id = ?', (unit_id,))
        contract_count = cursor.fetchone()[0]
        
        if contract_count > 0:
            conn.close()
            raise ValueError("この部屋には契約が存在するため削除できません")
        
        cursor.execute('DELETE FROM units WHERE id = ?', (unit_id,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_allowed_uses(unit_id: int) -> Dict[str, Any]:
        """部屋の使用条件を取得"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT pet_allowed, midnight_allowed, use_restrictions, power_capacity, notes
            FROM units WHERE id = ?
        ''', (unit_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else {}
    
    @staticmethod
    def add_owner(unit_id: int, owner_id: int, ownership_ratio: float = 100.0,
                  is_primary: bool = False, start_date: str = None, notes: str = None) -> int:
        """部屋にオーナーを追加（区分所有対応）"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # 既に削除済みのレコードがあるか確認
            cursor.execute('''
                SELECT id FROM unit_owners
                WHERE unit_id = ? AND owner_id = ? AND end_date IS NOT NULL
            ''', (unit_id, owner_id))
            existing = cursor.fetchone()

            if existing:
                # 削除済みレコードを再利用（復活）
                owner_relation_id = existing[0]
                cursor.execute('''
                    UPDATE unit_owners
                    SET end_date = NULL, ownership_ratio = ?, is_primary = ?,
                        start_date = ?, notes = ?
                    WHERE id = ?
                ''', (ownership_ratio, is_primary, start_date, notes, owner_relation_id))
            else:
                # 新規作成
                cursor.execute('''
                    INSERT INTO unit_owners (unit_id, owner_id, ownership_ratio,
                                            is_primary, start_date, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (unit_id, owner_id, ownership_ratio, is_primary, start_date, notes))
                owner_relation_id = cursor.lastrowid
            conn.commit()
            
            # アクティビティログを記録
            unit = Unit.get_by_id(unit_id)
            owner = Customer.get_by_id(owner_id)
            if unit and owner:
                ActivityLog.log(
                    activity_type='UPDATE',
                    entity_type='unit',
                    entity_id=unit_id,
                    entity_name=unit.get('room_number'),
                    description=f'部屋「{unit.get("room_number")}」にオーナー「{owner.get("name")}」を追加しました'
                )
            
            return owner_relation_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def get_owners(unit_id: int) -> List[Dict[str, Any]]:
        """部屋のオーナー一覧を取得"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT uo.*, c.name as owner_name, c.phone, c.email, c.type
            FROM unit_owners uo
            JOIN customers c ON uo.owner_id = c.id
            WHERE uo.unit_id = ? AND (uo.end_date IS NULL OR uo.end_date > date('now'))
            ORDER BY uo.is_primary DESC, uo.ownership_ratio DESC
        ''', (unit_id,))
        owners = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return owners
    
    @staticmethod
    def remove_owner(unit_id: int, owner_id: int, end_date: str = None):
        """部屋からオーナーを削除（論理削除）"""
        conn = get_db_connection()
        cursor = conn.cursor()
        if not end_date:
            from datetime import date
            end_date = date.today().isoformat()
        
        cursor.execute('''
            UPDATE unit_owners 
            SET end_date = ?
            WHERE unit_id = ? AND owner_id = ? AND end_date IS NULL
        ''', (end_date, unit_id, owner_id))
        conn.commit()
        conn.close()

# 賃貸契約クラス（拡張版）
class TenantContract:
    @staticmethod
    def create(unit_id: int, contractor_name: str, start_date: str = None, end_date: str = None,
               rent: int = None, maintenance_fee: int = None, security_deposit: int = None,
               key_money: int = None, renewal_method: str = None, insurance_flag: bool = False,
               renewal_notice_days: int = 60, renewal_deadline_days: int = 30,
               owner_cancellation_notice_days: int = 180, tenant_cancellation_notice_days: int = 30,
               auto_create_tasks: bool = True, memo: str = None, customer_id: int = None,
               contract_status: str = 'active', renewal_terms: str = None, tenant_phone: str = None,
               tenant_name: str = None, notes: str = None, mediation_type: str = '片手仲介',
               party_type: str = 'テナント（借主）', property_id: int = None) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tenant_contracts (unit_id, contractor_name, start_date, end_date,
                                        rent, maintenance_fee, security_deposit, key_money,
                                        renewal_method, insurance_flag, renewal_notice_days,
                                        renewal_deadline_days, owner_cancellation_notice_days,
                                        tenant_cancellation_notice_days, auto_create_tasks, memo, customer_id,
                                        contract_status, renewal_terms, tenant_phone, tenant_name, notes,
                                        mediation_type, party_type, property_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (unit_id, contractor_name, start_date, end_date, rent, maintenance_fee,
              security_deposit, key_money, renewal_method, insurance_flag,
              renewal_notice_days, renewal_deadline_days, owner_cancellation_notice_days,
              tenant_cancellation_notice_days, auto_create_tasks, memo, customer_id,
              contract_status, renewal_terms, tenant_phone, tenant_name, notes,
              mediation_type, party_type, property_id))
        contract_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # アクティビティログを記録
        ActivityLog.log(
            activity_type='CREATE',
            entity_type='contract',
            entity_id=contract_id,
            entity_name=contractor_name,
            description=f'契約「{contractor_name}」を登録しました'
        )
        
        return contract_id
    
    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT tc.*,
                   COALESCE(p.name, p2.name) as property_name,
                   u.room_number, u.floor,
                   COALESCE(u.property_id, tc.property_id) as property_id
            FROM tenant_contracts tc
            LEFT JOIN units u ON tc.unit_id = u.id
            LEFT JOIN properties p ON u.property_id = p.id
            LEFT JOIN properties p2 ON tc.property_id = p2.id
            ORDER BY tc.created_at DESC
        ''')
        contracts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return contracts
    
    @staticmethod
    def get_expiring_contracts(days: int = 30) -> List[Dict[str, Any]]:
        """更新期日が近い契約を取得"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT tc.*,
                   COALESCE(p.name, p2.name) as property_name,
                   u.room_number, u.floor,
                   COALESCE(u.property_id, tc.property_id) as property_id
            FROM tenant_contracts tc
            LEFT JOIN units u ON tc.unit_id = u.id
            LEFT JOIN properties p ON u.property_id = p.id
            LEFT JOIN properties p2 ON tc.property_id = p2.id
            WHERE tc.end_date <= date('now', '+' || ? || ' days')
            ORDER BY tc.end_date
        ''', (days,))
        contracts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return contracts
    
    @staticmethod
    def update_commission(contract_id: int, commission_data: dict):
        """仲介手数料を更新"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE tenant_contracts 
            SET tenant_commission_months = ?,
                landlord_commission_months = ?,
                tenant_commission_amount = ?,
                landlord_commission_amount = ?,
                advertising_fee = ?,
                advertising_fee_included = ?,
                commission_notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            commission_data.get('tenant_commission_months', 0),
            commission_data.get('landlord_commission_months', 0),
            commission_data.get('tenant_commission_amount', 0),
            commission_data.get('landlord_commission_amount', 0),
            commission_data.get('advertising_fee', 0),
            commission_data.get('advertising_fee_included', False),
            commission_data.get('commission_notes', ''),
            contract_id
        ))
        conn.commit()
        conn.close()

    @staticmethod
    def update(contract_id: int, **kwargs):
        """契約情報を更新"""
        conn = get_db_connection()
        cursor = conn.cursor()

        # 更新可能なフィールドのリスト
        allowed_fields = [
            'unit_id', 'contractor_name', 'start_date', 'end_date',
            'rent', 'maintenance_fee', 'security_deposit', 'key_money',
            'renewal_method', 'insurance_flag', 'renewal_notice_days',
            'renewal_deadline_days', 'auto_create_tasks', 'memo', 'customer_id',
            'tenant_commission_months', 'landlord_commission_months',
            'tenant_commission_amount', 'landlord_commission_amount',
            'advertising_fee', 'advertising_fee_included', 'commission_notes',
            'owner_cancellation_notice_days', 'tenant_cancellation_notice_days',
            'contract_status', 'renewal_terms', 'tenant_phone', 'tenant_name', 'notes',
            'mediation_type', 'party_type', 'property_id'
        ]

        # 更新するフィールドと値を抽出
        update_fields = []
        update_values = []

        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                update_fields.append(f'{field} = ?')
                update_values.append(value)

        if not update_fields:
            conn.close()
            return

        # updated_atも更新
        update_fields.append('updated_at = CURRENT_TIMESTAMP')

        # SQL実行
        sql = f"UPDATE tenant_contracts SET {', '.join(update_fields)} WHERE id = ?"
        update_values.append(contract_id)

        cursor.execute(sql, update_values)
        conn.commit()

        # アクティビティログを記録
        cursor.execute('SELECT contractor_name FROM tenant_contracts WHERE id = ?', (contract_id,))
        result = cursor.fetchone()
        if result:
            ActivityLog.log(
                activity_type='UPDATE',
                entity_type='contract',
                entity_id=contract_id,
                entity_name=result[0],
                description=f'契約「{result[0]}」を更新しました'
            )

        conn.close()

    @staticmethod
    def delete(contract_id: int):
        """契約を削除（関連するタスク、書類、チェックリストも削除）"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 関連するタスクを削除
            cursor.execute('DELETE FROM tasks WHERE contract_id = ?', (contract_id,))
            
            # 関連する書類を削除
            cursor.execute('DELETE FROM documents WHERE contract_id = ?', (contract_id,))
            
            # 関連するチェックリスト項目を削除
            cursor.execute('DELETE FROM checklist_status WHERE contract_id = ?', (contract_id,))
            
            # 関連する整合性チェック結果を削除
            cursor.execute('DELETE FROM consistency_checks WHERE contract_id = ?', (contract_id,))
            
            # 関連する接点履歴を削除
            cursor.execute('DELETE FROM communications WHERE contract_id = ?', (contract_id,))
            
            # 関連する手続きログを削除
            cursor.execute('DELETE FROM contract_procedure_logs WHERE contract_id = ?', (contract_id,))
            
            # 契約を削除
            cursor.execute('DELETE FROM tenant_contracts WHERE id = ?', (contract_id,))
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

# 書類クラス（拡張版）
class Document:
    @staticmethod
    def create(contract_id: int, document_type: str, file_path: str = None, 
               file_name: str = None, ocr_result: str = None) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO documents (contract_id, document_type, file_path, file_name, ocr_result)
            VALUES (?, ?, ?, ?, ?)
        ''', (contract_id, document_type, file_path, file_name, ocr_result))
        document_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return document_id
    
    @staticmethod
    def update_ocr_result(document_id: int, ocr_result: str, is_edited: bool = False):
        """OCR結果を更新"""
        conn = get_db_connection()
        cursor = conn.cursor()
        if is_edited:
            cursor.execute('''
                UPDATE documents SET ocr_edited = ?, is_verified = 1 WHERE id = ?
            ''', (ocr_result, document_id))
        else:
            cursor.execute('''
                UPDATE documents SET ocr_result = ? WHERE id = ?
            ''', (ocr_result, document_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_by_contract(contract_id: int) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM documents WHERE contract_id = ? ORDER BY created_at DESC', (contract_id,))
        documents = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return documents
    
    @staticmethod
    def get_by_type(document_type: str) -> List[Dict[str, Any]]:
        """書類種別で取得"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM documents WHERE document_type = ? ORDER BY created_at DESC', (document_type,))
        documents = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return documents

# タスククラス（新規）
class Task:
    @staticmethod
    def create(contract_id: int, task_type: str, title: str, description: str = None,
               due_date: str = None, priority: str = 'normal', assigned_to: str = None) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tasks (contract_id, task_type, title, description, due_date, priority, assigned_to)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (contract_id, task_type, title, description, due_date, priority, assigned_to))
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # アクティビティログを記録
        ActivityLog.log(
            activity_type='CREATE',
            entity_type='task',
            entity_id=task_id,
            entity_name=title,
            description=f'タスク「{title}」を作成しました'
        )
        
        return task_id
    
    @staticmethod
    def get_by_contract(contract_id: int) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tasks WHERE contract_id = ? ORDER BY due_date, priority', (contract_id,))
        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return tasks
    
    @staticmethod
    def get_pending_tasks() -> List[Dict[str, Any]]:
        """未完了タスクを取得"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT t.*, p.name as property_name, u.room_number
            FROM tasks t
            LEFT JOIN tenant_contracts tc ON t.contract_id = tc.id
            LEFT JOIN units u ON tc.unit_id = u.id
            LEFT JOIN properties p ON u.property_id = p.id
            WHERE t.status != 'completed'
            ORDER BY t.due_date, t.priority
        ''')
        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return tasks
    
    @staticmethod
    def get_all_tasks() -> List[Dict[str, Any]]:
        """全てのタスクを取得"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT t.*, p.name as property_name, u.room_number
            FROM tasks t
            LEFT JOIN tenant_contracts tc ON t.contract_id = tc.id
            LEFT JOIN units u ON tc.unit_id = u.id
            LEFT JOIN properties p ON u.property_id = p.id
            ORDER BY t.due_date, t.priority
        ''')
        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return tasks
    
    @staticmethod
    def update(id: int, task_type: str = None, title: str = None, description: str = None,
               due_date: str = None, priority: str = None, status: str = None, 
               assigned_to: str = None):
        """タスクを更新"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 更新するフィールドを動的に構築
        update_fields = []
        params = []
        
        if task_type is not None:
            update_fields.append("task_type = ?")
            params.append(task_type)
        if title is not None:
            update_fields.append("title = ?")
            params.append(title)
        if description is not None:
            update_fields.append("description = ?")
            params.append(description)
        if due_date is not None:
            update_fields.append("due_date = ?")
            params.append(due_date)
        if priority is not None:
            update_fields.append("priority = ?")
            params.append(priority)
        if status is not None:
            update_fields.append("status = ?")
            params.append(status)
        if assigned_to is not None:
            update_fields.append("assigned_to = ?")
            params.append(assigned_to)
        
        # updated_atを追加
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        
        if update_fields:
            params.append(id)
            query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
        
        conn.close()
    
    @staticmethod
    def delete(task_id: int):
        """タスクを削除"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        conn.commit()
        conn.close()

# チェックリスト項目クラス（拡張版）
class ChecklistStatus:
    @staticmethod
    def create(contract_id: int, item_name: str, item_category: str = 'required',
               is_required: bool = True, auto_detected: bool = False) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO checklist_status (contract_id, item_name, item_category, is_required, auto_detected)
            VALUES (?, ?, ?, ?, ?)
        ''', (contract_id, item_name, item_category, is_required, auto_detected))
        item_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return item_id
    
    @staticmethod
    def get_by_contract(contract_id: int) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM checklist_status WHERE contract_id = ? ORDER BY item_category, id', (contract_id,))
        items = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return items
    
    @staticmethod
    def update_status(item_id: int, is_completed: bool, notes: str = None):
        """チェックリスト項目の状態を更新"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE checklist_status SET is_completed = ?, notes = ? WHERE id = ?
        ''', (is_completed, notes, item_id))
        conn.commit()
        conn.close()

# 顧客との接点履歴クラス（新規）
class Communication:
    @staticmethod
    def create(customer_id: int, contract_id: int, communication_type: str,
               subject: str = None, content: str = None, contact_date: str = None,
               direction: str = '受信', next_action: str = None) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO communications (customer_id, contract_id, communication_type, 
                                      subject, content, contact_date, direction, next_action)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (customer_id, contract_id, communication_type, subject, content, contact_date, direction, next_action))
        communication_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # アクティビティログを記録
        ActivityLog.log(
            activity_type='CREATE',
            entity_type='communication',
            entity_id=communication_id,
            entity_name=subject or communication_type,
            description=f'{communication_type}「{subject or ""}」を記録しました'
        )
        
        return communication_id
    
    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        """全ての接点履歴を取得"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.*, cust.name as customer_name, tc.id as contract_id, 
                   p.name as property_name, u.room_number
            FROM communications c
            LEFT JOIN customers cust ON c.customer_id = cust.id
            LEFT JOIN tenant_contracts tc ON c.contract_id = tc.id
            LEFT JOIN units u ON tc.unit_id = u.id
            LEFT JOIN properties p ON u.property_id = p.id
            ORDER BY c.contact_date DESC, c.created_at DESC
        ''')
        communications = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return communications
    
    @staticmethod
    def get_by_customer(customer_id: int) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.*, tc.id as contract_id, p.name as property_name, u.room_number
            FROM communications c
            LEFT JOIN tenant_contracts tc ON c.contract_id = tc.id
            LEFT JOIN units u ON tc.unit_id = u.id
            LEFT JOIN properties p ON u.property_id = p.id
            WHERE c.customer_id = ?
            ORDER BY c.contact_date DESC, c.created_at DESC
        ''', (customer_id,))
        communications = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return communications

    @staticmethod
    def update(comm_id: int, **kwargs) -> bool:
        """接点履歴を更新"""
        allowed_fields = ['customer_id', 'contract_id', 'communication_type', 'subject',
                         'content', 'contact_date', 'direction', 'next_action']

        # 許可されたフィールドのみを抽出
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not update_data:
            return False

        # SET句を構築
        set_clause = ', '.join([f"{field} = ?" for field in update_data.keys()])
        values = list(update_data.values())
        values.append(comm_id)

        conn = get_db_connection()
        cursor = conn.cursor()

        # 元のデータを取得（ログ用）
        cursor.execute('SELECT subject, communication_type FROM communications WHERE id = ?', (comm_id,))
        old_data = cursor.fetchone()

        # 更新実行
        cursor.execute(f'UPDATE communications SET {set_clause} WHERE id = ?', values)
        conn.commit()
        conn.close()

        # アクティビティログを記録
        if old_data:
            subject = kwargs.get('subject', old_data['subject'])
            comm_type = kwargs.get('communication_type', old_data['communication_type'])
            ActivityLog.log(
                activity_type='UPDATE',
                entity_type='communication',
                entity_id=comm_id,
                entity_name=subject or comm_type,
                description=f'{comm_type}「{subject or ""}」を更新しました'
            )

        return True

    @staticmethod
    def delete(comm_id: int) -> bool:
        """接点履歴を削除"""
        conn = get_db_connection()
        cursor = conn.cursor()

        # 削除前にデータを取得（ログ用）
        cursor.execute('SELECT subject, communication_type FROM communications WHERE id = ?', (comm_id,))
        comm_data = cursor.fetchone()

        if not comm_data:
            conn.close()
            return False

        # 削除実行
        cursor.execute('DELETE FROM communications WHERE id = ?', (comm_id,))
        conn.commit()
        conn.close()

        # アクティビティログを記録
        ActivityLog.log(
            activity_type='DELETE',
            entity_type='communication',
            entity_id=comm_id,
            entity_name=comm_data['subject'] or comm_data['communication_type'],
            description=f'{comm_data["communication_type"]}「{comm_data["subject"] or ""}」を削除しました'
        )

        return True

# 参考物件クラス（新規）
class ReferenceProperty:
    @staticmethod
    def create(address: str, area: float = None, rent: int = None, 
               maintenance_fee: int = None, unit_price: float = None,
               source_document_id: int = None) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO reference_properties (address, area, rent, maintenance_fee, unit_price, source_document_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (address, area, rent, maintenance_fee, unit_price, source_document_id))
        ref_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return ref_id
    
    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM reference_properties ORDER BY registered_at DESC')
        properties = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return properties
    
    @staticmethod
    def get_by_area_range(min_area: float, max_area: float) -> List[Dict[str, Any]]:
        """面積範囲で参考物件を取得"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM reference_properties 
            WHERE area BETWEEN ? AND ?
            ORDER BY unit_price
        ''', (min_area, max_area))
        properties = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return properties

# 整合性チェッククラス（新規）
class ConsistencyCheck:
    @staticmethod
    def create(contract_id: int, check_item: str, document_type: str,
               extracted_value: str = None, db_value: str = None,
               is_consistent: bool = None, notes: str = None) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO consistency_checks (contract_id, check_item, document_type, 
                                          extracted_value, db_value, is_consistent, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (contract_id, check_item, document_type, extracted_value, db_value, is_consistent, notes))
        check_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return check_id
    
    @staticmethod
    def get_by_contract(contract_id: int) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM consistency_checks WHERE contract_id = ? ORDER BY created_at DESC', (contract_id,))
        checks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return checks
    
    @staticmethod
    def get_inconsistent_checks(contract_id: int) -> List[Dict[str, Any]]:
        """不一致のチェック結果を取得"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM consistency_checks 
            WHERE contract_id = ? AND is_consistent = 0
            ORDER BY created_at DESC
        ''', (contract_id,))
        checks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return checks

# 後方互換性のためのエイリアス
Contract = TenantContract
ChecklistItem = ChecklistStatus

# 階層詳細クラス（新規追加）
class FloorDetail:
    @staticmethod
    def create(property_id: int, floor_number: str, floor_name: str = None, 
               total_area: float = None, registry_area: float = None, 
               floor_usage: str = None, available_area: float = None, 
               occupied_area: float = None, notes: str = None) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO floor_details (property_id, floor_number, floor_name, total_area,
                                     registry_area, floor_usage, available_area, occupied_area, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (property_id, floor_number, floor_name, total_area, registry_area,
              floor_usage, available_area, occupied_area, notes))
        floor_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return floor_id
    
    @staticmethod
    def get_by_property(property_id: int) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM floor_details WHERE property_id = ? ORDER BY floor_number', (property_id,))
        floors = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return floors
    
    @staticmethod
    def get_by_id(floor_id: int) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM floor_details WHERE id = ?', (floor_id,))
        row = cursor.fetchone()
        floor = dict(row) if row else None
        conn.close()
        return floor
    
    @staticmethod
    def update(floor_id: int, floor_name: str = None, total_area: float = None,
               registry_area: float = None, floor_usage: str = None,
               available_area: float = None, occupied_area: float = None, notes: str = None):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        update_fields = []
        params = []
        
        if floor_name is not None:
            update_fields.append("floor_name = ?")
            params.append(floor_name)
        if total_area is not None:
            update_fields.append("total_area = ?")
            params.append(total_area)
        if registry_area is not None:
            update_fields.append("registry_area = ?")
            params.append(registry_area)
        if floor_usage is not None:
            update_fields.append("floor_usage = ?")
            params.append(floor_usage)
        if available_area is not None:
            update_fields.append("available_area = ?")
            params.append(available_area)
        if occupied_area is not None:
            update_fields.append("occupied_area = ?")
            params.append(occupied_area)
        if notes is not None:
            update_fields.append("notes = ?")
            params.append(notes)
        
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        
        if update_fields:
            params.append(floor_id)
            query = f"UPDATE floor_details SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
        
        conn.close()

# 階層入居状況クラス（新規追加）
class FloorOccupancy:
    @staticmethod
    def create(floor_detail_id: int, unit_id: int, tenant_id: int, tenant_name: str,
               occupied_area: float, contract_start_date: str = None, contract_end_date: str = None,
               rent_amount: int = None, maintenance_fee: int = None, 
               occupancy_status: str = 'occupied', notes: str = None) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO floor_occupancy (floor_detail_id, unit_id, tenant_id, tenant_name,
                                       occupied_area, contract_start_date, contract_end_date,
                                       rent_amount, maintenance_fee, occupancy_status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (floor_detail_id, unit_id, tenant_id, tenant_name, occupied_area,
              contract_start_date, contract_end_date, rent_amount, maintenance_fee,
              occupancy_status, notes))
        occupancy_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return occupancy_id
    
    @staticmethod
    def get_by_floor(floor_detail_id: int) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT fo.*, u.room_number, u.floor, c.name as customer_name
            FROM floor_occupancy fo
            LEFT JOIN units u ON fo.unit_id = u.id
            LEFT JOIN customers c ON fo.tenant_id = c.id
            WHERE fo.floor_detail_id = ?
            ORDER BY u.room_number
        ''', (floor_detail_id,))
        occupancies = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return occupancies
    
    @staticmethod
    def get_by_property(property_id: int) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT fo.*, fd.floor_number, fd.floor_name, u.room_number, c.name as customer_name
            FROM floor_occupancy fo
            JOIN floor_details fd ON fo.floor_detail_id = fd.id
            LEFT JOIN units u ON fo.unit_id = u.id
            LEFT JOIN customers c ON fo.tenant_id = c.id
            WHERE fd.property_id = ?
            ORDER BY fd.floor_number, u.room_number
        ''', (property_id,))
        occupancies = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return occupancies

# 募集状況クラス（新規追加）
class RecruitmentStatus:
    @staticmethod
    def create(floor_detail_id: int, unit_id: int, recruitment_type: str,
               available_area: float, expected_rent: int = None, expected_maintenance_fee: int = None,
               recruitment_start_date: str = None, recruitment_end_date: str = None,
               recruitment_status: str = 'active', contact_person: str = None, notes: str = None) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO recruitment_status (floor_detail_id, unit_id, recruitment_type,
                                          available_area, expected_rent, expected_maintenance_fee,
                                          recruitment_start_date, recruitment_end_date,
                                          recruitment_status, contact_person, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (floor_detail_id, unit_id, recruitment_type, available_area,
              expected_rent, expected_maintenance_fee, recruitment_start_date,
              recruitment_end_date, recruitment_status, contact_person, notes))
        recruitment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return recruitment_id
    
    @staticmethod
    def get_by_floor(floor_detail_id: int) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT rs.*, u.room_number, u.floor
            FROM recruitment_status rs
            LEFT JOIN units u ON rs.unit_id = u.id
            WHERE rs.floor_detail_id = ?
            ORDER BY u.room_number
        ''', (floor_detail_id,))
        recruitments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return recruitments
    
    @staticmethod
    def get_by_property(property_id: int) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT rs.*, fd.floor_number, fd.floor_name, u.room_number
            FROM recruitment_status rs
            JOIN floor_details fd ON rs.floor_detail_id = fd.id
            LEFT JOIN units u ON rs.unit_id = u.id
            WHERE fd.property_id = ?
            ORDER BY fd.floor_number, u.room_number
        ''', (property_id,))
        recruitments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return recruitments
    
    @staticmethod
    def get_active_recruitments(property_id: int) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT rs.*, fd.floor_number, fd.floor_name, u.room_number
            FROM recruitment_status rs
            JOIN floor_details fd ON rs.floor_detail_id = fd.id
            LEFT JOIN units u ON rs.unit_id = u.id
            WHERE fd.property_id = ? AND rs.recruitment_status = 'active'
            ORDER BY fd.floor_number, u.room_number
        ''', (property_id,))
        recruitments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return recruitments

 
# 契約手続きログクラス（新規）
class ContractProcedureLog:
    @staticmethod
    def create(contract_id: int, procedure_type: str, procedure_date: str = None,
               deadline_date: str = None, status: str = 'pending', notes: str = None) -> int:
        """契約手続きログを作成し、同時にタスクも生成"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 手続きログを作成
            cursor.execute('''
                INSERT INTO contract_procedure_logs (contract_id, procedure_type, procedure_date,
                                                   deadline_date, status, notes)
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
    def get_by_contract(contract_id: int) -> List[Dict[str, Any]]:
        """契約IDに基づく手続きログ一覧を取得"""
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
    def get_all() -> List[Dict[str, Any]]:
        """全ての手続きログを取得"""
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
    def get_pending_procedures() -> List[Dict[str, Any]]:
        """未処理の手続きログを取得"""
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
        conn = get_db_connection()
        cursor = conn.cursor()
        
        update_fields = ['status = ?', 'updated_at = CURRENT_TIMESTAMP']
        params = [status]
        
        if notes is not None:
            update_fields.append('notes = ?')
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
    def get_calendar_events(start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """カレンダー表示用の手続きイベントを取得"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                cpl.id,
                cpl.procedure_type as title,
                cpl.deadline_date as date,
                cpl.status,
                cpl.notes,
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

# アクティビティログクラス
class ActivityLog:
    @staticmethod
    def log(activity_type: str, entity_type: str, entity_id: int = None, 
            entity_name: str = None, description: str = None, 
            user_name: str = None, metadata: str = None):
        """アクティビティログを記録"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO activity_logs 
            (activity_type, entity_type, entity_id, entity_name, description, user_name, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (activity_type, entity_type, entity_id, entity_name, description, user_name, metadata))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_recent(limit: int = 50) -> List[Dict[str, Any]]:
        """最近のアクティビティを取得"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM activity_logs 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return logs
    
    @staticmethod
    def get_by_entity(entity_type: str, entity_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """特定エンティティのアクティビティを取得"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM activity_logs 
            WHERE entity_type = ? AND entity_id = ?
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (entity_type, entity_id, limit))
        logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return logs
    
    @staticmethod
    def get_by_date_range(start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """日付範囲でアクティビティを取得"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM activity_logs 
            WHERE DATE(created_at) BETWEEN ? AND ?
            ORDER BY created_at DESC
        ''', (start_date, end_date))
        logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return logs
    
    @staticmethod
    def cleanup_old_logs(days_to_keep: int = 90):
        """古いログを削除"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM activity_logs 
            WHERE created_at < datetime('now', '-' || ? || ' days')
        ''', (days_to_keep,))
        conn.commit()
        conn.close()
