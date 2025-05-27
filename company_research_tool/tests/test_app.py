def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {'status': 'healthy'}

def test_config_loading(app):
    """Test that configuration is loaded correctly."""
    assert app.config['TESTING'] is True
    assert app.config['DEBUG'] is True
    assert 'mongodb://localhost:27017/company_research_test' in app.config['MONGODB_URI'] 