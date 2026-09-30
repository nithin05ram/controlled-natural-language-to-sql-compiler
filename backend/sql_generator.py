# backend/sql_generator.py

from parser import (
    ASTNode,
    SelectNode,
    DeleteNode,
    UpdateNode,
    SetClauseNode, # Imported but not explicitly visited, handled within _visit_UpdateNode
    WhereClauseNode,
    ConditionNode,
    CreateTableNode,
    ColumnDefinitionNode,
    OrderByNode,
    CountNode,
    GroupByNode,
    JoinNode,
    QualifiedIdentifierNode,
    AggregateNode
)

class SQLGenerator:
    """
    Translates the Abstract Syntax Tree (AST) into a
    valid SQL query string. Implements the Visitor pattern.
    """
    
    # Generic entry point. Dispatches to the correct _visit_X method.
    def generate(self, node: ASTNode):
        if isinstance(node, ASTNode):
            # Dynamic dispatch: construct method name from class name (e.g., _visit_SelectNode)
            visitor_method_name = f"_visit_{node.__class__.__name__}"
            visitor_method = getattr(self, visitor_method_name, self._generic_visitor)
            return visitor_method(node)
        
        # Handle leaf nodes (literals and simple identifiers)
        if isinstance(node, str):
            return node # Simple identifier/column name
        if isinstance(node, tuple) and node[0] == 'LITERAL_NUMBER':
            return str(node[1]) # Unquoted number
        if isinstance(node, tuple) and node[0] == 'LITERAL_STRING':
            return f"'{node[1]}'" # Single-quoted string
        
        raise TypeError(f"Cannot generate SQL for node of type: {type(node)}")

    # Fallback for unhandled AST nodes.
    def _generic_visitor(self, node: ASTNode):
        raise TypeError(f"No SQL generator method for AST node of type '{node.__class__.__name__}'")

    # --- *** NEW VISITOR METHOD *** ---
    # Generates SQL for the UPDATE statement.
    def _visit_UpdateNode(self, node: UpdateNode):
        """Generates SQL for: UPDATE table SET col=val WHERE condition"""
        
        # 1. Generate SET clause list
        set_sqls = []
        for set_node in node.set_clauses:
            col = set_node.column
            # Recursively generate SQL for the value (which is a literal tuple)
            val = self.generate(set_node.value) 
            set_sqls.append(f"{col} = {val}")
        
        set_clause = ", ".join(set_sqls)
        
        # 2. Generate WHERE clause
        where_clause = self.generate(node.where_clause)
        
        return f"UPDATE {node.table} SET {set_clause} {where_clause};"


    # --- DELETE Statement ---
    # Generates SQL for the DELETE statement.
    def _visit_DeleteNode(self, node: DeleteNode):
        sql = f"DELETE FROM {node.table}"
        where_sql = self.generate(node.where_clause)
        sql += f" {where_sql}"
        return sql + ";"
    
    # --- SELECT Statement ---
    # Generates SQL for the SELECT statement.
    def _visit_SelectNode(self, node: SelectNode):
        columns_sql = ""
        # Handle SELECT *
        if node.select_list == "*":
            columns_sql = "*"
        else:
            # Join generated SQL for all items in the select list (columns, aggregates)
            columns_sql = ", ".join([self.generate(item) for item in node.select_list])
        
        table_sql = node.table
        sql = f"SELECT {columns_sql} FROM {table_sql}"
        
        # Add optional clauses
        if node.joins:
            for join_node in node.joins:
                sql += f" {self.generate(join_node)}"
        
        if node.where_clause:
            where_sql = self.generate(node.where_clause)
            sql += f" {where_sql}"
            
        if node.group_by_clause:
            group_by_sql = self.generate(node.group_by_clause)
            sql += f" {group_by_sql}"
            
        if node.order_by_clause:
            order_by_sql = self.generate(node.order_by_clause)
            sql += f" {order_by_sql}"
            
        return sql + ";"

    # --- Other Visitors ---
    # Generates SQL for a JOIN clause.
    def _visit_JoinNode(self, node: JoinNode):
        condition_sql = self.generate(node.condition)
        return f"JOIN {node.join_table} ON {condition_sql}"

    # Generates SQL for a qualified identifier (table.column).
    def _visit_QualifiedIdentifierNode(self, node: QualifiedIdentifierNode):
        return f"{node.table}.{node.column}"

    # Generates SQL for an aggregate function (e.g., MAX(column)).
    def _visit_AggregateNode(self, node: AggregateNode):
        column_sql = self.generate(node.column)
        return f"{node.function_name.upper()}({column_sql})"

    # Generates SQL for COUNT(*).
    def _visit_CountNode(self, node: CountNode):
        return f"COUNT({node.target})"

    # Generates SQL for the WHERE clause header and conditions.
    def _visit_WhereClauseNode(self, node: WhereClauseNode):
        condition_sqls = [self.generate(cond) for cond in node.conditions]
        return "WHERE " + " AND ".join(condition_sqls)

    # Generates SQL for a single condition (left op right).
    def _visit_ConditionNode(self, node: ConditionNode):
        left_sql = self.generate(node.left)
        right_sql = self.generate(node.right)
        return f"{left_sql} {node.operator} {right_sql}"

    # Generates SQL for the GROUP BY clause.
    def _visit_GroupByNode(self, node: GroupByNode):
        columns_sql = ", ".join([self.generate(col) for col in node.columns])
        return f"GROUP BY {columns_sql}"

    # Generates SQL for the ORDER BY clause.
    def _visit_OrderByNode(self, node: OrderByNode):
        column_sql = self.generate(node.column)
        return f"ORDER BY {column_sql} {node.direction}"

    # Generates SQL for a CREATE TABLE statement.
    def _visit_CreateTableNode(self, node: CreateTableNode):
        column_sqls = [self.generate(col) for col in node.columns]
        columns_sql = ", ".join(column_sqls)
        return f"CREATE TABLE {node.table_name} ({columns_sql});"

    # Generates SQL for a single column definition (Name Type).
    def _visit_ColumnDefinitionNode(self, node: ColumnDefinitionNode):
        sql_type = node.data_type.upper()
        # Map simplified types to canonical SQL types
        if sql_type == 'TEXT' and node.type_param:
            sql_type = f"VARCHAR({node.type_param})"
        elif sql_type == 'TEXT':
            sql_type = "TEXT" 
        elif sql_type == 'INT':
            sql_type = "INTEGER"
        elif sql_type == 'REAL':
            sql_type = "REAL"
        return f"{node.column_name} {sql_type}"