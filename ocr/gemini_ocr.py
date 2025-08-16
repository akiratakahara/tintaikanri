import google.generativeai as genai
from PIL import Image
import base64
import io
import requests
import json
import fitz  # PyMuPDF
import os
from config import GEMINI_API_KEY

class GeminiOCR:
    """Gemini Vision APIを使用したOCRクラス"""
    
    def __init__(self):
        """初期化"""
        if not GEMINI_API_KEY:
            # デフォルトのAPIキーを使用
            api_key = "AIzaSyCrpvxCC6mqPF9Il3qPwDp84hMJFT0XagU"
        else:
            api_key = GEMINI_API_KEY
        
        # Google Generative AIライブラリを使用
        genai.configure(api_key=api_key)
        # 最新のモデル名に変更
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 直接API呼び出し用の設定
        self.api_key = api_key
        # 最新のエンドポイントに変更
        self.endpoint = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"
    
    def pdf_to_images(self, pdf_path):
        """PDFファイルを画像に変換"""
        try:
            # PDFファイルを開く
            pdf_document = fitz.open(pdf_path)
            images = []
            
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                # ページを画像に変換（解像度を上げる）
                mat = fitz.Matrix(2.0, 2.0)  # 2倍の解像度
                pix = page.get_pixmap(matrix=mat)
                
                # PIL Imageに変換
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                images.append(img)
            
            pdf_document.close()
            return images
            
        except Exception as e:
            print(f"PDF変換エラー: {e}")
            return []
    
    def image_to_base64(self, image):
        """画像をbase64エンコード"""
        if isinstance(image, str):
            # ファイルパスの場合
            with open(image, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        else:
            # PIL Imageの場合
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def send_to_gemini_vision(self, base64_image, prompt):
        """Gemini Vision APIに直接リクエストを送信"""
        headers = {"Content-Type": "application/json"}
        parts = [{"inline_data": {"mime_type": "image/png", "data": base64_image}}]
        parts.insert(0, {"text": prompt})
        
        data = {"contents": [{"parts": parts}]}
        response = requests.post(
            f"{self.endpoint}?key={self.api_key}", 
            headers=headers, 
            json=data
        )
        return response.json()
    
    def extract_text_from_image(self, image_path):
        """画像からテキストを抽出"""
        try:
            # ファイル拡張子を確認
            file_ext = os.path.splitext(image_path)[1].lower()
            
            if file_ext == '.pdf':
                # PDFファイルの場合、画像に変換
                images = self.pdf_to_images(image_path)
                if not images:
                    return "PDFファイルの変換に失敗しました。"
                
                # 最初のページのみ処理（複数ページの場合は後で拡張）
                image = images[0]
            else:
                # 画像ファイルの場合
                image = Image.open(image_path)
            
            # 画像をbase64エンコード
            base64_image = self.image_to_base64(image)
            
            # Gemini Vision APIに送信するプロンプト
            prompt = """
            この画像は登記簿謄本です。画像内のすべてのテキストを正確に抽出してください。
            
            特に以下の項目に注目して抽出してください：
            
            1. 所有者・権利者情報
            2. 所在・住所情報
            3. 建物構造・階数
            4. 面積情報（床面積、地積など）
            5. 建築年月・竣工年月
            6. 登記年月日
            7. 抵当権・担保情報
            8. 土地番号・地番
            9. 地目・用途
            
            抽出したテキストをそのまま返してください。JSON形式ではなく、プレーンテキストで返してください。
            """
            
            # 直接API呼び出し
            response = self.send_to_gemini_vision(base64_image, prompt)
            
            if 'candidates' in response and len(response['candidates']) > 0:
                result = response['candidates'][0]['content']['parts'][0]['text']
                print(f"Gemini API応答: {result}")
                return result
            else:
                print(f"Gemini API応答エラー: {response}")
                return "OCR処理で結果を取得できませんでした。"
            
        except Exception as e:
            print(f"OCR処理エラー: {e}")
            return f"OCR処理中にエラーが発生しました: {str(e)}"
    
    def extract_checklist_items(self, image_path):
        """画像からチェックリスト項目を抽出"""
        try:
            # ファイル拡張子を確認
            file_ext = os.path.splitext(image_path)[1].lower()
            
            if file_ext == '.pdf':
                # PDFファイルの場合、画像に変換
                images = self.pdf_to_images(image_path)
                if not images:
                    return "PDFファイルの変換に失敗しました。"
                image = images[0]
            else:
                # 画像ファイルの場合
                image = Image.open(image_path)
            
            # 画像をbase64エンコード
            base64_image = self.image_to_base64(image)
            
            prompt = """
            この画像は賃貸契約の重要事項説明書またはチェックリストです。
            以下の項目が記載されているかチェックし、見つかった項目をリストアップしてください：
            
            必須項目：
            - 入居者本人確認書類
            - 収入証明書類
            - 連帯保証人情報
            - 緊急連絡先
            - 入居審査書
            - 重要事項説明書
            - 賃貸借契約書
            - 入居申込書
            - 管理規約
            - 火災保険加入証明
            
            オプション項目：
            - ペット飼育許可書
            - 車両登録証
            - その他特記事項
            
            見つかった項目を以下の形式で返してください：
            {
                "required_items": ["項目1", "項目2", ...],
                "optional_items": ["項目1", "項目2", ...],
                "missing_required": ["不足している必須項目1", "不足している必須項目2", ...]
            }
            """
            
            # 直接API呼び出し
            response = self.send_to_gemini_vision(base64_image, prompt)
            
            if 'candidates' in response and len(response['candidates']) > 0:
                return response['candidates'][0]['content']['parts'][0]['text']
            else:
                return "チェックリスト処理で結果を取得できませんでした。"
            
        except Exception as e:
            return f"チェックリスト抽出中にエラーが発生しました: {str(e)}"
    
    def extract_text_from_image_legacy(self, image_path):
        """従来のGoogle Generative AIライブラリを使用した方法（バックアップ）"""
        try:
            # 画像を読み込み
            image = Image.open(image_path)
            
            # Gemini Vision APIに送信するプロンプト
            prompt = """
            この画像は賃貸契約書類です。以下の項目を抽出してください：
            
            1. 顧客名（入居者名）
            2. 物件名・住所
            3. 賃料
            4. 敷金
            5. 礼金
            6. 管理費
            7. 契約日
            8. 入居開始日
            9. 契約期間
            10. その他の重要な契約条件
            
            抽出した情報を以下のJSON形式で返してください：
            {
                "customer_name": "顧客名",
                "property_name": "物件名",
                "property_address": "物件住所",
                "rent": "賃料",
                "deposit": "敷金",
                "key_money": "礼金",
                "management_fee": "管理費",
                "contract_date": "契約日",
                "start_date": "入居開始日",
                "contract_period": "契約期間",
                "other_conditions": "その他の条件"
            }
            
            情報が見つからない場合は空文字列を設定してください。
            """
            
            # Gemini Vision APIで画像解析
            response = self.model.generate_content([prompt, image])
            
            return response.text
            
        except Exception as e:
            return f"OCR処理中にエラーが発生しました: {str(e)}" 