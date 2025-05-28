from typing import Dict, Any, List, Optional
from datetime import datetime
from bson import ObjectId
from ..base import BaseDocument

class ResearchType:
    COMPANY_PROFILE = 'company_profile'
    MARKET_ANALYSIS = 'market_analysis'
    COMPETITOR_ANALYSIS = 'competitor_analysis'
    CUSTOM = 'custom'

class SessionStatus:
    PLANNED = 'planned'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    ARCHIVED = 'archived'

class ResearchSession(BaseDocument):
    """Research Session document model"""
    collection_name = 'research_sessions'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.research_type: str = kwargs.get('research_type', ResearchType.COMPANY_PROFILE)
        self.target_company_id: Optional[ObjectId] = kwargs.get('target_company_id')
        if isinstance(self.target_company_id, str):
            self.target_company_id = ObjectId(self.target_company_id)
        self.status: str = kwargs.get('status', SessionStatus.PLANNED)
        self.findings: Dict[str, Any] = kwargs.get('findings', {})
        self.task_ids: List[ObjectId] = []
        for task_id in kwargs.get('task_ids', []):
            if isinstance(task_id, str):
                self.task_ids.append(ObjectId(task_id))
            else:
                self.task_ids.append(task_id)
        self.progress: float = kwargs.get('progress', 0.0)
        self.completed_at: Optional[datetime] = kwargs.get('completed_at')
        
    def validate(self) -> bool:
        """Validate required fields"""
        if not self.target_company_id:
            raise ValueError("Target company ID is required")
        if self.research_type not in vars(ResearchType).values():
            raise ValueError("Invalid research type")
        if self.status not in vars(SessionStatus).values():
            raise ValueError("Invalid session status")
        if not 0 <= self.progress <= 100:
            raise ValueError("Progress must be between 0 and 100")
        return True
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert research session to dictionary"""
        base_dict = super().to_dict()
        session_dict = {
            'research_type': self.research_type,
            'target_company_id': self.target_company_id,
            'status': self.status,
            'findings': self.findings,
            'task_ids': self.task_ids,
            'progress': self.progress,
            'completed_at': self.completed_at
        }
        return {**base_dict, **session_dict}
        
    def add_task(self, task_id: ObjectId):
        """Add a task to the session"""
        if task_id not in self.task_ids:
            self.task_ids.append(task_id)
            
    def complete(self):
        """Mark session as completed"""
        self.status = SessionStatus.COMPLETED
        self.progress = 100.0
        self.completed_at = datetime.utcnow() 