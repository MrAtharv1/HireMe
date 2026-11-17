/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          dark: '#0f172a',    // Deep slate background
          card: '#1e293b',    // Slightly lighter for glassmorphism cards
          accent: '#3b82f6',  // Electric blue for primary buttons
          success: '#10b981', // Emerald green for high match scores
        }
      }
    },
  },
  plugins: [],
}