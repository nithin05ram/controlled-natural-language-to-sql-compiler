# backend/lexer.py
import re

# The Lexer class is responsible for taking a raw text input (like a natural language SQL query)
# and converting it into a sequence of meaningful tokens.
class Lexer:
    # Constructor: initializes the token specifications.
    def __init__(self):
        self.token_specs = self._build_token_specs()

    # Private method to define the rules for tokenization.
    # Each entry is a tuple: (TOKEN_NAME, REGULAR_EXPRESSION).
    # The order of specifications is crucial, as the regex engine matches them sequentially.
    def _build_token_specs(self):
        specs = [
            # --- SQL DML Keywords (for SELECT) ---
            # Broad selection command, including natural language synonyms.
            ('SELECT',      r'\bshow\b|\bselect\b|\blist\b|\bdisplay\b|\bfind\b|\bget\b'),
            # Aggregate functions and their synonyms (order matters for multi-word phrases)
            ('COUNT',       r'\bcount\b'),
            ('NUMBER_OF',   r'\bnumber of\b'), # Must come before single words like 'number' or 'of' if they were tokens
            ('AVG',         r'\baverage\b|\bavg\b'),
            ('MAX',         r'\bmaximum\b|\bmax\b|\bhighest\b|\blargest\b'),
            ('MIN',         r'\bminimum\b|\bmin\b|\blowest\b|\bsmallest\b'),
            ('SUM',         r'\btotal\b|\bsum\b'),
            ('FROM',        r'\bfrom\b|\bof\b'),
            ('WHERE',       r'\bwhere\b'),
            ('AND',         r'\band\b'),
            ('GROUP_BY',    r'\bgroup by\b|\bgrouped by\b|\bfor each\b'),
            ('EACH',        r'\beach\b'),
            ('ORDER_BY',    r'\border by\b|\bsorted by\b'),
            ('ASC',         r'\bascending\b|\basc\b'),
            ('DESC',        r'\bdescending\b|\bdesc\b'),
            ('ALL_PHRASE',  r'\ball details\b|\ball records\b'), # Multi-word 'ALL' synonyms
            ('ALL',         r'\ball\b|\bdetails\b|\brecords\b'), # Single-word 'ALL' synonyms
            ('JOIN',        r'\bjoin\b'),
            ('ON',          r'\bon\b'),
            ('LIKE',        r'\blike\b'),
            # Natural language synonyms for SQL LIKE patterns
            ('STARTS_WITH', r'\bstarts with\b'),
            ('ENDS_WITH',   r'\bends with\b'),
            ('CONTAINS',    r'\bcontains\b'),
            ('DELETE',      r'\bdelete\b'),
            
            # --- *** NEW DML TOKENS (UPDATE/SET) *** ---
            ('UPDATE',      r'\bupdate\b|\bset the\b'), # 'set the' is a natural language way to introduce an update
            ('SET',         r'\bset\b'), 
            
            # --- SQL DDL Keywords (for CREATE TABLE) ---
            ('CREATE',      r'\bcreate\b'),
            ('TABLE',       r'\btable\b'),
            ('NAMED',       r'\bnamed\b'),
            ('WITH',        r'\bwith\b'),
            ('COLUMNS',     r'\bcolumns\b'),
            
            # --- SQL Data Types ---
            ('TYPE_INT',    r'\bint\b|\binteger\b'),
            ('TYPE_TEXT',   r'\btext\b|\bstring\b|\bvarchar\b'),
            ('TYPE_REAL',   r'\breal\b|\bfloat\b|\bdouble\b'),

            # --- Operators and Punctuation (Order matters! Longest match first!) ---
            ('GREATER_EQUAL', r'\bis greater than or equal to\b|>=|=>'),
            ('LESS_EQUAL',    r'\bis less than or equal to\b|<=|=<'),
            ('NOT_EQUAL',     r'\bis not equal to\b|\bis not\b|!=|<>'),
            # Single-character operators must come *after* their multi-character counterparts
            ('GREATER',       r'\bis greater than\b|\bgreater than\b|>'),
            ('LESS',          r'\bis less than\b|\bless than\b|<'),
            ('EQUAL',         r'\bis equal to\b|\bequals\b|\bis\b|='),
            
            # Punctuation
            ('LPAREN',      r'\('),
            ('RPAREN',      r'\)'),
            ('COMMA',       r','),
            ('DOT',         r'\.'),
            
            # --- Literals (actual data values) ---
            ('NUMBER',      r'\b\d+(\.\d+)?\b'), # Integer or floating point number
            ('STRING',      r'\'[^\']+\'|\"[^\"]+\"'), # Single or double quoted strings

            # --- Stopword (to be ignored) ---
            # Common English words that add little meaning to the SQL logic.
            ('STOPWORD',    r'\ba\b|\ban\b|\bthe\b'), 
            
            # --- Generic IDENTIFIER (MUST BE AFTER KEYWORDS) ---
            # Catches table names, column names, etc. Must be last in this section to ensure
            # keywords like 'select' aren't mistakenly tokenized as IDENTIFIER.
            ('IDENTIFIER',  r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'),

            # --- Utility Tokens ---
            ('NEWLINE',     r'\n'),
            ('SKIP',        r'[ \t\?!:]+'), # Whitespace and common punctuation to ignore
            ('MISMATCH',    r'.'), # Catches any single character that hasn't been matched yet (error token)
        ]
        return specs

    # Main tokenization method. Takes a raw string and yields tokens.
    def tokenize(self, code):
        # 1. Build the master regex pattern by joining all token specs.
        # Uses named capture groups (?P<TOKEN_NAME>...)
        tok_regex = '|'.join(f'(?P<{pair[0]}>{pair[1]})' for pair in self.token_specs)
        # 2. Compile the regex with IGNORECASE flag for case-insensitive matching,
        # and pre-fetch the finditer method for performance.
        get_token = re.compile(tok_regex, re.IGNORECASE).finditer
        
        # 3. Iterate over all matches found in the input 'code'.
        for mo in get_token(code):
            kind = mo.lastgroup # The name of the matching capture group (the token kind)
            value = mo.group()  # The actual text matched by the regex
            
            # Skip utility/ignored tokens.
            if kind == 'NEWLINE' or kind == 'SKIP' or kind == 'STOPWORD':
                continue
            # Handle mismatch (unrecognized character).
            elif kind == 'MISMATCH':
                raise ValueError(f"Unexpected character '{value}'")
            
            # Normalize the token value:
            if kind in ('STRING', 'NUMBER'):
                # String and Number literals keep their original case/value.
                normalized_value = value
            elif kind == 'DOT':
                normalized_value = '.'
            else:
                # Keywords and Identifiers are normalized to lowercase initially.
                normalized_value = value.lower()

            # Operator normalization: map natural language or multi-character symbols to standard SQL operators.
            if kind == 'GREATER_EQUAL': normalized_value = '>='
            elif kind == 'LESS_EQUAL':    normalized_value = '<='
            elif kind == 'NOT_EQUAL':     normalized_value = '!='
            elif kind == 'GREATER':       normalized_value = '>'
            elif kind == 'LESS':          normalized_value = '<'
            elif kind == 'EQUAL':         normalized_value = '='
            
            # Data Type normalization: map synonyms to canonical type names (uppercase).
            if kind.startswith('TYPE_'):
                if kind == 'TYPE_INT': normalized_value = 'INT'
                elif kind == 'TYPE_TEXT': normalized_value = 'TEXT'
                elif kind == 'TYPE_REAL': normalized_value = 'REAL'
            
            # Aggregate Function normalization (to canonical uppercase names).
            elif kind == 'AVG': normalized_value = 'AVG'
            elif kind == 'MAX': normalized_value = 'MAX'
            elif kind == 'MIN': normalized_value = 'MIN'
            elif kind == 'SUM': normalized_value = 'SUM'
            
            # LIKE pattern normalization: map natural language phrases to a canonical LIKE type.
            elif kind == 'LIKE':          normalized_value = 'LIKE'
            elif kind == 'STARTS_WITH': normalized_value = 'LIKE_STARTS'
            elif kind == 'ENDS_WITH':   normalized_value = 'LIKE_ENDS'
            elif kind == 'CONTAINS':    normalized_value = 'LIKE_CONTAINS'
            
            # Yield the final token as a tuple (KIND, NORMALIZED_VALUE).
            yield (kind, normalized_value)