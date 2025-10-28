"""
AI書類解析・テンプレート生成モジュール

過去の契約書や重説をAIで解析し、テンプレート化する機能を提供
"""
import google.generativeai as genai
from PIL import Image
import json
import os
import fitz  # PyMuPDF
import io
from typing import Dict, List, Tuple
from config import GEMINI_API_KEY


class DocumentAI:
    """書類をAIで解析してテンプレート化するクラス"""

    def __init__(self):
        """初期化"""
        if not GEMINI_API_KEY:
            api_key = "AIzaSyCrpvxCC6mqPF9Il3qPwDp84hMJFT0XagU"
        else:
            api_key = GEMINI_API_KEY

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def pdf_to_images(self, pdf_path: str) -> List[Image.Image]:
        """PDFファイルを画像に変換"""
        try:
            pdf_document = fitz.open(pdf_path)
            images = []

            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                mat = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=mat)

                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                images.append(img)

            pdf_document.close()
            return images
        except Exception as e:
            print(f"PDF変換エラー: {e}")
            return []

    def analyze_document_structure(self, file_path: str, document_type: str = "contract") -> Dict:
        """
        書類を解析して構造とテンプレート化を行う

        Args:
            file_path: 書類ファイルのパス
            document_type: 書類の種類 ("contract": 契約書, "explanation": 重説, "application": 申込書)

        Returns:
            {
                "success": True/False,
                "document_type": 書類種別,
                "template_text": テンプレート化されたテキスト,
                "variables": [変数リスト],
                "sections": [セクション情報],
                "error": エラーメッセージ（失敗時）
            }
        """
        try:
            # ファイル拡張子を確認
            file_ext = os.path.splitext(file_path)[1].lower()

            if file_ext == '.pdf':
                images = self.pdf_to_images(file_path)
                if not images:
                    return {"success": False, "error": "PDFの変換に失敗しました"}
                image = images[0]  # 最初のページを解析
            else:
                image = Image.open(file_path)

            # 書類種別に応じたプロンプトを生成
            prompt = self._get_analysis_prompt(document_type)

            # Gemini APIで解析
            response = self.model.generate_content([prompt, image])
            result_text = response.text

            # JSON形式で返却されることを期待
            # Markdown のコードブロックを除去
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            result = json.loads(result_text)
            result["success"] = True
            return result

        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"JSON解析エラー: {str(e)}",
                "raw_response": result_text if 'result_text' in locals() else ""
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"書類解析エラー: {str(e)}"
            }

    def _get_analysis_prompt(self, document_type: str) -> str:
        """書類種別に応じた解析プロンプトを生成"""

        base_prompt = """
この画像は不動産賃貸の{doc_type_name}です。
以下のタスクを実行してください：

1. 書類全体のテキストを抽出
2. 変数となる部分（人名、日付、金額、物件名など）を識別
3. テンプレート化（変数部分を{{変数名}}形式に置き換え）

以下のJSON形式で返してください：

{{
    "document_type": "{doc_type}",
    "title": "書類のタイトル",
    "template_text": "テンプレート化されたテキスト全体（変数は{{変数名}}形式）",
    "variables": [
        {{
            "name": "変数名（日本語）",
            "placeholder": "{{変数名}}",
            "example_value": "元の文書から抽出した値",
            "data_type": "text/number/date/currency",
            "description": "この変数の説明",
            "source_fields": ["contract.tenant_name", "contract.rent"] // システムのどのフィールドから取得できるか
        }}
    ],
    "sections": [
        {{
            "section_name": "セクション名",
            "content": "セクションの内容（テンプレート化済み）"
        }}
    ],
    "notes": "解析時の注意事項や特記事項"
}}

【重要な変数の例】
"""

        if document_type == "contract":
            doc_type_name = "賃貸借契約書"
            variables_example = """
- テナント名（借主名）
- 貸主名（オーナー名）
- 物件名・住所
- 部屋番号
- 賃料
- 管理費・共益費
- 敷金
- 礼金
- 契約開始日
- 契約終了日
- 契約期間
- 更新料
- 保証会社名
- 特約事項
- 契約日
- 仲介業者名
"""
        elif document_type == "explanation":
            doc_type_name = "重要事項説明書"
            variables_example = """
- 借主名
- 貸主名
- 物件所在地
- 建物名称
- 部屋番号
- 専有面積
- 建物構造
- 築年月
- 賃料
- 管理費
- 敷金
- 礼金
- 契約期間
- 更新条件
- 用途地域
- 設備内容
- 禁止事項
- 解約条件
- 説明者名
- 宅建士番号
- 説明日
"""
        elif document_type == "application":
            doc_type_name = "入居申込書"
            variables_example = """
- 申込者氏名
- 生年月日
- 現住所
- 電話番号
- メールアドレス
- 勤務先名
- 勤務先住所
- 勤務先電話番号
- 年収
- 入居予定日
- 希望物件名
- 希望部屋番号
- 緊急連絡先氏名
- 緊急連絡先続柄
- 緊急連絡先電話番号
- 保証人氏名
- 保証人住所
- 保証人電話番号
- 申込日
"""
        else:
            doc_type_name = "書類"
            variables_example = "- 一般的な変数項目"

        return base_prompt.format(
            doc_type_name=doc_type_name,
            doc_type=document_type
        ) + variables_example

    def extract_data_from_application(self, file_path: str) -> Dict:
        """
        申込書からデータを抽出（契約情報への自動入力用）

        Returns:
            {
                "success": True/False,
                "data": {
                    "tenant_name": "テナント名",
                    "tenant_phone": "電話番号",
                    "tenant_email": "メールアドレス",
                    "rent": 100000,
                    "move_in_date": "2025-01-01",
                    ...
                },
                "error": エラーメッセージ
            }
        """
        try:
            file_ext = os.path.splitext(file_path)[1].lower()

            if file_ext == '.pdf':
                images = self.pdf_to_images(file_path)
                if not images:
                    return {"success": False, "error": "PDFの変換に失敗しました"}
                image = images[0]
            else:
                image = Image.open(file_path)

            prompt = """
この画像は入居申込書です。
以下の情報を抽出して、JSON形式で返してください：

{
    "tenant_name": "申込者氏名",
    "tenant_phone": "電話番号",
    "tenant_email": "メールアドレス",
    "tenant_address": "現住所",
    "tenant_birthdate": "生年月日 (YYYY-MM-DD形式)",
    "company_name": "勤務先名",
    "company_address": "勤務先住所",
    "company_phone": "勤務先電話番号",
    "annual_income": "年収（数値のみ）",
    "desired_move_in_date": "入居希望日 (YYYY-MM-DD形式)",
    "desired_property": "希望物件名",
    "desired_unit": "希望部屋番号",
    "emergency_contact_name": "緊急連絡先氏名",
    "emergency_contact_relation": "緊急連絡先続柄",
    "emergency_contact_phone": "緊急連絡先電話番号",
    "guarantor_name": "保証人氏名",
    "guarantor_address": "保証人住所",
    "guarantor_phone": "保証人電話番号",
    "application_date": "申込日 (YYYY-MM-DD形式)",
    "notes": "その他特記事項"
}

情報が見つからない場合は null を設定してください。
"""

            response = self.model.generate_content([prompt, image])
            result_text = response.text

            # Markdown のコードブロックを除去
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            data = json.loads(result_text)

            return {
                "success": True,
                "data": data
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"申込書データ抽出エラー: {str(e)}"
            }

    def fill_template(self, template_text: str, data: Dict) -> str:
        """
        テンプレートにデータを埋め込む

        Args:
            template_text: テンプレート文字列（{{変数名}}を含む）
            data: 埋め込むデータの辞書

        Returns:
            データが埋め込まれたテキスト
        """
        result = template_text

        for key, value in data.items():
            placeholder = "{{" + key + "}}"
            if placeholder in result and value is not None:
                result = result.replace(placeholder, str(value))

        return result

    def generate_document_from_contract(self, template: Dict, contract_data: Dict) -> str:
        """
        契約データからテンプレートを使って書類を生成

        Args:
            template: analyze_document_structureで取得したテンプレート
            contract_data: 契約データベースから取得した契約情報

        Returns:
            生成された書類テキスト
        """
        template_text = template.get("template_text", "")
        variables = template.get("variables", [])

        # 変数とcontract_dataのマッピングを作成
        data_mapping = {}

        for var in variables:
            var_name = var.get("placeholder", "").replace("{{", "").replace("}}", "")
            source_fields = var.get("source_fields", [])

            # source_fieldsから値を取得
            for field in source_fields:
                if "." in field:
                    # "contract.tenant_name" のような形式
                    parts = field.split(".")
                    if parts[0] == "contract" and parts[1] in contract_data:
                        data_mapping[var_name] = contract_data[parts[1]]
                        break
                elif field in contract_data:
                    data_mapping[var_name] = contract_data[field]
                    break

        # テンプレートにデータを埋め込み
        return self.fill_template(template_text, data_mapping)


class DocumentTemplate:
    """書類テンプレートを管理するクラス"""

    def __init__(self, db_path: str = None):
        """初期化"""
        if db_path is None:
            from models import get_data_directory
            data_dir = get_data_directory()
            self.templates_dir = data_dir / "document_templates"
            self.templates_dir.mkdir(exist_ok=True)
        else:
            self.templates_dir = db_path

    def save_template(self, template_name: str, template_data: Dict) -> bool:
        """テンプレートを保存"""
        try:
            file_path = self.templates_dir / f"{template_name}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"テンプレート保存エラー: {e}")
            return False

    def load_template(self, template_name: str) -> Dict:
        """テンプレートを読み込み"""
        try:
            file_path = self.templates_dir / f"{template_name}.json"
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"テンプレート読み込みエラー: {e}")
            return {}

    def list_templates(self) -> List[str]:
        """保存されているテンプレート一覧を取得"""
        try:
            templates = []
            for file in self.templates_dir.glob("*.json"):
                templates.append(file.stem)
            return templates
        except Exception as e:
            print(f"テンプレート一覧取得エラー: {e}")
            return []

    def delete_template(self, template_name: str) -> bool:
        """テンプレートを削除"""
        try:
            file_path = self.templates_dir / f"{template_name}.json"
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"テンプレート削除エラー: {e}")
            return False
