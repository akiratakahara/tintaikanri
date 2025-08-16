#!/usr/bin/env python3
"""
賃貸顧客管理システム エントリーポイント
"""

import sys
import os

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main_window import main

if __name__ == "__main__":
    main() 