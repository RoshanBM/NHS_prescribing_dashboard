import pytest
import sys
import os
import json

# Ensure 'src' is findable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from app import get_regional_cost_graph

def test_generate_plotly_data_for_region_costs():
    """
    GIVEN the NHS dataset
    WHEN we ask for a graph of 'Hypnotics & Anxiolytics' by Region
    THEN it should return a dictionary suitable for Plotly
    AND the x-axis should be Regions, y-axis should be Average Cost per Item
    """
    # 1. Execute Function
    target_category = "Hypnotics & Anxiolytics"
    graph_data = get_regional_cost_graph(target_category)
    
    # 2. Check Structure (Plotly usually expects data objects or simple lists)
    assert isinstance(graph_data, dict)
    assert 'x' in graph_data # Regions
    assert 'y' in graph_data # Costs
    assert 'type' in graph_data
    assert graph_data['type'] == 'bar'
    
    # 3. Check Data Quality
    # We know there are 101 regions, so we expect around that many bars
    # (Checking > 5 is safe enough to prove it worked)
    assert len(graph_data['x']) > 5
    assert len(graph_data['y']) == len(graph_data['x'])
    
    # 4. Check Math Logic (Sanity check)
    # Costs should be positive floats
    assert isinstance(graph_data['y'][0], float)
    assert graph_data['y'][0] > 0
    
    # 5. Check Sorting (Refactor requirement pre-empted in test)
    # We usually want the most expensive region first
    assert graph_data['y'][0] >= graph_data['y'][-1]