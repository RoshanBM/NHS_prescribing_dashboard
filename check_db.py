import sqlite3
import os

db_path = 'nhs_pai/data/nhs_data.db'

if not os.path.exists(db_path):
    print("Database file does not exist.")
else:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        tables = ['practices', 'drugs', 'prescriptions']
        for table in tables:
            try:
                cursor.execute(f"SELECT count(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"{table}: {count} rows")
            except sqlite3.OperationalError:
                print(f"{table}: Table does not exist")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
