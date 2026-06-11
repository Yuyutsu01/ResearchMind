import './style.css';

const API_BASE = "http://localhost:8000";
const WS_BASE = "ws://localhost:8000";

// State
let socket = null;
let uploadedPdfPath = "";
let currentTaskId = null;
let lastSummaryData = null; // Caches the active paper sections data

// DOM Elements
const statusText = document.getElementById('status-text');
const statusDot = document.querySelector('.dot');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatHistory = document.getElementById('chat-history');
const traceLogs = document.getElementById('trace-logs');
const fileInput = document.getElementById('file-input');
const uploadZone = document.getElementById('upload-zone');
const selectedFileLabel = document.getElementById('selected-file-label');
const historyList = document.getElementById('history-list');
const trainPolicyBtn = document.getElementById('train-policy-btn');

// RL Panel Elements
const rlSource = document.getElementById('rl-source');
const rlStrategy = document.getElementById('rl-strategy');
const rlDepth = document.getElementById('rl-depth');
const rlReward = document.getElementById('rl-reward');
const rlStateKey = document.getElementById('rl-state-key');

// Telemetry Elements
const telPlanVal = document.getElementById('tel-plan-val');
const telPlanProgress = document.getElementById('tel-plan-progress');
const telValidVal = document.getElementById('tel-valid-val');
const telValidProgress = document.getElementById('tel-valid-progress');
const telExecVal = document.getElementById('tel-exec-val');
const telExecProgress = document.getElementById('tel-exec-progress');

// Download Triggers
const downloadActions = document.getElementById('download-actions');
const downloadMd = document.getElementById('download-md');
const downloadPdf = document.getElementById('download-pdf');
const downloadDocx = document.getElementById('download-docx');
const downloadPptx = document.getElementById('download-pptx');
const downloadLatex = document.getElementById('download-latex');

// Connect WebSocket on Load
function connectWebSocket() {
  socket = new WebSocket(`${WS_BASE}/ws/chat`);

  socket.onopen = () => {
    statusText.textContent = 'Connected';
    statusDot.classList.add('connected');
  };

  socket.onclose = () => {
    statusText.textContent = 'Disconnected';
    statusDot.classList.remove('connected');
    setTimeout(connectWebSocket, 3000);
  };

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleSocketMessage(data);
  };
}

function handleSocketMessage(data) {
  if (data.type === 'status') {
    updateTraceStatus(data.message);
  } else if (data.type === 'rl_choices') {
    rlStateKey.textContent = `Active State: ${data.state_key}`;
    rlSource.textContent = ["ArXiv", "Scholar", "Web Search"][data.choices.source_selection] || "ArXiv";
    rlStrategy.textContent = ["Semantic", "BM25", "Hybrid"][data.choices.retrieval_strategy] || "Hybrid";
    rlDepth.textContent = ["None", "Shallow", "Deep"][data.choices.expansion_depth] || "Shallow";
  } else if (data.type === 'agent_step') {
    appendTraceItem(data.agent, data.messages[0] || "Running node...", data.metadata);
  } else if (data.type === 'result') {
    rlReward.textContent = data.reward >= 0 ? `+${data.reward.toFixed(2)}` : data.reward.toFixed(2);
    currentTaskId = data.task_id;
    
    // Load compiled task dashboard views
    loadTaskReports(data.task_id);
    loadHistory();
    loadTelemetry();
  }
}

// File Upload Handler
uploadZone.addEventListener('click', () => fileInput.click());
uploadZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  uploadZone.style.borderColor = "#3B82F6";
});
uploadZone.addEventListener('dragleave', () => {
  uploadZone.style.borderColor = "rgba(255, 255, 255, 0.08)";
});
uploadZone.addEventListener('drop', (e) => {
  e.preventDefault();
  uploadZone.style.borderColor = "rgba(255, 255, 255, 0.08)";
  if (e.dataTransfer.files.length > 0) {
    handleFileUpload(e.dataTransfer.files[0]);
  }
});
fileInput.addEventListener('change', () => {
  if (fileInput.files.length > 0) {
    handleFileUpload(fileInput.files[0]);
  }
});

async function handleFileUpload(file) {
  selectedFileLabel.textContent = `Uploading: ${file.name}...`;
  const formData = new FormData();
  formData.append("file", file);
  
  try {
    const res = await fetch(`${API_BASE}/upload`, {
      method: "POST",
      body: formData
    });
    const result = await res.json();
    if (result.success) {
      uploadedPdfPath = result.file_path;
      selectedFileLabel.textContent = `✓ Uploaded: ${file.name}`;
      selectedFileLabel.style.color = "#10B981";
    } else {
      selectedFileLabel.textContent = "Upload failed.";
      selectedFileLabel.style.color = "#EF4444";
    }
  } catch (err) {
    selectedFileLabel.textContent = "Upload error.";
    selectedFileLabel.style.color = "#EF4444";
  }
}

// Form Submit Handler
chatForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const query = chatInput.value.trim();
  if (!query) return;

  chatHistory.innerHTML = `
    <div class="processing-loader">
      <div class="spinner"></div>
      <p>Initiating scientific deconstruction and analysis for: <em>"${query}"</em></p>
    </div>
  `;
  traceLogs.innerHTML = "";
  downloadActions.style.display = "none";
  chatInput.value = "";
  
  // Set active tab to Brief on execution trigger
  switchTab("brief");

  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({
      request: query,
      pdf_path: uploadedPdfPath
    }));
  } else {
    chatHistory.innerHTML = "<p style='color:#EF4444;'>Error: WebSocket server is offline.</p>";
  }
});

function updateTraceStatus(msg) {
  const el = document.createElement('div');
  el.className = 'trace-item-desc';
  el.textContent = `> ${msg}`;
  traceLogs.appendChild(el);
  traceLogs.scrollTop = traceLogs.scrollHeight;
}

function appendTraceItem(agent, message, metadata) {
  const cleanAgentName = agent.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
  
  const el = document.createElement('div');
  el.className = 'trace-item';
  el.innerHTML = `
    <div class="trace-item-header">
      <span>${cleanAgentName}</span>
      <span class="trace-item-status success">Done</span>
    </div>
    <div class="trace-item-desc">${message}</div>
  `;
  traceLogs.appendChild(el);
  traceLogs.scrollTop = traceLogs.scrollHeight;
}

// Global Tab Navigation Routing
const tabButtons = document.querySelectorAll('.workspace-tabs .tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

tabButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    const tabId = btn.getAttribute('data-tab');
    switchTab(tabId);
  });
});

function switchTab(tabId) {
  tabButtons.forEach(b => {
    if (b.getAttribute('data-tab') === tabId) {
      b.classList.add('active');
    } else {
      b.classList.remove('active');
    }
  });

  tabContents.forEach(c => {
    if (c.id === `tab-${tabId}`) {
      c.style.display = 'block';
    } else {
      c.style.display = 'none';
    }
  });
}

// Helper to escape HTML characters
function escapeHtml(str) {
  if (!str) return '';
  return str.toString()
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// Main report visualizers loader
async function loadTaskReports(taskId) {
  try {
    currentTaskId = taskId;
    const res = await fetch(`${API_BASE}/api/reports/${taskId}`);
    const data = await res.json();
    
    if (data.reports && data.reports.length > 0) {
      const reportMap = {};
      let summaryData = null;
      
      data.reports.forEach(r => {
        const basename = r.file_path.split(/[\\/]/).pop();
        reportMap[r.format.toLowerCase()] = `${API_BASE}/reports/${basename}`;
        
        if (r.format.toLowerCase() === "markdown") {
          summaryData = r.section_summary;
          if (typeof summaryData === "string") {
            try {
              summaryData = JSON.parse(summaryData);
            } catch (e) {
              console.error("JSON parsing error for section_summary:", e);
            }
          }
        }
      });
      
      if (!summaryData) {
        // Fallback if no markdown key is found
        const firstRep = data.reports[0];
        summaryData = typeof firstRep.section_summary === "string" ? JSON.parse(firstRep.section_summary) : firstRep.section_summary;
      }
      
      lastSummaryData = summaryData; // Cache sections dictionary
      
      // Bind static download urls
      downloadMd.href = reportMap["markdown"] || "#";
      downloadPdf.href = reportMap["pdf"] || "#";
      
      // Bind dynamic export endpoint calls for docx, pptx, latex
      setupExportLink(taskId, "docx", downloadDocx);
      setupExportLink(taskId, "pptx", downloadPptx);
      setupExportLink(taskId, "latex", downloadLatex);
      
      downloadActions.style.display = "flex";
      
      // Render components across all remaining 5 tabs
      renderExecutiveBrief(summaryData);
      renderDeconstruction(summaryData);
      renderCitationSuite(taskId, summaryData);
      loadConcepts(taskId);
      renderOpportunities(summaryData);
      
    } else {
      chatHistory.innerHTML = `
        <div class="empty-state">
          <h3>No Reports Found</h3>
          <p>No reports found in SQLite registry for this research task.</p>
        </div>
      `;
      downloadActions.style.display = "none";
    }
  } catch (err) {
    console.error("Failed to load reports:", err);
    chatHistory.innerHTML = "<p style='color:#EF4444; padding: 1.5rem;'>Failed to retrieve reports from backend.</p>";
  }
}

function setupExportLink(taskId, format, linkEl) {
  linkEl.href = "#";
  const newLinkEl = linkEl.cloneNode(true);
  linkEl.parentNode.replaceChild(newLinkEl, linkEl);
  
  newLinkEl.addEventListener('click', async (e) => {
    e.preventDefault();
    const originalText = newLinkEl.textContent;
    newLinkEl.textContent = "...";
    try {
      const res = await fetch(`${API_BASE}/api/export/${taskId}/${format}`, { method: "POST" });
      const data = await res.json();
      if (data.success) {
        window.open(`${API_BASE}${data.file_path}`, '_blank');
      } else {
        alert(`Compilation failed: ${data.detail}`);
      }
    } catch (err) {
      alert("Failed to export: " + err.message);
    } finally {
      newLinkEl.textContent = originalText;
    }
  });
}

// -------------------------------------------------------------
// TAB 1: EXECUTIVE BRIEF RENDERER
// -------------------------------------------------------------
function renderExecutiveBrief(sections) {
  const briefContainer = document.getElementById('brief-container');
  if (!sections) {
    briefContainer.innerHTML = "<div class='empty-state'>No brief parameters.</div>";
    return;
  }
  
  const brief = sections.executive_brief || {};
  const contributions = sections.key_contributions || [];
  const matters = sections.why_it_matters || {};
  const roadmap = sections.reading_roadmap || {};
  
  // Format metadata pill display values
  const domain = brief.research_domain || "Scientific Research";
  const readingTime = brief.reading_time || "12 mins";
  const diffScore = brief.difficulty_score || "5";
  
  let contributionsHtml = "";
  if (contributions.length > 0) {
    contributions.forEach(c => {
      contributionsHtml += `
        <div class="brief-cont-item">
          <h5>${escapeHtml(c.title)}</h5>
          <p>${escapeHtml(c.description)}</p>
          <div class="brief-cont-importance"><strong>Importance:</strong> ${escapeHtml(c.importance)}</div>
        </div>
      `;
    });
  } else {
    contributionsHtml = "<p class='no-items'>No explicit contributions analyzed.</p>";
  }
  
  let roadmapBeforeHtml = "";
  const beforeRoadmap = roadmap.before_reading || [];
  beforeRoadmap.forEach(item => {
    roadmapBeforeHtml += `<span class="roadmap-pill prerequisite">${escapeHtml(item)}</span>`;
  });
  
  let roadmapAfterHtml = "";
  const afterRoadmap = roadmap.after_reading || [];
  afterRoadmap.forEach(item => {
    roadmapAfterHtml += `<span class="roadmap-pill successor">${escapeHtml(item)}</span>`;
  });
  
  const html = `
    <div class="brief-grid">
      <!-- Card 1: Executive Summary -->
      <div class="brief-card">
        <div class="brief-card-header">
          <h4>Executive Summary</h4>
          <div class="metadata-row">
            <span class="meta-pill domain-pill">${escapeHtml(domain)}</span>
            <span class="meta-pill time-pill">${escapeHtml(readingTime)}</span>
            <span class="meta-pill difficulty-pill">Diff: ${escapeHtml(diffScore)}/10</span>
          </div>
        </div>
        <div class="brief-card-body">
          <div class="brief-section">
            <h5>Problem Statement</h5>
            <p>${escapeHtml(brief.problem_statement || "Not detailed.")}</p>
          </div>
          <div class="brief-section">
            <h5>Proposed Solution</h5>
            <p>${escapeHtml(brief.proposed_solution || "Not detailed.")}</p>
          </div>
          <div class="brief-section">
            <h5>Key Innovation</h5>
            <p>${escapeHtml(brief.key_innovation || "Not detailed.")}</p>
          </div>
          <div class="brief-section">
            <h5>Main Findings & Empirical Results</h5>
            <p>${escapeHtml(brief.main_results || "Not detailed.")}</p>
          </div>
        </div>
      </div>
      
      <!-- Card 2: Key Contributions -->
      <div class="brief-card">
        <div class="brief-card-header">
          <h4>Key Contributions</h4>
        </div>
        <div class="brief-card-body scrollable-card-body">
          ${contributionsHtml}
        </div>
      </div>

      <!-- Card 3: Why Paper Matters -->
      <div class="brief-card">
        <div class="brief-card-header">
          <h4>Why This Paper Matters</h4>
        </div>
        <div class="brief-card-body scrollable-card-body">
          <div class="brief-section">
            <h5>Historical Lineage</h5>
            <p>${escapeHtml(matters.historical_importance || "N/A")}</p>
          </div>
          <div class="brief-section">
            <h5>Academic Influence</h5>
            <p>${escapeHtml(matters.academic_impact || "N/A")}</p>
          </div>
          <div class="brief-section">
            <h5>Industry Application</h5>
            <p>${escapeHtml(matters.industry_impact || "N/A")}</p>
          </div>
          <div class="brief-section">
            <h5>Influenced Systems & Models</h5>
            <p>${escapeHtml(Array.isArray(matters.papers_influenced) ? matters.papers_influenced.join(", ") : matters.papers_influenced || "N/A")}</p>
          </div>
        </div>
      </div>

      <!-- Card 4: Reading Roadmap -->
      <div class="brief-card">
        <div class="brief-card-header">
          <h4>Reading Roadmap</h4>
        </div>
        <div class="brief-card-body">
          <div class="brief-section">
            <h5>Prerequisites (Read Before)</h5>
            <div class="pills-flex">${roadmapBeforeHtml || "<span class='no-items'>None specified</span>"}</div>
          </div>
          <div class="brief-section">
            <h5>Follow-up Recommendations (Read After)</h5>
            <div class="pills-flex">${roadmapAfterHtml || "<span class='no-items'>None specified</span>"}</div>
          </div>
          <div class="brief-section">
            <h5>Learning Path Strategy</h5>
            <p>${escapeHtml(roadmap.learning_path || "N/A")}</p>
          </div>
        </div>
      </div>
    </div>
  `;
  briefContainer.innerHTML = html;
}

// -------------------------------------------------------------
// TAB 2: PAPER DECONSTRUCTION ACCORDIONS
// -------------------------------------------------------------
function renderDeconstruction(sections) {
  const container = document.getElementById('deconstruction-accordion');
  if (!sections || !sections.paper_deconstruction) {
    container.innerHTML = "<div class='empty-state'>No deconstruction metrics.</div>";
    return;
  }
  
  const deconstruction = sections.paper_deconstruction;
  container.innerHTML = "";
  
  const sectionsList = [
    { key: "problem", title: "Core Scientific Problem" },
    { key: "motivation", title: "Research Motivation" },
    { key: "methodology", title: "Methodology & Architecture Details" },
    { key: "experiments", title: "Experimental Settings & Benchmark Data" },
    { key: "results", title: "Empirical Outcomes & Achievements" },
    { key: "limitations", title: "Methodological Constraints & Limitations" },
    { key: "future_work", title: "Proposed Future Extensions" }
  ];
  
  sectionsList.forEach(item => {
    const content = deconstruction[item.key] || "No detail compiled.";
    
    const accItem = document.createElement('div');
    accItem.className = "accordion-item";
    
    accItem.innerHTML = `
      <button class="accordion-trigger">
        <span>${escapeHtml(item.title)}</span>
        <span class="chevron-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
        </span>
      </button>
      <div class="accordion-panel" style="display: none;">
        <div class="accordion-content">
          <p>${escapeHtml(content)}</p>
        </div>
      </div>
    `;
    
    // Toggle accordion state
    const trigger = accItem.querySelector('.accordion-trigger');
    const panel = accItem.querySelector('.accordion-panel');
    trigger.addEventListener('click', () => {
      const isVisible = panel.style.display === 'block';
      panel.style.display = isVisible ? 'none' : 'block';
      accItem.classList.toggle('open', !isVisible);
    });
    
    container.appendChild(accItem);
  });
}

// -------------------------------------------------------------
// TAB 3: CITATION GRAPH SUITE
// -------------------------------------------------------------
// Setup sub-tabs mapping
const citSubTabButtons = document.querySelectorAll('#citation-sub-tabs .sub-tab-btn');
const citSubTabContents = document.querySelectorAll('.citation-sub-content');

citSubTabButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    const subTabId = btn.getAttribute('data-sub-tab');
    
    citSubTabButtons.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    
    citSubTabContents.forEach(c => {
      if (c.id === `cit-sub-${subTabId}`) {
        c.style.display = 'block';
      } else {
        c.style.display = 'none';
      }
    });
  });
});

// Main Citation suite entry
async function renderCitationSuite(taskId, summaryData) {
  try {
    const res = await fetch(`${API_BASE}/api/citation-graph/${taskId}`);
    const data = await res.json();
    
    renderCitationTimeline(data);
    renderCitationInfluenceGraph(data);
    renderCitationReadingPath(data, summaryData);
  } catch (err) {
    console.error("Citation suite loading failed:", err);
  }
}

// Regex to extract 4 digit publication years (e.g. 1998, 2017) from strings
function parsePublicationYear(citationStr) {
  const match = citationStr.match(/\b(19\d\d|20\d\d)\b/);
  return match ? parseInt(match[1]) : null;
}

// View 1: Chronological Research Timeline
function renderCitationTimeline(graphData) {
  const container = document.getElementById('timeline-container');
  container.innerHTML = "";
  
  if (!graphData.nodes || graphData.nodes.length === 0) {
    container.innerHTML = "<div class='empty-state'>No citation network compiled.</div>";
    return;
  }
  
  // Categorize nodes with estimated publication years
  const datedNodes = [];
  const undatedNodes = [];
  
  graphData.nodes.forEach(node => {
    // If topic root or uploaded node, we mark as present/focus
    if (node.type === "topic") return; // Skip abstract topic node
    
    const year = parsePublicationYear(node.id);
    if (year) {
      datedNodes.push({ ...node, year });
    } else {
      undatedNodes.push({ ...node, year: 2026 }); // default mock year for undated references
    }
  });
  
  // Sort chronologically
  datedNodes.sort((a, b) => a.year - b.year);
  
  const allTimelineItems = [...datedNodes, ...undatedNodes];
  
  if (allTimelineItems.length === 0) {
    container.innerHTML = "<div class='empty-state'>No external citation nodes located.</div>";
    return;
  }
  
  const timelineList = document.createElement('div');
  timelineList.className = "vertical-timeline";
  
  allTimelineItems.forEach(item => {
    const itemEl = document.createElement('div');
    itemEl.className = `timeline-node-item ${item.type}`;
    
    const displayYear = item.year === 2026 ? "Undated Ref" : item.year;
    
    itemEl.innerHTML = `
      <div class="timeline-marker"></div>
      <div class="timeline-node-content">
        <span class="timeline-date">${escapeHtml(displayYear)}</span>
        <h4 class="timeline-title">${escapeHtml(item.label)}</h4>
        <p class="timeline-meta">Type: <strong>${escapeHtml(item.type.toUpperCase())}</strong> | Connectivity score: ${escapeHtml(item.centrality)}</p>
      </div>
    `;
    timelineList.appendChild(itemEl);
  });
  
  container.appendChild(timelineList);
}

// JS PageRank calculation algorithm
function calculatePageRank(nodes, links) {
  const N = nodes.length;
  if (N === 0) return;
  
  // Initialize PageRank weights
  nodes.forEach(d => d.pagerank = 1.0 / N);
  
  const damping = 0.85;
  const iterations = 20;
  
  for (let iter = 0; iter < iterations; iter++) {
    const nextPR = {};
    nodes.forEach(d => nextPR[d.id] = (1.0 - damping) / N);
    
    const outDegrees = {};
    nodes.forEach(d => outDegrees[d.id] = 0);
    
    links.forEach(l => {
      const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
      outDegrees[sourceId] = (outDegrees[sourceId] || 0) + 1;
    });
    
    links.forEach(l => {
      const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
      const targetId = typeof l.target === 'object' ? l.target.id : l.target;
      
      const prContribution = nodes.find(d => d.id === sourceId).pagerank / (outDegrees[sourceId] || 1);
      nextPR[targetId] = (nextPR[targetId] || 0) + damping * prContribution;
    });
    
    // Dangling nodes accumulation (nodes with no out links)
    let danglingSum = 0;
    nodes.forEach(d => {
      if (!outDegrees[d.id]) {
        danglingSum += d.pagerank;
      }
    });
    
    nodes.forEach(d => {
      nextPR[d.id] += damping * (danglingSum / N);
    });
    
    nodes.forEach(d => d.pagerank = nextPR[d.id]);
  }
}

// View 2: Interactive D3.js PageRank Sized Influence Network
let citationSimulation = null;
function renderCitationInfluenceGraph(graphData) {
  const container = document.getElementById('graph-container');
  const svg = d3.select("#citation-svg");
  const emptyState = document.getElementById("graph-empty-state");
  
  if (!graphData.nodes || graphData.nodes.length === 0) {
    emptyState.style.display = "block";
    svg.style("display", "none");
    return;
  }
  
  emptyState.style.display = "none";
  svg.style("display", "block").html(""); // Clean SVG canvas
  
  const width = container.clientWidth || 600;
  const height = 500;
  
  // Calculate PageRank for network influence node sizing
  calculatePageRank(graphData.nodes, graphData.links);
  
  const colorScale = d3.scaleOrdinal()
    .domain(["topic", "uploaded", "reference"])
    .range(["#EF4444", "#3B82F6", "#10B981"]);
    
  if (citationSimulation) citationSimulation.stop();
  
  citationSimulation = d3.forceSimulation(graphData.nodes)
    .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(150))
    .force("charge", d3.forceManyBody().strength(-300))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collision", d3.forceCollide().radius(d => {
      // Calculate dynamic radius based on PageRank score
      const baseRadius = d.type === "topic" ? 16 : d.type === "uploaded" ? 12 : 8;
      const prMultiplier = d.pagerank ? d.pagerank * 50 : 2;
      return Math.max(8, baseRadius + prMultiplier);
    }));
    
  // Drawing link lines
  const link = svg.append("g")
    .selectAll("line")
    .data(graphData.links)
    .enter().append("line")
    .attr("class", "link");
    
  // Creating a simple HTML tooltip overlay inside graph-container if not exists
  let tooltip = d3.select("#graph-tooltip");
  if (tooltip.empty()) {
    tooltip = d3.select("#graph-container")
      .append("div")
      .attr("id", "graph-tooltip")
      .attr("class", "graph-tooltip")
      .style("position", "absolute")
      .style("background", "rgba(11, 15, 25, 0.95)")
      .style("border", "1px solid rgba(59, 130, 246, 0.3)")
      .style("padding", "0.6rem")
      .style("border-radius", "6px")
      .style("pointer-events", "none")
      .style("display", "none")
      .style("font-size", "0.75rem")
      .style("color", "#F3F4F6")
      .style("z-index", "100");
  }

  // Draw node circles
  const node = svg.append("g")
    .selectAll("circle")
    .data(graphData.nodes)
    .enter().append("circle")
    .attr("class", "node")
    .attr("r", d => {
      const baseRadius = d.type === "topic" ? 14 : d.type === "uploaded" ? 11 : 7;
      const prMultiplier = d.pagerank ? d.pagerank * 60 : 2;
      return Math.max(7, baseRadius + prMultiplier);
    })
    .attr("fill", d => colorScale(d.type))
    .on("mouseover", (event, d) => {
      const prPercent = d.pagerank ? (d.pagerank * 100).toFixed(1) : "N/A";
      tooltip.html(`
        <strong>${escapeHtml(d.id)}</strong><br/>
        Type: ${escapeHtml(d.type.toUpperCase())}<br/>
        PageRank Network Influence: ${escapeHtml(prPercent)}%
      `)
      .style("display", "block");
    })
    .on("mousemove", (event) => {
      const containerRect = container.getBoundingClientRect();
      tooltip
        .style("left", (event.clientX - containerRect.left + 15) + "px")
        .style("top", (event.clientY - containerRect.top + 15) + "px");
    })
    .on("mouseout", () => {
      tooltip.style("display", "none");
    })
    .call(d3.drag()
      .on("start", dragstarted)
      .on("drag", dragged)
      .on("end", dragended));
      
  // Labels
  const label = svg.append("g")
    .selectAll("text")
    .data(graphData.nodes)
    .enter().append("text")
    .attr("class", "node-text")
    .attr("dy", d => {
      const baseRadius = d.type === "topic" ? 14 : d.type === "uploaded" ? 11 : 7;
      const prMultiplier = d.pagerank ? d.pagerank * 60 : 2;
      const radius = Math.max(7, baseRadius + prMultiplier);
      return -(radius + 4);
    })
    .text(d => d.label);
    
  citationSimulation.on("tick", () => {
    link
      .attr("x1", d => d.source.x)
      .attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x)
      .attr("y2", d => d.target.y);
      
    node
      .attr("cx", d => d.x = Math.max(20, Math.min(width - 20, d.x)))
      .attr("cy", d => d.y = Math.max(20, Math.min(height - 20, d.y)));
      
    label
      .attr("x", d => d.x)
      .attr("y", d => d.y);
  });
  
  function dragstarted(event, d) {
    if (!event.active) citationSimulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }
  
  function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
  }
  
  function dragended(event, d) {
    if (!event.active) citationSimulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  }
}

// View 3: Recommended Reading Path Table
function renderCitationReadingPath(graphData, sections) {
  const container = document.getElementById('reading-path-container');
  container.innerHTML = "";
  
  if (!sections) {
    container.innerHTML = "<div class='empty-state'>No analysis sections found.</div>";
    return;
  }
  
  const roadmap = sections.reading_roadmap || {};
  const beforeRoadmap = roadmap.before_reading || [];
  const afterRoadmap = roadmap.after_reading || [];
  
  let rowsHtml = "";
  let stepNum = 1;
  
  // Prerequisites
  beforeRoadmap.forEach(item => {
    rowsHtml += `
      <tr>
        <td>Step ${stepNum++}</td>
        <td><span class="badge prerequisite-badge">Prerequisite</span></td>
        <td><strong>${escapeHtml(item)}</strong></td>
        <td>Gain fundamental foundations before reviewing the core methodology.</td>
      </tr>
    `;
  });
  
  // Current Paper Node
  const brief = sections.executive_brief || {};
  const currentTitle = brief.proposed_solution || "Active Research Subject";
  rowsHtml += `
    <tr class="active-reading-row">
      <td>Step ${stepNum++}</td>
      <td><span class="badge active-badge">Core Subject</span></td>
      <td><strong>${escapeHtml(currentTitle)}</strong></td>
      <td>Primary focus of the active research brief.</td>
    </tr>
  `;
  
  // Recommended Post-readings
  afterRoadmap.forEach(item => {
    rowsHtml += `
      <tr>
        <td>Step ${stepNum++}</td>
        <td><span class="badge successor-badge">Follow-up</span></td>
        <td><strong>${escapeHtml(item)}</strong></td>
        <td>Apply methods to extensions, related domains, or specialized problems.</td>
      </tr>
    `;
  });
  
  if (beforeRoadmap.length === 0 && afterRoadmap.length === 0) {
    container.innerHTML = "<div class='empty-state'>No recommended reading pathway extracted.</div>";
    return;
  }
  
  container.innerHTML = `
    <table class="reading-path-table">
      <thead>
        <tr>
          <th>Sequence</th>
          <th>Role</th>
          <th>Topic / Paper Reference</th>
          <th>Instructional Guideline</th>
        </tr>
      </thead>
      <tbody>
        ${rowsHtml}
      </tbody>
    </table>
  `;
}

// -------------------------------------------------------------
// TAB 4: CONCEPT EXPLORER GRID (Static View)
// -------------------------------------------------------------
async function loadConcepts(taskId) {
  const grid = document.getElementById('concepts-grid');
  grid.innerHTML = "<p class='no-items'>Retrieving scientific terminology...</p>";
  
  try {
    const res = await fetch(`${API_BASE}/api/concepts/${taskId}`);
    const data = await res.json();
    grid.innerHTML = "";
    
    if (data.concepts && data.concepts.length > 0) {
      data.concepts.forEach(c => {
        const card = document.createElement('div');
        card.className = "concept-card"; // Static concept card styling
        card.innerHTML = `
          <div class="concept-title">${escapeHtml(c.term)}</div>
          <div class="concept-def">${escapeHtml(c.definition)}</div>
          ${c.math_formula ? `<div class="concept-math">${escapeHtml(c.math_formula)}</div>` : ''}
          <div class="concept-apps"><strong>Applications:</strong> ${escapeHtml(c.applications || 'General analysis')}</div>
        `;
        grid.appendChild(card);
      });
    } else {
      grid.innerHTML = "<div class='empty-state'>No key concepts extracted for this paper.</div>";
    }
  } catch (err) {
    grid.innerHTML = "<p style='color:#EF4444; padding: 1rem;'>Failed to retrieve concepts.</p>";
  }
}

// -------------------------------------------------------------
// TAB 5: RESEARCH OPPORTUNITIES
// -------------------------------------------------------------
function renderOpportunities(sections) {
  const container = document.getElementById('opportunities-container');
  container.innerHTML = "";
  
  const opportunities = sections.opportunities || [];
  
  if (opportunities.length === 0) {
    container.innerHTML = "<div class='empty-state'>No opportunities analyzed.</div>";
    return;
  }
  
  opportunities.forEach(opp => {
    const card = document.createElement('div');
    
    // Determine color code based on impact score
    const impactVal = parseInt(opp.impact) || 5;
    let impactClass = "impact-low";
    if (impactVal >= 8) {
      impactClass = "impact-high";
    } else if (impactVal >= 5) {
      impactClass = "impact-medium";
    }
    
    card.className = `opportunity-matrix-card ${impactClass}`;
    
    card.innerHTML = `
      <div class="opp-card-header">
        <h4>${escapeHtml(opp.title)}</h4>
        <span class="badge opp-impact-badge">Impact: ${escapeHtml(opp.impact)}/10</span>
      </div>
      <p class="opp-description">${escapeHtml(opp.description)}</p>
      
      <div class="opp-meta-grid">
        <div class="opp-meta-box">
          <span class="opp-meta-label">Novelty</span>
          <span class="opp-meta-val">${escapeHtml(opp.novelty)}/10</span>
        </div>
        <div class="opp-meta-box">
          <span class="opp-meta-label">Difficulty</span>
          <span class="opp-meta-val">${escapeHtml(opp.difficulty)}/10</span>
        </div>
        <div class="opp-meta-box">
          <span class="opp-meta-label">Timeline</span>
          <span class="opp-meta-val">${escapeHtml(opp.time)}</span>
        </div>
        <div class="opp-meta-box">
          <span class="opp-meta-label">Funding</span>
          <span class="opp-meta-val">${escapeHtml(opp.funding || 'High')}</span>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

// -------------------------------------------------------------
// SIDEBAR HISTORY & TELEMETRY LOADERS
// -------------------------------------------------------------
async function loadHistory() {
  try {
    const res = await fetch(`${API_BASE}/history`);
    const data = await res.json();
    historyList.innerHTML = "";
    if (data.history && data.history.length > 0) {
      data.history.forEach(item => {
        const div = document.createElement('div');
        div.className = "history-item";
        div.onclick = () => {
          chatHistory.innerHTML = `<p>Loading summary for task: ${item.prompt}...</p>`;
          loadTaskReports(item.id);
        };
        div.innerHTML = `
          <div class="history-item-main">
            <div class="history-item-title">${item.prompt}</div>
            <div class="history-item-meta">
              <span>#${item.id}</span>
              <span style="color:${item.status === 'completed' ? '#10B981' : '#F59E0B'}">${item.status}</span>
            </div>
          </div>
          <button class="delete-history-btn" title="Delete record">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
          </button>
        `;
        const deleteBtn = div.querySelector('.delete-history-btn');
        deleteBtn.onclick = async (e) => {
          e.stopPropagation();
          if (confirm(`Are you sure you want to delete research history for task #${item.id}?`)) {
            try {
              const delRes = await fetch(`${API_BASE}/history/${item.id}`, { method: "DELETE" });
              const delData = await delRes.json();
              if (delData.success) {
                if (currentTaskId === item.id) {
                  chatHistory.innerHTML = "<div class='empty-state'>Enter a prompt or upload a paper above to run.</div>";
                  downloadActions.style.display = "none";
                }
                loadHistory();
              } else {
                alert(`Error deleting record: ${delData.detail || 'unknown error'}`);
              }
            } catch (err) {
              console.error("Delete task error:", err);
              alert("Failed to delete record.");
            }
          }
        };
        historyList.appendChild(div);
      });
    } else {
      historyList.innerHTML = "<div class='empty-state'>No previous runs.</div>";
    }
  } catch (err) {
    console.error("History load error:", err);
  }
}

async function loadTelemetry() {
  try {
    const res = await fetch(`${API_BASE}/telemetry`);
    const data = await res.json();
    const metrics = data.metrics;
    
    if (metrics) {
      if (metrics["Planning Latency"]) {
        const val = metrics["Planning Latency"].avg_duration_ms;
        telPlanVal.textContent = `${val.toFixed(1)}ms`;
        telPlanProgress.style.width = `${Math.min(100, (val / 10) * 100)}%`; // Normalize scaling
      }
      
      if (metrics["Execution Latency"]) {
        const val = metrics["Execution Latency"].avg_duration_ms;
        telExecVal.textContent = `${val.toFixed(1)}ms`;
        telExecProgress.style.width = `${Math.min(100, (val / 10) * 100)}%`;
      }
      
      if (metrics["Validation Rate"]) {
        const val = metrics["Validation Rate"].success_rate;
        telValidVal.textContent = `${val.toFixed(0)}%`;
        telValidProgress.style.width = `${val}%`;
      }
    }
  } catch (err) {
    console.error("Telemetry load error:", err);
  }
}

// Trigger Manual RL Policy Training
trainPolicyBtn.addEventListener('click', async () => {
  trainPolicyBtn.disabled = true;
  trainPolicyBtn.textContent = "Training...";
  try {
    const res = await fetch(`${API_BASE}/rl/train`, { method: "POST" });
    const data = await res.json();
    alert(`Successfully completed ${data.updates_performed} policy experience updates!`);
  } catch (err) {
    alert("Training failed.");
  } finally {
    trainPolicyBtn.disabled = false;
    trainPolicyBtn.textContent = "Train Policy";
  }
});

// Init
connectWebSocket();
loadHistory();
loadTelemetry();
