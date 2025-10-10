'use client';

/**
 * SessionProvider - React Context Provider for Session Management
 *
 * Provides comprehensive session state management following the data model
 * from specs/003-add-ui-components/data-model.md
 */

import React, { createContext, useContext, useReducer, useEffect, useMemo, useCallback } from 'react';
import {
  SessionContextType,
  SessionStorage,
  MonthSession,
  SessionFilter,
  SessionAction,
  ReportFormat,
  DEFAULT_SESSION_FILTER,
} from '@/lib/session-types';

import {
  sessionStorageReducer,
  initializeSessionStorage,
  updateStorage,
  getActiveSession,
  createNewSession,
} from '@/lib/session-storage';

import {
  filterSessions,
  validateSessionName,
  validateReceiptFile,
  isSessionNameUnique,
} from '@/lib/session-utils';

import { listSessions, deleteSession as deleteSessionAPI } from '@/lib/api-client';

import SessionErrorBoundary from './session-error-boundary';

// Create the context
const SessionContext = createContext<SessionContextType | null>(null);

// Provider props
interface SessionProviderProps {
  children: React.ReactNode;
  initialStorage?: SessionStorage; // For testing and storybook
}

// Internal state for the provider
interface SessionProviderState {
  storage: SessionStorage;
  filter: SessionFilter;
  isLoading: boolean;
  error: string | null;
}

// Actions for the provider's internal reducer
type ProviderAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_FILTER'; payload: Partial<SessionFilter> }
  | { type: 'CLEAR_FILTER' }
  | { type: 'UPDATE_STORAGE'; payload: SessionStorage };

// Provider's internal reducer
function providerReducer(state: SessionProviderState, action: ProviderAction): SessionProviderState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };

    case 'SET_ERROR':
      return { ...state, error: action.payload, isLoading: false };

    case 'SET_FILTER':
      return {
        ...state,
        filter: { ...state.filter, ...action.payload },
      };

    case 'CLEAR_FILTER':
      return {
        ...state,
        filter: DEFAULT_SESSION_FILTER,
      };

    case 'UPDATE_STORAGE':
      return { ...state, storage: action.payload };

    default:
      return state;
  }
}

export function SessionProvider({ children, initialStorage }: SessionProviderProps) {
  // Initialize provider state
  const [state, dispatch] = useReducer(providerReducer, {
    storage: initialStorage || initializeSessionStorage(),
    filter: DEFAULT_SESSION_FILTER,
    isLoading: false,
    error: null,
  });

  // Helper to update session storage
  const updateSessionStorage = useCallback((action: SessionAction): SessionStorage => {
    const updatedStorage = updateStorage(state.storage, action);
    dispatch({ type: 'UPDATE_STORAGE', payload: updatedStorage });
    return updatedStorage;
  }, [state.storage]);

  // Get active session
  const activeSession = useMemo((): MonthSession | null => {
    return getActiveSession(state.storage);
  }, [state.storage]);

  // Get filtered sessions
  const filteredSessions = useMemo((): MonthSession[] => {
    const allSessions = Object.values(state.storage.sessions);
    return filterSessions(allSessions, state.filter);
  }, [state.storage.sessions, state.filter]);

  // Session management functions
  const createSession = useCallback(async (name: string, backendSessionId: string): Promise<string> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'SET_ERROR', payload: null });

      // Validate session name
      const nameValidation = validateSessionName(name);
      if (!nameValidation.isValid) {
        throw new Error(nameValidation.error);
      }

      // Check name uniqueness
      if (!isSessionNameUnique(state.storage, name)) {
        throw new Error('A session with this name already exists');
      }

      // Create session using storage helper
      const { storage: updatedStorage, sessionId } = createNewSession(
        state.storage,
        name,
        backendSessionId
      );

      dispatch({ type: 'UPDATE_STORAGE', payload: updatedStorage });

      return sessionId;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create session';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      throw error;
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [state.storage]);

  const renameSession = useCallback(async (id: string, name: string): Promise<void> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'SET_ERROR', payload: null });

      // Validate session name
      const nameValidation = validateSessionName(name);
      if (!nameValidation.isValid) {
        throw new Error(nameValidation.error);
      }

      // Check name uniqueness (excluding current session)
      if (!isSessionNameUnique(state.storage, name, id)) {
        throw new Error('A session with this name already exists');
      }

      // Check session exists
      if (!state.storage.sessions[id]) {
        throw new Error('Session not found');
      }

      updateSessionStorage({
        type: 'RENAME_SESSION',
        payload: { id, name },
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to rename session';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      throw error;
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [state.storage, updateSessionStorage]);

  const deleteSession = useCallback(async (id: string): Promise<void> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'SET_ERROR', payload: null });

      // Check session exists
      if (!state.storage.sessions[id]) {
        throw new Error('Session not found');
      }

      // Call backend API to delete session
      await deleteSessionAPI(id);

      // Reload sessions from backend after successful deletion
      const sessionsData = await listSessions(1, 50);

      // Map API sessions to MonthSession format
      const apiSessions: Record<string, MonthSession> = {};
      sessionsData.items.forEach((apiSession: any) => {
        // Map backend status to UI status
        let uiStatus: 'Processing' | 'Complete' | 'Updated' | 'Error' = 'Processing';
        if (apiSession.status === 'completed') uiStatus = 'Complete';
        else if (apiSession.status === 'failed') uiStatus = 'Error';
        else if (apiSession.status === 'processing') uiStatus = 'Processing';

        apiSessions[apiSession.id] = {
          id: apiSession.id,
          name: `Session ${new Date(apiSession.created_at).toLocaleDateString()}`,
          status: uiStatus,
          createdAt: new Date(apiSession.created_at).getTime(),
          updatedAt: new Date(apiSession.updated_at).getTime(),
          expiresAt: new Date(apiSession.expires_at).getTime(),
          hasReports: apiSession.total_transactions > 0 && apiSession.matched_count > 0,
          summary: apiSession.summary || undefined,
          uploadedFiles: {
            transactions: apiSession.total_transactions || 0,
            receipts: apiSession.total_receipts || 0,
          },
          matchResults: {
            totalMatches: apiSession.matched_count || 0,
            unmatchedTransactions: 0,
            unmatchedReceipts: 0,
          },
        };
      });

      // Update storage with refreshed sessions
      const updatedStorage: SessionStorage = {
        sessions: apiSessions,
        activeSessionId: state.storage.activeSessionId && apiSessions[state.storage.activeSessionId] ? state.storage.activeSessionId : null,
      };
      dispatch({ type: 'UPDATE_STORAGE', payload: updatedStorage });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete session';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      throw error;
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [state.storage, updateSessionStorage]);

  const setActiveSession = useCallback((id: string | null): void => {
    updateSessionStorage({
      type: 'SET_ACTIVE_SESSION',
      payload: { id },
    });
  }, [updateSessionStorage]);

  const updateReceipts = useCallback(async (sessionId: string, file: File): Promise<void> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'SET_ERROR', payload: null });

      // Validate file
      const fileValidation = validateReceiptFile(file);
      if (!fileValidation.isValid) {
        throw new Error(fileValidation.error);
      }

      // Check session exists
      if (!state.storage.sessions[sessionId]) {
        throw new Error('Session not found');
      }

      // Update session status to indicate update in progress
      updateSessionStorage({
        type: 'UPDATE_SESSION_STATUS',
        payload: { id: sessionId, status: 'Processing' },
      });

      // TODO: Implement actual file upload and backend integration
      // This will be completed in Phase 3.4 (Integration)

      // For now, simulate successful update
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Update session with success status
      updateSessionStorage({
        type: 'UPDATE_SESSION_STATUS',
        payload: { id: sessionId, status: 'Updated' },
      });

      // Update reports availability
      updateSessionStorage({
        type: 'UPDATE_SESSION_REPORTS',
        payload: { id: sessionId, hasReports: true, matchCount: 0 },
      });

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update receipts';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });

      // Update session with error status
      if (state.storage.sessions[sessionId]) {
        updateSessionStorage({
          type: 'UPDATE_SESSION_STATUS',
          payload: { id: sessionId, status: 'Error', errorMessage },
        });
      }

      throw error;
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [state.storage, updateSessionStorage]);

  const downloadReports = useCallback(async (sessionId: string, format: ReportFormat): Promise<void> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'SET_ERROR', payload: null });

      // Check session exists and has reports
      const session = state.storage.sessions[sessionId];
      if (!session) {
        throw new Error('Session not found');
      }

      if (!session.hasReports) {
        throw new Error('No reports available for this session');
      }

      // TODO: Implement actual report download
      // This will be completed in Phase 3.4 (Integration)

      // For now, simulate download
      await new Promise(resolve => setTimeout(resolve, 500));

      console.log(`Downloading ${format} report for session ${sessionId}`);

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to download reports';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      throw error;
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [state.storage]);

  const setFilter = useCallback((filter: Partial<SessionFilter>): void => {
    dispatch({ type: 'SET_FILTER', payload: filter });
  }, []);

  const clearFilter = useCallback((): void => {
    dispatch({ type: 'CLEAR_FILTER' });
  }, []);

  // Load sessions from backend API on mount
  useEffect(() => {
    const loadSessionsFromAPI = async () => {
      try {
        dispatch({ type: 'SET_LOADING', payload: true });
        const sessionsData = await listSessions(1, 50);

        // Map API sessions to MonthSession format
        const apiSessions: Record<string, MonthSession> = {};
        sessionsData.items.forEach((apiSession: any) => {
          // Map backend status to UI status
          let uiStatus: 'Processing' | 'Complete' | 'Updated' | 'Error' = 'Processing';
          if (apiSession.status === 'completed') uiStatus = 'Complete';
          else if (apiSession.status === 'failed') uiStatus = 'Error';
          else if (apiSession.status === 'processing') uiStatus = 'Processing';

          apiSessions[apiSession.id] = {
            id: apiSession.id,
            name: `Session ${new Date(apiSession.created_at).toLocaleDateString()}`,
            status: uiStatus,
            createdAt: new Date(apiSession.created_at).getTime(),
            lastUpdated: new Date(apiSession.updated_at).getTime(),
            fileCount: apiSession.upload_count || 0,
            matchCount: apiSession.matched_count || 0,
            hasReports: apiSession.status === 'completed',
            backendSessionId: apiSession.id,
          };
        });

        // Update storage with API sessions
        dispatch({
          type: 'UPDATE_STORAGE',
          payload: {
            ...state.storage,
            sessions: apiSessions,
          },
        });
        dispatch({ type: 'SET_LOADING', payload: false });
      } catch (error) {
        console.error('Failed to load sessions from API:', error);
        dispatch({ type: 'SET_ERROR', payload: 'Failed to load sessions from server' });
      }
    };

    loadSessionsFromAPI();
  }, []); // Only run on mount

  // Cleanup expired sessions periodically
  useEffect(() => {
    const cleanupInterval = setInterval(() => {
      updateSessionStorage({ type: 'CLEANUP_EXPIRED_SESSIONS' });
    }, 60 * 60 * 1000); // Every hour

    return () => clearInterval(cleanupInterval);
  }, [updateSessionStorage]);

  // Context value
  const contextValue: SessionContextType = {
    storage: state.storage,
    activeSession,
    filteredSessions,
    isLoading: state.isLoading,
    error: state.error,
    createSession,
    renameSession,
    deleteSession,
    setActiveSession,
    updateReceipts,
    downloadReports,
    setFilter,
    clearFilter,
  };

  return (
    <SessionErrorBoundary
      onError={(error, errorInfo) => {
        console.error('Session management error:', error, errorInfo);
        // Optionally report to error tracking service
      }}
      resetOnPropChange={state.storage.version} // Reset error state when storage changes
    >
      <SessionContext.Provider value={contextValue}>
        {children}
      </SessionContext.Provider>
    </SessionErrorBoundary>
  );
}

// Hook to use the session context
export function useSession(): SessionContextType {
  const context = useContext(SessionContext);

  if (!context) {
    throw new Error('useSession must be used within a SessionProvider');
  }

  return context;
}

// Export context for testing
export { SessionContext };