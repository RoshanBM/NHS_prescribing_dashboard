import pytest
import sys
import os
import sqlite3

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from app import app
from database_manager import DatabaseManager

# Mock Database Path for Testing
TEST_DB = 'test_nhs_data.db'

@pytest.fixture
def client():
    app.config['TESTING'] = True
    
    # Override get_db_manager to use test DB
    def mock_get_db_manager():
        manager = DatabaseManager(TEST_DB)
        manager.create_tables()
        return manager
        
    # Patch the get_db_manager in app module
    import app as app_module
    original_get_db_manager = app_module.get_db_manager
    app_module.get_db_manager = mock_get_db_manager
    
    with app.test_client() as client:
        yield client
        
    # Cleanup
    app_module.get_db_manager = original_get_db_manager
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except PermissionError:
            pass

@pytest.fixture
def db_verifier():
    """Fixture to verify database state."""
    manager = DatabaseManager(TEST_DB)
    yield manager
    manager.close_connection()

def test_crud_practice_success(client, db_verifier):
    # 1. Create (POST)
    response = client.post('/edit_database/add_practice', data={
        'practice_code': 'TEST01',
        'practice_name': 'Test Practice',
        'postcode': 'SW1A 1AA'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Practice added successfully!' in response.data
    
    # 2. Read (Verify it exists in DB)
    practice = db_verifier.get_practice('TEST01')
    assert practice is not None
    assert practice[1] == 'Test Practice'

    # 3. Update
    client.post('/edit_database/update_practice', data={
        'practice_code': 'TEST01',
        'practice_name': 'Updated Practice'
    }, follow_redirects=True)
    
    practice = db_verifier.get_practice('TEST01')
    assert practice[1] == 'Updated Practice'

    # 4. Delete
    response = client.get('/edit_database/delete_practice/TEST01', follow_redirects=True)
    assert b'Practice deleted successfully!' in response.data
    
    practice = db_verifier.get_practice('TEST01')
    assert practice is None

def test_crud_drug_success(client, db_verifier):
    # 1. Create Drug
    client.post('/edit_database/add_drug', data={
        'bnf_code': 'TESTDRUG01',
        'drug_name': 'Test Drug'
    }, follow_redirects=True)
    
    # 2. Read (Verify it exists)
    drug = db_verifier.get_drug('TESTDRUG01')
    
    assert drug is not None
    assert drug[1] == 'Test Drug'

def test_crud_prescription_success(client):
    # Setup: Add Practice and Drug first
    client.post('/edit_database/add_practice', data={
        'practice_code': 'P001',
        'practice_name': 'P1',
        'postcode': 'SW1A 1AA'
    })
    client.post('/edit_database/add_drug', data={
        'bnf_code': 'D001',
        'drug_name': 'D1'
    })
    
    # 1. Create Prescription
    client.post('/edit_database/add_prescription', data={
        'practice_code': 'P001',
        'bnf_code': 'D001',
        'items': '10',
        'act_cost': '100.0',
        'quantity': '50.0'
    }, follow_redirects=True)
    
    # 2. Delete Prescription
    response = client.get('/edit_database/delete_prescription/1', follow_redirects=True)
    
    assert b'Prescription deleted successfully!' in response.data
