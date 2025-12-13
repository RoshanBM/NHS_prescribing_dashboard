import pytest
import sys
import os
from unittest.mock import patch
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from app import app
from database_manager import DatabaseManager

TEST_DB = 'test_edge_cases.db'

@pytest.fixture
def client():
    app.config['TESTING'] = True
    def mock_get_db_manager():
        manager = DatabaseManager(TEST_DB)
        manager.create_tables()
        return manager
    import app as app_module
    original_get_db_manager = app_module.get_db_manager
    app_module.get_db_manager = mock_get_db_manager
    with app.test_client() as client:
        yield client
    app_module.get_db_manager = original_get_db_manager
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except PermissionError:
            pass

def test_empty_required_field(client):
    response = client.post('/edit_database/add_practice', data={
        'practice_code': 'VALID01',
        'practice_name': '',
        'postcode': 'SW1A 1AA'
    }, follow_redirects=True)
    assert b'Practice name is required' in response.data

def test_duplicate_primary_key(client):
    client.post('/edit_database/add_practice', data={
        'practice_code': 'DUP001',
        'practice_name': 'Original',
        'postcode': 'SW1A 1AA'
    })
    response = client.post('/edit_database/add_practice', data={
        'practice_code': 'DUP001',
        'practice_name': 'Duplicate',
        'postcode': 'SW1A 1AA'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Error adding practice. Code may already exist.' in response.data

def test_empty_dashboard(client):
    with patch('pandas.read_csv') as mock_read_csv:
        mock_read_csv.side_effect = FileNotFoundError
        response = client.get('/')
        assert response.status_code == 200
        assert b'No results found matching your filters.' in response.data

def test_filter_no_results(client):
    response = client.get('/?drug_name=NonExistentDrug')
    assert b'No results found matching your filters.' in response.data
