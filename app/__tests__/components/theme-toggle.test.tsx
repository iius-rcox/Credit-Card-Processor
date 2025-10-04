/**
 * Contract Tests for ThemeToggle Component
 * Feature: 004-change-the-dark
 * Task: T006
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import '@testing-library/jest-dom';

// Import the component (will fail initially - TDD approach)
import { ThemeToggle } from '@/components/theme-toggle';

describe('ThemeToggle Component Contract Tests', () => {
  beforeEach(() => {
    // Clear storage and reset DOM
    localStorage.clear();
    sessionStorage.clear();
    document.documentElement.classList.remove('dark');

    // Mock matchMedia
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
  });

  describe('Icon Rendering', () => {
    it('renders Moon icon in light mode', () => {
      render(<ThemeToggle />);

      // Look for button with aria-label indicating light mode
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-label', expect.stringMatching(/dark/i));
    });

    it('renders Sun icon in dark mode', () => {
      // Set up dark mode in localStorage
      localStorage.setItem('theme', 'dark');
      localStorage.setItem('theme-source', 'manual');

      render(<ThemeToggle />);

      // Look for button with aria-label indicating dark mode
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-label', expect.stringMatching(/light/i));
    });
  });

  describe('Theme Toggle Functionality', () => {
    it('toggles theme on click', async () => {
      render(<ThemeToggle />);

      const button = screen.getByRole('button');

      // Initial state should be light mode
      expect(document.documentElement.classList.contains('dark')).toBe(false);

      // Click to toggle
      fireEvent.click(button);

      // Should be dark mode now
      await waitFor(() => {
        expect(document.documentElement.classList.contains('dark')).toBe(true);
      });

      // Click again to toggle back
      fireEvent.click(button);

      // Should be light mode again
      await waitFor(() => {
        expect(document.documentElement.classList.contains('dark')).toBe(false);
      });
    });

    it('saves theme to storage on toggle', () => {
      render(<ThemeToggle />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(localStorage.getItem('theme')).toBe('dark');
      expect(localStorage.getItem('theme-source')).toBe('manual');
    });
  });

  describe('Callback Prop', () => {
    it('calls onThemeChange callback when provided', () => {
      const mockCallback = jest.fn();
      render(<ThemeToggle onThemeChange={mockCallback} />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(mockCallback).toHaveBeenCalledWith('dark');
    });

    it('does not error when callback not provided', () => {
      render(<ThemeToggle />);

      const button = screen.getByRole('button');

      expect(() => {
        fireEvent.click(button);
      }).not.toThrow();
    });
  });

  describe('Keyboard Accessibility', () => {
    it('is focusable via Tab key', () => {
      render(<ThemeToggle />);

      const button = screen.getByRole('button');

      // Button should be in tab order
      expect(button).toHaveAttribute('tabIndex');
    });

    it('toggles theme on Enter key', () => {
      render(<ThemeToggle />);

      const button = screen.getByRole('button');
      button.focus();

      fireEvent.keyDown(button, { key: 'Enter', code: 'Enter' });

      expect(document.documentElement.classList.contains('dark')).toBe(true);
    });

    it('toggles theme on Space key', () => {
      render(<ThemeToggle />);

      const button = screen.getByRole('button');
      button.focus();

      fireEvent.keyDown(button, { key: ' ', code: 'Space' });

      expect(document.documentElement.classList.contains('dark')).toBe(true);
    });
  });

  describe('Tooltip Prop', () => {
    it('shows tooltip when showTooltip=true', async () => {
      render(<ThemeToggle showTooltip={true} />);

      const button = screen.getByRole('button');

      // Hover over button
      fireEvent.mouseEnter(button);

      // Wait for tooltip to appear
      await waitFor(() => {
        const tooltip = screen.queryByRole('tooltip');
        expect(tooltip).toBeInTheDocument();
      });
    });

    it('does not show tooltip when showTooltip=false', async () => {
      render(<ThemeToggle showTooltip={false} />);

      const button = screen.getByRole('button');

      // Hover over button
      fireEvent.mouseEnter(button);

      // Wait a moment
      await new Promise(resolve => setTimeout(resolve, 500));

      // Tooltip should not appear
      const tooltip = screen.queryByRole('tooltip');
      expect(tooltip).not.toBeInTheDocument();
    });
  });

  describe('Custom ClassName Prop', () => {
    it('applies custom className to button', () => {
      render(<ThemeToggle className="custom-class" />);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('custom-class');
    });
  });

  describe('ARIA Attributes', () => {
    it('has proper aria-label', () => {
      render(<ThemeToggle />);

      const button = screen.getByRole('button');
      const ariaLabel = button.getAttribute('aria-label');

      expect(ariaLabel).toBeTruthy();
      expect(ariaLabel).toMatch(/switch to|toggle/i);
    });

    it('updates aria-label when theme changes', async () => {
      render(<ThemeToggle />);

      const button = screen.getByRole('button');
      const initialLabel = button.getAttribute('aria-label');

      fireEvent.click(button);

      await waitFor(() => {
        const newLabel = button.getAttribute('aria-label');
        expect(newLabel).not.toBe(initialLabel);
      });
    });

    it('hides icon from screen readers', () => {
      render(<ThemeToggle />);

      const button = screen.getByRole('button');
      const svg = button.querySelector('svg');

      expect(svg).toHaveAttribute('aria-hidden', 'true');
    });
  });

  describe('Responsive Sizing', () => {
    it('applies responsive size classes', () => {
      render(<ThemeToggle />);

      const button = screen.getByRole('button');

      // Button should have responsive classes
      const className = button.className;
      expect(className).toMatch(/md:/); // Tailwind responsive breakpoint
    });
  });

  describe('System Preference Detection', () => {
    it('detects dark mode system preference on first load', () => {
      // Mock system dark mode preference
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

      render(<ThemeToggle />);

      // Should apply dark mode from system preference
      expect(document.documentElement.classList.contains('dark')).toBe(true);
    });

    it('manual selection overrides system preference', () => {
      // Mock system dark mode preference
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

      // Set manual light mode preference
      localStorage.setItem('theme', 'light');
      localStorage.setItem('theme-source', 'manual');

      render(<ThemeToggle />);

      // Should use manual preference (light) instead of system (dark)
      expect(document.documentElement.classList.contains('dark')).toBe(false);
    });
  });
});
