# ResearchMind Response Composer Architecture Documentation

## 1. Executive Overview

ResearchMind's Swarm Analyst output engine has been refactored into a **Response Composer Architecture**.

Instead of returning unformatted, monolithic text walls from individual LLMs, Swarm Agents produce structured JSON schemas. The **Response Composer (`ResponseComposer`)** merges, ranks, deduplicates, and formats these outputs into rich, interactive Markdown documents with collapsible section accordions and a **Reading-Level Adaptor** (🎓 Beginner, 📖 Undergraduate, 🧪 Researcher).

---

## 2. Architecture & Data Flow

```
User Text / Object Selection
            │
            ▼
Swarm Orchestrator (Parallel Checkpointed Execution)
            │
  ┌─────────┼──────────┬──────────┐
  ▼         ▼          ▼          ▼
Explanation Math   Background Visual Agents
  │         │          │          │
  └─────────┴──────────┴──────────┘
            │
            ▼ Structured JSON Schemas
ResponseComposer Engine
            │
  - Deduplicates Repeated Points
  - Ranks Information by Priority
  - Formats Tab Layout (Explain, Math, Background, Visual, Citation)
  - Adapts Depth for Target Reading Level (Beginner / Undergrad / Researcher)
            │
            ▼ Composed Markdown Payload
WebSocket -> SwarmAnalystPanel (ReactMarkdown + Collapsible Accordions)
```

---

## 3. Implemented Modules & Responsibilities

| Component | File Path | Responsibilities |
| :--- | :--- | :--- |
| **ResponseComposer Engine** | [response_composer.py](file:///c:/Users/shiva/OneDrive/Desktop/projects/ResearchMind/backend/src/domain/swarm/response_composer.py) | Merges agent JSON outputs, removes redundancy, formats Markdown sections, adapts reading level. |
| **Swarm Orchestrator** | [orchestrator.py](file:///c:/Users/shiva/OneDrive/Desktop/projects/ResearchMind/backend/src/domain/swarm/orchestrator.py) | Routes selection tasks and passes merged outputs through `response_composer.compose(...)`. |
| **WebSocket Adapter** | [websocket.py](file:///c:/Users/shiva/OneDrive/Desktop/projects/ResearchMind/backend/src/adapters/api/websocket.py) | Delivers `reading_level` and `composer.composed_markdown` payloads over WebSocket. |
| **SwarmAnalystPanel** | [SwarmAnalystPanel.tsx](file:///c:/Users/shiva/OneDrive/Desktop/projects/ResearchMind/frontend/src/components/SwarmAnalystPanel.tsx) | Renders collapsible section accordions, reading level selector buttons, and ReactMarkdown text. |
| **ReadingWorkspace** | [ReadingWorkspace.tsx](file:///c:/Users/shiva/OneDrive/Desktop/projects/ResearchMind/frontend/src/components/ReadingWorkspace.tsx) | Integrates `SwarmAnalystPanel` into the 30% right sidebar layout. |

---

## 4. Tab Layout Specifications

### 📘 Explain Tab Layout
- `# 📘 Simple Explanation`: 2–4 short, clear paragraphs.
- `# 🎯 Key Takeaways`: Bullet points detailing main contributions and core ideas.
- `# 💡 Why This Matters`: Explanation of why the concept is critical inside the paper.
- `# 🧠 Simple Intuition`: Real-world analogy.
- `# 📚 Background Concepts`: Prerequisite topics.
- `# 🔬 Author's Main Claim`: Target thesis and evidence.
- `# 🚀 What's Next`: Bridge to following section.

### 📐 Math Tab Layout
- `# 📐 Equation`: Clean LaTeX display ($$...$$).
- `# 🔤 Variables & Notation`: Definition table/list.
- `# 🪜 Step-by-Step Derivation`: Numbered derivation breakdown.
- `# 🧠 Mathematical Intuition`: Plain English explanation of balance/optimization.
- `# 💡 Worked Example`: Simple numerical evaluation.

---

## 5. Reading-Level Adaptor Modes

1. 🎓 **Beginner**: Simple prose, intuitive analogies, high-level takeaways.
2. 📖 **Undergraduate**: Technical definitions, structured derivations, and algorithmic mechanics.
3. 🧪 **Researcher**: Rigorous terminology, boundary conditions, mathematical assumptions, and research implications.
