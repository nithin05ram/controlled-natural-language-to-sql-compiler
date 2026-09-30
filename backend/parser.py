# backend/parser.py
from lexer import Lexer

"""
---------------------------------------------------------------------
PART 1: ABSTRACT SYNTAX TREE (AST) NODES
---------------------------------------------------------------------
"""

# Base AST class
class ASTNode:
    pass


# --- SELECT Node ---
class SelectNode(ASTNode):
    def __init__(self, select_list, table, joins, where_clause=None, group_by_clause=None, order_by_clause=None):
        self.select_list = select_list
        self.table = table
        self.joins = joins
        self.where_clause = where_clause
        self.group_by_clause = group_by_clause
        self.order_by_clause = order_by_clause

    def __repr__(self):
        return (
            f"SelectNode(select={self.select_list}, table='{self.table}', joins={self.joins}, "
            f"where={self.where_clause}, group_by={self.group_by_clause}, order_by={self.order_by_clause})"
        )


# --- UPDATE Node ---
class UpdateNode(ASTNode):
    def __init__(self, table, set_clauses, where_clause):
        self.table = table
        self.set_clauses = set_clauses
        self.where_clause = where_clause

    def __repr__(self):
        return f"UpdateNode(table='{self.table}', set={self.set_clauses}, where={self.where_clause})"


# --- SET Clause Node ---
class SetClauseNode(ASTNode):
    def __init__(self, column, value):
        self.column = column
        self.value = value

    def __repr__(self):
        return f"SetClauseNode({self.column}={self.value})"


# --- DELETE Node ---
class DeleteNode(ASTNode):
    def __init__(self, table, where_clause):
        self.table = table
        self.where_clause = where_clause

    def __repr__(self):
        return f"DeleteNode(table='{self.table}', where={self.where_clause})"


# --- Qualified Identifier Node ---
class QualifiedIdentifierNode(ASTNode):
    def __init__(self, table, column):
        self.table = table
        self.column = column

    def __repr__(self):
        return f"{self.table}.{self.column}"


# --- JOIN Node ---
class JoinNode(ASTNode):
    def __init__(self, join_table, condition):
        self.join_table = join_table
        self.condition = condition

    def __repr__(self):
        return f"JoinNode(table={self.join_table}, on={self.condition})"


# --- COUNT Node ---
class CountNode(ASTNode):
    def __init__(self, target="*"):
        self.target = target

    def __repr__(self):
        return f"CountNode(target='{self.target}')"


# --- Aggregate Function Node ---
class AggregateNode(ASTNode):
    def __init__(self, function_name, column):
        self.function_name = function_name
        self.column = column

    def __repr__(self):
        return f"AggregateNode({self.function_name}({self.column}))"


# --- WHERE Clause ---
class WhereClauseNode(ASTNode):
    def __init__(self, conditions):
        self.conditions = conditions

    def __repr__(self):
        return f"WhereClauseNode(conditions={self.conditions})"


# --- Condition Node ---
class ConditionNode(ASTNode):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right

    def __repr__(self):
        return f"ConditionNode({self.left} {self.operator} {self.right})"


# --- GROUP BY Node ---
class GroupByNode(ASTNode):
    def __init__(self, columns):
        self.columns = columns

    def __repr__(self):
        return f"GroupByNode(columns={self.columns})"


# --- ORDER BY Node ---
class OrderByNode(ASTNode):
    def __init__(self, column, direction):
        self.column = column
        self.direction = direction

    def __repr__(self):
        return f"OrderByNode({self.column} {self.direction})"


# --- CREATE TABLE Node ---
class CreateTableNode(ASTNode):
    def __init__(self, table_name, columns):
        self.table_name = table_name
        self.columns = columns

    def __repr__(self):
        return f"CreateTableNode(table='{self.table_name}', columns={self.columns})"


# --- Column Definition Node ---
class ColumnDefinitionNode(ASTNode):
    def __init__(self, column_name, data_type, type_param=None):
        self.column_name = column_name
        self.data_type = data_type
        self.type_param = type_param

    def __repr__(self):
        if self.type_param:
            return f"ColumnDefinitionNode({self.column_name}, {self.data_type}({self.type_param}))"
        return f"ColumnDefinitionNode({self.column_name}, {self.data_type})"


# --- Token Wrapper ---
class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __repr__(self):
        return f"Token({self.type}, '{self.value}')"


"""
---------------------------------------------------------------------
PART 2: THE PARSER
---------------------------------------------------------------------
"""

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token_index = 0

    # --- MAIN ENTRY POINT ---
    def parse(self):
        if not self.tokens:
            raise SyntaxError("Cannot parse empty query.")

        first_token = self._current_token()
        if not first_token:
            raise SyntaxError("Cannot parse empty query.")

        first_type = first_token.type

        if first_type in ("SELECT", "COUNT", "NUMBER_OF", "AVG", "MAX", "MIN", "SUM"):
            return self._parse_select_statement(consume_select=(first_type == "SELECT"))
        elif first_type == "CREATE":
            return self._parse_create_table_statement()
        elif first_type == "DELETE":
            return self._parse_delete_statement()
        elif first_type == "UPDATE":
            return self._parse_update_statement()
        else:
            raise SyntaxError(f"Unsupported query type: '{first_type}'")

    # --- UPDATE STATEMENT ---
    def _parse_update_statement(self):
        self._consume("UPDATE")
        table = self._consume("IDENTIFIER").value
        self._consume("SET")
        clauses = self._parse_set_clause_list()
        if not self._match("WHERE"):
            raise SyntaxError("UPDATE must include WHERE clause.")
        where = self._parse_where_clause()
        return UpdateNode(table, clauses, where)

    def _parse_set_clause_list(self):
        set_clauses = []
        while True:
            col = self._consume("IDENTIFIER").value

            # Accept either '=' or English synonyms like 'equal', 'equals', or 'is'
            if self._match("EQUAL"):
                self._consume("EQUAL")
            elif self._match("IDENTIFIER") and self._current_token().value.lower() in ("equal", "equals", "is"):
                self._advance()  # consume the word
                if self._match("IDENTIFIER") and self._current_token().value.lower() == "to":
                    self._advance()  # consume 'to' if present
            else:
                raise SyntaxError(f"Expected '=' or 'equal to' after column name '{col}'.")

            # Now parse the value (number or string)
            if self._match("NUMBER") or self._match("STRING"):
                value = self._parse_value_or_identifier()
            else:
                raise SyntaxError("SET value must be a literal.")

            set_clauses.append(SetClauseNode(col, value))

            # Support comma or AND separation
            if self._match("COMMA"):
                self._consume("COMMA")
            elif self._match("AND"):
                self._consume("AND")
            else:
                break
        return set_clauses

    # --- DELETE STATEMENT ---
    def _parse_delete_statement(self):
        self._consume("DELETE")
        self._consume("FROM")
        table = self._consume("IDENTIFIER").value
        if not self._match("WHERE"):
            raise SyntaxError("DELETE must include WHERE clause.")
        where = self._parse_where_clause()
        return DeleteNode(table, where)

    # --- SELECT STATEMENT ---
    def _parse_select_statement(self, consume_select):
        if consume_select:
            self._consume("SELECT")

        select_list = None
        table_name = None

        if self._match("COUNT") or self._match("NUMBER_OF") or self._match("AVG") or self._match("MAX") or self._match("MIN") or self._match("SUM"):
            select_list = self._parse_select_list()
            if self._match("FROM"):
                self._consume("FROM")
            table_name = self._consume("IDENTIFIER").value

        elif self._match("ALL_PHRASE") or self._match("ALL"):
            self._advance()
            select_list = "*"
            self._consume("FROM")
            table_name = self._consume("IDENTIFIER").value

        else:
            select_list = self._parse_select_list()
            self._consume("FROM")
            table_name = self._consume("IDENTIFIER").value

        joins = []
        while self._match("JOIN"):
            joins.append(self._parse_join_clause())

        where_clause = None
        if self._match("WHERE"):
            where_clause = self._parse_where_clause()

        group_by_clause = None
        if self._match("GROUP_BY"):
            group_by_clause = self._parse_group_by_clause()
        elif self._match("EACH"):
            self._consume("EACH")
            col = self._consume("IDENTIFIER").value
            group_by_clause = GroupByNode([col])

        order_by_clause = None
        if self._match("ORDER_BY"):
            order_by_clause = self._parse_order_by_clause()

        return SelectNode(select_list, table_name, joins, where_clause, group_by_clause, order_by_clause)


    # --- JOIN CLAUSE ---
        # --- JOIN CLAUSE PARSING ---
    def _parse_join_clause(self):
        """
        Parses a JOIN clause of the form:
        JOIN <table> ON <left_operand> = <right_operand>
        """
        self._consume("JOIN")

        # Table to join
        join_table_token = self._consume("IDENTIFIER")
        join_table = join_table_token.value

        # Expect ON keyword
        self._consume("ON")

        # Parse the join condition (supports table.column = table.column)
        left_operand = self._parse_value_or_identifier()

        operator_token = self._advance()
        if operator_token.type not in ("EQUAL", "NOT_EQUAL", "GREATER", "LESS", "GREATER_EQUAL", "LESS_EQUAL"):
            raise SyntaxError(f"Expected comparison operator in JOIN condition but got '{operator_token.value}'")

        right_operand = self._parse_value_or_identifier()

        # Create condition node
        condition = ConditionNode(left_operand, operator_token.value, right_operand)

        # Return JoinNode
        return JoinNode(join_table, condition)

    # --- SELECT LIST ---
    def _parse_select_list(self):
        items = [self._parse_select_item()]
        while self._match("COMMA") or self._match("AND"):
            self._advance()
            if not self._current_token() or self._current_token().type == "FROM":
                break
            items.append(self._parse_select_item())
        return items

    def _parse_select_item(self):
        # Handle COUNT and NUMBER_OF first
        if self._match("COUNT") or self._match("NUMBER_OF"):
            self._advance()
            if self._match("ALL"):
                self._advance()
            return CountNode("*")

        # Handle aggregate functions (SUM, AVG, MAX, MIN)
        if self._match("SUM") or self._match("AVG") or self._match("MAX") or self._match("MIN"):
            agg = self._advance()
            if self._match("IDENTIFIER"):
                # Support table-qualified aggregates (e.g., SUM(students.salary))
                table_or_col = self._consume("IDENTIFIER")
                if self._match("DOT"):
                    self._consume("DOT")
                    col = self._consume("IDENTIFIER")
                    return AggregateNode(agg.value, f"{table_or_col.value}.{col.value}")
                else:
                    return AggregateNode(agg.value, table_or_col.value)
            raise SyntaxError(f"Expected column after {agg.value}")

        # Handle qualified or simple identifiers (e.g., students.name)
        if self._match("IDENTIFIER"):
            table_token = self._consume("IDENTIFIER")
            if self._match("DOT"):
                self._consume("DOT")
                col_token = self._consume("IDENTIFIER")
                return QualifiedIdentifierNode(table_token.value, col_token.value)
            return table_token.value

        raise SyntaxError(f"Expected value or identifier, got {self._current_token().type}")

    # --- GROUP BY ---
    def _parse_group_by_clause(self):
        self._consume("GROUP_BY")
        cols = self._parse_select_list()
        return GroupByNode(cols)

    # --- ORDER BY (Enhanced for Aggregates) ---
    def _parse_order_by_clause(self):
        self._consume("ORDER_BY")

        if self._match("SUM") or self._match("AVG") or self._match("MAX") or self._match("MIN"):
            agg_token = self._advance()
            if not self._match("IDENTIFIER"):
                raise SyntaxError(f"Expected column name after {agg_token.value}")
            col_token = self._consume("IDENTIFIER")
            target = AggregateNode(agg_token.value, col_token.value)
        else:
            target = self._parse_value_or_identifier()

        direction = "ASC"
        if self._match("ASC"):
            self._advance()
        elif self._match("DESC"):
            self._advance()
            direction = "DESC"

        return OrderByNode(target, direction)

    # --- WHERE CLAUSE ---
    def _parse_where_clause(self):
        self._consume("WHERE")
        conditions = [self._parse_condition()]
        while self._match("AND"):
            self._advance()
            conditions.append(self._parse_condition())
        return WhereClauseNode(conditions)

    def _parse_condition(self):
        """
        Parses WHERE or JOIN conditions, supporting both standard (=, >, <)
        and natural-language LIKE forms (contains, starts with, ends with).
        """
        left = self._parse_value_or_identifier()

        # Handle LIKE-style operators first
        if self._match("CONTAINS") or self._match("STARTS_WITH") or self._match("ENDS_WITH"):
            op_token = self._advance()
            right = self._parse_value_or_identifier()

            # Only string literals make sense for these
            if not (isinstance(right, tuple) and right[0] == "LITERAL_STRING"):
                raise SyntaxError(f"Expected a string literal after {op_token.value}")

            # Build SQL LIKE pattern
            value = right[1]
            if op_token.type == "CONTAINS":
                pattern = f"%{value}%"
            elif op_token.type == "STARTS_WITH":
                pattern = f"{value}%"
            elif op_token.type == "ENDS_WITH":
                pattern = f"%{value}"

            # Return LIKE-based condition
            return ConditionNode(left, "LIKE", ("LITERAL_STRING", pattern))

        # Handle equality / comparison operators
        if self._match("EQUAL"):
            op = self._advance()
        elif self._match("IDENTIFIER") and self._current_token().value.lower() in ("is", "equal", "equals"):
            self._advance()
            if self._match("IDENTIFIER") and self._current_token().value.lower() == "to":
                self._advance()
            op = Token("EQUAL", "=")
        elif self._match("GREATER") or self._match("LESS") or self._match("GREATER_EQUAL") or self._match("LESS_EQUAL") or self._match("NOT_EQUAL"):
            op = self._advance()
        else:
            raise SyntaxError(f"Expected EQUAL or synonym but got {self._current_token().type}")

        right = self._parse_value_or_identifier()
        return ConditionNode(left, op.value, right)


    # --- GENERIC VALUE HANDLER ---
    def _parse_value_or_identifier(self):
        if self._match("NUMBER"):
            t = self._consume("NUMBER")
            return ("LITERAL_NUMBER", t.value)
        elif self._match("STRING"):
            t = self._consume("STRING")
            return ("LITERAL_STRING", t.value.strip("'\""))
        elif self._match("IDENTIFIER"):
            ident = self._consume("IDENTIFIER")
            if self._match("DOT"):
                self._consume("DOT")
                col = self._consume("IDENTIFIER")
                return QualifiedIdentifierNode(ident.value, col.value)
            return ident.value
        raise SyntaxError("Expected value or identifier")

    # --- CREATE TABLE ---
    def _parse_create_table_statement(self):
        self._consume("CREATE")
        self._consume("TABLE")
        table = self._consume("IDENTIFIER")
        self._consume("WITH")
        self._consume("COLUMNS")
        cols = self._parse_column_definition_list()
        return CreateTableNode(table.value, cols)

    def _parse_column_definition_list(self):
        cols = [self._parse_column_definition()]
        while self._match("COMMA") or self._match("AND"):
            self._advance()
            if not self._match("IDENTIFIER"):
                break
            cols.append(self._parse_column_definition())
        return cols

    def _parse_column_definition(self):
        col_name = self._consume("IDENTIFIER")
        dtype = self._advance()
        if not dtype.type.startswith("TYPE_"):
            raise SyntaxError(f"Expected data type but got '{dtype.value}'")
        data_type = dtype.value
        param = None
        if self._match("LPAREN"):
            self._consume("LPAREN")
            num = self._consume("NUMBER")
            param = int(num.value)
            self._consume("RPAREN")
        return ColumnDefinitionNode(col_name.value, data_type, param)

    # --- TOKEN UTILITIES ---
    def _current_token(self):
        if self.current_token_index < len(self.tokens):
            return self.tokens[self.current_token_index]
        return None

    def _advance(self):
        token = self._current_token()
        if not token:
            raise SyntaxError("Unexpected end of query.")
        self.current_token_index += 1
        return token

    def _match(self, expected_type):
        token = self._current_token()
        return token is not None and token.type == expected_type

    def _consume(self, expected_type):
        token = self._current_token()
        if not token:
            raise SyntaxError(f"Expected {expected_type} but reached end of query.")
        if token.type != expected_type:
            raise SyntaxError(f"Expected {expected_type} but got {token.type}")
        self.current_token_index += 1
        return token
