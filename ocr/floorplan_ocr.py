#!/usr/bin/env python3
"""
募集図面OCR処理クラス
"""

import re
import os
from typing import Dict, Any, Optional, List
from gemini_ocr import GeminiOCR

class FloorplanOCR:
    """募集図面専用OCR処理クラス"""
    
    def __init__(self):
        try:
            self.ocr = GeminiOCR()
        except Exception as e:
            print(f"OCR初期化エラー: {e}")
            self.ocr = None
    
    def extract_room_info(self, image_path: str) -> List[Dict[str, Any]]:
        """募集図面から部屋情報を抽出"""
        try:
            if not self.ocr:
                return []
            
            # OCRでテキスト抽出
            ocr_text = self.ocr.extract_text_from_image(image_path)
            
            # 部屋情報を抽出
            rooms = []
            
            # 部屋番号パターン（101, 1F-1, 1階-1など）
            room_patterns = [
                r'(\d{3,4})',  # 101, 1001
                r'(\d+F-\d+)',  # 1F-1, 2F-2
                r'(\d+階-\d+)',  # 1階-1, 2階-2
                r'(\d+階\d+)',   # 1階1, 2階2
                r'(\d+-\d+)',    # 1-1, 2-2
            ]
            
            # 面積パターン
            area_patterns = [
                r'(\d+(?:\.\d+)?)\s*㎡',
                r'(\d+(?:\.\d+)?)\s*平米',
                r'(\d+(?:\.\d+)?)\s*平方メートル',
            ]
            
            # 賃料パターン
            rent_patterns = [
                r'(\d+(?:,\d+)*)\s*円',
                r'(\d+(?:,\d+)*)\s*万円',
                r'賃料[：:]\s*(\d+(?:,\d+)*)',
            ]
            
            # 管理費パターン
            management_fee_patterns = [
                r'管理費[：:]\s*(\d+(?:,\d+)*)',
                r'共益費[：:]\s*(\d+(?:,\d+)*)',
                r'(\d+(?:,\d+)*)\s*円\s*管理費',
            ]
            
            # 敷金・礼金パターン
            deposit_patterns = [
                r'敷金[：:]\s*(\d+(?:,\d+)*)',
                r'保証金[：:]\s*(\d+(?:,\d+)*)',
                r'礼金[：:]\s*(\d+(?:,\d+)*)',
            ]
            
            # テキストを行ごとに分割
            lines = ocr_text.split('\n')
            
            current_room = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 部屋番号を検出
                room_number = None
                for pattern in room_patterns:
                    match = re.search(pattern, line)
                    if match:
                        room_number = match.group(1)
                        break
                
                if room_number:
                    # 新しい部屋の開始
                    if current_room:
                        rooms.append(current_room)
                    
                    current_room = {
                        'room_number': room_number,
                        'area': None,
                        'rent': None,
                        'management_fee': None,
                        'deposit': None,
                        'key_money': None,
                        'floor': self._extract_floor_from_room_number(room_number),
                        'notes': ''
                    }
                
                if current_room:
                    # 面積を検出
                    if not current_room['area']:
                        for pattern in area_patterns:
                            match = re.search(pattern, line)
                            if match:
                                area_str = match.group(1).replace(',', '')
                                current_room['area'] = float(area_str)
                                break
                    
                    # 賃料を検出
                    if not current_room['rent']:
                        for pattern in rent_patterns:
                            match = re.search(pattern, line)
                            if match:
                                rent_str = match.group(1).replace(',', '')
                                if '万円' in line:
                                    current_room['rent'] = int(rent_str) * 10000
                                else:
                                    current_room['rent'] = int(rent_str)
                                break
                    
                    # 管理費を検出
                    if not current_room['management_fee']:
                        for pattern in management_fee_patterns:
                            match = re.search(pattern, line)
                            if match:
                                fee_str = match.group(1).replace(',', '')
                                current_room['management_fee'] = int(fee_str)
                                break
                    
                    # 敷金・礼金を検出
                    if '敷金' in line or '保証金' in line:
                        for pattern in deposit_patterns:
                            match = re.search(pattern, line)
                            if match:
                                deposit_str = match.group(1).replace(',', '')
                                current_room['deposit'] = int(deposit_str)
                                break
                    
                    if '礼金' in line:
                        for pattern in deposit_patterns:
                            match = re.search(pattern, line)
                            if match:
                                key_money_str = match.group(1).replace(',', '')
                                current_room['key_money'] = int(key_money_str)
                                break
            
            # 最後の部屋を追加
            if current_room:
                rooms.append(current_room)
            
            return rooms
            
        except Exception as e:
            print(f"募集図面OCR処理エラー: {e}")
            return []
    
    def _extract_floor_from_room_number(self, room_number: str) -> Optional[int]:
        """部屋番号から階数を抽出"""
        try:
            # 101 → 1階
            if len(room_number) >= 3 and room_number.isdigit():
                return int(room_number[0])
            
            # 1F-1 → 1階
            match = re.search(r'(\d+)F', room_number)
            if match:
                return int(match.group(1))
            
            # 1階-1 → 1階
            match = re.search(r'(\d+)階', room_number)
            if match:
                return int(match.group(1))
            
            # 1-1 → 1階
            match = re.search(r'^(\d+)-', room_number)
            if match:
                return int(match.group(1))
            
            return None
            
        except:
            return None 