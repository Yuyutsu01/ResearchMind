"use client";

import React from "react";

export const HeroContent: React.FC = () => {
  return (
    <div className="flex flex-col items-center text-center gap-4 max-w-3xl z-10 select-text">
      {/* Primary Brand Title */}
      <h1 className="font-header font-extrabold text-5xl sm:text-6xl md:text-7xl tracking-tight text-white leading-none">
        Research<span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">Mind</span>
      </h1>

      {/* Hero Welcome Message */}
      <div className="flex flex-col items-center gap-1">
        <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white tracking-tight">
          Welcome, <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">Researcher.</span>
        </h2>
        <p className="text-xl sm:text-2xl md:text-3xl font-light text-slate-300 tracking-wide">
          What's on your mind today?
        </p>
      </div>
    </div>
  );
};
