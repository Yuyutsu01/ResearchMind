"use client";

import React, { useState, useEffect, useRef } from "react";
import { computePosition, flip, shift, offset } from "@floating-ui/dom";
import { Sparkles, Calculator, BookOpen, Eye, GitCompare, ExternalLink, Send, X, Bookmark } from "lucide-react";

interface FloatingToolbarProps {
  range: Range | null;
  targetRect?: DOMRect | null;
  selectedText: string;
  selectedType?: string | null;
  onAction: (actionType: string, customPrompt?: string) => void;
  onClose: () => void;
}

export const FloatingToolbar: React.FC<FloatingToolbarProps> = ({
  range,
  targetRect,
  selectedText,
  selectedType,
  onAction,
  onClose,
}) => {
  const toolbarRef = useRef<HTMLDivElement>(null);
  const [showAskModal, setShowAskModal] = useState(false);
  const [customPrompt, setCustomPrompt] = useState("");
  const [positionStyle, setPositionStyle] = useState<React.CSSProperties>({
    position: "fixed",
    top: -9999,
    left: -9999,
  });

  // Calculate position using Floating UI
  useEffect(() => {
    if (!toolbarRef.current) return;

    let rect = targetRect;
    if (!rect && range) {
      rect = range.getBoundingClientRect();
    }

    if (!rect || (rect.width === 0 && rect.height === 0)) return;

    // Virtual element reference for Floating UI
    const virtualEl = {
      getBoundingClientRect: () => rect!,
    };

    computePosition(virtualEl, toolbarRef.current, {
      placement: "top",
      middleware: [offset(10), flip(), shift({ padding: 12 })],
    }).then(({ x, y }) => {
      setPositionStyle({
        position: "fixed",
        left: `${x}px`,
        top: `${y}px`,
      });
    });
  }, [range, targetRect]);

  const handleAskSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customPrompt.trim()) return;
    onAction("Ask", customPrompt);
    setShowAskModal(false);
    setCustomPrompt("");
  };

  return (
    <div
      ref={toolbarRef}
      style={positionStyle}
      className="z-50 animate-in fade-in zoom-in-95 duration-100 select-none"
    >
      {!showAskModal ? (
        <div className="bg-[#18181b]/95 backdrop-blur-md border border-blue-500/30 shadow-[0_0_20px_rgba(59,130,246,0.25)] rounded-xl p-1.5 flex items-center gap-1">
          {/* Action: Explain */}
          <button
            onClick={() => onAction("Explain")}
            className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider px-2.5 py-1.5 rounded-lg bg-blue-500/10 hover:bg-blue-600 text-blue-300 hover:text-white transition-all border border-blue-500/20"
            title="Explain with Swarm AI"
          >
            <Sparkles className="w-3.5 h-3.5 text-blue-400" />
            <span>Explain</span>
          </button>

          {/* Action: Math */}
          <button
            onClick={() => onAction("Math")}
            className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider px-2.5 py-1.5 rounded-lg bg-white/5 hover:bg-purple-600 text-slate-300 hover:text-white transition-all border border-white/5"
            title="Deconstruct Equation & Math"
          >
            <Calculator className="w-3.5 h-3.5 text-purple-400" />
            <span>Math</span>
          </button>

          {/* Action: Background */}
          <button
            onClick={() => onAction("Background")}
            className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider px-2.5 py-1.5 rounded-lg bg-white/5 hover:bg-emerald-600 text-slate-300 hover:text-white transition-all border border-white/5"
            title="Provide Literature Background"
          >
            <BookOpen className="w-3.5 h-3.5 text-emerald-400" />
            <span>Background</span>
          </button>

          {/* Action: Visualize */}
          <button
            onClick={() => onAction("Visual")}
            className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider px-2.5 py-1.5 rounded-lg bg-white/5 hover:bg-amber-600 text-slate-300 hover:text-white transition-all border border-white/5"
            title="Visualize Chart / Architecture"
          >
            <Eye className="w-3.5 h-3.5 text-amber-400" />
            <span>Visualize</span>
          </button>

          {/* Action: Compare */}
          <button
            onClick={() => onAction("Compare")}
            className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider px-2.5 py-1.5 rounded-lg bg-white/5 hover:bg-cyan-600 text-slate-300 hover:text-white transition-all border border-white/5"
            title="Compare with Related Works"
          >
            <GitCompare className="w-3.5 h-3.5 text-cyan-400" />
            <span>Compare</span>
          </button>

          {/* Action: Citation */}
          <button
            onClick={() => onAction("Citation")}
            className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider px-2.5 py-1.5 rounded-lg bg-white/5 hover:bg-rose-600 text-slate-300 hover:text-white transition-all border border-white/5"
            title="Lookup Citation & References"
          >
            <ExternalLink className="w-3.5 h-3.5 text-rose-400" />
            <span>Citation</span>
          </button>

          {/* Action: Save to Notebook */}
          <button
            onClick={() => onAction("Notebook")}
            className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider px-2.5 py-1.5 rounded-lg bg-white/5 hover:bg-indigo-600 text-slate-300 hover:text-white transition-all border border-white/5"
            title="Save Selection to Notebook"
          >
            <Bookmark className="w-3.5 h-3.5 text-indigo-400" />
            <span>Notebook</span>
          </button>

          {/* Action: Ask Custom Prompt */}
          <button
            onClick={() => setShowAskModal(true)}
            className="flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-all"
            title="Ask a custom question"
          >
            <span>Ask...</span>
          </button>

          <div className="w-[1px] h-4 bg-white/10 mx-0.5" />

          {/* Close toolbar */}
          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-white rounded hover:bg-white/10 transition-colors"
            title="Close toolbar"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      ) : (
        /* Custom Prompt Dialog */
        <form
          onSubmit={handleAskSubmit}
          className="bg-[#18181b]/95 backdrop-blur-md border border-blue-500/40 shadow-[0_0_25px_rgba(59,130,246,0.3)] rounded-xl p-2 flex items-center gap-2 w-80"
        >
          <input
            type="text"
            value={customPrompt}
            onChange={(e) => setCustomPrompt(e.target.value)}
            placeholder="Ask AI about this selection..."
            className="flex-1 bg-black/40 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            autoFocus
          />
          <button
            type="submit"
            className="p-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
          <button
            type="button"
            onClick={() => setShowAskModal(false)}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-white/10"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </form>
      )}
    </div>
  );
};
