from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from bson import ObjectId
import logging
from .base import BaseDocument
from .task_status_log import TaskStatusLog
from .task import Task
from .research_session import ResearchSession

__all__ = ['Task', 'TaskStatusLog', 'ResearchSession']

class Task(BaseDocument):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session_id = kwargs.get('session_id', '')
        self.task_type = kwargs.get('task_type', '')
        self.title = kwargs.get('title', '')
        self.description = kwargs.get('description', '')
        
        # Status tracking
        self.status = kwargs.get('status', 'pending')  # pending, in_progress, waiting_system, waiting_user, completed, failed, cancelled, stale
        self.progress_percentage = kwargs.get('progress_percentage', 0)
        self.current_step = kwargs.get('current_step', '')
        self.total_steps = kwargs.get('total_steps', 0)
        
        # Timing and dependencies
        self.started_at = kwargs.get('started_at')
        self.completed_at = kwargs.get('completed_at')
        self.due_date = kwargs.get('due_date')
        
        # User action requirements
        self.requires_user_action = kwargs.get('requires_user_action', False)
        self.user_action_description = kwargs.get('user_action_description', '')
        self.user_action_deadline = kwargs.get('user_action_deadline')
        
        # Results and data
        self.result_data = kwargs.get('result_data', {})
        self.error_message = kwargs.get('error_message', '')
        self.retry_count = kwargs.get('retry_count', 0)
        self.max_retries = kwargs.get('max_retries', 3)
        
        # Dependencies
        self.depends_on = kwargs.get('depends_on', [])
        self.blocks = kwargs.get('blocks', [])
    
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
            'progress_percentage': self.progress_percentage,
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'requires_user_action': self.requires_user_action,
            'user_action_description': self.user_action_description,
            'user_action_deadline': self.user_action_deadline.isoformat() if self.user_action_deadline else None,
            'result_data': self.result_data,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'depends_on': [str(task_id) for task_id in self.depends_on],
            'blocks': [str(task_id) for task_id in self.blocks]
        }
        return {**base_dict, **task_dict}
    
    @classmethod
    def find_by_id(cls, task_id: str, db_manager) -> Optional['Task']:
        """Find task by ID"""
        if not task_id:
            return None
        collection = db_manager.get_collection('tasks')
        task_data = collection.find_one({'_id': ObjectId(task_id)})
        return cls.from_dict(task_data) if task_data else None
    
    @classmethod
    def find_by_session(cls, session_id: str, db_manager) -> List['Task']:
        """Find all tasks for a session"""
        collection = db_manager.get_collection('tasks')
        tasks = collection.find({'session_id': ObjectId(session_id)})
        return [cls.from_dict(task) for task in tasks]
    
    @classmethod
    def find_by_session_and_status(cls, session_id: str, status: str, db_manager) -> List['Task']:
        """Find tasks by session and status"""
        collection = db_manager.get_collection('tasks')
        tasks = collection.find({
            'session_id': ObjectId(session_id),
            'status': status
        })
        return [cls.from_dict(task) for task in tasks]
    
    @classmethod
    def find_dependent_tasks(cls, task_id: str, db_manager) -> List['Task']:
        """Find tasks that depend on the given task"""
        collection = db_manager.get_collection('tasks')
        tasks = collection.find({'depends_on': ObjectId(task_id)})
        return [cls.from_dict(task) for task in tasks]
    
    @classmethod
    def find_stale_tasks(cls, threshold: datetime, db_manager) -> List['Task']:
        """Find tasks that haven't been updated since threshold"""
        collection = db_manager.get_collection('tasks')
        tasks = collection.find({
            'status': {'$in': ['pending', 'in_progress']},
            'updated_at': {'$lt': threshold}
        })
        return [cls.from_dict(task) for task in tasks]

class ResearchSession(BaseDocument):
    collection_name = 'research_sessions'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.target_company = kwargs.get('target_company', '')
        self.research_type = kwargs.get('research_type', '')
        self.status = kwargs.get('status', 'pending')
        self.completion_percentage = kwargs.get('completion_percentage', 0)
        self.results = kwargs.get('results', {})
        self.task_ids = kwargs.get('task_ids', [])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        base_dict = super().to_dict()
        session_dict = {
            'target_company': self.target_company,
            'research_type': self.research_type,
            'status': self.status,
            'completion_percentage': self.completion_percentage,
            'results': self.results,
            'task_ids': [str(task_id) if isinstance(task_id, ObjectId) else task_id 
                        for task_id in self.task_ids]
        }
        return {**base_dict, **session_dict}
    
    def add_task(self, task_id: str) -> None:
        """Add task to session"""
        if isinstance(task_id, str):
            task_id = ObjectId(task_id)
        if task_id not in self.task_ids:
            self.task_ids.append(task_id)
    
    @classmethod
    def find_by_id(cls, session_id: str, db_manager) -> Optional['ResearchSession']:
        """Find session by ID"""
        if not session_id:
            return None
            
        try:
            collection = db_manager.get_collection(cls.collection_name)
            session_data = collection.find_one({'_id': ObjectId(session_id)})
            return cls.from_dict(session_data) if session_data else None
        except Exception as e:
            logging.error(f"Error finding session {session_id}: {str(e)}")
            return None
    
    @classmethod
    def find_active_sessions(cls, db_manager) -> List['ResearchSession']:
        """Find all active research sessions"""
        try:
            collection = db_manager.get_collection(cls.collection_name)
            sessions = collection.find({
                'status': {'$in': ['pending', 'in_progress']}
            })
            return [cls.from_dict(session) for session in sessions]
        except Exception as e:
            logging.error(f"Error finding active sessions: {str(e)}")
            return []
    
    @classmethod
    def find_by_company(cls, company_id: str, db_manager) -> List['ResearchSession']:
        """Find sessions for a company"""
        try:
            collection = db_manager.get_collection(cls.collection_name)
            sessions = collection.find({'target_company': company_id})
            return [cls.from_dict(session) for session in sessions]
        except Exception as e:
            logging.error(f"Error finding sessions for company {company_id}: {str(e)}")
            return [] 