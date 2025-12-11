from flask import Flask, render_template, request  # Added 'request'
import pandas as pd
import os

app = Flask(__name__)

def get_joined_data(filters=None, sort_by='cost', sort_dir='desc'):
    """
    Reads CSVs, joins them, and applies filters if provided.
    filters: dict of {column_name: value}
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up two levels from src/app.py to reach nhs_pai/
    # Then into data/processed
    data_dir = os.path.join(base_dir, '../data/processed') 
    
    try:
        df_presc = pd.read_csv(os.path.join(data_dir, 'clean_prescriptions.csv'))
        # Drop category from prescriptions to avoid duplication during merge with drugs
        if 'category' in df_presc.columns:
            df_presc.drop(columns=['category'], inplace=True)
            
        df_prac = pd.read_csv(os.path.join(data_dir, 'clean_practices.csv'))
        df_drug = pd.read_csv(os.path.join(data_dir, 'clean_drugs.csv'))

        # 1. Join Prescriptions -> Practices (Keep 'region')
        merged_df = pd.merge(df_presc, df_prac, on='PRACTICE_CODE', how='inner')

        # 2. Join -> Drugs (Keep 'category')
        merged_df = pd.merge(merged_df, df_drug, left_on='BNF CODE', right_on='bnf_code', how='inner')
        
        # Drop redundant join key to avoid duplicate columns
        if 'BNF CODE' in merged_df.columns:
            merged_df.drop(columns=['BNF CODE'], inplace=True)
        
        # --- NEW: Renaming for consistency ---
        # Rename columns to make filtering easier (matches your CSV headers to our logic)
        merged_df.rename(columns={
            'PRACTICE_NAME': 'practice_name',
            'name': 'drug_name',
            'region': 'region',
            'category': 'category',
            'ACT COST': 'cost',
            'ITEMS': 'total_items',
            'presentation': 'presentation',
            'BNF CODE': 'bnf_code',
            'POSTCODE': 'post_code'
        }, inplace=True)

        merged_df['price_per_unit'] = merged_df.apply(
            lambda row: row['cost'] / row['total_items'] if row['total_items'] > 0 else 0, 
            axis=1
        )
        
        if filters:
            if filters.get('drug_name'):
                # Case insensitive string match
                merged_df = merged_df[merged_df['drug_name'].str.contains(filters['drug_name'], case=False, na=False)]
            
            if filters.get('practice_name'):
                merged_df = merged_df[merged_df['practice_name'].str.contains(filters['practice_name'], case=False, na=False)]
                
            if filters.get('region'):
                # Exact match for dropdowns usually, but partial here for flexibility
                merged_df = merged_df[merged_df['region'].str.contains(filters['region'], case=False, na=False)]
                
            if filters.get('category'):
                merged_df = merged_df[merged_df['category'].str.contains(filters['category'], case=False, na=False)]

            if filters.get('post_code'):
                # Normalize search term: remove spaces
                search_pc = filters['post_code'].replace(" ", "")
                # Normalize column: remove spaces, then check contains
                merged_df = merged_df[merged_df['post_code'].str.replace(" ", "").str.contains(search_pc, case=False, na=False)]
        
        # Handle sort column mapping
        if sort_by == 'items':
            sort_by = 'total_items'

        valid_sort_cols = ['total_items', 'cost', 'price_per_unit', 'practice_name', 'drug_name']
        
        if sort_by not in valid_sort_cols:
            sort_by = 'cost' # Default fallback

        ascending = True if sort_dir == 'asc' else False
        
        # Apply Pandas Sort
        merged_df = merged_df.sort_values(by=sort_by, ascending=ascending)
        # Select columns to display
        final_df = merged_df[['practice_name', 'drug_name', 'presentation', 'total_items', 'cost', 'bnf_code', 'region', 'category', 'post_code', 'price_per_unit']]
        
        return final_df.head(100).to_dict(orient='records') # Increased limit slightly
        
    except FileNotFoundError:
        return []

@app.route('/')
def index():
    # 1. Get parameters from URL (e.g., /?drug_name=Diazepam)
    filter_params = {
        'drug_name': request.args.get('drug_name'),
        'practice_name': request.args.get('doctor'), # User asked for 'doctor', we map to practice
        'region': request.args.get('region'),
        'category': request.args.get('category'),
        'post_code': request.args.get('post_code')
    }
    
    sort_by = request.args.get('sort', 'cost') # Default to cost
    sort_dir = request.args.get('direction', 'desc') # Default to desc
    # 2. Pass filters to data function
    prescriptions = get_joined_data(filters=filter_params, sort_by=sort_by, sort_dir=sort_dir)
    
    return render_template('index.html', prescriptions=prescriptions, current_sort=sort_by, current_dir=sort_dir)

if __name__ == '__main__':
    app.run(debug=True)