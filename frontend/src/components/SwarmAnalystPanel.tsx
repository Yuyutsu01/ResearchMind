"use client";

import React, { useState, useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ChevronDown, ChevronRight, GraduationCap, BookOpen, FlaskConical, Sparkles, Copy, Check } from "lucide-react";

interface SwarmAnalystPanelProps {
  markdownContent: string;
  selectedText: string;
  readingLevel: "Beginner" | "Undergraduate" | "Researcher";
  onLevelChange: (level: "Beginner" | "Undergraduate" | "Researcher") => void;
  isLoading: boolean;
  telemetry?: {
    cache?: string;
    redis_lookup_ms?: number;
    intent_router_ms?: number;
    context_builder_ms?: number;
    execution_ms?: number;
    ttft_ms?: number;
    total_ms?: number;
  };
}

export const SwarmAnalystPanel: React.FC<SwarmAnalystPanelProps> = ({
  markdownContent,
  selectedText,
  readingLevel,
  onLevelChange,
  isLoading,
  telemetry,
}) => {
  const [copied, setCopied] = useState(false);
  const [collapsedSections, setCollapsedSections] = useState<Record<string, boolean>>({});

  // Parse markdown content into collapsible sections based on `# Heading` anchors
  const sections = useMemo(() => {
    if (!markdownContent) return [];
    
    const lines = markdownContent.split("\n");
    const parsedSections: Array<{ id: string; title: string; content: string }> = [];
    let currentTitle = "Overview";
    let currentContent: string[] = [];

    for (const line of lines) {
      if (line.startsWith("# ")) {
        if (currentContent.length > 0 || currentTitle !== "Overview") {
          parsedSections.push({
            id: currentTitle.toLowerCase().replace(/[^a-z0-9]/g, "-"),
            title: currentTitle,
            content: currentContent.join("\n").trim(),
          });
        }
        currentTitle = line.replace("# ", "").trim();
        currentContent = [];
      } else {
        currentContent.push(line);
      }
    }

    if (currentContent.length > 0 || currentTitle !== "Overview") {
      parsedSections.push({
        id: currentTitle.toLowerCase().replace(/[^a-z0-9]/g, "-"),
        title: currentTitle,
        content: currentContent.join("\n").trim(),
      });
    }

    return parsedSections;
  }, [markdownContent]);

  const toggleSection = (sectionId: string) => {
    setCollapsedSections((prev) => ({
      ...prev,
      [sectionId]: !prev[sectionId],
    }));
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(markdownContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col h-full bg-[#18181b] text-slate-200 select-text overflow-hidden">
      {/* 1. Header & Reading-Level Adaptor Toggle */}
      <div className="flex-shrink-0 border-b border-white/10 p-3 bg-[#121212] select-none flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-xs font-bold text-blue-400">
            <Sparkles className="w-4 h-4" />
            <span>Swarm Analyst Intelligence</span>
          </div>

          <div className="flex items-center gap-2">
            {/* Developer Telemetry Timing Badge */}
            {telemetry && (
              <span
                className={`text-[8px] font-mono font-bold px-1.5 py-0.5 rounded border uppercase ${
                  telemetry.cache === "HIT"
                    ? "bg-green-500/20 text-green-400 border-green-500/30"
                    : "bg-blue-500/20 text-blue-400 border-blue-500/30"
                }`}
                title={`Redis: ${telemetry.redis_lookup_ms}ms | Intent: ${telemetry.intent_router_ms}ms | Context: ${telemetry.context_builder_ms}ms | TTFT: ${telemetry.ttft_ms}ms`}
              >
                ⚡ {telemetry.cache === "HIT" ? `CACHE HIT (${telemetry.total_ms}ms)` : `TTFT: ${telemetry.ttft_ms}ms | ${telemetry.total_ms}ms`}
              </span>
            )}

            {markdownContent && (
              <button
                onClick={handleCopy}
                className="flex items-center gap-1 text-[10px] text-slate-400 hover:text-white px-2 py-1 rounded bg-white/5 hover:bg-white/10 transition-all"
                title="Copy markdown response"
              >
                {copied ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
                <span>{copied ? "Copied" : "Copy"}</span>
              </button>
            )}
          </div>
        </div>

        {/* Reading Level Selector Buttons */}
        <div className="grid grid-cols-3 gap-1 bg-[#1e1e1e] p-1 rounded-lg border border-white/5">
          <button
            onClick={() => onLevelChange("Beginner")}
            className={`flex items-center justify-center gap-1 text-[9px] font-bold uppercase tracking-wider py-1.5 rounded transition-all ${
              readingLevel === "Beginner"
                ? "bg-blue-600 text-white shadow"
                : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
            }`}
          >
            <GraduationCap className="w-3 h-3 text-blue-300" />
            <span>Beginner</span>
          </button>

          <button
            onClick={() => onLevelChange("Undergraduate")}
            className={`flex items-center justify-center gap-1 text-[9px] font-bold uppercase tracking-wider py-1.5 rounded transition-all ${
              readingLevel === "Undergraduate"
                ? "bg-indigo-600 text-white shadow"
                : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
            }`}
          >
            <BookOpen className="w-3 h-3 text-indigo-300" />
            <span>Undergrad</span>
          </button>

          <button
            onClick={() => onLevelChange("Researcher")}
            className={`flex items-center justify-center gap-1 text-[9px] font-bold uppercase tracking-wider py-1.5 rounded transition-all ${
              readingLevel === "Researcher"
                ? "bg-purple-600 text-white shadow"
                : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
            }`}
          >
            <FlaskConical className="w-3 h-3 text-purple-300" />
            <span>Researcher</span>
          </button>
        </div>
      </div>

      {/* 2. Scrollable Body: Selected Highlight, Progressive Timeline & Collapsible Sections */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4 scrollable">
        {selectedText && (
          <div className="bg-[#121212] border-l-2 border-l-blue-500 border-white/5 border p-3 rounded text-xs italic text-slate-300">
            "{selectedText}"
          </div>
        )}

        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-16 text-slate-500 gap-4">
            <div className="w-8 h-8 rounded-full border-2 border-slate-700 border-t-blue-500 animate-spin" />
            <div className="flex flex-col gap-1.5 text-center text-[10px] font-mono text-slate-400">
              <span className="text-green-400 font-bold">✓ Single-Pass SharedContext Built</span>
              <span className="text-blue-400 font-bold animate-pulse">⚡ Parallel Execution & Section Streaming...</span>
            </div>
          </div>
        ) : sections.length > 0 ? (
          <div className="flex flex-col gap-3">
            {sections.map((sec) => {
              const isCollapsed = !!collapsedSections[sec.id];
              return (
                <div
                  key={sec.id}
                  className="bg-[#121212]/90 border border-white/5 rounded-xl overflow-hidden shadow-sm transition-all"
                >
                  {/* Collapsible Section Header */}
                  <button
                    onClick={() => toggleSection(sec.id)}
                    className="w-full flex items-center justify-between p-3 bg-white/5 hover:bg-white/10 text-left transition-colors select-none"
                  >
                    <h4 className="text-xs font-bold text-blue-300 uppercase tracking-wide flex items-center gap-1.5">
                      <span>{sec.title}</span>
                    </h4>
                    {isCollapsed ? (
                      <ChevronRight className="w-4 h-4 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    )}
                  </button>

                  {/* Section Markdown Body */}
                  {!isCollapsed && sec.content && (
                    <div className="p-3.5 text-xs text-slate-300 leading-relaxed border-t border-white/5 prose prose-invert max-w-none">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {sec.content}
                      </ReactMarkdown>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-16 text-slate-500 text-xs flex flex-col items-center gap-2">
            <BookOpen className="w-8 h-8 stroke-[1.5]" />
            <p>Select any equation, text, or figure in the paper to invoke Swarm Analyst.</p>
          </div>
        )}
      </div>
    </div>
  );
};
