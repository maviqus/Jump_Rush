@echo off
REM build_windows.bat — Tạo bản phân phối cho Windows bằng PyInstaller
REM Usage: run in Command Prompt with virtualenv activated

set APP_NAME=Jump Rush

REM On Windows use ; as separator for --add-data
pyinstaller --noconfirm --windowed --name "%APP_NAME%" --add-data "images;images" --add-data "music;music" main.py

echo Build finished. Kiểm tra thư mục dist\ để tìm "%APP_NAME%".
pause