import pytest
from bs4 import BeautifulSoup

def get_rows(response):
    soup = BeautifulSoup(response.data, 'html.parser')
    return soup.find_all('tr')[1:]

def test_filter_by_region(client):
    response = client.get('/?region=Southend-on-Sea')
    assert response.status_code == 200
    rows = get_rows(response)
    
    for row in rows:
        cols = row.find_all('td')
        if len(cols) > 0:
            assert cols[0].get_text(strip=True) == "Southend-on-Sea"

def test_combined_filters(client):
    response = client.get('/?region=Southend-on-Sea&category=Antiepileptics')
    assert response.status_code == 200
    rows = get_rows(response)
    
    for row in rows:
        cols = row.find_all('td')
        if len(cols) > 0:
            assert cols[0].get_text(strip=True) == "Southend-on-Sea"
            assert cols[3].get_text(strip=True) == "Antiepileptics"

def test_sorting_logic(client):
    response = client.get('/?sort=price_per_unit&direction=desc')
    assert response.status_code == 200
    rows = get_rows(response)
    
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
