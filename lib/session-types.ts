// Session Management Type Definitions
// Generated from specs/003-add-ui-components/data-model.md

/**
 * Current processing state of a session
 */
export type SessionStatus = 'Processing' | 'Complete' | 'Updated' | 'Error';

/**
 * Receipt update operation status
 */
export type ReceiptUpdateStatus = 'uploading' | 'processing' | 'complete' | 'error';

/**
 * Sort criteria for session browser
 */
export type SessionSortBy = 'name' | 'createdAt' | 'lastUpdated';

/**
 * Sort direction
 */
export type SessionSortOrder = 'asc' | 'desc';

/**
 * Report format options
 */
export type ReportFormat = 'excel' | 'csv';

/**
 * MonthSession represents a monthly expense processing session with complete lifecycle management
 */
export interface MonthSession {
  /** Unique identifier (UUID v4) */
  id: string;
  /** User-defined name (e.g., "January 2024", "Q1 Processing") */
  name: string;
  /** Unix timestamp of creation */
  createdAt: number;
  /** Unix timestamp when session expires (createdAt + 1 year) */
  expiresAt: number;
  /** Current processing state */
  status: SessionStatus;
  /** Associated backend session identifier */
  backendSessionId: string;
  /** Unix timestamp of last modification */
  lastUpdated: number;
  /** Whether Excel/CSV reports are available */
  hasReports: boolean;
  /** Number of files processed in this session */
  fileCount: number;
  /** Number of successful expense matches */
  matchCount: number;
  /** Error details if status is 'Error' */
  errorMessage?: string;
}

/**
 * SessionStorage container for all session data with automatic cleanup and limits
 */
export interface SessionStorage {
  /** All sessions keyed by ID */
  sessions: Record<string, MonthSession>;
  /** Currently selected session */
  activeSessionId: string | null;
  /** Unix timestamp of last expired session cleanup */
  lastCleanup: number;
  /** Schema version for migrations */
  version: number;
}

/**
 * ReceiptUpdate represents a receipt update operation with progress tracking
 */
export interface ReceiptUpdate {
  /** Target session for update */
  sessionId: string;
  /** Expense report file for upload */
  file: File;
  /** Upload/processing progress (0-100) */
  progress: number;
  /** Current status of the update operation */
  status: ReceiptUpdateStatus;
  /** Unix timestamp when update began */
  startedAt: number;
  /** Unix timestamp when update finished */
  completedAt?: number;
  /** Error details if update failed */
  errorMessage?: string;
}

/**
 * SessionFilter search and filter criteria for session browser
 */
export interface SessionFilter {
  /** Text search across session names */
  searchTerm: string;
  /** Filter by session status */
  statusFilter: SessionStatus[] | 'all';
  /** Filter by creation date */
  dateRange: {
    start?: Date;
    end?: Date;
  };
  /** Sort criteria */
  sortBy: SessionSortBy;
  /** Sort direction */
  sortOrder: SessionSortOrder;
}

/**
 * Session actions for useReducer pattern
 */
export type SessionAction =
  | { type: 'CREATE_SESSION'; payload: { name: string; backendSessionId: string } }
  | { type: 'RENAME_SESSION'; payload: { id: string; name: string } }
  | { type: 'DELETE_SESSION'; payload: { id: string } }
  | { type: 'SET_ACTIVE_SESSION'; payload: { id: string | null } }
  | { type: 'UPDATE_SESSION_STATUS'; payload: { id: string; status: SessionStatus; errorMessage?: string } }
  | { type: 'UPDATE_SESSION_REPORTS'; payload: { id: string; hasReports: boolean; matchCount: number } }
  | { type: 'CLEANUP_EXPIRED_SESSIONS' };

/**
 * SessionContextType interface for React Context
 */
export interface SessionContextType {
  /** Current session storage state */
  storage: SessionStorage;
  /** Currently active session */
  activeSession: MonthSession | null;
  /** Filtered sessions based on current filter criteria */
  filteredSessions: MonthSession[];
  /** Loading state for async operations */
  isLoading: boolean;
  /** Error state */
  error: string | null;

  // Actions
  /** Create a new session with the given name and backend session ID */
  createSession: (name: string, backendSessionId: string) => Promise<string>;
  /** Rename an existing session */
  renameSession: (id: string, name: string) => Promise<void>;
  /** Delete a session */
  deleteSession: (id: string) => Promise<void>;
  /** Set the active session */
  setActiveSession: (id: string | null) => void;
  /** Update receipts for a session */
  updateReceipts: (sessionId: string, file: File) => Promise<void>;
  /** Download reports for a session */
  downloadReports: (sessionId: string, format: ReportFormat) => Promise<void>;

  // Filters
  /** Set filter criteria */
  setFilter: (filter: Partial<SessionFilter>) => void;
  /** Clear all filters */
  clearFilter: () => void;
}

/**
 * Validation rules and constants
 */
export const SESSION_CONSTRAINTS = {
  /** Maximum number of sessions allowed */
  MAX_SESSIONS: 24,
  /** Session expiration period in milliseconds (1 year) */
  EXPIRATION_PERIOD: 31_536_000_000,
  /** Maximum session name length */
  MAX_NAME_LENGTH: 100,
  /** Minimum session name length */
  MIN_NAME_LENGTH: 1,
  /** Maximum file size for uploads (50MB) */
  MAX_FILE_SIZE: 50 * 1024 * 1024,
  /** localStorage key for session data */
  STORAGE_KEY: 'expense_sessions',
  /** Current schema version */
  SCHEMA_VERSION: 1,
} as const;

/**
 * Default session filter state
 */
export const DEFAULT_SESSION_FILTER: SessionFilter = {
  searchTerm: '',
  statusFilter: 'all',
  dateRange: {},
  sortBy: 'lastUpdated',
  sortOrder: 'desc',
};

/**
 * Default session storage state
 */
export const DEFAULT_SESSION_STORAGE: SessionStorage = {
  sessions: {},
  activeSessionId: null,
  lastCleanup: Date.now(),
  version: SESSION_CONSTRAINTS.SCHEMA_VERSION,
};