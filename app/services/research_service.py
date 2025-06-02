"""
Research service for managing research sessions and tasks.
"""

from app.database.models import ResearchSession, Task, Company, ResearchType, SessionStatus
from app.scrapers.company_website_scraper import CompanyWebsiteScraper
from datetime import datetime
from bson import ObjectId

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
        # Map the research type to a valid value
        mapped_research_type = self.RESEARCH_TYPE_MAPPING.get(research_type.lower())
        if not mapped_research_type:
            valid_types = list(self.RESEARCH_TYPE_MAPPING.keys())
            raise ValueError(f"Invalid research type. Valid types are: {', '.join(valid_types)}")

        # First, find or create the company
        company = Company.find_by_name(company_name, self.db)
        if not company:
            # Create a new company if it doesn't exist
            company = Company(
                name=company_name,
                domain=self._extract_domain(company_name),  # You might want to improve this
                status='pending_research'
            )
            company.save(self.db)
        
        # Create the research session
        session = ResearchSession(
            research_type=mapped_research_type,
            target_company_id=company._id,
            status=SessionStatus.PLANNED,
            created_at=datetime.utcnow()
        )
        session.save(self.db)
        
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
        base_tasks = [
            {'type': 'website_scraping', 'title': 'Scrape company website'},
            {'type': 'opencorporates_lookup', 'title': 'Get official company data'},
            {'type': 'company_info', 'title': 'Extract company metadata'},
        ]
        
        if session.research_type == ResearchType.COMPANY_PROFILE:
            base_tasks.extend([
                {'type': 'contact_discovery', 'title': 'Find key contacts'},
                {'type': 'company_analysis', 'title': 'Analyze company profile'}
            ])
        elif session.research_type == ResearchType.MARKET_ANALYSIS:
            base_tasks.extend([
                {'type': 'market_research', 'title': 'Research market size and trends'},
                {'type': 'competitor_mapping', 'title': 'Map key competitors'}
            ])
        elif session.research_type == ResearchType.COMPETITOR_ANALYSIS:
            base_tasks.extend([
                {'type': 'competitor_discovery', 'title': 'Identify main competitors'},
                {'type': 'competitor_analysis', 'title': 'Analyze competitor strengths and weaknesses'}
            ])
        
        for task_data in base_tasks:
            task = Task(
                session_id=session._id,
                task_type=task_data['type'],
                title=task_data['title'],
                status='pending',
                created_at=datetime.utcnow()
            )
            task.save(self.db)
    
    def get_session_status(self, session_id: str):
        """Get comprehensive session status"""
        session = ResearchSession.find_by_id(session_id, self.db)
        if not session:
            raise ValueError("Session not found")
        
        tasks = Task.find_by_session(session_id, self.db)
        
        # Get company information
        company = Company.find_by_id(session.target_company_id, self.db)
        
        return {
            'session_id': session_id,
            'status': session.status,
            'research_type': session.research_type,
            'company': {
                'id': str(company._id),
                'name': company.name,
                'domain': company.domain
            } if company else None,
            'created_at': session.created_at.isoformat(),
            'tasks': [task.to_dict() for task in tasks],
            'progress': self._calculate_progress(tasks)
        }
    
    def get_session_results(self, session_id: str):
        """Get results from completed research session"""
        session = ResearchSession.find_by_id(session_id, self.db)
        if not session:
            raise ValueError("Session not found")
        
        if session.status != 'completed':
            return {
                'session_id': session_id,
                'status': session.status,
                'message': 'Research is still in progress'
            }
        
        tasks = Task.find_by_session(session_id, self.db)
        company = Company.find_by_id(session.target_company_id, self.db)
        
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
    
    def _calculate_progress(self, tasks):
        """Calculate overall progress percentage"""
        if not tasks:
            return 0
        
        completed = sum(1 for task in tasks if task.status == 'completed')
        return int((completed / len(tasks)) * 100) 