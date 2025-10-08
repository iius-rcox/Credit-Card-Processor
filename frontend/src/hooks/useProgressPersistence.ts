/**
 * Custom hook for persisting progress state to localStorage.
 *
 * This hook provides functions to save, load, and clear progress data
 * from localStorage, enabling progress recovery after page refresh.
 */

import { useCallback } from 'react';
import { ProgressResponse } from '../types/progress';

const STORAGE_PREFIX = 'credit_card_progress_';
const STORAGE_EXPIRY_MS = 30 * 60 * 1000; // 30 minutes

interface StoredProgress {
  data: ProgressResponse;
  timestamp: number;
}

/**
 * Custom hook for managing progress persistence
 *
 * @param sessionId - The session ID to use as storage key
 * @returns Functions to save, load, and clear persisted progress
 */
export function useProgressPersistence(sessionId: string) {
  const storageKey = `${STORAGE_PREFIX}${sessionId}`;

  /**
   * Save progress to localStorage
   */
  const saveProgress = useCallback((progress: ProgressResponse) => {
    if (!sessionId) return;

    try {
      const storedData: StoredProgress = {
        data: progress,
        timestamp: Date.now()
      };

      localStorage.setItem(storageKey, JSON.stringify(storedData));
    } catch (error) {
      console.error('Failed to save progress to localStorage:', error);
    }
  }, [sessionId, storageKey]);

  /**
   * Load progress from localStorage
   */
  const loadProgress = useCallback((): ProgressResponse | null => {
    if (!sessionId) return null;

    try {
      const stored = localStorage.getItem(storageKey);
      if (!stored) return null;

      const parsed: StoredProgress = JSON.parse(stored);

      // Check if data is expired
      const age = Date.now() - parsed.timestamp;
      if (age > STORAGE_EXPIRY_MS) {
        console.debug('Stored progress expired, removing');
        localStorage.removeItem(storageKey);
        return null;
      }

      // Don't restore if processing is complete or failed
      if (parsed.data.currentPhase === 'completed' ||
          parsed.data.currentPhase === 'failed') {
        console.debug('Session already completed/failed, not restoring');
        localStorage.removeItem(storageKey);
        return null;
      }

      return parsed.data;
    } catch (error) {
      console.error('Failed to load progress from localStorage:', error);
      return null;
    }
  }, [sessionId, storageKey]);

  /**
   * Clear progress from localStorage
   */
  const clearProgress = useCallback(() => {
    if (!sessionId) return;

    try {
      localStorage.removeItem(storageKey);
    } catch (error) {
      console.error('Failed to clear progress from localStorage:', error);
    }
  }, [sessionId, storageKey]);

  /**
   * Clear all expired progress entries (housekeeping)
   */
  const clearExpiredProgress = useCallback(() => {
    try {
      const keys = Object.keys(localStorage);
      const now = Date.now();

      keys.forEach(key => {
        if (key.startsWith(STORAGE_PREFIX)) {
          try {
            const stored = localStorage.getItem(key);
            if (stored) {
              const parsed: StoredProgress = JSON.parse(stored);
              const age = now - parsed.timestamp;

              if (age > STORAGE_EXPIRY_MS) {
                localStorage.removeItem(key);
                console.debug(`Removed expired progress: ${key}`);
              }
            }
          } catch (error) {
            // If we can't parse it, remove it
            localStorage.removeItem(key);
          }
        }
      });
    } catch (error) {
      console.error('Failed to clear expired progress:', error);
    }
  }, []);

  /**
   * Get all active sessions from localStorage
   */
  const getAllActiveSessions = useCallback((): string[] => {
    try {
      const keys = Object.keys(localStorage);
      const sessions: string[] = [];

      keys.forEach(key => {
        if (key.startsWith(STORAGE_PREFIX)) {
          const sessionId = key.replace(STORAGE_PREFIX, '');
          const stored = localStorage.getItem(key);

          if (stored) {
            try {
              const parsed: StoredProgress = JSON.parse(stored);
              const age = Date.now() - parsed.timestamp;

              if (age <= STORAGE_EXPIRY_MS &&
                  parsed.data.currentPhase !== 'completed' &&
                  parsed.data.currentPhase !== 'failed') {
                sessions.push(sessionId);
              }
            } catch (error) {
              // Skip invalid entries
            }
          }
        }
      });

      return sessions;
    } catch (error) {
      console.error('Failed to get active sessions:', error);
      return [];
    }
  }, []);

  return {
    saveProgress,
    loadProgress,
    clearProgress,
    clearExpiredProgress,
    getAllActiveSessions
  };
}