#!/bin/bash

# Clean previous build artifacts
echo "Cleaning previous build..."
rm -rf build/ dist/

# Build the binary using PyInstaller
echo "Building binary with PyInstaller..."
pyinstaller --clean --noconfirm hosts_updater.spec

# Check if build was successful
if [ -f "dist/hosts_updater" ]; then
    echo "Build successful! Binary created at: dist/hosts_updater"
else
    echo "Build failed!"
    exit 1
fi
