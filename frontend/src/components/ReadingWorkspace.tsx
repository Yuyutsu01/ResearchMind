"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { BookOpen, AlertCircle, FileText, ChevronRight, Bookmark, Plus } from "lucide-react";

// 1. High-fidelity canvas-based scrollable PDF Page Viewer components
interface PdfPageProps {
  pdfUrl: string;
  pageNumber: number;
  scale: number;
  objects: any[];
  isVisible: boolean;
  defaultPageSize: { width: number; height: number } | null;
  registerRef: (node: HTMLDivElement | null, pageNum: number) => void;
  onTextSelect: (text: string, e: React.MouseEvent) => void;
  onObjectSelect: (obj: any, e: React.MouseEvent) => void;
}

const PdfPage: React.FC<PdfPageProps> = ({ 
  pdfUrl, 
  pageNumber, 
  scale, 
  objects, 
  isVisible, 
  defaultPageSize, 
  registerRef, 
  onTextSelect, 
  onObjectSelect 
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [textItems, setTextItems] = useState<any[]>([]);
  const [viewportSize, setViewportSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    if (!isVisible) return;
    let active = true;
    const renderPage = async () => {
      if (!(window as any).pdfjsLib) return;
      try {
        const loadingTask = (window as any).pdfjsLib.getDocument(pdfUrl);
        const pdf = await loadingTask.promise;
        const page = await pdf.getPage(pageNumber);
        
        const viewport = page.getViewport({ scale });
        
        if (!active) return;
        setViewportSize({ width: viewport.width, height: viewport.height });

        // Render PDF page to canvas with High-DPI (Retina) scaling
        const canvas = canvasRef.current;
        if (canvas) {
          const context = canvas.getContext("2d");
          const dpr = window.devicePixelRatio || 1;
          
          canvas.width = viewport.width * dpr;
          canvas.height = viewport.height * dpr;
          canvas.style.width = `${viewport.width}px`;
          canvas.style.height = `${viewport.height}px`;
          
          if (context) {
            context.scale(dpr, dpr);
            await page.render({ canvasContext: context, viewport }).promise;
          }
        }

        // Get text layer details
        const textContent = await page.getTextContent();
        if (!active) return;
        setTextItems(textContent.items);
      } catch (err) {
        console.error("Error rendering PDF page", err);
      }
    };

    renderPage();
    return () => {
      active = false;
    };
  }, [pdfUrl, pageNumber, scale, isVisible]);

  const handleMouseUp = (e: React.MouseEvent) => {
    const selection = window.getSelection();
    if (!selection) return;
    const text = selection.toString().trim();
    if (text.length > 2) {
      onTextSelect(text, e);
    }
  };

  // Render placeholder skeleton if page is unmounted / virtualized out of viewport
  if (!isVisible) {
    const width = viewportSize.width || (defaultPageSize ? defaultPageSize.width * scale : 600);
    const height = viewportSize.height || (defaultPageSize ? defaultPageSize.height * scale : 800);
    return (
      <div
        ref={(node) => registerRef(node, pageNumber)}
        data-page-number={pageNumber}
        className="relative mx-auto bg-[#1e1e1e]/40 border border-white/5 rounded-lg overflow-hidden select-none mb-6 flex items-center justify-center text-slate-500 text-xs"
        style={{ width: `${width}px`, height: `${height}px` }}
      >
        <div className="flex flex-col items-center gap-2">
          <div className="w-6 h-6 rounded-full border-2 border-slate-700 border-t-blue-500 animate-spin" />
          <span>Progressive Page {pageNumber}...</span>
        </div>
      </div>
    );
  }

  return (
    <div 
      ref={(node) => {
        containerRef.current = node;
        registerRef(node, pageNumber);
      }}
      data-page-number={pageNumber}
      onMouseUp={handleMouseUp}
      className="relative mx-auto bg-slate-900 shadow-xl border border-white/5 rounded-lg overflow-hidden select-text mb-6 transition-opacity duration-300"
      style={{ width: `${viewportSize.width}px`, height: `${viewportSize.height}px` }}
    >
      <canvas ref={canvasRef} className="absolute inset-0 z-0 pointer-events-none" />
      
      {/* Semantic Object Highlight Layout Overlay */}
      {objects.map((obj) => {
        if (!obj.bounding_box || obj.bounding_box.length < 4) return null;
        const [x0, y0, x1, y1] = obj.bounding_box;
        
        // Translate PDF page points directly to CSS pixels
        const left = x0 * scale;
        const top = y0 * scale;
        const width = (x1 - x0) * scale;
        const height = (y1 - y0) * scale;
        
        if (width <= 2 || height <= 2) return null;
        
        return (
          <div
            key={obj.id}
            onClick={(e) => {
              e.stopPropagation();
              onObjectSelect(obj, e);
            }}
            className="absolute border border-dashed border-blue-500/20 hover:border-blue-400 hover:bg-blue-500/10 transition-all cursor-pointer group"
            style={{
              left: `${left}px`,
              top: `${top}px`,
              width: `${width}px`,
              height: `${height}px`,
              zIndex: 20
            }}
            title={`Analyze ${obj.type}`}
          >
            <span className="hidden group-hover:block absolute -top-4 left-0 bg-blue-600 text-[8px] font-bold text-white uppercase px-1 rounded select-none z-30 pointer-events-none">
              {obj.type}
            </span>
          </div>
        );
      })}

      {/* Interactive selection transparent text layer overlay */}
      <div 
        className="absolute inset-0 z-10 select-text overflow-hidden" 
        style={{ width: `${viewportSize.width}px`, height: `${viewportSize.height}px` }}
      >
        {textItems.map((item, idx) => {
          if (!viewportSize.width || !(window as any).pdfjsLib) return null;
          
          const viewport = {
            transform: [scale, 0, 0, -scale, 0, viewportSize.height]
          };
          const tx = (window as any).pdfjsLib.Util.transform(viewport.transform, item.transform);
          
          const style = {
            left: `${tx[4]}px`,
            top: `${tx[5] - tx[3]}px`,
            fontSize: `${tx[3]}px`,
            fontFamily: item.fontName,
            position: "absolute" as const,
            color: "transparent",
            whiteSpace: "pre" as const,
            transformOrigin: "left bottom",
            transform: `scaleX(${item.width / (tx[0] * (item.str.length || 1))})`,
            cursor: "text",
            lineHeight: 1
          };
          return (
            <span key={idx} style={style}>
              {item.str}
            </span>
          );
        })}
      </div>
    </div>
  );
};

interface PdfViewerProps {
  pdfUrl: string;
  scale: number;
  objects: Record<number, any[]>;
  onPageChange: (pageNum: number) => void;
  onTextSelect: (text: string, e: React.MouseEvent) => void;
  onObjectSelect: (obj: any, e: React.MouseEvent) => void;
}

const PdfViewer: React.FC<PdfViewerProps> = ({ 
  pdfUrl, 
  scale, 
  objects, 
  onPageChange,
  onTextSelect, 
  onObjectSelect 
}) => {
  const [numPages, setNumPages] = useState<number>(0);
  const [pageSize, setPageSize] = useState<{ width: number; height: number } | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  
  // Track visible page states
  const observerRef = useRef<IntersectionObserver | null>(null);
  const [visiblePages, setVisiblePages] = useState<Record<number, boolean>>({});

  useEffect(() => {
    const loadPdf = async () => {
      if (!(window as any).pdfjsLib) {
        console.error("PDF.js library not loaded yet.");
        return;
      }
      (window as any).pdfjsLib.GlobalWorkerOptions.workerSrc = 
        "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js";

      try {
        const loadingTask = (window as any).pdfjsLib.getDocument(pdfUrl);
        const pdf = await loadingTask.promise;
        setNumPages(pdf.numPages);
        
        // Measure first page baseline dimensions
        const firstPage = await pdf.getPage(1);
        const viewport = firstPage.getViewport({ scale: 1.0 });
        setPageSize({ width: viewport.width, height: viewport.height });
      } catch (err) {
        console.error("Error loading PDF document", err);
      }
    };
    loadPdf();
  }, [pdfUrl]);

  // Set up intersection observer for virtualization
  useEffect(() => {
    observerRef.current = new IntersectionObserver(
      (entries) => {
        setVisiblePages((prev) => {
          const next = { ...prev };
          entries.forEach((entry) => {
            const pageNum = parseInt(entry.target.getAttribute("data-page-number") || "0", 10);
            if (pageNum > 0) {
              next[pageNum] = entry.isIntersecting;
              if (entry.isIntersecting) {
                // Notify parent workspace about visible page
                onPageChange(pageNum);
              }
            }
          });
          return next;
        });
      },
      {
        root: containerRef.current,
        rootMargin: "450px 0px",
        threshold: 0.01
      }
    );

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [onPageChange]);

  const registerPageRef = useCallback((node: HTMLDivElement | null, pageNum: number) => {
    if (node && observerRef.current) {
      observerRef.current.observe(node);
    }
  }, []);

  return (
    <div ref={containerRef} className="flex-1 flex flex-col gap-6 overflow-y-auto p-6 bg-slate-950/60 scrollable select-text">
      {numPages > 0 ? (
        Array.from({ length: numPages }, (_, i) => {
          const pageNum = i + 1;
          const isPageVisible = !!(
            visiblePages[pageNum] || 
            visiblePages[pageNum - 1] || 
            visiblePages[pageNum + 1]
          );

          return (
            <PdfPage 
              key={pageNum} 
              pdfUrl={pdfUrl} 
              pageNumber={pageNum} 
              scale={scale}
              objects={objects[pageNum] || []}
              isVisible={isPageVisible}
              defaultPageSize={pageSize}
              registerRef={registerPageRef}
              onTextSelect={onTextSelect} 
              onObjectSelect={onObjectSelect}
            />
          );
        })
      ) : (
        <div className="flex items-center justify-center h-full text-slate-500 py-20 animate-pulse">
          Loading PDF pages...
        </div>
      )}
    </div>
  );
};

interface ReadingWorkspaceProps {
  sessionId: number;
  apiBase: string;
  ws: WebSocket | null;
}

export const ReadingWorkspace: React.FC<ReadingWorkspaceProps> = ({ sessionId, apiBase, ws }) => {
  const [fileId, setFileId] = useState<string | null>(null);
  const [zoom, setZoom] = useState<number>(1.3);
  const [selectedText, setSelectedText] = useState("");
  const [selectedObjectId, setSelectedObjectId] = useState<string | null>(null);
  const [showHighlightMenu, setShowHighlightMenu] = useState(false);
  const [menuPosition, setMenuPosition] = useState({ x: 0, y: 0 });
  const [paperObjects, setPaperObjects] = useState<any[]>([]);
  const [parsingStatus, setParsingStatus] = useState<{ step: string; msg: string; page?: number } | null>(null);
  
  // Swarm explanation states
  const [activeTab, setActiveTab] = useState<"explain" | "notebook" | "timeline">("explain");
  const [swarmSubTab, setSwarmSubTab] = useState<"explain" | "math" | "background" | "visual" | "questions">("explain");
  const [currentExplanation, setCurrentExplanation] = useState<any>(null);
  const [explainingState, setExplainingState] = useState(false);

  // Notebook state
  const [notebook, setNotebook] = useState<any[]>([]);
  const [userNoteText, setUserNoteText] = useState("");
  const [savedNoteSuccess, setSavedNoteSuccess] = useState(false);
  const [timeline, setTimeline] = useState<any[]>([]);

  // Fetch paper metadata & objects
  const fetchPaperDetails = useCallback(async () => {
    try {
      const res = await fetch(`${apiBase}/api/v1/sessions/${sessionId}/paper`);
      const data = await res.json();
      if (data.success) {
        setFileId(data.file_id || null);
      }
    } catch (err) {
      console.error(err);
    }
  }, [sessionId, apiBase]);

  const fetchPaperObjects = useCallback(async () => {
    try {
      const res = await fetch(`${apiBase}/api/v1/sessions/${sessionId}/objects`);
      const data = await res.json();
      if (data.success) {
        setPaperObjects(data.objects || []);
      }
    } catch (err) {
      console.error(err);
    }
  }, [sessionId, apiBase]);

  const fetchTimeline = useCallback(async () => {
    try {
      const res = await fetch(`${apiBase}/api/v1/sessions/${sessionId}/timeline`);
      const data = await res.json();
      if (data.success) {
        setTimeline(data.timeline);
      }
    } catch (err) {
      console.error(err);
    }
  }, [sessionId, apiBase]);

  const fetchNotebook = useCallback(async () => {
    try {
      const res = await fetch(`${apiBase}/api/v1/sessions/${sessionId}/notebook`);
      const data = await res.json();
      if (data.success) {
        setNotebook(data.notebook);
      }
    } catch (err) {
      console.error(err);
    }
  }, [sessionId, apiBase]);

  useEffect(() => {
    fetchPaperDetails();
    fetchPaperObjects();
    fetchTimeline();
    fetchNotebook();
  }, [sessionId, fetchPaperDetails, fetchPaperObjects, fetchTimeline, fetchNotebook]);

  // Handle visible page scrolling events
  const handlePageChange = useCallback((pageNum: number) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: "page_visible",
        page: pageNum
      }));
    }
  }, [ws]);

  // Listen to WebSocket selection / progressive parsing returns
  useEffect(() => {
    if (!ws) return;
    const handleWsMessage = (event: MessageEvent) => {
      const data = JSON.parse(event.data);
      if (data.type === "selection_explanation") {
        setCurrentExplanation(data.explanation);
        setExplainingState(false);
        fetchTimeline();
      } else if (data.type === "progress_update") {
        setParsingStatus({
          step: data.step,
          msg: data.msg,
          page: data.page
        });
        if (data.step === "SECTIONS_READY" || data.step === "PAGE_PARSED") {
          fetchPaperDetails();
          fetchPaperObjects();
        }
      }
    };
    ws.addEventListener("message", handleWsMessage);
    return () => ws.removeEventListener("message", handleWsMessage);
  }, [ws, fetchPaperDetails, fetchPaperObjects, fetchTimeline]);

  // Submit selections to swarm orchestrator
  const triggerSwarmExplanation = (type: string) => {
    if (!ws || !selectedText) return;
    setShowHighlightMenu(false);
    setExplainingState(true);
    setActiveTab("explain");
    
    // Auto route swarm subtab focus
    const lowerType = type.toLowerCase();
    if (lowerType === "equation") setSwarmSubTab("math");
    else if (lowerType === "citation") setSwarmSubTab("explain");
    else setSwarmSubTab("explain");

    ws.send(JSON.stringify({
      type: "selection",
      text: selectedText,
      selection_type: type,
      id: selectedObjectId
    }));
  };

  const saveNoteToNotebook = async () => {
    if (!currentExplanation) return;
    try {
      const res = await fetch(`${apiBase}/api/v1/sessions/${sessionId}/notebook`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          selection_text: selectedText,
          selection_type: "HIGHLIGHT",
          ai_explanations: currentExplanation,
          user_note: userNoteText
        })
      });
      const data = await res.json();
      if (data.success) {
        setSavedNoteSuccess(true);
        setUserNoteText("");
        fetchNotebook();
        setTimeout(() => setSavedNoteSuccess(false), 3000);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Group objects by page number
  const groupedObjects = React.useMemo(() => {
    const groups: Record<number, any[]> = {};
    paperObjects.forEach((obj) => {
      const p = obj.page;
      if (!groups[p]) groups[p] = [];
      groups[p].push(obj);
    });
    return groups;
  }, [paperObjects]);

  return (
    <div className="flex-1 flex h-full w-full overflow-hidden bg-[#121212] select-text">
      
      {/* 1. Left Panel: Interactive Document Reader (70% width lock) */}
      <div className="w-[70%] flex flex-col h-full overflow-hidden border-r border-white/10 relative flex-shrink-0">
        {/* Reading Toolbar */}
        <div className="flex-shrink-0 flex items-center justify-between border-b border-white/10 px-4 h-[48px] bg-[#202124] select-none">
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-blue-400" />
            <h4 className="font-header text-xs font-semibold truncate max-w-xs">{fileId || "Research PDF Reader"}</h4>
            {parsingStatus && parsingStatus.step !== "COMPLETE" && (
              <div className="flex items-center gap-1 bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 rounded text-[8px] font-bold text-blue-400 uppercase animate-pulse">
                <span className="w-1 h-1 rounded-full bg-blue-500 animate-ping" />
                {parsingStatus.step === "SECTIONS_READY" ? "Progressive Ingestion" : parsingStatus.msg}
              </div>
            )}
            {parsingStatus && parsingStatus.step === "COMPLETE" && (
              <div className="flex items-center gap-1 bg-green-500/10 border border-green-500/20 px-2 py-0.5 rounded text-[8px] font-bold text-green-400 uppercase">
                ✓ Swarm Ready
              </div>
            )}
          </div>
          {/* Zoom Controls */}
          <div className="flex items-center gap-1.5 bg-[#121212] border border-white/10 rounded px-1.5 py-0.5">
            <button
              onClick={() => setZoom((z) => Math.max(z - 0.15, 0.75))}
              className="text-[10px] font-bold px-2 py-0.5 hover:bg-white/10 rounded text-slate-300 transition-colors"
              title="Zoom Out"
            >
              -
            </button>
            <span className="text-[9px] font-mono text-slate-400 px-1 font-bold">
              {Math.round(zoom * 100)}%
            </span>
            <button
              onClick={() => setZoom((z) => Math.min(z + 0.15, 2.5))}
              className="text-[10px] font-bold px-2 py-0.5 hover:bg-white/10 rounded text-slate-300 transition-colors"
              title="Zoom In"
            >
              +
            </button>
          </div>
        </div>

        {/* Scroll container for PDF */}
        <div className="flex-1 overflow-y-auto overflow-x-hidden bg-slate-950/40 relative">
          {fileId ? (
            <PdfViewer
              pdfUrl={`${apiBase}/uploads/${fileId}`}
              scale={zoom}
              objects={groupedObjects}
              onPageChange={handlePageChange}
              onTextSelect={(text, e) => {
                setSelectedText(text);
                setSelectedObjectId(null);
                setMenuPosition({ x: e.clientX, y: e.clientY - 40 });
                setShowHighlightMenu(true);
              }}
              onObjectSelect={(obj, e) => {
                setSelectedText(obj.text_content || `Selected ${obj.type}`);
                setSelectedObjectId(obj.id);
                setMenuPosition({ x: e.clientX, y: e.clientY - 40 });
                setShowHighlightMenu(true);
              }}
            />
          ) : (
            <div className="flex items-center justify-center h-full text-slate-500 gap-2 p-8">
              <FileText className="w-12 h-12 stroke-[1.5]" />
              <p>Upload a scientific paper to initialize the reading interface.</p>
            </div>
          )}
        </div>
      </div>

      {/* Floating Selection Toolbar */}
      {showHighlightMenu && (
        <div 
          style={{ top: menuPosition.y, left: menuPosition.x }}
          className="fixed bg-gray-900/95 border border-blue-500/30 shadow-[0_0_15px_rgba(59,130,246,0.3)] rounded-lg p-2 flex gap-1.5 z-50 animate-in fade-in zoom-in-95 duration-100"
        >
          {["Explain", "Math", "Background", "Visual", "Citation"].map((type) => (
            <button
              key={type}
              onClick={() => triggerSwarmExplanation(type)}
              className="text-[9px] uppercase font-bold px-2 py-1 bg-white/5 hover:bg-blue-600 text-slate-200 hover:text-white rounded transition-colors"
            >
              {type}
            </button>
          ))}
        </div>
      )}

      {/* 2. Right Panel: Swarm Sidebar Tools (30% width lock) */}
      <div className="w-[30%] flex flex-col h-full bg-[#1e1e1e] overflow-hidden flex-shrink-0">
        {/* Navigation Tabs */}
        <div className="flex-shrink-0 flex border-b border-white/10 bg-[#202124] h-[48px] select-none">
          {(["explain", "notebook", "timeline"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 py-3 text-[10px] font-bold uppercase tracking-wider transition-all border-b-2 ${
                activeTab === tab 
                  ? "border-blue-500 text-blue-400 bg-white/5" 
                  : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-white/5"
              }`}
            >
              {tab === "explain" && "Swarm Analyst"}
              {tab === "notebook" && "Notebook"}
              {tab === "timeline" && "Timeline"}
            </button>
          ))}
        </div>

        {/* Tab Viewport */}
        <div className="flex-1 relative overflow-hidden bg-[#1e1e1e]">
          
          {/* TAB 1: Swarm Analyst */}
          <div className={`absolute inset-0 flex flex-col ${activeTab === "explain" ? "block" : "hidden"}`}>
            {/* Agent Sub-Tabs */}
            <div className="flex-shrink-0 flex border-b border-white/5 bg-[#121212] px-2 py-1 gap-1 select-none">
              {(["explain", "math", "background", "visual", "questions"] as const).map((sub) => (
                <button
                  key={sub}
                  onClick={() => setSwarmSubTab(sub)}
                  className={`px-2 py-1 text-[8px] font-bold uppercase tracking-wider rounded transition-all ${
                    swarmSubTab === sub 
                      ? "bg-blue-600 text-white" 
                      : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
                  }`}
                >
                  {sub}
                </button>
              ))}
            </div>

            {/* Explanation scroll content */}
            <div className="flex-1 overflow-y-auto p-5 scrollable">
              {explainingState ? (
                <div className="flex flex-col items-center justify-center h-full py-20 text-slate-500 gap-3">
                  <div className="w-8 h-8 rounded-full border-2 border-slate-700 border-t-blue-500 animate-spin" />
                  <p className="text-[10px] uppercase font-bold animate-pulse text-blue-400">Swarm agents collaborating...</p>
                </div>
              ) : currentExplanation ? (
                <div className="flex flex-col gap-6 text-slate-300">
                  
                  {/* Selected Highlight Context */}
                  <div className="bg-[#121212] border border-white/5 p-3 rounded text-xs italic border-l-2 border-l-blue-500">
                    "{selectedText}"
                  </div>

                  {/* SUB-TABS RENDER */}
                  {swarmSubTab === "explain" && (
                    <div className="flex flex-col gap-4 animate-in fade-in slide-in-from-bottom-2 duration-200">
                      <div>
                        <h5 className="text-[9px] uppercase font-bold text-blue-400 mb-1">Simple Intuition</h5>
                        <p className="text-xs leading-relaxed">{currentExplanation.explanation?.explanation?.level_1 || currentExplanation.level_1 || "Select a part of the paper to generate simple explanations."}</p>
                      </div>
                      <div>
                        <h5 className="text-[9px] uppercase font-bold text-blue-400 mb-1">Detailed Mechanics</h5>
                        <p className="text-xs leading-relaxed">{currentExplanation.explanation?.explanation?.level_2 || currentExplanation.level_2}</p>
                      </div>
                      <div>
                        <h5 className="text-[9px] uppercase font-bold text-blue-400 mb-1">Author Choice Intent</h5>
                        <p className="text-xs leading-relaxed">{currentExplanation.explanation?.explanation?.why_this_matters?.author_intent || currentExplanation.why_this_matters?.author_intent}</p>
                      </div>
                    </div>
                  )}

                  {swarmSubTab === "math" && (
                    <div className="flex flex-col gap-4 animate-in fade-in slide-in-from-bottom-2 duration-200">
                      <h5 className="text-[9px] uppercase font-bold text-purple-400 mb-1">Equation Derivations</h5>
                      <div className="latex-math text-center py-4 my-2 text-white">
                        {currentExplanation.math?.latex_clean || currentExplanation.explanation?.explanation?.level_4 || currentExplanation.level_4 || "N/A"}
                      </div>
                      <div>
                        <h5 className="text-[9px] uppercase font-bold text-purple-400 mb-1">Variables Definition</h5>
                        {currentExplanation.math?.variable_definitions ? (
                          <div className="grid grid-cols-4 gap-2 text-xs">
                            {Object.entries(currentExplanation.math.variable_definitions).map(([k, v]: any) => (
                              <React.Fragment key={k}>
                                <span className="font-mono font-bold text-white">{k}</span>
                                <span className="col-span-3 text-slate-400">{v}</span>
                              </React.Fragment>
                            ))}
                          </div>
                        ) : (
                          <p className="text-xs text-slate-500">No math variables mapped for this object.</p>
                        )}
                      </div>
                    </div>
                  )}

                  {swarmSubTab === "background" && (
                    <div className="flex flex-col gap-4 animate-in fade-in slide-in-from-bottom-2 duration-200">
                      <h5 className="text-[9px] uppercase font-bold text-amber-400 mb-1">Prerequisite Concepts</h5>
                      {currentExplanation.background?.prerequisites ? (
                        <div className="flex flex-col gap-3">
                          {currentExplanation.background.prerequisites.map((p: string, i: number) => (
                            <div key={i} className="bg-white/5 border border-white/5 p-3 rounded">
                              <span className="text-xs font-bold text-white block mb-1">{p}</span>
                              <p className="text-xs text-slate-400">{currentExplanation.background.brief_explanations?.[p] || "Core background knowledge."}</p>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-xs text-slate-500">No prerequisites mapped for this object.</p>
                      )}
                    </div>
                  )}

                  {swarmSubTab === "visual" && (
                    <div className="flex flex-col gap-4 animate-in fade-in slide-in-from-bottom-2 duration-200">
                      <h5 className="text-[9px] uppercase font-bold text-green-400 mb-1">Flowcharts & Architectures</h5>
                      <pre className="bg-[#121212] border border-white/5 p-3 rounded text-[10px] font-mono text-green-400 overflow-x-auto leading-tight">
                        {currentExplanation.visual?.diagram || "+-----------------+\n| Selected Node   |\n+-----------------+"}
                      </pre>
                      <p className="text-xs text-slate-400">{currentExplanation.visual?.explanation}</p>
                    </div>
                  )}

                  {swarmSubTab === "questions" && (
                    <div className="flex flex-col gap-4 animate-in fade-in slide-in-from-bottom-2 duration-200">
                      <h5 className="text-[9px] uppercase font-bold text-blue-400 mb-1">Predicted Follow-up Questions</h5>
                      {currentExplanation.questions?.questions ? (
                        <div className="flex flex-col gap-2">
                          {currentExplanation.questions.questions.map((q: string, idx: number) => (
                            <button
                              key={idx}
                              onClick={() => {
                                setSelectedText(q);
                                setSelectedObjectId(null);
                                triggerSwarmExplanation("TEXT");
                              }}
                              className="text-left text-xs bg-white/5 border border-white/5 p-2 rounded hover:bg-blue-600 hover:text-white transition-colors"
                            >
                              {q}
                            </button>
                          ))}
                        </div>
                      ) : (
                        <p className="text-xs text-slate-500">No predictions generated.</p>
                      )}
                    </div>
                  )}

                  {/* Save Note to Research Notebook Widget */}
                  <div className="mt-8 border-t border-white/5 pt-6">
                    <h5 className="text-[9px] uppercase font-bold text-slate-400 mb-2">Save to Research Notebook</h5>
                    <div className="flex gap-2">
                      <input 
                        type="text" 
                        placeholder="Add personal note annotations..."
                        value={userNoteText}
                        onChange={(e) => setUserNoteText(e.target.value)}
                        className="flex-1 bg-[#121212] border border-white/10 rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
                      />
                      <button 
                        onClick={saveNoteToNotebook}
                        className="bg-blue-600 hover:bg-blue-700 text-white rounded p-1.5 transition-colors"
                        title="Save annotation"
                      >
                        <Plus className="w-4 h-4" />
                      </button>
                    </div>
                    {savedNoteSuccess && (
                      <p className="text-[10px] text-green-400 font-bold uppercase mt-2">Note saved successfully!</p>
                    )}
                  </div>

                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-full py-20 text-slate-500 gap-2">
                  <AlertCircle className="w-8 h-8 stroke-[1.5]" />
                  <p className="text-xs">Click any equation, figure, table, citation, or drag to highlight paragraphs.</p>
                </div>
              )}
            </div>
          </div>

          {/* TAB 2: Research Notebook */}
          <div className={`absolute inset-0 overflow-y-auto p-5 scrollable ${activeTab === "notebook" ? "block" : "hidden"}`}>
            <h5 className="text-[9px] uppercase font-bold text-slate-400 mb-4 tracking-wider">Research Notebook Annotations</h5>
            {notebook.length > 0 ? (
              <div className="flex flex-col gap-4">
                {notebook.map((item) => (
                  <div key={item.id} className="bg-white/5 border border-white/5 p-4 rounded-lg flex flex-col gap-2">
                    <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-400">
                      <Bookmark className="w-3.5 h-3.5 text-blue-400" />
                      <span className="uppercase text-blue-400">{item.selection_type}</span>
                      <span>•</span>
                      <span>{new Date(item.created_at).toLocaleDateString()}</span>
                    </div>
                    <p className="text-xs text-white italic bg-[#121212] p-2 rounded">"{item.selection_text}"</p>
                    {item.user_note && (
                      <p className="text-xs text-slate-300 font-medium">My note: {item.user_note}</p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 text-center py-10">No notebook annotations saved yet.</p>
            )}
          </div>

          {/* TAB 3: History Timeline */}
          <div className={`absolute inset-0 overflow-y-auto p-5 scrollable ${activeTab === "timeline" ? "block" : "hidden"}`}>
            <h5 className="text-[9px] uppercase font-bold text-slate-400 mb-4 tracking-wider">Reading History Timeline</h5>
            {timeline.length > 0 ? (
              <div className="flex flex-col gap-4">
                {timeline.map((item) => (
                  <div key={item.id} className="border-l-2 border-slate-700 pl-4 relative ml-2">
                    <span className="absolute -left-1.5 top-1 w-2 h-2 rounded-full bg-blue-500" />
                    <div className="flex flex-col gap-1">
                      <span className="text-[10px] font-bold text-blue-400 uppercase tracking-wider">{item.action_type}</span>
                      <p className="text-xs text-slate-300">{item.details?.text || "Interaction logged"}</p>
                      <span className="text-[9px] text-slate-500">{new Date(item.created_at).toLocaleTimeString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 text-center py-10">Start reading and highlighting to build a history timeline.</p>
            )}
          </div>

        </div>
      </div>
      
    </div>
  );
};
