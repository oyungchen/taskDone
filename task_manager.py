"""
Task Manager GUI Application
A kanban-style task management tool with three columns: Pending, Processing, Done
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
from typing import List, Optional, Callable
from models import Task, TaskStatus, Priority, PRIORITY_COLORS, STATUS_COLORS
from storage import TaskStorage


class TaskCard(tk.Frame):
    """A draggable task card widget"""

    def __init__(self, master, task: Task, on_drag_start, on_edit, on_delete, **kwargs):
        super().__init__(master, **kwargs)
        self.task = task
        self.on_drag_start = on_drag_start
        self.on_edit = on_edit
        self.on_delete = on_delete

        self.configure(bg=self._get_bg_color(), relief=tk.RAISED, bd=2, padx=5, pady=5)

        # Task name
        self.name_label = tk.Label(self, text=task.name, font=("Arial", 11, "bold"),
                                   bg=self._get_bg_color(), wraplength=180, justify=tk.LEFT)
        self.name_label.pack(anchor=tk.W, fill=tk.X)

        # Priority indicator
        priority_color = PRIORITY_COLORS.get(Priority(task.priority), "#888888")
        self.priority_frame = tk.Frame(self, bg=priority_color, height=4)
        self.priority_frame.pack(fill=tk.X, pady=(2, 5))

        # Created time
        created_str = self._format_time(task.created_at)
        self.time_label = tk.Label(self, text=f"Created: {created_str}",
                                   font=("Arial", 8), bg=self._get_bg_color(), fg="#666")
        self.time_label.pack(anchor=tk.W)

        # Context menu
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Edit", command=self._on_edit)
        self.context_menu.add_command(label="Delete", command=self._on_delete)

        # Bind events
        self.bind("<Button-1>", self._on_click)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Button-3>", self._on_right_click)  # Right-click for context menu

        for widget in [self.name_label, self.priority_frame, self.time_label]:
            widget.bind("<Button-1>", self._on_click)
            widget.bind("<B1-Motion>", self._on_drag)
            widget.bind("<ButtonRelease-1>", self._on_release)
            widget.bind("<Button-3>", self._on_right_click)

    def _get_bg_color(self) -> str:
        """Get background color based on task status"""
        try:
            status = TaskStatus(self.task.status)
            return STATUS_COLORS.get(status, "#ffffff")
        except ValueError:
            return "#ffffff"

    def _format_time(self, time_str: Optional[str]) -> str:
        """Format time string for display"""
        if not time_str:
            return "Unknown"
        try:
            dt = datetime.fromisoformat(time_str)
            return dt.strftime("%m-%d %H:%M")
        except:
            return time_str[:16] if len(time_str) > 16 else time_str

    def _on_click(self, event):
        """Handle mouse click - start drag tracking"""
        self.drag_start_x = event.x_root
        self.drag_start_y = event.y_root
        self.is_dragging = False

    def _on_drag(self, event):
        """Handle mouse drag"""
        if not hasattr(self, 'drag_start_x'):
            return

        # Check if moved enough to be considered a drag
        dx = abs(event.x_root - self.drag_start_x)
        dy = abs(event.y_root - self.drag_start_y)

        if dx > 5 or dy > 5:
            self.is_dragging = True
            if self.on_drag_start:
                self.on_drag_start(self, event.x_root, event.y_root)

    def _on_release(self, event):
        """Handle mouse release"""
        if not self.is_dragging:
            # This was a click, not a drag
            pass
        self.is_dragging = False

    def _on_right_click(self, event):
        """Show context menu on right click"""
        self.context_menu.post(event.x_root, event.y_root)

    def _on_edit(self):
        """Handle edit request"""
        if self.on_edit:
            self.on_edit(self.task)

    def _on_delete(self):
        """Handle delete request"""
        if self.on_delete:
            self.on_delete(self.task)


class TaskColumn(tk.Frame):
    """A column for displaying tasks of a specific status"""

    def __init__(self, master, title: str, status: TaskStatus,
                 on_drop: Callable, on_edit: Callable, on_delete: Callable,
                 bg_color: str = "#f0f0f0", **kwargs):
        super().__init__(master, **kwargs)
        self.status = status
        self.on_drop = on_drop
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.bg_color = bg_color

        self.configure(bg=bg_color, relief=tk.RIDGE, bd=2)

        # Header
        self.header = tk.Frame(self, bg=self._get_header_color(), height=40)
        self.header.pack(fill=tk.X)
        self.header.pack_propagate(False)

        self.title_label = tk.Label(self.header, text=title,
                                   font=("Arial", 14, "bold"),
                                   bg=self._get_header_color(), fg="white")
        self.title_label.pack(side=tk.LEFT, padx=10, pady=5)

        self.count_label = tk.Label(self.header, text="0",
                                   font=("Arial", 12, "bold"),
                                   bg=self._get_header_color(), fg="white")
        self.count_label.pack(side=tk.RIGHT, padx=10, pady=5)

        # Task container with scrollbar
        self.canvas = tk.Canvas(self, bg=bg_color, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.task_container = tk.Frame(self.canvas, bg=bg_color)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Pack scrollbar and canvas
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create window in canvas
        self.canvas_window = self.canvas.create_window((0, 0), window=self.task_container, anchor=tk.NW, width=280)

        # Bind resize and configure events
        self.task_container.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Drop target
        self.drag_enter_id = self.canvas.bind("<Enter>", self._on_drag_enter)
        self.drag_leave_id = self.canvas.bind("<Leave>", self._on_drag_leave)

        self.task_cards = []
        self.highlighted = False

    def _get_header_color(self) -> str:
        """Get header color based on status"""
        colors = {
            TaskStatus.PENDING: "#ffc107",
            TaskStatus.PROCESSING: "#007bff",
            TaskStatus.DONE: "#28a745"
        }
        return colors.get(self.status, "#6c757d")

    def _on_frame_configure(self, event=None):
        """Reset the scroll region to encompass the inner frame"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """When canvas is resized, resize the inner frame width"""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width - 5)

    def _on_drag_enter(self, event):
        """Highlight column when drag enters"""
        if not self.highlighted:
            self.canvas.configure(bg=self._get_highlight_color())
            self.highlighted = True

    def _on_drag_leave(self, event):
        """Remove highlight when drag leaves"""
        # Check if we're really leaving the canvas
        widget = event.widget
        if widget == self.canvas:
            self.canvas.configure(bg=self.bg_color)
            self.highlighted = False

    def _get_highlight_color(self) -> str:
        """Get highlight color for drag over"""
        colors = {
            TaskStatus.PENDING: "#ffe066",
            TaskStatus.PROCESSING: "#66b3ff",
            TaskStatus.DONE: "#6bcf7f"
        }
        return colors.get(self.status, "#d0d0d0")

    def add_task_card(self, task: Task):
        """Add a task card to this column"""
        def on_drag_start(card, x, y):
            # Notify parent of drag start
            self.event_generate("<<TaskDragStart>>",
                              x=x, y=y,
                              data=card.task.to_json())

        card = TaskCard(self.task_container, task,
                       on_drag_start=on_drag_start,
                       on_edit=self.on_edit,
                       on_delete=self.on_delete)
        card.pack(fill=tk.X, padx=5, pady=3)
        self.task_cards.append(card)
        self._update_count()

    def clear_tasks(self):
        """Remove all task cards"""
        for card in self.task_cards:
            card.destroy()
        self.task_cards = []
        self._update_count()

    def _update_count(self):
        """Update the task count label"""
        self.count_label.config(text=str(len(self.task_cards)))

    def highlight(self, active: bool = True):
        """Set highlight state for drop target"""
        if active:
            self.configure(bg=self._get_highlight_color())
        else:
            self.configure(bg=self.bg_color)


def main():
    app = TodoApp()
    app.run()


if __name__ == "__main__":
    main()