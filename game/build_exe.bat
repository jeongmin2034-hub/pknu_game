@echo off
cd /d "%~dp0"
echo [1/2] Installing pygame-ce and PyInstaller...
python -m pip install --upgrade pygame-ce pyinstaller
echo.
echo [2/2] Building PKNU_Survival.exe (takes 1-2 minutes)...
python -m PyInstaller --noconfirm --clean --onefile --windowed --name PKNU_Survival --add-data "assets;assets" main.py
echo.
if exist "dist\PKNU_Survival.exe" (
    echo Done! Run dist\PKNU_Survival.exe
    explorer dist
) else (
    echo Build failed. Check the messages above.
)
pause
