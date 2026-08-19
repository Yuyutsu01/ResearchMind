# ResearchMind Dynamic Curved Wave Trajectory Physics

## 1. Executive Summary

This component (**[ParticleWaveField.tsx](file:///c:/Users/shiva/OneDrive/Desktop/projects/ResearchMind/frontend/src/components/research-welcome/ParticleWaveField.tsx)**) implements **28 distinct high-amplitude sinusoidal wave streams** ($A_1 \approx 45\text{px}-85\text{px}$) with per-frame dynamic $y = f(x, t)$ curve evaluation, eliminating horizontal scan-line artifacts.

---

## 2. Dynamic Trajectory Physics & Curves

### 1. Per-Frame $y = f(x, t)$ Re-Evaluation
- As particle progress $p \in [0.0, 1.0]$ advances, horizontal position $x$ updates, and vertical position $y$ is recalculated dynamically on every animation frame:
  $$y(x, t) = y_{\text{base}} + A_1 \sin(f_1 x + t \cdot s_1 + \phi_1) + A_2 \sin(f_2 x - t \cdot s_2 + \phi_2)$$
- Primary Amplitude: $A_1 = 45\text{px} - 85\text{px}$ (large crests and troughs).
- Secondary Amplitude: $A_2 = 18\text{px} - 36\text{px}$ (organic variation).

### 2. Left & Right Flank Composition
- Left Flank ($x < 48\%$): 14 wave streams rendered in cyan/electric blue (`#00f0ff`, `#38bdf8`, `#3b82f6`).
- Right Flank ($x > 52\%$): 14 wave streams rendered in violet/purple (`#818cf8`, `#c084fc`, `#a855f7`).

### 3. Center Opacity Gradient Mask
- Opacity mask formula:
  $$\text{centerDist} = \left| \frac{x}{\text{width}} - 0.5 \right| \times 2$$
  $$\text{opacityMask} = 0.15 + 0.85 \times (\text{centerDist})^{1.6}$$
- Result: 100% opacity at screen flanks, smoothly dimming to ~15% behind center content.

### 4. Single-Particle Cursor Glow (No Wave Deformation)
- Interaction radius $R = 25\text{px}$.
- Highlight exponential smoothing:
  $$\text{highlight} \leftarrow \text{highlight} + (\text{target} - \text{highlight}) \times 0.22$$
