#!/usr/bin/env python3
"""
UI機能の実装確認テストスクリプト
実際のUI要素が正しく作成されているかをテスト
"""
import sys
import os

# モジュールのパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from models import create_tables, Customer, Property, Unit

def test_ui_implementation():
    """UI実装をテスト"""
    print("=" * 60)
    print("UI機能の実装確認テスト")
    print("=" * 60)
    
    # 1. データベース準備
    print("\n1. データベース準備中...")
    create_tables()
    print("   ✓ データベース準備完了")
    
    # 2. QApplicationの初期化（UIテスト用）
    print("\n2. QApplication初期化中...")
    app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()
    print("   ✓ QApplication初期化完了")
    
    # 3. 顧客タブのテスト
    print("\n3. 顧客タブのUI要素をテスト中...")
    try:
        from customer_tab import CustomerTab
        customer_tab = CustomerTab()
        
        # タブウィジェットの確認
        if hasattr(customer_tab, 'tab_widget'):
            print("   ✓ タブウィジェットが作成されている")
            tab_count = customer_tab.tab_widget.count()
            print(f"   ✓ タブ数: {tab_count}個")
            
            for i in range(tab_count):
                tab_text = customer_tab.tab_widget.tabText(i)
                print(f"     - タブ{i+1}: {tab_text}")
        
        # 所有物件管理の要素確認
        if hasattr(customer_tab, 'property_combo'):
            print("   ✓ 物件選択コンボボックスが作成されている")
        if hasattr(customer_tab, 'owned_properties_table'):
            print("   ✓ 所有物件テーブルが作成されている")
        if hasattr(customer_tab, 'owned_units_table'):
            print("   ✓ 所有部屋テーブルが作成されている")
        if hasattr(customer_tab, 'add_property_button'):
            print("   ✓ 物件追加ボタンが作成されている")
            
    except Exception as e:
        print(f"   ✗ 顧客タブエラー: {str(e)}")
    
    # 4. 物件タブのテスト
    print("\n4. 物件タブのUI要素をテスト中...")
    try:
        from property_tab import PropertyTab
        property_tab = PropertyTab()
        
        # オーナー関連要素の確認
        if hasattr(property_tab, 'owner_combo'):
            print("   ✓ オーナー選択コンボボックスが作成されている")
        if hasattr(property_tab, 'owner_table'):
            print("   ✓ オーナーテーブルが作成されている")
        if hasattr(property_tab, 'add_owner_button'):
            print("   ✓ オーナー追加ボタンが作成されている")
            
    except Exception as e:
        print(f"   ✗ 物件タブエラー: {str(e)}")
    
    # 5. 部屋タブのテスト
    print("\n5. 部屋タブのUI要素をテスト中...")
    try:
        from unit_tab import UnitTab
        unit_tab = UnitTab()
        
        # オーナー関連要素の確認
        if hasattr(unit_tab, 'owner_combo'):
            print("   ✓ オーナー選択コンボボックスが作成されている")
        if hasattr(unit_tab, 'owner_table'):
            print("   ✓ オーナーテーブルが作成されている")
        if hasattr(unit_tab, 'add_owner_button'):
            print("   ✓ オーナー追加ボタンが作成されている")
            
    except Exception as e:
        print(f"   ✗ 部屋タブエラー: {str(e)}")
    
    # 6. ダッシュボードタブのテスト
    print("\n6. ダッシュボードタブのUI要素をテスト中...")
    try:
        from dashboard_tab import DashboardTab
        dashboard_tab = DashboardTab()
        
        # アクティビティテーブルの確認
        if hasattr(dashboard_tab, 'activity_table'):
            print("   ✓ アクティビティテーブルが作成されている")
            
    except Exception as e:
        print(f"   ✗ ダッシュボードタブエラー: {str(e)}")
    
    # 7. データベース機能のテスト
    print("\n7. データベース機能をテスト中...")
    try:
        # テストオーナーを作成
        owner_id = Customer.create(
            name="テストオーナー",
            customer_type="owner",
            phone="090-1234-5678"
        )
        print(f"   ✓ オーナー作成: ID={owner_id}")
        
        # テスト物件を作成
        property_id = Property.create(
            name="テスト物件",
            address="テスト住所"
        )
        print(f"   ✓ 物件作成: ID={property_id}")
        
        # オーナーと物件を紐づけ
        Property.add_owner(property_id, owner_id, 100.0, is_primary=True)
        print("   ✓ オーナーと物件の紐づけ完了")
        
        # 所有物件を取得
        owners = Property.get_owners(property_id)
        print(f"   ✓ 所有者取得: {len(owners)}人")
        
    except Exception as e:
        print(f"   ✗ データベース機能エラー: {str(e)}")
    
    # 8. メソッドの存在確認
    print("\n8. 重要なメソッドの存在確認...")
    
    # CustomerTabのメソッド確認
    customer_methods = [
        'on_customer_selected', 'load_owned_properties', 'load_owned_units',
        'add_property_to_owner', 'remove_property_from_owner'
    ]
    
    for method in customer_methods:
        if hasattr(customer_tab, method):
            print(f"   ✓ CustomerTab.{method} が実装されている")
        else:
            print(f"   ✗ CustomerTab.{method} が見つからない")
    
    # PropertyTabのメソッド確認
    property_methods = [
        'add_owner_to_property', 'load_property_owners', 'remove_owner_from_property'
    ]
    
    for method in property_methods:
        if hasattr(property_tab, method):
            print(f"   ✓ PropertyTab.{method} が実装されている")
        else:
            print(f"   ✗ PropertyTab.{method} が見つからない")
    
    print("\n" + "=" * 60)
    print("UI機能実装確認テスト完了！")
    print("上記の結果を確認して、✓マークが多ければ正常に実装されています。")
    print("=" * 60)
    
    # アプリケーションを終了しない（バックグラウンドで起動したままにする）
    return True

if __name__ == "__main__":
    try:
        test_ui_implementation()
    except Exception as e:
        print(f"\nエラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()