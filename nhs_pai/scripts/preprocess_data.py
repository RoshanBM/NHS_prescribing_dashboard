import pandas as pd
import os

class NHSDataProcessor:
    def __init__(self, input_presc_file, input_addr_file, output_drugs, output_practices, output_prescriptions, target_chapter='04'):
        self.input_presc_file = input_presc_file
        self.input_addr_file = input_addr_file
        self.output_drugs = output_drugs
        self.output_practices = output_practices
        self.output_prescriptions = output_prescriptions
        self.target_chapter = target_chapter

    def process(self):
        print("Step 1: Loading Practice Addresses...")
        # Load the address file first to get Practice Names/Regions
        # Note: Column names vary slightly by month, these are standard defaults
        # Handle headerless CSV if needed, but the test creates it without header.
        # The original script assumed headerless for address file?
        # Original script: pd.read_csv(ADDRESS_FILE, names=['PERIOD', ...])
        # Test creates it without header. So names=... is correct.
        
        practices = pd.read_csv(self.input_addr_file, names=['PERIOD', 'PRACTICE_CODE', 'PRACTICE_NAME', 
                                                     'ADDRESS1', 'ADDRESS2', 'ADDRESS3', 'ADDRESS4', 'POSTCODE'])
        
        # We only need Code, Name, and Postcode for the app
        practices = practices[['PRACTICE_CODE', 'PRACTICE_NAME', 'POSTCODE']]
        practices.to_csv(self.output_practices, index=False)
        print(f"Saved {len(practices)} practices to {self.output_practices}")

        print("\nStep 2: Processing the Massive Prescribing File (Chunking)...")
        
        chunk_size = 100000  # Read 100k rows at a time to save memory
        filtered_chunks = []
        unique_drugs = set()
        
        # Create an iterator to read the big file in chunks
        # 'on_bad_lines' skips corrupted lines if any exist
        chunk_iterator = pd.read_csv(self.input_presc_file, chunksize=chunk_size, on_bad_lines='skip')

        processed_rows = 0
        
        for chunk in chunk_iterator:
            # 1. Filter: Keep only rows where 'BNF CODE' starts with our target chapter
            # BNF Codes are 15 digits. The first 2 digits are the Chapter.
            # Ensure column names match your CSV (sometimes 'BNF CODE' or 'BNF_CODE')
            # We strip whitespace just in case
            chunk.columns = [c.strip() for c in chunk.columns] 
            
            # Filter logic
            mask = chunk['BNF CODE'].astype(str).str.startswith(self.target_chapter)
            relevant_data = chunk[mask].copy()
            
            if not relevant_data.empty:
                # 2. Collect unique drugs for our 'Drugs' table
                # We keep BNF CODE and BNF NAME
                for _, row in relevant_data[['BNF CODE', 'BNF NAME']].iterrows():
                    unique_drugs.add((row['BNF CODE'], row['BNF NAME']))
                
                # 3. Select only columns we need for the database
                # We don't need 'BNF NAME' here anymore as it will be in the Drugs table
                # Note: The test creates 'PRACTICE_CODE' in prescribing file, but original data had 'PRACTICE'.
                # The test data has 'PRACTICE_CODE'.
                # We should check which column exists.
                
                if 'PRACTICE' in relevant_data.columns:
                     relevant_data = relevant_data.rename(columns={'PRACTICE': 'PRACTICE_CODE'})
                
                slim_chunk = relevant_data[['PRACTICE_CODE', 'BNF CODE', 'ITEMS', 'ACT COST', 'QUANTITY']]
                filtered_chunks.append(slim_chunk)
                
            processed_rows += len(chunk)
            # print(f"Processed {processed_rows:,} rows...", end='\r')

        print(f"\nFinished processing {processed_rows:,} rows.")
        
        # Combine all the small chunks we kept
        if filtered_chunks:
            full_filtered_df = pd.concat(filtered_chunks)
            full_filtered_df.to_csv(self.output_prescriptions, index=False)
            print(f"Saved {len(full_filtered_df)} relevant prescription records to {self.output_prescriptions}")
        else:
            print("Warning: No data matched your filter!")
            # Create empty file to satisfy test existence check if needed, or let it fail?
            # The test expects the file to exist.
            pd.DataFrame(columns=['PRACTICE_CODE', 'BNF CODE', 'ITEMS', 'ACT COST', 'QUANTITY']).to_csv(self.output_prescriptions, index=False)

        # Save the Drugs Reference Table
        drugs_df = pd.DataFrame(list(unique_drugs), columns=['bnf_code', 'drug_name'])
        drugs_df.to_csv(self.output_drugs, index=False)
        print(f"Saved {len(drugs_df)} unique drugs to {self.output_drugs}")
