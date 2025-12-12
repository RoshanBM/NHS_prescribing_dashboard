import pytest
import sys
import os
import io
import csv


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_export_filtered_data_as_csv(client):
   
   
    region_filter = "Southend-on-Sea"
    response = client.get(f'/export?region={region_filter}')
   
    assert response.status_code == 200
    assert "text/csv" in response.content_type
    assert "attachment" in response.headers["Content-Disposition"]
    
   
    csv_content = response.data.decode('utf-8')
    csv_reader = csv.reader(io.StringIO(csv_content))
    headers = next(csv_reader)
  
    assert "practice_name" in headers
    assert "cost" in headers
    
 
    first_row = next(csv_reader)

    region_idx = headers.index('region')
    assert region_filter in first_row[region_idx]