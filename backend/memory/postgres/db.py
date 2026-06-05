import os
import json
import sqlite3
from datetime import datetime

# Connection parameters
DB_PATH = "research_platform.db"
USE_POSTGRES = False
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        USE_POSTGRES = True
        print("[Database] Using PostgreSQL database.")
    except ImportError:
        print("[Database] psycopg2 not installed. Falling back to SQLite.")

def get_connection():
    if USE_POSTGRES:
        return psycopg2.connect(DATABASE_URL)
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def execute_query(query, params=None, fetch=False, commit=True):
    conn = get_connection()
    cursor = conn.cursor()
    result = None
    try:
        if USE_POSTGRES:
            cursor.execute(query, params or ())
            if fetch:
                # Use RealDictCursor-like behavior
                columns = [desc[0] for desc in cursor.description]
                result = [dict(zip(columns, row)) for row in cursor.fetchall()]
            if commit:
                conn.commit()
        else:
            # SQLite uses ? instead of %s for parameters
            sqlite_query = query.replace("%s", "?")
            cursor.execute(sqlite_query, params or ())
            if fetch:
                result = [dict(row) for row in cursor.fetchall()]
            if commit:
                conn.commit()
    except Exception as e:
        print(f"[Database Error] Query: {query}\nError: {e}")
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()
    return result

def init_db():
    print("[Database] Initializing schemas...")
    
    # SQLite / Postgres compatible type mapping
    text_type = "TEXT"
    json_type = "TEXT" if not USE_POSTGRES else "JSONB"
    serial_type = "INTEGER PRIMARY KEY AUTOINCREMENT" if not USE_POSTGRES else "SERIAL PRIMARY KEY"
    timestamp_type = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP" if not USE_POSTGRES else "TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP"
    
    queries = [
        f"""
        CREATE TABLE IF NOT EXISTS users (
            id {serial_type},
            name {text_type} NOT NULL,
            created_at {timestamp_type}
        );
        """,
        f"""
        CREATE TABLE IF NOT EXISTS tasks (
            id {serial_type},
            prompt {text_type} NOT NULL,
            final_output {text_type},
            status {text_type} DEFAULT 'planning',
            created_at {timestamp_type}
        );
        """,
        f"""
        CREATE TABLE IF NOT EXISTS plans (
            id {serial_type},
            task_id INTEGER,
            steps {json_type},
            created_at {timestamp_type}
        );
        """,
        f"""
        CREATE TABLE IF NOT EXISTS tool_calls (
            id {serial_type},
            task_id INTEGER,
            step_index INTEGER,
            tool_name {text_type},
            kwargs {json_type},
            output {text_type},
            success INTEGER,
            duration_ms REAL,
            created_at {timestamp_type}
        );
        """,
        f"""
        CREATE TABLE IF NOT EXISTS reports (
            id {serial_type},
            task_id INTEGER,
            file_path {text_type},
            format {text_type},
            section_summary {json_type},
            created_at {timestamp_type}
        );
        """,
        f"""
        CREATE TABLE IF NOT EXISTS experience_replay (
            id {serial_type},
            state {json_type},
            action {json_type},
            reward REAL,
            next_state {json_type},
            created_at {timestamp_type}
        );
        """,
        f"""
        CREATE TABLE IF NOT EXISTS telemetry (
            id {serial_type},
            metric_name {text_type},
            duration_ms REAL,
            success INTEGER,
            metadata {json_type},
            created_at {timestamp_type}
        );
        """,
        f"""
        CREATE TABLE IF NOT EXISTS concepts (
            id {serial_type},
            task_id INTEGER,
            term {text_type} NOT NULL,
            definition {text_type},
            math_formula {text_type},
            applications {text_type},
            created_at {timestamp_type}
        );
        """
    ]
    
    for query in queries:
        execute_query(query)
    print("[Database] Initialized successfully.")

def create_task(prompt: str) -> int:
    query = "INSERT INTO tasks (prompt, status) VALUES (%s, 'planning')"
    conn = get_connection()
    cursor = conn.cursor()
    task_id = 0
    try:
        if USE_POSTGRES:
            cursor.execute(query, (prompt,))
            cursor.execute("SELECT id FROM tasks ORDER BY id DESC LIMIT 1")
            res = cursor.fetchone()
            task_id = res[0] if res else 0
        else:
            sqlite_query = query.replace("%s", "?")
            cursor.execute(sqlite_query, (prompt,))
            task_id = cursor.lastrowid
        conn.commit()
    except Exception as e:
        print(f"[Database Error] create_task: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
    return task_id

def update_task_output(task_id: int, output: str, status: str = "completed"):
    query = "UPDATE tasks SET final_output = %s, status = %s WHERE id = %s"
    execute_query(query, (output, status, task_id))

def save_plan(task_id: int, steps: list):
    steps_json = json.dumps(steps)
    query = "INSERT INTO plans (task_id, steps) VALUES (%s, %s)"
    execute_query(query, (task_id, steps_json))

def log_tool_call(task_id: int, step_index: int, tool_name: str, kwargs: dict, output: str, success: bool, duration_ms: float):
    query = """
        INSERT INTO tool_calls (task_id, step_index, tool_name, kwargs, output, success, duration_ms)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    execute_query(query, (
        task_id,
        step_index,
        tool_name,
        json.dumps(kwargs),
        output,
        1 if success else 0,
        duration_ms
    ))

def save_report(task_id: int, file_path: str, report_format: str, section_summary: dict):
    query = "INSERT INTO reports (task_id, file_path, format, section_summary) VALUES (%s, %s, %s, %s)"
    execute_query(query, (task_id, file_path, report_format, json.dumps(section_summary)))

def save_concept(task_id: int, term: str, definition: str, math_formula: str, applications: str):
    query = "INSERT INTO concepts (task_id, term, definition, math_formula, applications) VALUES (%s, %s, %s, %s, %s)"
    execute_query(query, (task_id, term, definition, math_formula, applications))

def get_concepts(task_id: int) -> list:
    query = "SELECT term, definition, math_formula, applications FROM concepts WHERE task_id = %s"
    return execute_query(query, (task_id,), fetch=True) or []

def store_experience(state: dict, action: dict, reward: float, next_state: dict):
    query = "INSERT INTO experience_replay (state, action, reward, next_state) VALUES (%s, %s, %s, %s)"
    execute_query(query, (
        json.dumps(state),
        json.dumps(action),
        reward,
        json.dumps(next_state)
    ))

def get_experiences(limit: int = 100) -> list:
    query = "SELECT state, action, reward, next_state FROM experience_replay ORDER BY id DESC LIMIT %s"
    rows = execute_query(query, (limit,), fetch=True)
    experiences = []
    for r in rows:
        try:
            experiences.append({
                "state": json.loads(r["state"]),
                "action": json.loads(r["action"]),
                "reward": r["reward"],
                "next_state": json.loads(r["next_state"])
            })
        except Exception:
            continue
    return experiences

def log_telemetry(metric_name: str, duration_ms: float, success: bool, metadata: dict = None):
    query = "INSERT INTO telemetry (metric_name, duration_ms, success, metadata) VALUES (%s, %s, %s, %s)"
    execute_query(query, (
        metric_name,
        duration_ms,
        1 if success else 0,
        json.dumps(metadata or {})
    ))

def get_telemetry_summary() -> dict:
    # Aggregated metrics for display
    query = "SELECT metric_name, AVG(duration_ms) as avg_duration, SUM(success) as success_count, COUNT(*) as total_count FROM telemetry GROUP BY metric_name"
    rows = execute_query(query, fetch=True)
    summary = {}
    for r in rows:
        summary[r["metric_name"]] = {
            "avg_duration_ms": round(r["avg_duration"], 2) if r["avg_duration"] else 0.0,
            "success_rate": round((r["success_count"] / r["total_count"]) * 100, 2) if r["total_count"] > 0 else 0.0,
            "count": r["total_count"]
        }
    return summary

# Initialize on import
init_db()
