# backend/app.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- Compiler Components ---
from lexer import Lexer
from parser import Parser, Token
from sql_generator import SQLGenerator
from db_executor import DBExecutor
from schema_loader import SchemaLoader
from semantic_analyzer import SemanticAnalyzer


# --- Request Model ---
class CompileRequest(BaseModel):
    english_query: str


# --- FastAPI App Initialization ---
app = FastAPI(
    title="Natural Language to SQL Compiler",
    description="Translates Controlled English into executable SQL and returns results.",
)

# --- Enable CORS for Frontend Access ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Initialize Database + Compiler Components ---
try:
    DB_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "employees.db")

    if not os.path.exists(DB_FILE_PATH):
        raise FileNotFoundError(f"Database file not found at: {DB_FILE_PATH}")

    schema_loader = SchemaLoader(DB_FILE_PATH)
    app.state.schema = schema_loader.get_schema()

    app.state.lexer = Lexer()
    app.state.parser_factory = lambda tokens: Parser(tokens)
    app.state.analyzer = SemanticAnalyzer(app.state.schema)
    app.state.generator = SQLGenerator()
    app.state.executor = DBExecutor(DB_FILE_PATH)

except Exception as e:
    print(f"FATAL STARTUP ERROR: {e}")
    app.state.lexer = None
    app.state.executor = None


# --- Pipeline Function ---
def compile_query_pipeline(english_query: str):
    """
    Full compilation pipeline:
    1. Lexical analysis  -> Tokens
    2. Syntax parsing    -> AST
    3. Semantic analysis -> Validity check
    4. SQL generation    -> Executable SQL string
    """
    if not app.state.lexer or not app.state.generator:
        raise RuntimeError("Compiler not initialized. Verify database path and setup.")

    # 1. Lexical Analysis
    token_tuples = list(app.state.lexer.tokenize(english_query))
    tokens_for_ui = [t[1] for t in token_tuples]

    # 2. Parsing
    parser_tokens = [Token(t[0], t[1]) for t in token_tuples]
    ast = app.state.parser_factory(parser_tokens).parse()
    parse_tree_str = str(ast)

    # 3. Semantic Analysis
    app.state.analyzer.analyze(ast)

    # 4. SQL Generation
    sql = app.state.generator.generate(ast)

    return tokens_for_ui, parse_tree_str, sql


# --- API Endpoint ---
@app.post("/compile")
async def compile_query_api(request: CompileRequest):
    """
    Receives an English query, compiles it to SQL,
    executes it against the SQLite database, and
    returns tokens, parse tree, SQL, and data output.
    """
    try:
        # 1. Run Compiler Pipeline
        tokens_for_ui, parse_tree_str, sql = compile_query_pipeline(request.english_query)

        # 2. Execute SQL
        exec_result = app.state.executor.execute(sql)

        # 3. Handle success
        if exec_result.get("status") == "success":
            return {
                "tokens": tokens_for_ui,
                "parse_tree": parse_tree_str,
                "sql": sql,
                "data": exec_result.get("data", []),
                "message": exec_result.get("message"),
                "table_shown": exec_result.get("table_shown"),
                "error": None,
            }

        # 4. Handle database-level errors
        raise Exception(exec_result.get("message", "Unknown database error."))

    except (ValueError, SyntaxError, RuntimeError) as e:
        # Compiler-related issues (lexical, syntax, semantic, or pipeline errors)
        return {"error": f"Compiler Error: {e}"}

    except Exception as e:
        # Generic server or DB execution failure
        return {"error": f"Server Error: {e}"}
