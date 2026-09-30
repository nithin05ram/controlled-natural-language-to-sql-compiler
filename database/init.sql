-- This file creates our 'employees' table
DROP TABLE IF EXISTS employees;
CREATE TABLE employees (
  id INTEGER PRIMARY KEY,
  name TEXT,
  age INTEGER,
  salary REAL,
  department TEXT
);

-- Let's put some sample data inside
INSERT INTO employees (name, age, salary, department) VALUES ('Ravi', 32, 55000.00, 'Engineering');
INSERT INTO employees (name, age, salary, department) VALUES ('Aditi', 29, 62000.00, 'Sales');
INSERT INTO employees (name, age, salary, department) VALUES ('John', 45, 120000.00, 'Engineering');n
INSERT INTO employees (name, age, salary, department) VALUES ('Maria', 38, 48000.00, 'HR');
INSERT INTO employees (name, age, salary, department) VALUES ('Chen', 24, 75000.00, 'Sales');

-- *** NEW TABLES FOR JOIN *** ---

-- Create a 'students' table
DROP TABLE IF EXISTS students;
CREATE TABLE students (
  id INTEGER PRIMARY KEY,
  name TEXT,
  age INTEGER
);
INSERT INTO students (id, name, age) VALUES (101, 'Alice', 20);
INSERT INTO students (id, name, age) VALUES (102, 'Bob', 22);
INSERT INTO students (id, name, age) VALUES (103, 'Charlie', 21);

-- Create a 'courses' table linked to students
DROP TABLE IF EXISTS courses;
CREATE TABLE courses (
  course_id TEXT PRIMARY KEY,
  course_name TEXT,
  student_id INTEGER,
  FOREIGN KEY (student_id) REFERENCES students (id)
);
INSERT INTO courses (course_id, course_name, student_id) VALUES ('CS101', 'Intro to CS', 101);
INSERT INTO courses (course_id, course_name, student_id) VALUES ('MATH200', 'Calculus II', 102);
INSERT INTO courses (course_id, course_name, student_id) VALUES ('PHYS101', 'Physics', 101);