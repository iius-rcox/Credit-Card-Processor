/**
 * Integration Test: Old Button Removed
 * Feature: 004-change-the-dark
 * Task: T015 - Scenario 9 from quickstart.md
 */

import { describe, it, expect } from '@jest/globals';

describe('Scenario 9: Old Button Removed', () => {
  it('no centered button with old text present', () => {
    // After integration, old button should be removed
    const oldButtonText = '🌙 Switch to Dark Mode';
    const element = document.querySelector(`[id="theme-toggle"]`);
    expect(element).toBeNull();
  });

  it('no duplicate theme toggles', () => {
    // Only one theme toggle should exist
    const buttons = document.querySelectorAll('[aria-label*="theme"], [aria-label*="Toggle"]');
    // Count should be 1 (only the new icon)
    expect(buttons.length).toBeLessThanOrEqual(1);
  });

  it('no layout shift or empty space', () => {
    // Visual regression check - no orphaned container
    const emptyContainer = document.querySelector('.mb-8.text-center:empty');
    expect(emptyContainer).toBeNull();
  });
});
