import type { Config } from 'tailwindcss'

export default {
  content: [
    "./components/**/*.{js,vue,ts}",
    "./layouts/**/*.vue",
    "./pages/**/*.vue",
    "./app.vue",
  ],
  theme: {
    extend: {
      fontFamily: {
        arabic: ['Amiri', 'Traditional Arabic', 'serif'],
      },
    },
  },
  plugins: [],
} satisfies Config
