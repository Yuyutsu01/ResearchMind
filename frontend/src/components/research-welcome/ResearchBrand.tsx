"use client";

import React from "react";

export const ResearchBrand: React.FC = () => {
  return (
    <div className="flex items-center select-none cursor-pointer">
      {/* ResearchMind Text Wordmark Only */}
      <span className="font-header font-bold text-lg tracking-tight">
        <span className="text-white">Research</span>
        <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent ml-0.5">Mind</span>
      </span>
    </div>
  );
};
