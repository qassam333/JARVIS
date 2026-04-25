import React from 'react';

export default function Countdown({ daysLeft, isGradDay }) {
  if (daysLeft === null) {
    return (
      <div className="card text-center">
        <p className="text-text-muted">Grad deadline not set</p>
      </div>
    );
  }

  const getMessage = () => {
    if (daysLeft <= 7) return "CRITICAL";
    if (daysLeft <= 30) return "FINAL STRETCH";
    if (daysLeft <= 60) return "GET FOCUSED";
    return "STAY ON TRACK";
  };

  const getColor = () => {
    if (daysLeft <= 7) return "text-danger";
    if (daysLeft <= 30) return "text-warning";
    return "text-primary";
  };

  return (
    <div className={`card-glow text-center ${getColor()}`}>
      <h3 className="font-heading text-sm tracking-[0.3em] text-text-muted mb-2">
        GRADUATION
      </h3>
      <div className="font-mono text-6xl font-bold mb-2">
        {daysLeft}
      </div>
      <p className="font-heading text-sm tracking-wider">DAYS LEFT</p>
      <div className="mt-3 py-1 px-3 rounded bg-background-dark inline-block">
        <span className="text-xs text-text-muted">{getMessage()}</span>
      </div>
      {isGradDay && (
        <div className="mt-2 text-success text-xs">
          GRAD PROJECT DAY
        </div>
      )}
    </div>
  );
}
