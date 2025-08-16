# フォルダ構成

## メインファイル
- `main.py` - メインアプリケーションエントリポイント
- `modern_main_window.py` - モダンなメインウィンドウ（統合UI）
- `modern_ui_system.py` - モダンUIシステム・コンポーネント
- `models.py` - データベースモデル定義
- `config.py` - アプリケーション設定
- `utils.py` - 共通ユーティリティ関数
- `commission_manager.py` - 仲介手数料管理
- `contract_procedure_log.py` - 契約手続きログ
- `requirements.txt` - 必要なPythonパッケージ一覧
- `tintai_management.db` - SQLiteデータベース

## tabs/ - 各機能タブモジュール
- `calendar_tab.py` - カレンダー機能
- `checklist_tab.py` - チェックリスト機能
- `communication_tab.py` - コミュニケーション機能
- `communication_tab_basic.py` - 基本コミュニケーション機能
- `consistency_check_tab.py` - 整合性チェック機能
- `contract_tab.py` - 基本契約管理機能
- `contract_tab_improved.py` - 改良版契約管理機能
- `customer_tab.py` - 顧客管理機能
- `dashboard_tab.py` - ダッシュボード機能
- `document_tab.py` - ドキュメント管理機能
- `property_tab.py` - 基本物件管理機能
- `property_management_complete.py` - **🔥 統合物件管理システム（完全版・プロ仕様）**
- `task_tab.py` - 基本タスク管理機能
- `task_tab_basic.py` - 基本タスク管理機能
- `unit_tab.py` - 部屋管理機能
- `modern_calendar_tab.py` - モダンカレンダー機能

## ocr/ - OCR関連モジュール
- `floorplan_ocr.py` - 間取り図OCR
- `gemini_ocr.py` - Gemini OCR
- `registry_ocr.py` - 登記簿OCR

## ui/ - UI関連モジュール
- `ui_helpers.py` - UIヘルパー関数
- `ui_styles.py` - UIスタイル定義

## contract_documents/ - 契約書保存フォルダ
- 各契約の電子ファイルを保存

## archive/ - アーカイブ済みファイル
### archive/test_files/ - テストファイル
### archive/old_versions/ - 旧バージョンファイル
### archive/batch_files/ - バッチファイル
### archive/debug_files/ - デバッグファイル

## その他
- `start_app.bat` - アプリケーション起動用バッチファイル
- `venv/` - Python仮想環境