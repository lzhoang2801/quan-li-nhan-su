@echo off
REM Build script for Windows (recommended: --onedir so data folder is shipped next to exe)
REM Usage: run from project root in an activated virtualenv

pip install --upgrade pyinstaller
pyinstaller --noconfirm --onedir --windowed --add-data "data;data" --name DeptMemberManager main.py

echo.
echo Build finished. Check the dist\DeptMemberManager\ directory for the executable and bundled files.

echo To create a single-file EXE (no persistence of data folder recommended), run:
REM pyinstaller --noconfirm --onefile --windowed --add-data "data;data" --name DeptMemberManager main.py
pause