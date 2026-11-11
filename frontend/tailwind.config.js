/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        asphalt: {
          DEFAULT: "#14171c",
          soft: "#1f242c",
          mute: "#5c6673",
        },
        chalk: {
          DEFAULT: "#f3f4f6",
          warm: "#eceef1",
        },
        signal: {
          DEFAULT: "#e09a16",
          deep: "#b8790c",
          soft: "#fff4db",
        },
        steel: {
          DEFAULT: "#2f4a63",
          soft: "#e8eef4",
        },
        ok: "#1f7a4d",
        bad: "#c0392b",
      },
      fontFamily: {
        display: ['"Syne"', "sans-serif"],
        sans: ['"Manrope"', "sans-serif"],
      },
      keyframes: {
        rise: {
          from: { opacity: "0", transform: "translateY(10px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        fade: {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
      },
      animation: {
        rise: "rise 0.45s ease-out both",
        fade: "fade 0.35s ease-out both",
      },
    },
  },
  plugins: [],
};
