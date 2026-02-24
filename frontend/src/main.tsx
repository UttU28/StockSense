import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";

// Initialize theme from localStorage or system preference
const storedTheme = (localStorage.getItem("theme") as "light" | "dark" | null) ?? null;
const prefersDark = window.matchMedia &&
  window.matchMedia("(prefers-color-scheme: dark)").matches;
const initialTheme: "light" | "dark" =
  storedTheme ?? (prefersDark ? "dark" : "light");

document.documentElement.setAttribute("data-theme", initialTheme);

createRoot(document.getElementById("root")!).render(<App />);
