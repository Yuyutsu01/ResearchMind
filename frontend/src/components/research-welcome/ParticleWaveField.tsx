"use client";

import React, { useEffect, useRef } from "react";

interface WaveStreamParticle {
  lineIndex: number;
  progress: number; // 0.0 to 1.0 along the wave line
  speed: number;    // travel speed along wave
  baseY: number;
  amp1: number;
  freq1: number;
  speed1: number;
  phase1: number;
  amp2: number;
  freq2: number;
  speed2: number;
  phase2: number;
  baseSize: number;
  baseAlpha: number;
  color: string;
  highlight: number; // 0.0 to 1.0 smooth cursor glow state
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

    // Palette: Cyan/Blue on left, transitioning to Violet/Purple on right
    const particles: WaveStreamParticle[] = [];

    // Helper: Initialize 16 continuous flowing wave streams across the viewport
    const initParticles = () => {
      particles.length = 0;

      const numStreams = 16;
      const particlesPerStream = 50; // Total ~800 particles in continuous flow

      for (let s = 0; s < numStreams; s++) {
        const baseY = (height * 0.06) + (s / (numStreams - 1)) * (height * 0.88);
        const streamAmp1 = Math.random() * 22 + 14;
        const streamFreq1 = Math.random() * 0.003 + 0.002;
        const streamSpeed1 = Math.random() * 1.2 + 0.6;
        const streamPhase1 = Math.random() * Math.PI * 2;

        const streamAmp2 = Math.random() * 12 + 6;
        const streamFreq2 = Math.random() * 0.006 + 0.003;
        const streamSpeed2 = Math.random() * 0.8 + 0.4;
        const streamPhase2 = Math.random() * Math.PI * 2;

        for (let p = 0; p < particlesPerStream; p++) {
          const progress = (p / particlesPerStream) + (Math.random() * 0.015);
          const speed = (Math.random() * 0.0008 + 0.0005);
          const baseSize = Math.random() * 1.5 + 0.9;
          const baseAlpha = Math.random() * 0.35 + 0.35;

          // Color calculation based on initial x position
          const normX = progress;
          let color = "#38bdf8"; // Cyan/Blue
          if (normX > 0.6) color = "#c084fc"; // Purple
          else if (normX > 0.35) color = "#818cf8"; // Indigo

          particles.push({
            lineIndex: s,
            progress,
            speed,
            baseY,
            amp1: streamAmp1,
            freq1: streamFreq1,
            speed1: streamSpeed1,
            phase1: streamPhase1,
            amp2: streamAmp2,
            freq2: streamFreq2,
            speed2: streamSpeed2,
            phase2: streamPhase2,
            baseSize,
            baseAlpha,
            color,
            highlight: 0,
          });
        }
      }
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
      time += 0.012;
      ctx.clearRect(0, 0, width, height);

      // Deep dark navy base background gradient
      const bgGlow = ctx.createRadialGradient(width / 2, height / 2, 80, width / 2, height / 2, width * 0.75);
      bgGlow.addColorStop(0, "#050814");
      bgGlow.addColorStop(0.5, "#070c20");
      bgGlow.addColorStop(1, "#04060f");
      ctx.fillStyle = bgGlow;
      ctx.fillRect(0, 0, width, height);

      const mouse = mouseRef.current;
      const interactionRadius = 32; // Precise interaction radius

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];

        if (!prefersReducedMotion) {
          // Advance progress continuously along wave stream
          p.progress += p.speed;
          if (p.progress >= 1.0) {
            p.progress -= 1.0;
          }
        }

        // Calculate exact (x, y) coordinates along dual-frequency sine wave path
        const x = p.progress * width;
        const waveY = p.baseY +
          Math.sin(x * p.freq1 + time * p.speed1 + p.phase1) * p.amp1 +
          Math.cos(x * p.freq2 - time * p.speed2 + p.phase2) * p.amp2;

        const y = waveY;

        // CENTER OPACITY MASK: Smoothly dim particles behind center hero content (35% to 65% width)
        const normX = x / width;
        const centerDist = Math.abs(normX - 0.5) * 2; // 0.0 at center, 1.0 at screen edges
        const opacityMask = 0.20 + 0.80 * Math.pow(centerDist, 1.8); // 20% opacity at center, 100% at edges

        // Dynamic color transition across the wave width
        let currentColor = "#38bdf8"; // Left cyan
        if (normX > 0.65) currentColor = "#c084fc"; // Right purple
        else if (normX > 0.35) currentColor = "#818cf8"; // Mid indigo

        // PRECISE SINGLE-PARTICLE CURSOR GLOW INTERACTION
        let targetHighlight = 0;
        if (mouse.active) {
          const dx = mouse.x - x;
          const dy = mouse.y - y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < interactionRadius) {
            targetHighlight = 1 - (dist / interactionRadius);
          }
        }

        // Smooth exponential interpolation for cursor highlight state
        p.highlight += (targetHighlight - p.highlight) * 0.20;

        // Rendered particle dimensions & alpha
        const renderedSize = p.baseSize + p.highlight * 2.5;
        const renderedAlpha = Math.min(1.0, (p.baseAlpha * opacityMask) + p.highlight * 0.75);

        ctx.save();
        ctx.globalAlpha = renderedAlpha;
        ctx.fillStyle = p.highlight > 0.1 ? "#e0f2fe" : currentColor;
        ctx.shadowColor = p.highlight > 0.1 ? "#38bdf8" : currentColor;
        ctx.shadowBlur = renderedSize * 2 + p.highlight * 16;

        ctx.beginPath();
        ctx.arc(x, y, renderedSize, 0, Math.PI * 2);
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
