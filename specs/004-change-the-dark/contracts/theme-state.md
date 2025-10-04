# Theme State Management Contract

**Feature**: 004-change-the-dark
**Module**: `lib/theme-storage.ts`, `lib/theme-detection.ts`
**Date**: 2025-10-04

## Overview

Defines the contracts for theme state management, including storage abstraction and system preference detection.

---

## 1. Storage Abstraction (`lib/theme-storage.ts`)

### Interface: `ThemeStorage`

```typescript
interface ThemeStorage {
  /**
   * Retrieve the saved theme mode
   * @returns Saved theme or null if not found/invalid
   */
  getTheme(): 'light' | 'dark' | null;

  /**
   * Save the theme mode
   * @param theme - Theme mode to save
   * @returns true if saved successfully, false if storage unavailable
   */
  setTheme(theme: 'light' | 'dark'): boolean;

  /**
   * Retrieve the theme source (how it was set)
   * @returns Saved source or null if not found
   */
  getThemeSource(): 'system' | 'manual' | null;

  /**
   * Save the theme source
   * @param source - Source type to save
   * @returns true if saved successfully, false if storage unavailable
   */
  setThemeSource(source: 'system' | 'manual'): boolean;

  /**
   * Check if storage is available
   * @returns true if localStorage or sessionStorage accessible
   */
  isAvailable(): boolean;
}
```

### Implementation: `BrowserThemeStorage`

```typescript
export class BrowserThemeStorage implements ThemeStorage {
  private storage: Storage | null;

  constructor() {
    this.storage = this.detectStorage();
  }

  /**
   * Detect available storage (localStorage → sessionStorage → null)
   */
  private detectStorage(): Storage | null;

  /**
   * Validate theme mode value
   */
  private isValidTheme(value: unknown): value is 'light' | 'dark';

  /**
   * Validate theme source value
   */
  private isValidSource(value: unknown): value is 'system' | 'manual';

  // Interface method implementations...
}
```

### Export

```typescript
// Singleton instance
export const themeStorage = new BrowserThemeStorage();
```

### Usage

```typescript
import { themeStorage } from '@/lib/theme-storage';

// Save theme preference
const success = themeStorage.setTheme('dark');
if (success) {
  themeStorage.setThemeSource('manual');
}

// Retrieve preference
const saved = themeStorage.getTheme();  // 'dark' | 'light' | null
const source = themeStorage.getThemeSource();  // 'system' | 'manual' | null

// Check availability
if (themeStorage.isAvailable()) {
  console.log('Theme will persist across sessions');
} else {
  console.warn('Theme will reset on page reload');
}
```

### Storage Keys

| Key | Value | Description |
|-----|-------|-------------|
| `theme` | `'light' \| 'dark'` | Current theme mode |
| `theme-source` | `'system' \| 'manual'` | How theme was determined |

### Error Handling

```typescript
// All methods use try-catch internally
setTheme(theme: 'light' | 'dark'): boolean {
  if (!this.storage) return false;

  try {
    this.storage.setItem('theme', theme);
    return true;
  } catch (error) {
    console.warn('Failed to save theme:', error);
    return false;
  }
}
```

### Storage Fallback Behavior

| Scenario | Behavior |
|----------|----------|
| localStorage available | Use localStorage (persists indefinitely) |
| localStorage blocked, sessionStorage available | Use sessionStorage (persists for session) |
| Both unavailable | Return false from `setTheme()`, in-memory only |
| Storage quota exceeded | Fall back to sessionStorage, then in-memory |

---

## 2. System Preference Detection (`lib/theme-detection.ts`)

### Extend Existing Module

**Current File**: `lib/theme-detection.ts` (OKLCH detection only)

**Add Functions**:

```typescript
/**
 * Detect the user's system theme preference
 * @returns 'dark' if system prefers dark mode, 'light' otherwise
 */
export function detectSystemTheme(): 'light' | 'dark';

/**
 * Watch for system theme preference changes
 * @param callback - Called when system preference changes
 * @returns Cleanup function to remove listener
 */
export function watchSystemTheme(
  callback: (theme: 'light' | 'dark') => void
): () => void;
```

### Implementation Details

```typescript
export function detectSystemTheme(): 'light' | 'dark' {
  // SSR safety
  if (typeof window === 'undefined') return 'light';

  try {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    return mediaQuery.matches ? 'dark' : 'light';
  } catch (error) {
    console.warn('Failed to detect system theme:', error);
    return 'light';  // Fallback to light
  }
}

export function watchSystemTheme(
  callback: (theme: 'light' | 'dark') => void
): () => void {
  // SSR safety
  if (typeof window === 'undefined') return () => {};

  try {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    const handler = (e: MediaQueryListEvent | MediaQueryList) => {
      callback(e.matches ? 'dark' : 'light');
    };

    // Modern browsers
    mediaQuery.addEventListener('change', handler);

    // Return cleanup function
    return () => {
      mediaQuery.removeEventListener('change', handler);
    };
  } catch (error) {
    console.warn('Failed to watch system theme:', error);
    return () => {};  // No-op cleanup
  }
}
```

### Usage in Component

```typescript
import { detectSystemTheme, watchSystemTheme } from '@/lib/theme-detection';

function ThemeToggle() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    // Get initial system preference
    const systemTheme = detectSystemTheme();

    // Check for saved manual preference
    const saved = themeStorage.getTheme();
    const source = themeStorage.getThemeSource();

    if (saved && source === 'manual') {
      setTheme(saved);  // Manual overrides system
    } else {
      setTheme(systemTheme);
    }

    // Watch for system changes (only if not manual)
    const cleanup = watchSystemTheme((newTheme) => {
      if (themeStorage.getThemeSource() !== 'manual') {
        setTheme(newTheme);
        applyTheme(newTheme);
      }
    });

    return cleanup;  // Remove listener on unmount
  }, []);

  // ...
}
```

### Browser Compatibility

| Browser | `matchMedia` Support | `addEventListener('change')` |
|---------|----------------------|------------------------------|
| Chrome | ✅ 76+ | ✅ 76+ |
| Safari | ✅ 14+ | ✅ 14+ |
| Firefox | ✅ 67+ | ✅ 67+ |
| Edge | ✅ 79+ | ✅ 79+ |

**Fallback**: If `matchMedia` unavailable, defaults to `'light'`.

---

## 3. Theme Application

### DOM Manipulation

```typescript
/**
 * Apply theme to document
 * @param mode - Theme mode to apply
 */
export function applyTheme(mode: 'light' | 'dark'): void {
  if (typeof document === 'undefined') return;  // SSR safety

  if (mode === 'dark') {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
}
```

### CSS Integration

**Existing CSS** (`app/globals.css`):
```css
:root {
  --background: oklch(1 0 0);
  /* Light mode variables */
}

.dark {
  --background: oklch(0.145 0 0);
  /* Dark mode variables */
}
```

**No changes needed to CSS** - class toggle is sufficient.

---

## 4. Complete Flow Example

### Initial Load

```typescript
function initializeTheme(): 'light' | 'dark' {
  // 1. Check for saved manual preference (highest priority)
  const saved = themeStorage.getTheme();
  const source = themeStorage.getThemeSource();

  if (saved && source === 'manual') {
    applyTheme(saved);
    return saved;
  }

  // 2. Check system preference
  const systemTheme = detectSystemTheme();
  applyTheme(systemTheme);

  // Save as system source
  themeStorage.setTheme(systemTheme);
  themeStorage.setThemeSource('system');

  return systemTheme;
}
```

### User Toggle

```typescript
function toggleTheme(currentTheme: 'light' | 'dark'): 'light' | 'dark' {
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

  // Apply to DOM
  applyTheme(newTheme);

  // Save as manual preference
  themeStorage.setTheme(newTheme);
  themeStorage.setThemeSource('manual');

  return newTheme;
}
```

### System Preference Change

```typescript
useEffect(() => {
  const cleanup = watchSystemTheme((newSystemTheme) => {
    const source = themeStorage.getThemeSource();

    // Only apply if NOT manual override
    if (source !== 'manual') {
      applyTheme(newSystemTheme);
      setTheme(newSystemTheme);

      // Update storage (still system source)
      themeStorage.setTheme(newSystemTheme);
      themeStorage.setThemeSource('system');
    }
  });

  return cleanup;
}, []);
```

---

## 5. Type Definitions

### Complete Types

```typescript
// Theme mode (light or dark)
type ThemeMode = 'light' | 'dark';

// How theme was determined
type ThemeSource = 'system' | 'manual' | 'default';

// Complete theme state
interface ThemeState {
  mode: ThemeMode;
  source: ThemeSource;
  storageAvailable: boolean;
}

// Storage abstraction interface
interface ThemeStorage {
  getTheme(): ThemeMode | null;
  setTheme(theme: ThemeMode): boolean;
  getThemeSource(): Exclude<ThemeSource, 'default'> | null;
  setThemeSource(source: Exclude<ThemeSource, 'default'>): boolean;
  isAvailable(): boolean;
}
```

---

## 6. Testing Contract

### `lib/theme-storage.ts` Tests

```typescript
describe('BrowserThemeStorage', () => {
  it('saves and retrieves theme from localStorage', () => {
    const storage = new BrowserThemeStorage();
    storage.setTheme('dark');
    expect(storage.getTheme()).toBe('dark');
  });

  it('returns null when no theme saved', () => {
    const storage = new BrowserThemeStorage();
    expect(storage.getTheme()).toBeNull();
  });

  it('validates theme values', () => {
    localStorage.setItem('theme', 'invalid');
    const storage = new BrowserThemeStorage();
    expect(storage.getTheme()).toBeNull();
  });

  it('falls back to sessionStorage when localStorage blocked', () => {
    // Mock localStorage throwing error
    const storage = new BrowserThemeStorage();
    expect(storage.isAvailable()).toBe(true);  // sessionStorage still works
  });

  it('returns false when all storage unavailable', () => {
    // Mock both storage types throwing errors
    const storage = new BrowserThemeStorage();
    expect(storage.setTheme('dark')).toBe(false);
  });
});
```

### `lib/theme-detection.ts` Tests

```typescript
describe('detectSystemTheme', () => {
  it('returns "dark" when system prefers dark', () => {
    window.matchMedia = jest.fn().mockReturnValue({ matches: true });
    expect(detectSystemTheme()).toBe('dark');
  });

  it('returns "light" when system prefers light', () => {
    window.matchMedia = jest.fn().mockReturnValue({ matches: false });
    expect(detectSystemTheme()).toBe('light');
  });

  it('returns "light" when matchMedia unavailable', () => {
    window.matchMedia = undefined;
    expect(detectSystemTheme()).toBe('light');
  });
});

describe('watchSystemTheme', () => {
  it('calls callback when system preference changes', () => {
    const callback = jest.fn();
    const cleanup = watchSystemTheme(callback);

    // Simulate system theme change
    const changeEvent = new MediaQueryListEvent('change', { matches: true });
    window.dispatchEvent(changeEvent);

    expect(callback).toHaveBeenCalledWith('dark');
    cleanup();
  });

  it('cleanup removes event listener', () => {
    const callback = jest.fn();
    const cleanup = watchSystemTheme(callback);
    cleanup();

    // Event should not trigger after cleanup
    const changeEvent = new MediaQueryListEvent('change', { matches: true });
    window.dispatchEvent(changeEvent);

    expect(callback).not.toHaveBeenCalled();
  });
});
```

---

## 7. Migration Notes

### Existing Code Removal

**Remove from `index.html`**:
- Lines 439-460: `initThemeToggle()` function
- All references to `appState.isDark`

### Preserve Behavior

**Keep**:
- CSS variables in `app/globals.css` (no changes needed)
- `.dark` class application to `<html>` element
- OKLCH compatibility warning (separate concern)

**Enhance**:
- Add system preference detection
- Add storage fallback layer
- Add manual override priority logic

---

**Contract Status**: ✅ COMPLETE
**Related**: [component-api.md](./component-api.md), [../data-model.md](../data-model.md)
