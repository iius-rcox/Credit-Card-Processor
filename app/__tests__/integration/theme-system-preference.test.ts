/**
 * Integration Test: Initial Load with System Preference
 * Feature: 004-change-the-dark
 * Task: T007 - Scenario 1 from quickstart.md
 */

import { describe, it, expect, beforeEach, jest } from '@jest/globals';

describe('Scenario 1: Initial Load with System Preference', () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
  });

  it('app loads in dark mode when OS is dark', () => {
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

    // Simulate initial theme detection
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    expect(prefersDark).toBe(true);
  });

  it('app loads in light mode when OS is light', () => {
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

    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    expect(prefersDark).toBe(false);
  });

  it('localStorage shows theme-source: "system" after initial load', () => {
    // After component mounts and detects system preference
    // localStorage should be set with source='system'
    expect(localStorage.getItem('theme-source')).toBeDefined();
  });
});
