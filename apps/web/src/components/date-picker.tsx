"use client";

import { useState, useRef, useEffect } from "react";
import { ChevronLeft, ChevronRight, Calendar } from "./icons";

interface DatePickerProps {
  label?: string;
  value: Date | null;
  onChange: (date: Date | null) => void;
  placeholder?: string;
  className?: string;
  error?: string;
  helperText?: string;
}

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"
];

const WEEKDAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

export function DatePicker({
  label,
  value,
  onChange,
  placeholder = "Select date",
  className = "",
  error,
  helperText,
}: DatePickerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [currentMonth, setCurrentMonth] = useState(
    value ? value.getMonth() : new Date().getMonth()
  );
  const [currentYear, setCurrentYear] = useState(
    value ? value.getFullYear() : new Date().getFullYear()
  );
  const [focusedDate, setFocusedDate] = useState<number | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Handle click outside to close
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [isOpen]);

  // Format date for display
  const formatDate = (date: Date | null): string => {
    if (!date) return "";
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const year = date.getFullYear();
    return `${month}/${day}/${year}`;
  };

  // Get days in month
  const getDaysInMonth = (month: number, year: number): number => {
    return new Date(year, month + 1, 0).getDate();
  };

  // Get first day of month (0 = Sunday)
  const getFirstDayOfMonth = (month: number, year: number): number => {
    return new Date(year, month, 1).getDay();
  };

  // Generate calendar days
  const generateCalendarDays = (): (number | null)[] => {
    const daysInMonth = getDaysInMonth(currentMonth, currentYear);
    const firstDay = getFirstDayOfMonth(currentMonth, currentYear);
    const days: (number | null)[] = [];

    // Add empty cells for days before month starts
    for (let i = 0; i < firstDay; i++) {
      days.push(null);
    }

    // Add days of month
    for (let i = 1; i <= daysInMonth; i++) {
      days.push(i);
    }

    return days;
  };

  // Check if date is today
  const isToday = (day: number): boolean => {
    const today = new Date();
    return (
      day === today.getDate() &&
      currentMonth === today.getMonth() &&
      currentYear === today.getFullYear()
    );
  };

  // Check if date is selected
  const isSelected = (day: number): boolean => {
    if (!value) return false;
    return (
      day === value.getDate() &&
      currentMonth === value.getMonth() &&
      currentYear === value.getFullYear()
    );
  };

  // Handle date selection
  const handleDateSelect = (day: number) => {
    const newDate = new Date(currentYear, currentMonth, day);
    onChange(newDate);
    setIsOpen(false);
  };

  // Navigate months
  const goToPreviousMonth = () => {
    if (currentMonth === 0) {
      setCurrentMonth(11);
      setCurrentYear(currentYear - 1);
    } else {
      setCurrentMonth(currentMonth - 1);
    }
  };

  const goToNextMonth = () => {
    if (currentMonth === 11) {
      setCurrentMonth(0);
      setCurrentYear(currentYear + 1);
    } else {
      setCurrentMonth(currentMonth + 1);
    }
  };

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        setIsOpen(true);
      }
      return;
    }

    const days = generateCalendarDays().filter((d) => d !== null) as number[];
    const currentFocus = focusedDate ?? (value?.getDate() ?? 1);
    let newFocus = currentFocus;

    switch (e.key) {
      case "ArrowLeft":
        e.preventDefault();
        newFocus = Math.max(1, currentFocus - 1);
        break;
      case "ArrowRight":
        e.preventDefault();
        newFocus = Math.min(days.length, currentFocus + 1);
        break;
      case "ArrowUp":
        e.preventDefault();
        newFocus = Math.max(1, currentFocus - 7);
        break;
      case "ArrowDown":
        e.preventDefault();
        newFocus = Math.min(days.length, currentFocus + 7);
        break;
      case "Enter":
      case " ":
        e.preventDefault();
        handleDateSelect(currentFocus);
        break;
      case "Escape":
        e.preventDefault();
        setIsOpen(false);
        inputRef.current?.focus();
        break;
    }

    setFocusedDate(newFocus);
  };

  const calendarDays = generateCalendarDays();

  return (
    <div ref={containerRef} className={`relative w-full ${className}`}>
      {label && (
        <label className="mb-1.5 block text-sm font-medium text-text-secondary">
          {label}
        </label>
      )}

      {/* Input Field */}
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          readOnly
          value={formatDate(value)}
          onClick={() => setIsOpen(!isOpen)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className={`w-full min-h-[48px] rounded-lg border px-4 py-2.5 pr-11 text-base text-text-primary bg-surface transition-all placeholder:text-text-tertiary focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-1 cursor-pointer ${
            error
              ? "border-danger focus:ring-danger"
              : "border-border-strong hover:border-border-strong/80"
          }`}
          aria-label={label}
          aria-expanded={isOpen}
          aria-haspopup="dialog"
        />
        <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
          <Calendar className="h-5 w-5 text-text-tertiary" />
        </div>
      </div>

      {/* Calendar Dropdown */}
      {isOpen && (
        <div
          className="absolute left-0 right-0 z-[var(--z-dropdown)] mt-2 rounded-xl border border-border bg-surface shadow-lg animate-slide-down"
          role="dialog"
          aria-label="Calendar"
          style={{
            boxShadow: "var(--shadow-lg)",
          }}
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-border px-4 py-3">
            <button
              type="button"
              onClick={goToPreviousMonth}
              className="rounded-lg p-2 text-text-secondary transition-colors hover:bg-surface-alt hover:text-text-primary focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-1"
              aria-label="Previous month"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>

            <div className="font-[var(--font-display)] text-base font-medium text-text-primary">
              {MONTHS[currentMonth]} {currentYear}
            </div>

            <button
              type="button"
              onClick={goToNextMonth}
              className="rounded-lg p-2 text-text-secondary transition-colors hover:bg-surface-alt hover:text-text-primary focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-1"
              aria-label="Next month"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </div>

          {/* Calendar Grid */}
          <div className="p-4">
            {/* Weekday Headers */}
            <div className="mb-2 grid grid-cols-7 gap-1">
              {WEEKDAYS.map((day) => (
                <div
                  key={day}
                  className="text-center text-xs font-medium text-text-tertiary"
                >
                  {day}
                </div>
              ))}
            </div>

            {/* Days Grid */}
            <div className="grid grid-cols-7 gap-1">
              {calendarDays.map((day, index) => {
                if (day === null) {
                  return <div key={`empty-${index}`} className="aspect-square" />;
                }

                const selected = isSelected(day);
                const today = isToday(day);
                const focused = focusedDate === day;

                return (
                  <button
                    key={day}
                    type="button"
                    onClick={() => handleDateSelect(day)}
                    className={`
                      aspect-square rounded-lg text-sm font-medium transition-all duration-200
                      focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-1
                      ${
                        selected
                          ? "bg-primary-600 text-white shadow-sm hover:bg-primary-700"
                          : today
                          ? "border-2 border-primary-600 text-primary-700 hover:bg-primary-50"
                          : "text-text-primary hover:bg-surface-alt"
                      }
                      ${focused && !selected ? "ring-2 ring-primary-500 ring-offset-1" : ""}
                    `}
                    aria-label={`${MONTHS[currentMonth]} ${day}, ${currentYear}`}
                    aria-selected={selected}
                  >
                    {day}
                  </button>
                );
              })}
            </div>

            {/* Footer - Today button */}
            <div className="mt-4 flex justify-center border-t border-border pt-3">
              <button
                type="button"
                onClick={() => {
                  const today = new Date();
                  setCurrentMonth(today.getMonth());
                  setCurrentYear(today.getFullYear());
                  handleDateSelect(today.getDate());
                }}
                className="rounded-lg px-4 py-2 text-sm font-medium text-primary-600 transition-colors hover:bg-primary-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-1"
              >
                Today
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Helper Text / Error */}
      {error && <p className="mt-1.5 text-sm text-danger">{error}</p>}
      {helperText && !error && (
        <p className="mt-1.5 text-sm text-text-tertiary">{helperText}</p>
      )}
    </div>
  );
}
