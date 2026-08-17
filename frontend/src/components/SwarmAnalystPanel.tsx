"use client";

import React, { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Sparkles, Send, RefreshCw, Copy, Check, FileText, CornerDownLeft, RotateCcw } from "lucide-react";

export interface ChatMessageItem {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp?: number;
}

interface SwarmAnalystPanelProps {
  selectedText: string;
  conversationId?: string;
  pageNum?: number;
  sectionTitle?: string;
  initialAnalysisMarkdown?: string;
  chatMessages: ChatMessageItem[];
  isLoading: boolean;
  onSendFollowup: (question: string) => void;
  onResetAnalysis: () => void;
  onNavigateToPage?: (pageNum: number) => void;
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
  selectedText,
  conversationId,
  pageNum = 1,
  sectionTitle = "Selection Analysis",
  initialAnalysisMarkdown,
  chatMessages,
  isLoading,
  onSendFollowup,
  onResetAnalysis,
  onNavigateToPage,
  telemetry,
}) => {
  const [copied, setCopied] = useState(false);
  const [inputQuestion, setInputQuestion] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll chat thread to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages, isLoading, initialAnalysisMarkdown]);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuestion.trim() || isLoading) return;
    onSendFollowup(inputQuestion.trim());
    setInputQuestion("");
  };

  return (
    <div className="flex flex-col h-full bg-[#18181b] text-slate-200 select-text overflow-hidden">
      {/* 1. Header with Context Chip & Telemetry */}
      <div className="flex-shrink-0 border-b border-white/10 p-3 bg-[#121212] select-none flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-xs font-bold text-blue-400">
            <Sparkles className="w-4 h-4 text-blue-400" />
            <span>Swarm Analyst Research Chat</span>
          </div>

          <div className="flex items-center gap-2">
            {/* Telemetry Timing Badge */}
            {telemetry && (
              <span
                className={`text-[8px] font-mono font-bold px-1.5 py-0.5 rounded border uppercase ${
                  telemetry.cache === "HIT"
                    ? "bg-green-500/20 text-green-400 border-green-500/30"
                    : "bg-blue-500/20 text-blue-400 border-blue-500/30"
                }`}
                title={`Redis: ${telemetry.redis_lookup_ms}ms | Intent: ${telemetry.intent_router_ms}ms | TTFT: ${telemetry.ttft_ms}ms`}
              >
                ⚡ {telemetry.cache === "HIT" ? `CACHE HIT (${telemetry.total_ms}ms)` : `TTFT: ${telemetry.ttft_ms}ms | ${telemetry.total_ms}ms`}
              </span>
            )}

            {/* Clear / New Analysis Reset Button */}
            <button
              onClick={onResetAnalysis}
              className="flex items-center gap-1 text-[10px] text-slate-400 hover:text-white px-2 py-1 rounded bg-white/5 hover:bg-white/10 transition-all"
              title="Start New Analysis"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reset</span>
            </button>
          </div>
        </div>

        {/* Compact Context Chip */}
        {selectedText && (
          <div className="flex items-center gap-2 bg-[#1e1e1e] border border-white/10 px-2.5 py-1.5 rounded-lg text-[11px] text-slate-300">
            <button
              onClick={() => onNavigateToPage?.(pageNum)}
              className="flex items-center gap-1 text-blue-400 hover:underline font-mono font-bold flex-shrink-0"
              title={`Jump to Page ${pageNum}`}
            >
              <FileText className="w-3 h-3" />
              <span>Page {pageNum}</span>
            </button>
            <span className="text-slate-600">·</span>
            <span className="truncate italic text-slate-400">"{selectedText}"</span>
          </div>
        )}
      </div>

      {/* 2. Main Scrollable Chat Thread */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4 scrollable">
        {/* Initial Analysis Message */}
        {initialAnalysisMarkdown ? (
          <div className="bg-[#121212]/90 border border-white/10 rounded-xl p-4 text-xs leading-relaxed text-slate-200 shadow-md prose prose-invert max-w-none">
            <div className="flex items-center justify-between border-b border-white/5 pb-2 mb-3">
              <span className="text-[10px] uppercase font-bold text-blue-400 tracking-wider">Initial Swarm Analysis</span>
              <button
                onClick={() => handleCopy(initialAnalysisMarkdown)}
                className="text-slate-500 hover:text-white transition-colors"
                title="Copy markdown"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {initialAnalysisMarkdown}
            </ReactMarkdown>
          </div>
        ) : isLoading ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-500 gap-4">
            <div className="w-8 h-8 rounded-full border-2 border-slate-700 border-t-blue-500 animate-spin" />
            <div className="flex flex-col gap-1 text-center text-[10px] font-mono text-slate-400">
              <span className="text-green-400 font-bold">✓ Single-Pass SharedContext Built</span>
              <span className="text-blue-400 font-bold animate-pulse">⚡ Streaming Substantive Research Analysis...</span>
            </div>
          </div>
        ) : (
          <div className="text-center py-20 text-slate-500 text-xs flex flex-col items-center gap-2">
            <Sparkles className="w-8 h-8 text-blue-500/50" />
            <p>Select any equation, text, table, or figure in the paper to start an interactive research conversation.</p>
          </div>
        )}

        {/* Follow-up Chat Message History */}
        {chatMessages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col gap-1 max-w-[90%] text-xs ${
              msg.role === "user" ? "self-end items-end" : "self-start items-start"
            }`}
          >
            <div
              className={`p-3.5 rounded-xl leading-relaxed ${
                msg.role === "user"
                  ? "bg-blue-600 text-white rounded-br-none font-medium shadow-sm"
                  : "bg-[#121212] border border-white/10 text-slate-200 rounded-bl-none prose prose-invert max-w-none shadow-md"
              }`}
            >
              {msg.role === "user" ? (
                <span>{msg.content}</span>
              ) : (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {msg.content}
                </ReactMarkdown>
              )}
            </div>
          </div>
        ))}

        {/* Loading Spinner for follow-up responses */}
        {isLoading && initialAnalysisMarkdown && (
          <div className="self-start flex items-center gap-2 text-xs text-blue-400 font-mono bg-[#121212] border border-blue-500/20 px-3 py-2 rounded-xl">
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            <span>Analyzing follow-up question...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 3. Fixed Bottom Chat Composer */}
      <form onSubmit={handleFormSubmit} className="flex-shrink-0 p-3 bg-[#121212] border-t border-white/10 flex items-center gap-2">
        <input
          type="text"
          value={inputQuestion}
          onChange={(e) => setInputQuestion(e.target.value)}
          placeholder={selectedText ? "Ask anything about this selection..." : "Select paper text to begin..."}
          disabled={!selectedText || isLoading}
          className="flex-1 bg-[#1e1e1e] border border-white/10 rounded-xl px-3.5 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 disabled:opacity-50 transition-colors"
        />
        <button
          type="submit"
          disabled={!inputQuestion.trim() || isLoading}
          className="bg-blue-600 hover:bg-blue-500 text-white p-2 rounded-xl disabled:opacity-40 transition-all flex items-center justify-center flex-shrink-0"
          title="Send Follow-up Question"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
