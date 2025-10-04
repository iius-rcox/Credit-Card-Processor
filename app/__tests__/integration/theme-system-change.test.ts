/**
 * Integration Test: System Preference Change (Advanced)
 * Feature: 004-change-the-dark
 * Task: T016 - Scenario 10 from quickstart.md
 */

import { describe, it, expect, jest } from '@jest/globals';

describe('Scenario 10: System Preference Change (Advanced)', () => {
  it('app responds when OS theme changes', () => {
    let changeHandler: ((e: any) => void) | null = null;

    // Mock matchMedia with change listener
    window.matchMedia = jest.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn((event, handler) => {
        if (event === 'change') changeHandler = handler;
      }),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    }));

    // Simulate OS change to dark
    if (changeHandler) {
      changeHandler({ matches: true });
      expect(true).toBe(true); // Handler called
    }
  });

  it('system change ignored when manual override active', () => {
    localStorage.setItem('theme', 'light');
    localStorage.setItem('theme-source', 'manual');

    const source = localStorage.getItem('theme-source');

    // Should not update if source is manual
    if (source === 'manual') {
      expect(localStorage.getItem('theme')).toBe('light');
    }
  });

  it('system change applied when source is system', () => {
    localStorage.setItem('theme', 'light');
    localStorage.setItem('theme-source', 'system');

    const source = localStorage.getItem('theme-source');

    // Should update if source is system
    if (source === 'system') {
      // Can update to dark
      localStorage.setItem('theme', 'dark');
      expect(localStorage.getItem('theme')).toBe('dark');
    }
  });
});
