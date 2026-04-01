#!/bin/bash
# Task Manager Launcher Script

cd "$(dirname "$0")"

# Check Python availability
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "Error: Python is not installed or not in PATH"
    exit 1
fi

# Check tkinter
if ! $PYTHON -c "import tkinter" 2>/dev/null; then
    echo "Error: tkinter is not installed."
    echo ""
    echo "Please install tkinter:"
    echo "  macOS:   brew install python-tk"
    echo "  Ubuntu:  sudo apt-get install python3-tk"
    echo "  Fedora:  sudo dnf install python3-tkinter"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo "Starting Task Manager..."
$PYTHON main.py

# Keep terminal open on error
if [ $? -ne 0 ]; then
    echo ""
    echo "Task Manager exited with an error."
    read -p "Press Enter to close..."
fi