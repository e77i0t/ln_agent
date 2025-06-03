"""Task service for managing task operations"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from bson import ObjectId
from flask import current_app

from app.database.models import Task, TaskStatusLog

class TaskService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_task(self, session_id: str, task_type: str, title: str, 
                   description: str = None, depends_on: List[str] = None) -> Task:
        """Create a new task"""
        task = Task(
            session_id=session_id,
            task_type=task_type,
            title=title,
            description=description,
            depends_on=depends_on or [],
            status='pending',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        task.save(current_app.db)
        
        self._log_status_change(str(task._id), None, 'pending', 'system', 'Task created')
        return task
    
    def update_task_status(self, task_id: str, new_status: str, 
                          progress: int = None, current_step: str = None,
                          error_message: str = None) -> Task:
        """Update task status with logging"""
        task = Task.find_by_id(task_id, current_app.db)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        old_status = task.status
        task.status = new_status
        task.updated_at = datetime.utcnow()
        
        if progress is not None:
            task.progress = float(progress)
        
        if current_step:
            task.current_step = current_step
            
        if error_message:
            task.error_message = error_message
        
        if new_status == 'in_progress' and not task.started_at:
            task.started_at = datetime.utcnow()
        elif new_status == 'completed':
            task.completed_at = datetime.utcnow()
            task.progress = 100.0
        
        # Save task updates
        if not task.save(current_app.db):
            self.logger.error(f"Failed to save task {task_id} status update")
            return None
        
        # Log status change
        try:
            self._log_status_change(task_id, old_status, new_status, 'system')
            self.logger.info(f"Task {task_id} status changed: {old_status} -> {new_status}")
        except Exception as e:
            self.logger.error(f"Failed to log status change for task {task_id}: {str(e)}")
        
        # Check dependent tasks if completed
        if new_status == 'completed':
            try:
                self._check_dependent_tasks(task_id)
            except Exception as e:
                self.logger.error(f"Error checking dependent tasks for {task_id}: {str(e)}")
            
        return task
    
    def complete_task(self, task_id: str, result_data: Dict[str, Any]) -> Task:
        """Mark task as completed with results"""
        task = Task.find_by_id(task_id, current_app.db)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        task.status = 'completed'
        task.progress_percentage = 100
        task.completed_at = datetime.utcnow()
        task.result_data = result_data
        task.save(current_app.db)
        
        self._log_status_change(task_id, task.status, 'completed', 'system')
        self._check_dependent_tasks(task_id)
        
        return task
    
    def fail_task(self, task_id: str, error_message: str) -> Task:
        """Mark task as failed"""
        task = Task.find_by_id(task_id, current_app.db)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        old_status = task.status
        task.status = 'failed'
        task.error_message = error_message
        task.updated_at = datetime.utcnow()
        
        # Save task updates
        if not task.save(current_app.db):
            self.logger.error(f"Failed to save task {task_id} failure update")
            return None
        
        # Log status change
        try:
            self._log_status_change(task_id, old_status, 'failed', 'system', error_message)
            self.logger.info(f"Task {task_id} marked as failed: {error_message}")
        except Exception as e:
            self.logger.error(f"Failed to log status change for task {task_id}: {str(e)}")
        
        return task
    
    def retry_task(self, task_id: str) -> Task:
        """Retry a failed task"""
        task = Task.find_by_id(task_id, current_app.db)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        if task.status != 'failed':
            raise ValueError("Only failed tasks can be retried")
        
        if task.retry_count >= task.max_retries:
            raise ValueError("Maximum retry attempts exceeded")
        
        old_status = task.status
        task.retry_count += 1
        task.status = 'pending'
        task.error_message = None
        task.progress = 0
        task.current_step = 'Task queued for retry'
        task.updated_at = datetime.utcnow()
        
        # Save task updates
        if not task.save(current_app.db):
            self.logger.error(f"Failed to save task {task_id} retry update")
            return None
        
        # Log status change
        try:
            self._log_status_change(
                task_id, 
                old_status, 
                'pending', 
                'system', 
                f'Retry attempt {task.retry_count} of {task.max_retries}'
            )
            self.logger.info(f"Task {task_id} queued for retry (attempt {task.retry_count})")
        except Exception as e:
            self.logger.error(f"Failed to log status change for task {task_id}: {str(e)}")
        
        return task
    
    def cancel_task(self, task_id: str) -> Task:
        """Cancel a pending or in-progress task"""
        task = Task.find_by_id(task_id, current_app.db)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        if task.status not in ['pending', 'in_progress']:
            raise ValueError("Only pending or in-progress tasks can be cancelled")
        
        old_status = task.status
        task.status = 'cancelled'
        task.current_step = 'Task cancelled by user'
        task.updated_at = datetime.utcnow()
        
        # Save task updates
        if not task.save(current_app.db):
            self.logger.error(f"Failed to save task {task_id} cancellation")
            return None
        
        # Log status change
        try:
            self._log_status_change(task_id, old_status, 'cancelled', 'system', 'Task cancelled by user')
            self.logger.info(f"Task {task_id} cancelled")
        except Exception as e:
            self.logger.error(f"Failed to log status change for task {task_id}: {str(e)}")
        
        return task
    
    def get_ready_tasks(self, session_id: str) -> List[Task]:
        """Get tasks that are ready to be executed (dependencies satisfied)"""
        pending_tasks = Task.find_by_session_and_status(session_id, 'pending', current_app.db)
        return [task for task in pending_tasks if self._dependencies_satisfied(task)]
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        return Task.find_by_id(task_id, current_app.db)
    
    def get_session_tasks(self, session_id: str) -> List[Task]:
        """Get all tasks for a session"""
        return Task.find_by_session(session_id, current_app.db)
    
    def _dependencies_satisfied(self, task: Task) -> bool:
        """Check if all task dependencies are completed"""
        if not task.depends_on:
            return True
        
        for dep_id in task.depends_on:
            dep_task = Task.find_by_id(dep_id, current_app.db)
            if not dep_task or dep_task.status != 'completed':
                return False
        
        return True
    
    def _check_dependent_tasks(self, completed_task_id: str):
        """Check if any tasks can now start due to this completion"""
        dependent_tasks = Task.find_dependent_tasks(completed_task_id, current_app.db)
        
        for task in dependent_tasks:
            if task.status == 'pending' and self._dependencies_satisfied(task):
                self.logger.info(f"Task {task._id} is now ready to start")
                # Could trigger task execution here if using Celery
    
    def _log_status_change(self, task_id: str, old_status: str, new_status: str, 
                          changed_by: str, reason: str = None):
        """Log task status changes for audit trail"""
        try:
            log_entry = TaskStatusLog(
                task_id=task_id,
                old_status=old_status,
                new_status=new_status,
                changed_by=changed_by,
                change_reason=reason,
                timestamp=datetime.utcnow()
            )
            if not log_entry.save(current_app.db):
                self.logger.error(f"Failed to save status log for task {task_id}")
        except Exception as e:
            self.logger.error(f"Error logging status change for task {task_id}: {str(e)}")
    
    def get_stale_tasks(self, hours: int = 24) -> List[Task]:
        """Get tasks that haven't been updated in the specified hours"""
        stale_threshold = datetime.utcnow() - timedelta(hours=hours)
        return Task.find_stale_tasks(stale_threshold, current_app.db) 