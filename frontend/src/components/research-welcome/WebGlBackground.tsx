"use client";

import React, { useEffect, useRef } from "react";
import * as THREE from "three";

export const WebGlBackground: React.FC = () => {
  const linesCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const halftoneCanvasRef = useRef<HTMLCanvasElement | null>(null);

  // 1. WebGL 3D Lines Network Initialization
  useEffect(() => {
    const canvas = linesCanvasRef.current;
    if (!canvas) return;

    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);

    const resize = () => {
      if (!canvas.parentElement) return;
      const width = canvas.parentElement.clientWidth;
      const height = canvas.parentElement.clientHeight;
      renderer.setSize(width, height);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    };

    window.addEventListener("resize", resize);
    resize();

    camera.position.z = 4.5;

    const group = new THREE.Group();
    scene.add(group);

    // Subtle dark line network
    const material = new THREE.LineBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.45 });
    const particlesCount = 180;

    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particlesCount * 3);

    // Distribute nodes across 3D sphere volume
    for (let i = 0; i < particlesCount * 3; i += 3) {
      const r = 2.5;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);

      positions[i] = r * Math.sin(phi) * Math.cos(theta);
      positions[i + 1] = r * Math.sin(phi) * Math.sin(theta);
      positions[i + 2] = r * Math.cos(phi);
    }

    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));

    // Connect node pairs within distance threshold (distSq < 1.2)
    const index: number[] = [];
    for (let i = 0; i < particlesCount; i++) {
      for (let j = i + 1; j < particlesCount; j++) {
        const dx = positions[i * 3] - positions[j * 3];
        const dy = positions[i * 3 + 1] - positions[j * 3 + 1];
        const dz = positions[i * 3 + 2] - positions[j * 3 + 2];
        const distSq = dx * dx + dy * dy + dz * dz;
        if (distSq < 1.2) {
          index.push(i, j);
        }
      }
    }
    geometry.setIndex(index);

    const lines = new THREE.LineSegments(geometry, material);
    group.add(lines);

    let animationFrameId: number;
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      group.rotation.y += 0.0015;
      group.rotation.x += 0.0008;
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", resize);
      renderer.dispose();
      geometry.dispose();
      material.dispose();
    };
  }, []);

  // 2. WebGL GLSL Shader Halftone Matrix Initialization
  useEffect(() => {
    const canvas = halftoneCanvasRef.current;
    if (!canvas) return;

    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setClearColor(0x04060f, 1);
    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 10);

    const resize = () => {
      if (!canvas.parentElement) return;
      const width = Math.max(1, canvas.parentElement.clientWidth || window.innerWidth || 1);
      const height = Math.max(1, canvas.parentElement.clientHeight || window.innerHeight || 1);
      renderer.setSize(width, height, false);
      const aspect = width / height;
      camera.left = -aspect;
      camera.right = aspect;
      camera.bottom = -1;
      camera.top = 1;
      camera.updateProjectionMatrix();
    };

    window.addEventListener("resize", resize);
    resize();
    camera.position.z = 1;

    const gridSize = 22;
    const geometry = new THREE.BufferGeometry();
    const positions: number[] = [];
    const scales: number[] = [];

    for (let x = -gridSize; x <= gridSize; x++) {
      for (let y = -gridSize; y <= gridSize; y++) {
        positions.push(x * 0.15, y * 0.15, 0);
        scales.push(1);
      }
    }

    geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    geometry.setAttribute("scale", new THREE.Float32BufferAttribute(scales, 1));

    // Custom GLSL Shader Material for pulsating halftone matrix
    const material = new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 },
        color1: { value: new THREE.Color(0x38bdf8) }, // Electric Blue / Cyan
        color2: { value: new THREE.Color(0x818cf8) }  // Violet / Indigo
      },
      vertexShader: `
        attribute float scale;
        varying vec2 vUv;
        varying float vScale;
        uniform float time;
        
        void main() {
            vUv = position.xy;
            float dist = length(position.xy);
            float animatedScale = scale * (sin(dist * 6.0 - time * 2.5) * 0.5 + 0.5);
            vScale = animatedScale;
            
            gl_PointSize = animatedScale * 4.5; 
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        uniform vec3 color1;
        uniform vec3 color2;
        varying vec2 vUv;
        varying float vScale;
        
        void main() {
            vec2 coord = gl_PointCoord - vec2(0.5);
            if(length(coord) > 0.5) discard;
            
            vec3 finalColor = mix(color2, color1, (vUv.y + 1.0) * 0.5);
            gl_FragColor = vec4(finalColor, vScale * 0.45);
        }
      `,
      transparent: true
    });

    const points = new THREE.Points(geometry, material);
    scene.add(points);

    const clock = new THREE.Clock();
    let animationFrameId: number;
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      material.uniforms.time.value = clock.getElapsedTime();
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", resize);
      renderer.dispose();
      geometry.dispose();
      material.dispose();
    };
  }, []);

  return (
    <div className="absolute inset-0 w-full h-full pointer-events-none select-none z-0 overflow-hidden">
      {/* WebGL Halftone Dot Matrix Layer */}
      <canvas ref={halftoneCanvasRef} className="absolute inset-0 w-full h-full opacity-60" />
      {/* WebGL 3D Lines Network Layer */}
      <canvas ref={linesCanvasRef} className="absolute inset-0 w-full h-full opacity-75" />
    </div>
  );
};
