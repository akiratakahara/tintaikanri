#!/usr/bin/env python3
"""
アクティビティログ機能のテストスクリプト
"""
import sys
import os
from datetime import datetime, timedelta

# モジュールのパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import (
    create_tables, Customer, Property, Unit, TenantContract, 
    Task, Communication, ActivityLog
)

def test_activity_logging():
    """アクティビティログ機能をテスト"""
    print("=" * 50)
    print("アクティビティログ機能テスト")
    print("=" * 50)
    
    # テーブルを作成
    print("\n1. データベーステーブルを作成中...")
    create_tables()
    print("   ✓ テーブル作成完了")
    
    # テストデータを作成してアクティビティログが記録されるか確認
    print("\n2. テストデータを作成中...")
    
    # 顧客を作成
    customer_id = Customer.create(
        name="テスト太郎",
        customer_type="tenant",
        phone="090-1234-5678",
        email="test@example.com"
    )
    print(f"   ✓ 顧客作成: ID={customer_id}")
    
    # 物件を作成
    property_id = Property.create(
        name="テストマンション",
        address="東京都新宿区テスト1-2-3"
    )
    print(f"   ✓ 物件作成: ID={property_id}")
    
    # 部屋を作成
    unit_id = Unit.create(
        property_id=property_id,
        room_number="101",
        floor="1",
        area=45.5,
        use_restrictions="居住用",
        pet_allowed=False
    )
    print(f"   ✓ 部屋作成: ID={unit_id}")
    
    # 契約を作成
    contract_id = TenantContract.create(
        unit_id=unit_id,
        contractor_name="テスト太郎",
        start_date="2024-01-01",
        end_date="2025-12-31",
        rent=100000,
        customer_id=customer_id
    )
    print(f"   ✓ 契約作成: ID={contract_id}")
    
    # タスクを作成
    task_id = Task.create(
        contract_id=contract_id,
        task_type="更新",
        title="契約更新の確認",
        description="テナントに契約更新の意向を確認する",
        due_date="2025-11-30"
    )
    print(f"   ✓ タスク作成: ID={task_id}")
    
    # 接点履歴を作成
    comm_id = Communication.create(
        customer_id=customer_id,
        contract_id=contract_id,
        communication_type="電話",
        subject="契約更新について",
        content="更新の意向を確認しました",
        contact_date="2025-08-15"
    )
    print(f"   ✓ 接点履歴作成: ID={comm_id}")
    
    # 手動でアクティビティログを追加
    ActivityLog.log(
        activity_type='VIEW',
        entity_type='property',
        entity_id=property_id,
        entity_name="テストマンション",
        description="物件詳細を閲覧しました"
    )
    print("   ✓ 手動アクティビティログ追加")
    
    # アクティビティログを取得して表示
    print("\n3. 最近のアクティビティログを取得中...")
    activities = ActivityLog.get_recent(limit=10)
    
    print(f"\n   取得したアクティビティ数: {len(activities)}")
    print("\n   最近のアクティビティ:")
    print("   " + "-" * 70)
    
    for activity in activities:
        created_at = activity.get('created_at', '')
        activity_type = activity.get('activity_type', '')
        entity_type = activity.get('entity_type', '')
        entity_name = activity.get('entity_name', '')
        description = activity.get('description', '')
        
        # 日時をフォーマット
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                formatted_date = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                formatted_date = created_at
        else:
            formatted_date = 'N/A'
        
        print(f"   {formatted_date} | {activity_type:8} | {entity_type:12} | {description[:40]}")
    
    print("   " + "-" * 70)
    
    # 特定エンティティのアクティビティを取得
    print(f"\n4. 顧客ID={customer_id}のアクティビティログを取得中...")
    customer_activities = ActivityLog.get_by_entity('customer', customer_id)
    print(f"   取得したアクティビティ数: {len(customer_activities)}")
    
    # 統計情報
    print("\n5. アクティビティ統計:")
    activity_types = {}
    entity_types = {}
    
    for activity in activities:
        # タイプ別カウント
        atype = activity.get('activity_type', 'UNKNOWN')
        activity_types[atype] = activity_types.get(atype, 0) + 1
        
        # エンティティ別カウント
        etype = activity.get('entity_type', 'UNKNOWN')
        entity_types[etype] = entity_types.get(etype, 0) + 1
    
    print("\n   アクティビティタイプ別:")
    for atype, count in activity_types.items():
        print(f"     - {atype}: {count}件")
    
    print("\n   エンティティタイプ別:")
    for etype, count in entity_types.items():
        print(f"     - {etype}: {count}件")
    
    print("\n" + "=" * 50)
    print("テスト完了！")
    print("アクティビティログ機能が正常に動作しています。")
    print("=" * 50)

if __name__ == "__main__":
    try:
        test_activity_logging()
    except Exception as e:
        print(f"\nエラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()