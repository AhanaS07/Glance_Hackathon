/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Dark theme palette used across the dashboard
        base: '#0f0f0f',
        card: '#1a1a1a',
      },
    },
  },
  plugins: [],
}
