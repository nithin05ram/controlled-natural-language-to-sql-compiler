# backend/semantic_analyzer.py

# Import all AST nodes we need for validation
from parser import (
    SelectNode,
    DeleteNode,
    UpdateNode,
    CreateTableNode,
    WhereClauseNode,
    ConditionNode,
    QualifiedIdentifierNode,
    AggregateNode
)

class SemanticAnalyzer:
    """
    Validates the Abstract Syntax Tree (AST) against the database schema.
    """
    def __init__(self, schema):
        self.schema = schema
        self.known_tables = set(schema.keys())

    def analyze(self, ast):
        """
        Main entry point for semantic validation.
        """
        if isinstance(ast, SelectNode):
            self._analyze_select(ast)
        elif isinstance(ast, UpdateNode):
            self._analyze_update(ast)
        elif isinstance(ast, DeleteNode):
            self._analyze_delete(ast)
        elif isinstance(ast, CreateTableNode):
            self._analyze_create(ast)
        
        # If no error is raised, the AST is semantically valid

    # --- Utility Functions ---

    def _get_column_type(self, table_name, column_name):
        """Returns the SQL type of a column or raises an error."""
        if table_name not in self.known_tables:
            raise ValueError(f"Semantic Error: Unknown table '{table_name}'.")
            
        columns = self.schema[table_name]['columns']
        if column_name not in columns:
            raise ValueError(f"Semantic Error: Unknown column '{column_name}' in table '{table_name}'.")
            
        return columns[column_name]

    def _validate_table_and_column(self, table_name, column_name=None):
        """Ensures a table/column exists."""
        if table_name not in self.known_tables:
            raise ValueError(f"Semantic Error: Unknown table '{table_name}'.")
        if column_name and column_name not in self.schema[table_name]['columns']:
            raise ValueError(f"Semantic Error: Unknown column '{column_name}' in table '{table_name}'.")

    # --- Analysis for SELECT/UPDATE/DELETE Conditions ---

    def _analyze_where_clause(self, where_clause, current_tables):
        """Validates all conditions within the WHERE clause."""
        if not where_clause: return

        for condition in where_clause.conditions:
            self._analyze_condition(condition, current_tables)

    def _analyze_condition(self, condition, current_tables):
        """Validates a single condition (col OP value)."""
        
        # Determine the left side's column type
        left_op = condition.left
        if isinstance(left_op, QualifiedIdentifierNode):
            self._validate_table_and_column(left_op.table, left_op.column)
            col_type = self._get_column_type(left_op.table, left_op.column)
        elif isinstance(left_op, str): # Simple identifier (e.g., 'age')
            # For unqualified columns, ensure it exists in *one* of the available tables
            found_tables = [t for t in current_tables if left_op in self.schema.get(t, {}).get('columns', {})]
            if not found_tables:
                 raise ValueError(f"Semantic Error: Unknown column '{left_op}'.")
            if len(found_tables) > 1:
                # Ambiguous column error if we have joins
                if len(current_tables) > 1:
                    raise ValueError(f"Semantic Error: Ambiguous column '{left_op}'. Must use 'table.{left_op}'.")
            col_type = self._get_column_type(found_tables[0], left_op)
        else:
            raise ValueError(f"Semantic Error: Invalid operand on left side of condition: {left_op}")

        # Determine the right side's type (LITERAL or COLUMN)
        right_op = condition.right
        
        if isinstance(right_op, tuple) and right_op[0].startswith('LITERAL'):
            # Rule: Text columns can be compared with any operator, but numeric types 
            # must use numeric values for comparisons other than '=' and '!='.
            literal_type = right_op[0].split('_')[1] # 'NUMBER' or 'STRING'
            
            if col_type in ('INTEGER', 'REAL') and literal_type == 'STRING':
                if condition.operator not in ('=', '!='):
                    raise ValueError(f"Semantic Error: Cannot compare numeric column '{left_op}' with string '{right_op[1]}' using '{condition.operator}'.")
            
        elif isinstance(right_op, QualifiedIdentifierNode) or isinstance(right_op, str):
            # Rule: Joining or comparing two columns
            if condition.operator in ('>', '<', '>=', '<='):
                raise ValueError("Semantic Error: Comparison operators (>, <) only allowed with literals, not columns.")

    # --- Statement Specific Analysis ---

    def _analyze_select(self, ast: SelectNode):
        """Analyze SELECT statement."""
        
        # 1. Collect all tables involved (initial table + joins)
        current_tables = [ast.table] + [j.join_table for j in ast.joins]
        
        # 2. Validate all tables exist
        for table in current_tables:
            if table not in self.known_tables:
                raise ValueError(f"Semantic Error: Unknown table '{table}'.")

        # 3. Validate all selected columns exist and are unambiguous
        if ast.select_list != '*':
            for item in ast.select_list:
                if isinstance(item, AggregateNode):
                    # For AVG/MIN/MAX/SUM, validate the column inside
                    self._validate_table_and_column(current_tables[0], item.column)
                elif isinstance(item, QualifiedIdentifierNode):
                    self._validate_table_and_column(item.table, item.column)
                elif isinstance(item, str): # Simple column name
                    self._validate_table_and_column(current_tables[0], item)
                
        # 4. Validate WHERE clause
        self._analyze_where_clause(ast.where_clause, current_tables)

        # 5. Validate ORDER BY/GROUP BY columns
        if ast.order_by_clause:
            # We don't worry about complexity, just that the column exists
            col = ast.order_by_clause.column
            if isinstance(col, str):
                 self._validate_table_and_column(current_tables[0], col)


    def _analyze_update(self, ast: UpdateNode):
        """Analyze UPDATE statement."""
        
        self._validate_table_and_column(ast.table)
        current_tables = [ast.table]
        
        # 1. Validate SET clauses: column exists and value type is correct
        for set_clause in ast.set_clauses:
            col_name = set_clause.column
            self._validate_table_and_column(ast.table, col_name)
            col_type = self._get_column_type(ast.table, col_name)
            
            value_type = set_clause.value[0] # LITERAL_NUMBER or LITERAL_STRING
            
            # Simple Type Check: Ensure we don't set a number column to a pure string literal
            if col_type in ('INTEGER', 'REAL') and value_type == 'LITERAL_STRING':
                # Allow setting a numeric column to a string, but raise warning if not a number
                try:
                    float(set_clause.value[1])
                except ValueError:
                    raise ValueError(f"Semantic Error: Cannot set numeric column '{col_name}' to non-numeric string '{set_clause.value[1]}'.")

        # 2. Validate WHERE clause
        self._analyze_where_clause(ast.where_clause, current_tables)

    def _analyze_delete(self, ast: DeleteNode):
        """Analyze DELETE statement."""
        self._validate_table_and_column(ast.table)
        current_tables = [ast.table]
        
        # Validate WHERE clause (which is mandatory for DELETE)
        self._analyze_where_clause(ast.where_clause, current_tables)

    def _analyze_create(self, ast: CreateTableNode):
        """Analyze CREATE TABLE statement."""
        # Check if the table name already exists (a basic check)
        if ast.table_name in self.known_tables:
            raise ValueError(f"Semantic Error: Table '{ast.table_name}' already exists.")
        
        # Check for unique column names in the new table
        col_names = [col.column_name for col in ast.columns]
        if len(col_names) != len(set(col_names)):
            raise ValueError("Semantic Error: Duplicate column names found in CREATE TABLE statement.")