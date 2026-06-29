import React from 'react';

export default function ResearchHistory({ history, activeTaskId, onSelectTask, onDeleteTask }) {
  const handleDelete = (e, taskId) => {
    e.stopPropagation();
    if (confirm(`Are you sure you want to delete research history for task #${taskId}?`)) {
      onDeleteTask(taskId);
    }
  };

  return (
    <div className="card flex-grow scrollable">
      <h3>Research History</h3>
      <div id="history-list" class="history-list">
        {history && history.length > 0 ? (
          history.map((item) => (
            <div 
              key={item.id} 
              className={`history-item ${activeTaskId === item.id ? 'active' : ''}`}
              onClick={() => onSelectTask(item.id, item.prompt)}
              style={{ borderColor: activeTaskId === item.id ? 'var(--primary)' : 'var(--border-color)' }}
            >
              <div className="history-item-main">
                <div className="history-item-title" title={item.prompt}>{item.prompt}</div>
                <div className="history-item-meta">
                  <span>#{item.id}</span>
                  <span style={{ color: item.status === 'completed' ? 'var(--success)' : 'var(--warning)' }}>
                    {item.status}
                  </span>
                </div>
              </div>
              <button 
                className="delete-history-btn" 
                title="Delete record"
                onClick={(e) => handleDelete(e, item.id)}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="3 6 5 6 21 6"></polyline>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                  <line x1="10" y1="11" x2="10" y2="17"></line>
                  <line x1="14" y1="11" x2="14" y2="17"></line>
                </svg>
              </button>
            </div>
          ))
        ) : (
          <div className="empty-state">No previous tasks.</div>
        )}
      </div>
    </div>
  );
}
