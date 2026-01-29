import { format, formatDistanceToNow, parseISO } from "date-fns";

/**
 * Format a date string for display.
 *
 * @param dateString - ISO date string
 * @param formatStr - Format string (default: "MMM d, yyyy")
 * @returns Formatted date string
 */
export function formatDate(dateString: string, formatStr: string = "MMM d, yyyy"): string {
  if (!dateString) return "N/A";
  try {
    const date = parseISO(dateString);
    if (isNaN(date.getTime())) return "N/A";
    return format(date, formatStr);
  } catch {
    return "N/A";
  }
}

/**
 * Format a date string as relative time.
 *
 * @param dateString - ISO date string
 * @returns Relative time string (e.g., "2 hours ago")
 */
export function formatRelativeTime(dateString: string): string {
  if (!dateString) return "Unknown";
  try {
    const date = parseISO(dateString);
    if (isNaN(date.getTime())) return "Unknown";
    return formatDistanceToNow(date, { addSuffix: true });
  } catch {
    return "Unknown";
  }
}

/**
 * Format a number with commas.
 *
 * @param num - Number to format
 * @returns Formatted number string
 */
export function formatNumber(num: number): string {
  return num.toLocaleString();
}

/**
 * Format a percentage value.
 *
 * @param value - Decimal value (0-1)
 * @param decimals - Number of decimal places (default: 0)
 * @returns Formatted percentage string
 */
export function formatPercentage(value: number, decimals: number = 0): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Truncate a string to a maximum length.
 *
 * @param str - String to truncate
 * @param maxLength - Maximum length (default: 50)
 * @returns Truncated string with ellipsis if needed
 */
export function truncate(str: string, maxLength: number = 50): string {
  if (str.length <= maxLength) return str;
  return `${str.slice(0, maxLength - 3)}...`;
}

/**
 * Format a UUID for display (first 8 characters).
 *
 * @param uuid - Full UUID string
 * @returns Shortened UUID
 */
export function formatShortUuid(uuid: string): string {
  return uuid.slice(0, 8);
}
