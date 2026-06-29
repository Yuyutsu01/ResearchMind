import React, { useState } from 'react';

export default function Deconstruction({ sections }) {
  if (!sections || !sections.paper_deconstruction) {
    return <div className="empty-state">No deconstruction metrics. Run an analysis first.</div>;
  }

  const deconstruction = sections.paper_deconstruction;
  const [openItems, setOpenItems] = useState({});

  const toggleAccordion = (key) => {
    setOpenItems(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const sectionsList = [
    { key: "problem", title: "Core Scientific Problem" },
    { key: "motivation", title: "Research Motivation" },
    { key: "methodology", title: "Methodology & Architecture Details" },
    { key: "experiments", title: "Experimental Settings & Benchmark Data" },
    { key: "results", title: "Empirical Outcomes & Achievements" },
    { key: "limitations", title: "Methodological Constraints & Limitations" },
    { key: "future_work", title: "Proposed Future Extensions" }
  ];

  return (
    <div className="card">
      <h3>Paper Deconstruction</h3>
      <p className="section-description">Collapsible breakdown of the paper's design and outcomes for rapid scanning.</p>
      <div id="deconstruction-accordion" className="accordion-container">
        {sectionsList.map((item) => {
          const content = deconstruction[item.key] || "No detail compiled.";
          const isOpen = !!openItems[item.key];

          return (
            <div key={item.key} className={`accordion-item ${isOpen ? 'open' : ''}`}>
              <button className="accordion-trigger" onClick={() => toggleAccordion(item.key)}>
                <span>{item.title}</span>
                <span className="chevron-icon" style={{ transform: isOpen ? 'rotate(180deg)' : 'rotate(0)' }}>
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="6 9 12 15 18 9"></polyline>
                  </svg>
                </span>
              </button>
              <div className="accordion-panel" style={{ display: isOpen ? 'block' : 'none' }}>
                <div className="accordion-content">
                  <p>{content}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
