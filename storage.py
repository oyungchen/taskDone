"""
Task storage module for file-based persistence.
Stores tasks in separate files by status.
"""
import os
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from models import Task, TaskStatus


class TaskStorage:
    """File-based task storage with separate files per status"""

    TASKS_DIR = "tasks"
    PENDING_FILE = os.path.join(TASKS_DIR, "pending.json")
    PROCESSING_FILE = os.path.join(TASKS_DIR, "processing.json")
    DONE_FILE = os.path.join(TASKS_DIR, "done.json")

    def __init__(self):
        self._ensure_storage_exists()

    def _ensure_storage_exists(self):
        """Create tasks directory and files if they don't exist"""
        Path(self.TASKS_DIR).mkdir(parents=True, exist_ok=True)

        for filepath in [self.PENDING_FILE, self.PROCESSING_FILE, self.DONE_FILE]:
            if not os.path.exists(filepath):
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump([], f)

    def _get_file_for_status(self, status: str) -> str:
        """Get the file path for a given status"""
        status_map = {
            TaskStatus.PENDING.value: self.PENDING_FILE,
            TaskStatus.PROCESSING.value: self.PROCESSING_FILE,
            TaskStatus.DONE.value: self.DONE_FILE
        }
        return status_map.get(status, self.PENDING_FILE)

    def _read_tasks_from_file(self, filepath: str) -> List[Task]:
        """Read all tasks from a JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [Task.from_dict(t) for t in data]
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write_tasks_to_file(self, filepath: str, tasks: List[Task]):
        """Write tasks to a JSON file"""
        data = [t.to_dict() for t in tasks]
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_all_tasks(self) -> List[Task]:
        """Get all tasks from all status files"""
        all_tasks = []
        for filepath in [self.PENDING_FILE, self.PROCESSING_FILE, self.DONE_FILE]:
            all_tasks.extend(self._read_tasks_from_file(filepath))
        return all_tasks

    def get_tasks_by_status(self, status: str) -> List[Task]:
        """Get tasks filtered by status"""
        filepath = self._get_file_for_status(status)
        return self._read_tasks_from_file(filepath)

    def get_tasks_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Task]:
        """Get tasks within a date range"""
        all_tasks = self.get_all_tasks()
        filtered = []
        for task in all_tasks:
            try:
                task_date = datetime.fromisoformat(task.created_at)
                if start_date <= task_date <= end_date:
                    filtered.append(task)
            except (ValueError, TypeError):
                continue
        return filtered

    def save_task(self, task: Task) -> bool:
        """Save a task to the appropriate status file"""
        try:
            filepath = self._get_file_for_status(task.status)
            tasks = self._read_tasks_from_file(filepath)

            # Check if task already exists (by name and created_at)
            existing_idx = None
            for idx, t in enumerate(tasks):
                if t.name == task.name and t.created_at == task.created_at:
                    existing_idx = idx
                    break

            if existing_idx is not None:
                tasks[existing_idx] = task
            else:
                tasks.append(task)

            self._write_tasks_to_file(filepath, tasks)
            return True
        except Exception as e:
            print(f"Error saving task: {e}")
            return False

    def delete_task(self, task: Task) -> bool:
        """Delete a task from storage"""
        try:
            filepath = self._get_file_for_status(task.status)
            tasks = self._read_tasks_from_file(filepath)

            # Find and remove the task
            filtered = [t for t in tasks if not (t.name == task.name and t.created_at == task.created_at)]

            if len(filtered) < len(tasks):
                self._write_tasks_to_file(filepath, filtered)
                return True
            return False
        except Exception as e:
            print(f"Error deleting task: {e}")
            return False

    def move_task(self, task: Task, new_status: str) -> bool:
        """Move a task to a different status file"""
        try:
            # Remove from old status
            if self.delete_task(task):
                # Update status and save to new file
                task.status = new_status
                if new_status == TaskStatus.PROCESSING.value and task.started_at is None:
                    task.started_at = datetime.now().isoformat()
                elif new_status == TaskStatus.DONE.value and task.completed_at is None:
                    task.completed_at = datetime.now().isoformat()
                return self.save_task(task)
            return False
        except Exception as e:
            print(f"Error moving task: {e}")
            return False