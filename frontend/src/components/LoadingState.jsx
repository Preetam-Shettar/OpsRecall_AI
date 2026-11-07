import React from 'react';

export default function LoadingState({ message = 'Analyzing incident logs & querying Hindsight memory...' }) {
  return (
    <div className="loading-state-container">
      <div className="spinner"></div>
      <p className="loading-text">{message}</p>
      <div className="loading-steps">
        <span className="step-tag active">1. Redacting secrets</span>
        <span className="step-arrow">→</span>
        <span className="step-tag active">2. Querying Hindsight bank</span>
        <span className="step-arrow">→</span>
        <span className="step-tag active">3. Synthesizing diagnosis</span>
      </div>
    </div>
  );
}
