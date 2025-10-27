"""
ライセンス管理システム
賃貸管理システム v2.0
"""

import hashlib
import uuid
import os
from datetime import datetime, timedelta
from pathlib import Path


class LicenseManager:
    """ライセンスキーの生成・検証を管理するクラス"""

    def __init__(self):
        # ライセンスファイルもユーザーのドキュメントフォルダに保存
        self.data_dir = self._get_data_directory()
        self.license_file = str(self.data_dir / 'license.key')
        self.trial_file = str(self.data_dir / 'trial.dat')
        # 重要: 本番環境では必ず変更してください
        self.secret = "TintaiKanri2024SecretKey_ChangeThis!@#"
        self.trial_days = 30  # トライアル期間（30日間）

    def _get_data_directory(self):
        """アプリケーションのデータディレクトリを取得"""
        if os.name == 'nt':  # Windows
            documents = Path(os.path.expanduser("~")) / "Documents"
        else:  # Mac/Linux
            documents = Path(os.path.expanduser("~")) / "Documents"

        app_data_dir = documents / "賃貸管理システム"
        app_data_dir.mkdir(parents=True, exist_ok=True)
        return app_data_dir

    def generate_license_key(self, customer_name, customer_email, expiry_days=None):
        """
        ライセンスキーを生成

        Args:
            customer_name: 顧客名
            customer_email: 顧客メールアドレス
            expiry_days: 有効期限（日数）。Noneの場合は無期限

        Returns:
            dict: ライセンス情報
        """
        machine_id = self.get_machine_id()
        timestamp = datetime.now().strftime("%Y%m%d")

        # 有効期限設定
        if expiry_days:
            expiry_date = (datetime.now() + timedelta(days=expiry_days)).strftime("%Y%m%d")
        else:
            expiry_date = "99991231"  # 無期限（9999年12月31日）

        # ハッシュ生成（マシンIDベース）
        data = f"{customer_name}|{customer_email}|{machine_id}|{expiry_date}|{self.secret}"
        license_hash = hashlib.sha256(data.encode()).hexdigest()[:16].upper()

        # フォーマット: XXXX-XXXX-XXXX-XXXX
        key = f"{license_hash[0:4]}-{license_hash[4:8]}-{license_hash[8:12]}-{license_hash[12:16]}"

        return {
            'key': key,
            'customer_name': customer_name,
            'customer_email': customer_email,
            'expiry': expiry_date,
            'machine_id': machine_id,
            'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def get_machine_id(self):
        """
        PCの固有IDを取得

        Returns:
            str: マシン固有ID
        """
        return str(uuid.getnode())

    def verify_license(self):
        """
        保存されているライセンスキーを検証

        Returns:
            tuple: (bool: 有効かどうか, str: メッセージ, dict: ライセンス情報)
        """
        try:
            # license.keyファイルから情報読み込み
            if not os.path.exists(self.license_file):
                return False, "ライセンスファイルが見つかりません", None

            with open(self.license_file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines()]

                if len(lines) < 4:
                    return False, "ライセンスファイルが破損しています", None

                stored_key = lines[0]
                customer_name = lines[1]
                customer_email = lines[2]
                expiry_date = lines[3]

            # 有効期限確認
            if expiry_date != "99991231":
                try:
                    expiry = datetime.strptime(expiry_date, "%Y%m%d")
                    if datetime.now() > expiry:
                        return False, "ライセンスの有効期限が切れています", None
                except ValueError:
                    return False, "ライセンスファイルの日付形式が不正です", None

            # マシンID確認（キーを再生成して比較）
            current_machine_id = self.get_machine_id()
            expected_license = self.generate_license_key(customer_name, customer_email, None)

            # 無期限ライセンスの場合
            data = f"{customer_name}|{customer_email}|{current_machine_id}|{expiry_date}|{self.secret}"
            license_hash = hashlib.sha256(data.encode()).hexdigest()[:16].upper()
            expected_key = f"{license_hash[0:4]}-{license_hash[4:8]}-{license_hash[8:12]}-{license_hash[12:16]}"

            if stored_key != expected_key:
                return False, "このPCでは使用できないライセンスです", None

            license_info = {
                'customer_name': customer_name,
                'customer_email': customer_email,
                'expiry': expiry_date,
                'is_permanent': expiry_date == "99991231"
            }

            return True, f"{customer_name}様のライセンスが有効です", license_info

        except Exception as e:
            return False, f"ライセンス検証エラー: {str(e)}", None

    def save_license(self, license_info):
        """
        ライセンス情報をファイルに保存

        Args:
            license_info: ライセンス情報辞書
        """
        with open(self.license_file, 'w', encoding='utf-8') as f:
            f.write(f"{license_info['key']}\n")
            f.write(f"{license_info['customer_name']}\n")
            f.write(f"{license_info['customer_email']}\n")
            f.write(f"{license_info['expiry']}\n")
            f.write(f"{license_info['machine_id']}\n")

    def activate_license(self, license_key, customer_name, customer_email):
        """
        ライセンスキーをアクティベート

        Args:
            license_key: ライセンスキー
            customer_name: 顧客名
            customer_email: 顧客メールアドレス

        Returns:
            tuple: (bool: 成功したか, str: メッセージ)
        """
        try:
            # キーのフォーマット確認
            if not self._validate_key_format(license_key):
                return False, "ライセンスキーの形式が正しくありません"

            # 一時的にライセンス情報を保存
            temp_info = {
                'key': license_key,
                'customer_name': customer_name,
                'customer_email': customer_email,
                'expiry': '99991231',  # 仮の無期限
                'machine_id': self.get_machine_id()
            }

            self.save_license(temp_info)

            # 検証
            valid, message, info = self.verify_license()

            if not valid:
                # 検証失敗時はライセンスファイルを削除
                if os.path.exists(self.license_file):
                    os.remove(self.license_file)
                return False, message

            return True, "ライセンスの認証に成功しました"

        except Exception as e:
            return False, f"アクティベーションエラー: {str(e)}"

    def _validate_key_format(self, key):
        """
        ライセンスキーの形式を検証

        Args:
            key: ライセンスキー

        Returns:
            bool: 形式が正しいか
        """
        parts = key.split('-')
        if len(parts) != 4:
            return False

        for part in parts:
            if len(part) != 4 or not part.isalnum():
                return False

        return True

    # トライアル版機能

    def start_trial(self):
        """
        トライアルを開始

        Returns:
            tuple: (bool: 成功したか, str: メッセージ)
        """
        try:
            if os.path.exists(self.trial_file):
                return False, "トライアルは既に開始されています"

            start_date = datetime.now()
            end_date = start_date + timedelta(days=self.trial_days)

            with open(self.trial_file, 'w', encoding='utf-8') as f:
                f.write(start_date.strftime("%Y%m%d%H%M%S") + '\n')
                f.write(end_date.strftime("%Y%m%d%H%M%S") + '\n')
                f.write(self.get_machine_id() + '\n')

            return True, f"{self.trial_days}日間のトライアルを開始しました"

        except Exception as e:
            return False, f"トライアル開始エラー: {str(e)}"

    def check_trial(self):
        """
        トライアル期限をチェック

        Returns:
            tuple: (bool: 有効かどうか, str: メッセージ, int: 残り日数)
        """
        try:
            if not os.path.exists(self.trial_file):
                return False, "トライアルが開始されていません", 0

            with open(self.trial_file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines()]

                if len(lines) < 3:
                    return False, "トライアルファイルが破損しています", 0

                start_str = lines[0]
                end_str = lines[1]
                machine_id = lines[2]

            # マシンID確認
            if machine_id != self.get_machine_id():
                return False, "このPCではトライアルを使用できません", 0

            end_date = datetime.strptime(end_str, "%Y%m%d%H%M%S")
            remaining_time = end_date - datetime.now()
            remaining_days = remaining_time.days

            if remaining_days < 0:
                return False, "トライアル期間が終了しました", 0

            return True, f"トライアル残り {remaining_days} 日", remaining_days

        except Exception as e:
            return False, f"トライアルチェックエラー: {str(e)}", 0

    def is_licensed(self):
        """
        ライセンスまたはトライアルが有効かチェック

        Returns:
            tuple: (bool: 有効かどうか, str: メッセージ, str: タイプ（'license'/'trial'/None）)
        """
        # まずライセンスチェック
        valid, message, info = self.verify_license()
        if valid:
            return True, message, 'license'

        # トライアルチェック
        valid, message, days = self.check_trial()
        if valid:
            return True, message, 'trial'

        return False, "有効なライセンスまたはトライアルがありません", None


# テスト用コード
if __name__ == "__main__":
    manager = LicenseManager()

    # ライセンスキー生成のテスト
    print("=== ライセンスキー生成テスト ===")
    license_info = manager.generate_license_key(
        customer_name="株式会社テスト不動産",
        customer_email="test@example.com",
        expiry_days=None  # 無期限
    )

    print(f"ライセンスキー: {license_info['key']}")
    print(f"顧客名: {license_info['customer_name']}")
    print(f"メールアドレス: {license_info['customer_email']}")
    print(f"有効期限: {license_info['expiry']}")
    print(f"マシンID: {license_info['machine_id']}")
    print(f"生成日時: {license_info['generated_at']}")

    # ライセンス保存
    manager.save_license(license_info)
    print("\nライセンス情報を保存しました")

    # ライセンス検証
    print("\n=== ライセンス検証テスト ===")
    valid, message, info = manager.verify_license()
    print(f"検証結果: {message}")

    if valid and info:
        print(f"顧客名: {info['customer_name']}")
        print(f"無期限ライセンス: {info['is_permanent']}")
