import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/researchmind")

def init_db():
    """Initializes the PostgreSQL database schema."""
    print("[PostgreSQL] Connecting to initialize database schema...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Enable UUID extension
        cursor.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
        
        # Define tables
        queries = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                prompt TEXT NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'IDLE',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS blackboard_checkpoints (
                id SERIAL PRIMARY KEY,
                session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
                blackboard_state JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS knowledge_graph (
                id SERIAL PRIMARY KEY,
                session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
                nodes JSONB NOT NULL DEFAULT '[]'::jsonb,
                edges JSONB NOT NULL DEFAULT '[]'::jsonb,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS confidence_claims (
                id SERIAL PRIMARY KEY,
                session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
                claim_text TEXT NOT NULL,
                confidence_score REAL NOT NULL CHECK (confidence_score BETWEEN 0.0 AND 1.0),
                evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
                status VARCHAR(50) NOT NULL DEFAULT 'PROVISIONAL',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS hypotheses (
                id SERIAL PRIMARY KEY,
                session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
                hypothesis_text TEXT NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
                evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS telemetry_metrics (
                id SERIAL PRIMARY KEY,
                session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
                metric_name VARCHAR(100) NOT NULL,
                value REAL NOT NULL,
                unit VARCHAR(20) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """
        ]
        
        for q in queries:
            cursor.execute(q)
            
        # Create a default user if not exists
        cursor.execute("SELECT id FROM users LIMIT 1;")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (name, email) VALUES ('Default Researcher', 'researcher@mind.ai')")
            
        conn.commit()
        cursor.close()
        conn.close()
        print("[PostgreSQL] Schema initialization complete.")
    except Exception as e:
        print(f"[PostgreSQL Error] Initialization failed: {e}")

@contextmanager
def get_db_connection():
    """Provides a managed transaction database connection."""
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def execute_query(query: str, params: tuple = None, fetch: bool = False):
    """Executes a single SQL query in transaction mode."""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params or ())
            if fetch:
                return cursor.fetchall()
            return None
