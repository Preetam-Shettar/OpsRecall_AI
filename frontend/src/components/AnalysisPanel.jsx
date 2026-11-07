import React from 'react';
import { formatConfidence } from '../utils/formatters';

export default function AnalysisPanel({ analysis }) {
  if (!analysis) {
    return (
      <div className="panel empty-analysis">
        <p>Submit an incident or select an existing one to inspect AI diagnostic analysis.</p>
      </div>
    );
  }

  const confidenceInfo = formatConfidence(analysis.confidence);

  return (
    <div className="analysis-panel-root">
      {/* Header with Summary and Badges */}
      <div className="analysis-header-card">
        <div className="analysis-badges-row">
          <span className={`confidence-badge ${confidenceInfo.badgeClass}`}>
            {confidenceInfo.label}
          </span>
          {analysis.analysis_source === 'groq' ? (
            <span className="source-badge source-groq">Groq AI Active</span>
          ) : (
            <span className="source-badge source-local">
              {analysis.analysis_source === 'local_fallback' ? 'Local Fallback Engine' : 'Deterministic Analysis'}
            </span>
          )}
        </div>

        <p className="analysis-summary-text">{analysis.summary}</p>

        {analysis.analysis_notice && (
          <div className="analysis-notice-box">
            <span className="notice-icon">ℹ️</span>
            <span>{analysis.analysis_notice}</span>
          </div>
        )}
      </div>

      {/* Observed Symptoms */}
      {analysis.symptoms && analysis.symptoms.length > 0 && (
        <div className="analysis-section">
          <h4 className="section-title">Observed Symptoms</h4>
          <div className="symptoms-chips">
            {analysis.symptoms.map((symptom, idx) => (
              <span key={idx} className="symptom-chip">
                ⚠️ {symptom}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Possible Causes */}
      {analysis.possible_causes && analysis.possible_causes.length > 0 && (
        <div className="analysis-section">
          <h4 className="section-title">Possible Root Causes (Hypotheses)</h4>
          <div className="causes-list">
            {analysis.possible_causes.map((causeItem, idx) => {
              const causeConfidence = formatConfidence(causeItem.confidence);
              return (
                <div key={idx} className="cause-card">
                  <div className="cause-card-header">
                    <span className="cause-title">{causeItem.cause}</span>
                    <span className={`cause-confidence ${causeConfidence.badgeClass}`}>
                      {causeConfidence.label}
                    </span>
                  </div>
                  {causeItem.evidence && causeItem.evidence.length > 0 && (
                    <div className="cause-evidence">
                      <span className="evidence-label">Supporting clues in logs:</span>
                      <ul className="evidence-list">
                        {causeItem.evidence.map((ev, evIdx) => (
                          <li key={evIdx}>{ev}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Recommended Safe Checks */}
      {analysis.recommended_checks && analysis.recommended_checks.length > 0 && (
        <div className="analysis-section">
          <h4 className="section-title">Recommended Safe Investigation Steps</h4>
          <ol className="checks-list">
            {analysis.recommended_checks.map((check, idx) => (
              <li key={idx} className="check-item">
                <span className="check-number">{idx + 1}</span>
                <span className="check-text">{check}</span>
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Missing Information & Safety Notes */}
      <div className="analysis-meta-grid">
        {analysis.missing_information && analysis.missing_information.length > 0 && (
          <div className="meta-box">
            <h5>Missing Signals to Confirm Cause:</h5>
            <ul>
              {analysis.missing_information.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
          </div>
        )}

        {analysis.safety_notes && analysis.safety_notes.length > 0 && (
          <div className="meta-box safety-box">
            <h5>Operational Safety Guarantee:</h5>
            <ul>
              {analysis.safety_notes.map((note, idx) => (
                <li key={idx}>{note}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
