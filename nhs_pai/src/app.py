from flask import Flask, render_template, request, url_for, flash, redirect, Response
import pandas as pd
import os
import re
import logging
from logging.handlers import RotatingFileHandler
from database_manager import DatabaseManager
from analytics import calculate_price_stats
from utils import validate_practice_code, validate_bnf_code, validate_postcode
import csv
import io
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Required for flash messages

# Configure Logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'app.log')

handler = RotatingFileHandler(log_file, maxBytes=100000, backupCount=3)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s [%(remote_addr)s] %(message)s')
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
handler.setFormatter(formatter)

app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

def populate_db(manager):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, '../data/processed')
    
    try:
        # Practices
        if not manager.get_all_practices(limit=1):
            print("Populating Practices...")
            df_prac = pd.read_csv(os.path.join(data_dir, 'clean_practices.csv'))
            practices_data = list(df_prac[['PRACTICE_CODE', 'PRACTICE_NAME', 'POSTCODE']].itertuples(index=False, name=None))
            manager.insert_practices(practices_data)
        
        # Drugs
        if not manager.get_all_drugs(limit=1):
            print("Populating Drugs...")
            df_drug = pd.read_csv(os.path.join(data_dir, 'clean_drugs.csv'))
            drugs_data = list(df_drug[['bnf_code', 'name']].itertuples(index=False, name=None))
            manager.insert_drugs(drugs_data)
        
        # Prescriptions
        if not manager.get_all_prescriptions(limit=1):
            print("Populating Prescriptions...")
            df_presc = pd.read_csv(os.path.join(data_dir, 'clean_prescriptions.csv'))
            # Ensure columns match: practice_code, bnf_code, items, act_cost, quantity
            presc_data = list(df_presc[['PRACTICE_CODE', 'BNF CODE', 'ITEMS', 'ACT COST', 'QUANTITY']].itertuples(index=False, name=None))
            manager.insert_prescriptions(presc_data)
            
        print("Database population check complete.")
    except Exception as e:
        print(f"Error populating database: {e}")

def get_db_manager():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, '../data/nhs_data.db')
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    manager = DatabaseManager(db_path)
    manager.create_tables() # Ensure tables exist
    populate_db(manager) # Populate if empty
    return manager

# --- Validation Helpers ---
def validate_practice_code(code):
    # Alphanumeric, typically 6 characters
    return bool(re.match(r'^[A-Z0-9]{6}$', code))

def validate_bnf_code(code):
    # Alphanumeric, typically 9-15 characters
    return bool(re.match(r'^[A-Z0-9]+$', code))

def validate_postcode(postcode):
    # Simple UK postcode regex
    return bool(re.match(r'^[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}$', postcode, re.IGNORECASE))

@app.context_processor
def utility_processor():
    def sort_url(sort_by):
        args = request.args.copy()
        args['sort'] = sort_by
        current_sort = request.args.get('sort', 'price_per_unit')
        current_dir = request.args.get('direction', 'asc')
        
        if sort_by == current_sort and current_dir == 'asc':
            args['direction'] = 'desc'
        else:
            args['direction'] = 'asc'
        return url_for('index', **args)
    return dict(sort_url=sort_url)

def get_joined_data(filters=None, sort_by='price_per_unit', sort_dir='asc'):
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
        
        # --- NEW: Identify Cheapest Price Per Unit ---
        # Only if we have data and filters are applied (optional logic, but good for context)
        # We calculate min_price across the *filtered* dataset
        if not merged_df.empty:
            min_price = merged_df['price_per_unit'].min()
            merged_df['is_cheapest'] = merged_df['price_per_unit'] == min_price
        else:
            merged_df['is_cheapest'] = False

        # Calculate Stats
        min_price, avg_cost, max_price, min_row, max_row = calculate_price_stats(merged_df)

        # Handle sort column mapping
        if sort_by == 'items':
            sort_by = 'total_items'

        valid_sort_cols = ['total_items', 'cost', 'price_per_unit', 'practice_name', 'drug_name']
        
        if sort_by not in valid_sort_cols:
            sort_by = 'price_per_unit' # Default fallback

        ascending = True if sort_dir == 'asc' else False
        
        # Apply Pandas Sort
        merged_df = merged_df.sort_values(by=sort_by, ascending=ascending)
        # Select columns to display
        final_df = merged_df[['practice_name', 'drug_name', 'presentation', 'total_items', 'cost', 'bnf_code', 'region', 'category', 'post_code', 'price_per_unit', 'is_cheapest']]
        
        return final_df.head(100).to_dict(orient='records'), min_price, avg_cost, max_price, min_row, max_row
        
    except FileNotFoundError:
        return [], 0, 0, 0, {}, {}

@app.route('/export')
def export_csv():

    filter_params = {
        'drug_name': request.args.get('drug_name'),
        'practice_name': request.args.get('doctor'),
        'region': request.args.get('region'),
        'category': request.args.get('category')
    }
    

    # Unpack the tuple returned by get_joined_data. We only need the first element (the list of records).
    result = get_joined_data(filters=filter_params)
    
    # Check if result is valid and has data
    if not result or not result[0]:
        return Response("No data found", mimetype="text/plain")
        
    data = result[0]
    df_export = pd.DataFrame(data)
    

    output = io.StringIO()
    df_export.to_csv(output, index=False)
    csv_string = output.getvalue()
    

    return Response(
        csv_string,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=nhs_prescribing_data.csv"}
    )

def get_dropdown_options():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, '../data/processed')
    
    options = {
        'drugs': [],
        'practices': [],
        'regions': [],
        'categories': []
    }
    
    try:
        # Drugs & Categories
        df_drug = pd.read_csv(os.path.join(data_dir, 'clean_drugs.csv'))
        options['drugs'] = sorted(df_drug['name'].dropna().unique().tolist())
        if 'category' in df_drug.columns:
            options['categories'] = sorted(df_drug['category'].dropna().unique().tolist())
            
        # Practices & Regions
        df_prac = pd.read_csv(os.path.join(data_dir, 'clean_practices.csv'))
        options['practices'] = sorted(df_prac['PRACTICE_NAME'].dropna().unique().tolist())
        options['regions'] = sorted(df_prac['region'].dropna().unique().tolist())
        
    except FileNotFoundError:
        pass
        
    return options

@app.route('/')
def index():
    # 1. Get parameters from URL (e.g., /?drug_name=Diazepam)
    filter_params = {
        'drug_name': request.args.get('drug_name'),
        'practice_name': request.args.get('doctor'), 
        'region': request.args.get('region'),
        'category': request.args.get('category'),
        'post_code': request.args.get('post_code')
    }
    
    # Log the access
    log_msg = f"User {request.remote_addr} accessed Homepage. Filters: {filter_params}"
    app.logger.info(log_msg)
    
    sort_by = request.args.get('sort', 'price_per_unit') # Default to price_per_unit
    sort_dir = request.args.get('direction', 'asc') # Default to asc
    
    # Get dropdown options
    dropdown_options = get_dropdown_options()
    
    # 2. Pass filters to data function
    prescriptions, min_price, avg_cost, max_price, min_row, max_row = get_joined_data(filters=filter_params, sort_by=sort_by, sort_dir=sort_dir)
    
    # Determine labels for Min/Max boxes
    min_label = ""
    max_label = ""
    
    if filter_params.get('drug_name'):
        # Filtered by Medicine -> Show Practice Name
        min_label = min_row.get('practice_name', '')
        max_label = max_row.get('practice_name', '')
    elif filter_params.get('category'):
        # Filtered by Category -> Show Medicine Name
        min_label = min_row.get('drug_name', '')
        max_label = max_row.get('drug_name', '')
    
    return render_template('index.html', prescriptions=prescriptions, current_sort=sort_by, current_dir=sort_dir, 
                           min_price=min_price, avg_cost=avg_cost, max_price=max_price,
                           min_label=min_label, max_label=max_label,
                           dropdown_options=dropdown_options)

# --- Edit Database Routes ---

@app.route('/edit_database')
def edit_database():
    manager = get_db_manager()
    
    # Practices Filter
    p_code = request.args.get('p_code', '')
    p_name = request.args.get('p_name', '')
    
    # Drugs Filter
    d_code = request.args.get('d_code', '')
    d_name = request.args.get('d_name', '')
    
    # Prescriptions Filter
    pr_practice = request.args.get('pr_practice', '')
    pr_drug = request.args.get('pr_drug', '')

    # Use search methods with limits
    if p_code or p_name:
        practices = manager.search_practices(code=p_code, name=p_name)
    else:
        practices = manager.get_all_practices(limit=50)

    if d_code or d_name:
        drugs = manager.search_drugs(code=d_code, name=d_name)
    else:
        drugs = manager.get_all_drugs(limit=50)

    if pr_practice or pr_drug:
        prescriptions = manager.search_prescriptions(practice_code=pr_practice, bnf_code=pr_drug)
    else:
        prescriptions = manager.get_all_prescriptions(limit=50)

    manager.close_connection()

    # Determine active tab
    active_tab = 'practices'
    if d_code or d_name:
        active_tab = 'drugs'
    elif pr_practice or pr_drug:
        active_tab = 'prescriptions'

    return render_template('edit_database.html', 
                           practices=practices, drugs=drugs, prescriptions=prescriptions,
                           p_code=p_code, p_name=p_name,
                           d_code=d_code, d_name=d_name,
                           pr_practice=pr_practice, pr_drug=pr_drug,
                           active_tab=active_tab)

@app.route('/edit_database/add_practice', methods=['POST'])
def add_practice():
    code = request.form['practice_code']
    name = request.form['practice_name']
    postcode = request.form['postcode']
    
    app.logger.info(f"User {request.remote_addr} attempting to add practice: {code}, {name}")

    if not name or not name.strip():
        flash('Practice name is required', 'danger')
        return redirect(url_for('edit_database'))

    if not validate_practice_code(code):
        flash(f'Invalid Practice Code format: {code}. Must be 6 alphanumeric characters.', 'danger')
        return redirect(url_for('edit_database'))
        
    if not validate_postcode(postcode):
        flash(f'Invalid Postcode format: {postcode}.', 'danger')
        return redirect(url_for('edit_database'))

    manager = get_db_manager()
    if manager.add_practice(code, name, postcode):
        flash('Practice added successfully!', 'success')
    else:
        flash('Error adding practice. Code may already exist.', 'danger')
    manager.close_connection()
    return redirect(url_for('edit_database'))

@app.route('/edit_database/update_practice', methods=['POST'])
def update_practice():
    code = request.form['practice_code']
    name = request.form['practice_name']
    app.logger.info(f"User {request.remote_addr} updating practice {code} to name {name}")
    manager = get_db_manager()
    manager.update_practice(code, name)
    manager.close_connection()
    flash('Practice updated successfully!', 'success')
    return redirect(url_for('edit_database'))

@app.route('/edit_database/delete_practice/<code>')
def delete_practice(code):
    app.logger.warning(f"User {request.remote_addr} deleting practice {code}")
    manager = get_db_manager()
    manager.delete_practice(code)
    manager.close_connection()
    flash('Practice deleted successfully!', 'success')
    return redirect(url_for('edit_database'))

@app.route('/edit_database/add_drug', methods=['POST'])
def add_drug():
    code = request.form['bnf_code']
    name = request.form['drug_name']
    
    app.logger.info(f"User {request.remote_addr} attempting to add drug: {code}, {name}")

    if not validate_bnf_code(code):
        flash(f'Invalid BNF Code format: {code}. Must be alphanumeric.', 'danger')
        return redirect(url_for('edit_database'))

    manager = get_db_manager()
    if manager.add_drug(code, name):
        flash('Drug added successfully!', 'success')
    else:
        flash('Error adding drug. Code may already exist.', 'danger')
    manager.close_connection()
    return redirect(url_for('edit_database'))

@app.route('/edit_database/update_drug', methods=['POST'])
def update_drug():
    code = request.form['bnf_code']
    name = request.form['drug_name']
    app.logger.info(f"User {request.remote_addr} updating drug {code} to name {name}")
    manager = get_db_manager()
    manager.update_drug(code, name)
    manager.close_connection()
    flash('Drug updated successfully!', 'success')
    return redirect(url_for('edit_database'))

@app.route('/edit_database/delete_drug/<code>')
def delete_drug(code):
    app.logger.warning(f"User {request.remote_addr} deleting drug {code}")
    manager = get_db_manager()
    manager.delete_drug(code)
    manager.close_connection()
    flash('Drug deleted successfully!', 'success')
    return redirect(url_for('edit_database'))

@app.route('/edit_database/add_prescription', methods=['POST'])
def add_prescription():
    practice_code = request.form['practice_code']
    bnf_code = request.form['bnf_code']
    
    app.logger.info(f"User {request.remote_addr} attempting to add prescription: Practice={practice_code}, Drug={bnf_code}")

    try:
        items = int(request.form['items'])
        act_cost = float(request.form['act_cost'])
        quantity = float(request.form['quantity'])
    except ValueError:
        flash('Invalid number format for Items, Cost, or Quantity.', 'danger')
        return redirect(url_for('edit_database'))

    manager = get_db_manager()
    # Check if practice and drug exist
    if not manager.get_practice(practice_code):
        flash(f'Practice {practice_code} does not exist.', 'danger')
        manager.close_connection()
        return redirect(url_for('edit_database'))
        
    if not manager.get_drug(bnf_code):
        flash(f'Drug {bnf_code} does not exist.', 'danger')
        manager.close_connection()
        return redirect(url_for('edit_database'))

    if manager.add_prescription(practice_code, bnf_code, items, act_cost, quantity):
        flash('Prescription added successfully!', 'success')
    else:
        flash('Error adding prescription.', 'danger')
    manager.close_connection()
    return redirect(url_for('edit_database'))

@app.route('/edit_database/update_prescription', methods=['POST'])
def update_prescription():
    id = request.form['id']
    app.logger.info(f"User {request.remote_addr} updating prescription ID {id}")
    try:
        items = int(request.form['items'])
        act_cost = float(request.form['act_cost'])
        quantity = float(request.form['quantity'])
    except ValueError:
        flash('Invalid number format.', 'danger')
        return redirect(url_for('edit_database'))
        
    manager = get_db_manager()
    manager.update_prescription(id, items, act_cost, quantity)
    manager.close_connection()
    flash('Prescription updated successfully!', 'success')
    return redirect(url_for('edit_database'))

@app.route('/edit_database/delete_prescription/<id>')
def delete_prescription(id):
    app.logger.warning(f"User {request.remote_addr} deleting prescription ID {id}")
    manager = get_db_manager()
    manager.delete_prescription(id)
    manager.close_connection()
    flash('Prescription deleted successfully!', 'success')
    return redirect(url_for('edit_database'))

@app.route('/analytics')
def analytics():
    app.logger.info(f"User {request.remote_addr} accessed Analytics page.")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, '../data/processed')
    
    # Get lists for dropdowns
    try:
        df_drug = pd.read_csv(os.path.join(data_dir, 'clean_drugs.csv'))
        drugs = sorted(df_drug['name'].unique().tolist())
        # Assuming 'category' is in clean_drugs.csv or we need to join. 
        # Based on previous code, 'category' is in clean_drugs.csv (merged_df logic).
        # Let's check if 'category' column exists in df_drug
        if 'category' in df_drug.columns:
            categories = sorted(df_drug['category'].dropna().unique().tolist())
        else:
            # Fallback if category isn't in drugs directly (though it should be based on previous merges)
            categories = []
            
        # Get regions
        df_prac = pd.read_csv(os.path.join(data_dir, 'clean_practices.csv'))
        regions = sorted(df_prac['region'].dropna().unique().tolist())
        
    except Exception:
        drugs = []
        categories = []
        regions = []

    selected_drug = request.args.get('drug_name')
    selected_category = request.args.get('category')
    selected_region = request.args.get('region')
    
    practice_graph = get_practice_distribution_graph()
    price_graph = None
    pie_chart_data = None
    
    if selected_drug:
        price_graph = get_drug_regional_ppu(selected_drug)
    elif selected_category:
        price_graph = get_regional_cost_graph(selected_category)
        
    # Always get pie chart data (defaults to national if no region selected)
    pie_chart_data = get_regional_category_distribution(selected_region)
        
    return render_template('analytics.html', drugs=drugs, categories=categories, regions=regions,
                           selected_drug=selected_drug, selected_category=selected_category, selected_region=selected_region,
                           practice_graph=practice_graph, price_graph=price_graph, pie_chart_data=pie_chart_data)

def get_practice_distribution_graph():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, '../data/processed')
    try:
        df_prac = pd.read_csv(os.path.join(data_dir, 'clean_practices.csv'))
        all_practices = df_prac.groupby('region')['PRACTICE_CODE'].nunique().sort_values(ascending=False)
        
        practice_graph = {
            'x': all_practices.index.tolist(),
            'y': all_practices.tolist(),
            'type': 'bar',
            'marker': {'color': '#6c757d'}
        }
        return practice_graph
    except FileNotFoundError:
        return None

def get_regional_cost_graph(category_name):
    """
    Generates data for a Plotly Bar Chart.
    X = Region
    Y = Average Cost Per Item (Sum Cost / Sum Items)
    Filtered by the specific category provided.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Fix path: src/app.py -> ../data/processed
    data_dir = os.path.join(base_dir, '../data/processed')
    
    try:
        # Load Data
        df_presc = pd.read_csv(os.path.join(data_dir, 'clean_prescriptions.csv'))
        # Drop category from prescriptions to avoid duplication during merge with drugs
        if 'category' in df_presc.columns:
            df_presc.drop(columns=['category'], inplace=True)

        df_prac = pd.read_csv(os.path.join(data_dir, 'clean_practices.csv'))
        df_drug = pd.read_csv(os.path.join(data_dir, 'clean_drugs.csv'))

        # 1. Join Prescriptions -> Drugs (to filter by Category first, for speed)
        merged = pd.merge(df_presc, df_prac, on='PRACTICE_CODE', how='inner')
        merged = pd.merge(merged, df_drug, left_on='BNF CODE', right_on='bnf_code', how='inner')

        # 2. Filter by Category
        filtered_df = merged[merged['category'] == category_name]
        
        if filtered_df.empty:
            return None

        # 3. Group by Region
        # We need: Sum Cost, Sum Items, Count Unique Practices
        grouped = filtered_df.groupby('region').agg({
            'ACT COST': 'sum',
            'ITEMS': 'sum',
            'PRACTICE_CODE': 'nunique'
        })

        # 4. Calculate Average Price Per Item
        grouped = grouped[grouped['ITEMS'] > 0]
        grouped['avg_cost'] = grouped['ACT COST'] / grouped['ITEMS']

        # 5. Sort Descending (Highest cost first)
        grouped = grouped.sort_values(by='avg_cost', ascending=False)
        
        # 6. Determine Colors
        # Default Blue
        colors = ['#1f77b4'] * len(grouped)
        if len(grouped) > 0:
            # Max (First item because we sorted desc) -> Red
            colors[0] = '#dc3545' 
            # Min (Last item) -> Green
            colors[-1] = '#198754'

        # 7. Format Hover Text
        regions = grouped.index.tolist()
        costs = grouped['avg_cost'].tolist()
        items = grouped['ITEMS'].tolist()
        practices = grouped['PRACTICE_CODE'].tolist()
        
        hover_texts = []
        for r, c, i, p in zip(regions, costs, items, practices):
            hover_texts.append(f"Region: {r}<br>Avg Cost: £{c:.2f}<br>Total Items: {i}<br>Practices: {p}")

        # 8. Format for Plotly
        price_graph = {
            'x': regions,
            'y': costs,
            'type': 'bar',
            'marker': {'color': colors},
            'text': hover_texts,
            'hoverinfo': 'text'
        }
        
        return price_graph

    except FileNotFoundError:
        return None


def get_drug_regional_ppu(drug_name):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, '../data/processed')
    
    try:
        # Load Data
        df_presc = pd.read_csv(os.path.join(data_dir, 'clean_prescriptions.csv'))
        # Drop category from prescriptions to avoid duplication during merge with drugs
        if 'category' in df_presc.columns:
            df_presc.drop(columns=['category'], inplace=True)

        df_prac = pd.read_csv(os.path.join(data_dir, 'clean_practices.csv'))
        df_drug = pd.read_csv(os.path.join(data_dir, 'clean_drugs.csv'))

        # 1. Merge
        merged = pd.merge(df_presc, df_prac, on='PRACTICE_CODE', how='inner')
        merged = pd.merge(merged, df_drug, left_on='BNF CODE', right_on='bnf_code', how='inner')

        # 2. Filter by Exact Drug Name (Case insensitive)
        filtered_df = merged[merged['name'].str.lower() == drug_name.lower()]
        
        if filtered_df.empty:
            return None

        # 3. Group by Region
        grouped = filtered_df.groupby('region').agg({
            'ACT COST': 'sum',
            'ITEMS': 'sum',
            'PRACTICE_CODE': 'nunique'
        })

        # 4. Calculate Price Per Unit
        grouped = grouped[grouped['ITEMS'] > 0]
        grouped['ppu'] = grouped['ACT COST'] / grouped['ITEMS']

        # 5. Sort Descending (Most expensive region first)
        grouped = grouped.sort_values(by='ppu', ascending=False)

        # 6. Determine Colors
        colors = ['#1f77b4'] * len(grouped)
        if len(grouped) > 0:
            colors[0] = '#dc3545' # Max -> Red
            colors[-1] = '#198754' # Min -> Green

        # 7. Format Hover Text
        regions = grouped.index.tolist()
        ppus = grouped['ppu'].tolist()
        items = grouped['ITEMS'].tolist()
        practices = grouped['PRACTICE_CODE'].tolist()
        
        hover_texts = []
        for r, p, i, prac in zip(regions, ppus, items, practices):
            hover_texts.append(f"Region: {r}<br>Price/Item: £{p:.2f}<br>Total Items: {i}<br>Practices: {prac}")

        # 8. Format for Plotly
        price_graph = {
            'x': regions,
            'y': ppus,
            'type': 'bar',
            'marker': {'color': colors},
            'text': hover_texts,
            'hoverinfo': 'text'
        }
        
        return price_graph

    except FileNotFoundError:
        return None

def get_regional_category_distribution(region_name):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, '../data/processed')
    
    try:
        # Load Data
        df_presc = pd.read_csv(os.path.join(data_dir, 'clean_prescriptions.csv'))
        if 'category' in df_presc.columns:
            df_presc.drop(columns=['category'], inplace=True)
            
        df_prac = pd.read_csv(os.path.join(data_dir, 'clean_practices.csv'))
        df_drug = pd.read_csv(os.path.join(data_dir, 'clean_drugs.csv'))

        # 1. Merge
        merged = pd.merge(df_presc, df_prac, on='PRACTICE_CODE', how='inner')
        merged = pd.merge(merged, df_drug, left_on='BNF CODE', right_on='bnf_code', how='inner')

        # 2. Filter by Region (if provided)
        if region_name:
            filtered_df = merged[merged['region'] == region_name]
        else:
            filtered_df = merged
        
        if filtered_df.empty:
            return None

        # 3. Group by Category
        grouped = filtered_df.groupby('category').agg({
            'ITEMS': 'sum',
            'PRACTICE_CODE': 'nunique'
        }).reset_index()

        # 4. Format for Plotly Pie Chart
        pie_chart = {
            'labels': grouped['category'].tolist(),
            'values': grouped['ITEMS'].tolist(),
            'type': 'pie',
            'customdata': grouped['PRACTICE_CODE'].tolist(),
            'hovertemplate': (
                "<b>%{label}</b><br>" +
                "Items: %{value}<br>" +
                "Practices: %{customdata}<br>" +
                "<extra></extra>"
            )
        }
        
        return pie_chart

    except FileNotFoundError:
        return None

if __name__ == '__main__':
    app.run(debug=True)