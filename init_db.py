import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'nhs_pai', 'src'))

from app import get_db_manager

print("Initializing DB...")
manager = get_db_manager()
manager.close_connection()
print("Done.")
