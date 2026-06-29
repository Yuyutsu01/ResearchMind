import React, { useState, useEffect, useRef } from 'react';
import Header from './components/Header.jsx';
import UploadCenter from './components/UploadCenter.jsx';
import ResearchHistory from './components/ResearchHistory.jsx';
import RlDecisionOptimizer from './components/RlDecisionOptimizer.jsx';
import RealTimeTelemetry from './components/RealTimeTelemetry.jsx';
import ExecutiveBrief from './components/ExecutiveBrief.jsx';
import Deconstruction from './components/Deconstruction.jsx';
import OpportunityMatrix from './components/OpportunityMatrix.jsx';
import CitationTimeline from './components/CitationTimeline.jsx';
import CitationInfluenceGraph from './components/CitationInfluenceGraph.jsx';
import CitationReadingPath from './components/CitationReadingPath.jsx';

const API_BASE = "http://localhost:8000";
const WS_BASE = "ws://localhost:8000";

export default function App() {
  // Global States
  const [socketStatus, setSocketStatus] = useState('Disconnected');
  const [isTraining, setIsTraining] = useState(false);
  const [uploadedPdfPath, setUploadedPdfPath] = useState('');
  const [currentTaskId, setCurrentTaskId] = useState(null);
  const [activeTab, setActiveTab] = useState('brief');
  const [activeCitationSubTab, setActiveCitationSubTab] = useState('timeline');
  
  const [history, setHistory] = useState([]);
  const [telemetry, setTelemetry] = useState(null);
  const [traceLogs, setTraceLogs] = useState([]);
  const [rlChoices, setRlChoices] = useState(null);
  const [rlReward, setRlReward] = useState(null);
  const [rlStateKey, setRlStateKey] = useState('');
  
  // Active report data
  const [summaryData, setSummaryData] = useState(null);
  const [reportMap, setReportMap] = useState({});
  const [concepts, setConcepts] = useState([]);
  const [graphData, setGraphData] = useState(null);
  
  const [isLoading, setIsLoading] = useState(false);
  const [queryInput, setQueryInput] = useState('');
  
  const [exportLoading, setExportLoading] = useState({
    docx: false,
    pptx: false,
    latex: false
  });

  const socketRef = useRef(null);
  const traceEndRef = useRef(null);

  // Connect WebSocket with Reconnection logic
  const connectWebSocket = () => {
    setSocketStatus('Disconnected');
    const ws = new WebSocket(`${WS_BASE}/ws/chat`);
    socketRef.current = ws;

    ws.onopen = () => {
      setSocketStatus('Connected');
    };

    ws.onclose = () => {
      setSocketStatus('Disconnected');
      // Attempt reconnection in 3s
      setTimeout(connectWebSocket, 3000);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleSocketMessage(data);
    };
  };

  const handleSocketMessage = (data) => {
    if (data.type === 'status') {
      setTraceLogs(prev => [...prev, { type: 'status', message: data.message }]);
    } else if (data.type === 'rl_choices') {
      setRlStateKey(data.state_key);
      setRlChoices(data.choices);
    } else if (data.type === 'agent_step') {
      setTraceLogs(prev => [...prev, {
        type: 'step',
        agent: data.agent,
        message: data.messages[0] || "Running node...",
        metadata: data.metadata
      }]);
    } else if (data.type === 'result') {
      setRlReward(data.reward);
      setCurrentTaskId(data.task_id);
      setIsLoading(false);
      
      // Load completed details
      loadTaskReports(data.task_id);
      loadHistory();
      loadTelemetry();
    }
  };

  // API Call Loaders
  const loadHistory = async () => {
    try {
      const res = await fetch(`${API_BASE}/history`);
      const data = await res.json();
      setHistory(data.history || []);
    } catch (err) {
      console.error("Failed to load history:", err);
    }
  };

  const loadTelemetry = async () => {
    try {
      const res = await fetch(`${API_BASE}/telemetry`);
      const data = await res.json();
      setTelemetry(data.metrics || null);
    } catch (err) {
      console.error("Failed to load telemetry:", err);
    }
  };

  const loadTaskReports = async (taskId) => {
    try {
      setCurrentTaskId(taskId);
      const res = await fetch(`${API_BASE}/api/reports/${taskId}`);
      const data = await res.json();
      
      if (data.reports && data.reports.length > 0) {
        const tempReportMap = {};
        let summary = null;
        
        data.reports.forEach(r => {
          const basename = r.file_path.split(/[\\/]/).pop();
          tempReportMap[r.format.toLowerCase()] = `${API_BASE}/reports/${basename}`;
          
          if (r.format.toLowerCase() === "markdown") {
            summary = r.section_summary;
            if (typeof summary === "string") {
              try {
                summary = JSON.parse(summary);
              } catch (e) {
                console.error("Error parsing JSON section_summary:", e);
              }
            }
          }
        });
        
        if (!summary) {
          const firstRep = data.reports[0];
          summary = typeof firstRep.section_summary === "string" 
            ? JSON.parse(firstRep.section_summary) 
            : firstRep.section_summary;
        }

        setSummaryData(summary);
        setReportMap(tempReportMap);
        
        // Fetch concepts and citation graph asynchronously
        loadConcepts(taskId);
        loadCitationGraph(taskId);
      }
    } catch (err) {
      console.error("Failed to load task reports:", err);
    }
  };

  const loadConcepts = async (taskId) => {
    try {
      const res = await fetch(`${API_BASE}/api/concepts/${taskId}`);
      const data = await res.json();
      setConcepts(data.concepts || []);
    } catch (err) {
      console.error("Failed to load concepts:", err);
    }
  };

  const loadCitationGraph = async (taskId) => {
    try {
      const res = await fetch(`${API_BASE}/api/citation-graph/${taskId}`);
      const data = await res.json();
      setGraphData(data);
    } catch (err) {
      console.error("Failed to load citation graph:", err);
    }
  };

  // Actions
  const handleSelectTask = (taskId, prompt) => {
    setIsLoading(true);
    setTraceLogs([{ type: 'status', message: `Loading task reports for: "${prompt}"...` }]);
    setActiveTab('brief');
    loadTaskReports(taskId);
    setIsLoading(false);
  };

  const handleDeleteTask = async (taskId) => {
    try {
      const res = await fetch(`${API_BASE}/history/${taskId}`, { method: "DELETE" });
      const data = await res.json();
      if (data.success) {
        if (currentTaskId === taskId) {
          setCurrentTaskId(null);
          setSummaryData(null);
          setReportMap({});
          setConcepts([]);
          setGraphData(null);
          setTraceLogs([]);
        }
        loadHistory();
      } else {
        alert(`Failed to delete task: ${data.detail}`);
      }
    } catch (err) {
      console.error("Failed to delete task:", err);
      alert("Failed to delete record.");
    }
  };

  const handleTrainPolicy = async () => {
    setIsTraining(true);
    try {
      const res = await fetch(`${API_BASE}/rl/train`, { method: "POST" });
      const data = await res.json();
      alert(`Successfully completed ${data.updates_performed} policy experience updates!`);
    } catch (err) {
      alert("Policy training failed.");
    } finally {
      setIsTraining(false);
    }
  };

  const handleRunAnalysis = (e) => {
    e.preventDefault();
    if (!queryInput.trim()) return;

    setIsLoading(true);
    setTraceLogs([]);
    setRlChoices(null);
    setRlReward(null);
    setSummaryData(null);
    setGraphData(null);
    setConcepts([]);
    setActiveTab('brief');

    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({
        request: queryInput.trim(),
        pdf_path: uploadedPdfPath
      }));
      setQueryInput('');
    } else {
      setTraceLogs([{ type: 'status', message: 'Error: WebSocket connection is offline.' }]);
      setIsLoading(false);
    }
  };

  const handleExport = async (e, format) => {
    e.preventDefault();
    if (!currentTaskId) return;

    setExportLoading(prev => ({ ...prev, [format]: true }));
    try {
      const res = await fetch(`${API_BASE}/api/export/${currentTaskId}/${format}`, { method: "POST" });
      const data = await res.json();
      if (data.success) {
        window.open(`${API_BASE}${data.file_path}`, '_blank');
      } else {
        alert(`Compilation failed: ${data.detail}`);
      }
    } catch (err) {
      alert("Failed to compile export: " + err.message);
    } finally {
      setExportLoading(prev => ({ ...prev, [format]: false }));
    }
  };

  // Scroll trace logs to bottom
  useEffect(() => {
    if (traceEndRef.current) {
      traceEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [traceLogs]);

  // Init connections on mount
  useEffect(() => {
    connectWebSocket();
    loadHistory();
    loadTelemetry();

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, []);

  return (
    <div id="app">
      <Header 
        status={socketStatus} 
        onTrainPolicy={handleTrainPolicy} 
        isTraining={isTraining} 
      />

      <main className="app-main">
        {/* Left Side: File Upload & History */}
        <section className="side-panel left-panel">
          <UploadCenter 
            onUploadSuccess={(path) => setUploadedPdfPath(path)} 
            API_BASE={API_BASE} 
          />
          <ResearchHistory 
            history={history} 
            activeTaskId={currentTaskId} 
            onSelectTask={handleSelectTask} 
            onDeleteTask={handleDeleteTask} 
          />
        </section>

        {/* Middle Panel: Workspace */}
        <section className="main-workspace">
          <div className="card query-card">
            <form onSubmit={handleRunAnalysis} className="chat-input-container">
              <input 
                type="text" 
                value={queryInput}
                onChange={(e) => setQueryInput(e.target.value)}
                placeholder="Ask to analyze, compare, or generate a literature review..." 
                autoComplete="off" 
                required
              />
              <button type="submit" disabled={isLoading} className="btn btn-primary">
                <span>Run Analysis</span>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13"></line>
                  <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                </svg>
              </button>
            </form>
          </div>

          {/* Navigation Tabs */}
          <div className="workspace-tabs">
            <button className={`tab-btn ${activeTab === 'brief' ? 'active' : ''}`} onClick={() => setActiveTab('brief')}>Executive Brief</button>
            <button className={`tab-btn ${activeTab === 'deconstruction' ? 'active' : ''}`} onClick={() => setActiveTab('deconstruction')}>Deconstruction</button>
            <button className={`tab-btn ${activeTab === 'citation-graph' ? 'active' : ''}`} onClick={() => setActiveTab('citation-graph')}>Citation Graph</button>
            <button className={`tab-btn ${activeTab === 'concepts' ? 'active' : ''}`} onClick={() => setActiveTab('concepts')}>Concept Explorer</button>
            <button className={`tab-btn ${activeTab === 'opportunities' ? 'active' : ''}`} onClick={() => setActiveTab('opportunities')}>Opportunities</button>
          </div>

          {/* Tab Content 1: Executive Brief & Timeline */}
          {activeTab === 'brief' && (
            <div className="tab-content" style={{ display: 'block' }}>
              <div className="workspace-layout">
                {/* Executive summary details */}
                <div className="card result-card">
                  <div className="card-header-flex">
                    <h3>Executive Research Brief</h3>
                    {summaryData && (
                      <div className="download-actions" style={{ display: 'flex' }}>
                        {reportMap["markdown"] && (
                          <a href={reportMap["markdown"]} className="btn-download" target="_blank" rel="noreferrer">MD</a>
                        )}
                        {reportMap["pdf"] && (
                          <a href={reportMap["pdf"]} className="btn-download" target="_blank" rel="noreferrer">PDF</a>
                        )}
                        <a 
                          href="#" 
                          className="btn-download" 
                          onClick={(e) => handleExport(e, 'docx')}
                        >
                          {exportLoading.docx ? '...' : 'Word'}
                        </a>
                        <a 
                          href="#" 
                          className="btn-download" 
                          onClick={(e) => handleExport(e, 'pptx')}
                        >
                          {exportLoading.pptx ? '...' : 'Slides'}
                        </a>
                        <a 
                          href="#" 
                          className="btn-download" 
                          onClick={(e) => handleExport(e, 'latex')}
                        >
                          {exportLoading.latex ? '...' : 'LaTeX'}
                        </a>
                      </div>
                    )}
                  </div>
                  
                  <div id="brief-container" className="brief-container">
                    {isLoading && !summaryData ? (
                      <div className="processing-loader">
                        <div className="spinner"></div>
                        <p>Executing LangGraph agent nodes & retrieving citation metrics...</p>
                      </div>
                    ) : summaryData ? (
                      <ExecutiveBrief sections={summaryData} />
                    ) : (
                      <div className="empty-state">Enter a prompt or upload a paper above to run.</div>
                    )}
                  </div>
                </div>

                {/* Live execution telemetry trace */}
                <div className="card trace-card">
                  <h3>Agent Execution Timeline</h3>
                  <div id="trace-logs" className="trace-logs">
                    {traceLogs.length > 0 ? (
                      traceLogs.map((log, idx) => {
                        if (log.type === 'status') {
                          return <div key={idx} className="trace-item-desc">&gt; {log.message}</div>;
                        }
                        const cleanAgentName = log.agent.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
                        return (
                          <div key={idx} className="trace-item">
                            <div className="trace-item-header">
                              <span>{cleanAgentName}</span>
                              <span className="trace-item-status success">Done</span>
                            </div>
                            <div className="trace-item-desc">{log.message}</div>
                          </div>
                        );
                      })
                    ) : (
                      <div className="empty-state">Awaiting execution...</div>
                    )}
                    <div ref={traceEndRef} />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tab Content 2: Deconstruction */}
          {activeTab === 'deconstruction' && (
            <div className="tab-content" style={{ display: 'block' }}>
              <Deconstruction sections={summaryData} />
            </div>
          )}

          {/* Tab Content 3: Citations */}
          {activeTab === 'citation-graph' && (
            <div className="tab-content" style={{ display: 'block' }}>
              <div className="card">
                <div className="card-header-flex">
                  <h3>Citation Analysis Suite</h3>
                  <div className="sub-tabs" id="citation-sub-tabs">
                    <button 
                      className={`sub-tab-btn ${activeCitationSubTab === 'timeline' ? 'active' : ''}`} 
                      onClick={() => setActiveCitationSubTab('timeline')}
                    >
                      Timeline
                    </button>
                    <button 
                      className={`sub-tab-btn ${activeCitationSubTab === 'influence' ? 'active' : ''}`} 
                      onClick={() => setActiveCitationSubTab('influence')}
                    >
                      Influence Network
                    </button>
                    <button 
                      className={`sub-tab-btn ${activeCitationSubTab === 'reading-path' ? 'active' : ''}`} 
                      onClick={() => setActiveCitationSubTab('reading-path')}
                    >
                      Recommended Reading Path
                    </button>
                  </div>
                </div>

                {activeCitationSubTab === 'timeline' && (
                  <div className="citation-sub-content" id="cit-sub-timeline" style={{ display: 'block' }}>
                    <div id="timeline-container" className="timeline-container">
                      <CitationTimeline graphData={graphData} />
                    </div>
                  </div>
                )}

                {activeCitationSubTab === 'influence' && (
                  <div className="citation-sub-content" id="cit-sub-influence" style={{ display: 'block' }}>
                    <div id="graph-container" className="graph-container">
                      <CitationInfluenceGraph graphData={graphData} />
                    </div>
                  </div>
                )}

                {activeCitationSubTab === 'reading-path' && (
                  <div className="citation-sub-content" id="cit-sub-reading-path" style={{ display: 'block' }}>
                    <div id="reading-path-container" className="reading-path-container">
                      <CitationReadingPath sections={summaryData} />
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Tab Content 4: Concepts Grid */}
          {activeTab === 'concepts' && (
            <div className="tab-content" style={{ display: 'block' }}>
              <div className="card">
                <h3>Scientific Concept Explorer</h3>
                <p className="section-description">Grid of key technical concepts extracted from the research content.</p>
                <div id="concepts-grid" className="concepts-grid">
                  {concepts && concepts.length > 0 ? (
                    concepts.map((c, index) => (
                      <div key={index} className="concept-card">
                        <div className="concept-title">{c.term}</div>
                        <div className="concept-def">{c.definition}</div>
                        {c.math_formula && <div className="concept-math">{c.math_formula}</div>}
                        <div className="concept-apps">
                          <strong>Applications:</strong> {c.applications || 'General analysis'}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="empty-state">No key concepts extracted yet. Run an analysis task first.</div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Tab Content 5: Research Opportunities */}
          {activeTab === 'opportunities' && (
            <div className="tab-content" style={{ display: 'block' }}>
              <OpportunityMatrix sections={summaryData} />
            </div>
          )}
        </section>

        {/* Right Side: RL panel and Telemetry */}
        <section className="side-panel right-panel">
          <RlDecisionOptimizer 
            choices={rlChoices} 
            reward={rlReward} 
            stateKey={rlStateKey} 
          />
          <RealTimeTelemetry metrics={telemetry} />
        </section>
      </main>
    </div>
  );
}
