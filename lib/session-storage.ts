/**
 * Session Storage Implementation for Multi-Session Management
 *
 * Extends existing localStorage approach to support multiple named sessions
 * with 1-year TTL and 24-session limit as per specs/003-add-ui-components/research.md
 */

import {
  SessionStorage,
  MonthSession,
  SessionAction,
  SESSION_CONSTRAINTS,
  DEFAULT_SESSION_STORAGE,
} from './session-types';

import {
  loadSessionStorage,
  saveSessionStorage,
  cleanupExpiredSessions,
  isSessionExpired,
  createSession,
  generateSessionId,
} from './session-utils';

/**
 * Session storage reducer for managing session state updates
 */
export function sessionStorageReducer(
  state: SessionStorage,
  action: SessionAction
): SessionStorage {
  switch (action.type) {
    case 'CREATE_SESSION': {
      const { name, backendSessionId } = action.payload;

      // Clean up expired sessions first
      const cleanedState = cleanupExpiredSessions(state);

      // Check session limit
      if (Object.keys(cleanedState.sessions).length >= SESSION_CONSTRAINTS.MAX_SESSIONS) {
        // Remove oldest session to make room
        const oldestSession = Object.values(cleanedState.sessions)
          .sort((a, b) => a.createdAt - b.createdAt)[0];

        if (oldestSession) {
          delete cleanedState.sessions[oldestSession.id];

          // Clear active session if it was the removed one
          if (cleanedState.activeSessionId === oldestSession.id) {
            cleanedState.activeSessionId = null;
          }
        }
      }

      // Create new session
      const newSession = createSession(name, backendSessionId);

      return {
        ...cleanedState,
        sessions: {
          ...cleanedState.sessions,
          [newSession.id]: newSession,
        },
        activeSessionId: newSession.id,
        lastCleanup: Date.now(),
      };
    }

    case 'RENAME_SESSION': {
      const { id, name } = action.payload;

      if (!state.sessions[id]) {
        return state;
      }

      return {
        ...state,
        sessions: {
          ...state.sessions,
          [id]: {
            ...state.sessions[id],
            name: name.trim(),
            lastUpdated: Date.now(),
          },
        },
      };
    }

    case 'DELETE_SESSION': {
      const { id } = action.payload;

      const newSessions = { ...state.sessions };
      delete newSessions[id];

      return {
        ...state,
        sessions: newSessions,
        activeSessionId: state.activeSessionId === id ? null : state.activeSessionId,
      };
    }

    case 'SET_ACTIVE_SESSION': {
      const { id } = action.payload;

      // Validate session exists or is null
      if (id !== null && !state.sessions[id]) {
        return state;
      }

      return {
        ...state,
        activeSessionId: id,
      };
    }

    case 'UPDATE_SESSION_STATUS': {
      const { id, status, errorMessage } = action.payload;

      if (!state.sessions[id]) {
        return state;
      }

      return {
        ...state,
        sessions: {
          ...state.sessions,
          [id]: {
            ...state.sessions[id],
            status,
            lastUpdated: Date.now(),
            errorMessage: errorMessage || undefined,
          },
        },
      };
    }

    case 'UPDATE_SESSION_REPORTS': {
      const { id, hasReports, matchCount } = action.payload;

      if (!state.sessions[id]) {
        return state;
      }

      return {
        ...state,
        sessions: {
          ...state.sessions,
          [id]: {
            ...state.sessions[id],
            hasReports,
            matchCount,
            lastUpdated: Date.now(),
          },
        },
      };
    }

    case 'CLEANUP_EXPIRED_SESSIONS': {
      return cleanupExpiredSessions(state);
    }

    default:
      return state;
  }
}

/**
 * Initialize session storage from localStorage
 */
export function initializeSessionStorage(): SessionStorage {
  return loadSessionStorage();
}

/**
 * Persist session storage to localStorage
 */
export function persistSessionStorage(storage: SessionStorage): boolean {
  return saveSessionStorage(storage);
}

/**
 * Get all non-expired sessions
 */
export function getActiveSessions(storage: SessionStorage): MonthSession[] {
  return Object.values(storage.sessions).filter(session => !isSessionExpired(session));
}

/**
 * Get session by ID if it exists and is not expired
 */
export function getSessionById(storage: SessionStorage, id: string): MonthSession | null {
  if (!storage || !storage.sessions) {
    return null;
  }

  const session = storage.sessions[id];

  if (!session || isSessionExpired(session)) {
    return null;
  }

  return session;
}

/**
 * Get currently active session
 */
export function getActiveSession(storage: SessionStorage): MonthSession | null {
  if (!storage || !storage.activeSessionId) {
    return null;
  }

  return getSessionById(storage, storage.activeSessionId);
}

/**
 * Check if storage needs cleanup
 */
export function needsCleanup(storage: SessionStorage): boolean {
  const now = Date.now();
  const timeSinceLastCleanup = now - storage.lastCleanup;

  // Clean up every hour
  return timeSinceLastCleanup > 60 * 60 * 1000;
}

/**
 * Safely update storage with automatic persistence and cleanup
 */
export function updateStorage(
  currentStorage: SessionStorage,
  action: SessionAction
): SessionStorage {
  let updatedStorage = sessionStorageReducer(currentStorage, action);

  // Auto-cleanup if needed
  if (needsCleanup(updatedStorage)) {
    updatedStorage = cleanupExpiredSessions(updatedStorage);
  }

  // Persist to localStorage
  persistSessionStorage(updatedStorage);

  return updatedStorage;
}

/**
 * Create a new session with validation
 */
export function createNewSession(
  storage: SessionStorage,
  name: string,
  backendSessionId: string
): { storage: SessionStorage; sessionId: string } {
  const updatedStorage = updateStorage(storage, {
    type: 'CREATE_SESSION',
    payload: { name, backendSessionId },
  });

  // Find the newly created session (it should be the active one)
  const newSessionId = updatedStorage.activeSessionId;

  if (!newSessionId) {
    throw new Error('Failed to create new session');
  }

  return {
    storage: updatedStorage,
    sessionId: newSessionId,
  };
}

/**
 * Clear the current active session
 */
export function clearSession(): void {
  const storage = loadSessionStorage();
  if (storage.activeSessionId) {
    const updatedStorage = sessionStorageReducer(storage, {
      type: 'DELETE_SESSION',
      payload: { id: storage.activeSessionId },
    });
    persistSessionStorage(updatedStorage);
  }
}

/**
 * Get session from storage (alias for getActiveSession)
 */
export function getSession(storage: SessionStorage): MonthSession | null {
  return getActiveSession(storage);
}

/**
 * Save session to storage (alias for persistSessionStorage)
 */
export function saveSession(storage: SessionStorage): boolean {
  return persistSessionStorage(storage);
}

/**
 * Export for use in components
 */
export {
  loadSessionStorage,
  saveSessionStorage,
  cleanupExpiredSessions,
  isSessionExpired,
  createSession,
} from './session-utils';