"""
Company-related endpoints for searching and retrieving company information.
"""

from flask import Blueprint, request, jsonify, current_app
from app.database.models import Company
from app.api.utils import handle_errors

companies_bp = Blueprint('companies', __name__)

@companies_bp.route('/search', methods=['GET'])
@handle_errors
def search_companies():
    """Search for companies by name or domain"""
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 20))
    
    companies = Company.search(query, current_app.db, limit=limit)
    
    return jsonify({
        'companies': [company.to_dict() for company in companies],
        'count': len(companies)
    })

@companies_bp.route('/<company_id>', methods=['GET'])
@handle_errors
def get_company(company_id):
    """Get detailed company information"""
    company = Company.find_by_id(company_id, current_app.db)
    if not company:
        return jsonify({'error': 'Company not found'}), 404
    
    return jsonify(company.to_dict()) 