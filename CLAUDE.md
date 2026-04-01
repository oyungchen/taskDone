# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Task Management Tool** - a desktop GUI application with a Kanban-style board for managing tasks across three states: Pending, Processing, and Done.

## Architecture

### File Structure
- `main.py` - Application entry point
- `app.py` - Main application window and logic (`TaskManagerApp` class)
- `gui.py` - GUI components (`KanbanColumn`, `TaskCard`)
- `models.py` - Data models (`Task` dataclass, enums for status/priority)
- `storage.py` - File-based persistence (`TaskStorage` class)

### Data Storage
Tasks are stored in JSON format in the `tasks/` directory:
- `tasks/pending.json` - Pending tasks
- `tasks/processing.json` - In-progress tasks
- `tasks/done.json` - Completed tasks

Each task has: name, created_at, started_at, completed_at, priority (high/medium/low), status, color

### Key Features
- Kanban board with drag-drop support between columns
- Date range filtering (default: current week ±3 days)
- Task priorities with color coding (High=red, Medium=orange, Low=green)
- Task detail view with timestamps

## Running the Application

```bash
# Run directly
python main.py

# Or use the launcher script
./run.sh
```

## Requirements

- Python 3.x with tkinter support
- No external packages required (uses only standard library)

Installing tkinter:
- macOS: `brew install python-tk`
- Ubuntu/Debian: `sudo apt-get install python3-tk`
- Fedora: `sudo dnf install python3-tkinter`