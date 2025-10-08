/**
 * Custom hook for managing progress state with useReducer.
 *
 * This hook combines SSE connection management with progress state updates,
 * providing a complete solution for tracking processing progress.
 */

import { useReducer, useCallback, useEffect, useMemo } from 'react';
import { useSSE } from './useSSE';
import { useProgressPersistence } from './useProgressPersistence';
import {
  ProgressState,
  ProgressAction,
  ProgressResponse,
  ErrorContext
} from '../types/progress';

/**
 * Initial progress state
 */
const initialState: ProgressState = {
  sessionId: '',
  overall: {
    percentage: 0,
    phase: 'pending'
  },
  phases: {},
  statusMessage: '',
  lastUpdate: null,
  error: null,
  isLoading: false,
  connectionState: 'disconnected'
};

/**
 * Progress state reducer
 */
function progressReducer(state: ProgressState, action: ProgressAction): ProgressState {
  switch (action.type) {
    case 'SET_PROGRESS':
      return {
        ...state,
        sessionId: action.payload.sessionId,
        overall: {
          percentage: action.payload.overallPercentage,
          phase: action.payload.currentPhase
        },
        phases: action.payload.phases,
        statusMessage: action.payload.statusMessage,
        lastUpdate: action.payload.lastUpdate,
        error: action.payload.error || null,
        isLoading: false
      };

    case 'SET_CONNECTION_STATE':
      return {
        ...state,
        connectionState: action.payload
      };

    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        isLoading: false
      };

    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null
      };

    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload
      };

    case 'RESET':
      return initialState;

    default:
      return state;
  }
}

export interface UseProgressOptions {
  sessionId: string;
  enableSSE?: boolean;
  enablePolling?: boolean;
  pollingInterval?: number;
  enablePersistence?: boolean;
  onComplete?: () => void;
  onError?: (error: ErrorContext) => void;
}

export interface UseProgressReturn {
  state: ProgressState;
  connect: () => void;
  disconnect: () => void;
  refresh: () => Promise<void>;
  clearError: () => void;
  reset: () => void;
}

/**
 * Custom hook for managing progress state
 *
 * @param options - Configuration options
 * @returns Progress state and management functions
 */
export function useProgress(options: UseProgressOptions): UseProgressReturn {
  const {
    sessionId,
    enableSSE = true,
    enablePolling = !enableSSE,
    pollingInterval = 3000,
    enablePersistence = true,
    onComplete,
    onError
  } = options;

  const [state, dispatch] = useReducer(progressReducer, initialState);

  // Persistence hook
  const { saveProgress, loadProgress, clearProgress } = useProgressPersistence(sessionId);

  // Load persisted state on mount
  useEffect(() => {
    if (enablePersistence && sessionId) {
      const persisted = loadProgress();
      if (persisted) {
        dispatch({ type: 'SET_PROGRESS', payload: persisted });
      }
    }
  }, [sessionId, enablePersistence, loadProgress]);

  // Save state when it updates
  useEffect(() => {
    if (enablePersistence && state.sessionId && state.lastUpdate) {
      const progressData: ProgressResponse = {
        sessionId: state.sessionId,
        overallPercentage: state.overall.percentage,
        currentPhase: state.overall.phase,
        phases: state.phases,
        lastUpdate: state.lastUpdate,
        statusMessage: state.statusMessage,
        error: state.error || undefined
      };
      saveProgress(progressData);
    }
  }, [state, enablePersistence, saveProgress]);

  /**
   * Fetch progress via HTTP
   */
  const fetchProgress = useCallback(async () => {
    if (!sessionId) return;

    try {
      dispatch({ type: 'SET_LOADING', payload: true });

      const response = await fetch(`/api/sessions/${sessionId}/progress`);
      if (!response.ok) {
        throw new Error(`Failed to fetch progress: ${response.statusText}`);
      }

      const data: ProgressResponse = await response.json();
      dispatch({ type: 'SET_PROGRESS', payload: data });

      // Check for completion or error
      if (data.currentPhase === 'completed') {
        onComplete?.();
      } else if (data.error) {
        onError?.(data.error);
      }
    } catch (error) {
      console.error('Error fetching progress:', error);
      dispatch({
        type: 'SET_ERROR',
        payload: {
          type: 'FetchError',
          message: error instanceof Error ? error.message : 'Failed to fetch progress',
          context: { sessionId },
          timestamp: new Date().toISOString()
        }
      });
    }
  }, [sessionId, onComplete, onError]);

  /**
   * SSE URL for streaming updates
   */
  const sseUrl = useMemo(() => {
    return enableSSE && sessionId
      ? `/api/sessions/${sessionId}/progress/stream`
      : null;
  }, [enableSSE, sessionId]);

  /**
   * Handle SSE messages
   */
  const handleSSEMessage = useCallback((event: MessageEvent) => {
    try {
      if (event.type === 'progress') {
        const data = event.data as ProgressResponse;
        dispatch({ type: 'SET_PROGRESS', payload: data });
      } else if (event.type === 'complete') {
        dispatch({ type: 'SET_CONNECTION_STATE', payload: 'disconnected' });
        onComplete?.();
      } else if (event.type === 'error') {
        const error = event.data as { error: string; context?: any };
        dispatch({
          type: 'SET_ERROR',
          payload: {
            type: 'StreamError',
            message: error.error,
            context: error.context || {},
            timestamp: new Date().toISOString()
          }
        });
        onError?.(state.error!);
      }
    } catch (error) {
      console.error('Error handling SSE message:', error);
    }
  }, [onComplete, onError, state.error]);

  /**
   * SSE connection management
   */
  const {
    connectionState,
    connect: sseConnect,
    disconnect: sseDisconnect
  } = useSSE(sseUrl, {
    onMessage: handleSSEMessage,
    onOpen: () => dispatch({ type: 'SET_CONNECTION_STATE', payload: 'connected' }),
    onClose: () => dispatch({ type: 'SET_CONNECTION_STATE', payload: 'disconnected' }),
    onError: () => dispatch({ type: 'SET_CONNECTION_STATE', payload: 'error' })
  });

  // Update connection state
  useEffect(() => {
    dispatch({ type: 'SET_CONNECTION_STATE', payload: connectionState });
  }, [connectionState]);

  /**
   * Polling effect
   */
  useEffect(() => {
    if (!enablePolling || !sessionId) return;

    // Initial fetch
    fetchProgress();

    // Set up polling interval
    const intervalId = setInterval(fetchProgress, pollingInterval);

    return () => {
      clearInterval(intervalId);
    };
  }, [enablePolling, sessionId, pollingInterval, fetchProgress]);

  /**
   * Public API
   */
  const connect = useCallback(() => {
    if (enableSSE) {
      sseConnect();
    }
  }, [enableSSE, sseConnect]);

  const disconnect = useCallback(() => {
    if (enableSSE) {
      sseDisconnect();
    }
  }, [enableSSE, sseDisconnect]);

  const refresh = useCallback(async () => {
    await fetchProgress();
  }, [fetchProgress]);

  const clearError = useCallback(() => {
    dispatch({ type: 'CLEAR_ERROR' });
  }, []);

  const reset = useCallback(() => {
    dispatch({ type: 'RESET' });
    if (enablePersistence) {
      clearProgress();
    }
  }, [enablePersistence, clearProgress]);

  return {
    state,
    connect,
    disconnect,
    refresh,
    clearError,
    reset
  };
}