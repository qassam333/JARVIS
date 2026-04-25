import React from 'react';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell } from 'recharts';

export default function WeeklyStats({ stats }) {
  const CustomBar = (props) => {
    const { x, y, width, height, payload } = props;
    const percentage = payload.percentage || 0;
    const fillColor = percentage >= 70 ? '#00ff88' : percentage >= 40 ? '#00d4ff' : '#ff6b35';
    
    return (
      <g>
        <rect x={x} y={y} width={width} height={height} fill="#1a1a2e" rx={4} />
        <rect
          x={x}
          y={y + height - (height * percentage / 100)}
          width={width}
          height={height * percentage / 100}
          fill={fillColor}
          rx={4}
          style={{
            filter: `drop-shadow(0 0 8px ${fillColor})`,
          }}
        />
      </g>
    );
  };

  return (
    <div className="card h-full">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-heading text-lg text-primary tracking-wider">
          WEEKLY STATS
        </h2>
        <div className="text-right">
          <div className="font-mono text-2xl text-success">{stats.completion_rate}%</div>
          <div className="text-xs text-text-dim">completion</div>
        </div>
      </div>

      <div className="h-[200px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={stats.chart_data}
            margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
          >
            <XAxis
              dataKey="day"
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#6b7280', fontSize: 12, fontFamily: 'Rajdhani' }}
            />
            <YAxis
              domain={[0, 100]}
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#6b7280', fontSize: 10, fontFamily: 'JetBrains Mono' }}
              tickFormatter={(v) => `${v}%`}
            />
            <Bar dataKey="percentage" shape={<CustomBar />} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="flex justify-center gap-6 mt-4 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-success" />
          <span className="text-text-dim">70%+</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-primary" />
          <span className="text-text-dim">40-70%</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-warning" />
          <span className="text-text-dim">&lt;40%</span>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-primary/20">
        <div className="flex justify-between text-sm">
          <span className="text-text-dim">This week:</span>
          <span className="font-mono text-success">
            {stats.total_completed}/{stats.total_expected} habits
          </span>
        </div>
      </div>
    </div>
  );
}
