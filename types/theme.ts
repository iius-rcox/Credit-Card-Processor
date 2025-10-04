/**
 * Theme Type Definitions
 * Feature: 004-change-the-dark
 */

/**
 * Theme mode - light or dark color scheme
 */
export type ThemeMode = 'light' | 'dark';

/**
 * Theme source - how the theme was determined
 * - 'system': Detected from OS/browser preference
 * - 'manual': Explicitly set by user
 * - 'default': Fallback when no preference detected
 */
export type ThemeSource = 'system' | 'manual' | 'default';

/**
 * Complete theme state including mode, source, and storage availability
 */
export interface ThemeState {
  /** Current active theme mode */
  mode: ThemeMode;
  /** Origin of the current theme setting */
  source: ThemeSource;
  /** Whether browser storage is available for persistence */
  storageAvailable: boolean;
}

/**
 * Storage abstraction interface for theme persistence
 */
export interface ThemeStorage {
  /**
   * Retrieve the saved theme mode
   * @returns Saved theme or null if not found/invalid
   */
  getTheme(): ThemeMode | null;

  /**
   * Save the theme mode
   * @param theme - Theme mode to save
   * @returns true if saved successfully, false if storage unavailable
   */
  setTheme(theme: ThemeMode): boolean;

  /**
   * Retrieve the theme source (how it was set)
   * @returns Saved source or null if not found
   */
  getThemeSource(): Exclude<ThemeSource, 'default'> | null;

  /**
   * Save the theme source
   * @param source - Source type to save
   * @returns true if saved successfully, false if storage unavailable
   */
  setThemeSource(source: Exclude<ThemeSource, 'default'>): boolean;

  /**
   * Check if storage is available
   * @returns true if localStorage or sessionStorage accessible
   */
  isAvailable(): boolean;
}
