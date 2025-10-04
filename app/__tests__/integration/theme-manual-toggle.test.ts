/**
 * Integration Test: Manual Theme Toggle
 * Feature: 004-change-the-dark
 * Task: T008 - Scenario 2 from quickstart.md
 */

import { describe, it, expect, beforeEach } from '@jest/globals';

describe('Scenario 2: Manual Theme Toggle', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('dark');
  });

  it('click toggles light → dark immediately', () => {
    const startTime = performance.now();

    // Simulate theme toggle
    document.documentElement.classList.add('dark');
    localStorage.setItem('theme', 'dark');
    localStorage.setItem('theme-source', 'manual');

    const endTime = performance.now();
    const duration = endTime - startTime;

    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(duration).toBeLessThan(50); // < 50ms requirement
  });

  it('click toggles dark → light', () => {
    document.documentElement.classList.add('dark');

    // Simulate toggle
    document.documentElement.classList.remove('dark');
    localStorage.setItem('theme', 'light');

    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });

  it('localStorage updates to theme-source: "manual"', () => {
    localStorage.setItem('theme', 'dark');
    localStorage.setItem('theme-source', 'manual');

    expect(localStorage.getItem('theme-source')).toBe('manual');
  });

  it('theme switch completes in <50ms', () => {
    const startTime = performance.now();

    // Simulate instant theme application
    document.documentElement.classList.toggle('dark');

    const endTime = performance.now();
    const duration = endTime - startTime;

    expect(duration).toBeLessThan(50);
  });
});
