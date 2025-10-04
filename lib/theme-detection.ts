/**
 * Browser OKLCH Color Support Detection Utility
 *
 * Detects browser support for OKLCH color format and manages compatibility warnings.
 * Implements graceful degradation for unsupported browsers.
 */

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