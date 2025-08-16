#!/usr/bin/env python3
"""
接点履歴の修正をテストするスクリプト
"""
import sys
sys.path.append('.')

def test_communication_models():
    """Communicationモデルをテスト"""
    print("接点履歴モデルのテストを開始...")
    
    try:
        from models import Customer, Communication, create_tables
        
        print("1. データベーステーブルを初期化...")
        create_tables()
        print("✅ テーブル初期化成功")
        
        print("\n2. テスト用顧客を作成...")
        customer_id = Customer.create(
            name="テスト顧客",
            phone="090-1234-5678",
            email="test@example.com"
        )
        print(f"✅ 顧客作成成功 (ID: {customer_id})")
        
        print("\n3. テスト用接点履歴を作成...")
        comm_id = Communication.create(
            customer_id=customer_id,
            contract_id=None,
            communication_type="電話",
            subject="テスト問い合わせ",
            content="テスト用の接点履歴です。",
            contact_date="2024-12-12",
            direction="受信",
            next_action="フォローアップ予定"
        )
        print(f"✅ 接点履歴作成成功 (ID: {comm_id})")
        
        print("\n4. 全接点履歴を取得...")
        all_comms = Communication.get_all()
        print(f"✅ 全接点履歴取得成功 (件数: {len(all_comms)})")
        
        if all_comms:
            first_comm = all_comms[0]
            print(f"   最初の接点履歴:")
            print(f"   - 顧客名: {first_comm.get('customer_name')}")
            print(f"   - 件名: {first_comm.get('subject')}")
            print(f"   - 方向: {first_comm.get('direction')}")
            print(f"   - 接触日: {first_comm.get('contact_date')}")
        
        print("\n5. 顧客別接点履歴を取得...")
        customer_comms = Communication.get_by_customer(customer_id)
        print(f"✅ 顧客別接点履歴取得成功 (件数: {len(customer_comms)})")
        
        print("\n🎉 全てのテスト成功！接点履歴の修正は完了しています。")
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_communication_models()
    sys.exit(0 if success else 1)