"""
Research endpoints for managing research sessions and retrieving results.
"""

from flask import Blueprint, request, jsonify, current_app
from app.services.research_service import ResearchService
from app.api.utils import validate_request, handle_errors

research_bp = Blueprint('research', __name__)

@research_bp.route('/start', methods=['POST'])
@validate_request(['company_name', 'research_type'])
@handle_errors
def start_research():
    """
    Start a new company research session
    Expected JSON: {
        "company_name": "TechCorp Inc",
        "research_type": "general|sales_lead|job_application",
        "target_person": "optional",
        "additional_context": "optional"
    }
    """
    data = request.get_json()
    
    research_service = ResearchService(current_app.db)
    session = research_service.start_research(
        company_name=data['company_name'],
        research_type=data['research_type'],
        target_person=data.get('target_person'),
        context=data.get('additional_context')
    )
    
    return jsonify({
        'session_id': str(session._id),
        'status': session.status,
        'message': 'Research session started successfully'
    }), 201

@research_bp.route('/<session_id>/status', methods=['GET'])
@handle_errors
def get_research_status(session_id):
    """Get current status of research session"""
    research_service = ResearchService(current_app.db)
    status = research_service.get_session_status(session_id)
    
    return jsonify(status)

@research_bp.route('/<session_id>/results', methods=['GET'])
@handle_errors
def get_research_results(session_id):
    """Get results from completed research session"""
    research_service = ResearchService(current_app.db)
    results = research_service.get_session_results(session_id)
    
    return jsonify(results) 