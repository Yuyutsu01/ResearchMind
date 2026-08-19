"use client";

import React, { useEffect, useRef } from "react";

interface WaveParticle {
  side: "left" | "right";
  streamId: number;
  x: number;
  y: number;
  baseY: number;
  progress: number; // 0.0 to 1.0 along the wave span
  speed: number;
  amp1: number;
  freq1: number;
  speed1: number;
  phase1: number;
  amp2: number;
  freq2: number;
  speed2: number;
  phase2: number;
  size: number;
  alpha: number;
  color: string;
  highlight: number; // 0.0 to 1.0 smooth cursor glow state
  isHero: boolean; // large bloom "signature" dot
  isSparkle: boolean; // small breakaway trailing dot
}

export const ParticleWaveField: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const mouseRef = useRef<{ x: number; y: number; active: boolean }>({ x: -1000, y: -1000, active: false });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const leftColors = ["#00f0ff", "#38bdf8", "#3b82f6", "#60a5fa", "#0ea5e9"];
    const rightColors = ["#818cf8", "#c084fc", "#a855f7", "#7c3aed", "#6366f1"];

    const particles: WaveParticle[] = [];

    // Helper: Initialize wave streams with edge-weighted density (dense at edges, tapering to center)
    const initParticles = () => {
      particles.length = 0;

      const streamsPerSide = 14;
      const leftMaxX = width * 0.48;
      const rightMinX = width * 0.52;

      const buildSide = (side: "left" | "right", colors: string[]) => {
        for (let s = 0; s < streamsPerSide; s++) {
          const baseY = height * 0.08 + (s / (streamsPerSide - 1)) * (height * 0.84);

          const amp1 = 45 + Math.random() * 40;
          const freq1 = 0.005 + Math.random() * 0.004;
          const speed1 = 0.8 + Math.random() * 0.6;
          const phase1 = Math.random() * Math.PI * 2;

          const amp2 = 18 + Math.random() * 18;
          const freq2 = 0.01 + Math.random() * 0.006;
          const speed2 = 0.5 + Math.random() * 0.5;
          const phase2 = Math.random() * Math.PI * 2;

          const particlesInStream = 40;
          // Per-stream shared phase offset keeps each stream reading as one coherent ribbon
          const streamPhaseOffset = Math.random() * 0.015;

          for (let p = 0; p < particlesInStream; p++) {
            // Progress skews particles toward the outer edge of the span (density taper toward center)
            const linear = p / particlesInStream;
            const edgeWeighted =
              side === "left"
                ? 1 - Math.pow(1 - linear, 1.6) // denser near 0 (outer/left edge)
                : Math.pow(linear, 1.6); // denser near 1 (outer/right edge)

            const progress = edgeWeighted + streamPhaseOffset + (Math.random() - 0.5) * 0.01;
            const speed = 0.0007 + Math.random() * 0.0006;
            const size = 1.0 + Math.random() * 1.5;
            const alpha = 0.35 + Math.random() * 0.4;
            const color = colors[Math.floor(Math.random() * colors.length)];

            particles.push({
              side,
              streamId: s,
              x: side === "left" ? progress * leftMaxX : rightMinX + progress * (width - rightMinX),
              y: baseY,
              baseY,
              progress: Math.max(0, Math.min(1, progress)),
              speed,
              amp1,
              freq1,
              speed1,
              phase1,
              amp2,
              freq2,
              speed2,
              phase2,
              size,
              alpha,
              color,
              highlight: 0,
              isHero: false,
              isSparkle: false,
            });
          }
        }
      };

      buildSide("left", leftColors);
      buildSide("right", rightColors);

      // HERO BLOOM DOTS: a handful of large, brighter signature particles per side (matches
      // the big glowing cyan/purple dots in the reference art)
      const heroCountPerSide = 4;
      for (let i = 0; i < heroCountPerSide; i++) {
        const side: "left" | "right" = i % 2 === 0 ? "left" : "right"; // placeholder, overwritten below
      }
      const addHero = (side: "left" | "right", colors: string[]) => {
        for (let i = 0; i < heroCountPerSide; i++) {
          const progress = 0.05 + Math.random() * 0.35; // sit near the outer edge, matches reference
          const baseY = height * (0.1 + Math.random() * 0.7);
          particles.push({
            side,
            streamId: -1,
            x: side === "left" ? progress * leftMaxX : rightMinX + progress * (width - rightMinX),
            y: baseY,
            baseY,
            progress,
            speed: 0.00025 + Math.random() * 0.0002,
            amp1: 30 + Math.random() * 25,
            freq1: 0.004 + Math.random() * 0.003,
            speed1: 0.4 + Math.random() * 0.3,
            phase1: Math.random() * Math.PI * 2,
            amp2: 10 + Math.random() * 10,
            freq2: 0.008 + Math.random() * 0.004,
            speed2: 0.3 + Math.random() * 0.2,
            phase2: Math.random() * Math.PI * 2,
            size: 5 + Math.random() * 4, // 5px to 9px bloom dots
            alpha: 0.85 + Math.random() * 0.15,
            color: colors[Math.floor(Math.random() * colors.length)],
            highlight: 0,
            isHero: true,
            isSparkle: false,
          });
        }
      };
      addHero("left", leftColors);
      addHero("right", rightColors);

      // TRAILING SPARKLE CLUSTERS: small breakaway dots near a couple of random points per side,
      // scattered diagonally off the main flow (matches the loose sparkle cluster near the cursor
      // glow in the reference art)
      const addSparkleCluster = (side: "left" | "right", colors: string[]) => {
        const clusters = 2;
        for (let c = 0; c < clusters; c++) {
          const anchorProgress = 0.15 + Math.random() * 0.5;
          const anchorY = height * (0.15 + Math.random() * 0.6);
          const anchorX = side === "left" ? anchorProgress * leftMaxX : rightMinX + anchorProgress * (width - rightMinX);

          const sparklesInCluster = 10;
          for (let i = 0; i < sparklesInCluster; i++) {
            const offsetX = (Math.random() - 0.5) * 140;
            const offsetY = (Math.random() - 0.5) * 100 - i * 6; // slight diagonal drift
            particles.push({
              side,
              streamId: -2,
              x: anchorX + offsetX,
              y: anchorY + offsetY,
              baseY: anchorY + offsetY,
              progress: anchorProgress,
              speed: 0.0004 + Math.random() * 0.0004,
              amp1: 8 + Math.random() * 10,
              freq1: 0.01 + Math.random() * 0.01,
              speed1: 0.6 + Math.random() * 0.4,
              phase1: Math.random() * Math.PI * 2,
              amp2: 4 + Math.random() * 6,
              freq2: 0.02,
              speed2: 0.4,
              phase2: Math.random() * Math.PI * 2,
              size: 0.6 + Math.random() * 1.2,
              alpha: 0.25 + Math.random() * 0.4,
              color: colors[Math.floor(Math.random() * colors.length)],
              highlight: 0,
              isHero: false,
              isSparkle: true,
            });
          }
        }
      };
      addSparkleCluster("left", leftColors);
      addSparkleCluster("right", rightColors);
    };

    initParticles();

    const handleMouseMove = (e: MouseEvent) => {
      mouseRef.current = { x: e.clientX, y: e.clientY, active: true };
    };

    const handleMouseLeave = () => {
      mouseRef.current.active = false;
    };

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
      initParticles();
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseleave", handleMouseLeave);
    window.addEventListener("resize", handleResize);

    let time = 0;

    const render = () => {
      time += 0.014;
      ctx.clearRect(0, 0, width, height);

      // Deep dark navy base background gradient
      const bgGlow = ctx.createRadialGradient(width / 2, height / 2, 80, width / 2, height / 2, width * 0.75);
      bgGlow.addColorStop(0, "#050814");
      bgGlow.addColorStop(0.5, "#070c20");
      bgGlow.addColorStop(1, "#04060f");
      ctx.fillStyle = bgGlow;
      ctx.fillRect(0, 0, width, height);

      const mouse = mouseRef.current;
      // Wider, softer cursor glow radius so the halo effect actually reads (was 25px, too tight)
      const interactionRadius = 90;

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];

        if (!prefersReducedMotion) {
          p.progress += p.speed;
          if (p.progress >= 1.0) {
            p.progress -= 1.0;
          }
        }

        // Horizontal position — sparkle clusters stay locally anchored, main streams travel the full span
        if (!p.isSparkle) {
          const leftMaxX = width * 0.48;
          const rightMinX = width * 0.52;
          p.x = p.side === "left" ? p.progress * leftMaxX : rightMinX + p.progress * (width * 0.48);
        }

        // Curve trajectory (dual-sine composition)
        p.y = p.baseY +
          Math.sin(p.x * p.freq1 + time * p.speed1 + p.phase1) * p.amp1 +
          Math.sin(p.x * p.freq2 - time * p.speed2 + p.phase2) * p.amp2;

        // Center opacity mask: dim particles approaching the middle of the screen
        const normX = p.x / width;
        const centerDist = Math.abs(normX - 0.5) * 2;
        const opacityMask = 0.12 + 0.88 * Math.pow(centerDist, 1.6);

        // Cursor glow interaction, softened falloff (quadratic ease instead of linear)
        let targetHighlight = 0;
        if (mouse.active) {
          const dx = mouse.x - p.x;
          const dy = mouse.y - p.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < interactionRadius) {
            const t = 1 - dist / interactionRadius;
            targetHighlight = t * t;
          }
        }
        p.highlight += (targetHighlight - p.highlight) * 0.22;

        const renderedSize = p.size + p.highlight * 2.2;
        const baseAlpha = p.isHero ? p.alpha : p.alpha * opacityMask;
        const renderedAlpha = Math.min(1.0, baseAlpha + p.highlight * 0.8);

        ctx.save();
        ctx.globalAlpha = renderedAlpha;
        ctx.fillStyle = p.highlight > 0.1 ? "#e0f2fe" : p.color;
        ctx.shadowColor = p.highlight > 0.1 ? "#38bdf8" : p.color;
        ctx.shadowBlur = p.isHero
          ? renderedSize * 3.5 + p.highlight * 18
          : renderedSize * 2.5 + p.highlight * 14;

        ctx.beginPath();
        ctx.arc(p.x, p.y, renderedSize, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseleave", handleMouseLeave);
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className="absolute inset-0 w-full h-full pointer-events-none select-none z-0"
    />
  );
};
