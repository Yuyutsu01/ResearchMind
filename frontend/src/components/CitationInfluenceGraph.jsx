import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

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

export default function CitationInfluenceGraph({ graphData }) {
  const containerRef = useRef(null);
  const svgRef = useRef(null);
  const [tooltipData, setTooltipData] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
      return;
    }

    const container = containerRef.current;
    const svgEl = svgRef.current;
    const width = container.clientWidth || 600;
    const height = 500;

    // Deep copy nodes and links to prevent D3 from mutating original props directly
    const nodes = graphData.nodes.map(n => ({ ...n }));
    const links = graphData.links.map(l => ({ ...l }));

    // Run PageRank sizing
    calculatePageRank(nodes, links);

    const svg = d3.select(svgEl)
      .attr("width", "100%")
      .attr("height", height);

    svg.selectAll("*").remove(); // Clean canvas

    const colorScale = d3.scaleOrdinal()
      .domain(["topic", "uploaded", "reference"])
      .range(["#EF4444", "#3B82F6", "#10B981"]);

    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id(d => d.id).distance(150))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(d => {
        const baseRadius = d.type === "topic" ? 16 : d.type === "uploaded" ? 12 : 8;
        const prMultiplier = d.pagerank ? d.pagerank * 50 : 2;
        return Math.max(8, baseRadius + prMultiplier);
      }));

    // Draw links
    const link = svg.append("g")
      .selectAll("line")
      .data(links)
      .enter().append("line")
      .attr("class", "link")
      .attr("stroke", "rgba(255, 255, 255, 0.1)")
      .attr("stroke-width", 1.5);

    // Draw nodes
    const node = svg.append("g")
      .selectAll("circle")
      .data(nodes)
      .enter().append("circle")
      .attr("class", "node")
      .attr("r", d => {
        const baseRadius = d.type === "topic" ? 14 : d.type === "uploaded" ? 11 : 7;
        const prMultiplier = d.pagerank ? d.pagerank * 60 : 2;
        return Math.max(7, baseRadius + prMultiplier);
      })
      .attr("fill", d => colorScale(d.type))
      .attr("stroke", "rgba(255, 255, 255, 0.2)")
      .attr("stroke-width", 1.5)
      .on("mouseover", (event, d) => {
        const prPercent = d.pagerank ? (d.pagerank * 100).toFixed(1) : "N/A";
        setTooltipData({
          id: d.id,
          type: d.type.toUpperCase(),
          pagerank: prPercent
        });
      })
      .on("mousemove", (event) => {
        const containerRect = container.getBoundingClientRect();
        setTooltipPos({
          x: event.clientX - containerRect.left + 15,
          y: event.clientY - containerRect.top + 15
        });
      })
      .on("mouseout", () => {
        setTooltipData(null);
      })
      .call(d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended));

    // Draw labels
    const label = svg.append("g")
      .selectAll("text")
      .data(nodes)
      .enter().append("text")
      .attr("class", "node-text")
      .attr("font-size", "10px")
      .attr("fill", "#9CA3AF")
      .attr("text-anchor", "middle")
      .attr("dy", d => {
        const baseRadius = d.type === "topic" ? 14 : d.type === "uploaded" ? 11 : 7;
        const prMultiplier = d.pagerank ? d.pagerank * 60 : 2;
        const radius = Math.max(7, baseRadius + prMultiplier);
        return -(radius + 4);
      })
      .text(d => d.label);

    simulation.on("tick", () => {
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
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    return () => {
      simulation.stop();
    };
  }, [graphData]);

  const hasNodes = graphData && graphData.nodes && graphData.nodes.length > 0;

  return (
    <div ref={containerRef} style={{ position: 'relative', width: '100%' }}>
      {!hasNodes ? (
        <div className="empty-state">Awaiting analysis to compile reference networks...</div>
      ) : (
        <svg ref={svgRef} id="citation-svg" style={{ width: '100%', height: '500px' }}></svg>
      )}

      {tooltipData && (
        <div 
          className="graph-tooltip"
          style={{
            position: 'absolute',
            left: `${tooltipPos.x}px`,
            top: `${tooltipPos.y}px`,
            background: 'rgba(11, 15, 25, 0.95)',
            border: '1px solid rgba(59, 130, 246, 0.3)',
            padding: '0.6rem',
            borderRadius: '6px',
            pointerEvents: 'none',
            fontSize: '0.75rem',
            color: '#F3F4F6',
            zIndex: 100
          }}
        >
          <strong>{tooltipData.id}</strong><br/>
          Type: {tooltipData.type}<br/>
          PageRank Network Influence: {tooltipData.pagerank}%
        </div>
      )}
    </div>
  );
}
