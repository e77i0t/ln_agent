"""
Main API routes and blueprint registration.
"""

from flask import Blueprint
from app.api.research import research_bp
from app.api.companies import companies_bp

api_bp = Blueprint('api', __name__)

# Register sub-blueprints
api_bp.register_blueprint(research_bp, url_prefix='/research')
api_bp.register_blueprint(companies_bp, url_prefix='/companies')

@api_bp.route('/health')
def health_check():
    """API health check endpoint"""
    return {'status': 'healthy', 'message': 'API is running'} 