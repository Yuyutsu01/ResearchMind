"use client";

import React, { useState, useEffect, useRef } from "react";
import { Search, Upload, BookOpen, GitCommit, FileDown, Terminal, Award } from "lucide-react";
import TelemetryMetrics from "@/components/TelemetryMetrics";
import CytoscapeGraph from "@/components/CytoscapeGraph";
import QuizSection from "@/components/QuizSection";

const API_BASE = "http://localhost:8000";
const WS_BASE = "ws://localhost:8000";

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

  const [wsStatus, setWsStatus] = useState("Disconnected");
  const [isProcessing, setIsProcessing] = useState(false);
  
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
      }
    } catch (err) {
      console.error("Upload failed", err);
    } finally {
      setUploading(false);
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
    <div className="min-h-screen bg-[#0B0F19] text-gray-100 flex flex-col">
      {/* Header Banner */}
      <header className="border-b border-white/10 bg-gray-900/80 backdrop-blur px-8 py-4 flex justify-between items-center z-10">
        <div className="flex items-center gap-3">
          <BookOpen className="w-6 h-6 text-blue-500 filter drop-shadow-[0_0_8px_#3B82F6]" />
          <h1 className="font-header text-xl font-bold tracking-tight">
            ResearchMind <span className="text-blue-500 font-medium">Swarm v1</span>
          </h1>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <span className={`w-2.5 h-2.5 rounded-full ${wsStatus === "Connected" ? "bg-emerald-500" : "bg-rose-500"}`} />
            <span>Server: {wsStatus}</span>
          </div>
          <div className="text-xs bg-white/5 border border-white/10 rounded px-2.5 py-1 text-slate-300 font-medium">
            State Machine: <span className="text-blue-400 font-bold">{currentState}</span>
          </div>
        </div>
      </header>

      {/* Main Workspace Layout */}
      <main className="flex-1 p-6 max-w-7xl w-full mx-auto flex flex-col gap-6">
        
        {/* Telemetry panel */}
        <TelemetryMetrics metrics={metrics} budget={budget} />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left panel: Config and Swarm Timeline */}
          <div className="flex flex-col gap-6 lg:col-span-1">
            
            {/* Input Config Card */}
            <div className="glass-panel p-6 flex flex-col gap-4">
              <h3 className="font-header text-sm font-bold uppercase tracking-wider text-slate-400">
                Setup Research Task
              </h3>
              <form onSubmit={handleStartSession} className="flex flex-col gap-4">
                <div className="flex flex-col gap-2">
                  <label className="text-xs text-slate-400 font-medium">Core Query / Objective</label>
                  <input
                    type="text"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="E.g., Compare Attention complexities..."
                    className="w-full bg-[#111827] border border-white/10 rounded-lg p-3 text-xs focus:border-blue-500 focus:outline-none"
                    required
                  />
                </div>

                <div className="flex flex-col gap-2">
                  <label className="text-xs text-slate-400 font-medium">Upload Context Paper (PDF)</label>
                  <div className="border border-dashed border-white/10 hover:border-blue-500/50 rounded-lg p-4 flex flex-col items-center justify-center gap-2 cursor-pointer transition-all relative">
                    <input
                      type="file"
                      accept=".pdf"
                      onChange={handleUpload}
                      className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />
                    <Upload className="w-5 h-5 text-slate-500" />
                    <span className="text-[10px] text-slate-400 text-center">
                      {file ? file.name : "Drag & drop your PDF file here"}
                    </span>
                    {uploading && <span className="text-[10px] text-blue-400">Uploading & parsing...</span>}
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isProcessing}
                  className="btn btn-primary w-full text-xs py-3 mt-2 disabled:opacity-50"
                >
                  <Search className="w-4 h-4" />
                  <span>Start Swarm Research</span>
                </button>
              </form>
            </div>

            {/* Swarm Execution Timeline */}
            <div className="glass-panel p-6 flex-1 flex flex-col gap-4 min-h-[300px]">
              <div className="flex items-center justify-between border-b border-white/10 pb-2">
                <h3 className="font-header text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Terminal className="w-4 h-4" />
                  Swarm Action Logs
                </h3>
                <span className="text-[10px] text-slate-500">Live Trace</span>
              </div>
              <div className="flex-1 overflow-y-auto max-h-[320px] flex flex-col gap-3 scrollable pr-2 text-[11px]">
                {logs.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-slate-500">
                    Awaiting research start...
                  </div>
                ) : (
                  logs.map((log, idx) => (
                    <div key={idx} className="border-l-2 border-blue-500/50 pl-3 py-0.5 flex flex-col gap-1">
                      <div className="flex justify-between items-center">
                        <span className="font-bold text-blue-400 uppercase tracking-wide">{log.agent}</span>
                        <span className="text-[9px] bg-white/5 border border-white/10 px-1.5 py-0.2 rounded text-slate-400">
                          {log.action}
                        </span>
                      </div>
                      <p className="text-slate-300 leading-relaxed">{log.description}</p>
                    </div>
                  ))
                )}
                <div ref={logsEndRef} />
              </div>
            </div>

          </div>

          {/* Right panel: Knowledge Graph and Synthesis report */}
          <div className="lg:col-span-2 flex flex-col gap-6">
            
            {/* Interactive Cytoscape.js Graph Card */}
            <div className="glass-panel p-6 flex flex-col gap-4">
              <h3 className="font-header text-sm font-bold uppercase tracking-wider text-slate-400">
                NetworkX Knowledge Graph Visualizer
              </h3>
              <div className="h-[400px]">
                <CytoscapeGraph nodes={graphNodes} edges={graphEdges} />
              </div>
            </div>

            {/* Synthesis Output Narrative */}
            {report && (
              <div className="glass-panel p-6 flex flex-col gap-4">
                <div className="flex justify-between items-center border-b border-white/10 pb-2">
                  <h3 className="font-header text-sm font-bold uppercase tracking-wider text-slate-400">
                    Research Brief Synthesis
                  </h3>
                  <div className="flex gap-2">
                    <button onClick={() => handleExport("markdown")} className="btn btn-secondary py-1 px-3 text-[10px]">
                      <FileDown className="w-3 h-3" /> MD
                    </button>
                    <button onClick={() => handleExport("latex")} className="btn btn-secondary py-1 px-3 text-[10px]">
                      <FileDown className="w-3 h-3" /> LaTeX
                    </button>
                  </div>
                </div>
                <article className="prose prose-invert max-w-none text-slate-300 text-xs leading-relaxed max-h-[300px] overflow-y-auto pr-2 scrollable whitespace-pre-wrap">
                  {report}
                </article>
              </div>
            )}

            {/* Researcher Quiz Modal */}
            {quiz.length > 0 && (
              <QuizSection
                quiz={quiz}
                onComplete={(score) => {
                  // User quiz completion metrics logged
                  console.log("Quiz submitted, score:", score);
                }}
              />
            )}

          </div>
        </div>

      </main>
    </div>
  );
}
