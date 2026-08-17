# ResearchMind Continuous Flowing Wave Streams Architecture

## 1. Executive Summary

This component (**[ParticleWaveField.tsx](file:///c:/Users/shiva/OneDrive/Desktop/projects/ResearchMind/frontend/src/components/research-welcome/ParticleWaveField.tsx)**) implements **16 continuous flowing particle wave streams** across the entire viewport, using **center opacity gradient masking** to preserve 100% typography readability and **precise single-particle cursor glow interaction**.

---

## 2. Mathematical Wave Stream Models

### 1. Continuous Wave Flow Equations
- 16 distinct wave streams initialized from $y_{\text{base}} = 6\%$ to $88\%$ viewport height.
- Each particle advances continuously along progress parameter $p \in [0.0, 1.0]$:
  $$p \leftarrow (p + \text{speed}) \pmod{1.0}$$
  $$x = p \cdot \text{width}$$
  $$y(x, t) = y_{\text{base}} + A_1 \sin(f_1 x + t \cdot s_1 + \phi_1) + A_2 \cos(f_2 x - t \cdot s_2 + \phi_2)$$

### 2. Smooth Center Opacity Gradient Masking
- Particles flow continuously across the entire screen (including center).
- Opacity mask formula:
  $$\text{normX} = \frac{x}{\text{width}}$$
  $$\text{centerDist} = | \text{normX} - 0.5 | \times 2$$
  $$\text{opacityMask} = 0.20 + 0.80 \times (\text{centerDist})^{1.8}$$
- Result: 100% opacity on left & right flanks, smoothly dimming to 20% behind center content.

### 3. Precise Single-Particle Cursor Glow
- Interaction Radius: $R = 32\text{px}$.
- Zero wave deformation or displacement.
- Exponential highlight interpolation:
  $$\text{particle.highlight} += (\text{targetHighlight} - \text{particle.highlight}) \times 0.20$$
