"""Initial schema migration for ResearchMind

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-07-23

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. users table
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. sessions table
    op.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            prompt TEXT NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'IDLE',
            file_id VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)
    op.execute("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS file_id VARCHAR(255);")
    op.execute("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'IDLE';")

    # 3. paper_objects table
    op.execute("""
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
    """)

    # 4. object_relationships table
    op.execute("""
        CREATE TABLE IF NOT EXISTS object_relationships (
            session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
            source_id VARCHAR(100) NOT NULL,
            target_id VARCHAR(100) NOT NULL,
            relationship_type VARCHAR(50) NOT NULL,
            PRIMARY KEY (session_id, source_id, target_id, relationship_type)
        );
    """)

    # 5. research_notebook table
    op.execute("""
        CREATE TABLE IF NOT EXISTS research_notebook (
            id SERIAL PRIMARY KEY,
            session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
            selection_text TEXT NOT NULL,
            selection_type VARCHAR(30) NOT NULL,
            ai_explanations JSONB NOT NULL,
            user_note TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 6. reading_timeline table
    op.execute("""
        CREATE TABLE IF NOT EXISTS reading_timeline (
            id SERIAL PRIMARY KEY,
            session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
            action_type VARCHAR(50) NOT NULL,
            details JSONB NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 7. workflow_runs table
    op.execute("""
        CREATE TABLE IF NOT EXISTS workflow_runs (
            run_id UUID PRIMARY KEY,
            session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
            selection_text TEXT NOT NULL,
            selection_type VARCHAR(50) NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 8. task_checkpoints table
    op.execute("""
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
    """)

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS task_checkpoints CASCADE;")
    op.execute("DROP TABLE IF EXISTS workflow_runs CASCADE;")
    op.execute("DROP TABLE IF EXISTS reading_timeline CASCADE;")
    op.execute("DROP TABLE IF EXISTS research_notebook CASCADE;")
    op.execute("DROP TABLE IF EXISTS object_relationships CASCADE;")
    op.execute("DROP TABLE IF EXISTS paper_objects CASCADE;")
    op.execute("DROP TABLE IF EXISTS sessions CASCADE;")
    op.execute("DROP TABLE IF EXISTS users CASCADE;")
