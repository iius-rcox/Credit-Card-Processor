/**
 * Browser OKLCH Color Support Detection Utility
 *
 * Detects browser support for OKLCH color format and manages compatibility warnings.
 * Implements graceful degradation for unsupported browsers.
 *
 * Extended with System Theme Preference Detection
 * Feature: 004-change-the-dark (Task T018)
 */

import type { ThemeMode } from '@/types/theme';

export interface BrowserCompatibility {
  supportsOKLCH: boolean;
  warningDisplayed: boolean;
  warningDismissed: boolean;
}

const STORAGE_KEY = 'oklch-warning-dismissed';

/**
 * Detects if the current browser supports OKLCH color format
 * @returns true if OKLCH is supported, false otherwise
 */
export function supportsOKLCH(): boolean {
  // Check if CSS.supports API is available
  if (typeof CSS === 'undefined' || typeof CSS.supports !== 'function') {
    return false;
  }

  try {
    // Test OKLCH color format support
    return CSS.supports('color', 'oklch(0.5 0.2 180)');
  } catch (error) {
    // Fallback for browsers that might throw errors
    console.warn('Error checking OKLCH support:', error);
    return false;
  }
}

/**
 * Checks if the compatibility warning has been dismissed by the user
 * @returns true if the warning was previously dismissed
 */
export function isWarningDismissed(): boolean {
  if (typeof localStorage === 'undefined') {
    return false;
  }

  try {
    return localStorage.getItem(STORAGE_KEY) === 'true';
  } catch (error) {
    // Handle cases where localStorage might not be available
    console.warn('Error accessing localStorage:', error);
    return false;
  }
}

/**
 * Marks the compatibility warning as dismissed
 */
export function dismissWarning(): void {
  if (typeof localStorage === 'undefined') {
    return;
  }

  try {
    localStorage.setItem(STORAGE_KEY, 'true');
  } catch (error) {
    console.warn('Error saving warning dismissal:', error);
  }
}

/**
 * Resets the warning dismissal state (useful for testing)
 */
export function resetWarningDismissal(): void {
  if (typeof localStorage === 'undefined') {
    return;
  }

  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    console.warn('Error resetting warning dismissal:', error);
  }
}

/**
 * Gets comprehensive browser compatibility information
 * @returns BrowserCompatibility object with support and warning state
 */
export function getBrowserCompatibility(): BrowserCompatibility {
  const hasOKLCHSupport = supportsOKLCH();
  const wasDismissed = isWarningDismissed();

  return {
    supportsOKLCH: hasOKLCHSupport,
    warningDisplayed: !hasOKLCHSupport && !wasDismissed,
    warningDismissed: wasDismissed,
  };
}

/**
 * Determines if a compatibility warning should be shown to the user
 * @returns true if warning should be displayed
 */
export function shouldShowCompatibilityWarning(): boolean {
  return !supportsOKLCH() && !isWarningDismissed();
}

/**
 * Gets browser-specific information for debugging
 * @returns Object with browser capabilities and version info
 */
export function getBrowserInfo(): {
  userAgent: string;
  supportsOKLCH: boolean;
  supportsCSSSupports: boolean;
  hasLocalStorage: boolean;
} {
  return {
    userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'Unknown',
    supportsOKLCH: supportsOKLCH(),
    supportsCSSSupports: typeof CSS !== 'undefined' && typeof CSS.supports === 'function',
    hasLocalStorage: typeof localStorage !== 'undefined',
  };
}

/**
 * Runs a complete compatibility check and returns actionable information
 * @returns Object with compatibility status and recommended actions
 */
export function runCompatibilityCheck(): {
  isCompatible: boolean;
  shouldWarn: boolean;
  canDismiss: boolean;
  message?: string;
  action?: 'none' | 'warn' | 'degrade';
} {
  const compat = getBrowserCompatibility();

  if (compat.supportsOKLCH) {
    return {
      isCompatible: true,
      shouldWarn: false,
      canDismiss: false,
      action: 'none',
    };
  }

  if (compat.warningDismissed) {
    return {
      isCompatible: false,
      shouldWarn: false,
      canDismiss: true,
      message: 'Your browser has limited color support. Colors may appear different.',
      action: 'degrade',
    };
  }

  return {
    isCompatible: false,
    shouldWarn: true,
    canDismiss: true,
    message: 'Your browser has limited color support. The interface may look different, but all functionality will work normally.',
    action: 'warn',
  };
}

// ============================================================================
// System Theme Preference Detection
// Feature: 004-change-the-dark (Task T018)
// ============================================================================

/**
 * Detects the user's system theme preference using matchMedia API
 * @returns 'dark' if system prefers dark mode, 'light' otherwise
 */
export function detectSystemTheme(): ThemeMode {
  // SSR safety check
  if (typeof window === 'undefined') {
    return 'light';
  }

  try {
    // Check if matchMedia is available
    if (typeof window.matchMedia !== 'function') {
      console.warn('matchMedia API not available, defaulting to light theme');
      return 'light';
    }

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    return mediaQuery.matches ? 'dark' : 'light';
  } catch (error) {
    console.error('Error detecting system theme preference:', error);
    return 'light'; // Fallback to light mode
  }
}

/**
 * Watches for system theme preference changes and calls callback when changed
 * @param callback - Function called when system preference changes
 * @returns Cleanup function to remove the event listener
 */
export function watchSystemTheme(
  callback: (theme: ThemeMode) => void
): () => void {
  // SSR safety check
  if (typeof window === 'undefined') {
    return () => {}; // No-op cleanup
  }

  try {
    // Check if matchMedia is available
    if (typeof window.matchMedia !== 'function') {
      console.warn('matchMedia API not available, cannot watch system theme changes');
      return () => {}; // No-op cleanup
    }

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    // Event handler for theme changes
    const handler = (e: MediaQueryListEvent | MediaQueryList) => {
      const newTheme: ThemeMode = e.matches ? 'dark' : 'light';
      callback(newTheme);
    };

    // Add event listener (modern browsers)
    mediaQuery.addEventListener('change', handler as EventListener);

    // Return cleanup function
    return () => {
      mediaQuery.removeEventListener('change', handler as EventListener);
    };
  } catch (error) {
    console.error('Error watching system theme changes:', error);
    return () => {}; // No-op cleanup
  }
}