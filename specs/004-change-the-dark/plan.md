# Implementation Plan: Simplify Dark Mode Toggle to Icon

**Branch**: `004-change-the-dark` | **Date**: 2025-10-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-change-the-dark/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → ✅ Loaded from /Users/rogercox/Credit-Card-Processor/specs/004-change-the-dark/spec.md
2. Fill Technical Context
   → ✅ Project Type: Web (Next.js 15 + React 19)
   → ✅ Structure Decision: app/ directory with components/
3. Fill Constitution Check section
   → ✅ Constitution is template-only, no specific project requirements
4. Evaluate Constitution Check
   → ✅ No violations - UI-only feature, no new architectural patterns
   → ✅ Update Progress Tracking: Initial Constitution Check PASSED
5. Execute Phase 0 → research.md
   → ✅ No NEEDS CLARIFICATION markers remain
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
   → Pending execution
7. Re-evaluate Constitution Check
   → Pending after Phase 1
8. Plan Phase 2 → Describe task generation approach
   → Pending
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary

Replace the current centered, prominent dark mode toggle button with a subtle icon positioned in the top right corner of the page. The icon will:
- Display moon (light mode) or sun (dark mode) to indicate current state
- Provide visual hover feedback and tooltip
- Detect and respect system dark mode preference initially
- Support responsive sizing (larger on mobile/touch devices)
- Gracefully degrade when localStorage is unavailable
- Match existing accessibility standards

**Technical Approach**: Create a new React component (`ThemeToggle`) that encapsulates theme detection, icon rendering, tooltip, and state management. Remove the existing centered button from `index.html` and integrate the new icon component into the app layout header.

## Technical Context

**Language/Version**: TypeScript 5.x
**Primary Dependencies**: React 19, Next.js 15.5.4, shadcn/ui, Radix UI, Tailwind CSS 4.x, lucide-react (icons)
**Storage**: localStorage (with sessionStorage fallback)
**Testing**: Existing test suite (Jest/Vitest), Storybook for component validation
**Target Platform**: Web browsers (Chrome 111+, Safari 15.4+, Firefox 113+ for OKLCH support)
**Project Type**: Web (Next.js App Directory architecture)
**Performance Goals**: Immediate theme switch (<50ms), no layout shift, no flash of unstyled content
**Constraints**: Preserve all existing theme functionality, must be visible in both light and dark modes, maintain OKLCH color theme compatibility
**Scale/Scope**: Single component affecting 1-2 layout files, ~100-150 lines of new code

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Initial Check (Pre-Phase 0)
**Status**: ✅ PASSED

**Analysis**:
- Constitution file is template-only with placeholder principles
- No project-specific constraints defined
- Feature is UI-only modification with no new architectural patterns
- Leverages existing shadcn/ui component patterns already in use
- No constitutional violations identified

### Post-Design Check (After Phase 1)
**Status**: Pending completion of Phase 1

## Project Structure

### Documentation (this feature)
```
specs/004-change-the-dark/
├── plan.md              # This file (/plan command output)
├── spec.md              # Feature specification (completed)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
│   ├── component-api.md # ThemeToggle component contract
│   └── theme-state.md   # Theme state management contract
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)

**Next.js App Directory Structure**:
```
app/
├── layout.tsx           # ROOT LAYOUT - Integration point for ThemeToggle icon
├── page.tsx             # Main page (no changes needed)
└── globals.css          # Theme CSS variables (existing)

components/
├── ui/                  # shadcn/ui components (existing)
│   ├── button.tsx
│   ├── tooltip.tsx      # May need to add if not present
│   └── ...
├── theme-toggle.tsx     # NEW - Theme toggle icon component
└── compatibility-warning.tsx  # Existing OKLCH warning component

lib/
├── theme-detection.ts   # MODIFY - Extend for system preference detection
├── theme-storage.ts     # NEW - localStorage/sessionStorage abstraction
└── utils.ts             # Existing utility functions

stories/
└── ThemeToggle.stories.tsx  # NEW - Storybook stories for validation

index.html               # MODIFY - Remove centered theme toggle button (lines 306-310)

app/__tests__/
└── components/
    └── theme-toggle.test.tsx  # NEW - Component tests
```

## Phase 0: Research & Analysis

### Objective
Investigate existing theme implementation, icon libraries, and component patterns to inform design decisions.

### Research Areas

1. **Current Theme Implementation Analysis**
   - Location: `index.html` lines 306-310 (centered button), lines 439-460 (theme toggle JS)
   - Current behavior: Centered button with emoji icons (🌙/☀️), localStorage persistence
   - Current accessibility: Basic button element, no ARIA labels or keyboard navigation specified
   - Gap analysis: No system preference detection, no graceful localStorage fallback, fixed positioning

2. **System Dark Mode Preference Detection**
   - API: `window.matchMedia('(prefers-color-scheme: dark)')`
   - Event listener: `matchMedia.addEventListener('change', handler)`
   - Priority logic: localStorage value > system preference > default (light)
   - Browser support: Universal (all modern browsers)

3. **Icon Implementation Options**
   - **Option A**: lucide-react icons (already in dependencies)
     - Icons: `Moon`, `Sun`, `MoonStar`, `SunMedium`
     - Pros: Consistent with existing shadcn/ui patterns, tree-shakeable, TypeScript types
     - Cons: None for this use case
   - **Option B**: Emoji icons (current approach)
     - Icons: 🌙, ☀️
     - Pros: No dependencies, universal support
     - Cons: Less professional, sizing inconsistencies, accessibility challenges
   - **Decision**: lucide-react for consistency and accessibility

4. **Tooltip Implementation**
   - Evaluate Radix UI Tooltip (part of shadcn/ui ecosystem)
   - Check if `components/ui/tooltip.tsx` exists; if not, add via `npx shadcn@latest add tooltip`
   - Tooltip content: Dynamic based on current state ("Switch to dark mode" / "Switch to light mode")
   - Accessibility: Radix handles ARIA automatically

5. **Responsive Sizing Strategy**
   - Desktop: 20px icon size (subtle, unobtrusive)
   - Mobile/Tablet: 24-28px icon size (easier touch target)
   - Breakpoint: Tailwind `md:` breakpoint (768px)
   - Touch target: Minimum 44x44px clickable area (WCAG guideline)

6. **Storage Abstraction Layer**
   - Create `lib/theme-storage.ts` to encapsulate:
     - `getThemePreference()`: Try localStorage, fall back to sessionStorage
     - `setThemePreference(theme)`: Try localStorage, fall back to sessionStorage
     - `isStorageAvailable()`: Detect storage support
   - Graceful degradation: Session-only persistence when localStorage blocked

7. **Positioning in Layout**
   - Target: `app/layout.tsx` root layout
   - Position: Top-right corner, likely in a header/nav component
   - Current header: Check if header component exists in `app/page.tsx` lines 153-177
   - Integration point: Add to existing navigation or create new header wrapper

8. **Accessibility Review**
   - Current app accessibility level: Review existing buttons (`components/ui/button.tsx`)
   - Requirements from clarification: "Match existing accessibility level"
   - Baseline: Semantic HTML, keyboard navigation (Tab/Enter), focus indicators
   - No WCAG 2.1 AA requirement specified, so match app standard

### Research Output
- Document findings in `research.md`
- Include code examples for system preference detection
- Icon comparison with screenshots/examples
- Storage fallback pseudo-code
- Accessibility compliance checklist

**Deliverable**: `specs/004-change-the-dark/research.md`

## Phase 1: Design Artifacts

### 1. Data Model (`data-model.md`)

**Theme State Entity**:
```
ThemeState {
  mode: 'light' | 'dark'
  source: 'system' | 'manual' | 'default'
  storageAvailable: boolean
}
```

**State Transitions**:
- Initial load: system preference → theme state
- User toggle: manual override → localStorage → theme state
- Reload with saved preference: localStorage → theme state (overrides system)
- localStorage unavailable: sessionStorage → theme state (session-only)

**Storage Keys**:
- `theme`: Stores 'light' or 'dark'
- `theme-source`: Stores 'system' or 'manual' (determines priority)

### 2. Component Contracts (`contracts/`)

**`contracts/component-api.md`** - ThemeToggle Component:
```typescript
interface ThemeToggleProps {
  className?: string;  // Allow custom positioning/styling
  size?: 'sm' | 'md' | 'lg';  // Responsive size variants
  showTooltip?: boolean;  // Enable/disable tooltip (default: true)
}

// Events
onThemeChange?: (theme: 'light' | 'dark') => void;

// Accessibility
- role: "button"
- aria-label: "Toggle theme" or "Switch to {opposite} mode"
- tabIndex: 0
- keyboard: Enter/Space to toggle
```

**`contracts/theme-state.md`** - Theme Management Contract:
```typescript
// lib/theme-storage.ts
interface ThemeStorage {
  getTheme(): 'light' | 'dark' | null;
  setTheme(theme: 'light' | 'dark'): boolean;
  getThemeSource(): 'system' | 'manual' | null;
  setThemeSource(source: 'system' | 'manual'): boolean;
  isAvailable(): boolean;
}

// lib/theme-detection.ts (extend existing)
function detectSystemTheme(): 'light' | 'dark';
function watchSystemTheme(callback: (theme: 'light' | 'dark') => void): () => void;
```

### 3. Quickstart Validation (`quickstart.md`)

Manual testing checklist:
1. **Initial Load Test**
   - Clear localStorage
   - Set system to dark mode → Verify app loads in dark mode
   - Set system to light mode → Verify app loads in light mode

2. **Toggle Test**
   - Click icon → Verify immediate theme switch
   - Verify icon changes (moon ↔ sun)
   - Reload page → Verify theme persists

3. **System Override Test**
   - Have system in dark mode
   - Manually toggle to light mode
   - Reload → Verify stays light (manual overrides system)

4. **Hover/Tooltip Test**
   - Hover over icon → Verify visual feedback
   - Verify tooltip appears with correct text
   - Test in both light and dark modes

5. **Responsive Test**
   - View on desktop → Verify smaller, subtle icon
   - View on mobile → Verify larger, touch-friendly icon

6. **Storage Fallback Test**
   - Open in private/incognito mode
   - Toggle theme → Verify works during session
   - Close and reopen → Verify resets to system preference

7. **Accessibility Test**
   - Tab to icon → Verify focus indicator
   - Press Enter → Verify toggles theme
   - Screen reader → Verify announces state

8. **Visual Regression Test**
   - Verify old centered button removed
   - Verify icon visible in both light and dark modes
   - Verify no layout shift on toggle

### 4. Agent Context (`CLAUDE.md`)

Update project context with:
- New component: `components/theme-toggle.tsx`
- New utility: `lib/theme-storage.ts`
- Modified: `lib/theme-detection.ts` (add system preference detection)
- Modified: `app/layout.tsx` (integrate ThemeToggle)
- Modified: `index.html` (remove old button)
- Tech stack: Emphasize lucide-react for icons, Radix UI tooltips

## Phase 2: Task Generation Plan

**Approach**: Incremental implementation with validation at each step.

### Task Breakdown Strategy

1. **Setup Tasks** (Preparation)
   - Add shadcn/ui tooltip component if not present
   - Create storage abstraction layer (`lib/theme-storage.ts`)
   - Extend theme detection with system preference (`lib/theme-detection.ts`)

2. **Component Development Tasks** (Core Implementation)
   - Create `ThemeToggle` component with basic structure
   - Implement icon rendering (Moon/Sun from lucide-react)
   - Add hover states and visual feedback
   - Integrate Radix UI tooltip
   - Add responsive sizing (desktop/mobile variants)

3. **Integration Tasks** (Connect to App)
   - Integrate ThemeToggle into `app/layout.tsx`
   - Remove old button from `index.html` (lines 306-310)
   - Update theme initialization logic to detect system preference
   - Implement manual override priority logic

4. **Testing Tasks** (Validation)
   - Write component tests for ThemeToggle
   - Create Storybook stories for visual validation
   - Execute quickstart manual testing checklist
   - Verify accessibility with keyboard navigation

5. **Refinement Tasks** (Polish)
   - Verify icon visibility in both themes
   - Fine-tune hover/focus states
   - Test localStorage fallback in private browsing
   - Visual regression check (before/after screenshots)

### Task Dependencies
```
Setup → Component Development → Integration → Testing → Refinement
   ↓                                   ↓
   └─────────────────────────────────→ (parallel)
```

### Estimation
- Setup: 30 minutes
- Component Development: 1-2 hours
- Integration: 30-45 minutes
- Testing: 1 hour
- Refinement: 30 minutes
**Total**: ~3.5-4.5 hours

## Progress Tracking

- [x] Initial Constitution Check (Pre-Phase 0)
- [x] Phase 0: Research & Analysis planning complete
- [x] Phase 0: Research artifacts generated (`research.md`)
- [x] Phase 1: Data model designed (`data-model.md`)
- [x] Phase 1: Component contracts defined (`contracts/`)
  - [x] `contracts/component-api.md` (ThemeToggle component)
  - [x] `contracts/theme-state.md` (Storage and detection)
- [x] Phase 1: Quickstart validation created (`quickstart.md`)
- [x] Phase 1: Agent context updated (`CLAUDE.md`)
- [x] Post-Design Constitution Check (After Phase 1)
- [x] Phase 2: Task generation plan defined
- [x] Ready for `/tasks` command

## Post-Design Constitution Check

**Status**: ✅ PASSED (No violations)

**Analysis**:
- UI-only feature, no new architectural patterns
- Leverages existing shadcn/ui and Radix UI patterns
- Storage abstraction follows single responsibility principle
- Component is self-contained and independently testable
- No constitutional violations after design

## Next Steps

1. ✅ **Phase 0 Complete**: Research findings documented
2. ✅ **Phase 1 Complete**: All design artifacts created
3. ✅ **Constitution Re-check**: No violations detected
4. ⏭️ **Proceed to `/tasks`**: Generate executable task list

**Current Status**: ✅ Planning complete. All artifacts generated. Ready for task generation via `/tasks` command.
