"use client";

import { useSyncExternalStore } from "react";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "./theme-provider";

type ThemeToggleProps = {
  className?: string;
};

function useIsHydrated() {
  return useSyncExternalStore(
    (listener) => {
      if (typeof window !== "undefined") {
        listener();
      }
      return () => {};
    },
    () => true,
    () => false,
  );
}

export function ThemeToggle({ className = "" }: ThemeToggleProps) {
  const { theme, toggleTheme } = useTheme();
  const hydrated = useIsHydrated();

  const renderIcon = () => {
    if (!hydrated) {
      return (
        <span className="block w-5 h-5 rounded-full bg-gray-300 dark:bg-gray-600 animate-pulse" />
      );
    }

    return theme === "light" ? (
      <Moon className="w-5 h-5 text-gray-700 dark:text-gray-300" />
    ) : (
      <Sun className="w-5 h-5 text-yellow-500" />
    );
  };

  return (
    <button
      onClick={toggleTheme}
      className={`p-3 rounded-full bg-white dark:bg-gray-800 shadow-lg border border-gray-200 dark:border-gray-700 hover:shadow-xl transition-all duration-200 hover:scale-110 ${className}`.trim()}
      aria-label="Toggle dark mode"
    >
      {renderIcon()}
    </button>
  );
}
