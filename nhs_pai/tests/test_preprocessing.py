import pytest
import pandas as pd
import os
import shutil
import sys

# Add parent directory to path to allow imports from scripts
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.preprocess_data import NHSDataProcessor

@pytest.fixture
def setup_data():
    """
    Create temporary dummy CSV files that mimic the real NHS data.
    """
    test_dir = 'test_data_temp'
    os.makedirs(test_dir, exist_ok=True)

    # Define temporary filenames
    input_presc = os.path.join(test_dir, 'dummy_prescriptions.csv')
    input_addr = os.path.join(test_dir, 'dummy_addr.csv')
    out_drugs = os.path.join(test_dir, 'out_drugs.csv')
    out_prac = os.path.join(test_dir, 'out_practices.csv')
    out_presc = os.path.join(test_dir, 'out_presc.csv')

    # 1. Create a dummy Practice Address file
    # Format: PERIOD, PRACTICE_CODE, PRACTICE_NAME, ADDRESS1... POSTCODE
    pd.DataFrame({
        'PERIOD': [202409, 202409],
        'PRACTICE_CODE': ['P001', 'P002'],
        'PRACTICE_NAME': ['TEST SURGERY A', 'Test Surgery B'],
        'ADDRESS1': ['1 Way', '2 Way'], 'ADDRESS2': ['', ''], 'ADDRESS3': ['', ''], 'ADDRESS4': ['', ''],
        'POSTCODE': [' sw1 1aa ', 'm1 2bb']
    }).to_csv(input_addr, index=False, header=False) # NHS address file usually has no header

    # 2. Create a dummy Prescribing file
    # - Row 1: BNF starts with '04' (Should KEEP)
    # - Row 2: BNF starts with '05' (Should DROP)
    # - Row 3: BNF starts with '04' (Should KEEP)
    pd.DataFrame({
        'PRACTICE_CODE': ['P001', 'P001', 'P002'],
        'BNF CODE': ['0401000A', '0501000B', '0402000C'], # Note the codes
        'BNF NAME': ['Mental_Health Drug', 'Antibiotic_Tab', 'Anxiety_Drug'],
        'ITEMS': [10, 5, 20],
        'ACT COST': [50.0, 12.5, 100.0],
        'QUANTITY': [100, 50, 200]
    }).to_csv(input_presc, index=False)

    # Return paths to the test function
    paths = {
        'test_dir': test_dir,
        'input_presc': input_presc,
        'input_addr': input_addr,
        'out_drugs': out_drugs,
        'out_prac': out_prac,
        'out_presc': out_presc
    }
    
    yield paths

    # Teardown
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

def test_process_filters_correctly(setup_data):
    """
    Test that only '04' drugs are kept and files are generated.
    """
    paths = setup_data
    
    # Initialize processor with our dummy paths
    processor = NHSDataProcessor(
        input_presc_file=paths['input_presc'],
        input_addr_file=paths['input_addr'],
        output_drugs=paths['out_drugs'],
        output_practices=paths['out_prac'],
        output_prescriptions=paths['out_presc'],
        target_chapter='04'
    )

    # Run the logic
    processor.process()

    # --- ASSERTIONS ---

    # 1. Check if files were created
    assert os.path.exists(paths['out_presc'])
    assert os.path.exists(paths['out_drugs'])

    # 2. Check content of Prescriptions (Should only have 2 rows, not 3)
    df_presc = pd.read_csv(paths['out_presc'])
    assert len(df_presc) == 2
    assert '0501000B' not in df_presc['BNF CODE'].values # Ensure the '05' drug is gone
    assert 'category' in df_presc.columns
    assert df_presc.loc[df_presc['BNF CODE'] == '0401000A', 'category'].values[0] == 'Hypnotics & Anxiolytics'

    # 3. Check content of Drugs (Should have 2 unique drugs)
    df_drugs = pd.read_csv(paths['out_drugs'])
    assert len(df_drugs) == 2
    assert 'name' in df_drugs.columns
    assert 'presentation' in df_drugs.columns
    assert 'Mental' in df_drugs['name'].values
    assert 'Health Drug' in df_drugs['presentation'].values
    assert 'category' in df_drugs.columns
    assert 'Hypnotics & Anxiolytics' in df_drugs['category'].values

    # 4. Check content of Practices (Title Case and Postcode Cleaning)
    df_prac = pd.read_csv(paths['out_prac'])
    assert 'Test Surgery A' in df_prac['PRACTICE_NAME'].values # Was 'TEST SURGERY A'
    assert 'SW1 1AA' in df_prac['POSTCODE'].values # Was ' sw1 1aa '
    assert 'M1 2BB' in df_prac['POSTCODE'].values # Was 'm1 2bb'
    
    # 5. Check Region Mapping
    # SW1 1AA -> SW -> London (South West)
    # M1 2BB -> M -> Manchester
    assert 'region' in df_prac.columns
    assert df_prac.loc[df_prac['POSTCODE'] == 'SW1 1AA', 'region'].values[0] == 'London (South West)'
    assert df_prac.loc[df_prac['POSTCODE'] == 'M1 2BB', 'region'].values[0] == 'Manchester'
