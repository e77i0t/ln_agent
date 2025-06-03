import pytest
from datetime import datetime, timedelta
from app.services.task_service import TaskService
from app.services.status_service import StatusService
from app.database.models import Task, TaskStatusLog, ResearchSession

@pytest.fixture
def task_service():
    return TaskService()

@pytest.fixture
def status_service():
    return StatusService()

@pytest.fixture
def sample_session():
    session = ResearchSession(
        target_company='Test Company',
        research_type='general'
    )
    session.save()
    return session

def test_create_task(task_service, sample_session):
    """Test task creation"""
    task = task_service.create_task(
        session_id=str(sample_session._id),
        task_type='website_scrape',
        title='Scrape company website',
        description='Extract information from company website'
    )
    
    assert task is not None
    assert task.status == 'pending'
    assert task.progress_percentage == 0
    assert task.session_id == str(sample_session._id)
    assert task.created_at is not None
    assert task.updated_at is not None

def test_task_status_updates(task_service, sample_session):
    """Test task status lifecycle"""
    task = task_service.create_task(
        session_id=str(sample_session._id),
        task_type='website_scrape',
        title='Scrape company website'
    )
    
    # Test in_progress update
    updated_task = task_service.update_task_status(
        str(task._id),
        'in_progress',
        progress=25,
        current_step='Downloading webpage'
    )
    assert updated_task.status == 'in_progress'
    assert updated_task.progress_percentage == 25
    assert updated_task.current_step == 'Downloading webpage'
    assert updated_task.started_at is not None
    
    # Test completion
    result_data = {'url': 'http://example.com', 'content': 'Sample data'}
    completed_task = task_service.complete_task(str(task._id), result_data)
    assert completed_task.status == 'completed'
    assert completed_task.progress_percentage == 100
    assert completed_task.completed_at is not None
    assert completed_task.result_data == result_data

def test_task_failure_handling(task_service, sample_session):
    """Test task failure scenarios"""
    task = task_service.create_task(
        session_id=str(sample_session._id),
        task_type='website_scrape',
        title='Scrape company website'
    )
    
    # Test failure
    error_msg = 'Connection timeout'
    failed_task = task_service.fail_task(str(task._id), error_msg)
    assert failed_task.status == 'failed'
    assert failed_task.error_message == error_msg
    assert failed_task.completed_at is None

def test_task_dependencies(task_service, sample_session):
    """Test task dependency management"""
    # Create parent task
    parent_task = task_service.create_task(
        session_id=str(sample_session._id),
        task_type='website_scrape',
        title='Scrape company website'
    )
    
    # Create dependent task
    dependent_task = task_service.create_task(
        session_id=str(sample_session._id),
        task_type='contact_discovery',
        title='Discover contacts',
        depends_on=[str(parent_task._id)]
    )
    
    # Check dependency
    assert not task_service._dependencies_satisfied(dependent_task)
    
    # Complete parent task
    task_service.complete_task(str(parent_task._id), {'status': 'success'})
    
    # Check dependency again
    assert task_service._dependencies_satisfied(dependent_task)

def test_stale_task_detection(task_service, sample_session):
    """Test stale task detection"""
    # Create a task with old timestamp
    task = task_service.create_task(
        session_id=str(sample_session._id),
        task_type='website_scrape',
        title='Scrape company website'
    )
    
    # Manually update timestamp to simulate old task
    task.updated_at = datetime.utcnow() - timedelta(hours=25)
    task.save()
    
    # Check stale tasks
    stale_tasks = task_service.get_stale_tasks(hours=24)
    assert len(stale_tasks) > 0
    assert str(task._id) in [str(t._id) for t in stale_tasks]

def test_session_dashboard(status_service, task_service, sample_session):
    """Test session dashboard data"""
    # Create multiple tasks in different states
    tasks = [
        ('website_scrape', 'Scrape website', 'completed'),
        ('contact_discovery', 'Find contacts', 'in_progress'),
        ('data_analysis', 'Analyze data', 'pending'),
        ('report_generation', 'Generate report', 'failed')
    ]
    
    for task_type, title, status in tasks:
        task = task_service.create_task(
            session_id=str(sample_session._id),
            task_type=task_type,
            title=title
        )
        if status != 'pending':
            task_service.update_task_status(str(task._id), status)
    
    # Get dashboard data
    dashboard = status_service.get_session_dashboard(str(sample_session._id))
    
    assert dashboard['overall_status'] == 'has_failures'
    assert dashboard['progress']['total_tasks'] == len(tasks)
    assert dashboard['progress']['completed_tasks'] == 1
    assert len(dashboard['task_breakdown']['completed']) == 1
    assert len(dashboard['task_breakdown']['in_progress']) == 1
    assert len(dashboard['task_breakdown']['failed']) == 1
    assert len(dashboard['task_breakdown']['pending']) == 1

def test_task_retry(task_service, sample_session):
    """Test task retry functionality"""
    # Create and fail a task
    task = task_service.create_task(
        session_id=str(sample_session._id),
        task_type='website_scrape',
        title='Scrape company website'
    )
    
    task_service.fail_task(str(task._id), 'Initial failure')
    
    # Update retry count and try again
    task.retry_count = 1
    task.save()
    
    # Should be able to retry
    updated_task = task_service.update_task_status(
        str(task._id),
        'pending',
        progress=0,
        current_step='Task queued for retry'
    )
    
    assert updated_task.status == 'pending'
    assert updated_task.error_message is None
    assert updated_task.retry_count == 1
    
    # Fail again but exceed max retries
    task_service.fail_task(str(task._id), 'Second failure')
    task.retry_count = task.max_retries
    task.save()
    
    # Should not be able to retry
    with pytest.raises(ValueError):
        task_service.update_task_status(
            str(task._id),
            'pending',
            progress=0,
            current_step='Task queued for retry'
        ) 