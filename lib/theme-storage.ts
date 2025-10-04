/**
 * Theme Storage Abstraction Layer
 * Feature: 004-change-the-dark
 * Task: T017
 *
 * Provides localStorage/sessionStorage abstraction with graceful fallback
 */

import type { ThemeMode, ThemeSource, ThemeStorage } from '@/types/theme';

/**
 * Browser-based theme storage implementation
 * Tries localStorage first, falls back to sessionStorage, then in-memory only
 */
class BrowserThemeStorage implements ThemeStorage {
  private storage: Storage | null = null;

  constructor() {
    this.storage = this.detectStorage();
  }

  /**
   * Detect available storage mechanism
   * Priority: localStorage → sessionStorage → null
   */
  private detectStorage(): Storage | null {
    // Try localStorage first
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.setItem('__storage_test__', '1');
        window.localStorage.removeItem('__storage_test__');
        return window.localStorage;
      }
    } catch (error) {
      // localStorage unavailable or blocked
      console.warn('localStorage unavailable, falling back to sessionStorage');
    }

    // Fallback to sessionStorage
    try {
      if (typeof window !== 'undefined' && window.sessionStorage) {
        window.sessionStorage.setItem('__storage_test__', '1');
        window.sessionStorage.removeItem('__storage_test__');
        return window.sessionStorage;
      }
    } catch (error) {
      // sessionStorage also unavailable
      console.warn('sessionStorage unavailable, theme will not persist');
    }

    return null;
  }

  /**
   * Validate theme mode value
   */
  private isValidThemeMode(value: unknown): value is ThemeMode {
    return value === 'light' || value === 'dark';
  }

  /**
   * Validate theme source value
   */
  private isValidThemeSource(value: unknown): value is Exclude<ThemeSource, 'default'> {
    return value === 'system' || value === 'manual';
  }

  /**
   * Get saved theme mode from storage
   */
  getTheme(): ThemeMode | null {
    if (!this.storage) return null;

    try {
      const value = this.storage.getItem('theme');
      if (value && this.isValidThemeMode(value)) {
        return value;
      }
      return null;
    } catch (error) {
      console.error('Failed to read theme from storage:', error);
      return null;
    }
  }

  /**
   * Save theme mode to storage
   */
  setTheme(theme: ThemeMode): boolean {
    if (!this.storage) return false;

    try {
      this.storage.setItem('theme', theme);
      return true;
    } catch (error) {
      console.error('Failed to save theme to storage:', error);
      return false;
    }
  }

  /**
   * Get saved theme source from storage
   */
  getThemeSource(): Exclude<ThemeSource, 'default'> | null {
    if (!this.storage) return null;

    try {
      const value = this.storage.getItem('theme-source');
      if (value && this.isValidThemeSource(value)) {
        return value;
      }
      return null;
    } catch (error) {
      console.error('Failed to read theme source from storage:', error);
      return null;
    }
  }

  /**
   * Save theme source to storage
   */
  setThemeSource(source: Exclude<ThemeSource, 'default'>): boolean {
    if (!this.storage) return false;

    try {
      this.storage.setItem('theme-source', source);
      return true;
    } catch (error) {
      console.error('Failed to save theme source to storage:', error);
      return false;
    }
  }

  /**
   * Check if storage is available
   */
  isAvailable(): boolean {
    return this.storage !== null;
  }
}

/**
 * Singleton instance for theme storage
 * Use this throughout the application
 */
export const themeStorage = new BrowserThemeStorage();
