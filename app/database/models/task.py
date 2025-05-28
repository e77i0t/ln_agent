from typing import Dict, Any, Optional
from datetime import datetime
from bson import ObjectId
from ..base import BaseDocument

class TaskStatus:
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    FAILED = 'failed'

class TaskType:
    RESEARCH = 'research'
    DATA_COLLECTION = 'data_collection'
    ANALYSIS = 'analysis'
    REPORT = 'report'

class Task(BaseDocument):
    """Task document model"""
    collection_name = 'tasks'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session_id: Optional[ObjectId] = kwargs.get('session_id')
        if isinstance(self.session_id, str):
            self.session_id = ObjectId(self.session_id)
        self.task_type: str = kwargs.get('task_type', TaskType.RESEARCH)
        self.title: str = kwargs.get('title', '')
        self.status: str = kwargs.get('status', TaskStatus.PENDING)
        self.progress: float = kwargs.get('progress', 0.0)
        self.completed_at: Optional[datetime] = kwargs.get('completed_at')
        
    def validate(self) -> bool:
        """Validate required fields"""
        if not self.session_id:
            raise ValueError("Session ID is required")
        if not self.title.strip():
            raise ValueError("Task title is required")
        if self.task_type not in vars(TaskType).values():
            raise ValueError("Invalid task type")
        if self.status not in vars(TaskStatus).values():
            raise ValueError("Invalid task status")
        if not 0 <= self.progress <= 100:
            raise ValueError("Progress must be between 0 and 100")
        return True
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary"""
        base_dict = super().to_dict()
        task_dict = {
            'session_id': self.session_id,
            'task_type': self.task_type,
            'title': self.title,
            'status': self.status,
            'progress': self.progress,
            'completed_at': self.completed_at
        }
        return {**base_dict, **task_dict}
        
    def complete(self):
        """Mark task as completed"""
        self.status = TaskStatus.COMPLETED
        self.progress = 100.0
        self.completed_at = datetime.utcnow() 