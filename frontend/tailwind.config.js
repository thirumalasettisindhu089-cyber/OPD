/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        hospital: {
          dark: '#0a0f1d',
          surface: '#131c31',
          card: '#18233d',
          cardHover: '#1f2d4e',
          input: '#0e1628',
          border: 'rgba(255, 255, 255, 0.1)',
        },
        triage: {
          1: '#ef4444', // Resuscitation Red
          2: '#f97316', // Emergent Orange
          3: '#eab308', // Urgent Yellow
          4: '#10b981', // Less Urgent Green
          5: '#3b82f6', // Non-urgent Blue
          abstain: '#a855f7', // Abstain Purple
        }
      },
      animation: {
        'pulse-fast': 'pulse 1.2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
}
