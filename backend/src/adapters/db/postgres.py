import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from workspace root .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../../../.env"))
load_dotenv()

from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/researchmind")

def init_db():
    """
    Initializes the PostgreSQL database schema for ResearchMind.
    Sets up tables for user sessions, parsed paper layout objects, 
    relational citation links, notebooks, and user timelines.
    """
    print("[PostgreSQL] Connecting to initialize database schema...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Enable UUID extension
        cursor.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
        
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
                file_id VARCHAR(255),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            ALTER TABLE sessions ADD COLUMN IF NOT EXISTS file_id VARCHAR(255);
            """,
            """
            ALTER TABLE sessions ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'IDLE';
            """,
            """
            CREATE TABLE IF NOT EXISTS paper_objects (
                session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
                id VARCHAR(100) NOT NULL,
                type VARCHAR(50) NOT NULL,
                page INTEGER NOT NULL,
                bounding_box REAL[] NOT NULL,
                parent_id VARCHAR(100),
                text_content TEXT,
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (session_id, id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS object_relationships (
                session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
                source_id VARCHAR(100) NOT NULL,
                target_id VARCHAR(100) NOT NULL,
                relationship_type VARCHAR(50) NOT NULL,
                PRIMARY KEY (session_id, source_id, target_id, relationship_type)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS research_notebook (
                id SERIAL PRIMARY KEY,
                session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
                selection_text TEXT NOT NULL,
                selection_type VARCHAR(30) NOT NULL,
                ai_explanations JSONB NOT NULL,
                user_note TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS reading_timeline (
                id SERIAL PRIMARY KEY,
                session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
                action_type VARCHAR(50) NOT NULL,
                details JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS workflow_runs (
                run_id UUID PRIMARY KEY,
                session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
                selection_text TEXT NOT NULL,
                selection_type VARCHAR(50) NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS task_checkpoints (
                task_id UUID PRIMARY KEY,
                run_id UUID REFERENCES workflow_runs(run_id) ON DELETE CASCADE,
                agent_name VARCHAR(50) NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
                result JSONB,
                retries INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
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
