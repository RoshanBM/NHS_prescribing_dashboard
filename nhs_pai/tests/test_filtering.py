import pytest
import sys
import os
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_filter_by_region(client):
    response = client.get('/?region=Southend-on-Sea')
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, 'html.parser')
    rows = soup.find_all('tr')[1:] 
    
    for row in rows:
        cols = row.find_all('td')
        if len(cols) > 0:
            region_text = cols[0].get_text(strip=True)
            assert region_text == "Southend-on-Sea"

def test_combined_filters(client):
    response = client.get('/?region=Southend-on-Sea&category=Antiepileptics')
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, 'html.parser')
    rows = soup.find_all('tr')[1:]
    
    for row in rows:
        cols = row.find_all('td')
        if len(cols) > 0:
            region_text = cols[0].get_text(strip=True)
            category_text = cols[3].get_text(strip=True)
            assert region_text == "Southend-on-Sea"
            assert category_text == "Antiepileptics"

def test_sorting_logic(client):
    response = client.get('/?sort=price_per_unit&direction=desc')
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, 'html.parser')
    rows = soup.find_all('tr')[1:]
    
    prices = []
    for row in rows:
        cols = row.find_all('td')
        if len(cols) > 5:
            price_text = cols[5].get_text(strip=True).replace('£', '').split()[0]
            try:
                prices.append(float(price_text))
            except ValueError:
                pass
    
    if len(prices) > 1:
        assert prices[0] >= prices[-1]
