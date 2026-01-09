"use client";

import React, { useState, useCallback, useEffect, useRef } from "react";
import { cn } from "@/lib/utils";

/**
 * Props for the SearchInput component
 */
interface SearchInputProps {
  /** Current search value */
  value: string;
  /** Callback when search value changes (debounced) */
  onChange: (value: string) => void;
  /** Debounce delay in milliseconds */
  debounceMs?: number;
  /** Placeholder text */
  placeholder?: string;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Search icon SVG component
 */
function SearchIcon({ className }: { className?: string }): React.ReactElement {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn("w-4 h-4", className)}
    >
      <circle cx="11" cy="11" r="8" />
      <path d="m21 21-4.3-4.3" />
    </svg>
  );
}

/**
 * Clear/X icon SVG component
 */
function ClearIcon({ className }: { className?: string }): React.ReactElement {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn("w-4 h-4", className)}
    >
      <path d="M18 6 6 18" />
      <path d="m6 6 12 12" />
    </svg>
  );
}

/**
 * SearchInput Component
 * Debounced search input with clear button for filtering stocks by ticker or company name
 */
export function SearchInput({
  value,
  onChange,
  debounceMs = 300,
  placeholder = "Search ticker or company...",
  className,
}: SearchInputProps): React.ReactElement {
  const [localValue, setLocalValue] = useState(value);
  const inputRef = useRef<HTMLInputElement>(null);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Sync local value with external value changes
   */
  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  /**
   * Handle input change with debouncing
   */
  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value;
      setLocalValue(newValue);

      // Clear existing timer
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }

      // Set new debounce timer
      debounceTimerRef.current = setTimeout(() => {
        onChange(newValue);
      }, debounceMs);
    },
    [onChange, debounceMs]
  );

  /**
   * Handle clear button click
   */
  const handleClear = useCallback(() => {
    setLocalValue("");
    onChange("");
    inputRef.current?.focus();
  }, [onChange]);

  /**
   * Handle keyboard shortcuts
   */
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      // Escape to clear
      if (e.key === "Escape") {
        handleClear();
      }
      // Enter to submit immediately (cancel debounce)
      if (e.key === "Enter") {
        if (debounceTimerRef.current) {
          clearTimeout(debounceTimerRef.current);
        }
        onChange(localValue);
      }
    },
    [handleClear, onChange, localValue]
  );

  /**
   * Cleanup debounce timer on unmount
   */
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  return (
    <div className={cn("relative", className)}>
      {/* Search Icon */}
      <div className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none">
        <SearchIcon className="text-foreground-muted" />
      </div>

      {/* Input Field */}
      <input
        ref={inputRef}
        type="text"
        value={localValue}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className={cn(
          "w-full h-10 pl-10 pr-10 text-sm bg-background-secondary border border-border rounded-lg",
          "focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/50",
          "placeholder:text-foreground-muted/50",
          "transition-colors"
        )}
        aria-label="Search stocks"
        autoComplete="off"
        autoCorrect="off"
        autoCapitalize="off"
        spellCheck="false"
      />

      {/* Clear Button */}
      {localValue && (
        <button
          onClick={handleClear}
          className={cn(
            "absolute right-2 top-1/2 -translate-y-1/2",
            "p-1 rounded-md",
            "text-foreground-muted hover:text-foreground",
            "hover:bg-background-tertiary",
            "transition-colors",
            "focus:outline-none focus:ring-1 focus:ring-accent"
          )}
          aria-label="Clear search"
          type="button"
        >
          <ClearIcon />
        </button>
      )}

      {/* Keyboard shortcut hint */}
      {!localValue && (
        <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none hidden sm:flex items-center gap-1">
          <kbd className="px-1.5 py-0.5 text-[10px] font-mono bg-background-tertiary border border-border rounded text-foreground-muted">
            /
          </kbd>
        </div>
      )}
    </div>
  );
}

/**
 * Custom hook for global search shortcut (/ key)
 */
export function useSearchShortcut(
  inputRef: React.RefObject<HTMLInputElement | null>
): void {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Check if user is typing in another input
      const activeElement = document.activeElement;
      const isInputActive =
        activeElement instanceof HTMLInputElement ||
        activeElement instanceof HTMLTextAreaElement ||
        activeElement instanceof HTMLSelectElement;

      if (e.key === "/" && !isInputActive) {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [inputRef]);
}

export default SearchInput;
