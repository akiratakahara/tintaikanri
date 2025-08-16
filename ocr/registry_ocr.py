#!/usr/bin/env python3
"""
登記簿謄本OCR処理クラス
"""

import re
import os
from typing import Dict, Any, Optional
from gemini_ocr import GeminiOCR

class RegistryOCR:
    """登記簿謄本専用OCR処理クラス"""
    
    def __init__(self):
        try:
            self.ocr = GeminiOCR()
        except Exception as e:
            print(f"OCR初期化エラー: {e}")
            self.ocr = None
    
    def extract_building_info(self, pdf_path: str) -> Dict[str, Any]:
        """建物登記簿から情報を抽出"""
        try:
            if not self.ocr:
                return {}
            
            # OCRでテキスト抽出
            ocr_text = self.ocr.extract_text_from_image(pdf_path)
            
            # デバッグ用：OCR結果を表示
            print("=== OCR結果（建物登記簿） ===")
            print(ocr_text)
            print("================================")
            
            # 建物情報を抽出
            building_info = {
                'registry_owner': self._extract_owner(ocr_text),
                'registry_address': self._extract_building_address(ocr_text),
                'building_structure': self._extract_building_structure(ocr_text),
                'building_floors': self._extract_building_floors(ocr_text),
                'building_area': self._extract_building_area(ocr_text),
                'building_date': self._extract_building_date(ocr_text),
                'registry_date': self._extract_registry_date(ocr_text),
                'mortgage_info': self._extract_mortgage_info(ocr_text),
                'notes': ''
            }
            
            # デバッグ用：抽出結果を表示
            print("=== 抽出結果（建物登記簿） ===")
            for key, value in building_info.items():
                print(f"{key}: {value}")
            print("================================")
            
            return building_info
            
        except Exception as e:
            print(f"建物登記簿OCR処理エラー: {e}")
            return {}
    
    def extract_land_info(self, pdf_path: str) -> Dict[str, Any]:
        """土地登記簿から情報を抽出"""
        try:
            if not self.ocr:
                return {}
            
            # OCRでテキスト抽出
            ocr_text = self.ocr.extract_text_from_image(pdf_path)
            
            # デバッグ用：OCR結果を表示
            print("=== OCR結果（土地登記簿） ===")
            print(ocr_text)
            print("================================")
            
            # 土地情報を抽出
            land_info = {
                'land_number': self._extract_land_number(ocr_text),
                'land_owner': self._extract_owner(ocr_text),
                'land_address': self._extract_land_address(ocr_text),
                'land_area': self._extract_land_area(ocr_text),
                'land_use': self._extract_land_use(ocr_text),
                'registry_date': self._extract_registry_date(ocr_text),
                'mortgage_info': self._extract_mortgage_info(ocr_text),
                'notes': ''
            }
            
            # デバッグ用：抽出結果を表示
            print("=== 抽出結果（土地登記簿） ===")
            for key, value in land_info.items():
                print(f"{key}: {value}")
            print("================================")
            
            return land_info
            
        except Exception as e:
            print(f"土地登記簿OCR処理エラー: {e}")
            return {}
    
    def _extract_owner(self, text: str) -> Optional[str]:
        """所有者を抽出（改善版）"""
        # より柔軟なパターン
        patterns = [
            # 標準的なパターン
            r'所有者[：:]\s*([^\n\r]+)',
            r'権利者[：:]\s*([^\n\r]+)',
            r'氏名[：:]\s*([^\n\r]+)',
            # スペース区切りパターン
            r'所有者\s+([^\n\r]+)',
            r'権利者\s+([^\n\r]+)',
            r'氏名\s+([^\n\r]+)',
            # 括弧付きパターン
            r'所有者[（(]([^）)]+)[）)]',
            r'権利者[（(]([^）)]+)[）)]',
            r'氏名[（(]([^）)]+)[）)]',
            # 行末パターン
            r'所有者[：:]\s*([^、。\n\r]+)',
            r'権利者[：:]\s*([^、。\n\r]+)',
            r'氏名[：:]\s*([^、。\n\r]+)',
            # より広範囲の検索
            r'所有者[：:]\s*([^、。\n\r]{2,50})',
            r'権利者[：:]\s*([^、。\n\r]{2,50})',
            r'氏名[：:]\s*([^、。\n\r]{2,50})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
            if match:
                result = match.group(1).strip()
                if result and len(result) > 1:  # 空でないことを確認
                    print(f"所有者抽出成功: {result}")
                    return result
        
        # フォールバック: 一般的な人名パターンを検索
        name_patterns = [
            r'([一-龯]{2,4}\s*[一-龯]{1,2})',  # 漢字の名前
            r'([ァ-ヶ]{2,10})',  # カタカナの名前
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if match and len(match.strip()) > 1:
                    print(f"所有者抽出（フォールバック）: {match}")
                    return match.strip()
        
        print("所有者抽出失敗")
        return None
    
    def _extract_building_address(self, text: str) -> Optional[str]:
        """建物住所を抽出（改善版）"""
        patterns = [
            # 標準的なパターン
            r'所在[：:]\s*([^\n\r]+)',
            r'住所[：:]\s*([^\n\r]+)',
            r'建物の所在[：:]\s*([^\n\r]+)',
            # スペース区切りパターン
            r'所在\s+([^\n\r]+)',
            r'住所\s+([^\n\r]+)',
            r'建物の所在\s+([^\n\r]+)',
            # 住所らしいパターン
            r'([東京都|大阪府|京都府|北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|滋賀県|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県][^\n\r]{5,50})',
            # 郵便番号付き住所
            r'(\d{3}-?\d{4}[^\n\r]{5,50})',
            # より広範囲の検索
            r'所在[：:]\s*([^、。\n\r]{5,100})',
            r'住所[：:]\s*([^、。\n\r]{5,100})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
            if match:
                result = match.group(1).strip()
                if result and len(result) > 5:  # 住所らしい長さを確認
                    print(f"建物住所抽出成功: {result}")
                    return result
        print("建物住所抽出失敗")
        return None
    
    def _extract_building_structure(self, text: str) -> Optional[str]:
        """建物構造を抽出（改善版）"""
        patterns = [
            # 標準的なパターン
            r'構造[：:]\s*([^\n\r]+)',
            r'建物の構造[：:]\s*([^\n\r]+)',
            r'構造種別[：:]\s*([^\n\r]+)',
            # スペース区切りパターン
            r'構造\s+([^\n\r]+)',
            r'建物の構造\s+([^\n\r]+)',
            r'構造種別\s+([^\n\r]+)',
            # 具体的な構造名
            r'(RC造|SRC造|S造|木造|鉄骨造|鉄筋コンクリート造|鉄骨鉄筋コンクリート造|鉄骨造|木造|その他)',
            # より広範囲の検索
            r'構造[：:]\s*([^、。\n\r]{2,20})',
            r'建物の構造[：:]\s*([^、。\n\r]{2,20})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
            if match:
                result = match.group(1).strip()
                if result and len(result) > 1:
                    print(f"建物構造抽出成功: {result}")
                    return result
        print("建物構造抽出失敗")
        return None
    
    def _extract_building_floors(self, text: str) -> Optional[int]:
        """建物階数を抽出（改善版）"""
        patterns = [
            # 標準的なパターン
            r'階数[：:]\s*(\d+)',
            r'建物の階数[：:]\s*(\d+)',
            # スペース区切りパターン
            r'階数\s+(\d+)',
            r'建物の階数\s+(\d+)',
            # 階建て表現
            r'(\d+)階建',
            r'(\d+)階建て',
            # より広範囲の検索
            r'階数[：:]\s*(\d{1,2})',
            r'建物の階数[：:]\s*(\d{1,2})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
            if match:
                result = int(match.group(1))
                if 1 <= result <= 100:  # 妥当な範囲を確認
                    print(f"建物階数抽出成功: {result}")
                    return result
        print("建物階数抽出失敗")
        return None
    
    def _extract_building_area(self, text: str) -> Optional[float]:
        """建物面積を抽出（改善版）"""
        patterns = [
            # 標準的なパターン
            r'床面積[：:]\s*([\d,\.]+)\s*㎡',
            r'建物面積[：:]\s*([\d,\.]+)\s*㎡',
            r'面積[：:]\s*([\d,\.]+)\s*㎡',
            # スペース区切りパターン
            r'床面積\s+([\d,\.]+)\s*㎡',
            r'建物面積\s+([\d,\.]+)\s*㎡',
            r'面積\s+([\d,\.]+)\s*㎡',
            # 単位なしパターン
            r'床面積[：:]\s*([\d,\.]+)',
            r'建物面積[：:]\s*([\d,\.]+)',
            r'面積[：:]\s*([\d,\.]+)',
            # より広範囲の検索
            r'床面積[：:]\s*([\d,\.]{1,10})\s*㎡',
            r'建物面積[：:]\s*([\d,\.]{1,10})\s*㎡'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
            if match:
                area_str = match.group(1).replace(',', '')
                try:
                    result = float(area_str)
                    if 0 < result < 10000:  # 妥当な範囲を確認
                        print(f"建物面積抽出成功: {result}")
                        return result
                except ValueError:
                    continue
        print("建物面積抽出失敗")
        return None
    
    def _extract_building_date(self, text: str) -> Optional[str]:
        """建築年月を抽出（改善版）"""
        patterns = [
            # 標準的なパターン
            r'建築年月[：:]\s*([^\n\r]+)',
            r'建築[：:]\s*([^\n\r]+)',
            r'竣工[：:]\s*([^\n\r]+)',
            # スペース区切りパターン
            r'建築年月\s+([^\n\r]+)',
            r'建築\s+([^\n\r]+)',
            r'竣工\s+([^\n\r]+)',
            # 日付パターン
            r'(\d{4}年\d{1,2}月)',
            r'(\d{4}/\d{1,2})',
            r'(\d{4}-\d{1,2})',
            # より広範囲の検索
            r'建築年月[：:]\s*([^、。\n\r]{5,20})',
            r'建築[：:]\s*([^、。\n\r]{5,20})',
            r'竣工[：:]\s*([^、。\n\r]{5,20})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
            if match:
                result = match.group(1).strip()
                if result and len(result) > 3:
                    print(f"建築年月抽出成功: {result}")
                    return result
        print("建築年月抽出失敗")
        return None
    
    def _extract_land_number(self, text: str) -> Optional[str]:
        """土地番号を抽出（改善版）"""
        patterns = [
            # 標準的なパターン
            r'土地番号[：:]\s*([^\n\r]+)',
            r'番地[：:]\s*([^\n\r]+)',
            r'地番[：:]\s*([^\n\r]+)',
            # スペース区切りパターン
            r'土地番号\s+([^\n\r]+)',
            r'番地\s+([^\n\r]+)',
            r'地番\s+([^\n\r]+)',
            # 番地パターン
            r'(\d+-\d+)',
            r'(\d+丁目\d+番\d+号)',
            r'(\d+番\d+号)',
            # より広範囲の検索
            r'土地番号[：:]\s*([^、。\n\r]{2,20})',
            r'番地[：:]\s*([^、。\n\r]{2,20})',
            r'地番[：:]\s*([^、。\n\r]{2,20})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
            if match:
                result = match.group(1).strip()
                if result and len(result) > 1:
                    print(f"土地番号抽出成功: {result}")
                    return result
        print("土地番号抽出失敗")
        return None
    
    def _extract_land_address(self, text: str) -> Optional[str]:
        """土地住所を抽出（改善版）"""
        patterns = [
            # 標準的なパターン
            r'所在[：:]\s*([^\n\r]+)',
            r'住所[：:]\s*([^\n\r]+)',
            r'土地の所在[：:]\s*([^\n\r]+)',
            # スペース区切りパターン
            r'所在\s+([^\n\r]+)',
            r'住所\s+([^\n\r]+)',
            r'土地の所在\s+([^\n\r]+)',
            # 住所らしいパターン
            r'([東京都|大阪府|京都府|北海道|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|滋賀県|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県][^\n\r]{5,50})',
            # より広範囲の検索
            r'所在[：:]\s*([^、。\n\r]{5,100})',
            r'住所[：:]\s*([^、。\n\r]{5,100})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
            if match:
                result = match.group(1).strip()
                if result and len(result) > 5:
                    print(f"土地住所抽出成功: {result}")
                    return result
        print("土地住所抽出失敗")
        return None
    
    def _extract_land_area(self, text: str) -> Optional[float]:
        """土地面積を抽出（改善版）"""
        patterns = [
            # 標準的なパターン
            r'地積[：:]\s*([\d,\.]+)\s*㎡',
            r'土地面積[：:]\s*([\d,\.]+)\s*㎡',
            r'面積[：:]\s*([\d,\.]+)\s*㎡',
            # スペース区切りパターン
            r'地積\s+([\d,\.]+)\s*㎡',
            r'土地面積\s+([\d,\.]+)\s*㎡',
            r'面積\s+([\d,\.]+)\s*㎡',
            # 単位なしパターン
            r'地積[：:]\s*([\d,\.]+)',
            r'土地面積[：:]\s*([\d,\.]+)',
            r'面積[：:]\s*([\d,\.]+)',
            # より広範囲の検索
            r'地積[：:]\s*([\d,\.]{1,10})\s*㎡',
            r'土地面積[：:]\s*([\d,\.]{1,10})\s*㎡'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
            if match:
                area_str = match.group(1).replace(',', '')
                try:
                    result = float(area_str)
                    if 0 < result < 100000:  # 妥当な範囲を確認
                        print(f"土地面積抽出成功: {result}")
                        return result
                except ValueError:
                    continue
        print("土地面積抽出失敗")
        return None
    
    def _extract_land_use(self, text: str) -> Optional[str]:
        """土地用途を抽出（改善版）"""
        patterns = [
            # 標準的なパターン
            r'地目[：:]\s*([^\n\r]+)',
            r'用途[：:]\s*([^\n\r]+)',
            r'土地の用途[：:]\s*([^\n\r]+)',
            # スペース区切りパターン
            r'地目\s+([^\n\r]+)',
            r'用途\s+([^\n\r]+)',
            r'土地の用途\s+([^\n\r]+)',
            # 具体的な地目
            r'(宅地|田|畑|山林|原野|牧場|池沼|鉱泉地|温泉地|塩田|水道用地|用悪水路|ため池|堤|井溝|保安林|公衆用道路|公園|雑種地)',
            # より広範囲の検索
            r'地目[：:]\s*([^、。\n\r]{2,20})',
            r'用途[：:]\s*([^、。\n\r]{2,20})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
            if match:
                result = match.group(1).strip()
                if result and len(result) > 1:
                    print(f"土地用途抽出成功: {result}")
                    return result
        print("土地用途抽出失敗")
        return None
    
    def _extract_registry_date(self, text: str) -> Optional[str]:
        """登記年月日を抽出（改善版）"""
        patterns = [
            # 標準的なパターン
            r'登記年月日[：:]\s*([^\n\r]+)',
            r'登記日[：:]\s*([^\n\r]+)',
            r'年月日[：:]\s*([^\n\r]+)',
            # スペース区切りパターン
            r'登記年月日\s+([^\n\r]+)',
            r'登記日\s+([^\n\r]+)',
            r'年月日\s+([^\n\r]+)',
            # 日付パターン
            r'(\d{4}年\d{1,2}月\d{1,2}日)',
            r'(\d{4}/\d{1,2}/\d{1,2})',
            r'(\d{4}-\d{1,2}-\d{1,2})',
            # より広範囲の検索
            r'登記年月日[：:]\s*([^、。\n\r]{5,20})',
            r'登記日[：:]\s*([^、。\n\r]{5,20})',
            r'年月日[：:]\s*([^、。\n\r]{5,20})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
            if match:
                result = match.group(1).strip()
                if result and len(result) > 5:
                    print(f"登記年月日抽出成功: {result}")
                    return result
        print("登記年月日抽出失敗")
        return None
    
    def _extract_mortgage_info(self, text: str) -> Optional[str]:
        """抵当権情報を抽出（改善版）"""
        patterns = [
            # 標準的なパターン
            r'抵当権[：:]\s*([^\n\r]+)',
            r'担保[：:]\s*([^\n\r]+)',
            r'権利[：:]\s*([^\n\r]+)',
            # スペース区切りパターン
            r'抵当権\s+([^\n\r]+)',
            r'担保\s+([^\n\r]+)',
            r'権利\s+([^\n\r]+)',
            # 抵当権関連キーワード
            r'(抵当権設定|抵当権抹消|担保設定|担保抹消)',
            # より広範囲の検索
            r'抵当権[：:]\s*([^、。\n\r]{2,50})',
            r'担保[：:]\s*([^、。\n\r]{2,50})',
            r'権利[：:]\s*([^、。\n\r]{2,50})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
            if match:
                result = match.group(1).strip()
                if result and len(result) > 1:
                    print(f"抵当権情報抽出成功: {result}")
                    return result
        print("抵当権情報抽出失敗")
        return None 