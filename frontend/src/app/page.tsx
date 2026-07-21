"use client";

import React, { useState, useEffect, useRef } from "react";
import { Search, Upload, BookOpen, GitCommit, FileDown, Terminal, Award, RefreshCw } from "lucide-react";
import TelemetryMetrics from "@/components/TelemetryMetrics";
import CytoscapeGraph from "@/components/CytoscapeGraph";
import QuizSection from "@/components/QuizSection";
import { ReadingWorkspace } from "@/components/ReadingWorkspace";


const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
const WS_BASE = API_BASE.replace(/^http/, "ws");

interface LogItem {
  agent: string;
  action: string;
  description: string;
}

export default function Dashboard() {
  const [prompt, setPrompt] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [fileId, setFileId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [currentState, setCurrentState] = useState("IDLE");
  
  const [logs, setLogs] = useState<LogItem[]>([]);
  const [graphNodes, setGraphNodes] = useState([]);
  const [graphEdges, setGraphEdges] = useState([]);
  const [report, setReport] = useState("");
  const [quiz, setQuiz] = useState([]);
  
  const [metrics, setMetrics] = useState({
    task_completion_rate: 0.0,
    autonomy_score: 1.0,
    answer_grounding_score: 1.0,
    hallucination_rate: 0.0,
    cost_usd: 0.0,
  });

  const [budget, setBudget] = useState({
    tokens_remaining: 500000,
    dollars_remaining: 10.0,
  });

  const [wsStatus, setWsStatus] = useState("Checking...");
  const [isProcessing, setIsProcessing] = useState(false);

  // Check if API Server is online on mount and poll
  useEffect(() => {
    const checkApi = async () => {
      try {
        const res = await fetch(`${API_BASE}/`);
        const data = await res.json();
        if (data.status === "online") {
          // If we are currently active on a WebSocket session, preserve its state
          setWsStatus((current) => (current === "Connected" || current === "Connecting") ? current : "Ready");
        } else {
          setWsStatus("Offline");
        }
      } catch (err) {
        setWsStatus("Offline");
      }
    };
    checkApi();
    const interval = setInterval(checkApi, 5000);
    return () => clearInterval(interval);
  }, []);
  
  const wsRef = useRef<WebSocket | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs]);

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
        // Automatically start the session and transition to the reading workspace
        await autoLaunchSession(data.file_id, selectedFile.name);
      }
    } catch (err) {
      console.error("Upload failed", err);
    } finally {
      setUploading(false);
    }
  };

  const autoLaunchSession = async (fId: string, filename: string) => {
    setIsProcessing(true);
    setLogs([]);
    setReport("");
    setQuiz([]);
    setGraphNodes([]);
    setGraphEdges([]);
    setWsStatus("Connecting");
    
    try {
      // 1. Create Session
      const res = await fetch(`${API_BASE}/api/v1/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: 1,
          prompt: `Read and analyze ${filename}`,
          file_id: fId,
        }),
      });
      const data = await res.json();
      const sId = data.session_id;
      setSessionId(sId);

      // 2. Connect WebSocket
      const ws = new WebSocket(`${WS_BASE}/ws/v1/research/${sId}`);
      wsRef.current = ws;

      ws.onopen = () => {
        setWsStatus("Connected");
      };

      ws.onclose = () => {
        setWsStatus("Disconnected");
        setIsProcessing(false);
      };

      ws.onmessage = (event) => {
        const payload = JSON.parse(event.data);
        handleWsMessage(payload, sId);
      };
      
    } catch (err) {
      console.error("Failed to auto-start session", err);
      setIsProcessing(false);
      setWsStatus("Offline");
    }
  };

  const handleStartSession = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setIsProcessing(true);
    setLogs([]);
    setReport("");
    setQuiz([]);
    setGraphNodes([]);
    setGraphEdges([]);
    
    try {
      // 1. Create Session
      const res = await fetch(`${API_BASE}/api/v1/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: 1,
          prompt: prompt,
          file_id: fileId,
        }),
      });
      const data = await res.json();
      const sId = data.session_id;
      setSessionId(sId);

      // 2. Connect WebSocket
      const ws = new WebSocket(`${WS_BASE}/ws/v1/research/${sId}`);
      wsRef.current = ws;
      setWsStatus("Connecting");

      ws.onopen = () => {
        setWsStatus("Connected");
      };

      ws.onclose = () => {
        setWsStatus("Disconnected");
        setIsProcessing(false);
      };

      ws.onmessage = (event) => {
        const payload = JSON.parse(event.data);
        handleWsMessage(payload, sId);
      };
      
    } catch (err) {
      console.error("Failed to start session", err);
      setIsProcessing(false);
    }
  };

  const handleWsMessage = (data: any, sId: number) => {
    if (data.type === "state_change") {
      setCurrentState(data.state);
    } else if (data.type === "agent_step") {
      setLogs((prev) => [
        ...prev,
        {
          agent: data.agent,
          action: data.action,
          description: data.description,
        },
      ]);
      // Asynchronously fetch graph updates
      fetchGraph(sId);
    } else if (data.type === "telemetry_update") {
      setMetrics(data.metrics);
      setBudget(data.budget);
    } else if (data.type === "ui_prompt") {
      // Handle user clarification options in UI
      setLogs((prev) => [
        ...prev,
        {
          agent: "UIAgent",
          action: "PROMPT_USER",
          description: `Paused for clarification: ${data.message}`,
        },
      ]);
    } else if (data.type === "result") {
      setReport(data.report);
      setQuiz(data.quiz);
      setMetrics(data.metrics);
      setIsProcessing(false);
    }
  };

  const fetchGraph = async (sId: number) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/sessions/${sId}/graph`);
      const data = await res.json();
      setGraphNodes(data.nodes || []);
      setGraphEdges(data.edges || []);
    } catch (err) {
      console.error("Failed to fetch graph data", err);
    }
  };

  const handleExport = async (format: string) => {
    if (!sessionId) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}/export`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ format }),
      });
      const data = await res.json();
      if (data.success) {
        window.open(`${API_BASE}${data.download_url}`, "_blank");
      }
    } catch (err) {
      console.error("Export failed", err);
    }
  };

  return (
    <div className="h-screen w-screen bg-[#121212] text-gray-100 flex flex-col overflow-hidden select-none">
      {/* Header Banner */}
      <header className="h-[56px] border-b border-white/10 bg-[#202124] px-6 flex justify-between items-center z-10 flex-shrink-0">
        <div className="flex items-center gap-3">
          <BookOpen className="w-5 h-5 text-blue-500 filter drop-shadow-[0_0_8px_#3B82F6]" />
          <h1 className="font-header text-base font-bold tracking-tight">
            ResearchMind <span className="text-blue-500 font-medium">Swarm v1</span>
          </h1>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <span className={`w-2 h-2 rounded-full ${
              wsStatus === "Connected" ? "bg-emerald-500 animate-pulse" :
              wsStatus === "Ready" ? "bg-blue-500" :
              wsStatus === "Connecting" ? "bg-amber-500 animate-pulse" :
              "bg-rose-500"
            }`} />
            <span>Server: <strong className={
              wsStatus === "Connected" ? "text-emerald-400" :
              wsStatus === "Ready" ? "text-blue-400" :
              wsStatus === "Connecting" ? "text-amber-400" :
              "text-rose-400"
            }>{wsStatus}</strong></span>
          </div>
          <div className="text-xs bg-white/5 border border-white/10 rounded px-2 py-0.5 text-slate-300 font-medium">
            State: <span className="text-blue-400 font-bold">{currentState}</span>
          </div>
        </div>
      </header>

      {/* Fixed Workspace Layout */}
      {sessionId ? (
        <main className="flex-1 flex flex-col h-[calc(100vh-56px)] overflow-hidden w-full bg-[#121212]">
          <ReadingWorkspace
            sessionId={sessionId}
            apiBase={API_BASE}
            ws={wsRef.current}
            onRefreshGraph={() => fetchGraph(sessionId)}
          />
        </main>
      ) : (
        <main className="flex-1 p-6 max-w-7xl w-full mx-auto flex flex-col gap-6 overflow-y-auto">
          <div className="flex-1 flex flex-col items-center justify-center py-20 max-w-lg mx-auto gap-8 animate-in fade-in duration-300">
            <div className="text-center space-y-3">
              <h2 className="text-4xl font-extrabold tracking-tight font-header bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent">
                Welcome, Researcher
              </h2>
              <p className="text-slate-400 text-sm leading-relaxed">
                Upload a scientific PDF paper to immediately launch your collaborative AI swarm reading workspace.
              </p>
            </div>

            {/* Premium drag & drop file upload area */}
            <div className="w-full glass-panel p-8 flex flex-col items-center gap-6 border border-white/10 hover:border-blue-500/20 transition-all rounded-2xl relative shadow-[0_0_50px_rgba(59,130,246,0.05)]">
              <div className="border border-dashed border-white/10 hover:border-blue-500/40 rounded-xl p-8 flex flex-col items-center justify-center gap-4 cursor-pointer w-full transition-all bg-white/5 hover:bg-white/10 relative">
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handleUpload}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <Upload className="w-10 h-10 text-blue-500 animate-bounce" />
                <div className="text-center space-y-1">
                  <span className="text-sm font-semibold text-slate-200">
                    {file ? file.name : "Select or drag your PDF paper"}
                  </span>
                  <p className="text-[10px] text-slate-500">Supported formats: PDF documents up to 50MB</p>
                </div>
              </div>

              {uploading && (
                <div className="flex items-center gap-2 text-xs text-blue-400 animate-pulse font-medium">
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Uploading & parsing document layout...</span>
                </div>
              )}
            </div>
          </div>
        </main>
      )}
    </div>
  );
}
