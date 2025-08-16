#!/usr/bin/env python3
"""
顧客オーナーの物件紐づけ機能のテストスクリプト
"""
import sys
import os
from datetime import datetime

# モジュールのパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import (
    create_tables, Customer, Property, Unit, ActivityLog
)

def test_customer_property_linking():
    """顧客とオーナーの物件紐づけ機能をテスト"""
    print("=" * 70)
    print("顧客オーナーの物件紐づけ機能テスト")
    print("=" * 70)
    
    # 1. データベーステーブルを作成
    print("\n1. データベーステーブルを作成中...")
    create_tables()
    print("   ✓ テーブル作成完了")
    
    # 2. テスト用オーナー顧客を作成
    print("\n2. テスト用オーナー顧客を作成中...")
    
    owner1_id = Customer.create(
        name="株式会社東京不動産",
        customer_type="owner",
        phone="03-1111-1111",
        email="tokyo@realestate.co.jp",
        address="東京都千代田区大手町1-1-1 東京ビル10F",
        memo="大手不動産会社"
    )
    print(f"   ✓ オーナー1作成: {Customer.get_by_id(owner1_id)['name']} (ID: {owner1_id})")
    
    owner2_id = Customer.create(
        name="個人投資家 田中太郎",
        customer_type="owner",
        phone="090-2222-3333",
        email="tanaka@example.com",
        address="東京都港区六本木2-2-2",
        memo="個人投資家、複数物件所有"
    )
    print(f"   ✓ オーナー2作成: {Customer.get_by_id(owner2_id)['name']} (ID: {owner2_id})")
    
    owner3_id = Customer.create(
        name="相続物件管理会社",
        customer_type="owner",
        phone="03-4444-5555",
        email="souzoku@management.com",
        address="東京都新宿区西新宿3-3-3"
    )
    print(f"   ✓ オーナー3作成: {Customer.get_by_id(owner3_id)['name']} (ID: {owner3_id})")
    
    # 3. テスト用物件を作成
    print("\n3. テスト用物件を作成中...")
    
    property1_id = Property.create(
        name="東京駅前ビル",
        address="東京都千代田区丸の内1-1-1",
        structure="SRC造15階建",
        registry_owner="株式会社東京不動産"
    )
    print(f"   ✓ 物件1作成: 東京駅前ビル (ID: {property1_id})")
    
    property2_id = Property.create(
        name="渋谷商業ビル",
        address="東京都渋谷区渋谷2-2-2",
        structure="RC造8階建",
        registry_owner="田中太郎"
    )
    print(f"   ✓ 物件2作成: 渋谷商業ビル (ID: {property2_id})")
    
    property3_id = Property.create(
        name="新宿マンション",
        address="東京都新宿区新宿3-3-3",
        structure="RC造12階建",
        registry_owner="相続物件管理会社"
    )
    print(f"   ✓ 物件3作成: 新宿マンション (ID: {property3_id})")
    
    # 4. オーナーと物件を紐づけ
    print("\n4. オーナーと物件を紐づけ中...")
    
    # 株式会社東京不動産 → 東京駅前ビル（100%単独所有）
    Property.add_owner(property1_id, owner1_id, 100.0, is_primary=True)
    print(f"   ✓ 株式会社東京不動産 → 東京駅前ビル（100%単独所有）")
    
    # 個人投資家田中太郎 → 渋谷商業ビル（70%主要所有）+ 新宿マンション（30%共同所有）
    Property.add_owner(property2_id, owner2_id, 70.0, is_primary=True)
    Property.add_owner(property3_id, owner2_id, 30.0, is_primary=False)
    print(f"   ✓ 個人投資家 田中太郎 → 渋谷商業ビル（70%主要所有）")
    print(f"   ✓ 個人投資家 田中太郎 → 新宿マンション（30%共同所有）")
    
    # 相続物件管理会社 → 新宿マンション（70%主要所有）
    Property.add_owner(property3_id, owner3_id, 70.0, is_primary=True)
    print(f"   ✓ 相続物件管理会社 → 新宿マンション（70%主要所有）")
    
    # 5. テスト用部屋を作成（区分所有テスト用）
    print("\n5. テスト用部屋を作成中（区分所有テスト用）...")
    
    unit1_id = Unit.create(
        property_id=property3_id,
        room_number="1001",
        floor="10",
        area=85.5,
        use_restrictions="居住専用"
    )
    
    unit2_id = Unit.create(
        property_id=property3_id,
        room_number="1002", 
        floor="10",
        area=92.0,
        use_restrictions="居住専用"
    )
    print(f"   ✓ 部屋1001, 1002作成 (新宿マンション内)")
    
    # 部屋1001を田中太郎の区分所有に設定
    Unit.add_owner(unit1_id, owner2_id, 100.0, is_primary=True)
    print(f"   ✓ 個人投資家 田中太郎 → 新宿マンション1001号室（100%区分所有）")
    
    # 6. 各オーナーの所有物件を確認
    print("\n6. 各オーナーの所有物件を確認中...")
    
    all_owners = [
        (owner1_id, "株式会社東京不動産"),
        (owner2_id, "個人投資家 田中太郎"),
        (owner3_id, "相続物件管理会社")
    ]
    
    for owner_id, owner_name in all_owners:
        print(f"\n   【{owner_name}の所有物件】")
        
        # 物件レベルの所有
        all_properties = Property.get_all()
        owned_properties = []
        for prop in all_properties:
            owners = Property.get_owners(prop['id'])
            for owner in owners:
                if owner['owner_id'] == owner_id:
                    owned_properties.append((prop, owner))
                    break
        
        if owned_properties:
            print("   ◆ 所有物件:")
            for prop, owner_data in owned_properties:
                primary_text = "（主要）" if owner_data.get('is_primary') else ""
                print(f"     - {prop['name']}: {owner_data['ownership_ratio']:.1f}% {primary_text}")
                print(f"       住所: {prop['address']}")
        else:
            print("   ◆ 所有物件: なし")
        
        # 部屋レベルの所有（区分所有）
        all_units = Unit.get_all()
        owned_units = []
        for unit in all_units:
            owners = Unit.get_owners(unit['id'])
            for owner in owners:
                if owner['owner_id'] == owner_id:
                    prop = Property.get_by_id(unit['property_id'])
                    owned_units.append((unit, owner, prop))
                    break
        
        if owned_units:
            print("   ◆ 区分所有部屋:")
            for unit, owner_data, prop in owned_units:
                primary_text = "（主要）" if owner_data.get('is_primary') else ""
                print(f"     - {prop['name']} {unit['room_number']}号室: {owner_data['ownership_ratio']:.1f}% {primary_text}")
                print(f"       面積: {unit.get('area', 0)}㎡, 階: {unit.get('floor', '')}F")
        else:
            print("   ◆ 区分所有部屋: なし")
    
    # 7. アクティビティログを確認
    print("\n7. アクティビティログを確認中...")
    activities = ActivityLog.get_recent(limit=15)
    
    print(f"   最近のアクティビティ（物件・オーナー関連）:")
    print("   " + "-" * 65)
    for activity in activities:
        if any(keyword in activity.get('description', '') for keyword in ['オーナー', '物件', '部屋']):
            created_at = activity.get('created_at', '')[:19]
            entity_type = activity.get('entity_type', '')
            description = activity.get('description', '')
            print(f"   {created_at} | {entity_type:10} | {description}")
    print("   " + "-" * 65)
    
    # 8. 統計情報
    print("\n8. 統計情報:")
    
    all_customers = Customer.get_all()
    owners = [c for c in all_customers if c.get('type') == 'owner']
    
    print(f"   - 総オーナー数: {len(owners)}")
    
    # 物件所有状況
    properties_with_owners = 0
    total_ownership_records = 0
    
    all_properties = Property.get_all()
    for prop in all_properties:
        owners_of_prop = Property.get_owners(prop['id'])
        if owners_of_prop:
            properties_with_owners += 1
            total_ownership_records += len(owners_of_prop)
    
    print(f"   - 総物件数: {len(all_properties)}")
    print(f"   - オーナー設定済み物件数: {properties_with_owners}")
    print(f"   - 物件所有権記録数: {total_ownership_records}")
    
    # 部屋所有状況
    units_with_owners = 0
    total_unit_ownership_records = 0
    
    all_units = Unit.get_all()
    for unit in all_units:
        owners_of_unit = Unit.get_owners(unit['id'])
        if owners_of_unit:
            units_with_owners += 1
            total_unit_ownership_records += len(owners_of_unit)
    
    print(f"   - 総部屋数: {len(all_units)}")
    print(f"   - 区分所有設定済み部屋数: {units_with_owners}")
    print(f"   - 部屋所有権記録数: {total_unit_ownership_records}")
    
    # 9. オーナー別所有物件数
    print("\n9. オーナー別所有物件数:")
    
    for owner_id, owner_name in all_owners:
        property_count = 0
        unit_count = 0
        
        # 物件数をカウント
        for prop in all_properties:
            owners = Property.get_owners(prop['id'])
            if any(owner['owner_id'] == owner_id for owner in owners):
                property_count += 1
        
        # 部屋数をカウント
        for unit in all_units:
            owners = Unit.get_owners(unit['id'])
            if any(owner['owner_id'] == owner_id for owner in owners):
                unit_count += 1
        
        print(f"   - {owner_name}: 物件 {property_count}件、部屋 {unit_count}室")
    
    print("\n" + "=" * 70)
    print("テスト完了！")
    print("顧客オーナーの物件紐づけ機能が正常に動作しています。")
    print("顧客タブの「所有物件管理」タブで各オーナーの物件を確認できます。")
    print("=" * 70)

if __name__ == "__main__":
    try:
        test_customer_property_linking()
    except Exception as e:
        print(f"\nエラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()