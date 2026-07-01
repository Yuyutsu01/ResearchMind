import React from 'react';

export default function Header({ status, onTrainPolicy, isTraining }) {
  return (
    <header className="app-header">
      <div className="logo-area">
        <svg className="logo-icon" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
        </svg>
        <h1>ResearchMind</h1>
      </div>

      <div className="header-controls">
        <button 
          id="train-policy-btn" 
          className="btn btn-secondary btn-small"
          onClick={onTrainPolicy}
          disabled={isTraining}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/>
          </svg>
          {isTraining ? 'Training...' : 'Train Policy'}
        </button>
        <div className="status-indicator">
          <span className={`dot ${status === 'Connected' ? 'connected' : ''}`}></span>
          <span id="status-text">{status}</span>
        </div>
      </div>
    </header>
  );
}
