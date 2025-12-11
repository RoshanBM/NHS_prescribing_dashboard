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

# ... (Rest of app.py) ...