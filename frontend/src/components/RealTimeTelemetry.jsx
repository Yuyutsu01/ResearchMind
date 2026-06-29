import React from 'react';

export default function RealTimeTelemetry({ metrics }) {
  const planVal = metrics?.["Planning Latency"]?.avg_duration_ms ?? 0;
  const execVal = metrics?.["Execution Latency"]?.avg_duration_ms ?? 0;
  const validVal = metrics?.["Validation Rate"]?.success_rate ?? 0;

  // Normalized scaling calculations
  const planProgressWidth = `${Math.min(100, (planVal / 10) * 100)}%`;
  const execProgressWidth = `${Math.min(100, (execVal / 10) * 100)}%`;
  const validProgressWidth = `${validVal}%`;

  return (
    <div className="card flex-grow scrollable">
      <h3>Real-time Telemetry</h3>
      <div id="telemetry-list" className="telemetry-list">
        <div className="telemetry-item">
          <div className="telemetry-header">
            <span>Planning Latency</span>
            <span id="tel-plan-val" className="success-badge">{planVal.toFixed(1)}ms</span>
          </div>
          <div className="progress-bar">
            <div id="tel-plan-progress" className="progress" style={{ width: planProgressWidth }}></div>
          </div>
        </div>
        <div className="telemetry-item">
          <div className="telemetry-header">
            <span>Validation Rate</span>
            <span id="tel-valid-val" className="success-badge">{validVal.toFixed(0)}%</span>
          </div>
          <div className="progress-bar">
            <div id="tel-valid-progress" className="progress" style={{ width: validProgressWidth }}></div>
          </div>
        </div>
        <div className="telemetry-item">
          <div className="telemetry-header">
            <span>Execution Latency</span>
            <span id="tel-exec-val" className="success-badge">{execVal.toFixed(1)}ms</span>
          </div>
          <div className="progress-bar">
            <div id="tel-exec-progress" className="progress" style={{ width: execProgressWidth }}></div>
          </div>
        </div>
      </div>
    </div>
  );
}
