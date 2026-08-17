"use client";

import React, { useState, useRef } from "react";
import { Upload, ArrowUp, AlertCircle, RefreshCw } from "lucide-react";

interface ResearchUploadProps {
  onFileSelect: (file: File) => void;
  uploading: boolean;
  error?: string | null;
}

export const ResearchUpload: React.FC<ResearchUploadProps> = ({ onFileSelect, uploading, error }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndProcess(e.dataTransfer.files[0]);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndProcess(e.target.files[0]);
    }
  };

  const validateAndProcess = (file: File) => {
    if (file.type !== "application/pdf" && !file.name.endsWith(".pdf")) {
      alert("Please select a valid PDF research paper.");
      return;
    }
    if (file.size > 25 * 1024 * 1024) {
      alert("File size exceeds 25 MB limit.");
      return;
    }
    onFileSelect(file);
  };

  return (
    <div className="w-full max-w-xl mx-auto relative z-20 my-2">
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,application/pdf"
        onChange={handleInputChange}
        className="hidden"
      />

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !uploading && fileInputRef.current?.click()}
        className={`relative overflow-hidden rounded-2xl border transition-all duration-300 cursor-pointer p-8 sm:p-10 flex flex-col items-center justify-center gap-4 text-center group backdrop-blur-xl ${
          isDragOver
            ? "border-blue-400 bg-blue-600/15 shadow-[0_0_40px_rgba(59,130,246,0.35)] scale-[1.01]"
            : "border-blue-500/20 bg-[#0a0f1d]/75 hover:border-blue-400/50 hover:bg-[#0e1529]/85 shadow-[0_10px_40px_rgba(0,0,0,0.6)]"
        }`}
      >
        {/* Top/Bottom Light Streak Accents */}
        <div className="absolute top-0 left-1/4 right-1/4 h-[1px] bg-gradient-to-r from-transparent via-blue-400 to-transparent opacity-75" />
        <div className="absolute bottom-0 left-1/4 right-1/4 h-[1px] bg-gradient-to-r from-transparent via-purple-400 to-transparent opacity-50" />

        {uploading ? (
          <div className="flex flex-col items-center gap-3 py-4">
            <RefreshCw className="w-8 h-8 text-blue-400 animate-spin" />
            <span className="text-sm font-semibold text-white">Ingesting Research Paper...</span>
            <span className="text-xs text-slate-400 font-mono">Parsing layout structure & spatial index...</span>
          </div>
        ) : (
          <>
            {/* Upload Icon Box matching visual reference */}
            <div className="w-12 h-12 rounded-xl bg-blue-600/15 border border-blue-500/30 flex items-center justify-center text-blue-400 group-hover:scale-110 group-hover:bg-blue-600/25 transition-all shadow-[0_0_15px_rgba(59,130,246,0.2)]">
              <ArrowUp className="w-6 h-6 stroke-[2]" />
            </div>

            {/* Upload Titles */}
            <div className="flex flex-col gap-1">
              <h3 className="text-base sm:text-lg font-bold text-white tracking-tight">
                {isDragOver ? "Drop your research paper here" : "Upload your research paper"}
              </h3>
              <p className="text-xs sm:text-sm text-slate-400">
                Drag & drop your PDF here, or{" "}
                <span className="text-blue-400 font-semibold group-hover:underline">browse files</span>
              </p>
            </div>

            {/* Pill Tag */}
            <div className="flex items-center gap-2 text-[10px] text-slate-500 uppercase tracking-widest font-mono bg-white/5 border border-white/5 px-3 py-1 rounded-full mt-1">
              <span>PDF FORMAT</span>
              <span>•</span>
              <span>UP TO 25 MB</span>
            </div>
          </>
        )}
      </div>

      {/* Error Alert */}
      {error && (
        <div className="mt-4 bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded-xl text-xs flex items-start gap-2 animate-in fade-in">
          <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
          <span className="leading-relaxed">{error}</span>
        </div>
      )}
    </div>
  );
};
