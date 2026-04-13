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
                 on_drag_start: Optional[Callable] = None,
                 on_drag_end: Optional[Callable] = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.task = task
        self.on_click = on_click
        self.on_drag_start = on_drag_start
        self.on_drag_end = on_drag_end
        self.drag_data = {"x": 0, "y": 0, "dragging": False}

        # Drag ghost widget for visual feedback
        self.ghost_window = None

        # Card styling
        self.configure(
            bg=task.color or "#ffffff",
            highlightbackground="#cccccc",
            highlightthickness=1,
            relief="raised",
            bd=2
        )

        # Bind drag events
        self.bind("<Button-1>", self._on_drag_start)
        self.bind("<B1-Motion>", self._on_drag_motion)
        self.bind("<ButtonRelease-1>", self._on_drag_end)

        # Task name
        self.name_label = tk.Label(
            self,
            text=task.name,
            font=("Arial", 10, "bold"),
            bg=task.color or "#ffffff",
            wraplength=180,
            justify="left"
        )
        self.name_label.pack(anchor="w", padx=5, pady=(5, 0))
        self.name_label.bind("<Button-1>", self._on_drag_start)
        self.name_label.bind("<B1-Motion>", self._on_drag_motion)
        self.name_label.bind("<ButtonRelease-1>", self._on_drag_end)

        # Created time
        created_text = f"Created: {self._format_time(task.created_at)}"
        self.created_label = tk.Label(
            self,
            text=created_text,
            font=("Arial", 8),
            bg=task.color or "#ffffff",
            fg="#666666"
        )
        self.created_label.pack(anchor="w", padx=5, pady=(2, 5))
        self.created_label.bind("<Button-1>", self._on_drag_start)
        self.created_label.bind("<B1-Motion>", self._on_drag_motion)
        self.created_label.bind("<ButtonRelease-1>", self._on_drag_end)

    def _format_time(self, time_str: Optional[str]) -> str:
        """Format ISO time string for display"""
        if not time_str:
            return "N/A"
        try:
            dt = datetime.fromisoformat(time_str)
            return dt.strftime("%m-%d %H:%M")
        except:
            return time_str[:16] if len(time_str) > 16 else time_str

    def _on_drag_start(self, event):
        """Handle drag start"""
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        self.drag_data["dragging"] = False

    def _on_drag_motion(self, event):
        """Handle drag motion"""
        # Check if we've moved enough to start dragging
        dx = abs(event.x - self.drag_data["x"])
        dy = abs(event.y - self.drag_data["y"])

        if not self.drag_data["dragging"] and (dx > 5 or dy > 5):
            self.drag_data["dragging"] = True
            if self.on_drag_start:
                self.on_drag_start(self.task)
            # Create ghost window for visual feedback
            self._create_ghost()

        # Update ghost position during drag
        if self.drag_data["dragging"] and self.ghost_window:
            self._update_ghost_position(event)

    def _on_drag_end(self, event):
        """Handle drag end"""
        was_dragging = self.drag_data["dragging"]
        self.drag_data["dragging"] = False

        if self.on_click and not was_dragging:
            self.on_click(self.task)

        if self.on_drag_end:
            self.on_drag_end(self.task)

    def _create_ghost(self):
        """Create ghost window for drag visual feedback"""
        if self.ghost_window:
            return
        self.ghost_window = tk.Toplevel(self)
        self.ghost_window.overrideredirect(True)
        self.ghost_window.attributes("-alpha", 0.7)
        self.ghost_window.attributes("-topmost", True)

        # Create a simple label showing task name
        ghost_label = tk.Label(
            self.ghost_window,
            text=self.task.name,
            font=("Arial", 10, "bold"),
            bg=self.task.color or "#ffffff",
            relief="raised",
            bd=2,
            padx=10,
            pady=5
        )
        ghost_label.pack()

        self._update_ghost_position(None)

    def _update_ghost_position(self, event):
        """Update ghost window position to follow mouse"""
        if not self.ghost_window:
            return
        x = self.winfo_pointerx() + 10
        y = self.winfo_pointery() + 10
        self.ghost_window.geometry(f"+{x}+{y}")

    def destroy_ghost(self):
        """Destroy ghost window"""
        if self.ghost_window:
            self.ghost_window.destroy()
            self.ghost_window = None


class KanbanColumn(tk.Frame):
    """Kanban column widget for a specific status"""

    def __init__(self, parent, title: str, status: TaskStatus,
                 bg_color: str = "#f0f0f0", on_drop: Optional[Callable] = None,
                 on_drag_enter: Optional[Callable] = None,
                 on_drag_leave: Optional[Callable] = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.status = status
        self.tasks = []
        self.on_drop = on_drop
        self.on_drag_enter = on_drag_enter
        self.on_drag_leave = on_drag_leave
        self.bg_color = bg_color
        self.is_drop_target = False
        self.drop_highlight_color = "#2196F3"

        # Column styling
        self.configure(bg=bg_color, relief="sunken", bd=2)

        # Header
        header_frame = tk.Frame(self, bg=bg_color)
        header_frame.pack(fill="x", padx=5, pady=5)

        # Title with status indicator color (using plain text, no emoji)
        status_colors = {
            TaskStatus.PENDING: "#ff9800",
            TaskStatus.PROCESSING: "#2196F3",
            TaskStatus.DONE: "#4CAF50"
        }
        status_color = status_colors.get(status, "#666666")

        title_label = tk.Label(
            header_frame,
            text=title,
            font=("Arial", 12, "bold"),
            bg=bg_color,
            fg=status_color
        )
        title_label.pack(side="left")

        self.count_label = tk.Label(
            header_frame,
            text="(0)",
            font=("Arial", 11),
            bg=bg_color,
            fg="#666666"
        )
        self.count_label.pack(side="left", padx=(8, 0))

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

        # Bind hover events for drop indication
        self.canvas.bind("<Enter>", self._on_enter)
        self.canvas.bind("<Leave>", self._on_leave)

    def _on_enter(self, event):
        """Handle mouse enter - indicate drop zone"""
        if self.on_drop:
            self.configure(highlightbackground="#2196F3", highlightthickness=3)

    def _on_leave(self, event):
        """Handle mouse leave"""
        self.configure(highlightbackground="#cccccc", highlightthickness=0)

    def clear_tasks(self):
        """Remove all task cards from the column"""
        for widget in self.task_frame.winfo_children():
            widget.destroy()
        self.tasks = []

    def add_task(self, task: Task, on_click=None, on_drag=None, on_drag_end=None):
        """Add a task card to the column"""
        card = TaskCard(
            self.task_frame,
            task,
            on_click=on_click,
            on_drag_start=on_drag,
            on_drag_end=on_drag_end,
            width=200
        )
        card.pack(fill="x", pady=5, padx=5)
        self.tasks.append(task)

    def update_count(self):
        """Update the task count label"""
        self.count_label.config(text=f"({len(self.tasks)})")

    def set_drop_target(self, active: bool):
        """Set or clear drop target status"""
        self.is_drop_target = active
        if active:
            self.configure(
                highlightbackground=self.drop_highlight_color,
                highlightthickness=3
            )
            if self.on_drag_enter:
                self.on_drag_enter(self.status)
        else:
            self.configure(highlightbackground="#cccccc", highlightthickness=0)
            if self.on_drag_leave:
                self.on_drag_leave(self.status)

    def handle_drop(self, task: Task):
        """Handle task drop on this column"""
        if self.on_drop:
            self.on_drop(task, self.status)
        self.set_drop_target(False)