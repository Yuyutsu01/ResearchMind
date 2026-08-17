# ResearchMind Landing & Welcome Screen Architecture Documentation

## 1. Executive Summary

The **ResearchWelcome Landing Experience** (`frontend/src/components/ResearchWelcome/`) transforms ResearchMind's initial pre-upload view into a **sophisticated AI Research Workspace landing page**.

---

## 2. Key Architecture Decisions

### 1. Complete Removal of Initial Focus Prompt
- Removed `"RESEARCH FOCUS PROMPT"` heading and `"Explain the paper methodology and equations."` text input.
- Researchers simply upload their PDF, and the interactive research conversation begins when analyzing the paper inside the workspace.

### 2. Modular Component Tree
- `ResearchWelcome.tsx` — Main landing page orchestrator.
- `ResearchLogo.tsx` — Interactive logo with orbiting nodes and soft connection pulses.
- `FloatingResearchTools.tsx` — 7 floating capability cards (`Paper`, `Equation`, `Figure`, `Citation`, `Swarm`, `Knowledge`, `Experiment`) with GPU-accelerated `@keyframes floatSlow` animations.
- `PaperUpload.tsx` — Drag & drop upload card with hover highlight and 25MB validation.
- `ResearchBackground.tsx` — Ambient academic grid and radial background glow.
- `WelcomeStatus.tsx` — `● AI Research Workspace Ready` status badge.

### 3. Accessibility & Performance
- Full support for `prefers-reduced-motion: reduce`.
- GPU-accelerated CSS transforms (`translateY`) with 0 heavy WebGL/canvas CPU loops.
