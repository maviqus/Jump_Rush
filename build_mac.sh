#!/usr/bin/env bash
# build_mac.sh — Tạo bản phân phối cho macOS bằng PyInstaller
# Usage:
#   chmod +x build_mac.sh
#   ./build_mac.sh

set -euo pipefail

# Activate venv manually if you want
# source .venv/bin/activate

# Tên ứng dụng (không có phần mở rộng)
APP_NAME="Jump Rush"

# Tập hợp các tùy chọn chung
PYINSTALLER_OPTS=(--noconfirm --windowed --name "${APP_NAME}")

# Trên macOS và Linux, dùng dấu ':' trong --add-data
PYINSTALLER_OPTS+=(--add-data "images:images" --add-data "music:music")

# Nếu bạn muốn single-file (không khuyến nghị cho pygame), thêm --onefile
# PYINSTALLER_OPTS+=(--onefile)

# Chạy PyInstaller
pyinstaller "${PYINSTALLER_OPTS[@]}" main.py

echo "Build finished. Kiểm tra thư mục dist/ để tìm ${APP_NAME} (one-folder hoặc .app)."