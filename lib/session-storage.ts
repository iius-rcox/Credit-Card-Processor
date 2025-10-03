/**
 * Session storage utilities for browser localStorage.
 *
 * Manages session persistence with 24-hour TTL (Time To Live).
 */

const SESSION_KEY = "expense_session";
const SESSION_TTL = 24 * 60 * 60 * 1000; // 24 hours in milliseconds

export interface SessionData {
  sessionId: string;
  createdAt: number;
  expiresAt: number;
}

/**
 * Save session ID to localStorage with 24-hour expiration.
 *
 * @param sessionId - UUID string from backend
 *
 * @example
 * ```ts
 * saveSession("550e8400-e29b-41d4-a716-446655440000");
 * ```
 */
export function saveSession(sessionId: string): void {
  const now = Date.now();

  const sessionData: SessionData = {
    sessionId,
    createdAt: now,
    expiresAt: now + SESSION_TTL,
  };

  localStorage.setItem(SESSION_KEY, JSON.stringify(sessionData));
}

/**
 * Retrieve session ID from localStorage.
 *
 * Automatically clears expired sessions (> 24 hours old).
 *
 * @returns Session ID string if valid session exists, null otherwise
 *
 * @example
 * ```ts
 * const sessionId = getSession();
 * if (sessionId) {
 *   console.log("Resuming session:", sessionId);
 * } else {
 *   console.log("No active session");
 * }
 * ```
 */
export function getSession(): string | null {
  try {
    const stored = localStorage.getItem(SESSION_KEY);

    if (!stored) {
      return null;
    }

    const sessionData: SessionData = JSON.parse(stored);

    // Validate session data structure
    if (!sessionData.sessionId || !sessionData.expiresAt) {
      // Malformed data - clear it
      clearSession();
      return null;
    }

    // Check expiration
    const now = Date.now();
    if (now > sessionData.expiresAt) {
      // Session expired - clear it
      clearSession();
      return null;
    }

    return sessionData.sessionId;
  } catch (error) {
    // JSON parse error or other issue - clear bad data
    clearSession();
    return null;
  }
}

/**
 * Clear session from localStorage.
 *
 * Call this when user explicitly ends session or starts a new one.
 *
 * @example
 * ```ts
 * clearSession();
 * console.log("Session cleared");
 * ```
 */
export function clearSession(): void {
  localStorage.removeItem(SESSION_KEY);
}

/**
 * Check if a valid session exists without retrieving it.
 *
 * @returns True if valid session exists, false otherwise
 */
export function hasActiveSession(): boolean {
  return getSession() !== null;
}

/**
 * Get time remaining until session expires.
 *
 * @returns Milliseconds until expiration, or 0 if no session/expired
 */
export function getTimeUntilExpiration(): number {
  try {
    const stored = localStorage.getItem(SESSION_KEY);

    if (!stored) {
      return 0;
    }

    const sessionData: SessionData = JSON.parse(stored);
    const now = Date.now();

    if (now > sessionData.expiresAt) {
      return 0;
    }

    return sessionData.expiresAt - now;
  } catch {
    return 0;
  }
}
