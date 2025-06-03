from flask import Blueprint, jsonify, request, current_app
from app.services.status_service import StatusService
from app.services.task_service import TaskService
from app.api.utils import handle_errors, validate_request
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)
tasks_bp = Blueprint('tasks', __name__, url_prefix='/tasks')
status_service = StatusService()
task_service = TaskService()

@tasks_bp.route('/dashboard', methods=['GET'])
@handle_errors
def get_dashboard():
    """Get dashboard overview of all active sessions"""
    # TODO: Implement multi-session dashboard
    sessions = []  # Get active sessions from database
    dashboard_data = []
    
    for session in sessions:
        try:
            session_status = status_service.get_session_dashboard(str(session._id))
            dashboard_data.append(session_status)
        except Exception as e:
            logger.error(f"Error getting status for session {session._id}: {str(e)}")
            continue
    
    return jsonify({
        'sessions': dashboard_data,
        'total_sessions': len(sessions),
        'active_sessions': len([s for s in dashboard_data if s['overall_status'] != 'completed'])
    })

@tasks_bp.route('/<session_id>/status', methods=['GET'])
@handle_errors
def get_session_tasks(session_id: str):
    """Get all tasks for a research session"""
    try:
        tasks = task_service.get_session_tasks(session_id)
        task_breakdown = {
            'pending': [],
            'in_progress': [],
            'completed': [],
            'failed': [],
            'cancelled': []
        }
        
        for task in tasks:
            task_dict = task.to_dict()
            status = task.status if task.status in task_breakdown else 'pending'
            task_breakdown[status].append(task_dict)
        
        return jsonify({
            'session_id': session_id,
            'task_breakdown': task_breakdown,
            'total_tasks': len(tasks),
            'completed_tasks': len(task_breakdown['completed'])
        })
    except Exception as e:
        logger.error(f"Error getting tasks for session {session_id}: {str(e)}")
        return jsonify({'error': str(e)}), 404

@tasks_bp.route('/<task_id>', methods=['GET'])
@handle_errors
def get_task_details(task_id: str):
    """Get detailed information about a specific task"""
    try:
        task = task_service.get_task(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        return jsonify(task.to_dict())
    except Exception as e:
        logger.error(f"Error getting task {task_id}: {str(e)}")
        return jsonify({'error': str(e)}), 404

@tasks_bp.route('/<task_id>/update', methods=['PUT'])
@handle_errors
@validate_request(['status'])
def update_task_status(task_id: str):
    """Update task status"""
    try:
        # First check if task exists
        task = task_service.get_task(task_id)
        if not task:
            return jsonify({'error': f'Task {task_id} not found'}), 404
        
        data = request.get_json()
        
        # Validate status value
        valid_statuses = [
            'pending', 'in_progress', 'completed', 'failed',
            'waiting_user', 'cancelled', 'stale'
        ]
        if data['status'] not in valid_statuses:
            return jsonify({
                'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            }), 400
        
        # Attempt to update task
        updated_task = task_service.update_task_status(
            task_id,
            data['status'],
            progress=data.get('progress'),
            current_step=data.get('current_step'),
            error_message=data.get('error_message')
        )
        
        if not updated_task:
            return jsonify({'error': 'Failed to update task status'}), 500
            
        return jsonify({
            'message': 'Task status updated successfully',
            'task': updated_task.to_dict()
        })
    except ValueError as e:
        logger.error(f"Error updating task {task_id}: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error updating task {task_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@tasks_bp.route('/<task_id>/retry', methods=['POST'])
@handle_errors
def retry_task(task_id: str):
    """Retry a failed task"""
    try:
        # First check if task exists
        task = task_service.get_task(task_id)
        if not task:
            return jsonify({'error': f'Task {task_id} not found'}), 404
        
        # Validate task can be retried
        if task.status != 'failed':
            return jsonify({'error': 'Only failed tasks can be retried'}), 400
            
        if task.retry_count >= task.max_retries:
            return jsonify({'error': 'Maximum retry attempts exceeded'}), 400
        
        # Attempt to retry task
        updated_task = task_service.retry_task(task_id)
        if not updated_task:
            return jsonify({'error': 'Failed to retry task'}), 500
            
        return jsonify({
            'message': f'Task queued for retry (attempt {updated_task.retry_count} of {updated_task.max_retries})',
            'task': updated_task.to_dict()
        })
    except ValueError as e:
        logger.error(f"Error retrying task {task_id}: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error retrying task {task_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@tasks_bp.route('/<task_id>/cancel', methods=['POST'])
@handle_errors
def cancel_task(task_id: str):
    """Cancel a pending or in-progress task"""
    try:
        # First check if task exists
        task = task_service.get_task(task_id)
        if not task:
            return jsonify({'error': f'Task {task_id} not found'}), 404
        
        # Validate task can be cancelled
        if task.status not in ['pending', 'in_progress']:
            return jsonify({'error': 'Only pending or in-progress tasks can be cancelled'}), 400
        
        # Attempt to cancel task
        updated_task = task_service.cancel_task(task_id)
        if not updated_task:
            return jsonify({'error': 'Failed to cancel task'}), 500
            
        return jsonify({
            'message': 'Task cancelled successfully',
            'task': updated_task.to_dict()
        })
    except ValueError as e:
        logger.error(f"Error cancelling task {task_id}: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error cancelling task {task_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@tasks_bp.route('/<task_id>/fail', methods=['POST'])
@handle_errors
@validate_request(['error_message'])
def fail_task(task_id: str):
    """Mark task as failed"""
    try:
        # First check if task exists
        task = task_service.get_task(task_id)
        if not task:
            return jsonify({'error': f'Task {task_id} not found'}), 404
        
        # Attempt to mark task as failed
        data = request.get_json()
        updated_task = task_service.fail_task(task_id, data['error_message'])
        if not updated_task:
            return jsonify({'error': 'Failed to mark task as failed'}), 500
            
        return jsonify({
            'message': 'Task marked as failed',
            'task': updated_task.to_dict()
        })
    except ValueError as e:
        logger.error(f"Error failing task {task_id}: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error failing task {task_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@tasks_bp.route('/stale', methods=['GET'])
@handle_errors
def get_stale_tasks():
    """Get list of stale tasks"""
    try:
        hours = request.args.get('hours', default=24, type=int)
        stale_tasks = task_service.get_stale_tasks(hours)
        
        return jsonify({
            'stale_tasks': [task.to_dict() for task in stale_tasks],
            'count': len(stale_tasks),
            'threshold_hours': hours
        })
    except Exception as e:
        logger.error(f"Error getting stale tasks: {str(e)}")
        return jsonify({'error': str(e)}), 500 