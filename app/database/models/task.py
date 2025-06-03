from typing import Dict, Any, Optional, List
from datetime import datetime
from bson import ObjectId
from ..base import BaseDocument

class TaskStatus:
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    STALE = 'stale'

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
        self.description: str = kwargs.get('description', '')
        self.status: str = kwargs.get('status', TaskStatus.PENDING)
        self.progress: float = kwargs.get('progress', 0.0)
        self.current_step: str = kwargs.get('current_step', '')
        self.error_message: str = kwargs.get('error_message', '')
        self.result_data: Dict[str, Any] = kwargs.get('result_data', {})
        self.depends_on: List[ObjectId] = []
        for task_id in kwargs.get('depends_on', []):
            if isinstance(task_id, str):
                self.depends_on.append(ObjectId(task_id))
            else:
                self.depends_on.append(task_id)
        self.retry_count: int = kwargs.get('retry_count', 0)
        self.max_retries: int = kwargs.get('max_retries', 3)
        self.started_at: Optional[datetime] = kwargs.get('started_at')
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
            'task_id': str(self._id) if self._id else None,
            'session_id': str(self.session_id) if self.session_id else None,
            'task_type': self.task_type,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'progress': self.progress,
            'current_step': self.current_step,
            'error_message': self.error_message,
            'result_data': self.result_data,
            'depends_on': [str(task_id) for task_id in self.depends_on],
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
        return {**base_dict, **task_dict}
        
    def complete(self):
        """Mark task as completed"""
        self.status = TaskStatus.COMPLETED
        self.progress = 100.0
        self.completed_at = datetime.utcnow()

    @classmethod
    def find_by_session(cls, session_id: str, db_manager) -> List['Task']:
        """Find all tasks for a given session"""
        if not cls.collection_name:
            raise ValueError("collection_name must be set in derived class")
            
        collection = db_manager.get_collection(cls.collection_name)
        tasks = collection.find({'session_id': ObjectId(session_id)})
        return [cls.from_dict(task) for task in tasks]
    
    @classmethod
    def find_by_session_and_status(cls, session_id: str, status: str, db_manager) -> List['Task']:
        """Find all tasks for a given session with specific status"""
        if not cls.collection_name:
            raise ValueError("collection_name must be set in derived class")
            
        collection = db_manager.get_collection(cls.collection_name)
        tasks = collection.find({
            'session_id': ObjectId(session_id),
            'status': status
        })
        return [cls.from_dict(task) for task in tasks]
    
    @classmethod
    def find_stale_tasks(cls, stale_threshold: datetime, db_manager) -> List['Task']:
        """Find tasks that haven't been updated since the threshold"""
        if not cls.collection_name:
            raise ValueError("collection_name must be set in derived class")
            
        collection = db_manager.get_collection(cls.collection_name)
        tasks = collection.find({
            'status': {'$in': [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]},
            'updated_at': {'$lt': stale_threshold}
        })
        return [cls.from_dict(task) for task in tasks]
    
    @classmethod
    def find_dependent_tasks(cls, task_id: str, db_manager) -> List['Task']:
        """Find tasks that depend on the given task"""
        if not cls.collection_name:
            raise ValueError("collection_name must be set in derived class")
            
        collection = db_manager.get_collection(cls.collection_name)
        tasks = collection.find({'depends_on': ObjectId(task_id)})
        return [cls.from_dict(task) for task in tasks] 