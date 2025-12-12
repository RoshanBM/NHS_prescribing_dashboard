import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from analytics import calculate_price_stats

def test_calculate_price_stats_all_nan():
    # Create a DataFrame with NaN values in price_per_unit
    df = pd.DataFrame({
        'price_per_unit': [np.nan, np.nan],
        'cost': [10.0, 20.0],
        'total_items': [1, 2]
    })
    
    # This is expected to fail if the code doesn't handle all-NaNs gracefully
    # It might raise a KeyError or TypeError when trying to access df.loc[nan]
    min_price, avg_cost, max_price, min_row, max_row = calculate_price_stats(df)
    
    assert min_price == 0
    assert max_price == 0
    assert min_row == {}
    assert max_row == {}
