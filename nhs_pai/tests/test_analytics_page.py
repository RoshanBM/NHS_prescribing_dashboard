import pytest
from bs4 import BeautifulSoup

def test_analytics_status(client):
    response = client.get('/analytics')
    assert response.status_code == 200

def test_analytics_json_data(client):
    response = client.get('/analytics')
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, 'html.parser')
    scripts = soup.find_all('script')
    practice_found = False
    price_found = False
    for script in scripts:
        if script.string:
            if 'var practiceGraph =' in script.string:
                practice_found = True
            if 'var priceGraph =' in script.string:
                price_found = True
    assert practice_found
    assert price_found