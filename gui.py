"""
GUI module for the task management system using tkinter.
Provides a Kanban-style board with three columns: pending, processing, done.
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
from typing import Optional, Callable
from models import Task, TaskStatus, Priority, PRIORITY_COLORS, STATUS_COLORS
from storage import TaskStorage


class TaskCard(tk.Frame):
    """Individual task card widget for Kanban board"""

    def __init__(self, parent, task: Task, on_click: Optional[Callable] = None,
                 on_drag_start: Optional[Callable] = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.task = task
        self.on_click = on_click
        self.on_drag_start = on_drag_start

        # Card styling
        self.configure(
            bg=task.color or "#ffffff",
            highlightbackground="#cccccc",
            highlightthickness=1,
            relief="raised",
            bd=2
        )

        # Bind events
        self.bind("<Button-1>", self._on_click)
        self.bind("<B1-Motion>", self._on_drag)

        # Task name
        name_label = tk.Label(
            self,
            text=task.name,
            font=("Arial", 10, "bold"),
            bg=task.color or "#ffffff",
            wraplength=180,
            justify="left"
        )
        name_label.pack(anchor="w", padx=5, pady=(5, 0))
        name_label.bind("<Button-1>", self._on_click)

        # Created time
        created_text = f"Created: {self._format_time(task.created_at)}"
        created_label = tk.Label(
            self,
            text=created_text,
            font=("Arial", 8),
            bg=task.color or "#ffffff",
            fg="#666666"
        )
        created_label.pack(anchor="w", padx=5, pady=(2, 5))
        created_label.bind("<Button-1>", self._on_click)

    def _format_time(self, time_str: Optional[str]) -> str:
        """Format ISO time string for display"""
        if not time_str:
            return "N/A"
        try:
            dt = datetime.fromisoformat(time_str)
            return dt.strftime("%m-%d %H:%M")
        except:
            return time_str[:16] if len(time_str) > 16 else time_str

    def _on_click(self, event):
        """Handle click event"""
        if self.on_click:
            self.on_click(self.task)

    def _on_drag(self, event):
        """Handle drag start"""
        if self.on_drag_start:
            self.on_drag_start(self.task, event)


class KanbanColumn(tk.Frame):
    """Kanban column widget for a specific status"""

    def __init__(self, parent, title: str, status: TaskStatus,
                 bg_color: str = "#f0f0f0", **kwargs):
        super().__init__(parent, **kwargs)
        self.status = status
        self.tasks = []

        # Column styling
        self.configure(bg=bg_color, relief="sunken", bd=2)

        # Header
        header_frame = tk.Frame(self, bg=bg_color)
        header_frame.pack(fill="x", padx=5, pady=5)

        title_label = tk.Label(
            header_frame,
            text=title,
            font=("Arial", 14, "bold"),
            bg=bg_color
        )
        title_label.pack(side="left")

        self.count_label = tk.Label(
            header_frame,
            text="(0)",
            font=("Arial", 12),
            bg=bg_color,
            fg="#666666"
        )
        self.count_label.pack(side="left", padx=(5, 0))

        # Task container with scrollbar
        container = tk.Frame(self, bg=bg_color)
        container.pack(fill="both", expand=True, padx=5, pady=5)

        self.canvas = tk.Canvas(container, bg=bg_color, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.task_frame = tk.Frame(self.canvas, bg=bg_color)

        self.task_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.task_frame, anchor="nw", width=220)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def clear_tasks(self):
        """Remove all task cards from the column"""
        for widget in self.task_frame.winfo_children():
            widget.destroy()
        self.tasks = []

    def add_task(self, task: Task, on_click=None, on_drag=None):
        """Add a task card to the column"""
        card = TaskCard(
            self.task_frame,
            task,
            on_click=on_click,
            on_drag_start=on_drag,
            width=200
        )
        card.pack(fill="x", pady=5, padx=5)
        self.tasks.append(task)

    def update_count(self):
        """Update the task count label"""
        self.count_label.config(text=f"({len(self.tasks)})")