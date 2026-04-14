const API_BASE = '/api';

async function fetchJSON(endpoint, options = {}) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  });
  
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }
  
  return response.json();
}

export const api = {
  async getProfile() {
    return fetchJSON('/profile');
  },
  
  async getHabits() {
    const data = await fetchJSON('/habits');
    return data.habits;
  },
  
  async logHabit(habitId, { pages, duration } = {}) {
    const params = new URLSearchParams();
    if (pages !== undefined) params.append('pages', pages);
    if (duration !== undefined) params.append('duration', duration);
    
    return fetchJSON(`/habits/${habitId}/log?${params}`, {
      method: 'POST',
    });
  },
  
  async unlogHabit(habitId) {
    return fetchJSON(`/habits/${habitId}/log`, {
      method: 'DELETE',
    });
  },
  
  async getGoals() {
    const data = await fetchJSON('/goals');
    return data.goals;
  },
  
  async updateGoalProgress(goalId, progress) {
    return fetchJSON(`/goals/${goalId}/progress?progress=${progress}`, {
      method: 'PUT',
    });
  },
  
  async getWeeklyStats() {
    return fetchJSON('/reviews/weekly');
  },
  
  async getQuote() {
    return fetchJSON('/quotes');
  },
};

export default api;
