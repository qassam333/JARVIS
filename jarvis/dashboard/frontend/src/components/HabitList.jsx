import React, { useState } from 'react';
import api from '../api';

export default function HabitList({ habits, onUpdate }) {
  const [loading, setLoading] = useState(null);

  const handleToggle = async (habit) => {
    setLoading(habit.id);
    try {
      if (habit.completed_today) {
        await api.unlogHabit(habit.id);
      } else {
        await api.logHabit(habit.id, {
          pages: habit.name.toLowerCase().includes('quran') ? 1 : undefined,
        });
      }
      onUpdate();
    } catch (error) {
      console.error('Failed to toggle habit:', error);
    } finally {
      setLoading(null);
    }
  };

  const FireIcon = () => (
    <span className="fire-icon text-warning">🔥</span>
  );

  const StreakBadge = ({ streak }) => (
    <div className="flex items-center gap-1 text-xs text-text-muted">
      <FireIcon />
      <span className="font-mono">{streak}d</span>
    </div>
  );

  const ExtraInfo = ({ habit }) => {
    if (habit.pages) {
      return <span className="text-xs text-cyan">{habit.pages} pg</span>;
    }
    if (habit.duration) {
      return <span className="text-xs text-cyan">{habit.duration}m</span>;
    }
    return null;
  };

  const sortedHabits = [...habits].sort((a, b) => {
    if (a.completed_today !== b.completed_today) {
      return a.completed_today ? 1 : -1;
    }
    return b.current_streak - a.current_streak;
  });

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-heading text-lg text-cyan tracking-wider">
          TODAY'S HABITS
        </h2>
        <div className="text-sm text-text-muted">
          {habits.filter(h => h.completed_today).length}/{habits.length}
        </div>
      </div>

      <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2">
        {sortedHabits.map((habit) => (
          <div
            key={habit.id}
            className={`habit-item ${habit.completed_today ? 'completed' : ''}`}
          >
            <div className="flex items-center gap-3">
              <button
                onClick={() => handleToggle(habit)}
                disabled={loading === habit.id}
                className={`checkbox ${habit.completed_today ? 'checked' : ''}`}
              >
                {habit.completed_today && (
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                )}
              </button>
              <span className={`font-body ${habit.completed_today ? 'line-through text-text-muted' : 'text-text'}`}>
                {habit.name}
              </span>
            </div>

            <div className="flex items-center gap-3">
              <ExtraInfo habit={habit} />
              <StreakBadge streak={habit.current_streak} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
