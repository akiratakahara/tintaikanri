#!/usr/bin/env python3
"""
OCR処理デバッグスクリプト
"""

import os
import sys
from gemini_ocr import GeminiOCR
from registry_ocr import RegistryOCR

def debug_ocr_extraction(image_path: str):
    """OCR抽出処理をデバッグ"""
    print("🔍 OCR抽出デバッグを開始します...")
    print(f"📁 対象ファイル: {image_path}")
    
    if not os.path.exists(image_path):
        print("❌ ファイルが存在しません")
        return
    
    try:
        # GeminiOCRでテキスト抽出
        print("\n📄 GeminiOCRでテキスト抽出中...")
        ocr = GeminiOCR()
        raw_text = ocr.extract_text_from_image(image_path)
        
        print("=== 生のOCR結果 ===")
        print(raw_text)
        print("===================")
        
        # RegistryOCRで構造化抽出
        print("\n🏗️ RegistryOCRで構造化抽出中...")
        registry_ocr = RegistryOCR()
        
        # 建物情報抽出
        building_info = registry_ocr.extract_building_info(image_path)
        print("\n=== 建物情報抽出結果 ===")
        for key, value in building_info.items():
            print(f"{key}: {value}")
        print("========================")
        
        # 土地情報抽出
        land_info = registry_ocr.extract_land_info(image_path)
        print("\n=== 土地情報抽出結果 ===")
        for key, value in land_info.items():
            print(f"{key}: {value}")
        print("========================")
        
        # 抽出結果の分析
        print("\n📊 抽出結果分析:")
        total_items = len(building_info) + len(land_info)
        extracted_items = sum(1 for v in building_info.values() if v is not None) + \
                         sum(1 for v in land_info.values() if v is not None)
        
        print(f"総項目数: {total_items}")
        print(f"抽出成功項目数: {extracted_items}")
        print(f"抽出成功率: {extracted_items/total_items*100:.1f}%")
        
        if extracted_items == 0:
            print("\n⚠️ 抽出に失敗しました。以下を確認してください:")
            print("1. 画像の品質（解像度、コントラスト）")
            print("2. 画像の向き（回転していないか）")
            print("3. 文字の読みやすさ")
            print("4. 登記簿謄本の形式が標準的か")
            
            # 生テキストから手動で情報を探す
            print("\n🔍 生テキストから手動検索:")
            search_keywords = [
                "所有者", "権利者", "氏名", "所在", "住所", "構造", "階数", 
                "面積", "床面積", "地積", "建築", "竣工", "登記", "抵当権"
            ]
            
            for keyword in search_keywords:
                if keyword in raw_text:
                    # キーワード周辺のテキストを抽出
                    start = max(0, raw_text.find(keyword) - 20)
                    end = min(len(raw_text), raw_text.find(keyword) + 50)
                    context = raw_text[start:end]
                    print(f"'{keyword}' 周辺: {context}")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """メイン関数"""
    print("🏠 賃貸顧客管理システム - OCRデバッグツール")
    print("=" * 50)
    
    # ファイルパスを入力
    image_path = input("デバッグする画像ファイルのパスを入力してください: ").strip()
    
    if not image_path:
        print("❌ ファイルパスが入力されていません")
        return
    
    debug_ocr_extraction(image_path)

if __name__ == "__main__":
    main() 