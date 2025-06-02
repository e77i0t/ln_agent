"""
API Blueprint initialization and configuration.
"""

from flask import Blueprint

api_bp = Blueprint('api', __name__)

from . import routes  # noqa: F401 