#!/usr/bin/env python3
"""
賃貸管理システム v2.0 - 改良版起動ファイル
"""

import sys
import os

# パスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# メインウィンドウを起動
from main_window_improved import main

if __name__ == "__main__":
    main()