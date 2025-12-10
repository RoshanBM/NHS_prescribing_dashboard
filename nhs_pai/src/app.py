from flask import Flask, render_template
import pandas as pd
import os

app = Flask(__name__)

def get_joined_data():
    """
    Reads the 3 CSV files and performs a relational join:
    Prescriptions (Fact) -> Practices (Dimension)
    Prescriptions (Fact) -> Drugs (Dimension)
    """


    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, '../../data') # Assuming data is in nhs_pai/data
    

    # Define paths to your CSV files (Assumes they are in the 'data' folder relative to project root)
    # Adjust this path if your files are stored elsewhere
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, '../../data') # Assuming data is in nhs_pai/data
    
    # For this example, we assume files are in the current working directory or fixed path
    # If running directly from src/, paths might need adjustment. 
    # Here we try to find them dynamically or default to filename.
    

    try:
        # Load DataFrames
        df_presc = pd.read_csv(os.path.join(data_dir, 'clean_prescriptions.csv'))
        df_prac = pd.read_csv(os.path.join(data_dir, 'clean_practices.csv'))
        df_drug = pd.read_csv(os.path.join(data_dir, 'clean_drugs.csv'))

        # 1. Join Prescriptions with Practices on PRACTICE_CODE


        merged_df = pd.merge(df_presc, df_prac, on='PRACTICE_CODE', how='inner')

        # 2. Join with Drugs on BNF CODE

        merged_df = pd.merge(merged_df, df_drug, left_on='BNF CODE', right_on='bnf_code', how='inner')

        # 3. Select and Rename columns for the View


        # SQL equivalent: JOIN practices ON prescriptions.PRACTICE_CODE = practices.PRACTICE_CODE
        merged_df = pd.merge(df_presc, df_prac, on='PRACTICE_CODE', how='inner')

        # 2. Join with Drugs on BNF CODE
        # Note: Prescriptions has 'BNF CODE', Drugs has 'bnf_code'
        merged_df = pd.merge(merged_df, df_drug, left_on='BNF CODE', right_on='bnf_code', how='inner')

        # 3. Select and Rename columns for the View
        # We only want relevant columns to display

        final_df = merged_df[[
            'PRACTICE_NAME', 
            'name',           # From drugs table
            'presentation',   # From drugs table
            'ITEMS', 
            'ACT COST',
            'BNF CODE'
        ]]

        # Rename for cleaner template usage
        final_df.columns = ['practice_name', 'drug_name', 'presentation', 'items', 'cost', 'bnf_code']

        # Sort by Cost (descending) to make it interesting
        final_df = final_df.sort_values(by='cost', ascending=False)

        # Return top 50 rows to keep the page fast
        return final_df.head(50).to_dict(orient='records')
        
    except FileNotFoundError:
        # Fallback for testing if files aren't in the exact path
        print("CSV Files not found. Check paths.")
        return []

@app.route('/')
def index():
    prescriptions = get_joined_data()
    return render_template('index.html', prescriptions=prescriptions)

if __name__ == '__main__':
    app.run(debug=True)