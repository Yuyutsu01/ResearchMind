import React, { useState, useEffect, useRef, useCallback } from "react";
import { BookOpen, AlertCircle, FileText, ChevronRight, Bookmark, Plus, Bug } from "lucide-react";
import { FloatingToolbar } from "./FloatingToolbar";
import { spatialIndex } from "@/lib/spatial_index";
import { DocumentObject } from "@/lib/document_model";
import { textLayerManager } from "@/lib/TextLayerManager";
import { pageCache } from "@/lib/PageCache";
import { selectionEngine } from "@/lib/SelectionEngine";
import { semanticResolver } from "@/lib/SemanticResolver";

// 1. High-fidelity canvas-based scrollable PDF Page Viewer components
interface PdfPageProps {
  pdfUrl: string;
  pageNumber: number;
  scale: number;
  objects: any[];
  isVisible: boolean;
  debugMode?: boolean;
  defaultPageSize: { width: number; height: number } | null;
  registerRef: (node: HTMLDivElement | null, pageNum: number) => void;
  onTextSelect: (text: string, range: Range | null, matchedObj?: DocumentObject | null) => void;
  onObjectSelect: (obj: any, e: React.MouseEvent) => void;
}

const PdfPage: React.FC<PdfPageProps> = ({ 
  pdfUrl, 
  pageNumber, 
  scale, 
  objects, 
  isVisible, 
  debugMode = false,
  defaultPageSize, 
  registerRef, 
  onTextSelect, 
  onObjectSelect 
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const textLayerRef = useRef<HTMLDivElement>(null);
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

        // Render official PDF.js Native Text Layer via TextLayerManager
        const textLayerDiv = textLayerRef.current;
        if (textLayerDiv) {
          await textLayerManager.renderTextLayer(pageNumber, page, viewport, scale, textLayerDiv);
        }
      } catch (err) {
        console.error("Error rendering PDF page native text layer", err);
      }
    };

    renderPage();
    return () => {
      active = false;
    };
  }, [pdfUrl, pageNumber, scale, isVisible]);

  const handleMouseUp = () => {
    const sel = selectionEngine.getSelection();
    if (!sel || !containerRef.current) return;

    const containerRect = containerRef.current.getBoundingClientRect();

    // Convert selection screen pixels to scaled page coordinates
    const pdfBBox = {
      x0: (sel.bounds!.left - containerRect.left) / scale,
      y0: (sel.bounds!.top - containerRect.top) / scale,
      x1: (sel.bounds!.right - containerRect.left) / scale,
      y1: (sel.bounds!.bottom - containerRect.top) / scale,
    };

    // Perform sub-1ms hit-testing against RBush Spatial Index
    const matchedObj = spatialIndex.resolveSelectionObject(pageNumber, pdfBBox, sel.text);
    
    onTextSelect(sel.text, sel.range, matchedObj);
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
      className={`relative mx-auto bg-slate-900 shadow-xl border ${
        debugMode ? "border-amber-500/50" : "border-white/5"
      } rounded-lg overflow-hidden select-text mb-6 transition-opacity duration-300`}
      style={{ width: `${viewportSize.width}px`, height: `${viewportSize.height}px` }}
    >
      {/* High-fidelity clean PDF Canvas (visually identical to Adobe Reader) */}
      <canvas ref={canvasRef} className="absolute inset-0 z-0 pointer-events-none" />

      {/* Official PDF.js Native Text Layer Container */}
      <div 
        ref={textLayerRef}
        className={`textLayer absolute inset-0 z-10 select-text overflow-hidden ${
          debugMode ? "bg-amber-500/5 border border-dashed border-amber-500/30" : ""
        }`} 
        style={{ width: `${viewportSize.width}px`, height: `${viewportSize.height}px` }}
      />

      {/* Developer Debug Overlay (Feature Flag DEBUG_TEXT_LAYER) */}
      {debugMode && (
        <div className="absolute top-2 left-2 z-30 bg-amber-500 text-black font-mono font-bold text-[9px] px-1.5 py-0.5 rounded shadow pointer-events-none select-none">
          DEBUG PAGE {pageNumber} | objects: {objects.length}
        </div>
      )}
    </div>
  );
};

interface PdfViewerProps {
  pdfUrl: string;
  scale: number;
  objects: Record<number, any[]>;
  debugMode?: boolean;
  onPageChange: (pageNum: number) => void;
  onTextSelect: (text: string, range: Range | null, matchedObj?: DocumentObject | null) => void;
  onObjectSelect: (obj: any, e: React.MouseEvent) => void;
}

const PdfViewer: React.FC<PdfViewerProps> = ({ 
  pdfUrl, 
  scale, 
  objects, 
  debugMode = false,
  onPageChange,
  onTextSelect, 
  onObjectSelect 
}) => {
  const [numPages, setNumPages] = useState<number>(0);
  const [currentPage, setCurrentPage] = useState<number>(1);
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

  // Set up intersection observer for virtualization with pageCache buffer
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
                setCurrentPage(pageNum);
                onPageChange(pageNum);
              }
            }
          });
          return next;
        });
      },
      {
        root: containerRef.current,
        rootMargin: "650px 0px", // Larger buffer for selection survival
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
          // Phase 5: Virtual page cache keeps active page ± 2 surrounding pages mounted
          const isPageVisible = pageCache.isPageMounted(pageNum, currentPage, numPages) || !!visiblePages[pageNum];

          return (
            <PdfPage 
              key={pageNum} 
              pdfUrl={pdfUrl} 
              pageNumber={pageNum} 
              scale={scale}
              objects={objects[pageNum] || []}
              isVisible={isPageVisible}
              debugMode={debugMode}
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
  
  // Developer Debug Mode state (DEBUG_TEXT_LAYER)
  const [debugMode, setDebugMode] = useState<boolean>(false);

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

  // Selection & spatial document state
  const [selectedDocumentObject, setSelectedDocumentObject] = useState<DocumentObject | null>(null);
  const [selectedRange, setSelectedRange] = useState<Range | null>(null);
  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);

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
        // Load into spatial index for sub-1ms hit detection
        spatialIndex.loadObjects(data.objects || []);
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

  // Submit selections to swarm orchestrator with enriched document object metadata
  const triggerSwarmExplanation = (type: string, customPrompt?: string) => {
    if (!ws || !selectedText) return;
    setShowHighlightMenu(false);

    if (type === "Notebook") {
      saveNoteToNotebook();
      return;
    }

    setExplainingState(true);
    setActiveTab("explain");
    
    // Auto route swarm subtab focus
    const lowerType = type.toLowerCase();
    if (lowerType === "equation" || lowerType === "math") setSwarmSubTab("math");
    else if (lowerType === "visual") setSwarmSubTab("visual");
    else setSwarmSubTab("explain");

    // Phase 8: Resolve structured semantic payload
    const dummyBBox = { x0: 0, y0: 0, x1: 0, y1: 0 };
    const semanticContext = semanticResolver.resolveContext(
      selectedDocumentObject?.page || 1,
      dummyBBox,
      selectedText,
      selectedDocumentObject
    );

    const payload: any = {
      type: "selection",
      text: selectedText,
      selection_type: type,
      id: selectedObjectId || selectedDocumentObject?.id || null,
      custom_prompt: customPrompt || null,
      document_object: semanticContext
    };

    ws.send(JSON.stringify(payload));
  };

  const saveNoteToNotebook = async () => {
    try {
      const res = await fetch(`${apiBase}/api/v1/sessions/${sessionId}/notebook`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          selection_text: selectedText,
          selection_type: "HIGHLIGHT",
          ai_explanations: currentExplanation || { summary: "User Highlighted Note" },
          user_note: userNoteText || selectedText
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
          
          {/* Zoom & Developer Debug Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setDebugMode(!debugMode)}
              className={`flex items-center gap-1 text-[9px] font-mono font-bold px-2 py-1 rounded border transition-all ${
                debugMode
                  ? "bg-amber-500 text-black border-amber-400 shadow-[0_0_10px_rgba(245,158,11,0.5)]"
                  : "bg-white/5 text-slate-400 hover:text-white border-white/10"
              }`}
              title="Toggle Developer Debug Overlay (DEBUG_TEXT_LAYER)"
            >
              <Bug className="w-3 h-3" />
              <span>{debugMode ? "DEBUG ON" : "DEBUG"}</span>
            </button>

            <div className="flex items-center gap-1.5 bg-[#121212] border border-white/10 rounded px-1.5 py-0.5">
              <button
                onClick={() => {
                  setZoom((z) => Math.max(z - 0.15, 0.75));
                  textLayerManager.invalidateCache();
                }}
                className="text-[10px] font-bold px-2 py-0.5 hover:bg-white/10 rounded text-slate-300 transition-colors"
                title="Zoom Out"
              >
                -
              </button>
              <span className="text-[9px] font-mono text-slate-400 px-1 font-bold">
                {Math.round(zoom * 100)}%
              </span>
              <button
                onClick={() => {
                  setZoom((z) => Math.min(z + 0.15, 2.5));
                  textLayerManager.invalidateCache();
                }}
                className="text-[10px] font-bold px-2 py-0.5 hover:bg-white/10 rounded text-slate-300 transition-colors"
                title="Zoom In"
              >
                +
              </button>
            </div>
          </div>
        </div>

        {/* Scroll container for PDF */}
        <div className="flex-1 overflow-y-auto overflow-x-hidden bg-slate-950/40 relative">
          {fileId ? (
            <PdfViewer
              pdfUrl={`${apiBase}/uploads/${fileId}`}
              scale={zoom}
              objects={groupedObjects}
              debugMode={debugMode}
              onPageChange={handlePageChange}
              onTextSelect={(text, range, matchedObj) => {
                setSelectedText(text);
                setSelectedRange(range);
                setTargetRect(range ? range.getBoundingClientRect() : null);
                setSelectedDocumentObject(matchedObj || null);
                setSelectedObjectId(matchedObj ? matchedObj.id : null);
                setShowHighlightMenu(true);
              }}
              onObjectSelect={(obj, e) => {
                setSelectedText(obj.text_content || `Selected ${obj.type}`);
                setSelectedRange(null);
                setTargetRect(e.currentTarget.getBoundingClientRect());
                setSelectedDocumentObject(obj);
                setSelectedObjectId(obj.id);
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

      {/* Floating AI Toolbar with Floating UI Positioning (< 16ms appearance) */}
      {showHighlightMenu && (
        <FloatingToolbar
          range={selectedRange}
          targetRect={targetRect}
          selectedText={selectedText}
          selectedType={selectedDocumentObject?.type}
          onAction={(type, customPrompt) => triggerSwarmExplanation(type, customPrompt)}
          onClose={() => setShowHighlightMenu(false)}
        />
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
