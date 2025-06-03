"""
Research service for managing research sessions and tasks.
"""

from app.database.models import ResearchSession, Task, Company, ResearchType, SessionStatus, TaskType, TaskStatus
from app.scrapers.company_website_scraper import CompanyWebsiteScraper
from datetime import datetime
from bson import ObjectId
from app.utils.logger import setup_logger
from typing import List, Dict, Any

logger = setup_logger(__name__)

class ResearchService:
    # Map common research type inputs to valid ResearchType values
    RESEARCH_TYPE_MAPPING = {
        'general': ResearchType.COMPANY_PROFILE,
        'company_profile': ResearchType.COMPANY_PROFILE,
        'market': ResearchType.MARKET_ANALYSIS,
        'market_analysis': ResearchType.MARKET_ANALYSIS,
        'competitor': ResearchType.COMPETITOR_ANALYSIS,
        'competitor_analysis': ResearchType.COMPETITOR_ANALYSIS,
        'custom': ResearchType.CUSTOM
    }

    def __init__(self, db_manager):
        self.db = db_manager
        self.scraper = CompanyWebsiteScraper()
    
    def start_research(self, company_name: str, research_type: str, 
                      target_person: str = None, context: str = None):
        """Start a new research session"""
        logger.info(f"Starting research for company: {company_name}, type: {research_type}")
        
        # Map the research type to a valid value
        mapped_research_type = self.RESEARCH_TYPE_MAPPING.get(research_type.lower())
        if not mapped_research_type:
            valid_types = list(self.RESEARCH_TYPE_MAPPING.keys())
            logger.error(f"Invalid research type: {research_type}. Valid types are: {', '.join(valid_types)}")
            raise ValueError(f"Invalid research type. Valid types are: {', '.join(valid_types)}")

        # First, find or create the company
        company = Company.find_by_name(company_name, self.db)
        if not company:
            logger.info(f"Company {company_name} not found, creating new entry")
            # Create a new company if it doesn't exist
            company = Company(
                name=company_name,
                domain=self._extract_domain(company_name),  # You might want to improve this
                status='pending_research'
            )
            if not company.save(self.db):
                logger.error(f"Failed to save company: {company_name}")
                raise ValueError("Failed to save company")
            logger.info(f"Created new company with ID: {company._id}")
        
        # Create the research session
        session = ResearchSession(
            research_type=mapped_research_type,
            target_company_id=company._id,
            status=SessionStatus.PLANNED,
            created_at=datetime.utcnow()
        )
        if not session.save(self.db):
            logger.error("Failed to save research session")
            raise ValueError("Failed to save research session")
        logger.info(f"Created research session with ID: {session._id}")
        
        # Create initial research tasks
        self._create_research_tasks(session)
        
        return session
    
    def _extract_domain(self, company_name: str) -> str:
        """Extract a potential domain from company name (temporary solution)"""
        # Remove common company suffixes and spaces
        name = company_name.lower()
        for suffix in [' inc', ' corp', ' llc', ' ltd']:
            name = name.replace(suffix, '')
        # Convert spaces to dashes and add .com
        return f"{name.replace(' ', '-')}.com"
    
    def _create_research_tasks(self, session):
        """Create appropriate tasks based on research type"""
        logger.info(f"Creating tasks for session {session._id}")
        base_tasks = [
            {'task_type': TaskType.DATA_COLLECTION, 'title': 'Scrape company website'},
            {'task_type': TaskType.DATA_COLLECTION, 'title': 'Get official company data'},
            {'task_type': TaskType.ANALYSIS, 'title': 'Extract company metadata'},
        ]
        
        if session.research_type == ResearchType.COMPANY_PROFILE:
            base_tasks.extend([
                {'task_type': TaskType.DATA_COLLECTION, 'title': 'Find key contacts'},
                {'task_type': TaskType.ANALYSIS, 'title': 'Analyze company profile'}
            ])
        elif session.research_type == ResearchType.MARKET_ANALYSIS:
            base_tasks.extend([
                {'task_type': TaskType.RESEARCH, 'title': 'Research market size and trends'},
                {'task_type': TaskType.ANALYSIS, 'title': 'Map key competitors'}
            ])
        elif session.research_type == ResearchType.COMPETITOR_ANALYSIS:
            base_tasks.extend([
                {'task_type': TaskType.RESEARCH, 'title': 'Identify main competitors'},
                {'task_type': TaskType.ANALYSIS, 'title': 'Analyze competitor strengths and weaknesses'}
            ])
        
        created_tasks = []
        for task_data in base_tasks:
            try:
                task = Task(
                    session_id=session._id,
                    task_type=task_data['task_type'],
                    title=task_data['title'],
                    description=task_data.get('description', ''),
                    status=TaskStatus.PENDING,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                if task.save(self.db):
                    logger.info(f"Created task: {task.title} with ID: {task._id}")
                    session.add_task(task._id)
                    # Save session after each task to ensure task_ids are persisted
                    if session.save(self.db):
                        created_tasks.append(task)
                        logger.info(f"Updated session {session._id} with task {task._id}")
                    else:
                        logger.error(f"Failed to update session with task: {task._id}")
                        task.delete(self.db)  # Rollback task creation
                else:
                    logger.error(f"Failed to save task: {task_data['title']}")
            except Exception as e:
                logger.error(f"Error creating task '{task_data['title']}': {str(e)}")
        
        if created_tasks:
            logger.info(f"Created {len(created_tasks)} tasks for session {session._id}")
        else:
            logger.error("No tasks were created for the session")
    
    def get_session_status(self, session_id: str):
        """Get comprehensive session status"""
        logger.info(f"Getting status for session: {session_id}")
        try:
            session = ResearchSession.find_by_id(session_id, self.db)
            if not session:
                logger.error(f"Session not found: {session_id}")
                raise ValueError(f"Session not found: {session_id}")
            
            tasks = Task.find_by_session(session_id, self.db)
            logger.info(f"Found {len(tasks)} tasks for session {session_id}")
            
            # Get company information
            company = Company.find_by_id(str(session.target_company_id), self.db)
            if not company:
                logger.warning(f"Company not found for session {session_id}")
            
            # Calculate task statistics
            task_stats = self._calculate_task_stats(tasks)
            
            return {
                'session_id': session_id,
                'status': session.status,
                'research_type': session.research_type,
                'company': {
                    'id': str(company._id) if company else None,
                    'name': company.name if company else None,
                    'domain': company.domain if company else None
                },
                'created_at': session.created_at.isoformat(),
                'updated_at': session.updated_at.isoformat(),
                'tasks': [task.to_dict() for task in tasks],
                'task_stats': task_stats,
                'progress': self._calculate_progress(tasks)
            }
        except ValueError as e:
            logger.error(f"Error getting session status: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting session status: {str(e)}")
            raise ValueError(f"Error retrieving session status: {str(e)}")
    
    def _calculate_task_stats(self, tasks: List[Task]) -> Dict[str, Any]:
        """Calculate task statistics"""
        stats = {
            'total': len(tasks),
            'by_status': {
                'pending': 0,
                'in_progress': 0,
                'completed': 0,
                'failed': 0,
                'cancelled': 0,
                'stale': 0
            },
            'completion_rate': 0
        }
        
        for task in tasks:
            stats['by_status'][task.status] = stats['by_status'].get(task.status, 0) + 1
        
        if stats['total'] > 0:
            stats['completion_rate'] = (stats['by_status']['completed'] / stats['total']) * 100
        
        return stats
    
    def _calculate_progress(self, tasks: List[Task]) -> Dict[str, Any]:
        """Calculate overall session progress"""
        if not tasks:
            return {
                'percentage': 0,
                'completed_tasks': 0,
                'total_tasks': 0,
                'status': 'no_tasks'
            }
        
        completed = sum(1 for t in tasks if t.status == 'completed')
        failed = sum(1 for t in tasks if t.status == 'failed')
        in_progress = sum(1 for t in tasks if t.status == 'in_progress')
        
        total = len(tasks)
        percentage = (completed / total) * 100 if total > 0 else 0
        
        status = 'completed' if completed == total else \
                 'failed' if failed > 0 else \
                 'in_progress' if in_progress > 0 else 'pending'
        
        return {
            'percentage': percentage,
            'completed_tasks': completed,
            'total_tasks': total,
            'status': status
        }
    
    def get_session_results(self, session_id: str):
        """Get results from completed research session"""
        logger.info(f"Getting results for session: {session_id}")
        session = ResearchSession.find_by_id(session_id, self.db)
        if not session:
            logger.error(f"Session not found: {session_id}")
            raise ValueError("Session not found")
        
        if session.status != SessionStatus.COMPLETED:
            logger.info(f"Session {session_id} is still in progress")
            return {
                'session_id': session_id,
                'status': session.status,
                'message': 'Research is still in progress'
            }
        
        tasks = Task.find_by_session(session_id, self.db)
        company = Company.find_by_id(str(session.target_company_id), self.db)
        
        results = {
            'session_id': session_id,
            'status': session.status,
            'research_type': session.research_type,
            'company': {
                'id': str(company._id),
                'name': company.name,
                'domain': company.domain
            } if company else None,
            'created_at': session.created_at.isoformat(),
            'completed_at': session.completed_at.isoformat() if session.completed_at else None,
            'tasks': [task.to_dict() for task in tasks],
            'findings': session.findings
        }
        
        return results 