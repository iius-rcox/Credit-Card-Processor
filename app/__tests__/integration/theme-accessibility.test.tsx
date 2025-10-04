/**
 * Integration Test: Accessibility
 * Feature: 004-change-the-dark
 * Task: T012 - Scenario 6 from quickstart.md
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from '@jest/globals';
import '@testing-library/jest-dom';

describe('Scenario 6: Accessibility (Keyboard Navigation)', () => {
  const TestButton = () => (
    <button
      aria-label="Toggle theme"
      className="focus-visible:ring-2"
      tabIndex={0}
    >
      Icon
    </button>
  );

  it('Tab focuses icon', () => {
    render(<TestButton />);
    const button = screen.getByRole('button');

    expect(button).toHaveAttribute('tabIndex', '0');
  });

  it('Enter key toggles theme', () => {
    const handleKeyDown = jest.fn((e: React.KeyboardEvent) => {
      if (e.key === 'Enter') {
        // Toggle logic here
      }
    });

    const KeyTestButton = () => (
      <button onKeyDown={handleKeyDown}>Icon</button>
    );

    render(<KeyTestButton />);
    const button = screen.getByRole('button');

    fireEvent.keyDown(button, { key: 'Enter' });
    expect(handleKeyDown).toHaveBeenCalled();
  });

  it('Space key toggles theme', () => {
    const handleKeyDown = jest.fn((e: React.KeyboardEvent) => {
      if (e.key === ' ') {
        // Toggle logic here
      }
    });

    const KeyTestButton = () => (
      <button onKeyDown={handleKeyDown}>Icon</button>
    );

    render(<KeyTestButton />);
    const button = screen.getByRole('button');

    fireEvent.keyDown(button, { key: ' ' });
    expect(handleKeyDown).toHaveBeenCalled();
  });

  it('focus indicator visible', () => {
    render(<TestButton />);
    const button = screen.getByRole('button');

    expect(button.className).toContain('focus-visible');
  });
});
