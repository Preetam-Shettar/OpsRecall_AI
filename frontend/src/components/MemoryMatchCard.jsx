import React from 'react';

export default function MemoryMatchCard({ memories = [] }) {
  if (!memories || memories.length === 0) {
    return (
      <div className="memory-card empty">
        <div className="memory-card-header">
          <span className="memory-chip memory-chip-neutral">🧠 Hindsight Memory</span>
        </div>
        <p className="empty-text">No relevant past incidents found in the memory bank yet.</p>
        <span className="empty-subtext">Verified resolutions saved for this incident will become persistent memory for future incidents.</span>
      </div>
    );
  }

  return (
    <div className="memory-match-container">
      <div className="memory-card-header">
        <div className="memory-title-group">
          <span className="memory-chip memory-chip-active">🧠 Hindsight Recall Active</span>
          <h4>Related Past Incidents ({memories.length})</h4>
        </div>
        <span className="memory-badge-verified">Verified Historical Resolutions</span>
      </div>

      <p className="memory-disclaimer">
        <strong>Context note:</strong> Prior verified fixes are retrieved as context to avoid repetitive debugging, not as proof that causes are identical.
      </p>

      <div className="memory-items-list">
        {memories.map((mem, index) => {
          const incId = mem.incident_id || mem.context || `INC-00${index + 1}`;
          const content = mem.lesson || mem.content || '';

          return (
            <div key={`${incId}-${index}`} className="memory-item">
              <div className="memory-item-top">
                <span className="memory-ref-badge">{incId}</span>
                {mem.service && <span className="memory-service-tag">{mem.service}</span>}
                <span className="memory-verified-tag">✓ Confirmed Fix</span>
              </div>
              <p className="memory-lesson-text">{content}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
