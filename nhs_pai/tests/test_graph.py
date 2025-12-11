import pytest
import sys
import os
import json
import pandas as pd
from unittest.mock import patch

# Ensure 'src' is findable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from app import get_regional_cost_graph

@patch('app.pd.read_csv')
def test_generate_plotly_data_for_region_costs(mock_read_csv):
    """
    GIVEN the NHS dataset
    WHEN we ask for a graph of 'Hypnotics & Anxiolytics' by Region
    THEN it should return a dictionary suitable for Plotly
    AND the x-axis should be Regions, y-axis should be Average Cost per Item
    """
    
    # --- MOCK DATA SETUP ---

    df_drugs = pd.DataFrame({
        'bnf_code': ['010101', '020202'],
        'category': ['Hypnotics & Anxiolytics', 'Other']
    })
    

    regions = ['Region A', 'Region B', 'Region C', 'Region D', 'Region E', 'Region F']
    practices_data = {
        'PRACTICE_CODE': [f'P00{i}' for i in range(6)],
        'region': regions
    }
    df_practices = pd.DataFrame(practices_data)
    

    presc_data = {
        'PRACTICE_CODE': [f'P00{i}' for i in range(6)],
        'BNF CODE': ['010101'] * 6, # All match the target category drug
        'ACT COST': [100.0, 200.0, 300.0, 400.0, 500.0, 600.0],
        'ITEMS': [10, 10, 10, 10, 10, 10]
    }
    df_presc = pd.DataFrame(presc_data)
    
    # Configure the mock to return these DFs in order
 
    mock_read_csv.side_effect = [df_presc, df_practices, df_drugs]

 
    target_category = "Hypnotics & Anxiolytics"
    graph_data = get_regional_cost_graph(target_category)
    

    assert isinstance(graph_data, dict)
    assert 'x' in graph_data # Regions
    assert 'y' in graph_data # Costs
    assert 'type' in graph_data
    assert graph_data['type'] == 'bar'
    

    assert len(graph_data['x']) > 5
    assert len(graph_data['y']) == len(graph_data['x'])
    

    assert isinstance(graph_data['y'][0], float)
    assert graph_data['y'][0] > 0
    
   
    assert graph_data['y'][0] >= graph_data['y'][-1]