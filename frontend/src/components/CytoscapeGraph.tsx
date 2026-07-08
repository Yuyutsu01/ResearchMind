import React, { useEffect, useRef } from "react";
import cytoscape from "cytoscape";

interface GraphNode {
  id: string;
  label: string;
  type: string;
}

interface GraphEdge {
  source: string;
  target: string;
  relationship: string;
}

interface CytoscapeGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export default function CytoscapeGraph({ nodes, edges }: CytoscapeGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || !nodes.length) return;

    // Format elements for cytoscape format
    const cyNodes = nodes.map((node) => ({
      data: {
        id: node.id,
        label: node.label || node.id,
        type: node.type || "concept"
      }
    }));

    const cyEdges = edges.map((edge, idx) => ({
      data: {
        id: `e_${idx}`,
        source: edge.source,
        target: edge.target,
        label: edge.relationship || "cites"
      }
    }));

    const cy = cytoscape({
      container: containerRef.current,
      elements: [...cyNodes, ...cyEdges],
      style: [
        {
          selector: "node",
          style: {
            "label": "data(label)",
            "color": "#F3F4F6",
            "font-size": "10px",
            "font-family": "Outfit, sans-serif",
            "text-valign": "center",
            "text-halign": "center",
            "background-color": "#4B5563",
            "width": "35px",
            "height": "35px",
            "overlay-padding": "6px",
            "z-index": 10
          }
        },
        {
          selector: 'node[type="paper"]',
          style: {
            "background-color": "#3B82F6",
            "shape": "rectangle",
            "width": "50px",
            "height": "25px"
          }
        },
        {
          selector: 'node[type="concept"]',
          style: {
            "background-color": "#10B981",
            "shape": "ellipse"
          }
        },
        {
          selector: 'node[type="method"]',
          style: {
            "background-color": "#8B5CF6",
            "shape": "hexagon"
          }
        },
        {
          selector: 'node[type="dataset"]',
          style: {
            "background-color": "#F59E0B",
            "shape": "triangle"
          }
        },
        {
          selector: "edge",
          style: {
            "width": 1.5,
            "line-color": "rgba(255, 255, 255, 0.15)",
            "target-arrow-color": "rgba(255, 255, 255, 0.15)",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            "label": "data(label)",
            "font-size": "8px",
            "color": "#9CA3AF",
            "text-rotation": "autorotate",
            "text-margin-y": -8
          }
        }
      ],
      layout: {
        name: "cose",
        animate: true,
        fit: true,
        padding: 30
      } as any
    });

    return () => {
      cy.destroy();
    };
  }, [nodes, edges]);

  return (
    <div className="w-full h-full min-h-[400px] relative glass-panel overflow-hidden">
      <div ref={containerRef} className="absolute inset-0 w-full h-full" />
      {nodes.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center text-slate-500 text-sm">
          No concepts or connections generated yet.
        </div>
      )}
    </div>
  );
}
