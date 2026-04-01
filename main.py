#!/usr/bin/env python3
"""
Task Manager - Main entry point
A Kanban-style task management application with file-based storage.
"""
import sys
import os

# Ensure the tasks directory exists
os.makedirs("tasks", exist_ok=True)


def check_tkinter():
    """Check if tkinter is available"""
    try:
        import tkinter
        return True
    except ImportError:
        return False


def main():
    """Main entry point"""
    if not check_tkinter():
        print("Error: tkinter is not installed.")
        print("Please install tkinter for your Python version.")
        print("  macOS: brew install python-tk")
        print("  Ubuntu/Debian: sudo apt-get install python3-tk")
        print("  Fedora: sudo dnf install python3-tkinter")
        sys.exit(1)

    import tkinter as tk
    from app import TaskManagerApp

    root = tk.Tk()
    app = TaskManagerApp(root)
    app.run()


if __name__ == "__main__":
    main()