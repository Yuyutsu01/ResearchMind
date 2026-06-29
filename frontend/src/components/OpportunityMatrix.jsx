import React from 'react';

export default function OpportunityMatrix({ sections }) {
  if (!sections || !sections.opportunities) {
    return <div className="empty-state">No opportunities computed. Run a paper analysis.</div>;
  }

  const opportunities = sections.opportunities || [];

  if (opportunities.length === 0) {
    return <div className="empty-state">No opportunities analyzed.</div>;
  }

  return (
    <div className="card">
      <h3>Opportunity Matrix</h3>
      <p className="section-description">Extrapolated funding, timeline, and difficulty assessments ranked by expected impact score.</p>
      <div id="opportunities-container" className="opportunities-container">
        {opportunities.map((opp, idx) => {
          const impactVal = parseInt(opp.impact) || 5;
          let impactClass = "impact-low";
          if (impactVal >= 8) {
            impactClass = "impact-high";
          } else if (impactVal >= 5) {
            impactClass = "impact-medium";
          }

          return (
            <div key={idx} className={`opportunity-matrix-card ${impactClass}`}>
              <div className="opp-card-header">
                <h4>{opp.title}</h4>
                <span className="badge opp-impact-badge">Impact: {opp.impact}/10</span>
              </div>
              <p className="opp-description">{opp.description}</p>
              
              <div className="opp-meta-grid">
                <div className="opp-meta-box">
                  <span className="opp-meta-label">Novelty</span>
                  <span className="opp-meta-val">{opp.novelty}/10</span>
                </div>
                <div className="opp-meta-box">
                  <span className="opp-meta-label">Difficulty</span>
                  <span className="opp-meta-val">{opp.difficulty}/10</span>
                </div>
                <div className="opp-meta-box">
                  <span className="opp-meta-label">Timeline</span>
                  <span className="opp-meta-val">{opp.time}</span>
                </div>
                <div className="opp-meta-box">
                  <span className="opp-meta-label">Funding</span>
                  <span className="opp-meta-val">{opp.funding || 'High'}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
