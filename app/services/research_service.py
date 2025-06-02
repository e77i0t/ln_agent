"""
Research service for managing research sessions and tasks.
"""

from app.database.models import ResearchSession, Task
from app.scrapers.company_website_scraper import CompanyWebsiteScraper
from datetime import datetime

class ResearchService:
    def __init__(self, db_manager):
        self.db = db_manager
        self.scraper = CompanyWebsiteScraper()
    
    def start_research(self, company_name: str, research_type: str, 
                      target_person: str = None, context: str = None):
        """Start a new research session"""
        session = ResearchSession(
            research_type=research_type,
            target_company=company_name,
            target_person=target_person,
            status='started',
            created_at=datetime.utcnow()
        )
        session.save()
        
        # Create initial research tasks
        self._create_research_tasks(session)
        
        return session
    
    def _create_research_tasks(self, session):
        """Create appropriate tasks based on research type"""
        base_tasks = [
            {'type': 'website_scraping', 'title': 'Scrape company website'},
            {'type': 'opencorporates_lookup', 'title': 'Get official company data'},
            {'type': 'company_info', 'title': 'Extract company metadata'},
        ]
        
        if session.research_type == 'sales_lead':
            base_tasks.append({'type': 'contact_discovery', 'title': 'Find key contacts'})
        elif session.research_type == 'job_application':
            base_tasks.append({'type': 'job_analysis', 'title': 'Analyze job opportunities'})
        
        for task_data in base_tasks:
            task = Task(
                session_id=session._id,
                task_type=task_data['type'],
                title=task_data['title'],
                status='pending',
                created_at=datetime.utcnow()
            )
            task.save()
    
    def get_session_status(self, session_id: str):
        """Get comprehensive session status"""
        session = ResearchSession.find_by_id(session_id)
        if not session:
            raise ValueError("Session not found")
        
        tasks = Task.find_by_session(session_id)
        
        return {
            'session_id': session_id,
            'status': session.status,
            'research_type': session.research_type,
            'target_company': session.target_company,
            'created_at': session.created_at.isoformat(),
            'tasks': [task.to_dict() for task in tasks],
            'progress': self._calculate_progress(tasks)
        }
    
    def get_session_results(self, session_id: str):
        """Get results from completed research session"""
        session = ResearchSession.find_by_id(session_id)
        if not session:
            raise ValueError("Session not found")
        
        if session.status != 'completed':
            return {
                'session_id': session_id,
                'status': session.status,
                'message': 'Research is still in progress'
            }
        
        tasks = Task.find_by_session(session_id)
        results = {
            'session_id': session_id,
            'status': session.status,
            'research_type': session.research_type,
            'target_company': session.target_company,
            'created_at': session.created_at.isoformat(),
            'completed_at': session.completed_at.isoformat() if session.completed_at else None,
            'tasks': [task.to_dict() for task in tasks],
            'findings': session.findings
        }
        
        return results
    
    def _calculate_progress(self, tasks):
        """Calculate overall progress percentage"""
        if not tasks:
            return 0
        
        completed = sum(1 for task in tasks if task.status == 'completed')
        return int((completed / len(tasks)) * 100) 