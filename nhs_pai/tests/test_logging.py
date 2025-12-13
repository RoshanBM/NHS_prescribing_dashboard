import os

def test_logging_on_homepage_access(client):
    log_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../logs/app.log'))
    
    if os.path.exists(log_path):
        with open(log_path, 'w') as f:
            f.write('')

    client.get('/')
    
    assert os.path.exists(log_path)
    with open(log_path, 'r') as f:
        content = f.read()
        assert "accessed Homepage" in content