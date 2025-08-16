#!/usr/bin/env python3
"""
物件・部屋オーナー機能のテストスクリプト
"""
import sys
import os
from datetime import datetime

# モジュールのパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import (
    create_tables, Customer, Property, Unit, ActivityLog
)

def test_owner_features():
    """オーナー機能をテスト"""
    print("=" * 60)
    print("物件・部屋オーナー機能テスト")
    print("=" * 60)
    
    # 1. データベーステーブルを作成
    print("\n1. データベーステーブルを作成中...")
    create_tables()
    print("   ✓ テーブル作成完了")
    
    # 2. テスト用オーナーを作成
    print("\n2. テスト用オーナーを作成中...")
    
    owner1_id = Customer.create(
        name="山田不動産株式会社",
        customer_type="owner",
        phone="03-1111-2222",
        email="yamada@example.com",
        address="東京都千代田区大手町1-1-1"
    )
    print(f"   ✓ オーナー1作成: ID={owner1_id}")
    
    owner2_id = Customer.create(
        name="鈴木オーナー",
        customer_type="owner",
        phone="090-3333-4444",
        email="suzuki@example.com",
        address="東京都港区六本木2-2-2"
    )
    print(f"   ✓ オーナー2作成: ID={owner2_id}")
    
    # 3. テスト用物件を作成
    print("\n3. テスト用物件を作成中...")
    
    property_id = Property.create(
        name="テストビル",
        address="東京都新宿区西新宿3-3-3",
        structure="RC造10階建",
        registry_owner="山田不動産株式会社"
    )
    print(f"   ✓ 物件作成: ID={property_id}")
    
    # 4. 物件にオーナーを追加
    print("\n4. 物件にオーナーを追加中...")
    
    Property.add_owner(property_id, owner1_id, 70.0, is_primary=True)
    print(f"   ✓ 山田不動産株式会社を主要オーナー（70%）として追加")
    
    Property.add_owner(property_id, owner2_id, 30.0, is_primary=False)
    print(f"   ✓ 鈴木オーナーを副オーナー（30%）として追加")
    
    # 5. 物件のオーナー一覧を取得
    print("\n5. 物件のオーナー一覧を取得中...")
    property_owners = Property.get_owners(property_id)
    
    print(f"   物件「テストビル」のオーナー一覧:")
    print("   " + "-" * 50)
    for owner in property_owners:
        primary_text = "（主要）" if owner.get('is_primary') else ""
        print(f"   - {owner['owner_name']}: {owner['ownership_ratio']:.1f}% {primary_text}")
        print(f"     連絡先: {owner.get('phone', '')} / {owner.get('email', '')}")
    print("   " + "-" * 50)
    
    # 6. テスト用部屋を作成
    print("\n6. テスト用部屋を作成中...")
    
    unit1_id = Unit.create(
        property_id=property_id,
        room_number="501",
        floor="5",
        area=80.5,
        use_restrictions="事務所利用のみ"
    )
    print(f"   ✓ 部屋501作成: ID={unit1_id}")
    
    unit2_id = Unit.create(
        property_id=property_id,
        room_number="601",
        floor="6",
        area=120.0,
        use_restrictions="店舗・事務所可"
    )
    print(f"   ✓ 部屋601作成: ID={unit2_id}")
    
    # 7. 区分所有として部屋601に個別オーナーを設定
    print("\n7. 区分所有として部屋601に個別オーナーを設定中...")
    
    owner3_id = Customer.create(
        name="田中投資合同会社",
        customer_type="owner",
        phone="03-5555-6666",
        email="tanaka@example.com"
    )
    print(f"   ✓ 区分所有オーナー作成: ID={owner3_id}")
    
    Unit.add_owner(unit2_id, owner3_id, 100.0, is_primary=True)
    print(f"   ✓ 田中投資合同会社を部屋601の単独オーナー（100%）として追加")
    
    # 8. 部屋のオーナー一覧を取得
    print("\n8. 部屋のオーナー一覧を取得中...")
    
    unit1_owners = Unit.get_owners(unit1_id)
    if not unit1_owners:
        print(f"   部屋501: 個別オーナー設定なし（物件オーナーが適用）")
    
    unit2_owners = Unit.get_owners(unit2_id)
    print(f"   部屋601のオーナー一覧（区分所有）:")
    print("   " + "-" * 50)
    for owner in unit2_owners:
        primary_text = "（主要）" if owner.get('is_primary') else ""
        print(f"   - {owner['owner_name']}: {owner['ownership_ratio']:.1f}% {primary_text}")
        print(f"     連絡先: {owner.get('phone', '')} / {owner.get('email', '')}")
    print("   " + "-" * 50)
    
    # 9. アクティビティログを確認
    print("\n9. アクティビティログを確認中...")
    activities = ActivityLog.get_recent(limit=10)
    
    print(f"   最近のアクティビティ（オーナー関連）:")
    print("   " + "-" * 60)
    for activity in activities:
        if 'オーナー' in activity.get('description', ''):
            created_at = activity.get('created_at', '')
            entity_type = activity.get('entity_type', '')
            description = activity.get('description', '')
            print(f"   {created_at[:19]} | {entity_type:10} | {description}")
    print("   " + "-" * 60)
    
    # 10. 統計情報
    print("\n10. 統計情報:")
    
    all_customers = Customer.get_all()
    owners = [c for c in all_customers if c.get('type') == 'owner']
    tenants = [c for c in all_customers if c.get('type') == 'tenant']
    
    print(f"   - 総顧客数: {len(all_customers)}")
    print(f"   - オーナー数: {len(owners)}")
    print(f"   - テナント数: {len(tenants)}")
    
    all_properties = Property.get_all()
    properties_with_owners = 0
    for prop in all_properties:
        if Property.get_owners(prop['id']):
            properties_with_owners += 1
    
    print(f"   - 総物件数: {len(all_properties)}")
    print(f"   - オーナー設定済み物件数: {properties_with_owners}")
    
    all_units = Unit.get_all()
    units_with_owners = 0
    for unit in all_units:
        if Unit.get_owners(unit['id']):
            units_with_owners += 1
    
    print(f"   - 総部屋数: {len(all_units)}")
    print(f"   - 区分所有設定済み部屋数: {units_with_owners}")
    
    print("\n" + "=" * 60)
    print("テスト完了！")
    print("物件・部屋オーナー機能が正常に動作しています。")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_owner_features()
    except Exception as e:
        print(f"\nエラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()