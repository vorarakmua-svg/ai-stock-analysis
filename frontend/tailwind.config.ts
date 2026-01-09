import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
    "./providers/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Bloomberg Terminal-inspired color palette
        background: {
          DEFAULT: "#0a0a0a",
          secondary: "#1a1a1a",
          tertiary: "#2a2a2a",
        },
        foreground: {
          DEFAULT: "#fafafa",
          muted: "#a1a1aa",
        },
        positive: {
          DEFAULT: "#22c55e",
          muted: "#166534",
        },
        negative: {
          DEFAULT: "#ef4444",
          muted: "#991b1b",
        },
        accent: {
          DEFAULT: "#3b82f6",
          hover: "#2563eb",
        },
        border: {
          DEFAULT: "#27272a",
          hover: "#3f3f46",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
