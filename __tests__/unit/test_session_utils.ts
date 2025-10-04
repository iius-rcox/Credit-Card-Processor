/**
 * Unit tests for session utilities
 * Tests all utility functions in lib/session-utils.ts
 */

import {
  generateSessionId,
  validateSessionName,
  validateReceiptFile,
  createSession,
  isSessionExpired,
  getExpiredSessions,
  cleanupExpiredSessions,
  isApproachingSessionLimit,
  isAtSessionLimit,
  filterSessions,
  formatSessionDate,
  formatSessionStatus,
  getSessionStatusColor,
  getTimeUntilExpiration,
  isSessionNameUnique,
  loadSessionStorage,
  saveSessionStorage,
} from '@/lib/session-utils';

import {
  MonthSession,
  SessionStorage,
  SessionFilter,
  SessionStatus,
  SESSION_CONSTRAINTS,
  DEFAULT_SESSION_STORAGE,
  DEFAULT_SESSION_FILTER,
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

const createMockFile = (overrides: Partial<File> = {}): File => {
  const mockFile = new File(['test content'], 'test.pdf', {
    type: 'application/pdf',
    ...overrides,
  });

  // Mock the size property
  Object.defineProperty(mockFile, 'size', {
    value: overrides.size || 1024 * 1024, // 1MB default
    writable: false,
  });

  return mockFile;
};

describe('Session Utilities', () => {
  beforeEach(() => {
    localStorageMock.clear();
    jest.clearAllMocks();
  });

  describe('generateSessionId', () => {
    it('should generate a valid UUID v4', () => {
      const id = generateSessionId();

      // UUID v4 format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
      const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
      expect(id).toMatch(uuidRegex);
    });

    it('should generate unique IDs', () => {
      const id1 = generateSessionId();
      const id2 = generateSessionId();

      expect(id1).not.toBe(id2);
    });

    it('should always have version 4 (4 in 3rd section)', () => {
      const id = generateSessionId();
      const sections = id.split('-');

      expect(sections[2]).toMatch(/^4[0-9a-f]{3}$/i);
    });
  });

  describe('validateSessionName', () => {
    it('should accept valid session names', () => {
      const result = validateSessionName('January 2024');

      expect(result.isValid).toBe(true);
      expect(result.error).toBeUndefined();
    });

    it('should reject empty names', () => {
      const result = validateSessionName('');

      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Session name cannot be empty');
    });

    it('should reject whitespace-only names', () => {
      const result = validateSessionName('   ');

      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Session name cannot be empty');
    });

    it('should reject names that are too short', () => {
      const result = validateSessionName('A');

      expect(result.isValid).toBe(false);
      expect(result.error).toBe(`Session name must be at least ${SESSION_CONSTRAINTS.MIN_NAME_LENGTH} character`);
    });

    it('should reject names that are too long', () => {
      const longName = 'A'.repeat(SESSION_CONSTRAINTS.MAX_NAME_LENGTH + 1);
      const result = validateSessionName(longName);

      expect(result.isValid).toBe(false);
      expect(result.error).toBe(`Session name must be no more than ${SESSION_CONSTRAINTS.MAX_NAME_LENGTH} characters`);
    });

    it('should trim whitespace before validation', () => {
      const result = validateSessionName('  January 2024  ');

      expect(result.isValid).toBe(true);
    });
  });

  describe('validateReceiptFile', () => {
    it('should accept valid PDF files', () => {
      const file = createMockFile({ type: 'application/pdf', size: 1024 * 1024 });
      const result = validateReceiptFile(file);

      expect(result.isValid).toBe(true);
      expect(result.error).toBeUndefined();
    });

    it('should reject non-PDF files', () => {
      const file = createMockFile({ type: 'image/jpeg' });
      const result = validateReceiptFile(file);

      expect(result.isValid).toBe(false);
      expect(result.error).toBe('Only PDF files are allowed for receipt uploads');
    });

    it('should reject files that are too large', () => {
      const file = createMockFile({
        type: 'application/pdf',
        size: SESSION_CONSTRAINTS.MAX_FILE_SIZE + 1
      });
      const result = validateReceiptFile(file);

      expect(result.isValid).toBe(false);
      expect(result.error).toContain('File size must be less than');
    });

    it('should accept files at the size limit', () => {
      const file = createMockFile({
        type: 'application/pdf',
        size: SESSION_CONSTRAINTS.MAX_FILE_SIZE
      });
      const result = validateReceiptFile(file);

      expect(result.isValid).toBe(true);
    });
  });

  describe('createSession', () => {
    it('should create a session with correct structure', () => {
      const name = 'Test Session';
      const backendSessionId = 'backend-123';
      const beforeCreate = Date.now();

      const session = createSession(name, backendSessionId);
      const afterCreate = Date.now();

      expect(session).toMatchObject({
        name: 'Test Session',
        status: 'Processing',
        backendSessionId: 'backend-123',
        hasReports: false,
        fileCount: 0,
        matchCount: 0,
      });

      expect(session.id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i);
      expect(session.createdAt).toBeGreaterThanOrEqual(beforeCreate);
      expect(session.createdAt).toBeLessThanOrEqual(afterCreate);
      expect(session.lastUpdated).toBe(session.createdAt);
      expect(session.expiresAt).toBe(session.createdAt + SESSION_CONSTRAINTS.EXPIRATION_PERIOD);
    });

    it('should trim the session name', () => {
      const session = createSession('  Test Session  ', 'backend-123');

      expect(session.name).toBe('Test Session');
    });

    it('should generate unique IDs for different sessions', () => {
      const session1 = createSession('Session 1', 'backend-1');
      const session2 = createSession('Session 2', 'backend-2');

      expect(session1.id).not.toBe(session2.id);
    });
  });

  describe('isSessionExpired', () => {
    it('should return false for non-expired sessions', () => {
      const session = createMockSession({
        expiresAt: Date.now() + 86400000, // 1 day from now
      });

      expect(isSessionExpired(session)).toBe(false);
    });

    it('should return true for expired sessions', () => {
      const session = createMockSession({
        expiresAt: Date.now() - 86400000, // 1 day ago
      });

      expect(isSessionExpired(session)).toBe(true);
    });

    it('should return true for sessions expiring exactly now', () => {
      const session = createMockSession({
        expiresAt: Date.now(),
      });

      expect(isSessionExpired(session)).toBe(true);
    });
  });

  describe('getExpiredSessions', () => {
    it('should return only expired sessions', () => {
      const activeSession = createMockSession({
        id: 'active-1',
        expiresAt: Date.now() + 86400000,
      });

      const expiredSession = createMockSession({
        id: 'expired-1',
        expiresAt: Date.now() - 86400000,
      });

      const storage = createMockStorage([activeSession, expiredSession]);
      const expired = getExpiredSessions(storage);

      expect(expired).toHaveLength(1);
      expect(expired[0].id).toBe('expired-1');
    });

    it('should return empty array when no sessions are expired', () => {
      const session1 = createMockSession({
        id: 'active-1',
        expiresAt: Date.now() + 86400000,
      });

      const session2 = createMockSession({
        id: 'active-2',
        expiresAt: Date.now() + 172800000,
      });

      const storage = createMockStorage([session1, session2]);
      const expired = getExpiredSessions(storage);

      expect(expired).toHaveLength(0);
    });
  });

  describe('cleanupExpiredSessions', () => {
    it('should remove expired sessions', () => {
      const activeSession = createMockSession({
        id: 'active-1',
        expiresAt: Date.now() + 86400000,
      });

      const expiredSession = createMockSession({
        id: 'expired-1',
        expiresAt: Date.now() - 86400000,
      });

      const storage = createMockStorage([activeSession, expiredSession]);
      const cleaned = cleanupExpiredSessions(storage);

      expect(Object.keys(cleaned.sessions)).toHaveLength(1);
      expect(cleaned.sessions['active-1']).toBeDefined();
      expect(cleaned.sessions['expired-1']).toBeUndefined();
    });

    it('should clear active session if it is expired', () => {
      const expiredSession = createMockSession({
        id: 'expired-1',
        expiresAt: Date.now() - 86400000,
      });

      const storage = createMockStorage([expiredSession]);
      storage.activeSessionId = 'expired-1';

      const cleaned = cleanupExpiredSessions(storage);

      expect(cleaned.activeSessionId).toBeNull();
    });

    it('should update lastCleanup timestamp', () => {
      const storage = createMockStorage([]);
      const beforeCleanup = Date.now();

      const cleaned = cleanupExpiredSessions(storage);

      expect(cleaned.lastCleanup).toBeGreaterThanOrEqual(beforeCleanup);
    });
  });

  describe('isApproachingSessionLimit', () => {
    it('should return true when approaching limit', () => {
      const sessions = Array.from({ length: 22 }, (_, i) =>
        createMockSession({ id: `session-${i}` })
      );
      const storage = createMockStorage(sessions);

      expect(isApproachingSessionLimit(storage)).toBe(true);
    });

    it('should return false when well below limit', () => {
      const sessions = Array.from({ length: 10 }, (_, i) =>
        createMockSession({ id: `session-${i}` })
      );
      const storage = createMockStorage(sessions);

      expect(isApproachingSessionLimit(storage)).toBe(false);
    });
  });

  describe('isAtSessionLimit', () => {
    it('should return true when at limit', () => {
      const sessions = Array.from({ length: SESSION_CONSTRAINTS.MAX_SESSIONS }, (_, i) =>
        createMockSession({ id: `session-${i}` })
      );
      const storage = createMockStorage(sessions);

      expect(isAtSessionLimit(storage)).toBe(true);
    });

    it('should return false when below limit', () => {
      const sessions = Array.from({ length: SESSION_CONSTRAINTS.MAX_SESSIONS - 1 }, (_, i) =>
        createMockSession({ id: `session-${i}` })
      );
      const storage = createMockStorage(sessions);

      expect(isAtSessionLimit(storage)).toBe(false);
    });
  });

  describe('filterSessions', () => {
    const sessions = [
      createMockSession({
        id: '1',
        name: 'January 2024',
        status: 'Complete',
        createdAt: Date.now() - 172800000, // 2 days ago
        lastUpdated: Date.now() - 86400000, // 1 day ago
      }),
      createMockSession({
        id: '2',
        name: 'February 2024',
        status: 'Processing',
        createdAt: Date.now() - 86400000, // 1 day ago
        lastUpdated: Date.now(),
      }),
      createMockSession({
        id: '3',
        name: 'March 2024',
        status: 'Error',
        createdAt: Date.now(),
        lastUpdated: Date.now(),
      }),
    ];

    it('should filter by search term', () => {
      const filter: SessionFilter = {
        ...DEFAULT_SESSION_FILTER,
        searchTerm: 'January',
      };

      const filtered = filterSessions(sessions, filter);

      expect(filtered).toHaveLength(1);
      expect(filtered[0].name).toBe('January 2024');
    });

    it('should filter by status', () => {
      const filter: SessionFilter = {
        ...DEFAULT_SESSION_FILTER,
        statusFilter: ['Processing'],
      };

      const filtered = filterSessions(sessions, filter);

      expect(filtered).toHaveLength(1);
      expect(filtered[0].status).toBe('Processing');
    });

    it('should sort by name ascending', () => {
      const filter: SessionFilter = {
        ...DEFAULT_SESSION_FILTER,
        sortBy: 'name',
        sortOrder: 'asc',
      };

      const filtered = filterSessions(sessions, filter);

      expect(filtered[0].name).toBe('February 2024');
      expect(filtered[1].name).toBe('January 2024');
      expect(filtered[2].name).toBe('March 2024');
    });

    it('should sort by created date descending', () => {
      const filter: SessionFilter = {
        ...DEFAULT_SESSION_FILTER,
        sortBy: 'createdAt',
        sortOrder: 'desc',
      };

      const filtered = filterSessions(sessions, filter);

      expect(filtered[0].name).toBe('March 2024');
      expect(filtered[1].name).toBe('February 2024');
      expect(filtered[2].name).toBe('January 2024');
    });

    it('should handle empty search term', () => {
      const filter: SessionFilter = {
        ...DEFAULT_SESSION_FILTER,
        searchTerm: '',
      };

      const filtered = filterSessions(sessions, filter);

      expect(filtered).toHaveLength(3);
    });

    it('should be case insensitive for search', () => {
      const filter: SessionFilter = {
        ...DEFAULT_SESSION_FILTER,
        searchTerm: 'JANUARY',
      };

      const filtered = filterSessions(sessions, filter);

      expect(filtered).toHaveLength(1);
      expect(filtered[0].name).toBe('January 2024');
    });
  });

  describe('formatSessionDate', () => {
    it('should format date correctly', () => {
      const timestamp = new Date('2024-01-15').getTime();
      const formatted = formatSessionDate(timestamp);

      expect(formatted).toBe('Jan 15, 2024');
    });

    it('should handle current date', () => {
      const now = Date.now();
      const formatted = formatSessionDate(now);

      expect(formatted).toMatch(/\w{3} \d{1,2}, \d{4}/);
    });
  });

  describe('formatSessionStatus', () => {
    it('should format all status types correctly', () => {
      expect(formatSessionStatus('Processing')).toBe('Processing');
      expect(formatSessionStatus('Complete')).toBe('Complete');
      expect(formatSessionStatus('Updated')).toBe('Updated');
      expect(formatSessionStatus('Error')).toBe('Error');
    });

    it('should handle unknown status', () => {
      expect(formatSessionStatus('Unknown' as SessionStatus)).toBe('Unknown');
    });
  });

  describe('getSessionStatusColor', () => {
    it('should return correct colors for each status', () => {
      expect(getSessionStatusColor('Processing')).toBe('blue');
      expect(getSessionStatusColor('Complete')).toBe('green');
      expect(getSessionStatusColor('Updated')).toBe('amber');
      expect(getSessionStatusColor('Error')).toBe('red');
    });

    it('should return gray for unknown status', () => {
      expect(getSessionStatusColor('Unknown' as SessionStatus)).toBe('gray');
    });
  });

  describe('getTimeUntilExpiration', () => {
    it('should calculate time correctly for non-expired sessions', () => {
      const session = createMockSession({
        expiresAt: Date.now() + (2 * 24 * 60 * 60 * 1000), // 2 days from now
      });

      const result = getTimeUntilExpiration(session);

      expect(result.expired).toBe(false);
      expect(result.days).toBe(1); // Should be 1 due to rounding
      expect(result.hours).toBeGreaterThanOrEqual(0);
    });

    it('should return expired true for expired sessions', () => {
      const session = createMockSession({
        expiresAt: Date.now() - 86400000, // 1 day ago
      });

      const result = getTimeUntilExpiration(session);

      expect(result.expired).toBe(true);
      expect(result.days).toBe(0);
      expect(result.hours).toBe(0);
    });
  });

  describe('isSessionNameUnique', () => {
    it('should return true for unique names', () => {
      const sessions = [
        createMockSession({ id: '1', name: 'January 2024' }),
        createMockSession({ id: '2', name: 'February 2024' }),
      ];
      const storage = createMockStorage(sessions);

      expect(isSessionNameUnique(storage, 'March 2024')).toBe(true);
    });

    it('should return false for duplicate names', () => {
      const sessions = [
        createMockSession({ id: '1', name: 'January 2024' }),
        createMockSession({ id: '2', name: 'February 2024' }),
      ];
      const storage = createMockStorage(sessions);

      expect(isSessionNameUnique(storage, 'January 2024')).toBe(false);
    });

    it('should ignore the excluded session ID', () => {
      const sessions = [
        createMockSession({ id: '1', name: 'January 2024' }),
        createMockSession({ id: '2', name: 'February 2024' }),
      ];
      const storage = createMockStorage(sessions);

      expect(isSessionNameUnique(storage, 'January 2024', '1')).toBe(true);
    });

    it('should be case insensitive', () => {
      const sessions = [
        createMockSession({ id: '1', name: 'January 2024' }),
      ];
      const storage = createMockStorage(sessions);

      expect(isSessionNameUnique(storage, 'JANUARY 2024')).toBe(false);
    });
  });

  describe('loadSessionStorage', () => {
    it('should return default storage when localStorage is empty', () => {
      localStorageMock.getItem.mockReturnValue(null);

      const storage = loadSessionStorage();

      expect(storage).toEqual(DEFAULT_SESSION_STORAGE);
    });

    it('should parse valid stored data', () => {
      const mockStorage = createMockStorage([createMockSession()]);
      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockStorage));

      const storage = loadSessionStorage();

      expect(storage.version).toBe(SESSION_CONSTRAINTS.SCHEMA_VERSION);
      expect(Object.keys(storage.sessions)).toHaveLength(1);
    });

    it('should handle invalid JSON gracefully', () => {
      localStorageMock.getItem.mockReturnValue('invalid json');
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      const storage = loadSessionStorage();

      expect(storage).toEqual(DEFAULT_SESSION_STORAGE);
      expect(consoleSpy).toHaveBeenCalled();

      consoleSpy.mockRestore();
    });

    it('should handle version mismatch', () => {
      const mockStorage = { ...createMockStorage([]), version: 999 };
      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockStorage));

      const storage = loadSessionStorage();

      expect(storage).toEqual(DEFAULT_SESSION_STORAGE);
    });

    it('should cleanup expired sessions on load', () => {
      const expiredSession = createMockSession({
        id: 'expired-1',
        expiresAt: Date.now() - 86400000,
      });
      const mockStorage = createMockStorage([expiredSession]);
      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockStorage));

      const storage = loadSessionStorage();

      expect(Object.keys(storage.sessions)).toHaveLength(0);
    });
  });

  describe('saveSessionStorage', () => {
    it('should save storage to localStorage', () => {
      const mockStorage = createMockStorage([createMockSession()]);

      const result = saveSessionStorage(mockStorage);

      expect(result).toBe(true);
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        SESSION_CONSTRAINTS.STORAGE_KEY,
        JSON.stringify(mockStorage)
      );
    });

    it('should handle save errors gracefully', () => {
      const mockStorage = createMockStorage([]);
      localStorageMock.setItem.mockImplementation(() => {
        throw new Error('Storage full');
      });
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      const result = saveSessionStorage(mockStorage);

      expect(result).toBe(false);
      expect(consoleSpy).toHaveBeenCalled();

      consoleSpy.mockRestore();
    });
  });
});