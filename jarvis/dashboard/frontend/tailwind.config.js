/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: {
          DEFAULT: '#0a0a0f',
          dark: '#0f0f1a',
          card: 'rgba(26, 26, 46, 0.8)',
        },
        cyan: {
          DEFAULT: '#00d4ff',
          glow: '#00ffff',
          dim: '#0088ff',
        },
        purple: {
          DEFAULT: '#7b2cbf',
          bright: '#9d4edd',
        },
        success: '#00ff88',
        warning: '#ff6b35',
        danger: '#ff3366',
        text: {
          DEFAULT: '#ffffff',
          muted: '#b8c5d6',
          dim: '#6b7280',
        },
      },
      fontFamily: {
        heading: ['Orbitron', 'sans-serif'],
        body: ['Rajdhani', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'glow-cyan': '0 0 20px rgba(0, 212, 255, 0.3)',
        'glow-cyan-lg': '0 0 40px rgba(0, 212, 255, 0.5)',
        'glow-purple': '0 0 20px rgba(123, 44, 191, 0.3)',
        'glow-fire': '0 0 15px rgba(255, 107, 53, 0.5)',
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'slide-up': 'slide-up 0.3s ease-out',
        'fire': 'fire 1s ease-in-out infinite',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { boxShadow: '0 0 20px rgba(0, 212, 255, 0.3)' },
          '50%': { boxShadow: '0 0 40px rgba(0, 212, 255, 0.6)' },
        },
        'slide-up': {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        'fire': {
          '0%, 100%': { transform: 'scale(1)', filter: 'brightness(1)' },
          '50%': { transform: 'scale(1.1)', filter: 'brightness(1.2)' },
        },
      },
      backgroundImage: {
        'grid': 'linear-gradient(rgba(0, 212, 255, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 212, 255, 0.03) 1px, transparent 1px)',
      },
    },
  },
  plugins: [],
}
