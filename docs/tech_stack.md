# ResearchMind Technology Stack Reference

This document summarizes the core technologies and components powering **ResearchMind**.

---

## 1. Frontend Technologies

| Technology | Role / Purpose | Configuration Details |
| :--- | :--- | :--- |
| **Next.js 15 (App Router)** | UI Core Framework | Modular routing pages inside `src/app`. |
| **React 19 & TypeScript** | Component Logic | High type-safety checks (`npx tsc --noEmit` green). |
| **Tailwind CSS v4** | Component Styling | Configured via `@import "tailwindcss"` in `globals.css`. |
| **Lucide React** | Icons Asset Library | Minimalist SVG icons. |
| **Zustand** | Client State Manager | Active session identifiers and upload cache states. |
| **PDF.js (CDN)** | Text/Rendering Overlay | Loaded asynchronously via CDN script tag injection. |

---

## 2. Backend Technologies

| Technology | Role / Purpose | Configuration Details |
| :--- | :--- | :--- |
| **FastAPI** | High-performance API Gateway | Run via `uvicorn src.main:app --port 8001`. |
| **psycopg2-binary** | Relational Database Adapter | Configured for transactional raw PostgreSQL operations. |
| **qdrant-client** | Vector Search Engine | Filters chunks by metadata attributes (like `session_id`). |
| **sentence-transformers** | Context Embeddings generator | Runs local all-MiniLM-L6-v2 (384 dimensions). |
| **fitz (PyMuPDF)** | Document Ingestion Engine | Low-level PDF block extraction. |
| **redis** | L1 Explanation Cache | Keys formatted as `cache:agent:{name}:{session_id}:{id}`. |
| **asyncio** | Concurrent execution | Handles progressive background pipeline queue schedulers. |

---

## 3. Storage & Databases

* **PostgreSQL (Port 5432)**: Relational schema housing parsed paragraphs, section identifiers, research notebook notes, and chronological timelines.
* **Qdrant Vector Database (Port 6333)**: Distance calculation: `Cosine`. Dimensions: `384`.
* **Redis Cache (Port 6379)**: Hot explanation cache. Default TTL: `3600 seconds`.
