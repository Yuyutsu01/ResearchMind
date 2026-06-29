import React from 'react';

export default function ExecutiveBrief({ sections }) {
  if (!sections) {
    return <div className="empty-state">No brief parameters. Run an analysis first.</div>;
  }

  const brief = sections.executive_brief || {};
  const contributions = sections.key_contributions || [];
  const matters = sections.why_it_matters || {};
  const roadmap = sections.reading_roadmap || {};

  const domain = brief.research_domain || "Scientific Research";
  const readingTime = brief.reading_time || "12 mins";
  const diffScore = brief.difficulty_score || "5";

  return (
    <div className="brief-grid">
      {/* Card 1: Executive Summary */}
      <div className="brief-card">
        <div className="brief-card-header">
          <h4>Executive Summary</h4>
          <div className="metadata-row">
            <span className="meta-pill domain-pill">{domain}</span>
            <span className="meta-pill time-pill">{readingTime}</span>
            <span className="meta-pill difficulty-pill">Diff: {diffScore}/10</span>
          </div>
        </div>
        <div className="brief-card-body">
          <div className="brief-section">
            <h5>Problem Statement</h5>
            <p>{brief.problem_statement || "Not detailed."}</p>
          </div>
          <div className="brief-section">
            <h5>Proposed Solution</h5>
            <p>{brief.proposed_solution || "Not detailed."}</p>
          </div>
          <div className="brief-section">
            <h5>Key Innovation</h5>
            <p>{brief.key_innovation || "Not detailed."}</p>
          </div>
          <div className="brief-section">
            <h5>Main Findings & Empirical Results</h5>
            <p>{brief.main_results || "Not detailed."}</p>
          </div>
        </div>
      </div>

      {/* Card 2: Key Contributions */}
      <div className="brief-card">
        <div className="brief-card-header">
          <h4>Key Contributions</h4>
        </div>
        <div className="brief-card-body scrollable-card-body">
          {contributions.length > 0 ? (
            contributions.map((c, index) => (
              <div key={index} className="brief-cont-item">
                <h5>{c.title}</h5>
                <p>{c.description}</p>
                <div className="brief-cont-importance">
                  <strong>Importance:</strong> {c.importance}
                </div>
              </div>
            ))
          ) : (
            <p className="no-items">No explicit contributions analyzed.</p>
          )}
        </div>
      </div>

      {/* Card 3: Why Paper Matters */}
      <div className="brief-card">
        <div className="brief-card-header">
          <h4>Why This Paper Matters</h4>
        </div>
        <div className="brief-card-body scrollable-card-body">
          <div className="brief-section">
            <h5>Historical Lineage</h5>
            <p>{matters.historical_importance || "N/A"}</p>
          </div>
          <div className="brief-section">
            <h5>Academic Influence</h5>
            <p>{matters.academic_impact || "N/A"}</p>
          </div>
          <div className="brief-section">
            <h5>Industry Application</h5>
            <p>{matters.industry_impact || "N/A"}</p>
          </div>
          <div className="brief-section">
            <h5>Influenced Systems & Models</h5>
            <p>
              {Array.isArray(matters.papers_influenced)
                ? matters.papers_influenced.join(", ")
                : matters.papers_influenced || "N/A"}
            </p>
          </div>
        </div>
      </div>

      {/* Card 4: Reading Roadmap */}
      <div className="brief-card">
        <div className="brief-card-header">
          <h4>Reading Roadmap</h4>
        </div>
        <div className="brief-card-body">
          <div className="brief-section">
            <h5>Prerequisites (Read Before)</h5>
            <div className="pills-flex">
              {roadmap.before_reading && roadmap.before_reading.length > 0 ? (
                roadmap.before_reading.map((item, idx) => (
                  <span key={idx} className="roadmap-pill prerequisite">
                    {item}
                  </span>
                ))
              ) : (
                <span className="no-items">None specified</span>
              )}
            </div>
          </div>
          <div className="brief-section">
            <h5>Follow-up Recommendations (Read After)</h5>
            <div className="pills-flex">
              {roadmap.after_reading && roadmap.after_reading.length > 0 ? (
                roadmap.after_reading.map((item, idx) => (
                  <span key={idx} className="roadmap-pill successor">
                    {item}
                  </span>
                ))
              ) : (
                <span className="no-items">None specified</span>
              )}
            </div>
          </div>
          <div className="brief-section">
            <h5>Learning Path Strategy</h5>
            <p>{roadmap.learning_path || "N/A"}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
