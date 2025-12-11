import os
import pandas as pd

def get_category_costs():
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, '../data/processed')
    
    try:
        df_presc = pd.read_csv(os.path.join(data_dir, 'clean_prescriptions.csv'))
        if 'category' in df_presc.columns:
            df_presc.drop(columns=['category'], inplace=True)
            
        df_drug = pd.read_csv(os.path.join(data_dir, 'clean_drugs.csv'))

        # 1. Join Prescriptions -> Drugs to get 'category'
        merged_df = pd.merge(df_presc, df_drug, left_on='BNF CODE', right_on='bnf_code', how='inner')

        # 2. Group by Category
    
        grouped = merged_df.groupby('category')[['ACT COST', 'ITEMS']].sum()

        # 3. Calculate Average Cost per Item
        grouped['avg_cost_per_item'] = grouped['ACT COST'] / grouped['ITEMS']

        # 4. Convert to Dictionary { 'CategoryName': 12.50, ... }
        return grouped['avg_cost_per_item'].to_dict()

    except Exception as e:
        print(f"Error calculating stats: {e}")
        return {}

def calculate_filtered_average_cost(df):
    """
    Calculates average cost per item for the provided filtered dataframe.
    Expects columns: 'cost', 'total_items'
    """
    if df.empty:
        return 0
    
    # Check if required columns exist
    if 'cost' not in df.columns or 'total_items' not in df.columns:
        return 0

    total_cost = df['cost'].sum()
    total_items = df['total_items'].sum()
    
    if total_items == 0:
        return 0
        
    return total_cost / total_items

def calculate_price_stats(df):
    """
    Calculates Min, Average, and Max Price Per Unit.
    Returns tuple: (min_price, avg_cost, max_price, min_row, max_row)
    """
    if df.empty:
        return 0, 0, 0, {}, {}
        
    # Calculate Average (Weighted)
    avg_cost = calculate_filtered_average_cost(df)
    
    # Calculate Min/Max based on 'price_per_unit' column
    # Ensure column exists (it should be calculated in app.py)
    if 'price_per_unit' in df.columns:
        min_idx = df['price_per_unit'].idxmin()
        max_idx = df['price_per_unit'].idxmax()
        
        min_price = df.loc[min_idx, 'price_per_unit']
        max_price = df.loc[max_idx, 'price_per_unit']
        
        min_row = df.loc[min_idx].to_dict()
        max_row = df.loc[max_idx].to_dict()
    else:
        min_price = 0
        max_price = 0
        min_row = {}
        max_row = {}
        
    return min_price, avg_cost, max_price, min_row, max_row