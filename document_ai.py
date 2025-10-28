"""
AI書類解析・テンプレート生成モジュール

過去の契約書や重説をAIで解析し、テンプレート化する機能を提供
ローカルOCR（Tesseract + pdfplumber）を使用
"""
import json
import os
import re
from typing import Dict, List, Tuple
from pathlib import Path


class DocumentAI:
    """書類をAIで解析してテンプレート化するクラス（ローカルOCR版）"""

    def __init__(self):
        """初期化"""
        # ContractOCRクラスを使用
        from contract_ocr import ContractOCR
        self.ocr = ContractOCR()

        print("DocumentAI初期化完了（ローカルOCR使用）")
        print(f"  pdfplumber: {'✓' if self.ocr.pdfplumber_available else '✗'}")
        print(f"  Tesseract OCR: {'✓' if self.ocr.tesseract_available else '✗'}")
        print(f"  pdf2image: {'✓' if self.ocr.pdf2image_available else '✗'}")

    def analyze_document_structure(self, file_path: str, document_type: str = "contract") -> Dict:
        """
        書類を解析して構造とテンプレート化を行う（ローカルOCR版）

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
            # OCRでテキスト抽出
            print(f"書類からテキストを抽出中: {file_path}")
            text = self.ocr.extract_text_from_pdf(file_path)

            if not text or not text.strip():
                return {"success": False, "error": "テキストの抽出に失敗しました"}

            print(f"抽出されたテキスト（先頭500文字）:\n{text[:500]}...")

            # テキストからテンプレートと変数を生成
            template_result = self._create_template_from_text(text, document_type)

            return {
                "success": True,
                "document_type": document_type,
                "title": template_result.get("title", ""),
                "template_text": template_result.get("template_text", text),
                "variables": template_result.get("variables", []),
                "sections": template_result.get("sections", []),
                "notes": "ローカルOCRで抽出されたテキストをテンプレート化しました"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"書類解析エラー: {str(e)}"
            }

    def _create_template_from_text(self, text: str, document_type: str) -> Dict:
        """
        抽出したテキストからテンプレートと変数を生成（正規表現ベース）

        Args:
            text: OCRで抽出されたテキスト
            document_type: 書類の種類

        Returns:
            テンプレート情報
        """
        # テキストを正規化
        normalized_text = re.sub(r'\s+', ' ', text)

        variables = []
        template_text = text

        # 契約書の場合の変数抽出パターン
        if document_type == "contract":
            title = "賃貸借契約書"

            # テナント名（借主）
            tenant_pattern = r'(賃借人|借主|乙)[：:\s]*([\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF\s]+?)(?=住所|電話|〒|$)'
            match = re.search(tenant_pattern, normalized_text)
            if match:
                tenant_name = match.group(2).strip()
                variables.append({
                    "name": "テナント名",
                    "placeholder": "{{テナント名}}",
                    "example_value": tenant_name,
                    "data_type": "text",
                    "description": "賃借人（借主）の氏名",
                    "source_fields": ["contract.contractor_name", "contract.tenant_name"]
                })
                template_text = template_text.replace(tenant_name, "{{テナント名}}")

            # オーナー名（貸主）
            owner_pattern = r'(賃貸人|貸主|甲)[：:\s]*([\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF\s]+?)(?=住所|電話|〒|$)'
            match = re.search(owner_pattern, normalized_text)
            if match:
                owner_name = match.group(2).strip()
                variables.append({
                    "name": "オーナー名",
                    "placeholder": "{{オーナー名}}",
                    "example_value": owner_name,
                    "data_type": "text",
                    "description": "賃貸人（貸主）の氏名",
                    "source_fields": ["property.owner_name"]
                })
                template_text = template_text.replace(owner_name, "{{オーナー名}}")

            # 賃料
            rent_pattern = r'賃料[はわ、，：:\s]*[月額は]*金?[¥￥]?\s*([\d,，]+)\s*円也?'
            match = re.search(rent_pattern, normalized_text)
            if match:
                rent_value = match.group(1)
                variables.append({
                    "name": "賃料",
                    "placeholder": "{{賃料}}",
                    "example_value": rent_value,
                    "data_type": "currency",
                    "description": "月額賃料",
                    "source_fields": ["contract.rent"]
                })
                template_text = template_text.replace(f"金{rent_value}円", "金{{賃料}}円")

            # 管理費
            maint_pattern = r'管理費[はわ、，：:\s]*[月額は]*金?[¥￥]?\s*([\d,，]+)\s*円也?'
            match = re.search(maint_pattern, normalized_text)
            if match:
                maint_value = match.group(1)
                variables.append({
                    "name": "管理費",
                    "placeholder": "{{管理費}}",
                    "example_value": maint_value,
                    "data_type": "currency",
                    "description": "月額管理費",
                    "source_fields": ["contract.maintenance_fee"]
                })
                template_text = template_text.replace(f"金{maint_value}円", "金{{管理費}}円")

            # 契約期間（開始日）
            start_pattern = r'(\d{4})[年/\-](\d{1,2})[月/\-](\d{1,2})日?[からより]'
            match = re.search(start_pattern, normalized_text)
            if match:
                start_date = f"{match.group(1)}年{match.group(2)}月{match.group(3)}日"
                variables.append({
                    "name": "契約開始日",
                    "placeholder": "{{契約開始日}}",
                    "example_value": start_date,
                    "data_type": "date",
                    "description": "契約開始日",
                    "source_fields": ["contract.start_date"]
                })
                template_text = template_text.replace(start_date, "{{契約開始日}}")

            # 契約期間（終了日）
            end_pattern = r'(\d{4})[年/\-](\d{1,2})[月/\-](\d{1,2})日?まで'
            match = re.search(end_pattern, normalized_text)
            if match:
                end_date = f"{match.group(1)}年{match.group(2)}月{match.group(3)}日"
                variables.append({
                    "name": "契約終了日",
                    "placeholder": "{{契約終了日}}",
                    "example_value": end_date,
                    "data_type": "date",
                    "description": "契約終了日",
                    "source_fields": ["contract.end_date"]
                })
                template_text = template_text.replace(end_date, "{{契約終了日}}")

        elif document_type == "explanation":
            title = "重要事項説明書"
            # 重説用の変数抽出ロジック（簡易版）
            # ここでは契約書と同様のパターンを使用
            variables.append({
                "name": "物件所在地",
                "placeholder": "{{物件所在地}}",
                "example_value": "",
                "data_type": "text",
                "description": "物件の所在地",
                "source_fields": ["property.address"]
            })

        elif document_type == "application":
            title = "入居申込書"
            # 申込書用の変数抽出ロジック（簡易版）
            variables.append({
                "name": "申込者氏名",
                "placeholder": "{{申込者氏名}}",
                "example_value": "",
                "data_type": "text",
                "description": "申込者の氏名",
                "source_fields": ["customer.name"]
            })
        else:
            title = "書類"

        # セクション分割（簡易版：改行で分割）
        sections = []
        paragraphs = text.split('\n\n')
        for i, para in enumerate(paragraphs[:5]):  # 最初の5段落のみ
            if para.strip():
                sections.append({
                    "section_name": f"第{i+1}条" if i < 10 else f"セクション{i+1}",
                    "content": para.strip()[:200]  # 最初の200文字
                })

        return {
            "title": title,
            "template_text": template_text,
            "variables": variables,
            "sections": sections
        }

    def extract_data_from_application(self, file_path: str) -> Dict:
        """
        申込書からデータを抽出（契約情報への自動入力用）ローカルOCR版

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
            # OCRでテキスト抽出
            print(f"申込書からテキストを抽出中: {file_path}")
            text = self.ocr.extract_text_from_pdf(file_path)

            if not text or not text.strip():
                return {"success": False, "error": "テキストの抽出に失敗しました"}

            # テキストを正規化
            normalized_text = re.sub(r'\s+', ' ', text)

            # 抽出データの初期化
            data = {
                "tenant_name": None,
                "tenant_phone": None,
                "tenant_email": None,
                "tenant_address": None,
                "tenant_birthdate": None,
                "company_name": None,
                "company_address": None,
                "company_phone": None,
                "annual_income": None,
                "desired_move_in_date": None,
                "desired_property": None,
                "desired_unit": None,
                "emergency_contact_name": None,
                "emergency_contact_relation": None,
                "emergency_contact_phone": None,
                "guarantor_name": None,
                "guarantor_address": None,
                "guarantor_phone": None,
                "application_date": None,
                "notes": None
            }

            # 申込者氏名
            name_pattern = r'(申込者|氏名|名前)[：:\s]*([\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF\s]+?)(?=住所|電話|生年月日|$)'
            match = re.search(name_pattern, normalized_text)
            if match:
                data["tenant_name"] = match.group(2).strip()

            # 電話番号
            phone_pattern = r'(電話|TEL|tel|携帯)[：:\s]*(\d{2,4}[-\s]?\d{2,4}[-\s]?\d{4})'
            match = re.search(phone_pattern, normalized_text)
            if match:
                data["tenant_phone"] = match.group(2).strip()

            # メールアドレス
            email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            match = re.search(email_pattern, normalized_text)
            if match:
                data["tenant_email"] = match.group(1).strip()

            # 希望物件名
            property_pattern = r'(希望物件|物件名)[：:\s]*([\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF0-9\s]+?)(?=部屋番号|号室|$)'
            match = re.search(property_pattern, normalized_text)
            if match:
                data["desired_property"] = match.group(2).strip()

            # 入居希望日
            date_pattern = r'(入居希望日|入居予定日)[：:\s]*(\d{4})[年/\-](\d{1,2})[月/\-](\d{1,2})日?'
            match = re.search(date_pattern, normalized_text)
            if match:
                data["desired_move_in_date"] = f"{match.group(2)}-{match.group(3).zfill(2)}-{match.group(4).zfill(2)}"

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
