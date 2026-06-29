import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export type ColorType = 'percentage' | 'confidence' | 'timeRemaining' | 'slaBreach' | 'daysAgo' | 'resolutionRate';

export function getColor(value: number, type: ColorType): string {
  switch (type) {
    case 'percentage':
    case 'confidence':
      if (value >= 70) return '#4A7A4A';
      if (value >= 40) return '#B87A00';
      return '#C41E1E';
    case 'timeRemaining':
      if (value >= 50) return '#4A7A4A';
      if (value >= 25) return '#B87A00';
      return '#C41E1E';
    case 'slaBreach':
      if (value === 0) return '#1A1A1A';
      if (value <= 5) return '#B87A00';
      return '#C41E1E';
    case 'daysAgo':
      if (value < 2) return '#1A1A1A';
      if (value <= 7) return '#B87A00';
      return '#C41E1E';
    case 'resolutionRate':
      if (value >= 80) return '#4A7A4A';
      if (value >= 60) return '#B87A00';
      return '#C41E1E';
    default:
      return '#1A1A1A';
  }
}

export const CATEGORY_COLORS: Record<string, string> = {
  roads: '#C24B2A',
  water: '#0D6B6E',
  garbage: '#6B7A2A',
};

export const STATE_BADGE_STYLES: Record<string, { bg: string; text: string; border?: string }> = {
  'reported': { bg: '#1A2B5F', text: '#FFFFFF' },
  'acknowledged': { bg: '#6B6B6B', text: '#FFFFFF' },
  'visited': { bg: '#9B9B9B', text: '#FFFFFF' },
  'in_progress': { bg: '#0D6B6E', text: '#FFFFFF' },
  'resolved_claimed': { bg: '#B87A00', text: '#FFFFFF' },
  'resolved_confirmed': { bg: '#4A7A4A', text: '#FFFFFF' },
  'resolution_unverified': { bg: '#6B6B6B', text: '#FFFFFF', border: '2px dashed #B87A00' },
  'disputed': { bg: '#C41E1E', text: '#FFFFFF' },
  'reopened': { bg: '#C41E1E', text: '#FFFFFF' },
  'closed': { bg: '#1A1A1A', text: '#FFFFFF' },
};

export const PRIORITY_STYLES: Record<string, { color: string; weight: number }> = {
  'critical': { color: '#C41E1E', weight: 900 },
  'high': { color: '#C41E1E', weight: 700 },
  'medium': { color: '#B87A00', weight: 600 },
  'low': { color: '#4A7A4A', weight: 500 },
};

export const ACTOR_BADGES: Record<string, { bg: string; text: string; label: string }> = {
  'citizen': { bg: '#0D6B6E', text: '#FFFFFF', label: 'CITIZEN' },
  'authority': { bg: '#1A2B5F', text: '#FFFFFF', label: 'MUNICIPAL CORP' },
  'system': { bg: '#C41E1E', text: '#FFFFFF', label: 'SYSTEM' },
};

export function formatDate(date: string | Date): string {
  const d = new Date(date);
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase();
}

export function formatTime(date: string | Date): string {
  const d = new Date(date);
  return d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false });
}

export function formatDateTime(date: string | Date): string {
  return `${formatDate(date)}, ${formatTime(date)}`;
}

export function daysAgo(date: string | Date): number {
  const d = new Date(date);
  const now = new Date();
  return Math.floor((now.getTime() - d.getTime()) / (1000 * 60 * 60 * 24));
}

export function formatDaysAgo(date: string | Date): string {
  const days = daysAgo(date);
  if (days === 0) return 'TODAY';
  if (days === 1) return '1 DAY AGO';
  return `${days} DAYS AGO`;
}