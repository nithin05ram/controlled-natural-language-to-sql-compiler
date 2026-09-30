# backend/schema_loader.py
import sqlite3
import os

class SchemaLoader:
    """
    Connects to the database and extracts table and column metadata.
    """
    def __init__(self, db_path):
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found at: {db_path}")
        self.db_path = db_path
        self.schema = self._load_schema()

    def _load_schema(self):
        """
        Connects to the database and retrieves table and column information.
        Returns a dict: {'table_name': {'columns': {'col_name': 'type'}, 'pk': 'col_name'}}
        """
        schema = {}
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall() if row[0] != 'sqlite_sequence']
            
            for table_name in tables:
                table_info = {'columns': {}, 'pk': None}
                
                # Get column details (CID, NAME, TYPE, NOTNULL, PK)
                cursor.execute(f"PRAGMA table_info({table_name});")
                for col_info in cursor.fetchall():
                    col_name = col_info[1]
                    col_type = col_info[2].upper()
                    is_pk = col_info[5]
                    
                    table_info['columns'][col_name] = col_type
                    if is_pk:
                        table_info['pk'] = col_name
                        
                schema[table_name] = table_info
                
            conn.close()
        except sqlite3.Error as e:
            print(f"Error loading schema: {e}")
            raise
            
        return schema

    def get_schema(self):
        return self.schema
    