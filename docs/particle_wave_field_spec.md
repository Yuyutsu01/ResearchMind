# ResearchMind Two-Symmetrical Particle Wave System Specification

## 1. Executive Summary

This component (**[ParticleWaveField.tsx](file:///c:/Users/shiva/OneDrive/Desktop/projects/ResearchMind/frontend/src/components/research-welcome/ParticleWaveField.tsx)**) implements **two symmetrical smooth particle wave fields** (left & right) with **stable wave geometry** and **precise single-particle cursor glow interaction**.

---

## 2. Layout & Mathematical Architecture

### 1. Left Wave Field (0% → 35% Viewport Width)
- 14 smooth wave streamlines rendered in blue, cyan, and electric blue (`#38bdf8`, `#3b82f6`, `#60a5fa`, `#0ea5e9`).
- Fade-out opacity curve towards the inner 35% margin.

### 2. Right Wave Field (65% → 100% Viewport Width)
- 14 smooth wave streamlines rendered in blue, violet, and purple (`#818cf8`, `#c084fc`, `#a855f7`, `#6366f1`).
- Fade-out opacity curve towards the inner 65% margin.

### 3. Clean Center Negative Space (35% → 65% Viewport Width)
- Zero particles spawned in the center zone to preserve clean visual contrast for the hero title and upload card.

### 4. Precise Single-Particle Cursor Glow
- Interaction Radius: $R = 28\text{px}$.
- Mouse movement does **not** push, deform, or warp the wave geometry.
- Highlight interpolation per animation frame:
  $$\text{particle.highlight} += (\text{targetHighlight} - \text{particle.highlight}) \times 0.18$$
- When cursor touches a particle, it smoothly glows bright cyan/white. When cursor leaves, it smoothly fades back to normal.
