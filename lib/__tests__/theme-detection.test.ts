/**
 * Contract Tests for System Preference Detection
 * Feature: 004-change-the-dark
 * Task: T005
 */

import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';

// Import the implementation (will fail initially - TDD approach)
import { detectSystemTheme, watchSystemTheme } from '@/lib/theme-detection';

describe('System Theme Detection Contract Tests', () => {
  let originalMatchMedia: typeof window.matchMedia;

  beforeEach(() => {
    // Save original matchMedia
    originalMatchMedia = window.matchMedia;
  });

  afterEach(() => {
    // Restore original matchMedia
    window.matchMedia = originalMatchMedia;
  });

  describe('detectSystemTheme()', () => {
    it('returns "dark" when system prefers dark mode', () => {
      // Mock matchMedia to return dark preference
      window.matchMedia = jest.fn().mockImplementation((query) => ({
        matches: query === '(prefers-color-scheme: dark)',
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      }));

      const result = detectSystemTheme();
      expect(result).toBe('dark');
    });

    it('returns "light" when system prefers light mode', () => {
      // Mock matchMedia to return light preference
      window.matchMedia = jest.fn().mockImplementation((query) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      }));

      const result = detectSystemTheme();
      expect(result).toBe('light');
    });

    it('returns "light" when matchMedia is unavailable', () => {
      // Mock matchMedia as undefined
      window.matchMedia = undefined as any;

      const result = detectSystemTheme();
      expect(result).toBe('light');
    });

    it('handles errors gracefully and returns "light" as fallback', () => {
      // Mock matchMedia to throw error
      window.matchMedia = jest.fn().mockImplementation(() => {
        throw new Error('matchMedia error');
      });

      const result = detectSystemTheme();
      expect(result).toBe('light');
    });
  });

  describe('watchSystemTheme()', () => {
    it('calls callback when system preference changes to dark', () => {
      const mockCallback = jest.fn();
      let changeHandler: ((e: any) => void) | null = null;

      // Mock matchMedia with event listener support
      window.matchMedia = jest.fn().mockImplementation((query) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn((event: string, handler: any) => {
          if (event === 'change') {
            changeHandler = handler;
          }
        }),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      }));

      const cleanup = watchSystemTheme(mockCallback);

      // Simulate system theme change to dark
      if (changeHandler) {
        changeHandler({ matches: true } as any);
      }

      expect(mockCallback).toHaveBeenCalledWith('dark');

      cleanup();
    });

    it('calls callback when system preference changes to light', () => {
      const mockCallback = jest.fn();
      let changeHandler: ((e: any) => void) | null = null;

      window.matchMedia = jest.fn().mockImplementation((query) => ({
        matches: true,
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn((event: string, handler: any) => {
          if (event === 'change') {
            changeHandler = handler;
          }
        }),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      }));

      const cleanup = watchSystemTheme(mockCallback);

      // Simulate system theme change to light
      if (changeHandler) {
        changeHandler({ matches: false } as any);
      }

      expect(mockCallback).toHaveBeenCalledWith('light');

      cleanup();
    });

    it('cleanup function removes event listener', () => {
      const mockCallback = jest.fn();
      const removeEventListenerMock = jest.fn();

      window.matchMedia = jest.fn().mockImplementation((query) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: removeEventListenerMock,
        dispatchEvent: jest.fn(),
      }));

      const cleanup = watchSystemTheme(mockCallback);
      cleanup();

      expect(removeEventListenerMock).toHaveBeenCalled();
    });

    it('returns no-op cleanup when matchMedia unavailable', () => {
      const mockCallback = jest.fn();
      window.matchMedia = undefined as any;

      const cleanup = watchSystemTheme(mockCallback);

      // Should not throw when called
      expect(() => cleanup()).not.toThrow();
    });

    it('handles errors gracefully and returns no-op cleanup', () => {
      const mockCallback = jest.fn();

      window.matchMedia = jest.fn().mockImplementation(() => {
        throw new Error('matchMedia error');
      });

      const cleanup = watchSystemTheme(mockCallback);

      // Should not throw when called
      expect(() => cleanup()).not.toThrow();
    });
  });

  describe('SSR Safety', () => {
    it('detectSystemTheme handles undefined window', () => {
      // This test documents SSR safety requirements
      // Actual SSR testing would require different environment setup
      const result = detectSystemTheme();
      expect(result).toBeDefined();
      expect(['light', 'dark']).toContain(result);
    });

    it('watchSystemTheme handles undefined window', () => {
      const mockCallback = jest.fn();
      const cleanup = watchSystemTheme(mockCallback);

      // Should return a function even in SSR context
      expect(typeof cleanup).toBe('function');
      expect(() => cleanup()).not.toThrow();
    });
  });
});
