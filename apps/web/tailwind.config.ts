import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        apex: {
          red: "#E10600",
          dark: "#0D0E12",
          card: "#15171E",
          border: "#272A35",
          muted: "#8F96A3",
          text: "#F5F6F8",
        },
      },
    },
  },
  plugins: [],
};
export default config;
