"""
API utility functions and decorators for request validation and error handling.
"""

from functools import wraps
from flask import request, jsonify
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

def validate_request(required_fields):
    """Decorator to validate required JSON fields"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                logger.error("Request Content-Type is not application/json")
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            data = request.get_json()
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                logger.error(f"Missing required fields: {', '.join(missing_fields)}")
                return jsonify({
                    'error': 'Missing required fields',
                    'missing_fields': missing_fields
                }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def handle_errors(f):
    """Decorator for consistent error handling"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            error_msg = str(e)
            logger.error(f"Validation error: {error_msg}")
            if "not found" in error_msg.lower():
                return jsonify({'error': error_msg}), 404
            return jsonify({'error': error_msg}), 400
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    return decorated_function 