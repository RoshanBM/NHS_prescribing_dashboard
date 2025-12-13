import pytest
import sys
import os

# Ensure 'src' is findable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from analytics import get_category_costs

def test_get_average_cost_per_item_by_category():
 
    # 1. Run the function
    stats = get_category_costs()
    
    # 2. Basic Validations
    assert isinstance(stats, dict)
    assert len(stats) > 0
    
    # 3. specific Data Check
    
    target_category = 'Hypnotics & Anxiolytics'
    assert target_category in stats
    
    # 4. Value Check
    
    avg_price = stats[target_category]
    assert isinstance(avg_price, float)
    assert avg_price > 0