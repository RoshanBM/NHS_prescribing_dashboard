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
    """
    Fixture to setup a test client with a temporary database.
    Patches get_db_manager to use the test database.
    """
    app.config['TESTING'] = True
    
    # Use patch context manager for cleaner mocking
    with patch('app.get_db_manager') as mock_get_db:
        def mock_manager_factory():
            manager = DatabaseManager(TEST_DB)
            manager.create_tables()
            return manager
        
        mock_get_db.side_effect = mock_manager_factory
        
        with app.test_client() as client:
            yield client
            
    # Cleanup
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except PermissionError:
            pass

def test_empty_required_field(client):
    """
    Test submitting a form with an empty required field (Practice Name).
    Should return an error message.
    """
    response = client.post('/edit_database/add_practice', data={
        'practice_code': 'VALID01',
        'practice_name': '',
        'postcode': 'SW1A 1AA'
    }, follow_redirects=True)
    
    assert b'Practice name is required' in response.data

def test_duplicate_primary_key(client):
    """
    Test adding a record with a duplicate Primary Key.
    Should return a specific error message and not crash.
    """
    # Add initial record
    client.post('/edit_database/add_practice', data={
        'practice_code': 'DUP001',
        'practice_name': 'Original',
        'postcode': 'SW1A 1AA'
    })
    
    # Attempt to add duplicate
    response = client.post('/edit_database/add_practice', data={
        'practice_code': 'DUP001',
        'practice_name': 'Duplicate',
        'postcode': 'SW1A 1AA'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Error adding practice. Code may already exist.' in response.data

def test_empty_dashboard(client):
    """
    Test the dashboard behavior when data files are missing (simulating empty DB/Data).
    Should display a 'No results' message instead of crashing.
    """
    with patch('pandas.read_csv') as mock_read_csv:
        mock_read_csv.side_effect = FileNotFoundError
        response = client.get('/')
        assert response.status_code == 200
        assert b'No results found matching your filters.' in response.data

def test_filter_no_results(client):
    """
    Test filtering with a term that yields no results.
    Should display a 'No results' message.
    """
    response = client.get('/?drug_name=NonExistentDrug')
    assert b'No results found matching your filters.' in response.data
