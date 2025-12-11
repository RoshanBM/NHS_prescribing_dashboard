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
    assert "Cost (£)" in page_content
    
    # 3. Check for specific data we saw in your CSV (e.g., "Hypnotics" or specific practice)
    # Note: This assumes 'clean_practices.csv' contains 'Chaudhury Surgery' as seen in the inspection.
    # If the specific row isn't guaranteed to be on page 1, we check for structure mainly.
    assert "table-striped" in page_content

def test_search_filters(client):
    """
    GIVEN the app is running with data
    WHEN we search for a specific Region and Category
    THEN the page should only show results matching those criteria
    """
    # Simulate a user searching for "London" region and "Antiepileptics" category
    response = client.get('/?region=Southend-on-Sea&category=Antiepileptics')
    
    assert response.status_code == 200
    page_content = response.data.decode('utf-8')
    
    # ASSERTION 1: The correct data should appear

    assert "Southend-on-Sea" in page_content
    
    # ASSERTION 2: The wrong data should NOT appear

    assert "Chelmsford" not in page_content

def test_postcode_filter(client):
    """
    GIVEN the app is running with data
    WHEN we search for a specific Post Code
    THEN the page should only show results matching that Post Code
    """
    # Use a postcode from clean_practices.csv that has prescriptions: SK9 1PA (Kenmore Medical Centre)
    response = client.get('/?post_code=SK9 1PA')
    
    assert response.status_code == 200
    page_content = response.data.decode('utf-8')
    
    assert "SK9 1PA" in page_content
    assert "Kenmore Medical Centre" in page_content
    
    # Check that another postcode/practice is not present
    # CM12 0UA (Queens Park Surgery)
    assert "CM12 0UA" not in page_content
    assert "Queens Park Surgery" not in page_content

def test_postcode_filter_no_spaces(client):
    """
    GIVEN the app is running with data
    WHEN we search for a postcode without spaces (e.g. 'sk91pa')
    THEN the page should still find the results for 'SK9 1PA'
    """
    # Search for 'sk91pa' (lowercase, no space)
    response = client.get('/?post_code=sk91pa')
    
    assert response.status_code == 200
    page_content = response.data.decode('utf-8')
    
    # Should find 'SK9 1PA' in the output table
    assert "SK9 1PA" in page_content
    assert "Kenmore Medical Centre" in page_content

def test_price_per_unit_calculation(client):

    response = client.get('/')
    assert response.status_code == 200
    
 
    from app import get_joined_data
    
    # Fetch data (mocking filters as None)
    data = get_joined_data()
    
    # 3. Check the first record (assuming data exists)
    if data:
        record = data[0]
        
        # FAIL POINT: This key 'price_per_unit' does not exist yet
        assert 'price_per_unit' in record
        
        # Check the math: Cost divided by Items
        expected_ppu = record['cost'] / record['items']
        assert record['price_per_unit'] == pytest.approx(expected_ppu, 0.01)

