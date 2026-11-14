import React, { useState } from 'react';
import { formatConfidence } from '../utils/formatters';

export default function AnalysisPanel({ analysis }) {
  const [isReasoningOpen, setIsReasoningOpen] = useState(true);
  const [copiedIndex, setCopiedIndex] = useState(null);

  if (!analysis) {
    return (
      <div className="panel empty-analysis">
        <p>Submit an incident or select an existing one to inspect AI diagnostic analysis.</p>
      </div>
    );
  }

  const confidenceInfo = formatConfidence(analysis.confidence);

  // Fallbacks and extractions
  const primaryCause =
    analysis.primary_cause ||
    (analysis.possible_causes && analysis.possible_causes[0]) ||
    null;

  const reasoningSteps = analysis.reasoning_chain || [];

  const alternativeList =
    (analysis.alternative_hypotheses && analysis.alternative_hypotheses.length > 0)
      ? analysis.alternative_hypotheses
      : (analysis.possible_causes && analysis.possible_causes.length > 1)
        ? analysis.possible_causes.slice(1).map((item) => ({
            cause: item.cause,
            status: 'alternative',
            ruling_out_rationale: 'Secondary candidate considered based on initial telemetry.',
            evidence: item.evidence || [],
          }))
        : [];

  const logExcerpts = analysis.supporting_log_excerpts || [];

  const structuredChecks =
    (analysis.structured_checks && analysis.structured_checks.length > 0)
      ? analysis.structured_checks
      : (analysis.recommended_checks || []).map((c) => ({
          check: c,
          check_type: 'read_only',
          command_hint: null,
        }));

  function handleCopy(command, idx) {
    if (!command) return;
    navigator.clipboard.writeText(command);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  }

  return (
    <div className="analysis-panel-root">
      {/* 1. Human Verification Advisory Banner */}
      <div className="human-verification-advisory-banner">
        <span className="advisory-icon">⚠️</span>
        <div className="advisory-text">
          <strong>Advisory AI Investigation:</strong> AI-generated diagnosis is an evidence-based hypothesis.
          Engineer verification is required before any resolution becomes trusted institutional memory.
        </div>
      </div>

      {/* 2. Header with Summary and Confidence Badges */}
      <div className="analysis-header-card">
        <div className="analysis-badges-row">
          <span className={`confidence-badge ${confidenceInfo.badgeClass}`}>
            Confidence: {confidenceInfo.label}
          </span>
          {analysis.analysis_source === 'groq' ? (
            <span className="source-badge source-groq">Groq AI Active</span>
          ) : (
            <span className="source-badge source-local">
              {analysis.analysis_source === 'local_fallback' ? 'Local Fallback Engine' : 'Deterministic Analysis'}
            </span>
          )}
          <span className="hypothesis-indicator-pill">AI Hypothesis — Unconfirmed</span>
        </div>

        <p className="analysis-summary-text">{analysis.summary}</p>

        {analysis.analysis_notice && (
          <div className="analysis-notice-box">
            <span className="notice-icon">ℹ️</span>
            <span>{analysis.analysis_notice}</span>
          </div>
        )}
      </div>

      {/* 3. Evidence-Backed Leading Cause */}
      {primaryCause && (
        <div className="analysis-section leading-cause-section">
          <div className="leading-cause-card">
            <div className="leading-cause-top">
              <span className="leading-cause-badge">🎯 Primary Hypothesis</span>
              <span className={`cause-confidence ${formatConfidence(primaryCause.confidence).badgeClass}`}>
                {formatConfidence(primaryCause.confidence).label}
              </span>
            </div>
            <h3 className="leading-cause-title">{primaryCause.cause}</h3>

            {/* Verbatim Supporting Log Excerpts */}
            <div className="supporting-excerpts-wrapper">
              <div className="excerpts-header">
                <span className="excerpts-label">📄 Verbatim Log Evidence Lines ({logExcerpts.length})</span>
                <span className="excerpts-sub">Directly traced from sanitized logs</span>
              </div>

              {logExcerpts.length > 0 ? (
                <div className="excerpts-list">
                  {logExcerpts.map((excerpt, idx) => (
                    <div key={idx} className="log-excerpt-row">
                      <div className="excerpt-meta-col">
                        <span className="excerpt-line-badge">Line {excerpt.line_number || idx + 1}</span>
                        {excerpt.signal_matched && (
                          <span className="excerpt-signal-pill">{excerpt.signal_matched}</span>
                        )}
                      </div>
                      <pre className="excerpt-code">{excerpt.log_text}</pre>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="no-excerpts-notice">
                  <span>ℹ️ No direct error log lines isolated from raw logs. Diagnosis was synthesized from description and system context.</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 4. Observed Symptoms */}
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

      {/* 5. Diagnostic Reasoning Chain (Expandable) */}
      {reasoningSteps.length > 0 && (
        <div className="analysis-section reasoning-section">
          <div
            className="section-title-toggle"
            onClick={() => setIsReasoningOpen(!isReasoningOpen)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                setIsReasoningOpen(!isReasoningOpen);
              }
            }}
          >
            <h4 className="section-title">
              <span>🧠 Diagnostic Reasoning &amp; Causality Chain ({reasoningSteps.length} Steps)</span>
            </h4>
            <span className="toggle-btn-indicator">
              {isReasoningOpen ? '▲ Collapse Reasoning' : '▼ Expand Reasoning'}
            </span>
          </div>

          {isReasoningOpen && (
            <div className="reasoning-chain-steps">
              {reasoningSteps.map((step, idx) => (
                <div key={idx} className="reasoning-step-item">
                  <div className="step-marker-col">
                    <span className="step-index-pill">{idx + 1}</span>
                    {idx < reasoningSteps.length - 1 && <span className="step-line" />}
                  </div>
                  <div className="step-content">
                    <p className="step-text">{step.replace(/^\d+\.\s*/, '')}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 6. Alternative Hypotheses (Differential Diagnosis) */}
      {alternativeList.length > 0 && (
        <div className="analysis-section alternative-hypotheses-section">
          <h4 className="section-title">⚖️ Alternative Hypotheses Considered (Differential Diagnosis)</h4>
          <div className="alternatives-grid">
            {alternativeList.map((alt, idx) => {
              const status = alt.status || 'alternative';
              const statusLabel =
                status === 'ruled_out'
                  ? 'Ruled Out'
                  : status === 'less_likely'
                  ? 'Less Likely'
                  : 'Alternative Hypothesis';
              const statusClass =
                status === 'ruled_out'
                  ? 'status-ruled-out'
                  : status === 'less_likely'
                  ? 'status-less-likely'
                  : 'status-alt';

              return (
                <div key={idx} className="alternative-card">
                  <div className="alt-header">
                    <span className="alt-title">{alt.cause}</span>
                    <span className={`alt-status-pill ${statusClass}`}>{statusLabel}</span>
                  </div>
                  {alt.ruling_out_rationale && (
                    <div className="alt-rationale-box">
                      <span className="rationale-tag">Differential Rationale:</span>
                      <p>{alt.ruling_out_rationale}</p>
                    </div>
                  )}
                  {alt.evidence && alt.evidence.length > 0 && (
                    <div className="alt-evidence-row">
                      <span className="alt-evidence-label">Observed signal:</span>
                      <span className="alt-evidence-text">{alt.evidence.join('; ')}</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 7. Recommended Diagnostic Checks (Categorized) */}
      {structuredChecks.length > 0 && (
        <div className="analysis-section checks-section">
          <div className="checks-header-row">
            <h4 className="section-title">🛠️ Recommended Actionable Diagnostic Checks</h4>
            <span className="checks-safety-note">Distinguishing safe read-only checks from disruptive actions</span>
          </div>

          <div className="structured-checks-list">
            {structuredChecks.map((item, idx) => {
              const checkType = item.check_type || 'read_only';
              const badgeLabel =
                checkType === 'read_only'
                  ? '🟢 READ-ONLY'
                  : checkType === 'active_validation'
                  ? '🟡 ACTIVE VALIDATION'
                  : '🟠 MITIGATION';
              const badgeClass =
                checkType === 'read_only'
                  ? 'badge-check-readonly'
                  : checkType === 'active_validation'
                  ? 'badge-check-active'
                  : 'badge-check-mitigation';

              return (
                <div key={idx} className="structured-check-item">
                  <div className="check-item-top">
                    <span className={`check-type-pill ${badgeClass}`}>{badgeLabel}</span>
                    <span className="check-text-content">{item.check}</span>
                  </div>

                  {item.command_hint && (
                    <div className="command-hint-box">
                      <code className="command-code">{item.command_hint}</code>
                      <button
                        type="button"
                        className="copy-command-btn"
                        onClick={() => handleCopy(item.command_hint, idx)}
                        title="Copy command to clipboard"
                      >
                        {copiedIndex === idx ? '✓ Copied' : '📋 Copy'}
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
          <p className="checks-disclaimer-text">
            * Suggested for human operators. OpsRecall AI does not automatically execute commands.
          </p>
        </div>
      )}

      {/* 8. Confidence Justification & Observability Limitations */}
      <div className="analysis-meta-grid">
        <div className="meta-box confidence-box">
          <h5>📊 Confidence Justification ({confidenceInfo.label})</h5>
          <p className="justification-text">
            {analysis.confidence_justification ||
              `Assigned qualitative ${confidenceInfo.label} confidence based on supplied incident telemetry.`}
          </p>
          <span className="uncalibrated-disclaimer">
            * Qualitative operational assessment. Not a calibrated mathematical probability.
          </span>
        </div>

        {analysis.missing_information && analysis.missing_information.length > 0 && (
          <div className="meta-box missing-info-box">
            <h5>🔍 Missing Telemetry Signals to Confirm Root Cause:</h5>
            <ul>
              {analysis.missing_information.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
          </div>
        )}

        {analysis.safety_notes && analysis.safety_notes.length > 0 && (
          <div className="meta-box safety-box">
            <h5>🛡️ Operational Safety Guarantee:</h5>
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
