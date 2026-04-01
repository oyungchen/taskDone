# Task Manager

A desktop task management application with a Kanban-style board interface.

## Features

- **Kanban Board**: Three columns (Pending, Processing, Done) for task organization
- **Drag & Drop**: Move tasks between columns by clicking to change status
- **Date Filtering**: View tasks by date range (defaults to current week)
- **Priority Levels**: High (red), Medium (orange), Low (green) with color coding
- **Persistent Storage**: Tasks saved locally in JSON files

## Screenshots

*To be added*

## Installation

### Requirements
- Python 3.x with tkinter support

### Quick Start

```bash
# Clone or download the repository
git clone <repository-url>
cd task-manager

# Run the application
python main.py

# Or use the launcher script (macOS/Linux)
./run.sh
```

### Installing tkinter

**macOS:**
```bash
brew install python-tk
```

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-tk
```

**Fedora:**
```bash
sudo dnf install python3-tkinter
```

## Usage

1. **Adding Tasks**: Click the "+ New Task" button or use File → New Task (Ctrl+N)
2. **Moving Tasks**: Click on a task to open details, then use the "Move to..." buttons
3. **Editing/Deleting**: Open task details to delete a task
4. **Date Navigation**: Use the date controls to view tasks from different weeks

## File Structure

```
task-manager/
├── main.py          # Application entry point
├── app.py           # Main application window
├── gui.py           # GUI components (Kanban columns, cards)
├── models.py        # Data models (Task, enums)
├── storage.py       # File-based storage
├── tasks/           # Task data directory
│   ├── pending.json
│   ├── processing.json
│   └── done.json
└── run.sh           # Launcher script
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.