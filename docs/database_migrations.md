# Database Migrations Architecture (Alembic)

ResearchMind uses **Alembic** to manage PostgreSQL database migrations, schema evolution, version tracking, upgrades, and rollbacks without risk of data loss.

---

## 1. Migration Command Guide

All migration commands should be executed from the `backend` directory:

```bash
cd backend
```

### 1.1 Apply Latest Migrations (Upgrade)
Apply all pending schema migrations to bring the database up-to-date:
```bash
alembic upgrade head
```

### 1.2 Rollback Migrations (Downgrade)
Roll back the database by 1 migration version:
```bash
alembic downgrade -1
```

Or roll back all migrations to base state:
```bash
alembic downgrade base
```

### 1.3 Create a New Migration Version
Generate a new auto-titled migration revision script:
```bash
alembic revision -m "add_new_feature_table"
```

---

## 2. Config & Structure

```text
backend/
├── alembic.ini             # Main Alembic configuration settings
└── alembic/
    ├── env.py              # Dynamic DB URL environment loader
    ├── script.py.mako      # Migration file template
    └── versions/
        └── 001_initial_schema.py # Initial baseline migration (users, sessions, paper_objects, workflow_runs, task_checkpoints...)
```

### 2.1 Dynamic Connection Resolution
`alembic/env.py` reads `DATABASE_URL` directly from the project's `.env` configuration file, supporting both local PostgreSQL instances and cloud database providers (e.g. Neon, AWS RDS) seamlessly.
