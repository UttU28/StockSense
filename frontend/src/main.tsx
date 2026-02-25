import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";

// Initialize theme from localStorage; default to light
const storedTheme = localStorage.getItem("theme") as "light" | "dark" | null;
const initialTheme: "light" | "dark" = storedTheme ?? "light";

document.documentElement.setAttribute("data-theme", initialTheme);

createRoot(document.getElementById("root")!).render(<App />);
