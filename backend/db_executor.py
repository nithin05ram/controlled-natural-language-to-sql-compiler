# backend/db_executor.py
import sqlite3
import os
import re

class DBExecutor:
    """
    Connects to the SQLite database and executes
    the generated SQL queries safely.
    """

    def __init__(self, db_path):
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found at: {db_path}")
        self.db_path = db_path

    class ConnectionContext:
        def __init__(self, db_path):
            self.db_uri = f"file:{db_path}?mode=rw"

        def __enter__(self):
            self.connection = sqlite3.connect(
                self.db_uri,
                uri=True,
                check_same_thread=False
            )
            self.connection.row_factory = sqlite3.Row
            return self.connection

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is None:
                self.connection.commit()
            else:
                self.connection.rollback()
            self.connection.close()

    # Helper: Re-fetch updated data for visualization
    def _run_select_query_on_existing_conn(self, table_name, existing_conn):
        try:
            cursor = existing_conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception:
            return []

    def execute(self, sql_query: str, params=()):
        """
        Executes a SQL query using a thread-safe context manager.
        Returns a consistent JSON response.
        """
        table_name = None
        table_name = None
        match = re.search(r"^(UPDATE|DELETE)\s+(?:FROM\s+)?(\w+)", sql_query, re.IGNORECASE)
        if match:
            table_name = match.group(2)

        try:
            with self.ConnectionContext(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(sql_query, params)

                if cursor.description:
                    # SELECT query
                    rows = cursor.fetchall()
                    data = [dict(row) for row in rows]
                    return {
                        "status": "success",
                        "data": data,
                        "message": None,
                        "table_shown": None,
                    }

                else:
                    # DML/DDL (UPDATE, DELETE, CREATE, etc.)
                    affected = cursor.rowcount
                    action = "Executed"

                    if sql_query.strip().upper().startswith("UPDATE"):
                        action = "Updated"
                    elif sql_query.strip().upper().startswith("DELETE"):
                        action = "Deleted"
                    elif sql_query.strip().upper().startswith("CREATE"):
                        action = "Created"

                    message = f"Query executed successfully. **{affected} row(s) {action}.**"

                    data = []
                    table_shown = None

                    if table_name:
                        data = self._run_select_query_on_existing_conn(table_name, conn)
                        table_shown = table_name

                    return {
                        "status": "success",
                        "data": data,
                        "message": message,
                        "table_shown": table_shown,
                    }

        except sqlite3.Error as e:
            return {"status": "error", "message": f"Database Error: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Server Error: {e}"}
