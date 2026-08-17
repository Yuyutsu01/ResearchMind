"use client";

import React from "react";
import { Sparkles } from "lucide-react";

export const ResearchBrand: React.FC = () => {
  return (
    <div className="flex items-center gap-2 select-none cursor-pointer">
      <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center text-white shadow-[0_0_12px_rgba(59,130,246,0.5)]">
        <Sparkles className="w-4 h-4 text-white" />
      </div>
      <span className="font-header font-bold text-lg tracking-tight">
        <span className="text-white">Research</span>
        <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent ml-0.5">Mind</span>
      </span>
    </div>
  );
};
