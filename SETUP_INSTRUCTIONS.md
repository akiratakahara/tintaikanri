# 賃貸管理システム v2.0 セットアップ手順

## 🚀 簡単セットアップ（Windows）

### 方法1: バッチファイルを使用（推奨）

1. **依存関係のインストール**
   ```
   install_requirements.bat
   ```
   
2. **アプリケーションの起動**
   ```
   run_improved.bat
   ```

### 方法2: 手動セットアップ

1. **仮想環境の作成**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

2. **依存関係のインストール**
   ```bash
   pip install PyQt6==6.6.1
   pip install python-dotenv==1.0.0
   ```

3. **アプリケーションの起動**
   ```bash
   python run_improved.py
   ```

## 🔧 トラブルシューティング

PyQt6 DLL エラーの場合：
1. Microsoft Visual C++ 再頒布可能パッケージをインストール
2. PyQt6を再インストール
3. システム再起動

---
**バージョン**: v2.0 Professional Edition