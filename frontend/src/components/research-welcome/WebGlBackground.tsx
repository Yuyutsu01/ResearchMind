"use client";

import React, { useEffect, useRef } from "react";
import * as THREE from "three";

export const WebGlBackground: React.FC = () => {
  const halftoneCanvasRef = useRef<HTMLCanvasElement | null>(null);

  // WebGL GLSL Shader Halftone Matrix Background Initialization
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

    const startTime = performance.now();
    let animationFrameId: number;
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      material.uniforms.time.value = (performance.now() - startTime) * 0.001;
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
      {/* WebGL Halftone Dot Matrix Background Layer */}
      <canvas ref={halftoneCanvasRef} className="absolute inset-0 w-full h-full opacity-60" />
    </div>
  );
};
