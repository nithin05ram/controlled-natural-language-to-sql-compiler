# Natural Language to SQL Compiler

This project is a **full-stack application** that implements a complete, multi-stage **compiler**
to translate **Controlled English queries** into executable SQL.

It features a **Python (FastAPI) backend** that performs lexical, syntactical, and semantic analysis,
and a **vanilla HTML/CSS/JavaScript frontend** that visualizes each stage of the compilation pipeline.

---

## 🚀 Core Features

### Full Compiler Pipeline
Implements all major compiler phases:

1. **Lexical Analysis** (Tokenization)  
2. **Syntax Analysis** (Recursive Descent Parsing to an AST)  
3. **Semantic Analysis** (Schema-aware validation)  
4. **Code Generation** (AST-to-SQL translation)

### Rich SQL Support
Compiles a wide range of SQL commands and clauses:

- **Commands**: `SELECT`, `CREATE TABLE`, `UPDATE`, `DELETE`
- **Clauses**: `SELECT *`, `JOIN ... ON`, `WHERE`, `GROUP BY`, `ORDER BY`
- **Aggregates**: `COUNT`, `AVG`, `MIN`, `MAX`, `SUM`
- **Operators**: `AND`, `LIKE` (starts with, contains, ends with)

### Database-Aware Validation
The Semantic Analyzer connects to the database on startup and caches the schema to validate queries before execution. It detects:

- Type mismatches (e.g., `WHERE age > 'text'`)
- Unknown columns (e.g., `Show birthday from employees`)
- Unknown tables (e.g., `Show name from managers`)

### DML Safety
All `DELETE` and `UPDATE` statements **require a WHERE clause**, preventing accidental full-table operations.

### Interactive UI
The frontend visualizes each compiler phase using dedicated cards that display:

- Tokens
- Parse Tree (AST)
- Generated SQL
- Final database result

### DML Result Visualization
After a successful `UPDATE` or `DELETE`, the UI automatically executes a `SELECT *`
on the affected table to show the updated data state.

---

## ⚙️ Project Architecture

The application runs as **two separate servers**:

- A Python backend (compiler engine)
- A frontend web server (user interface)

---

## 🧠 Backend Compilation Pipeline

The backend (`app.py`) exposes a single `/compile` endpoint that executes the full compilation pipeline:

1. **User Query**
Show avg salary for each department


2. **Lexical Analysis (`lexer.py`)**


[SELECT, AVG, IDENTIFIER(salary), EACH, IDENTIFIER(department)]


3. **Syntax Analysis (`parser.py`)**


SelectNode(select=[AggregateNode(AVG(salary))], ...)


4. **Schema Context (`schema_loader.py`)**
- Loads and caches database schema
- Example: `employees.salary` → `REAL`

5. **Semantic Analysis (`semantic_analyzer.py`)**
- Validates column existence
- Validates aggregate usage
- Validates GROUP BY semantics

6. **Code Generation (`sql_generator.py`)**
    ```sql
    SELECT AVG(salary), department
    FROM employees
    GROUP BY department;

7. **Execution (`db_executor.py`)**
- Executes SQL on employees.db
- Uses a thread-safe database connection manager

- Output:

  ```sql
  [{"department": "Sales", "AVG(salary)": 65000}]
  
8. **Frontend Response**

- Returns all intermediate compiler stages as JSON for visualization

---
**🛠️ Technology Stack**
### Backend ###
- Python 3.10+
- FastAPI
- Uvicorn
- SQLite3

### Frontend ###
- HTML5
- CSS3 (custom properties, no frameworks)
- JavaScript (ES6+)

### Compiler Theory ###
- Lexer: Regular Expressions
- Parser: Recursive Descent Parsing
- Code Generator: Visitor Pattern
---
**🏁 Getting Started — Setup & Installation**
 ### Project Structure 
    nl_sql_compiler/
    ├── backend/
    │   ├── app.py
    │   ├── lexer.py
    │   ├── parser.py
    │   ├── semantic_analyzer.py
    │   ├── sql_generator.py
    │   ├── db_executor.py
    │   ├── schema_loader.py
    │   └── requirements.txt
    ├── frontend/
    │   ├── index.html
    │   ├── styles.css
    │   ├── script.js
    │   └── assets/
    │       └── compiler_icon.png
    └── database/
        ├── init.sql
        └── sqlite3.exe
---
**🗄️ Step 1: Set Up the Database**
- Download SQLite Tools
- Get the Precompiled Binaries for Windows from the official SQLite website.
- Copy the executable
- Place sqlite3.exe inside the database/ folder.
- Initialize the database
- Open PowerShell in the database/ folder and run:
  ```
  Get-Content init.sql | .\sqlite3 employees.db
- This creates employees.db with sample data.

**⚙️ Step 2: Set Up the Backend**
- Create requirements.txt inside backend/:
- fastapi
- uvicorn[standard]
- Install dependencies:
- pip install -r requirements.txt
- Run the backend server:
  ```
  uvicorn app:app --reload
- Backend runs at:
  ```
  http://127.0.0.1:8000
  
**🎨 Step 3: Set Up the Frontend**
- Open a second terminal
- Navigate to the frontend/ folder
- Run:
  ```
  python -m http.server 8080
- Frontend runs at:
  ```
  http://localhost:8080
  
**🌐 Step 4: Access the Application**
- Open your browser and visit:
  ```
  http://localhost:8080
- Project is Now Live at "http://localhost:8080"
---
**📖 Supported Grammar Examples**
- SELECT and WHERE

- Show name and age from employees
 
- List all details from students

- Show name from employees where age > 30

- Display name and department from employees where department = 'Sales' AND salary > 60000
---
### LIKE (String Matching) ###
- Show name from employees where name starts with 'A'

- List employees where department ends with 'ing'

- Find courses that contain 'Intro'
---
### Aggregates ###
- Count all employees

- Show the number of students

- List the average salary from employees

- Find the highest age from students

- Show total salary from employees where department = 'Engineering'
---
### GROUP BY ###
- Show the number of employees for each department

- List department and average salary from employees grouped by department
---
### ORDER BY ###

- Show name and salary from employees sorted by salary descending

- List all students sorted by age ascending
---
### JOIN ###
- Show students.name and courses.course_name from students
- JOIN courses ON students.id = courses.student_id
---
### DML ###
- Update employees set salary = 65000 where name = 'Aditi'

- Delete from students where age < 21

- Create a table projects with columns: id int, name text, budget real
---
**👥 Authors**
- Srikala
- Nithin
- Ravi Tejesh
- Durga Prasad
