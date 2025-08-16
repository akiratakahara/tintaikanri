#!/usr/bin/env python3
"""
OCR機能テストスクリプト
"""

import os
import sys
from gemini_ocr import GeminiOCR

def test_ocr_functionality():
    """OCR機能をテスト"""
    print("🔍 OCR機能テストを開始します...")
    
    try:
        # OCRクラスの初期化
        ocr = GeminiOCR()
        print("✅ GeminiOCRクラスの初期化が完了しました")
        
        # テスト用の画像ファイルパスを確認
        test_image_path = input("テスト用の画像ファイルパスを入力してください: ").strip()
        
        if not os.path.exists(test_image_path):
            print("❌ 指定されたファイルが存在しません")
            return
        
        print(f"📁 テストファイル: {test_image_path}")
        
        # テキスト抽出テスト
        print("\n📄 テキスト抽出テストを実行中...")
        text_result = ocr.extract_text_from_image(test_image_path)
        print("📋 抽出結果:")
        print("-" * 50)
        print(text_result)
        print("-" * 50)
        
        # チェックリスト抽出テスト
        print("\n📋 チェックリスト抽出テストを実行中...")
        checklist_result = ocr.extract_checklist_items(test_image_path)
        print("📋 チェックリスト結果:")
        print("-" * 50)
        print(checklist_result)
        print("-" * 50)
        
        print("\n✅ OCR機能テストが完了しました")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        print("\n🔧 トラブルシューティング:")
        print("1. .envファイルにAPIキーが設定されているか確認")
        print("2. インターネット接続を確認")
        print("3. 画像ファイルが破損していないか確認")

def test_api_connection():
    """API接続をテスト"""
    print("🌐 API接続テストを開始します...")
    
    try:
        from config import GEMINI_API_KEY
        
        if not GEMINI_API_KEY:
            print("❌ APIキーが設定されていません")
            print("🔧 .envファイルにGEMINI_API_KEYを設定してください")
            return
        
        print("✅ APIキーが設定されています")
        
        # 簡単なAPI呼び出しテスト
        ocr = GeminiOCR()
        print("✅ GeminiOCRクラスの初期化が成功しました")
        print("✅ API接続テストが完了しました")
        
    except Exception as e:
        print(f"❌ API接続テストでエラーが発生しました: {str(e)}")

def main():
    """メイン関数"""
    print("🏠 賃貸顧客管理システム - OCR機能テスト")
    print("=" * 50)
    
    while True:
        print("\n📋 テストメニュー:")
        print("1. API接続テスト")
        print("2. OCR機能テスト")
        print("3. 終了")
        
        choice = input("\n選択してください (1-3): ").strip()
        
        if choice == "1":
            test_api_connection()
        elif choice == "2":
            test_ocr_functionality()
        elif choice == "3":
            print("👋 テストを終了します")
            break
        else:
            print("❌ 無効な選択です。1-3の数字を入力してください")

if __name__ == "__main__":
    main() 