#!/bin/bash
# BarberShop Manager - DMG Build Automation Script for macOS
# This script packages the Python backend and then builds the Electron app.

# Exit on error
set -e

echo "Starting macOS Build Process..."

# 1. Ensure dist_python directory exists
if [ ! -d "dist_python" ]; then
    echo "Creating dist_python directory..."
    mkdir -p dist_python
fi

# Clean previous backend build output to avoid PyInstaller prompt
if [ -d "dist_python/barbershop_backend.app" ]; then
    echo "Removing previous dist_python/barbershop_backend.app..."
    rm -rf dist_python/barbershop_backend.app
fi

# 2. Package Python Backend
echo ""
echo "[1/2] Packaging Python Backend (Flask)..."
echo "Installing dependencies..."
pip3 install pyinstaller flask gunicorn

echo "Running PyInstaller..."
# Mac uses ":" as separator for --add-data
# Syntax: "source:destination"
python3 -m PyInstaller --onefile --noconsole --noconfirm \
    --name barbershop_backend \
    --add-data "templates:templates" \
    --add-data "static:static" \
    --add-data "AlShahidLogo.jpeg:." \
    --distpath dist_python \
    --clean \
    app.py

if [ $? -ne 0 ]; then
    echo ""
    echo "[!] PyInstaller failed. Aborting."
    exit 1
fi

# 3. Build Electron App
echo ""
echo "[2/2] Building Electron DMG..."
echo "Installing Node dependencies..."
npm install

echo "Running electron-builder..."
# This will use the "mac" configuration in package.json to create a DMG
npm run dist

if [ $? -ne 0 ]; then
    echo ""
    echo "[!] Electron build failed."
    exit 1
fi

echo ""
echo "[SUCCESS] DMG creation complete! Check the 'dist' folder for the .dmg file."
echo "The Python backend is bundled inside the app for macOS."
