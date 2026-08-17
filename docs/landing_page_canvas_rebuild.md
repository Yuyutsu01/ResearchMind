# ResearchMind Landing Page Canvas Rebuild Architecture

## 1. Executive Summary

This rebuild reproduces the exact visual language, spacing, proportions, dark navy palette (`#04060f`), hero layout, glassmorphic upload card, status badges, feature capability pills, and **cursor-reactive HTML5 Canvas particle wave mechanics** specified by the visual reference image.

---

## 2. Key Architecture & Component Tree

`frontend/src/components/research-welcome/`
- **`ResearchWelcome.tsx`** — Landing page layout orchestrator assembling top bar, hero, particle field, upload card, and capability pills.
- **`ParticleField.tsx`** — High-performance 60 FPS HTML5 Canvas engine. Renders flowing vector particle waves with mouse-reactive repulsion, cursor glow, and zero React state re-renders. Includes `prefers-reduced-motion` support.
- **`ResearchBrand.tsx`** — Top-left wordmark: `Research` (clean white) + `Mind` (gradient from `#60a5fa` blue to `#c084fc` purple).
- **`StatusPills.tsx`** — Top-center soundwave glassmorphic badge (`|||| Intelligent Research. Deeper Understanding.`) and top-right status pill (`● AI Research Workspace`).
- **`HeroContent.tsx`** — Hero title and subheadings matching reference hierarchy.
- **`ResearchUpload.tsx`** — Translucent glassmorphic card (`#0a0f1d`) with top/bottom glowing light streaks, drag & drop, and 25MB PDF validation.
- **`CapabilityPills.tsx`** — 5 capability pills (📄 `Paper Understanding`, ∑ `Mathematical Reasoning`, 📊 `Figure & Table Analysis`, 🔗 `Citation Intelligence`, 🧠 `AI Agent Swarm`).

---

## 3. Verification & Safety Checks
- **Zero Backend / Swarm Changes**: PDF parser, PDF.js text layer, Swarm agents, AI runtime, Redis, PostgreSQL, and upload API are unchanged.
- **Zero Static Screenshot Hacks**: The page is built with 100% interactive HTML5, CSS3, SVG, Canvas, and React components.
