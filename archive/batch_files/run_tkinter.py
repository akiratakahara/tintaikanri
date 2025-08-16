#!/usr/bin/env python3
"""
賃貸管理システム v2.0 - Tkinter版起動ファイル
PyQt6の問題がある場合の代替版
"""

import sys
import os

# パスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Tkinterベースのメインウィンドウを起動
from main_window_tkinter import main

if __name__ == "__main__":
    main()