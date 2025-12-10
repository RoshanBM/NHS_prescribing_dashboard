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

    def process(self):
        print("Step 1: Loading Practice Addresses...")
        try:
            # Using 'header=None' because NHS address files often lack headers
            practices = pd.read_csv(self.input_addr, header=None, 
                                    names=['PERIOD', 'PRACTICE_CODE', 'PRACTICE_NAME', 
                                           'ADDRESS1', 'ADDRESS2', 'ADDRESS3', 'ADDRESS4', 'POSTCODE'])
            
            # Select relevant columns
            practices = practices[['PRACTICE_CODE', 'PRACTICE_NAME', 'POSTCODE']]
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
                    unique_drugs.add((row['BNF CODE'], row['BNF NAME'], row['category']))
                
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
        drugs_df = pd.DataFrame(list(unique_drugs), columns=['bnf_code', 'drug_name', 'category'])
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