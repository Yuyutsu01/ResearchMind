import React from 'react';

// Regex helper to extract publication years
function parsePublicationYear(citationStr) {
  const match = citationStr.match(/\b(19\d\d|20\d\d)\b/);
  return match ? parseInt(match[1]) : null;
}

export default function CitationTimeline({ graphData }) {
  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return <div className="empty-state">No citation network compiled.</div>;
  }

  const datedNodes = [];
  const undatedNodes = [];

  graphData.nodes.forEach(node => {
    if (node.type === "topic") return; // Skip top-level topic roots
    
    const year = parsePublicationYear(node.id);
    if (year) {
      datedNodes.push({ ...node, year });
    } else {
      undatedNodes.push({ ...node, year: 2026 }); // Default fallback
    }
  });

  datedNodes.sort((a, b) => a.year - b.year);
  const allTimelineItems = [...datedNodes, ...undatedNodes];

  if (allTimelineItems.length === 0) {
    return <div className="empty-state">No external citation nodes located.</div>;
  }

  return (
    <div className="vertical-timeline">
      {allTimelineItems.map((item, idx) => {
        const displayYear = item.year === 2026 ? "Undated Ref" : item.year;
        return (
          <div key={idx} className={`timeline-node-item ${item.type}`}>
            <div className="timeline-marker"></div>
            <div className="timeline-node-content">
              <span className="timeline-date">{displayYear}</span>
              <h4 class="timeline-title">{item.label}</h4>
              <p className="timeline-meta">
                Type: <strong>{item.type.toUpperCase()}</strong> | Connectivity: {item.centrality}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
