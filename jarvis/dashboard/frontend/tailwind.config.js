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
          DEFAULT: '#04001a',
          dark: '#02000d',
          card: 'rgba(7, 0, 184, 0.1)',
        },
        primary: {
          DEFAULT: '#0700b8',
          glow: '#4d4dff',
          dim: '#050080',
        },
        accent: {
          DEFAULT: '#00ff88',
          bright: '#5cffb1',
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
        body: ['Manrope', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'glow-primary': '0 0 20px rgba(7, 0, 184, 0.5)',
        'glow-primary-lg': '0 0 40px rgba(7, 0, 184, 0.7)',
        'glow-accent': '0 0 20px rgba(0, 255, 136, 0.3)',
        'glow-fire': '0 0 15px rgba(255, 107, 53, 0.5)',
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'slide-up': 'slide-up 0.3s ease-out',
        'fire': 'fire 1s ease-in-out infinite',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { boxShadow: '0 0 20px rgba(7, 0, 184, 0.4)' },
          '50%': { boxShadow: '0 0 40px rgba(7, 0, 184, 0.8)' },
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
        'grid': 'linear-gradient(rgba(7, 0, 184, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(7, 0, 184, 0.05) 1px, transparent 1px)',
      },
    },
  },
  plugins: [],
}
