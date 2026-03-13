/**
 * Utility functions
 */

import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(value: number | undefined | null, decimals: number = 1): string {
  if (value === undefined || value === null) return "N/A";
  return value.toFixed(decimals);
}

export function formatPercentage(value: number | undefined | null): string {
  if (value === undefined || value === null) return "N/A";
  return `${value.toFixed(1)}%`;
}

export function formatStat(value: number | undefined | null, isPercentage: boolean = false): string {
  if (value === undefined || value === null) return "0";
  return isPercentage ? formatPercentage(value) : formatNumber(value);
}

export function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function truncate(text: string, maxLength: number = 100): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + "...";
}

export function formatDate(dateString: string): string {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return dateString;
  }
}
