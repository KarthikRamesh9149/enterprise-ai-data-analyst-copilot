import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#111827",
        muted: "#5b6472",
        line: "#d8dee8",
        teal: "#0f766e",
        amber: "#b45309",
      },
    },
  },
  plugins: [],
};

export default config;
