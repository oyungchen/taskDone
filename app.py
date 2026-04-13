"""
Main GUI application for the task management system.
Provides a Kanban-style board interface.
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
from typing import Optional
from models import Task, TaskStatus, Priority, PRIORITY_COLORS, STATUS_COLORS
from storage import TaskStorage
from gui import KanbanColumn, TaskCard


class TaskManagerApp:
    """Main application window for the task manager"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Task Manager - Kanban Board")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f5f5f5")

        self.storage = TaskStorage()
        self.current_date = datetime.now()

        self.create_menu()
        self.create_toolbar()
        self.create_date_selector()
        self.create_kanban_board()
        self.create_status_bar()

        self.refresh_board()

    def create_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="新建任务", command=self.show_add_task_dialog, accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Previous Week", command=self.prev_week)
        view_menu.add_command(label="Next Week", command=self.next_week)
        view_menu.add_command(label="Today", command=self.go_to_today)

        # Bind keyboard shortcuts
        self.root.bind("<Control-n>", lambda e: self.show_add_task_dialog())

    def create_toolbar(self):
        """Create toolbar with quick actions"""
        toolbar = tk.Frame(self.root, bg="#f5f5f5", relief="raised", bd=1)
        toolbar.pack(fill="x", padx=5, pady=5)

        # Add task button
        add_btn = tk.Button(
            toolbar,
            text="+ 新建任务",
            font=("Arial", 10, "bold"),
            bg="#4CAF50",
            command=self.show_add_task_dialog
        )
        add_btn.pack(side="left", padx=5, pady=5)

        # Refresh button
        refresh_btn = tk.Button(
            toolbar,
            text="刷新",
            font=("Arial", 10),
            command=self.refresh_board
        )
        refresh_btn.pack(side="left", padx=5, pady=5)

    def create_date_selector(self):
        """Create date range selector"""
        date_frame = tk.Frame(self.root, bg="#f5f5f5")
        date_frame.pack(fill="x", padx=10, pady=5)

        # Previous week button
        prev_btn = tk.Button(
            date_frame,
            text="← 上周",
            font=("Arial", 9),
            command=self.prev_week
        )
        prev_btn.pack(side="left", padx=5)

        # Date label
        self.date_label = tk.Label(
            date_frame,
            text=self._get_date_range_text(),
            font=("Arial", 11, "bold"),
            bg="#f5f5f5"
        )
        self.date_label.pack(side="left", padx=20)

        # Next week button
        next_btn = tk.Button(
            date_frame,
            text="下周 →",
            font=("Arial", 9),
            command=self.next_week
        )
        next_btn.pack(side="left", padx=5)

        # Today button
        today_btn = tk.Button(
            date_frame,
            text="今天",
            font=("Arial", 9, "bold"),
            bg="#2196F3",
            command=self.go_to_today
        )
        today_btn.pack(side="right", padx=5)

    def create_kanban_board(self):
        """Create the Kanban board with three columns"""
        # Main container with scrollbar
        container = tk.Frame(self.root, bg="#f5f5f5")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # Canvas for horizontal scrolling
        self.board_canvas = tk.Canvas(container, bg="#f5f5f5", highlightthickness=0)
        h_scrollbar = tk.Scrollbar(container, orient="horizontal", command=self.board_canvas.xview)

        self.board_canvas.configure(xscrollcommand=h_scrollbar.set)

        h_scrollbar.pack(side="bottom", fill="x")
        self.board_canvas.pack(side="top", fill="both", expand=True)

        # Frame to hold the three columns
        self.columns_frame = tk.Frame(self.board_canvas, bg="#f5f5f5")
        self.board_canvas.create_window((0, 0), window=self.columns_frame, anchor="nw")

        # Create three columns (without emoji to avoid display issues)
        self.pending_column = KanbanColumn(
            self.columns_frame,
            "[待处理]",
            TaskStatus.PENDING,
            bg_color="#fff8e1",
            on_drop=lambda task: self._on_task_drop(task, TaskStatus.PENDING)
        )
        self.pending_column.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.processing_column = KanbanColumn(
            self.columns_frame,
            "[进行中]",
            TaskStatus.PROCESSING,
            bg_color="#e3f2fd",
            on_drop=lambda task: self._on_task_drop(task, TaskStatus.PROCESSING)
        )
        self.processing_column.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.done_column = KanbanColumn(
            self.columns_frame,
            "[已完成]",
            TaskStatus.DONE,
            bg_color="#e8f5e9",
            on_drop=lambda task: self._on_task_drop(task, TaskStatus.DONE)
        )
        self.done_column.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        # Update scroll region when frame size changes
        self.columns_frame.bind("<Configure>", self._on_frame_configure)

        # Bind drag and drop events
        self.dragged_task = None

    def _on_frame_configure(self, event=None):
        """Reset the scroll region to encompass the inner frame"""
        self.board_canvas.configure(scrollregion=self.board_canvas.bbox("all"))

    def create_status_bar(self):
        """Create status bar at the bottom"""
        self.status_bar = tk.Label(
            self.root,
            text="Ready",
            bd=1,
            relief="sunken",
            anchor="w",
            font=("Arial", 9)
        )
        self.status_bar.pack(side="bottom", fill="x")

    # === Date range methods ===

    def _get_date_range_text(self) -> str:
        """Get formatted date range text"""
        start = self.current_date - timedelta(days=3)
        end = self.current_date + timedelta(days=3)
        return f"{start.strftime('%Y-%m-%d')} ~ {end.strftime('%Y-%m-%d')}"

    def prev_week(self):
        """Go to previous week"""
        self.current_date -= timedelta(days=7)
        self.date_label.config(text=self._get_date_range_text())
        self.refresh_board()

    def next_week(self):
        """Go to next week"""
        self.current_date += timedelta(days=7)
        self.date_label.config(text=self._get_date_range_text())
        self.refresh_board()

    def go_to_today(self):
        """Go to today"""
        self.current_date = datetime.now()
        self.date_label.config(text=self._get_date_range_text())
        self.refresh_board()

    # === Task operations ===

    def refresh_board(self):
        """Refresh the Kanban board with current tasks"""
        # Get date range
        start = self.current_date - timedelta(days=3)
        end = self.current_date + timedelta(days=3)

        # Get all tasks
        all_tasks = self.storage.get_all_tasks()

        # Filter by date range
        filtered_tasks = []
        for task in all_tasks:
            try:
                task_date = datetime.fromisoformat(task.created_at)
                if start <= task_date <= end:
                    filtered_tasks.append(task)
            except (ValueError, TypeError):
                continue

        # Clear columns
        self.pending_column.clear_tasks()
        self.processing_column.clear_tasks()
        self.done_column.clear_tasks()

        # Add tasks to appropriate columns
        for task in filtered_tasks:
            if task.status == TaskStatus.PENDING.value:
                self.pending_column.add_task(
                    task,
                    on_click=self.on_task_click,
                    on_drag=self.on_task_drag,
                    on_drag_end=self.on_task_drag_end
                )
            elif task.status == TaskStatus.PROCESSING.value:
                self.processing_column.add_task(
                    task,
                    on_click=self.on_task_click,
                    on_drag=self.on_task_drag,
                    on_drag_end=self.on_task_drag_end
                )
            elif task.status == TaskStatus.DONE.value:
                self.done_column.add_task(
                    task,
                    on_click=self.on_task_click,
                    on_drag=self.on_task_drag,
                    on_drag_end=self.on_task_drag_end
                )

        # Update counts
        self.pending_column.update_count()
        self.processing_column.update_count()
        self.done_column.update_count()

        # Update status bar
        total = len(filtered_tasks)
        self.status_bar.config(text=f"Showing {total} tasks for {self._get_date_range_text()}")

    def show_add_task_dialog(self):
        """Show dialog to add a new task"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Task")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()

        # Task name
        tk.Label(dialog, text="Task Name:", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        name_entry = tk.Entry(dialog, font=("Arial", 11), width=40)
        name_entry.pack(fill="x", padx=10, pady=5)
        name_entry.focus()

        # Priority
        tk.Label(dialog, text="Priority:", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        priority_var = tk.StringVar(value="medium")
        priority_frame = tk.Frame(dialog)
        priority_frame.pack(anchor="w", padx=10, pady=5)

        for text, value in [("High", "high"), ("Medium", "medium"), ("Low", "low")]:
            rb = tk.Radiobutton(
                priority_frame,
                text=text,
                variable=priority_var,
                value=value,
                font=("Arial", 9)
            )
            rb.pack(side="left", padx=10)

        # Buttons
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(fill="x", padx=10, pady=20)

        def save_task():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Warning", "Please enter a task name.", parent=dialog)
                return

            priority = priority_var.get()
            task = Task(
                name=name,
                created_at=datetime.now().isoformat(),
                priority=priority,
                status=TaskStatus.PENDING.value
            )

            if self.storage.save_task(task):
                self.refresh_board()
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to save task.", parent=dialog)

        tk.Button(
            btn_frame,
            text="Cancel",
            font=("Arial", 10),
            command=dialog.destroy
        ).pack(side="right", padx=5)

        tk.Button(
            btn_frame,
            text="Save Task",
            font=("Arial", 10, "bold"),
            bg="#4CAF50",
            command=save_task
        ).pack(side="right", padx=5)

        # Enter key to save
        dialog.bind("<Return>", lambda e: save_task())

    def on_task_click(self, task: Task):
        """Handle task card click"""
        self.show_task_details(task)

    def on_task_drag(self, task: Task):
        """Handle task card drag start - mark task as being dragged"""
        self.dragged_task = task
        # Change cursor to indicate dragging
        self.root.config(cursor="fleur")
        # Store reference to source card for ghost cleanup
        self.drag_source_card = None

    def on_task_drag_end(self, task: Task):
        """Handle task card drag end - cleanup"""
        # Reset cursor
        self.root.config(cursor="")
        # Clean up ghost window if exists
        if hasattr(self, 'drag_source_card') and self.drag_source_card:
            # Find the card widget and destroy its ghost
            for column in [self.pending_column, self.processing_column, self.done_column]:
                for child in column.task_frame.winfo_children():
                    if isinstance(child, TaskCard) and child.task.id == task.id:
                        child.destroy_ghost()
                        break
        self.drag_source_card = None

    def _on_task_drop(self, task: Task, target_status: TaskStatus):
        """Handle task drop on a column"""
        # Reset cursor
        self.root.config(cursor="")

        if not self.dragged_task:
            return

        # Only move if status changed
        if self.dragged_task.status == target_status.value:
            self.dragged_task = None
            return

        # Move the task
        if self.storage.move_task(self.dragged_task, target_status.value):
            self.refresh_board()
        else:
            messagebox.showerror("Error", "Failed to move task.")

        self.dragged_task = None

    def show_task_details(self, task: Task):
        """Show task details dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Task Details")
        dialog.geometry("400x400")
        dialog.transient(self.root)

        # Task info frame
        info_frame = tk.Frame(dialog, padx=20, pady=20)
        info_frame.pack(fill="both", expand=True)

        # Name
        tk.Label(
            info_frame,
            text=task.name,
            font=("Arial", 14, "bold"),
            wraplength=350
        ).pack(anchor="w", pady=(0, 10))

        # Status
        tk.Label(
            info_frame,
            text=f"Status: {task.status.upper()}",
            font=("Arial", 11),
            fg=self._get_status_color(task.status)
        ).pack(anchor="w", pady=2)

        # Priority
        tk.Label(
            info_frame,
            text=f"Priority: {task.priority.upper()}",
            font=("Arial", 11)
        ).pack(anchor="w", pady=2)

        # Created
        tk.Label(
            info_frame,
            text=f"Created: {self._format_datetime(task.created_at)}",
            font=("Arial", 10),
            fg="#666666"
        ).pack(anchor="w", pady=(10, 2))

        # Started (if applicable)
        if task.started_at:
            tk.Label(
                info_frame,
                text=f"Started: {self._format_datetime(task.started_at)}",
                font=("Arial", 10),
                fg="#666666"
            ).pack(anchor="w", pady=2)

        # Completed (if applicable)
        if task.completed_at:
            tk.Label(
                info_frame,
                text=f"Completed: {self._format_datetime(task.completed_at)}",
                font=("Arial", 10),
                fg="#666666"
            ).pack(anchor="w", pady=2)

        # Button frame
        btn_frame = tk.Frame(dialog, padx=20, pady=15)
        btn_frame.pack(fill="x")

        # Status change buttons
        if task.status != TaskStatus.PENDING.value:
            tk.Button(
                btn_frame,
                text="Move to Pending",
                command=lambda: self.change_task_status(task, TaskStatus.PENDING.value, dialog)
            ).pack(side="left", padx=5)

        if task.status != TaskStatus.PROCESSING.value:
            tk.Button(
                btn_frame,
                text="Move to Processing",
                command=lambda: self.change_task_status(task, TaskStatus.PROCESSING.value, dialog)
            ).pack(side="left", padx=5)

        if task.status != TaskStatus.DONE.value:
            tk.Button(
                btn_frame,
                text="Move to Done",
                command=lambda: self.change_task_status(task, TaskStatus.DONE.value, dialog)
            ).pack(side="left", padx=5)

        # Delete button
        tk.Button(
            btn_frame,
            text="Delete",
            bg="#f44336",
            fg="white",
            command=lambda: self.delete_task(task, dialog)
        ).pack(side="right", padx=5)

        # Close button
        tk.Button(
            btn_frame,
            text="Close",
            command=dialog.destroy
        ).pack(side="right", padx=5)

    def change_task_status(self, task: Task, new_status: str, dialog):
        """Change task status and refresh"""
        if self.storage.move_task(task, new_status):
            self.refresh_board()
            dialog.destroy()
        else:
            messagebox.showerror("Error", "Failed to move task.")

    def delete_task(self, task: Task, dialog):
        """Delete a task"""
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this task?"):
            if self.storage.delete_task(task):
                self.refresh_board()
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to delete task.")

    def _get_status_color(self, status: str) -> str:
        """Get color for a status"""
        colors = {
            TaskStatus.PENDING.value: "#ff9800",
            TaskStatus.PROCESSING.value: "#2196F3",
            TaskStatus.DONE.value: "#4CAF50"
        }
        return colors.get(status, "#666666")

    def _format_datetime(self, dt_str: Optional[str]) -> str:
        """Format datetime string for display"""
        if not dt_str:
            return "N/A"
        try:
            dt = datetime.fromisoformat(dt_str)
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return dt_str

    def run(self):
        """Start the application"""
        self.root.mainloop()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = TaskManagerApp(root)
    app.run()


if __name__ == "__main__":
    main()