from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from bson import ObjectId
from ..base import BaseDocument

class TaskStatusLog(BaseDocument):
    """Model for tracking task status changes"""
    collection_name = 'task_status_logs'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.task_id = kwargs.get('task_id', '')
        self.old_status = kwargs.get('old_status')
        self.new_status = kwargs.get('new_status')
        self.changed_by = kwargs.get('changed_by', 'system')  # system or user ID
        self.change_reason = kwargs.get('change_reason', '')
        self.timestamp = kwargs.get('timestamp', datetime.utcnow())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary"""
        base_dict = super().to_dict()
        log_dict = {
            'task_id': str(self.task_id) if isinstance(self.task_id, str) else str(self.task_id),
            'old_status': self.old_status,
            'new_status': self.new_status,
            'changed_by': self.changed_by,
            'change_reason': self.change_reason,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
        return {**base_dict, **log_dict}
    
    @classmethod
    def find_by_task_id(cls, task_id: str, db_manager) -> List['TaskStatusLog']:
        """Find all status changes for a task"""
        collection = db_manager.get_collection(cls.collection_name)
        logs = collection.find({'task_id': ObjectId(task_id)}).sort('timestamp', -1)
        return [cls.from_dict(log) for log in logs]
    
    @classmethod
    def find_recent_changes(cls, hours: int, db_manager) -> List['TaskStatusLog']:
        """Find recent status changes"""
        threshold = datetime.utcnow() - timedelta(hours=hours)
        collection = db_manager.get_collection(cls.collection_name)
        logs = collection.find({'timestamp': {'$gt': threshold}}).sort('timestamp', -1)
        return [cls.from_dict(log) for log in logs] 