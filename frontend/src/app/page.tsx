"use client";

import React, { useState, useEffect, useRef } from "react";
import { Search, Upload, BookOpen, Terminal, RefreshCw, AlertCircle } from "lucide-react";
import { ReadingWorkspace } from "@/components/ReadingWorkspace";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
const WS_BASE = API_BASE.replace(/^http/, "ws");

export default function Dashboard() {
  const [prompt, setPrompt] = useState("Explain the paper methodology and equations.");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [fileId, setFileId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [currentState, setCurrentState] = useState("IDLE");
  
  const [wsStatus, setWsStatus] = useState("Ready");
  const [isProcessing, setIsProcessing] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    
    setUploading(true);
    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const res = await fetch(`${API_BASE}/api/v1/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (data.success) {
        setFileId(data.file_id);
        // Automatically launch session
        autoLaunchSession(data.file_id);
      }
    } catch (err) {
      console.error("Upload failed", err);
    } finally {
      setUploading(false);
    }
  };

  const autoLaunchSession = async (fId: string) => {
    setIsProcessing(true);
    setLogs(["[Client] Creating ResearchMind session in Postgres...", "[Client] Instantiating Swarm orchestrators..."]);
    setWsStatus("Connecting");
    
    try {
      // 1. Create Session
      const res = await fetch(`${API_BASE}/api/v1/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: 1,
          prompt: prompt,
          file_id: fId,
        }),
      });
      
      if (!res.ok) {
        const errDetail = await res.text();
        throw new Error(`Failed to create session (HTTP ${res.status}): ${errDetail}`);
      }

      const data = await res.json();
      if (!data || !data.session_id) {
        throw new Error("Invalid response received from sessions API.");
      }

      setSessionId(data.session_id);
      
      // 2. Establish WebSocket Stream connection
      const socket = new WebSocket(`${WS_BASE}/ws/v1/research/${data.session_id}`);
      wsRef.current = socket;
      
      socket.onopen = () => {
        setWsStatus("Connected");
        setLogs((prev) => [...prev, "[WebSocket] Connection established.", "[Pipeline] Loading parser plugins..."]);
      };
      
      socket.onmessage = (event) => {
        const payload = JSON.parse(event.data);
        if (payload.type === "progress_update") {
          setLogs((prev) => [...prev, `[Pipeline] ${payload.msg}`]);
          if (payload.step === "COMPLETE") {
            setCurrentState("READY");
            setIsProcessing(false);
          }
        }
      };

      socket.onerror = (err) => {
        console.error("WebSocket error", err);
        setWsStatus("Error");
      };

      socket.onclose = () => {
        setWsStatus("Disconnected");
      };

    } catch (err) {
      console.error("Failed to create session", err);
      setLogs((prev) => [...prev, `[Error] ${err instanceof Error ? err.message : String(err)}`]);
      setWsStatus("Error");
      setIsProcessing(false);
    }
  };

  if (sessionId && fileId) {
    return (
      <main className="h-screen w-screen overflow-hidden flex flex-col bg-[#121212]">
        {/* Navigation Bar */}
        <div className="flex-shrink-0 flex items-center justify-between px-6 h-[56px] border-b border-white/10 bg-[#1e1e1e] select-none">
          <div className="flex items-center gap-2">
            <span className="font-header font-bold text-sm tracking-wider text-white">RESEARCHMIND</span>
            <span className="text-[10px] bg-blue-600/20 text-blue-400 border border-blue-600/30 px-2 py-0.5 rounded uppercase font-bold">Workspace</span>
          </div>
          <div className="flex items-center gap-4 text-xs font-medium text-slate-400">
            <span>WebSocket: <strong className={wsStatus === "Connected" ? "text-green-400" : "text-amber-400"}>{wsStatus}</strong></span>
          </div>
        </div>
        
        {/* Main interactive panel workspace */}
        <div className="flex-1 overflow-hidden relative">
          <ReadingWorkspace 
            sessionId={sessionId} 
            apiBase={API_BASE} 
            ws={wsRef.current} 
          />
        </div>
      </main>
    );
  }

  return (
    <main className="h-screen w-screen bg-[#121212] flex items-center justify-center p-6 text-slate-300">
      <div className="w-full max-w-md bg-[#1e1e1e] border border-white/5 shadow-2xl rounded-2xl p-8 flex flex-col gap-6 relative overflow-hidden select-none">
        
        {/* Gradient Header */}
        <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-blue-600 to-indigo-600" />
        
        <div className="flex flex-col items-center text-center gap-2">
          <div className="w-12 h-12 rounded-xl bg-blue-600/10 border border-blue-600/20 flex items-center justify-center text-blue-400 mb-2">
            <BookOpen className="w-6 h-6 stroke-[1.5]" />
          </div>
          <h1 className="font-header font-bold text-2xl text-white tracking-tight">ResearchMind</h1>
          <p className="text-xs text-slate-500 max-w-xs leading-normal">
            Research Companion: Interactive Swarm AI Workspace for Scientific Papers.
          </p>
        </div>

        {isProcessing ? (
          <div className="flex flex-col gap-4 py-4 animate-in fade-in duration-300">
            <div className="flex items-center gap-3 bg-[#121212] border border-white/5 rounded-lg p-3">
              <RefreshCw className="w-5 h-5 text-blue-500 animate-spin" />
              <div className="flex-1">
                <span className="text-xs font-bold text-white block">Analyzing Document Layout</span>
                <span className="text-[10px] text-slate-500">Fast PyMuPDF extraction running...</span>
              </div>
            </div>
            
            {/* Real-time Logger Terminal console */}
            <div className="bg-black border border-white/10 rounded-lg p-4 font-mono text-[9px] text-green-400 flex flex-col gap-1.5 h-36 overflow-y-auto scrollable">
              {logs.map((log, idx) => (
                <div key={idx} className="flex gap-1.5 items-start">
                  <Terminal className="w-3 h-3 text-slate-500 mt-0.5 flex-shrink-0" />
                  <span>{log}</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex flex-col gap-4 select-none">
            {/* Prompt input query */}
            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Research Focus Prompt</label>
              <input 
                type="text" 
                placeholder="What is your research goal?"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                className="w-full bg-[#121212] border border-white/10 rounded-lg px-4 py-2.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-blue-500 transition-colors"
              />
            </div>
            
            {/* File upload zone drop area */}
            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Select Scientific Paper PDF</label>
              <div className="border border-dashed border-white/10 hover:border-blue-500/50 hover:bg-blue-500/5 rounded-lg p-6 flex flex-col items-center justify-center gap-2 cursor-pointer transition-all relative">
                <input 
                  type="file" 
                  accept="application/pdf"
                  onChange={handleUpload}
                  disabled={uploading}
                  className="absolute inset-0 opacity-0 cursor-pointer"
                />
                <Upload className="w-6 h-6 text-slate-500" />
                <span className="text-xs text-slate-400 font-medium">
                  {uploading ? "Uploading paper..." : "Upload scientific paper PDF"}
                </span>
                <span className="text-[9px] text-slate-600">Supports PDF up to 25MB</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
