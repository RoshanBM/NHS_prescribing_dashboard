import pytest
import sqlite3
import os
import sys

# Add parent directory to path to allow imports from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database_manager import DatabaseManager

TEST_DB_NAME = 'test_nhs.db'

@pytest.fixture
def db_manager():
    """Fixture to create a temporary test DB and clean it up afterwards."""
    manager = DatabaseManager(TEST_DB_NAME)
    manager.create_tables()
    
    yield manager
    
    manager.close_connection()
    if os.path.exists(TEST_DB_NAME):
        try:
            os.remove(TEST_DB_NAME)
        except PermissionError:
            pass 

def test_create_tables(db_manager):
    """Test if tables are created successfully."""
    db_manager.create_tables()
    
    # Verify the tables exist in SQLite system logic
    conn = sqlite3.connect(TEST_DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    assert 'practices' in tables
    assert 'drugs' in tables
    assert 'prescriptions' in tables
    conn.close()

def test_insert_practice(db_manager):
    """Test if we can insert a practice record."""
    db_manager.create_tables()
    
    # Test Data
    practice_data = [('P001', 'Test Surgery', 'CV1 5FB')]
    db_manager.insert_practices(practice_data)
    
    # Check if it's actually there
    conn = sqlite3.connect(TEST_DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT practice_name FROM practices WHERE practice_code='P001'")
    result = cursor.fetchone()
    
    assert result is not None
    assert result[0] == 'Test Surgery'
    conn.close()

def test_crud_practice(db_manager):
    """
    Test the full lifecycle of a Practice record:
    1. CREATE a new practice
    2. READ it back to verify
    3. UPDATE its name
    4. DELETE it
    """
    
    # 1. CREATE
    practice_code = "TEST001"
    initial_name = "Test Surgery"
    postcode = "SW1A 1AA"
    
    db_manager.add_practice(practice_code, initial_name, postcode)
    
    # 2. READ
    result = db_manager.get_practice(practice_code)
    assert result is not None
    assert result[1] == initial_name
    assert result[2] == postcode
    
    # 3. UPDATE
    new_name = "Updated Health Centre"
    db_manager.update_practice(practice_code, new_name)
    
    updated_result = db_manager.get_practice(practice_code)
    assert updated_result[1] == new_name
    
    # 4. DELETE
    db_manager.delete_practice(practice_code)
    
    final_result = db_manager.get_practice(practice_code)
    assert final_result is None