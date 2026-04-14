import React, { useState, useEffect, useCallback } from 'react';
import api from './api';
import Countdown from './components/Countdown';
import HabitList from './components/HabitList';
import GoalProgress from './components/GoalProgress';
import WeeklyStats from './components/WeeklyStats';
import Quote from './components/Quote';

function App() {
  const [profile, setProfile] = useState(null);
  const [habits, setHabits] = useState([]);
  const [goals, setGoals] = useState([]);
  const [weeklyStats, setWeeklyStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  const loadData = useCallback(async () => {
    try {
      const [profileData, habitsData, goalsData, statsData] = await Promise.all([
        api.getProfile(),
        api.getHabits(),
        api.getGoals(),
        api.getWeeklyStats(),
      ]);
      
      setProfile(profileData);
      setHabits(habitsData);
      setGoals(goalsData);
      setWeeklyStats(statsData);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 60000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleRefresh = () => {
    setLoading(true);
    loadData();
  };

  if (loading && !profile) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="text-cyan font-heading text-2xl tracking-[0.3em] mb-4 animate-pulse">
            LOADING JARVIS
          </div>
          <div className="w-48 h-1 bg-background-dark rounded overflow-hidden">
            <div className="h-full bg-cyan animate-pulse" style={{ width: '60%' }} />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen overflow-hidden bg-background">
      <div className="h-full flex flex-col">
        {/* Header */}
        <header className="flex-shrink-0 px-6 py-4 border-b border-cyan/20">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="font-heading text-2xl tracking-[0.2em] neon-text">
                JARVIS
              </h1>
              <span className="text-text-dim text-sm">|</span>
              <span className="font-heading text-sm tracking-wider text-purple-bright">
                O4 STUDIO
              </span>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="text-xs text-text-dim">
                Updated: {lastUpdate.toLocaleTimeString()}
              </div>
              <button
                onClick={handleRefresh}
                className="btn-icon"
                title="Refresh"
              >
                <svg className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 overflow-auto p-6">
          <div className="grid grid-cols-12 gap-6 h-full">
            {/* Top Row */}
            <div className="col-span-3">
              <Countdown 
                daysLeft={profile?.days_until_grad} 
                isGradDay={profile?.is_grad_day}
              />
            </div>
            <div className="col-span-3">
              <div className="card h-full flex flex-col justify-center items-center">
                <h3 className="font-heading text-sm tracking-[0.3em] text-text-muted mb-2">
                  TODAY
                </h3>
                <div className="font-heading text-4xl text-cyan">
                  {profile?.day_name}
                </div>
                <div className="text-sm text-text-dim mt-2">
                  {new Date(profile?.today).toLocaleDateString('en-US', { 
                    month: 'short', 
                    day: 'numeric' 
                  })}
                </div>
                {profile?.is_grad_day && (
                  <div className="mt-3 px-3 py-1 bg-warning/20 border border-warning rounded text-warning text-xs font-heading">
                    GRAD DAY
                  </div>
                )}
              </div>
            </div>
            <div className="col-span-6">
              <Quote />
            </div>

            {/* Middle Row - Habits */}
            <div className="col-span-12">
              <HabitList habits={habits} onUpdate={loadData} />
            </div>

            {/* Bottom Row */}
            <div className="col-span-7">
              <GoalProgress goals={goals} />
            </div>
            <div className="col-span-5">
              <WeeklyStats stats={weeklyStats} />
            </div>
          </div>
        </main>

        {/* Footer */}
        <footer className="flex-shrink-0 px-6 py-2 border-t border-cyan/10 text-center">
          <span className="text-xs text-text-dim font-heading tracking-wider">
            JARVIS DASHBOARD v1.0 | POWERED BY O4 STUDIO | AUTO-REFRESH: 60s
          </span>
        </footer>
      </div>
    </div>
  );
}

export default App;
