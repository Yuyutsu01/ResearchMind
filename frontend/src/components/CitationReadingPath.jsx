import React from 'react';

export default function CitationReadingPath({ sections }) {
  if (!sections) {
    return <div className="empty-state">No analysis sections found.</div>;
  }

  const roadmap = sections.reading_roadmap || {};
  const beforeRoadmap = roadmap.before_reading || [];
  const afterRoadmap = roadmap.after_reading || [];
  const brief = sections.executive_brief || {};
  const currentTitle = brief.proposed_solution || "Active Research Subject";

  if (beforeRoadmap.length === 0 && afterRoadmap.length === 0) {
    return <div className="empty-state">No recommended reading pathway extracted.</div>;
  }

  let stepNum = 1;

  return (
    <table className="reading-path-table">
      <thead>
        <tr>
          <th>Sequence</th>
          <th>Role</th>
          <th>Topic / Paper Reference</th>
          <th>Instructional Guideline</th>
        </tr>
      </thead>
      <tbody>
        {/* Prerequisites */}
        {beforeRoadmap.map((item, idx) => (
          <tr key={`before-${idx}`}>
            <td>Step {stepNum++}</td>
            <td><span className="badge prerequisite-badge">Prerequisite</span></td>
            <td><strong>{item}</strong></td>
            <td>Gain fundamental foundations before reviewing the core methodology.</td>
          </tr>
        ))}

        {/* Current Core Subject */}
        <tr className="active-reading-row">
          <td>Step {stepNum++}</td>
          <td><span className="badge active-badge">Core Subject</span></td>
          <td><strong>{currentTitle}</strong></td>
          <td>Primary focus of the active research brief.</td>
        </tr>

        {/* Successors */}
        {afterRoadmap.map((item, idx) => (
          <tr key={`after-${idx}`}>
            <td>Step {stepNum++}</td>
            <td><span className="badge successor-badge">Follow-up</span></td>
            <td><strong>{item}</strong></td>
            <td>Apply methods to extensions, related domains, or specialized problems.</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
