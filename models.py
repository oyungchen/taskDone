"""
Task data models for the task management system.
"""
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Optional
import json


class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"


class Priority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


PRIORITY_COLORS = {
    Priority.HIGH: "#ff4444",
    Priority.MEDIUM: "#ffaa00",
    Priority.LOW: "#44aa44"
}

STATUS_COLORS = {
    TaskStatus.PENDING: "#fff3cd",
    TaskStatus.PROCESSING: "#cce5ff",
    TaskStatus.DONE: "#d4edda"
}


@dataclass
class Task:
    name: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    priority: str = "medium"
    status: str = "pending"
    color: Optional[str] = None

    def __post_init__(self):
        if self.color is None:
            self.color = PRIORITY_COLORS.get(Priority(self.priority), "#888888")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(**data)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "Task":
        return cls.from_dict(json.loads(json_str))

    def start(self):
        """Mark task as started"""
        self.status = TaskStatus.PROCESSING.value
        self.started_at = datetime.now().isoformat()

    def complete(self):
        """Mark task as completed"""
        self.status = TaskStatus.DONE.value
        self.completed_at = datetime.now().isoformat()

    def reset(self):
        """Reset task to pending"""
        self.status = TaskStatus.PENDING.value
        self.started_at = None
        self.completed_at = None