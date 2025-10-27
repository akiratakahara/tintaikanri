#!/usr/bin/env python3
"""
賃貸管理システム v2.0 - Modern Edition ✅
メインエントリーポイント
"""

import sys
import os
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ModernMainWindowを直接import
from modern_main_window import ModernMainWindow
from models import create_tables
from license_manager import LicenseManager
from license_dialog import LicenseDialog

def check_license():
    """ライセンスまたはトライアルをチェック"""
    manager = LicenseManager()

    # ライセンスまたはトライアルが有効かチェック
    valid, message, license_type = manager.is_licensed()

    if valid:
        if license_type == 'trial':
            # トライアル版の場合、残り日数を表示
            _, _, remaining_days = manager.check_trial()
            QMessageBox.information(
                None,
                "トライアル版",
                f"{message}\n\n製品版ライセンスのご購入をご検討ください。"
            )
        return True

    # 有効なライセンスもトライアルもない場合
    # トライアルが開始されていない場合は自動開始
    if not os.path.exists(manager.trial_file):
        success, msg = manager.start_trial()
        if success:
            QMessageBox.information(
                None,
                "トライアル開始",
                f"30日間の無料トライアルを開始しました。\n\n"
                f"トライアル期間終了後は、ライセンスキーの購入が必要です。\n\n"
                f"購入URL: https://s-k-dangi.com"
            )
            return True
        else:
            QMessageBox.critical(
                None,
                "エラー",
                f"トライアル開始に失敗しました: {msg}"
            )
            return False

    # トライアル期限切れの場合
    QMessageBox.critical(
        None,
        "トライアル期間終了",
        "30日間の無料トライアル期間が終了しました。\n\n"
        "引き続きご利用いただくには、ライセンスキーの購入が必要です。\n\n"
        "購入URL: https://s-k-dangi.com\n\n"
        "購入後、「ライセンス登録」からライセンスキーを入力してください。"
    )

    # ライセンス登録ダイアログを表示
    dialog = LicenseDialog()
    result = dialog.exec() == QDialog.DialogCode.Accepted

    if not result:
        # ライセンス登録をキャンセルした場合は終了
        QMessageBox.warning(
            None,
            "アプリケーション終了",
            "ライセンス認証がキャンセルされました。\n\nアプリケーションを終了します。"
        )
        return False

    return result

def main():
    """メイン関数"""
    # Windows文字化け対策
    if os.name == 'nt':
        try:
            os.system('chcp 65001 >nul 2>&1')
            import codecs
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'ignore')
        except:
            pass

    app = QApplication(sys.argv)

    # ライセンスチェック
    if not check_license():
        print("ライセンス認証がキャンセルされました")
        sys.exit(0)
    
    # 高DPI対応（PyQt6では自動的に有効）
    try:
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    except AttributeError:
        pass  # PyQt6では不要
    
    try:
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        pass  # PyQt6では不要
    
    # フォント設定
    if os.name == 'nt':
        font = QFont("Yu Gothic UI", 9)
        if not font.exactMatch():
            font = QFont("Segoe UI", 9)
        app.setFont(font)
    
    try:
        print("========================================")
        print("🏢 賃貸管理システム v2.0 - Modern Edition ✅")
        print("========================================")
        print("✨ モダンUIで全面刷新しました")
        print("🚀 起動中...")
        print()
        
        # データベース初期化
        create_tables()
        
        window = ModernMainWindow()
        window.show()
        
        print("[SUCCESS] アプリケーションが正常に起動しました")
        print("💡 左のサイドバーからページを切り替えてください")
        
        sys.exit(app.exec())
        
    except Exception as e:
        error_msg = f"アプリケーション起動エラー: {e}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        
        try:
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Icon.Critical)
            error_dialog.setWindowTitle("起動エラー")
            error_dialog.setText("アプリケーションの起動に失敗しました")
            error_dialog.setDetailedText(str(e))
            error_dialog.exec()
        except:
            pass
        
        input("エラーが発生しました。Enterキーで終了...")

if __name__ == "__main__":
    main()