# ResearchMind Structured Particle Flow Field Architecture

## 1. Executive Summary

This architecture rebuilds **[ParticleField.tsx](file:///c:/Users/shiva/OneDrive/Desktop/projects/ResearchMind/frontend/src/components/research-welcome/ParticleField.tsx)** from random starfield dots into a **procedural mathematical vector flow field** matching the visual reference image.

---

## 2. Mathematical Vector Field Models

### 1. Left-Side Wave Streamlines
- **Streamlines Count**: 18 layered wave channels spanning the left flank.
- **Wave Motion Equation**:
  $$y(x, t) = y_{\text{base}} + A \cdot \sin(x \cdot f + t \cdot s + \phi)$$
- **Particle Flow**: Particles travel horizontally along streamlines from left to right, returning to the left border upon exiting.

### 2. Right-Side Logarithmic Spiral Vortex
- **Vortex Center**: Positioned at ~82% viewport width, ~50% viewport height.
- **Spiral Arm Motion**: 8 concentric spiral arms with 55 particles per arm.
- **Parametric Spiral Equation**:
  $$x(\theta, t) = x_{\text{vortex}} + r(t) \cdot \cos(\theta(t))$$
  $$y(\theta, t) = y_{\text{vortex}} + r(t) \cdot \sin(\theta(t))$$
  $$r(t) = r_{\text{base}} + 8 \cdot \sin(0.8 \cdot t + 2 \cdot \theta)$$

### 3. Cursor Force Field & Localized Deformation
- Mouse position $(x_{\text{mouse}}, y_{\text{mouse}})$ acts as a dynamic force field inside $R = 130\text{px}$.
- Computes tangential swirl vector $\vec{v}_{\text{swirl}}$ and smooth repulsion displacement, blending back to the underlying vector field when the cursor leaves.

### 4. Center Negative Space
- Particle density is suppressed in the center ($0.35 < \text{normX} < 0.65$) to ensure maximum readability for hero text and upload card.
