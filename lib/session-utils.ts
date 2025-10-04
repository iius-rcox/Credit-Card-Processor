// Session Management Utilities
// Generated from specs/003-add-ui-components/data-model.md and research.md

import {
  MonthSession,
  SessionStorage,
  SessionFilter,
  SessionStatus,
  SESSION_CONSTRAINTS,
  DEFAULT_SESSION_STORAGE
} from './session-types';

/**
 * Generate a UUID v4 for session IDs
 */
export function generateSessionId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

/**
 * Validate session name according to constraints
 */
export function validateSessionName(name: string): { isValid: boolean; error?: string } {
  const trimmed = name.trim();

  if (trimmed.length === 0) {
    return { isValid: false, error: 'Session name cannot be empty' };
  }

  if (trimmed.length < SESSION_CONSTRAINTS.MIN_NAME_LENGTH) {
    return { isValid: false, error: `Session name must be at least ${SESSION_CONSTRAINTS.MIN_NAME_LENGTH} character` };
  }

  if (trimmed.length > SESSION_CONSTRAINTS.MAX_NAME_LENGTH) {
    return { isValid: false, error: `Session name must be no more than ${SESSION_CONSTRAINTS.MAX_NAME_LENGTH} characters` };
  }

  return { isValid: true };
}

/**
 * Validate file for receipt upload
 */
export function validateReceiptFile(file: File): { isValid: boolean; error?: string } {
  // Check file type (PDF only)
  if (file.type !== 'application/pdf') {
    return { isValid: false, error: 'Only PDF files are allowed for receipt uploads' };
  }

  // Check file size (50MB limit)
  if (file.size > SESSION_CONSTRAINTS.MAX_FILE_SIZE) {
    const maxSizeMB = SESSION_CONSTRAINTS.MAX_FILE_SIZE / (1024 * 1024);
    return { isValid: false, error: `File size must be less than ${maxSizeMB}MB` };
  }

  return { isValid: true };
}

/**
 * Create a new MonthSession with default values
 */
export function createSession(name: string, backendSessionId: string): MonthSession {
  const now = Date.now();

  return {
    id: generateSessionId(),
    name: name.trim(),
    createdAt: now,
    expiresAt: now + SESSION_CONSTRAINTS.EXPIRATION_PERIOD,
    status: 'Processing' as SessionStatus,
    backendSessionId,
    lastUpdated: now,
    hasReports: false,
    fileCount: 0,
    matchCount: 0,
  };
}

/**
 * Check if a session has expired
 */
export function isSessionExpired(session: MonthSession): boolean {
  return Date.now() > session.expiresAt;
}

/**
 * Get sessions that have expired
 */
export function getExpiredSessions(storage: SessionStorage): MonthSession[] {
  return Object.values(storage.sessions).filter(isSessionExpired);
}

/**
 * Remove expired sessions from storage
 */
export function cleanupExpiredSessions(storage: SessionStorage): SessionStorage {
  const now = Date.now();
  const cleanedSessions: Record<string, MonthSession> = {};
  let activeSessionId = storage.activeSessionId;

  // Keep only non-expired sessions
  Object.values(storage.sessions).forEach(session => {
    if (!isSessionExpired(session)) {
      cleanedSessions[session.id] = session;
    } else if (session.id === activeSessionId) {
      // Clear active session if it's expired
      activeSessionId = null;
    }
  });

  return {
    ...storage,
    sessions: cleanedSessions,
    activeSessionId,
    lastCleanup: now,
  };
}

/**
 * Check if we're approaching the session limit
 */
export function isApproachingSessionLimit(storage: SessionStorage): boolean {
  const sessionCount = Object.keys(storage.sessions).length;
  return sessionCount >= SESSION_CONSTRAINTS.MAX_SESSIONS - 2; // Warning at 22+ sessions
}

/**
 * Check if we're at the session limit
 */
export function isAtSessionLimit(storage: SessionStorage): boolean {
  const sessionCount = Object.keys(storage.sessions).length;
  return sessionCount >= SESSION_CONSTRAINTS.MAX_SESSIONS;
}

/**
 * Filter sessions based on filter criteria
 */
export function filterSessions(sessions: MonthSession[], filter: SessionFilter): MonthSession[] {
  let filtered = Object.values(sessions);

  // Apply search term filter
  if (filter.searchTerm.trim()) {
    const searchLower = filter.searchTerm.toLowerCase().trim();
    filtered = filtered.filter(session =>
      session.name.toLowerCase().includes(searchLower)
    );
  }

  // Apply status filter
  if (filter.statusFilter !== 'all') {
    filtered = filtered.filter(session =>
      filter.statusFilter.includes(session.status)
    );
  }

  // Apply date range filter
  if (filter.dateRange.start) {
    const startTime = filter.dateRange.start.getTime();
    filtered = filtered.filter(session => session.createdAt >= startTime);
  }

  if (filter.dateRange.end) {
    const endTime = filter.dateRange.end.getTime();
    filtered = filtered.filter(session => session.createdAt <= endTime);
  }

  // Apply sorting
  filtered.sort((a, b) => {
    let aValue: number | string;
    let bValue: number | string;

    switch (filter.sortBy) {
      case 'name':
        aValue = a.name.toLowerCase();
        bValue = b.name.toLowerCase();
        break;
      case 'createdAt':
        aValue = a.createdAt;
        bValue = b.createdAt;
        break;
      case 'lastUpdated':
        aValue = a.lastUpdated;
        bValue = b.lastUpdated;
        break;
      default:
        aValue = a.lastUpdated;
        bValue = b.lastUpdated;
    }

    if (typeof aValue === 'string' && typeof bValue === 'string') {
      const comparison = aValue.localeCompare(bValue);
      return filter.sortOrder === 'asc' ? comparison : -comparison;
    }

    if (typeof aValue === 'number' && typeof bValue === 'number') {
      const comparison = aValue - bValue;
      return filter.sortOrder === 'asc' ? comparison : -comparison;
    }

    return 0;
  });

  return filtered;
}

/**
 * Format date for display
 */
export function formatSessionDate(timestamp: number): string {
  return new Date(timestamp).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

/**
 * Format session status for display
 */
export function formatSessionStatus(status: SessionStatus): string {
  switch (status) {
    case 'Processing':
      return 'Processing';
    case 'Complete':
      return 'Complete';
    case 'Updated':
      return 'Updated';
    case 'Error':
      return 'Error';
    default:
      return 'Unknown';
  }
}

/**
 * Get status color for UI theming
 */
export function getSessionStatusColor(status: SessionStatus): string {
  switch (status) {
    case 'Processing':
      return 'blue';
    case 'Complete':
      return 'green';
    case 'Updated':
      return 'amber';
    case 'Error':
      return 'red';
    default:
      return 'gray';
  }
}

/**
 * Calculate time until session expires
 */
export function getTimeUntilExpiration(session: MonthSession): {
  expired: boolean;
  days: number;
  hours: number;
} {
  const now = Date.now();
  const timeLeft = session.expiresAt - now;

  if (timeLeft <= 0) {
    return { expired: true, days: 0, hours: 0 };
  }

  const days = Math.floor(timeLeft / (24 * 60 * 60 * 1000));
  const hours = Math.floor((timeLeft % (24 * 60 * 60 * 1000)) / (60 * 60 * 1000));

  return { expired: false, days, hours };
}

/**
 * Check if session name is unique within storage
 */
export function isSessionNameUnique(storage: SessionStorage, name: string, excludeId?: string): boolean {
  const trimmedName = name.trim().toLowerCase();
  return !Object.values(storage.sessions).some(session =>
    session.id !== excludeId && session.name.toLowerCase() === trimmedName
  );
}

/**
 * Load session storage from localStorage with error handling
 */
export function loadSessionStorage(): SessionStorage {
  try {
    // Check if localStorage is available (client-side only)
    if (typeof window === 'undefined' || typeof localStorage === 'undefined') {
      return DEFAULT_SESSION_STORAGE;
    }

    const stored = localStorage.getItem(SESSION_CONSTRAINTS.STORAGE_KEY);
    if (!stored) {
      return DEFAULT_SESSION_STORAGE;
    }

    const parsed = JSON.parse(stored) as SessionStorage;

    // Validate schema version and migrate if needed
    if (parsed.version !== SESSION_CONSTRAINTS.SCHEMA_VERSION) {
      // Migration logic would go here for future versions
      return DEFAULT_SESSION_STORAGE;
    }

    // Cleanup expired sessions on load
    return cleanupExpiredSessions(parsed);
  } catch (error) {
    console.error('Failed to load session storage:', error);
    return DEFAULT_SESSION_STORAGE;
  }
}

/**
 * Save session storage to localStorage with error handling
 */
export function saveSessionStorage(storage: SessionStorage): boolean {
  try {
    // Check if localStorage is available (client-side only)
    if (typeof window === 'undefined' || typeof localStorage === 'undefined') {
      return false;
    }

    const serialized = JSON.stringify(storage);
    localStorage.setItem(SESSION_CONSTRAINTS.STORAGE_KEY, serialized);
    return true;
  } catch (error) {
    console.error('Failed to save session storage:', error);
    return false;
  }
}