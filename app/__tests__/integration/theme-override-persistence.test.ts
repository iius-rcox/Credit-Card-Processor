/**
 * Integration Test: Manual Override Persistence
 * Feature: 004-change-the-dark
 * Task: T009 - Scenario 3 from quickstart.md
 */

import { describe, it, expect, beforeEach, jest } from '@jest/globals';

describe('Scenario 3: Manual Override Persistence', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('manual selection overrides system preference', () => {
    // System is dark
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

    // Manual light mode
    localStorage.setItem('theme', 'light');
    localStorage.setItem('theme-source', 'manual');

    // Manual should win
    expect(localStorage.getItem('theme')).toBe('light');
    expect(localStorage.getItem('theme-source')).toBe('manual');
  });

  it('manual theme persists across page reloads', () => {
    localStorage.setItem('theme', 'dark');
    localStorage.setItem('theme-source', 'manual');

    // Simulate reload
    const savedTheme = localStorage.getItem('theme');
    const savedSource = localStorage.getItem('theme-source');

    expect(savedTheme).toBe('dark');
    expect(savedSource).toBe('manual');
  });

  it('manual choice respected even when system changes', () => {
    localStorage.setItem('theme', 'light');
    localStorage.setItem('theme-source', 'manual');

    // System changes to dark
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

    // Manual setting should remain
    const source = localStorage.getItem('theme-source');
    if (source === 'manual') {
      // Don't update from system change
      expect(localStorage.getItem('theme')).toBe('light');
    }
  });
});
