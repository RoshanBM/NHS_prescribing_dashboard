import sqlite3
import logging

class DatabaseManager:
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = None
        self.connect()

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_name)
        except sqlite3.Error as e:
            logging.error(f"Error connecting to DB: {e}")

    def close_connection(self):
        if self.conn:
            self.conn.close()

    def create_tables(self):
        if not self.conn:
            return
        
        cursor = self.conn.cursor()
        
        # Practices Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS practices (
                practice_code TEXT PRIMARY KEY,
                practice_name TEXT,
                postcode TEXT
            )
        ''')
        
        # Drugs Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drugs (
                bnf_code TEXT PRIMARY KEY,
                drug_name TEXT
            )
        ''')
        
        # Prescriptions Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prescriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                practice_code TEXT,
                bnf_code TEXT,
                items INTEGER,
                act_cost REAL,
                quantity REAL,
                FOREIGN KEY (practice_code) REFERENCES practices (practice_code),
                FOREIGN KEY (bnf_code) REFERENCES drugs (bnf_code)
            )
        ''')
        
        self.conn.commit()

    def insert_practices(self, practices_data):
        """
        practices_data: List of tuples (practice_code, practice_name, postcode)
        """
        if not self.conn:
            return
            
        cursor = self.conn.cursor()
        cursor.executemany('''
            INSERT OR IGNORE INTO practices (practice_code, practice_name, postcode)
            VALUES (?, ?, ?)
        ''', practices_data)
        self.conn.commit()

    def add_practice(self, code, name, postcode):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO practices (practice_code, practice_name, postcode) VALUES (?, ?, ?)", 
                (code, name, postcode)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            print(f"Error: Practice {code} already exists.")
            return False

    def get_practice(self, code):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM practices WHERE practice_code = ?", (code,))
        return cursor.fetchone()

    def update_practice(self, code, new_name):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE practices SET practice_name = ? WHERE practice_code = ?", 
            (new_name, code)
        )
        self.conn.commit()

    def delete_practice(self, code):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM practices WHERE practice_code = ?", (code,))
        self.conn.commit()