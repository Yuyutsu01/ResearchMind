"use client";

import React, { useState, useRef } from "react";
import { ReadingWorkspace } from "@/components/ReadingWorkspace";
import { ResearchWelcome } from "@/components/research-welcome/ResearchWelcome";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
const WS_BASE = API_BASE.replace(/^http/, "ws");

export default function Dashboard() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [fileId, setFileId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<number | null>(null);
  
  const [wsStatus, setWsStatus] = useState("Ready");
  const [isProcessing, setIsProcessing] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleUploadFile = async (selectedFile: File) => {
    setFile(selectedFile);
    setErrorMessage(null);
    setUploading(true);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const res = await fetch(`${API_BASE}/api/v1/upload`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        throw new Error(`Upload server error (HTTP ${res.status})`);
      }
      const data = await res.json();
      if (data.success) {
        setFileId(data.file_id);
        autoLaunchSession(data.file_id);
      }
    } catch (err: any) {
      console.error("Upload failed", err);
      setErrorMessage(`Backend Connection Failed: Ensure FastAPI backend is running on ${API_BASE}.`);
      setUploading(false);
    }
  };

  const autoLaunchSession = async (fId: string) => {
    setIsProcessing(true);
    setLogs(["[Client] Creating ResearchMind session...", "[Client] Instantiating Swarm orchestrators..."]);
    setWsStatus("Connecting");
    
    try {
      const res = await fetch(`${API_BASE}/api/v1/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: 1,
          prompt: "Interactive Research Analysis",
          file_id: fId,
        }),
      });
      
      if (!res.ok) {
        const errDetail = await res.text();
        throw new Error(`Failed to create session (HTTP ${res.status}): ${errDetail}`);
      }

      const data = await res.json();
      setSessionId(data.session_id);
      
      const socket = new WebSocket(`${WS_BASE}/ws/v1/research/${data.session_id}`);
      wsRef.current = socket;
      
      socket.onopen = () => {
        setWsStatus("Connected");
        setIsProcessing(false);
      };
      
      socket.onmessage = (event) => {
        const payload = JSON.parse(event.data);
        if (payload.type === "progress_update") {
          setLogs((prev) => [...prev, `[Pipeline] ${payload.msg}`]);
          if (payload.step === "COMPLETE") {
            setIsProcessing(false);
          }
        }
      };

      socket.onerror = (err) => {
        setWsStatus("Error");
        setIsProcessing(false);
      };

      socket.onclose = () => {
        setWsStatus("Disconnected");
      };

    } catch (err) {
      setLogs((prev) => [...prev, `[Error] ${err instanceof Error ? err.message : String(err)}`]);
      setWsStatus("Error");
      setIsProcessing(false);
      setUploading(false);
    }
  };

  if (sessionId && fileId) {
    return (
      <main className="h-screen w-screen overflow-hidden flex flex-col bg-[#121212]">
        <div className="flex-shrink-0 flex items-center justify-between px-6 h-[56px] border-b border-white/10 bg-[#1e1e1e] select-none">
          <div className="flex items-center gap-2">
            <span className="font-header font-bold text-sm tracking-wider text-white">RESEARCHMIND</span>
            <span className="text-[10px] bg-blue-600/20 text-blue-400 border border-blue-600/30 px-2 py-0.5 rounded uppercase font-bold">Workspace</span>
          </div>
          <div className="flex items-center gap-4 text-xs font-medium text-slate-400">
            <span>WebSocket: <strong className={wsStatus === "Connected" ? "text-green-400" : "text-amber-400"}>{wsStatus}</strong></span>
          </div>
        </div>
        
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
    <ResearchWelcome
      onFileSelect={handleUploadFile}
      uploading={uploading || isProcessing}
      error={errorMessage}
    />
  );
}
