@echo off
echo Installing required packages for Rental Management System...

echo Creating virtual environment...
python -m venv .venv

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing PyQt6...
python -m pip install PyQt6==6.6.1

echo Installing other requirements...
python -m pip install SQLAlchemy==2.0.23
python -m pip install google-generativeai==0.3.2
python -m pip install Pillow>=10.2.0
python -m pip install python-dotenv==1.0.0
python -m pip install requests==2.31.0

echo Installation completed!
echo.
echo To run the application:
echo 1. Run: .venv\Scripts\activate.bat
echo 2. Run: python run_improved.py
pause