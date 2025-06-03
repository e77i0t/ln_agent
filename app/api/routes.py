"""
Main API routes and blueprint registration.
"""

from flask import Blueprint
from app.api.research import research_bp
from app.api.companies import companies_bp
from app.api.tasks import tasks_bp

api_bp = Blueprint('api', __name__)

# Register sub-blueprints
api_bp.register_blueprint(research_bp, url_prefix='/research')
api_bp.register_blueprint(companies_bp, url_prefix='/companies')
api_bp.register_blueprint(tasks_bp)  # No url_prefix needed since it's defined in tasks_bp

@api_bp.route('/health')
def health_check():
    """API health check endpoint"""
    return {'status': 'healthy', 'message': 'API is running'} 