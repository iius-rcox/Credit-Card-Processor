# Data Model: Dark Mode Toggle

**Feature**: 004-change-the-dark
**Date**: 2025-10-04

## Overview

This data model defines the theme state management for the dark mode toggle feature. The system manages user theme preferences with a priority system: manual user selection > system preference > default (light).

---

## Entities

### 1. ThemeState

Represents the current theme configuration and its source.

**Properties**:
```typescript
interface ThemeState {
  mode: 'light' | 'dark';           // Current active theme
  source: 'system' | 'manual' | 'default';  // How theme was determined
  storageAvailable: boolean;         // Whether persistence is available
}
```

**Field Descriptions**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mode` | `'light' \| 'dark'` | Yes | The currently active theme mode. Controls CSS class on `<html>` element. |
| `source` | `'system' \| 'manual' \| 'default'` | Yes | Origin of the current theme setting. Determines priority when resolving conflicts. |
| `storageAvailable` | `boolean` | Yes | Whether browser storage (localStorage or sessionStorage) is available for persistence. |

**State Values**:

- **mode**:
  - `'light'`: Light color scheme active
  - `'dark'`: Dark color scheme active

- **source**:
  - `'system'`: Theme detected from OS/browser preference (`prefers-color-scheme`)
  - `'manual'`: User explicitly clicked toggle (highest priority)
  - `'default'`: Fallback when no preference detected (light mode)

- **storageAvailable**:
  - `true`: localStorage or sessionStorage accessible for persistence
  - `false`: Storage blocked (private browsing, enterprise policy, quota exceeded)

**Lifecycle**:
```
Initial Load → Determine Source → Set Mode → Persist (if available) → Apply to DOM
     ↓
User Toggle → Set Source='manual' → Toggle Mode → Persist → Apply to DOM
     ↓
Reload → Check Storage → Restore State → Apply to DOM
```

---

## 2. ThemePreference (Persisted Data)

Data structure stored in browser storage (localStorage or sessionStorage).

**Storage Keys**:
```typescript
// Key-value pairs in Web Storage API
'theme': 'light' | 'dark'
'theme-source': 'system' | 'manual'
```

**Storage Schema**:

| Key | Value Type | Example | Description |
|-----|------------|---------|-------------|
| `theme` | `'light' \| 'dark'` | `'dark'` | Last selected theme mode |
| `theme-source` | `'system' \| 'manual'` | `'manual'` | Whether user manually selected or system detected |

**Storage Lifecycle**:

```typescript
// On theme toggle
localStorage.setItem('theme', 'dark');
localStorage.setItem('theme-source', 'manual');

// On initial load
const savedTheme = localStorage.getItem('theme');  // 'dark' | 'light' | null
const savedSource = localStorage.getItem('theme-source');  // 'system' | 'manual' | null

// On storage unavailable (fallback to sessionStorage)
sessionStorage.setItem('theme', 'dark');
sessionStorage.setItem('theme-source', 'manual');
```

**Persistence Behavior**:

| Storage Type | Lifetime | Use Case |
|--------------|----------|----------|
| `localStorage` | Permanent (until cleared) | Normal operation |
| `sessionStorage` | Current tab/window session | Private browsing, localStorage blocked |
| None (in-memory only) | Current page load | Both storage types unavailable |

---

## State Transitions

### Transition Diagram

```
┌─────────────┐
│  App Loads  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│ Check localStorage/session  │
└──────┬─────────────┬────────┘
       │             │
    Found         Not Found
       │             │
       ▼             ▼
┌──────────────┐  ┌───────────────────┐
│ Load Saved   │  │ Detect System     │
│ Theme +      │  │ Preference        │
│ Source       │  │ (matchMedia)      │
└──────┬───────┘  └────────┬──────────┘
       │                   │
       │                   ▼
       │          ┌────────────────────┐
       │          │ Set source=        │
       │          │ 'system' or        │
       │          │ 'default'          │
       │          └────────┬───────────┘
       │                   │
       └───────┬───────────┘
               │
               ▼
     ┌──────────────────┐
     │ Apply Theme to   │
     │ DOM (<html>      │
     │ class="dark")    │
     └────────┬─────────┘
              │
              ▼
     ┌──────────────────┐
     │ User Interaction │
     │ (Click Toggle)   │
     └────────┬─────────┘
              │
              ▼
     ┌──────────────────┐
     │ Toggle mode,     │
     │ Set source=      │
     │ 'manual'         │
     └────────┬─────────┘
              │
              ▼
     ┌──────────────────┐
     │ Persist to       │
     │ Storage (if      │
     │ available)       │
     └────────┬─────────┘
              │
              ▼
     ┌──────────────────┐
     │ Apply to DOM +   │
     │ Update Icon      │
     └──────────────────┘
```

### State Resolution Priority

When determining the active theme, the system follows this priority order:

```typescript
function resolveTheme(): ThemeState {
  // Priority 1: Manual user selection (highest)
  const saved = storage.getTheme();
  const source = storage.getThemeSource();

  if (saved && source === 'manual') {
    return {
      mode: saved,
      source: 'manual',
      storageAvailable: storage.isAvailable()
    };
  }

  // Priority 2: System preference
  if (typeof window !== 'undefined' && window.matchMedia) {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const systemTheme = prefersDark ? 'dark' : 'light';

    return {
      mode: systemTheme,
      source: 'system',
      storageAvailable: storage.isAvailable()
    };
  }

  // Priority 3: Default (light)
  return {
    mode: 'light',
    source: 'default',
    storageAvailable: storage.isAvailable()
  };
}
```

---

## System Preference Integration

### matchMedia API

**Detection**:
```typescript
const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
const prefersDark = mediaQuery.matches;  // boolean
```

**Live Monitoring**:
```typescript
mediaQuery.addEventListener('change', (e) => {
  const newTheme = e.matches ? 'dark' : 'light';

  // Only apply if source is NOT 'manual'
  if (themeState.source !== 'manual') {
    updateTheme(newTheme, 'system');
  }
});
```

**Integration Logic**:

| Scenario | Current Source | System Changes | Behavior |
|----------|----------------|----------------|----------|
| First visit, no saved preference | `'default'` | Dark → Light | Apply system preference |
| User manually selected dark | `'manual'` | Dark → Light | **Ignore** system change (manual priority) |
| User manually selected light | `'manual'` | Light → Dark | **Ignore** system change (manual priority) |
| System-detected theme active | `'system'` | Dark → Light | Follow system change |

---

## DOM Integration

### HTML Class Application

**Light Mode**:
```html
<html lang="en">
  <!-- No 'dark' class -->
</html>
```

**Dark Mode**:
```html
<html lang="en" class="dark">
  <!-- 'dark' class applied -->
</html>
```

**CSS Variables** (existing in `app/globals.css`):
```css
:root {
  --background: oklch(1 0 0);     /* Light background */
  --foreground: oklch(0.145 0 0); /* Light text */
  /* ... other light mode variables ... */
}

.dark {
  --background: oklch(0.145 0 0); /* Dark background */
  --foreground: oklch(0.985 0 0); /* Dark text */
  /* ... other dark mode variables ... */
}
```

**Application Code**:
```typescript
function applyTheme(mode: 'light' | 'dark') {
  if (typeof document !== 'undefined') {
    document.documentElement.classList.toggle('dark', mode === 'dark');
  }
}
```

---

## Component State (React)

### ThemeToggle Component State

```typescript
interface ThemeToggleState {
  isDark: boolean;              // Derived from ThemeState.mode
  isLoading: boolean;           // True during SSR hydration
  hasHydrated: boolean;         // True after client-side mount
}
```

**Hydration Safety**:
```typescript
// Prevent hydration mismatch (server doesn't know system preference)
const [hasHydrated, setHasHydrated] = useState(false);

useEffect(() => {
  setHasHydrated(true);
  // Now safe to read system preference and apply theme
}, []);

if (!hasHydrated) {
  // Server-side: render neutral state
  return <div className="h-9 w-9" />;  // Placeholder
}

// Client-side: render actual toggle
return <button>{isDark ? <Sun /> : <Moon />}</button>;
```

---

## Storage Abstraction Layer

### Interface

```typescript
interface ThemeStorage {
  // Get current theme mode
  getTheme(): 'light' | 'dark' | null;

  // Set theme mode
  setTheme(theme: 'light' | 'dark'): boolean;  // Returns success/failure

  // Get theme source
  getThemeSource(): 'system' | 'manual' | null;

  // Set theme source
  setThemeSource(source: 'system' | 'manual'): boolean;

  // Check if any storage available
  isAvailable(): boolean;
}
```

### Implementation Strategy

```typescript
class BrowserThemeStorage implements ThemeStorage {
  private storage: Storage | null;

  constructor() {
    // Try localStorage → sessionStorage → null
    this.storage = this.detectStorage();
  }

  private detectStorage(): Storage | null {
    try {
      if (window.localStorage) {
        localStorage.setItem('__test__', '1');
        localStorage.removeItem('__test__');
        return localStorage;
      }
    } catch {
      // localStorage blocked
    }

    try {
      if (window.sessionStorage) {
        sessionStorage.setItem('__test__', '1');
        sessionStorage.removeItem('__test__');
        return sessionStorage;
      }
    } catch {
      // sessionStorage also blocked
    }

    return null;  // No storage available
  }

  // ... implementation of interface methods
}
```

---

## Data Flow Summary

```
┌─────────────────┐
│  User Action    │  (Click toggle)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Update State    │  mode = 'dark', source = 'manual'
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Persist State   │  localStorage.setItem('theme', 'dark')
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Apply to DOM    │  document.documentElement.classList.add('dark')
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Update Icon     │  Swap Moon → Sun
└─────────────────┘
```

---

## Validation Rules

### Theme Mode Validation
```typescript
function isValidThemeMode(value: unknown): value is 'light' | 'dark' {
  return value === 'light' || value === 'dark';
}
```

### Theme Source Validation
```typescript
function isValidThemeSource(value: unknown): value is 'system' | 'manual' {
  return value === 'system' || value === 'manual';
}
```

### Storage Read Validation
```typescript
const saved = localStorage.getItem('theme');
if (saved && isValidThemeMode(saved)) {
  // Safe to use
  applyTheme(saved);
} else {
  // Invalid or corrupted value, fall back to system/default
  const systemTheme = detectSystemTheme();
  applyTheme(systemTheme);
}
```

---

## Edge Cases

| Case | Behavior |
|------|----------|
| Storage quota exceeded | Fall back to sessionStorage or in-memory |
| Invalid stored value | Ignore, use system preference or default |
| System preference changes while app open | Only update if source !== 'manual' |
| User toggles multiple times rapidly | Debounce not needed (instant toggle is desired) |
| SSR hydration | Defer theme detection to client-side useEffect |
| Storage cleared externally | Treat as first visit, detect system preference |

---

## Related Artifacts

- **Research**: [research.md](./research.md) - System preference detection implementation
- **Contracts**: [contracts/theme-state.md](./contracts/theme-state.md) - API definitions
- **Component**: [contracts/component-api.md](./contracts/component-api.md) - ThemeToggle props

---

**Data Model Status**: ✅ COMPLETE
**Next Artifact**: Component Contracts
