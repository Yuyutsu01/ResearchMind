import React, { useState, useEffect, useRef } from "react";
import { 
  BookOpen, Clock, FileText, Share2, Layers, Award, AlertTriangle, 
  HelpCircle, ChevronRight, Save, Plus, ArrowRight, Zap, RefreshCw 
} from "lucide-react";
import cytoscape from "cytoscape";

// 1. Interactive Latex Components
interface LatexProps {
  math: string;
  block?: boolean;
}

export const Latex: React.FC<LatexProps> = ({ math, block = false }) => {
  const containerRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (containerRef.current && (window as any).katex) {
      try {
        (window as any).katex.render(math, containerRef.current, {
          displayMode: block,
          throwOnError: false,
        });
      } catch (err) {
        console.error("KaTeX error", err);
      }
    }
  }, [math, block]);

  return <span ref={containerRef} className={block ? "block my-3 text-center" : "inline-block px-0.5"} dangerouslySetInnerHTML={{ __html: math }} />;
};

export const renderTextWithLatex = (text: string) => {
  if (!text) return "";
  const parts = text.split(/(\$\$.*?\$\$|\$.*?\$)/g);
  return parts.map((part, index) => {
    if (part.startsWith("$$") && part.endsWith("$$")) {
      return <Latex key={index} math={part.slice(2, -2)} block={true} />;
    } else if (part.startsWith("$") && part.endsWith("$")) {
      return <Latex key={index} math={part.slice(1, -1)} block={false} />;
    }
    return <span key={index}>{part}</span>;
  });
};

// 2. High-fidelity canvas-based scrollable PDF Page Viewer components
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
  onTextSelect: (text: string, e: React.MouseEvent) => void;
  onObjectSelect: (obj: any, e: React.MouseEvent) => void;
}

const PdfViewer: React.FC<PdfViewerProps> = ({ pdfUrl, scale, objects, onTextSelect, onObjectSelect }) => {
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
        
        // Measure first page baseline dimensions for placeholder sizing
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
            }
          });
          return next;
        });
      },
      {
        root: containerRef.current,
        rootMargin: "450px 0px", // Loads/renders 450px before entering viewport
        threshold: 0.01
      }
    );

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, []);

  const registerPageRef = React.useCallback((node: HTMLDivElement | null, pageNum: number) => {
    if (node && observerRef.current) {
      observerRef.current.observe(node);
    }
  }, []);

  return (
    <div ref={containerRef} className="flex-1 flex flex-col gap-6 overflow-y-auto p-6 bg-slate-950/60 scrollable select-text">
      {numPages > 0 ? (
        Array.from({ length: numPages }, (_, i) => {
          const pageNum = i + 1;
          // Render page if it's visible, or if its direct neighbor is visible (prefetch padding)
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
  onRefreshGraph: () => void;
}

export const ReadingWorkspace: React.FC<ReadingWorkspaceProps> = ({ sessionId, apiBase, ws, onRefreshGraph }) => {
  // Reading States
  const [sections, setSections] = useState<Record<string, string>>({});
  const [fileId, setFileId] = useState<string | null>(null);
  const [zoom, setZoom] = useState<number>(1.3);
  const [activeSection, setActiveSection] = useState<string>("");
  const [selectedText, setSelectedText] = useState("");
  const [showHighlightMenu, setShowHighlightMenu] = useState(false);
  const [menuPosition, setMenuPosition] = useState({ x: 0, y: 0 });
  const [paperObjects, setPaperObjects] = useState<any[]>([]);
  const [selectedObjectId, setSelectedObjectId] = useState<string | null>(null);

  // Right sidebar tab state: 'explain' | 'graph' | 'notebook' | 'timeline'
  const [activeTab, setActiveTab] = useState<"explain" | "graph" | "notebook" | "timeline">("explain");
  const [swarmSubTab, setSwarmSubTab] = useState<"explain" | "math" | "critique" | "related" | "code" | "notes">("explain");
  const [currentExplanation, setCurrentExplanation] = useState<any>(null);
  const [explanationLevel, setExplanationLevel] = useState<number>(1);
  const [explainingState, setExplainingState] = useState(false);

  // Notebook state
  const [notebook, setNotebook] = useState<any[]>([]);
  const [userNoteText, setUserNoteText] = useState("");
  const [savedNoteSuccess, setSavedNoteSuccess] = useState(false);

  // Timeline state
  const [timeline, setTimeline] = useState<any[]>([]);

  // Citation Graph Refs
  const cytoscapeRef = useRef<HTMLDivElement>(null);
  const [graphFilter, setGraphFilter] = useState("all");

  const [parsingStatus, setParsingStatus] = useState<{ step: string; msg: string; page?: number } | null>(null);

  const fetchPaper = async () => {
    try {
      const res = await fetch(`${apiBase}/api/v1/sessions/${sessionId}/paper`);
      const data = await res.json();
      if (data.success) {
        setSections(data.sections || {});
        setFileId(data.file_id || null);
        const firstSection = Object.keys(data.sections || {})[0] || "";
        setActiveSection(firstSection);
      }
    } catch (err) {
      console.error("Failed to load paper sections", err);
    }
  };

  // Load paper content and initial timeline/notebook
  useEffect(() => {
    fetchPaper();
    fetchTimeline();
    fetchNotebook();
    fetchPaperObjects();
  }, [sessionId, apiBase]);

  // Fetch paper objects from DB
  const fetchPaperObjects = async () => {
    try {
      const res = await fetch(`${apiBase}/api/v1/sessions/${sessionId}/objects`);
      const data = await res.json();
      if (data.success) {
        setPaperObjects(data.objects || []);
      }
    } catch (err) {
      console.error("Failed to load paper objects", err);
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

  // Fetch timeline from DB
  const fetchTimeline = async () => {
    try {
      const res = await fetch(`${apiBase}/api/v1/sessions/${sessionId}/timeline`);
      const data = await res.json();
      if (data.success) {
        setTimeline(data.timeline);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Fetch notebook from DB
  const fetchNotebook = async () => {
    try {
      const res = await fetch(`${apiBase}/api/v1/sessions/${sessionId}/notebook`);
      const data = await res.json();
      if (data.success) {
        setNotebook(data.notebook);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Text selection handler in reading view
  const handleTextSelection = (e: React.MouseEvent) => {
    const selection = window.getSelection();
    if (!selection) return;
    const text = selection.toString().trim();
    if (text.length > 2) {
      setSelectedText(text);
      setMenuPosition({ x: e.clientX, y: e.clientY - 40 });
      setShowHighlightMenu(true);
    } else {
      setShowHighlightMenu(false);
    }
  };

  // Submit highlight selection to the Swarm
  const triggerSwarmExplanation = (type: string) => {
    if (!ws || !selectedText) return;
    setShowHighlightMenu(false);
    setExplainingState(true);
    setActiveTab("explain");
    setExplanationLevel(1); // Reset level

    ws.send(JSON.stringify({
      type: "selection",
      text: selectedText,
      selection_type: type,
      id: selectedObjectId
    }));
  };

  // Listen for Selection WebSocket returns
  useEffect(() => {
    if (!ws) return;
    const handleWsMessage = (event: MessageEvent) => {
      const data = JSON.parse(event.data);
      if (data.type === "selection_explanation") {
        setCurrentExplanation(data.explanation);
        setExplainingState(false);
        fetchTimeline(); // Reload timeline
        onRefreshGraph(); // Refresh the main Cytoscape graph
      } else if (data.type === "progress_update") {
        setParsingStatus({
          step: data.step,
          msg: data.msg,
          page: data.page
        });
        if (data.step === "SECTIONS_READY" || data.step === "PAGE_PARSED") {
          fetchPaper();
          fetchPaperObjects();
        }
      }
    };
    ws.addEventListener("message", handleWsMessage);
    return () => ws.removeEventListener("message", handleWsMessage);
  }, [ws]);

  // Save selection explanation to the Research Notebook database
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

  // Render citation graph inside the tab
  useEffect(() => {
    if (activeTab !== "graph" || !cytoscapeRef.current) return;
    
    // Obsidian style visualizer
    const cy = cytoscape({
      container: cytoscapeRef.current,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#3B82F6',
            'label': 'data(label)',
            'color': '#fff',
            'font-size': '10px',
            'text-valign': 'center',
            'text-halign': 'center',
            'width': '60px',
            'height': '60px',
            'border-width': '2px',
            'border-color': '#1E3A8A'
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#4B5563',
            'target-arrow-color': '#4B5563',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(relationship)',
            'font-size': '8px',
            'color': '#9CA3AF'
          }
        }
      ],
      elements: [
        // Dummy mock elements for citation graph
        { data: { id: 'root', label: 'This Paper' } },
        { data: { id: 'ref1', label: 'Attention (2017)' } },
        { data: { id: 'ref2', label: 'PPO (2017)' } },
        { data: { id: 'ref3', label: 'HER (2018)' } },
        { data: { id: 'concept1', label: 'Self-Attention' } },
        { data: { id: 'concept2', label: 'Reward Shaping' } },
        { data: { source: 'root', target: 'ref1', relationship: 'cites' } },
        { data: { source: 'root', target: 'ref2', relationship: 'extends' } },
        { data: { source: 'root', target: 'ref3', relationship: 'contradicts' } },
        { data: { source: 'ref1', target: 'concept1', relationship: 'uses' } },
        { data: { source: 'ref2', target: 'concept2', relationship: 'uses' } },
      ],
      layout: {
        name: 'cose',
        animate: false
      }
    });

    return () => {
      cy.stop();
      cy.destroy();
    };
  }, [activeTab]);

  return (
    <div className="flex-1 flex h-full w-full overflow-hidden bg-[#121212] select-text">
      
      {/* 1. Left Panel: Interactive Document Reader (70% width lock) */}
      <div className="w-[70%] flex flex-col h-full overflow-hidden border-r border-white/10 relative flex-shrink-0">
        {/* Sticky Reading Toolbar (fixed) */}
        <div className="flex-shrink-0 flex items-center justify-between border-b border-white/10 px-4 h-[48px] bg-[#202124] select-none">
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-blue-400" />
            <h4 className="font-header text-xs font-semibold truncate max-w-xs">{fileId || "Scientific Paper Reader"}</h4>
            {parsingStatus && parsingStatus.step !== "COMPLETE" && (
              <div className="flex items-center gap-1 bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 rounded text-[8px] font-bold text-blue-400 uppercase animate-pulse">
                <span className="w-1 h-1 rounded-full bg-blue-500 animate-ping" />
                {parsingStatus.step === "SECTIONS_READY" ? "Progressive Loading" : parsingStatus.msg}
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

        {/* Scroll container for PDF (scrolls independently) */}
        <div className="flex-1 overflow-y-auto overflow-x-hidden bg-slate-950/40 relative">
          {fileId ? (
            <PdfViewer
              pdfUrl={`${apiBase}/uploads/${fileId}`}
              scale={zoom}
              objects={groupedObjects}
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
              <p>Upload a research paper to initialize the reading interface.</p>
            </div>
          )}
        </div>
      </div>

      {/* Sticky Floating Selection Toolbar (anchored to selection) */}
      {showHighlightMenu && (
        <div 
          style={{ top: menuPosition.y, left: menuPosition.x }}
          className="fixed bg-gray-900/95 border border-blue-500/30 shadow-[0_0_15px_rgba(59,130,246,0.3)] rounded-lg p-2 flex gap-1.5 z-50 animate-in fade-in zoom-in-95 duration-100"
        >
          {[
            { id: "explain", label: "Explain" },
            { id: "math", label: "Math" },
            { id: "critique", label: "Critique" },
            { id: "code", label: "Code" },
            { id: "related", label: "Related" },
            { id: "notes", label: "Add Note" }
          ].map((opt) => (
            <button
              key={opt.id}
              onClick={() => {
                setSwarmSubTab(opt.id as any);
                triggerSwarmExplanation(opt.id.toUpperCase());
              }}
              className="text-[9px] uppercase font-bold px-2 py-1 bg-white/5 hover:bg-blue-600 text-slate-200 hover:text-white rounded transition-colors"
            >
              {opt.label}
            </button>
          ))}
        </div>
      )}

      {/* 2. Right Panel: Swarm Sidebar Tools (30% width lock) */}
      <div className="w-[30%] flex flex-col h-full bg-[#1e1e1e] overflow-hidden flex-shrink-0">
        {/* Navigation Tabs (Fixed) */}
        <div className="flex-shrink-0 flex border-b border-white/10 bg-[#202124] h-[48px] select-none">
          {(["explain", "graph", "notebook", "timeline"] as const).map((tab) => (
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
              {tab === "graph" && "Citation Map"}
              {tab === "notebook" && "Notebook"}
              {tab === "timeline" && "Timeline"}
            </button>
          ))}
        </div>

        {/* Tab Viewport holding absolute, independently-scrollable tab panels (preserves scroll state) */}
        <div className="flex-1 relative overflow-hidden bg-[#1e1e1e]">
          
          {/* TAB 1: Swarm Analyst */}
          <div className={`absolute inset-0 overflow-y-auto p-5 scrollable space-y-6 ${activeTab === 'explain' ? 'block' : 'hidden'}`}>
            {explainingState ? (
              <div className="flex flex-col gap-4 p-4 bg-[#121212] border border-white/5 rounded-xl">
                <div className="flex items-center gap-2 text-xs text-blue-400 font-bold uppercase tracking-wider animate-pulse">
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Swarm analyzing selection...</span>
                </div>
                
                {/* Swarm checklist panel */}
                <div className="flex flex-col gap-2.5 text-xs text-slate-400 font-medium">
                  <div className="flex items-center justify-between">
                    <span>Explorer Agent checking literature...</span>
                    <span className="text-[10px] text-emerald-400 font-bold">✓ Active</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Analyst Agent explaining concept...</span>
                    <span className="text-[10px] text-blue-400 font-bold">● Running</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Critic Agent checking assumptions...</span>
                    <span className="text-[10px] text-amber-500 animate-pulse">● Waiting</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Synthesizer Agent updating knowledge graph...</span>
                    <span className="text-[10px] text-slate-600">● Queued</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Memory Keeper logging notes...</span>
                    <span className="text-[10px] text-slate-600">● Queued</span>
                  </div>
                </div>
              </div>
            ) : currentExplanation ? (
              <div className="space-y-5 animate-in fade-in duration-200">
                <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3">
                  <span className="text-[9px] uppercase font-bold text-blue-400">Selection Lens active</span>
                  <p className="text-xs font-medium text-white italic mt-1 font-serif">"{selectedText}"</p>
                </div>

                {/* Swarm Sub Tabs */}
                <div className="flex border-b border-white/5 text-[10px] uppercase font-bold tracking-wide">
                  {[
                    { id: "explain", label: "Explain" },
                    { id: "math", label: "Math" },
                    { id: "critique", label: "Critique" },
                    { id: "related", label: "Related" },
                    { id: "code", label: "Code" },
                    { id: "notes", label: "Notes" }
                  ].map((subTab) => (
                    <button
                      key={subTab.id}
                      onClick={() => setSwarmSubTab(subTab.id as any)}
                      className={`flex-1 py-2 text-center border-b-2 transition-colors ${
                        swarmSubTab === subTab.id 
                          ? "border-blue-500 text-blue-400 bg-white/5" 
                          : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-white/5"
                      }`}
                    >
                      {subTab.label}
                    </button>
                  ))}
                </div>

                {/* Sub Tab Viewport */}
                <div className="text-xs text-slate-300 leading-relaxed min-h-[150px] space-y-4 pt-2">
                  {swarmSubTab === "explain" && (
                    <div className="space-y-4">
                      <div>
                        <strong className="text-[11px] text-white block mb-1 uppercase tracking-wider text-slate-400">Core Intuition (Lvl 1):</strong>
                        <p className="text-slate-300 leading-relaxed font-serif text-sm bg-white/5 p-3 rounded-lg border border-white/5">
                          {renderTextWithLatex(currentExplanation.level_1)}
                        </p>
                      </div>
                      <div>
                        <strong className="text-[11px] text-white block mb-1 uppercase tracking-wider text-slate-400">Summary (Lvl 2):</strong>
                        <p className="text-slate-400">
                          {renderTextWithLatex(currentExplanation.level_2)}
                        </p>
                      </div>
                      {currentExplanation.why_this_matters && (
                        <div className="bg-emerald-500/5 border border-emerald-500/10 rounded-lg p-3.5 space-y-2">
                          <strong className="text-[11px] text-emerald-400 block font-bold uppercase tracking-wider">
                            Why This Matters
                          </strong>
                          <div className="space-y-2 text-[11px] text-slate-400">
                            <div>
                              <span className="text-slate-300 block font-bold">Author Intent:</span>
                              {currentExplanation.why_this_matters.author_intent}
                            </div>
                            <div>
                              <span className="text-slate-300 block font-bold">Problem Solved:</span>
                              {currentExplanation.why_this_matters.problem_solved}
                            </div>
                            <div>
                              <span className="text-slate-300 block font-bold">Prerequisites:</span>
                              {currentExplanation.why_this_matters.prerequisites}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {swarmSubTab === "math" && (
                    <div className="space-y-3">
                      <strong className="text-[11px] text-white block mb-1 uppercase tracking-wider text-slate-400">Mathematical Derivation & Intuition (Lvl 4):</strong>
                      <div className="p-3 bg-[#111827] border border-white/5 rounded-lg font-serif">
                        {renderTextWithLatex(currentExplanation.level_4 || "No mathematical formulas found for this term.")}
                      </div>
                    </div>
                  )}

                  {swarmSubTab === "critique" && (
                    <div className="space-y-3">
                      <strong className="text-[11px] text-white block mb-1 uppercase tracking-wider text-slate-400">Critic Review & Limitations:</strong>
                      <div className="bg-rose-500/5 border border-rose-500/10 rounded-lg p-4 text-slate-400 text-xs leading-relaxed">
                        {currentExplanation.critic_warning || "No critic reviews compiled yet for this selection."}
                      </div>
                    </div>
                  )}

                  {swarmSubTab === "related" && (
                    <div className="space-y-3">
                      <strong className="text-[11px] text-white block mb-1 uppercase tracking-wider text-slate-400">Related Literature & References (Lvl 7):</strong>
                      <div className="text-slate-400 text-xs">
                        {renderTextWithLatex(currentExplanation.level_7 || "No citation links available.")}
                      </div>
                    </div>
                  )}

                  {swarmSubTab === "code" && (
                    <div className="space-y-3">
                      <strong className="text-[11px] text-white block mb-1 uppercase tracking-wider text-slate-400">Implementation Pseudocode (Lvl 6):</strong>
                      <pre className="bg-[#111827] border border-white/5 rounded-lg p-3.5 font-mono text-[10px] text-blue-300 overflow-x-auto whitespace-pre-wrap">
                        {currentExplanation.level_6 || "No PyTorch/pseudocode implementations mapped."}
                      </pre>
                    </div>
                  )}

                  {swarmSubTab === "notes" && (
                    <div className="flex flex-col gap-3 bg-white/5 p-4 rounded-lg border border-white/5">
                      <label className="text-[11px] font-bold text-slate-300 uppercase tracking-wider">Add Notebook Annotation</label>
                      <textarea
                        value={userNoteText}
                        onChange={(e) => setUserNoteText(e.target.value)}
                        placeholder="Type notes to save to notebook..."
                        className="w-full bg-[#111827] border border-white/10 rounded-lg p-3 text-xs text-slate-200 focus:border-blue-500 focus:outline-none h-20"
                      />
                      <button
                        onClick={saveNoteToNotebook}
                        className="flex items-center justify-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs py-2 px-4 rounded-lg transition-colors"
                      >
                        <Save className="w-3.5 h-3.5" />
                        Save Annotation
                      </button>
                      {savedNoteSuccess && (
                        <span className="text-[10px] text-emerald-400 font-bold text-center mt-1">✓ Saved to Research Notebook!</span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-20 text-slate-500 gap-2 h-full">
                <Zap className="w-8 h-8 text-blue-500 animate-bounce" />
                <p className="text-xs text-center font-medium">Highlight any phrase or formula in the reader to trigger swarm analysis.</p>
              </div>
            )}
          </div>

          {/* TAB 2: Citation Map */}
          <div className={`absolute inset-0 overflow-y-auto p-5 scrollable flex flex-col gap-3 ${activeTab === 'graph' ? 'block' : 'hidden'}`}>
            <div className="flex justify-between items-center bg-white/5 px-3 py-1.5 rounded-lg border border-white/5 flex-shrink-0">
              <span className="text-[10px] uppercase font-bold text-slate-400">Obsidian-Style Citation Network</span>
              <select
                value={graphFilter}
                onChange={(e) => setGraphFilter(e.target.value)}
                className="bg-[#111827] border border-white/10 rounded text-[10px] px-1.5 py-0.5 text-slate-200 focus:outline-none"
              >
                <option value="all">Filter: All Nodes</option>
                <option value="paper">Papers Only</option>
                <option value="concept">Concepts Only</option>
              </select>
            </div>
            <div 
              ref={cytoscapeRef} 
              className="flex-1 bg-[#111827] rounded-lg border border-white/10 min-h-[350px]"
            />
          </div>

          {/* TAB 3: Research Notebook */}
          <div className={`absolute inset-0 overflow-y-auto p-5 scrollable space-y-4 ${activeTab === 'notebook' ? 'block' : 'hidden'}`}>
            <h5 className="text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-white/5 pb-2">
              Personal Research Notebook ({notebook.length} notes)
            </h5>
            {notebook.length > 0 ? (
              <div className="space-y-3">
                {notebook.map((note) => (
                  <div key={note.id} className="bg-white/5 border border-white/10 rounded-lg p-3 space-y-2">
                    <div className="flex justify-between items-start">
                      <span className="text-[10px] bg-blue-600/30 text-blue-400 px-1.5 py-0.5 rounded font-bold uppercase">
                        {note.selection_type}
                      </span>
                      <span className="text-[9px] text-slate-500 font-mono">
                        {new Date(note.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <p className="text-xs text-white italic font-serif">"{note.selection_text}"</p>
                    {note.user_note && (
                      <div className="bg-[#111827] border-l-2 border-amber-500 p-2 text-xs text-amber-300">
                        <strong>My Note:</strong> {note.user_note}
                      </div>
                    )}
                    <details className="text-[11px] text-slate-400 cursor-pointer">
                      <summary className="hover:text-white font-medium">View AI Swarm Analysis</summary>
                      <div className="mt-2 bg-[#111827] p-2.5 rounded text-[11px] text-slate-300 space-y-1 cursor-default">
                        <div><strong>Intuition:</strong> {note.ai_explanations.level_1}</div>
                        <div className="mt-1"><strong>Warning:</strong> {note.ai_explanations.critic_warning}</div>
                      </div>
                    </details>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 text-center py-10">No notes saved to notebook yet.</p>
            )}
          </div>

          {/* TAB 4: Reading Timeline */}
          <div className={`absolute inset-0 overflow-y-auto p-5 scrollable space-y-4 ${activeTab === 'timeline' ? 'block' : 'hidden'}`}>
            <h5 className="text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-white/5 pb-2">
              Swarm Reading Timeline
            </h5>
            {timeline.length > 0 ? (
              <div className="relative border-l border-white/10 ml-2.5 pl-4 space-y-4">
                {timeline.map((item) => (
                  <div key={item.id} className="relative">
                    {/* Timeline dot */}
                    <span className="absolute -left-[21px] top-1.5 w-2 h-2 rounded-full bg-blue-500 border border-slate-900" />
                    <div className="space-y-0.5">
                      <div className="flex justify-between items-center">
                        <span className="text-[10px] font-bold text-slate-300 uppercase">
                          {item.action_type}
                        </span>
                        <span className="text-[8px] text-slate-500 font-mono">
                          {new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                      {item.details && (
                        <p className="text-xs text-slate-400 leading-snug">
                          {item.details.text ? (
                            <span>Highlighted <strong className="text-blue-400">"{item.details.text}"</strong> - {item.details.summary}</span>
                          ) : (
                            item.details.msg || "Visits section"
                          )}
                        </p>
                      )}
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
