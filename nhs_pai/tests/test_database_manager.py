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
