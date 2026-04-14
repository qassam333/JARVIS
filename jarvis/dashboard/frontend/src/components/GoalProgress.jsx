import React, { useState } from 'react';
import api from '../api';

export default function GoalProgress({ goals }) {
  const [editing, setEditing] = useState(null);
  const [newProgress, setNewProgress] = useState(0);

  const handleUpdate = async (goalId) => {
    try {
      await api.updateGoalProgress(goalId, newProgress);
      setEditing(null);
    } catch (error) {
      console.error('Failed to update progress:', error);
    }
  };

  const ProgressBar = ({ progress, color }) => (
    <div className="progress-bar">
      <div
        className="progress-fill"
        style={{ width: `${progress}%` }}
      />
    </div>
  );

  const PriorityBadge = ({ priority }) => {
    const colors = {
      critical: 'bg-danger/20 text-danger border-danger',
      high: 'bg-warning/20 text-warning border-warning',
      medium: 'bg-cyan/20 text-cyan border-cyan',
      low: 'bg-text-dim/20 text-text-dim border-text-dim',
    };
    
    return (
      <span className={`text-xs px-2 py-0.5 rounded border ${colors[priority] || colors.medium}`}>
        {priority.toUpperCase()}
      </span>
    );
  };

  const sortedGoals = [...goals].sort((a, b) => {
    const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
    return (priorityOrder[a.priority] || 2) - (priorityOrder[b.priority] || 2);
  });

  return (
    <div className="card h-full">
      <h2 className="font-heading text-lg text-cyan tracking-wider mb-4">
        GOAL PROGRESS
      </h2>

      <div className="space-y-4 max-h-[350px] overflow-y-auto pr-2">
        {sortedGoals.map((goal) => (
          <div key={goal.id} className="space-y-2">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span 
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: goal.area_color }}
                  />
                  <span className="font-body text-sm font-semibold">
                    {goal.title}
                  </span>
                </div>
                <PriorityBadge priority={goal.priority} />
              </div>
              
              {editing === goal.id ? (
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={newProgress}
                    onChange={(e) => setNewProgress(parseInt(e.target.value) || 0)}
                    className="w-16 px-2 py-1 bg-background-dark border border-cyan rounded text-center font-mono text-sm"
                  />
                  <button
                    onClick={() => handleUpdate(goal.id)}
                    className="btn-icon text-xs px-2 py-1"
                  >
                    OK
                  </button>
                  <button
                    onClick={() => setEditing(null)}
                    className="text-text-dim hover:text-danger text-xs"
                  >
                    X
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => {
                    setEditing(goal.id);
                    setNewProgress(goal.progress);
                  }}
                  className="font-mono text-cyan text-sm hover:text-cyan-glow"
                >
                  {goal.progress}%
                </button>
              )}
            </div>

            <ProgressBar progress={goal.progress} color={goal.area_color} />

            {goal.target_date && (
              <div className="text-xs text-text-dim">
                Due: {new Date(goal.target_date).toLocaleDateString()}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
