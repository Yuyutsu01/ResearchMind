# ResearchMind Features & Changes Log

This document tracks all features added, modified, or deleted within **ResearchMind**.

---

## [2026-07-21] - Comprehensive Reset & Rebuild (PaperOS Refactor)

### Added
* **Virtualized PDF Viewer Overlay**:
  * Implemented an `IntersectionObserver` in `ReadingWorkspace.tsx` to mount only visible pages (and immediate sibling buffers), preventing GPU canvas resource leaks.
  * Added floating selection menu allowing users to route highlighted text or layout objects directly to the Swarm.
* **Progressive Ingestion Worker**:
  * Created `background_worker.py` utilizing async priority queues to parse PDF outlines first, making documents readable in < 1.5 seconds, while Qdrant vector indexing and citation matching runs in the background.
* **Specialized Swarm Agents**:
  * Created `orchestrator.py` and `agents.py` containing math, background, visual, terminology, and citation expert modules.
* **L1 Redis Cache Integration**:
  * Connected `llm_adapter.py` queries to a local Redis cache to enable sub-50ms query retrievals on cached selection overlays.
* **PostgreSQL Schema Expansion**:
  * Created schemas for `paper_objects`, `object_relationships`, `research_notebook`, and `reading_timeline`.

### Deleted
* **Legacy Reinforcement Learning Strategist**:
  * Removed previous RL strategist components (`backend/src/domain/rl/strategist.py`) to align on the core Swarm AI paper assistant objective.
* **Legacy Blackboard Controllers**:
  * Cleared legacy blackboard agents to start fresh with a clean modular monolith directory structure.
