#!/usr/bin/env python3
"""
Import test script to verify all modules can be imported correctly
"""
import sys
import traceback

def test_imports():
    """Test all critical imports"""
    tests = []
    
    # Test PyQt6 imports
    try:
        from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
        from PyQt6.QtCore import Qt, pyqtSignal
        from PyQt6.QtGui import QColor, QFont
        tests.append(("PyQt6 basic imports", True, "OK"))
    except Exception as e:
        tests.append(("PyQt6 basic imports", False, str(e)))
    
    # Test models import
    try:
        from models import Property, Customer
        tests.append(("Models import", True, "OK"))
    except Exception as e:
        tests.append(("Models import", False, str(e)))
    
    # Test utils import
    try:
        from utils import MessageHelper, DateHelper
        tests.append(("Utils import", True, "OK"))
    except Exception as e:
        tests.append(("Utils import", False, str(e)))
    
    # Test ui_styles import
    try:
        from ui_styles import ModernStyles, ButtonHelper
        tests.append(("UI Styles import", True, "OK"))
    except Exception as e:
        tests.append(("UI Styles import", False, str(e)))
    
    # Test property_tab_basic import
    try:
        from property_tab_basic import PropertyTabBasic, PropertyEditDialog
        tests.append(("Property Tab import", True, "OK"))
    except Exception as e:
        tests.append(("Property Tab import", False, str(e)))
    
    # Test main_window import
    try:
        from main_window_minimal import MainWindowMinimal
        tests.append(("Main Window import", True, "OK"))
    except Exception as e:
        tests.append(("Main Window import", False, str(e)))
    
    # Print results
    print("=" * 60)
    print("Import Test Results")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed, message in tests:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:25} {status:10} {message}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("✅ All imports successful!")
        return True
    else:
        print("❌ Some imports failed. Check the error messages above.")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)