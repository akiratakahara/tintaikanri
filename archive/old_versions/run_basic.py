#!/usr/bin/env python3
"""
賃貸管理システム v2.0 - 基本版起動ファイル（OCR機能なし）
"""

import sys
import os

# パスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 基本版メインウィンドウを起動
from main_window_basic import main

if __name__ == "__main__":
    main()