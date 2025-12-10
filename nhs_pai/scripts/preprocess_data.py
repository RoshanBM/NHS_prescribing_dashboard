import pandas as pd
import os

class NHSDataProcessor:
    BNF_CATEGORY_MAP = {
        '0401': 'Hypnotics & Anxiolytics',
        '0402': 'Psychosis & Related',
        '0403': 'Antidepressants',
        '0404': 'CNS Stimulants/ADHD',
        '0405': 'Obesity',
        '0406': 'Nausea & Vertigo',
        '0407': 'Analgesics (Pain)',
        '0408': 'Antiepileptics',
        '0409': 'Parkinsonism',
        '0410': 'Substance Dependence',
        '0411': 'Dementia'
    }

    POSTCODE_REGION_MAP = {
        'B': 'Birmingham', 'M': 'Manchester', 'S': 'Sheffield', 'L': 'Liverpool', 
        'NG': 'Nottingham', 'NE': 'Newcastle upon Tyne', 'E': 'London (East)', 
        'SE': 'London (South East)', 'CV': 'Coventry', 'SW': 'London (South West)', 
        'LE': 'Leicester', 'LS': 'Leeds', 'DN': 'Doncaster', 'N': 'London (North)', 
        'WA': 'Warrington', 'ST': 'Stoke-on-Trent', 'PE': 'Peterborough', 
        'BS': 'Bristol', 'TN': 'Tunbridge Wells', 'GL': 'Gloucester', 
        'W': 'London (West)', 'BN': 'Brighton', 'ME': 'Rochester (Medway)', 
        'BD': 'Bradford', 'TS': 'Cleveland (Teesside)', 'RM': 'Romford', 
        'OL': 'Oldham', 'DE': 'Derby', 'BB': 'Blackburn', 'RG': 'Reading', 
        'CM': 'Chelmsford', 'HA': 'Harrow', 'PR': 'Preston', 'SS': 'Southend-on-Sea', 
        'WS': 'Walsall', 'CH': 'Chester', 'NR': 'Norwich', 'PO': 'Portsmouth', 
        'NW': 'London (North West)', 'GU': 'Guildford', 'PL': 'Plymouth', 
        'SK': 'Stockport', 'MK': 'Milton Keynes', 'SO': 'Southampton', 'WN': 'Wigan', 
        'KT': 'Kingston upon Thames', 'BL': 'Bolton', 'WV': 'Wolverhampton', 
        'WF': 'Wakefield', 'NN': 'Northampton', 'UB': 'Southall (Uxbridge)', 
        'TW': 'Twickenham', 'IP': 'Ipswich', 'CT': 'Canterbury', 'EX': 'Exeter', 
        'DY': 'Dudley', 'YO': 'York', 'CR': 'Croydon', 'OX': 'Oxford', 'HU': 'Hull', 
        'RH': 'Redhill', 'SN': 'Swindon', 'DL': 'Darlington', 'HP': 'Hemel Hempstead', 
        'DA': 'Dartford', 'BH': 'Bournemouth', 'WR': 'Worcester', 'CB': 'Cambridge', 
        'CO': 'Colchester', 'HD': 'Huddersfield', 'BR': 'Bromley', 'IG': 'Ilford', 
        'BA': 'Bath', 'DH': 'Durham', 'LN': 'Lincoln', 'SR': 'Sunderland', 
        'LU': 'Luton', 'SL': 'Slough', 'EN': 'Enfield', 'FY': 'Blackpool', 
        'TR': 'Truro', 'CW': 'Crewe', 'SG': 'Stevenage', 'CA': 'Carlisle', 
        'LA': 'Lancaster', 'TA': 'Taunton', 'SY': 'Shrewsbury', 'TQ': 'Torquay', 
        'AL': 'St Albans', 'SM': 'Sutton', 'WD': 'Watford', 'HR': 'Hereford', 
        'HG': 'Harrogate', 'SP': 'Salisbury', 'DT': 'Dorchester', 'HX': 'Halifax', 
        'TF': 'Telford', 'WC': 'London (Western Central)', 'EC': 'London (East Central)', 
        'TD': 'Galashiels (Scottish Borders)'
    }

    def __init__(self, input_presc_file, input_addr_file, 
                 output_drugs, output_practices, output_prescriptions, 
                 target_chapter='04'):
        """
        Initialize with file paths so they can be swapped for testing.
        """
        self.input_presc = input_presc_file
        self.input_addr = input_addr_file
        self.output_drugs = output_drugs
        self.output_practices = output_practices
        self.output_presc = output_prescriptions
        self.target_chapter = target_chapter

    def get_category(self, bnf_code):
        """Map BNF code to category based on first 4 digits."""
        code_prefix = str(bnf_code)[:4]
        return self.BNF_CATEGORY_MAP.get(code_prefix, 'Other')

    def get_region(self, postcode):
        """Map postcode to region based on first 1-2 letters."""
        if not isinstance(postcode, str) or not postcode:
            return 'Unknown'
        
        # Extract leading letters
        import re
        match = re.match(r"^[A-Z]+", postcode)
        if match:
            prefix = match.group(0)
            # Try exact match (e.g. 'CV')
            if prefix in self.POSTCODE_REGION_MAP:
                return self.POSTCODE_REGION_MAP[prefix]
            # Try first letter if 2-letter prefix not found (e.g. 'B' from 'B1')
            # But wait, 'B' is in the map. 'CV' is in the map.
            # If we have 'CV1', prefix is 'CV'. 'CV' is in map.
            # If we have 'B1', prefix is 'B'. 'B' is in map.
            # If we have 'XYZ', prefix is 'XYZ'. Not in map.
            return 'Other'
        return 'Unknown'

    def process(self):
        print("Step 1: Loading Practice Addresses...")
        try:
            # Using 'header=None' because NHS address files often lack headers
            practices = pd.read_csv(self.input_addr, header=None, 
                                    names=['PERIOD', 'PRACTICE_CODE', 'PRACTICE_NAME', 
                                           'ADDRESS1', 'ADDRESS2', 'ADDRESS3', 'ADDRESS4', 'POSTCODE'])
            
            # Select relevant columns
            practices = practices[['PRACTICE_CODE', 'PRACTICE_NAME', 'POSTCODE']]
            
            # Clean Data
            # 1. Title Case Practice Name
            practices['PRACTICE_NAME'] = practices['PRACTICE_NAME'].astype(str).str.title()
            
            # 2. Clean Postcode (Strip whitespace, ensure uppercase)
            practices['POSTCODE'] = practices['POSTCODE'].astype(str).str.strip().str.upper()

            # 3. Add Region Column
            practices['region'] = practices['POSTCODE'].apply(self.get_region)

            practices.to_csv(self.output_practices, index=False)
            print(f"Saved {len(practices)} practices to {self.output_practices}")
        except Exception as e:
            print(f"Error processing addresses: {e}")
            return

        print("\nStep 2: Processing Prescribing File...")
        
        chunk_size = 100000 
        filtered_chunks = []
        unique_drugs = set()
        
        # Read in chunks
        chunk_iterator = pd.read_csv(self.input_presc, chunksize=chunk_size, on_bad_lines='skip')

        processed_rows = 0
        
        for chunk in chunk_iterator:
            # Clean column names
            chunk.columns = [c.strip() for c in chunk.columns] 
            
            # Filter logic
            mask = chunk['BNF CODE'].astype(str).str.startswith(self.target_chapter)
            relevant_data = chunk[mask].copy()
            
            if not relevant_data.empty:
                # Add Category Column
                relevant_data['category'] = relevant_data['BNF CODE'].apply(self.get_category)

                # Collect unique drugs
                for _, row in relevant_data[['BNF CODE', 'BNF NAME', 'category']].iterrows():
                    bnf_name = str(row['BNF NAME'])
                    if '_' in bnf_name:
                        parts = bnf_name.split('_', 1)
                        name = parts[0]
                        presentation = parts[1]
                    else:
                        name = bnf_name
                        presentation = ''
                    unique_drugs.add((row['BNF CODE'], name, presentation, row['category']))
                
                # Select columns for DB
                # Rename PRACTICE to PRACTICE_CODE if necessary
                if 'PRACTICE' in relevant_data.columns:
                    relevant_data = relevant_data.rename(columns={'PRACTICE': 'PRACTICE_CODE'})
                
                slim_chunk = relevant_data[['PRACTICE_CODE', 'BNF CODE', 'ITEMS', 'ACT COST', 'QUANTITY', 'category']]
                filtered_chunks.append(slim_chunk)
                
            processed_rows += len(chunk)
            print(f"Processed {processed_rows:,} rows...", end='\r')

        print(f"\nFinished processing {processed_rows:,} rows.")
        
        # Save Prescriptions
        if filtered_chunks:
            full_filtered_df = pd.concat(filtered_chunks)
            full_filtered_df.to_csv(self.output_presc, index=False)
            print(f"Saved {len(full_filtered_df)} records to {self.output_presc}")
        else:
            print("Warning: No data matched your filter!")

        # Save Drugs Reference
        drugs_df = pd.DataFrame(list(unique_drugs), columns=['bnf_code', 'name', 'presentation', 'category'])
        drugs_df.to_csv(self.output_drugs, index=False)
        print(f"Saved {len(drugs_df)} unique drugs to {self.output_drugs}")

# --- ENTRY POINT FOR RUNNING MANUALLY ---
if __name__ == "__main__":
    # Define real paths here
    processor = NHSDataProcessor(
        input_presc_file='data/raw/raw_pdpi.csv',
        input_addr_file='data/raw/raw_address.csv',
        output_drugs='data/processed/clean_drugs.csv',
        output_practices='data/processed/clean_practices.csv',
        output_prescriptions='data/processed/clean_prescriptions.csv',
        target_chapter='04'
    )
    processor.process()