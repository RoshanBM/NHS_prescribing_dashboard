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
    price_graph = get_regional_cost_graph(target_category)
    
    # 2. Check Structure (Updated for single graph return)
    assert isinstance(price_graph, dict)
    
    # Check Price Graph
    assert 'x' in price_graph # Regions
    assert 'y' in price_graph # Costs
    assert 'type' in price_graph
    assert price_graph['type'] == 'bar'
    
    # 3. Check Data Quality
    assert len(price_graph['x']) > 5
    assert len(price_graph['y']) == len(price_graph['x'])
    
    # 4. Check Math Logic (Sanity check)
    assert isinstance(price_graph['y'][0], float)
    assert price_graph['y'][0] > 0
    
    # 5. Check Sorting
    assert price_graph['y'][0] >= price_graph['y'][-1]

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from app import get_drug_regional_ppu

@patch('app.pd.read_csv')
def test_generate_graph_data_for_drug_ppu(mock_read_csv):

    # --- MOCK DATA SETUP ---
    # 1. Drugs
    df_drugs = pd.DataFrame({
        'bnf_code': ['010101', '020202'],
        'name': ['Alzain', 'OtherDrug']
    })
    
    # 2. Practices
    regions = ['Region A', 'Region B']
    practices_data = {
        'PRACTICE_CODE': ['P001', 'P002'],
        'region': regions
    }
    df_practices = pd.DataFrame(practices_data)
    
    # 3. Prescriptions
    presc_data = {
        'PRACTICE_CODE': ['P001', 'P002'],
        'BNF CODE': ['010101', '010101'], # Both use Alzain
        'ACT COST': [100.0, 200.0],
        'ITEMS': [10, 10]
    }
    df_presc = pd.DataFrame(presc_data)
    
    # Configure mock side effects (presc, prac, drug)
    mock_read_csv.side_effect = [df_presc, df_practices, df_drugs]

    # 1. Execute Function with a known drug name from your CSV
    target_drug = "Alzain" 
    price_graph = get_drug_regional_ppu(target_drug)
    
    # 2. Check Structure (Updated for single graph return)
    assert isinstance(price_graph, dict)
    
    # Check Price Graph
    assert price_graph['type'] == 'bar'
    
    # 3. Check Data Quality
    assert len(price_graph['x']) > 0 
    assert len(price_graph['y']) == len(price_graph['x'])
    
    # 4. Check Math Logic
    first_price = price_graph['y'][0]
    assert isinstance(first_price, float)
    assert first_price > 0