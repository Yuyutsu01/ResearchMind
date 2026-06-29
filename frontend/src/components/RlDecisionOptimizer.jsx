import React from 'react';

export default function RlDecisionOptimizer({ choices, reward, stateKey }) {
  // Translate numeric choices to labels as in Vanilla client
  const sourceLabel = ["ArXiv", "Scholar", "Web Search"][choices?.source_selection] || "ArXiv";
  const strategyLabel = ["Semantic", "BM25", "Hybrid"][choices?.retrieval_strategy] || "Hybrid";
  const depthLabel = ["None", "Shallow", "Deep"][choices?.expansion_depth] || "Shallow";
  
  const formattedReward = reward !== null 
    ? (reward >= 0 ? `+${reward.toFixed(2)}` : reward.toFixed(2)) 
    : '+0.85';

  const activeStateKey = stateKey ? `Active State: ${stateKey}` : 'Active State: state_general_no_pdf';

  return (
    <div className="card">
      <h3>RL Decision Optimizer</h3>
      <div className="metrics-grid">
        <div className="metric-box">
          <div className="metric-label">Source Selection</div>
          <div id="rl-source" className="metric-val">{sourceLabel}</div>
        </div>
        <div className="metric-box">
          <div className="metric-label">RAG Strategy</div>
          <div id="rl-strategy" className="metric-val">{strategyLabel}</div>
        </div>
        <div className="metric-box">
          <div className="metric-label">Expansion Depth</div>
          <div id="rl-depth" className="metric-val">{depthLabel}</div>
        </div>
        <div className="metric-box">
          <div className="metric-label">Policy Reward</div>
          <div id="rl-reward" className="metric-val">{formattedReward}</div>
        </div>
      </div>
      <div id="rl-state-key" className="rl-state-key">{activeStateKey}</div>
    </div>
  );
}
