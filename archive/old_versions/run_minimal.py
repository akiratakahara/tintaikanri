#!/usr/bin/env python3
"""
賃貸管理システム v2.0 - 最小版起動ファイル
"""

import sys
import os

# パスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 最小版メインウィンドウを起動
from main_window_minimal import main

if __name__ == "__main__":
    main()