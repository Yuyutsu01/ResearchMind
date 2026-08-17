# ResearchMind Detailed Explanation Engine & Swarm Analyst Chat Architecture

## 1. Executive Summary

This architecture transforms ResearchMind's Swarm Analyst from a static panel with short summaries into a **substantive, expert mentor-level Research Explanation Engine** with an **interactive conversational AI Chat UX** attached directly to paper selections.

---

## 2. Key Architecture Decisions

### 1. Complete Removal of Reading-Level Selector
- Removed `Beginner`, `Undergraduate`, `Researcher` buttons, state, API parameters, and prompt hardcoding across frontend and backend.
- Explanation depth is dynamically adapted based on selected content, paper context, and user query complexity.

### 2. Substantive 500–1500 Word Research Explanations
- **`Simple Explanation`**: 2–5 rich paragraphs covering *What the authors are saying*, *What it means*, *How it works*, and *How it connects to the paper*.
- **`Key Takeaways`**: 5–8 explanatory bullet points with deep technical reasoning.
- **`Why This Matters`**: 2–4 detailed paragraphs.
- **`Equations / Figures / Tables / Citations`**: Deep LaTeX derivations, variable definitions, component axes, step-by-step readings, and author intent.
- Expanded completion token budget in `AIHarness` (`max_token_budget=12000`).

### 3. Conversational AI Research Chat
- **`ConversationContext`**: Dataclass & Redis manager storing `document_id`, `selection_id`, `page`, `section`, `selected_text`, `content_type`, and `messages`.
- **Fast Follow-ups**: Follow-up questions reuse existing `ConversationContext` without re-parsing PDF or re-querying document context, delivering sub-second responses.
- **Follow-up Intent Routing**: `IntentRouter.route_followup_intent(question)` routes questions to minimal required sub-agents (`math`, `background`, `visual`, `citation`, `terminology`, `explanation`).
- **Context Chip & References**: Compact Context Chip (`📄 Page X · §Y · Selected text`) at top of chat thread with clickable page links.
