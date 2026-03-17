/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'cyber-black': '#0B0F0C',
        'cyber-dark': '#121A14',
        'cyber-darker': '#0D1410',
        'cyber-green': '#00FF9C',
        'cyber-green-light': '#00FFB3',
        'cyber-green-dark': '#00C97B',
        'cyber-green-darker': '#1DB954',
        'cyber-gray': '#1A2420',
        'cyber-gray-light': '#2A3630',
        'cyber-border': 'rgba(0, 255, 156, 0.15)',
        'cyber-border-hover': 'rgba(0, 255, 156, 0.3)',
      },
      backgroundImage: {
        'gradient-cyber': 'linear-gradient(135deg, #0B0F0C 0%, #121A14 100%)',
        'gradient-green': 'linear-gradient(135deg, #00FF9C 0%, #00C97B 100%)',
        'gradient-glow': 'radial-gradient(circle at center, rgba(0, 255, 156, 0.1) 0%, transparent 70%)',
      },
      boxShadow: {
        'cyber': '0 4px 20px rgba(0, 255, 156, 0.1)',
        'cyber-lg': '0 8px 30px rgba(0, 255, 156, 0.15)',
        'cyber-glow': '0 0 20px rgba(0, 255, 156, 0.2)',
        'cyber-glow-strong': '0 0 30px rgba(0, 255, 156, 0.3)',
        'inner-glow': 'inset 0 0 20px rgba(0, 255, 156, 0.05)',
      },
      animation: {
        'glow': 'glow 2s ease-in-out infinite alternate',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        glow: {
          'from': { boxShadow: '0 0 10px rgba(0, 255, 156, 0.2)' },
          'to': { boxShadow: '0 0 20px rgba(0, 255, 156, 0.4)' },
        }
      }
    },
  },
  plugins: [],
}
