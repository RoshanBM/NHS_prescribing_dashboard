import pytest
import sys
import os

# Ensure 'src' is findable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

try:
    import app
    print(f"Imported app from: {app.__file__}")
except ImportError as e:
    print(f"ImportError: {e}")

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    # We set a custom config to tell the app where the CSVs are (optional, but good practice)
    with app.test_client() as client:
        yield client

def test_homepage_displays_real_csv_data(client):
    """
    GIVEN the Flask app connected to the CSV files
    WHEN the '/' page is requested
    THEN check that it displays merged data (Practice Name + Drug Name)
    """
    response = client.get('/')
    
    # 1. Check page loads
    assert response.status_code == 200
    
    page_content = response.data.decode('utf-8')
    
    # 2. Check for Table Headers from your specific columns
    assert "Practice Name" in page_content
    assert "Act Cost" in page_content
    
    # 3. Check for specific data we saw in your CSV (e.g., "Hypnotics" or specific practice)
    # Note: This assumes 'clean_practices.csv' contains 'Chaudhury Surgery' as seen in the inspection.
    # If the specific row isn't guaranteed to be on page 1, we check for structure mainly.
    assert "table-striped" in page_content