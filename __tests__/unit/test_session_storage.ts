/**
 * Unit tests for session storage functions
 * Tests all storage functions in lib/session-storage.ts
 */

import {
  sessionStorageReducer,
  initializeSessionStorage,
  persistSessionStorage,
  getActiveSessions,
  getSessionById,
  getActiveSession,
  needsCleanup,
  updateStorage,
  createNewSession,
} from '@/lib/session-storage';

import {
  MonthSession,
  SessionStorage,
  SessionAction,
  SessionStatus,
  SESSION_CONSTRAINTS,
  DEFAULT_SESSION_STORAGE,
} from '@/lib/session-types';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: jest.fn((key: string) => store[key] || null),
    setItem: jest.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: jest.fn((key: string) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Test data helpers
const createMockSession = (overrides: Partial<MonthSession> = {}): MonthSession => ({
  id: '550e8400-e29b-41d4-a716-446655440000',
  name: 'Test Session',
  createdAt: Date.now() - 86400000, // 1 day ago
  expiresAt: Date.now() + (365 * 24 * 60 * 60 * 1000), // 1 year from now
  status: 'Complete' as SessionStatus,
  backendSessionId: '550e8400-e29b-41d4-a716-446655440001',
  lastUpdated: Date.now() - 86400000,
  hasReports: true,
  fileCount: 2,
  matchCount: 15,
  ...overrides,
});

const createMockStorage = (sessions: MonthSession[] = []): SessionStorage => ({
  sessions: sessions.reduce((acc, session) => {
    acc[session.id] = session;
    return acc;
  }, {} as Record<string, MonthSession>),
  activeSessionId: sessions.length > 0 ? sessions[0].id : null,
  lastCleanup: Date.now(),
  version: SESSION_CONSTRAINTS.SCHEMA_VERSION,
});

describe('Session Storage Functions', () => {
  beforeEach(() => {
    localStorageMock.clear();
    jest.clearAllMocks();
  });

  describe('sessionStorageReducer', () => {
    describe('CREATE_SESSION action', () => {
      it('should create a new session', () => {
        const initialState = createMockStorage([]);
        const action: SessionAction = {
          type: 'CREATE_SESSION',
          payload: { name: 'Test Session', backendSessionId: 'backend-123' },
        };

        const newState = sessionStorageReducer(initialState, action);

        expect(Object.keys(newState.sessions)).toHaveLength(1);
        expect(newState.activeSessionId).not.toBeNull();

        const newSession = Object.values(newState.sessions)[0];
        expect(newSession.name).toBe('Test Session');
        expect(newSession.backendSessionId).toBe('backend-123');
        expect(newSession.status).toBe('Processing');
      });

      it('should clean up expired sessions before creating', () => {
        const expiredSession = createMockSession({
          id: 'expired-1',
          expiresAt: Date.now() - 86400000,
        });

        const initialState = createMockStorage([expiredSession]);
        const action: SessionAction = {
          type: 'CREATE_SESSION',
          payload: { name: 'New Session', backendSessionId: 'backend-123' },
        };

        const newState = sessionStorageReducer(initialState, action);

        expect(newState.sessions['expired-1']).toBeUndefined();
        expect(Object.keys(newState.sessions)).toHaveLength(1);
      });

      it('should remove oldest session when at limit', () => {
        const sessions = Array.from({ length: SESSION_CONSTRAINTS.MAX_SESSIONS }, (_, i) =>
          createMockSession({
            id: `session-${i}`,
            createdAt: Date.now() - (i * 86400000), // Different creation times
          })
        );

        const initialState = createMockStorage(sessions);
        const action: SessionAction = {
          type: 'CREATE_SESSION',
          payload: { name: 'New Session', backendSessionId: 'backend-123' },
        };

        const newState = sessionStorageReducer(initialState, action);

        expect(Object.keys(newState.sessions)).toHaveLength(SESSION_CONSTRAINTS.MAX_SESSIONS);

        // Oldest session should be removed
        const oldestSessionId = `session-${SESSION_CONSTRAINTS.MAX_SESSIONS - 1}`;
        expect(newState.sessions[oldestSessionId]).toBeUndefined();
      });

      it('should clear active session if removed oldest was active', () => {
        const oldestSession = createMockSession({
          id: 'oldest',
          createdAt: Date.now() - (100 * 86400000),
        });

        const sessions = [
          oldestSession,
          ...Array.from({ length: SESSION_CONSTRAINTS.MAX_SESSIONS - 1 }, (_, i) =>
            createMockSession({
              id: `session-${i}`,
              createdAt: Date.now() - (i * 86400000),
            })
          ),
        ];

        const initialState = createMockStorage(sessions);
        initialState.activeSessionId = 'oldest';

        const action: SessionAction = {
          type: 'CREATE_SESSION',
          payload: { name: 'New Session', backendSessionId: 'backend-123' },
        };

        const newState = sessionStorageReducer(initialState, action);

        expect(newState.sessions['oldest']).toBeUndefined();
        expect(newState.activeSessionId).not.toBe('oldest');
      });
    });

    describe('RENAME_SESSION action', () => {
      it('should rename an existing session', () => {
        const session = createMockSession({ id: 'test-1', name: 'Old Name' });
        const initialState = createMockStorage([session]);

        const action: SessionAction = {
          type: 'RENAME_SESSION',
          payload: { id: 'test-1', name: 'New Name' },
        };

        const newState = sessionStorageReducer(initialState, action);

        expect(newState.sessions['test-1'].name).toBe('New Name');
        expect(newState.sessions['test-1'].lastUpdated).toBeGreaterThan(session.lastUpdated);
      });

      it('should trim whitespace from name', () => {
        const session = createMockSession({ id: 'test-1', name: 'Old Name' });
        const initialState = createMockStorage([session]);

        const action: SessionAction = {
          type: 'RENAME_SESSION',
          payload: { id: 'test-1', name: '  New Name  ' },
        };

        const newState = sessionStorageReducer(initialState, action);

        expect(newState.sessions['test-1'].name).toBe('New Name');
      });

      it('should ignore renaming non-existent session', () => {
        const initialState = createMockStorage([]);

        const action: SessionAction = {
          type: 'RENAME_SESSION',
          payload: { id: 'non-existent', name: 'New Name' },
        };

        const newState = sessionStorageReducer(initialState, action);

        expect(newState).toBe(initialState);
      });
    });

    describe('DELETE_SESSION action', () => {
      it('should delete an existing session', () => {
        const session1 = createMockSession({ id: 'test-1' });
        const session2 = createMockSession({ id: 'test-2' });
        const initialState = createMockStorage([session1, session2]);

        const action: SessionAction = {
          type: 'DELETE_SESSION',
          payload: { id: 'test-1' },
        };

        const newState = sessionStorageReducer(initialState, action);

        expect(newState.sessions['test-1']).toBeUndefined();
        expect(newState.sessions['test-2']).toBeDefined();
        expect(Object.keys(newState.sessions)).toHaveLength(1);
      });

      it('should clear active session if deleted session was active', () => {
        const session = createMockSession({ id: 'test-1' });
        const initialState = createMockStorage([session]);

        const action: SessionAction = {
          type: 'DELETE_SESSION',
          payload: { id: 'test-1' },
        };

        const newState = sessionStorageReducer(initialState, action);

        expect(newState.activeSessionId).toBeNull();
      });

      it('should preserve active session if different session deleted', () => {
        const session1 = createMockSession({ id: 'test-1' });
        const session2 = createMockSession({ id: 'test-2' });
        const initialState = createMockStorage([session1, session2]);
        initialState.activeSessionId = 'test-2';

        const action: SessionAction = {
          type: 'DELETE_SESSION',
          payload: { id: 'test-1' },
        };

        const newState = sessionStorageReducer(initialState, action);

        expect(newState.activeSessionId).toBe('test-2');
      });
    });

    describe('SET_ACTIVE_SESSION action', () => {
      it('should set active session to existing session', () => {
        const session1 = createMockSession({ id: 'test-1' });
        const session2 = createMockSession({ id: 'test-2' });
        const initialState = createMockStorage([session1, session2]);
        initialState.activeSessionId = 'test-1';

        const action: SessionAction = {
          type: 'SET_ACTIVE_SESSION',
          payload: { id: 'test-2' },
        };

        const newState = sessionStorageReducer(initialState, action);

        expect(newState.activeSessionId).toBe('test-2');
      });

      it('should set active session to null', () => {
        const session = createMockSession({ id: 'test-1' });
        const initialState = createMockStorage([session]);

        const action: SessionAction = {
          type: 'SET_ACTIVE_SESSION',
          payload: { id: null },
        };

        const newState = sessionStorageReducer(initialState, action);

        expect(newState.activeSessionId).toBeNull();
      });

      it('should ignore setting active session to non-existent session', () => {
        const session = createMockSession({ id: 'test-1' });
        const initialState = createMockStorage([session]);

        const action: SessionAction = {
          type: 'SET_ACTIVE_SESSION',
          payload: { id: 'non-existent' },
        };

        const newState = sessionStorageReducer(initialState, action);

        expect(newState).toBe(initialState);
      });
    });

    describe('UPDATE_SESSION_STATUS action', () => {
      it('should update session status', () => {
        const session = createMockSession({ id: 'test-1', status: 'Processing' });
        const initialState = createMockStorage([session]);

        const action: SessionAction = {
          type: 'UPDATE_SESSION_STATUS',
          payload: { id: 'test-1', status: 'Complete' },
        };

        const newState = sessionStorageReducer(initialState, action);

        expect(newState.sessions['test-1'].status).toBe('Complete');
        expect(newState.sessions['test-1'].lastUpdated).toBeGreaterThan(session.lastUpdated);
      });

      it('should set error message for error status', () => {
        const session = createMockSession({ id: 'test-1', status: 'Processing' });
        const initialState = createMockStorage([session]);

        const action: SessionAction = {
          type: 'UPDATE_SESSION_STATUS',
          payload: { id: 'test-1', status: 'Error', errorMessage: 'Something went wrong' },
        };

        const newState = sessionStorageReducer(initialState, action);

        expect(newState.sessions['test-1'].status).toBe('Error');
        expect(newState.sessions['test-1'].errorMessage).toBe('Something went wrong');
      });

      it('should ignore updating non-existent session', () => {
        const initialState = createMockStorage([]);

        const action: SessionAction = {
          type: 'UPDATE_SESSION_STATUS',
          payload: { id: 'non-existent', status: 'Complete' },
        };

        const newState = sessionStorageReducer(initialState, action);

        expect(newState).toBe(initialState);
      });
    });

    describe('UPDATE_SESSION_REPORTS action', () => {
      it('should update session reports info', () => {
        const session = createMockSession({
          id: 'test-1',
          hasReports: false,
          matchCount: 0
        });
        const initialState = createMockStorage([session]);

        const action: SessionAction = {
          type: 'UPDATE_SESSION_REPORTS',
          payload: { id: 'test-1', hasReports: true, matchCount: 25 },
        };

        const newState = sessionStorageReducer(initialState, action);

        expect(newState.sessions['test-1'].hasReports).toBe(true);
        expect(newState.sessions['test-1'].matchCount).toBe(25);
        expect(newState.sessions['test-1'].lastUpdated).toBeGreaterThan(session.lastUpdated);
      });

      it('should ignore updating non-existent session', () => {
        const initialState = createMockStorage([]);

        const action: SessionAction = {
          type: 'UPDATE_SESSION_REPORTS',
          payload: { id: 'non-existent', hasReports: true, matchCount: 25 },
        };

        const newState = sessionStorageReducer(initialState, action);

        expect(newState).toBe(initialState);
      });
    });

    describe('CLEANUP_EXPIRED_SESSIONS action', () => {
      it('should remove expired sessions', () => {
        const activeSession = createMockSession({
          id: 'active-1',
          expiresAt: Date.now() + 86400000,
        });

        const expiredSession = createMockSession({
          id: 'expired-1',
          expiresAt: Date.now() - 86400000,
        });

        const initialState = createMockStorage([activeSession, expiredSession]);

        const action: SessionAction = { type: 'CLEANUP_EXPIRED_SESSIONS' };

        const newState = sessionStorageReducer(initialState, action);

        expect(newState.sessions['active-1']).toBeDefined();
        expect(newState.sessions['expired-1']).toBeUndefined();
      });
    });

    describe('unknown action type', () => {
      it('should return state unchanged for unknown action', () => {
        const initialState = createMockStorage([]);

        const action = { type: 'UNKNOWN_ACTION' } as any;

        const newState = sessionStorageReducer(initialState, action);

        expect(newState).toBe(initialState);
      });
    });
  });

  describe('initializeSessionStorage', () => {
    it('should return default storage when localStorage is empty', () => {
      localStorageMock.getItem.mockReturnValue(null);

      const storage = initializeSessionStorage();

      expect(storage).toEqual(DEFAULT_SESSION_STORAGE);
    });

    it('should load and clean up stored data', () => {
      const expiredSession = createMockSession({
        id: 'expired-1',
        expiresAt: Date.now() - 86400000,
      });
      const activeSession = createMockSession({
        id: 'active-1',
        expiresAt: Date.now() + 86400000,
      });

      const mockStorage = createMockStorage([expiredSession, activeSession]);
      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockStorage));

      const storage = initializeSessionStorage();

      expect(storage.sessions['active-1']).toBeDefined();
      expect(storage.sessions['expired-1']).toBeUndefined();
    });
  });

  describe('persistSessionStorage', () => {
    it('should save storage to localStorage', () => {
      const mockStorage = createMockStorage([createMockSession()]);

      const result = persistSessionStorage(mockStorage);

      expect(result).toBe(true);
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        SESSION_CONSTRAINTS.STORAGE_KEY,
        JSON.stringify(mockStorage)
      );
    });

    it('should handle save errors', () => {
      const mockStorage = createMockStorage([]);
      localStorageMock.setItem.mockImplementation(() => {
        throw new Error('Storage full');
      });
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      const result = persistSessionStorage(mockStorage);

      expect(result).toBe(false);
      expect(consoleSpy).toHaveBeenCalled();

      consoleSpy.mockRestore();
    });
  });

  describe('getActiveSessions', () => {
    it('should return only non-expired sessions', () => {
      const activeSession = createMockSession({
        id: 'active-1',
        expiresAt: Date.now() + 86400000,
      });

      const expiredSession = createMockSession({
        id: 'expired-1',
        expiresAt: Date.now() - 86400000,
      });

      const storage = createMockStorage([activeSession, expiredSession]);
      const activeSessions = getActiveSessions(storage);

      expect(activeSessions).toHaveLength(1);
      expect(activeSessions[0].id).toBe('active-1');
    });

    it('should return empty array when all sessions are expired', () => {
      const expiredSession1 = createMockSession({
        id: 'expired-1',
        expiresAt: Date.now() - 86400000,
      });

      const expiredSession2 = createMockSession({
        id: 'expired-2',
        expiresAt: Date.now() - 172800000,
      });

      const storage = createMockStorage([expiredSession1, expiredSession2]);
      const activeSessions = getActiveSessions(storage);

      expect(activeSessions).toHaveLength(0);
    });
  });

  describe('getSessionById', () => {
    it('should return session if it exists and is not expired', () => {
      const session = createMockSession({
        id: 'test-1',
        expiresAt: Date.now() + 86400000,
      });

      const storage = createMockStorage([session]);
      const result = getSessionById(storage, 'test-1');

      expect(result).toEqual(session);
    });

    it('should return null for non-existent session', () => {
      const storage = createMockStorage([]);
      const result = getSessionById(storage, 'non-existent');

      expect(result).toBeNull();
    });

    it('should return null for expired session', () => {
      const expiredSession = createMockSession({
        id: 'expired-1',
        expiresAt: Date.now() - 86400000,
      });

      const storage = createMockStorage([expiredSession]);
      const result = getSessionById(storage, 'expired-1');

      expect(result).toBeNull();
    });
  });

  describe('getActiveSession', () => {
    it('should return active session if it exists and is not expired', () => {
      const session = createMockSession({
        id: 'test-1',
        expiresAt: Date.now() + 86400000,
      });

      const storage = createMockStorage([session]);
      storage.activeSessionId = 'test-1';

      const result = getActiveSession(storage);

      expect(result).toEqual(session);
    });

    it('should return null when no active session is set', () => {
      const storage = createMockStorage([createMockSession()]);
      storage.activeSessionId = null;

      const result = getActiveSession(storage);

      expect(result).toBeNull();
    });

    it('should return null when active session is expired', () => {
      const expiredSession = createMockSession({
        id: 'expired-1',
        expiresAt: Date.now() - 86400000,
      });

      const storage = createMockStorage([expiredSession]);
      storage.activeSessionId = 'expired-1';

      const result = getActiveSession(storage);

      expect(result).toBeNull();
    });
  });

  describe('needsCleanup', () => {
    it('should return true when cleanup is needed', () => {
      const storage = createMockStorage([]);
      storage.lastCleanup = Date.now() - (2 * 60 * 60 * 1000); // 2 hours ago

      const result = needsCleanup(storage);

      expect(result).toBe(true);
    });

    it('should return false when cleanup is not needed', () => {
      const storage = createMockStorage([]);
      storage.lastCleanup = Date.now() - (30 * 60 * 1000); // 30 minutes ago

      const result = needsCleanup(storage);

      expect(result).toBe(false);
    });
  });

  describe('updateStorage', () => {
    it('should apply action and persist storage', () => {
      const initialStorage = createMockStorage([]);
      const action: SessionAction = {
        type: 'CREATE_SESSION',
        payload: { name: 'Test Session', backendSessionId: 'backend-123' },
      };

      const result = updateStorage(initialStorage, action);

      expect(Object.keys(result.sessions)).toHaveLength(1);
      expect(localStorageMock.setItem).toHaveBeenCalled();
    });

    it('should auto-cleanup when needed', () => {
      const expiredSession = createMockSession({
        id: 'expired-1',
        expiresAt: Date.now() - 86400000,
      });

      const initialStorage = createMockStorage([expiredSession]);
      initialStorage.lastCleanup = Date.now() - (2 * 60 * 60 * 1000); // 2 hours ago

      const action: SessionAction = {
        type: 'SET_ACTIVE_SESSION',
        payload: { id: null },
      };

      const result = updateStorage(initialStorage, action);

      expect(result.sessions['expired-1']).toBeUndefined();
      expect(result.lastCleanup).toBeGreaterThan(initialStorage.lastCleanup);
    });
  });

  describe('createNewSession', () => {
    it('should create new session and return updated storage with session ID', () => {
      const initialStorage = createMockStorage([]);

      const result = createNewSession(initialStorage, 'New Session', 'backend-123');

      expect(result.sessionId).toBeDefined();
      expect(result.storage.sessions[result.sessionId]).toBeDefined();
      expect(result.storage.sessions[result.sessionId].name).toBe('New Session');
      expect(result.storage.activeSessionId).toBe(result.sessionId);
    });

    it('should persist the storage', () => {
      const initialStorage = createMockStorage([]);

      createNewSession(initialStorage, 'New Session', 'backend-123');

      expect(localStorageMock.setItem).toHaveBeenCalled();
    });

    it('should throw error if session creation fails', () => {
      // Mock a scenario where session creation somehow fails
      const mockReducer = jest.spyOn(require('@/lib/session-storage'), 'sessionStorageReducer');
      mockReducer.mockReturnValue({
        ...createMockStorage([]),
        activeSessionId: null,
      });

      const initialStorage = createMockStorage([]);

      expect(() => {
        createNewSession(initialStorage, 'New Session', 'backend-123');
      }).toThrow('Failed to create new session');

      mockReducer.mockRestore();
    });
  });
});