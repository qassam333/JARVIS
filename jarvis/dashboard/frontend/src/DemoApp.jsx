import React, { useState } from 'react';
import Countdown from './components/Countdown';
import HabitList from './components/HabitList';
import GoalProgress from './components/GoalProgress';
import WeeklyStats from './components/WeeklyStats';
import Quote from './components/Quote';

function DemoApp() {
  const [loading, setLoading] = useState(false);

  // Fake Data for LinkedIn Showcase
  const profile = {
    days_until_grad: 30,
    day_name: new Date().toLocaleDateString('en-US', { weekday: 'long' }),
    today: new Date().toISOString(),
    is_grad_day: false,
  };

  const habits = [
    { id: '1', name: 'Core Engine Development', current_streak: 45, best_streak: 50, completed_today: true, duration: 240, frequency: 'daily' },
    { id: '2', name: 'Read Tech Papers', current_streak: 12, best_streak: 15, completed_today: true, pages: 25, frequency: 'daily' },
    { id: '3', name: 'Daily Standup & Planning', current_streak: 108, best_streak: 120, completed_today: true, frequency: 'daily' },
    { id: '4', name: 'Morning Workout', current_streak: 5, best_streak: 30, completed_today: false, frequency: 'daily' }
  ];

  const goals = [
    {
      id: '1',
      title: 'Ship O4 Studio Alpha',
      description: 'First playable release of the game engine',
      progress: 85,
      status: 'active',
      priority: 'critical',
      area_color: '#0700b8',
      target_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
      milestones: [
        { id: '1', title: 'Physics Engine V2', progress: 100, completed: true },
        { id: '2', title: 'Multiplayer Netcode', progress: 100, completed: true },
        { id: '3', title: 'Final Polish & QA', progress: 20, completed: false }
      ]
    },
    {
      id: '2',
      title: 'Launch Marketing Campaign',
      description: 'Build hype for the alpha release',
      progress: 60,
      status: 'active',
      priority: 'high',
      area_color: '#00ff88',
      target_date: new Date(Date.now() + 15 * 24 * 60 * 60 * 1000).toISOString(),
      milestones: [
        { id: '4', title: 'Trailer Rendering', progress: 100, completed: true },
        { id: '5', title: 'Press Release Distribution', progress: 0, completed: false }
      ]
    }
  ];

  const weeklyStats = {
    completion_rate: 92,
    total_completed: 26,
    total_expected: 28,
    chart_data: [
      { day: "Mon", completed: 4, total: 4, percentage: 100 },
      { day: "Tue", completed: 4, total: 4, percentage: 100 },
      { day: "Wed", completed: 3, total: 4, percentage: 75 },
      { day: "Thu", completed: 4, total: 4, percentage: 100 },
      { day: "Fri", completed: 4, total: 4, percentage: 100 },
      { day: "Sat", completed: 3, total: 4, percentage: 75 },
      { day: "Sun", completed: 4, total: 4, percentage: 100 }
    ]
  };

  const handleRefresh = () => {
    setLoading(true);
    setTimeout(() => setLoading(false), 500); // Fake loading delay
  };

  return (
    <div className="h-screen w-screen overflow-hidden bg-background">
      <div className="h-full flex flex-col">
        {/* Header */}
        <header className="flex-shrink-0 px-6 py-4 border-b border-primary/20">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="font-heading text-2xl tracking-[0.2em] neon-text">
                JARVIS
              </h1>
              <span className="text-text-dim text-sm">|</span>
              <span className="font-heading text-sm tracking-wider text-accent-bright">
                O4 STUDIO DEMO
              </span>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="text-xs text-text-dim">
                Updated: {new Date().toLocaleTimeString()}
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
                daysLeft={profile.days_until_grad} 
                isGradDay={profile.is_grad_day}
              />
            </div>
            <div className="col-span-3">
              <div className="card h-full flex flex-col justify-center items-center">
                <h3 className="font-heading text-sm tracking-[0.3em] text-text-muted mb-2">
                  TODAY
                </h3>
                <div className="font-heading text-4xl text-primary">
                  {profile.day_name}
                </div>
                <div className="text-sm text-text-dim mt-2">
                  {new Date(profile.today).toLocaleDateString('en-US', { 
                    month: 'short', 
                    day: 'numeric' 
                  })}
                </div>
              </div>
            </div>
            <div className="col-span-6">
              <Quote />
            </div>

            {/* Middle Row - Habits */}
            <div className="col-span-12">
              <HabitList habits={habits} onUpdate={() => {}} />
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
        <footer className="flex-shrink-0 px-6 py-2 border-t border-primary/10 text-center">
          <span className="text-xs text-text-dim font-heading tracking-wider">
            JARVIS DASHBOARD v1.0 | POWERED BY O4 STUDIO | DEMO MODE
          </span>
        </footer>
      </div>
    </div>
  );
}

export default DemoApp;
