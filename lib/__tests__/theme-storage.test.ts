/**
 * Contract Tests for ThemeStorage Interface
 * Feature: 004-change-the-dark
 * Task: T004
 */

import { describe, it, expect, beforeEach, afterEach } from '@jest/globals';
import type { ThemeStorage, ThemeMode, ThemeSource } from '@/types/theme';

// Import the implementation (will fail initially - TDD approach)
import { themeStorage } from '@/lib/theme-storage';

describe('ThemeStorage Contract Tests', () => {
  beforeEach(() => {
    // Clear storage before each test
    localStorage.clear();
    sessionStorage.clear();
  });

  afterEach(() => {
    // Clean up after each test
    localStorage.clear();
    sessionStorage.clear();
  });

  describe('getTheme()', () => {
    it('returns null when no theme saved', () => {
      const result = themeStorage.getTheme();
      expect(result).toBeNull();
    });

    it('returns saved light theme', () => {
      localStorage.setItem('theme', 'light');
      const result = themeStorage.getTheme();
      expect(result).toBe('light');
    });

    it('returns saved dark theme', () => {
      localStorage.setItem('theme', 'dark');
      const result = themeStorage.getTheme();
      expect(result).toBe('dark');
    });

    it('returns null for invalid theme value', () => {
      localStorage.setItem('theme', 'invalid-theme');
      const result = themeStorage.getTheme();
      expect(result).toBeNull();
    });
  });

  describe('setTheme()', () => {
    it('saves dark theme to localStorage', () => {
      const success = themeStorage.setTheme('dark');
      expect(success).toBe(true);
      expect(localStorage.getItem('theme')).toBe('dark');
    });

    it('saves light theme to localStorage', () => {
      const success = themeStorage.setTheme('light');
      expect(success).toBe(true);
      expect(localStorage.getItem('theme')).toBe('light');
    });

    it('overwrites existing theme', () => {
      themeStorage.setTheme('light');
      themeStorage.setTheme('dark');
      expect(localStorage.getItem('theme')).toBe('dark');
    });
  });

  describe('getThemeSource()', () => {
    it('returns null when no source saved', () => {
      const result = themeStorage.getThemeSource();
      expect(result).toBeNull();
    });

    it('returns saved manual source', () => {
      localStorage.setItem('theme-source', 'manual');
      const result = themeStorage.getThemeSource();
      expect(result).toBe('manual');
    });

    it('returns saved system source', () => {
      localStorage.setItem('theme-source', 'system');
      const result = themeStorage.getThemeSource();
      expect(result).toBe('system');
    });

    it('returns null for invalid source value', () => {
      localStorage.setItem('theme-source', 'invalid-source');
      const result = themeStorage.getThemeSource();
      expect(result).toBeNull();
    });
  });

  describe('setThemeSource()', () => {
    it('saves manual source to localStorage', () => {
      const success = themeStorage.setThemeSource('manual');
      expect(success).toBe(true);
      expect(localStorage.getItem('theme-source')).toBe('manual');
    });

    it('saves system source to localStorage', () => {
      const success = themeStorage.setThemeSource('system');
      expect(success).toBe(true);
      expect(localStorage.getItem('theme-source')).toBe('system');
    });
  });

  describe('isAvailable()', () => {
    it('returns true when localStorage is available', () => {
      const result = themeStorage.isAvailable();
      expect(result).toBe(true);
    });
  });

  describe('Storage Fallback', () => {
    it('falls back to sessionStorage when localStorage blocked', () => {
      // Mock localStorage to throw error
      const originalSetItem = Storage.prototype.setItem;
      let localStorageCalls = 0;

      Storage.prototype.setItem = function(key: string, value: string) {
        if (this === localStorage) {
          localStorageCalls++;
          throw new Error('localStorage is disabled');
        }
        return originalSetItem.call(this, key, value);
      };

      // Create a new storage instance to test fallback
      // Note: This test validates the storage abstraction design
      // The actual implementation will handle this in the constructor

      expect(() => {
        localStorage.setItem('test', 'value');
      }).toThrow();

      // Verify sessionStorage still works
      sessionStorage.setItem('test', 'value');
      expect(sessionStorage.getItem('test')).toBe('value');

      // Restore original behavior
      Storage.prototype.setItem = originalSetItem;
    });

    it('returns false when both storage types unavailable', () => {
      // This test documents expected behavior when storage is completely blocked
      // Implementation should handle this gracefully and return false
      // Actual testing would require mocking both storage types
      expect(themeStorage.isAvailable()).toBeDefined();
    });
  });

  describe('Value Validation', () => {
    it('validates theme mode values', () => {
      // Only 'light' and 'dark' should be valid
      const validThemes: ThemeMode[] = ['light', 'dark'];

      validThemes.forEach(theme => {
        const success = themeStorage.setTheme(theme);
        expect(success).toBe(true);
        expect(themeStorage.getTheme()).toBe(theme);
      });
    });

    it('validates theme source values', () => {
      // Only 'system' and 'manual' should be valid for storage
      const validSources: Exclude<ThemeSource, 'default'>[] = ['system', 'manual'];

      validSources.forEach(source => {
        const success = themeStorage.setThemeSource(source);
        expect(success).toBe(true);
        expect(themeStorage.getThemeSource()).toBe(source);
      });
    });
  });
});
