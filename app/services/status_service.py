from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from app.database.models import Task, ResearchSession
from app.services.task_service import TaskService

class StatusService:
    def __init__(self):
        self.task_service = TaskService()
    
    def get_session_dashboard(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session status for dashboard"""
        session = ResearchSession.find_by_id(session_id)
        if not session:
            raise ValueError("Session not found")
        
        tasks = self.task_service.get_session_tasks(session_id)
        
        # Categorize tasks by status
        task_categories = {
            'waiting_system': [t for t in tasks if t.status == 'in_progress'],
            'waiting_user': [t for t in tasks if t.status == 'waiting_user'],
            'completed': [t for t in tasks if t.status == 'completed'],
            'failed': [t for t in tasks if t.status == 'failed'],
            'pending': [t for t in tasks if t.status == 'pending']
        }
        
        # Calculate progress
        total_tasks = len(tasks)
        completed_tasks = len(task_categories['completed'])
        progress = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
        
        # Identify stale items
        stale_items = self._identify_stale_tasks(tasks)
        
        return {
            'session_id': session_id,
            'target_company': session.target_company,
            'research_type': session.research_type,
            'overall_status': self._calculate_overall_status(task_categories),
            'progress': {
                'completion_percentage': progress,
                'completed_tasks': completed_tasks,
                'total_tasks': total_tasks
            },
            'task_breakdown': {
                'waiting_system': [self._task_summary(t) for t in task_categories['waiting_system']],
                'waiting_user': [self._task_summary(t) for t in task_categories['waiting_user']],
                'completed': [self._task_summary(t) for t in task_categories['completed']],
                'failed': [self._task_summary(t) for t in task_categories['failed']],
                'pending': [self._task_summary(t) for t in task_categories['pending']]
            },
            'stale_items': stale_items,
            'next_actions': self._generate_next_actions(task_categories, stale_items),
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def _identify_stale_tasks(self, tasks: List[Task]) -> List[Dict[str, Any]]:
        """Identify tasks that have been inactive for too long"""
        stale_items = []
        stale_threshold = datetime.utcnow() - timedelta(hours=24)
        
        for task in tasks:
            if task.status in ['pending', 'in_progress'] and task.updated_at < stale_threshold:
                stale_items.append({
                    'task_id': str(task._id),
                    'title': task.title,
                    'status': task.status,
                    'stale_since': task.updated_at.isoformat(),
                    'hours_stale': int((datetime.utcnow() - task.updated_at).total_seconds() / 3600),
                    'recommended_action': self._get_stale_recommendation(task)
                })
        
        return stale_items
    
    def _calculate_overall_status(self, task_categories: Dict[str, List]) -> str:
        """Calculate overall session status"""
        if task_categories['failed']:
            return 'has_failures'
        elif task_categories['waiting_user']:
            return 'waiting_user'
        elif task_categories['waiting_system']:
            return 'in_progress'
        elif task_categories['pending']:
            return 'pending'
        else:
            return 'completed'
    
    def _task_summary(self, task: Task) -> Dict[str, Any]:
        """Create task summary for dashboard"""
        return {
            'task_id': str(task._id),
            'title': task.title,
            'type': task.task_type,
            'status': task.status,
            'progress': task.progress_percentage,
            'current_step': task.current_step,
            'error': task.error_message if task.status == 'failed' else None,
            'created_at': task.created_at.isoformat(),
            'updated_at': task.updated_at.isoformat(),
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'duration': self._calculate_duration(task)
        }
    
    def _calculate_duration(self, task: Task) -> Optional[int]:
        """Calculate task duration in seconds"""
        if task.started_at:
            end_time = task.completed_at or datetime.utcnow()
            return int((end_time - task.started_at).total_seconds())
        return None
    
    def _get_stale_recommendation(self, task: Task) -> str:
        """Get recommendation for handling stale task"""
        if task.status == 'pending':
            return "Review dependencies and initiate task if ready"
        elif task.status == 'in_progress':
            return "Check for system issues or stuck processing"
        elif task.status == 'waiting_user':
            return "Follow up on required user action"
        return "Review task status and take appropriate action"
    
    def _generate_next_actions(self, task_categories: Dict[str, List], 
                             stale_items: List) -> List[str]:
        """Generate recommended next actions"""
        actions = []
        
        if stale_items:
            actions.append(f"Review {len(stale_items)} stale items requiring attention")
        
        if task_categories['waiting_user']:
            actions.append(f"Complete {len(task_categories['waiting_user'])} pending user actions")
        
        if task_categories['failed']:
            actions.append(f"Address {len(task_categories['failed'])} failed tasks")
        
        if not actions and task_categories['waiting_system']:
            actions.append("System is processing tasks - check back soon")
            
        if not actions and not task_categories['completed']:
            actions.append("No tasks in progress - consider starting new tasks")
        
        return actions
    
    def get_task_details(self, task_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific task"""
        task = self.task_service.get_task(task_id)
        if not task:
            raise ValueError("Task not found")
            
        return {
            **self._task_summary(task),
            'description': task.description,
            'dependencies': task.depends_on,
            'result_data': task.result_data if task.status == 'completed' else None,
            'retry_count': task.retry_count,
            'max_retries': task.max_retries
        } 