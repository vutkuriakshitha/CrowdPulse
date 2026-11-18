/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f2a3d",
        soft: "#dff0f6",
        panel: "#f7fcff",
        line: "#9ec4d8",
        mist: "#4a6678",
        canvas: "#c8e8f0",
        signal: {
          green: "#12a454",
          yellow: "#e0a100",
          orange: "#f06a12",
          red: "#e11d2e",
        },
        accent: "#0b7fd4",
        teal: "#00a896",
        amber: "#f5a524",
        coral: "#ff6b4a",
        sky: "#38bdf8",
      },
      fontFamily: {
        sans: ["IBM Plex Sans", "Segoe UI", "sans-serif"],
        mono: ["IBM Plex Mono", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
};
