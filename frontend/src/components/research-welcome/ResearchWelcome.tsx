"use client";

import React from "react";
import { ParticleWaveField } from "./ParticleWaveField";
import { ResearchBrand } from "./ResearchBrand";
import { HeroContent } from "./HeroContent";
import { ResearchUpload } from "./ResearchUpload";

interface ResearchWelcomeProps {
  onFileSelect: (file: File) => void;
  uploading: boolean;
  error?: string | null;
}

export const ResearchWelcome: React.FC<ResearchWelcomeProps> = ({ onFileSelect, uploading, error }) => {
  return (
    <main className="relative min-h-screen w-screen bg-[#04060f] flex flex-col justify-between p-6 overflow-x-hidden overflow-y-auto select-text font-sans">
      {/* 1. Two-Symmetrical Smooth Particle Wave Background */}
      <ParticleWaveField />

      {/* 2. Top Navigation Bar (Branding Left) */}
      <header className="w-full max-w-7xl mx-auto flex items-center justify-between z-20 flex-shrink-0 py-2">
        <ResearchBrand />
      </header>

      {/* 3. Center Hero & Upload Ecosystem Container */}
      <div className="w-full max-w-4xl mx-auto flex flex-col items-center justify-center text-center gap-6 z-20 my-auto py-8">
        <HeroContent />
        <ResearchUpload onFileSelect={onFileSelect} uploading={uploading} error={error} />
      </div>

      {/* 4. Footer Space Reservation */}
      <footer className="w-full max-w-7xl mx-auto flex justify-center text-[10px] text-slate-600 font-mono py-2 z-20 select-none">
        <span>ResearchMind AI Workspace • Version 2.0</span>
      </footer>
    </main>
  );
};
