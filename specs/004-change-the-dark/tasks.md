# Tasks: Simplify Dark Mode Toggle to Icon

**Input**: Design documents from `/specs/004-change-the-dark/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → ✅ Tech stack: TypeScript 5.x, React 19, Next.js 15.5.4, shadcn/ui, lucide-react
   → ✅ Structure: Next.js app/ directory with components/
2. Load optional design documents:
   → ✅ data-model.md: ThemeState entity, storage abstraction
   → ✅ contracts/: component-api.md, theme-state.md
   → ✅ research.md: lucide-react, Radix tooltip, matchMedia API
   → ✅ quickstart.md: 11 test scenarios
3. Generate tasks by category:
   → ✅ Setup: tooltip component, dependencies
   → ✅ Tests: contract tests (2), integration tests (11 scenarios)
   → ✅ Core: storage layer, detection layer, component
   → ✅ Integration: layout, remove old button
   → ✅ Polish: Storybook, accessibility, performance
4. Apply task rules:
   → ✅ Different files = [P] for parallel
   → ✅ Same file = sequential
   → ✅ Tests before implementation (TDD)
5. Number tasks sequentially (T001-T027)
6. Generate dependency graph
7. Create parallel execution examples
8. ✅ Validation:
   → ✅ All contracts have tests
   → ✅ ThemeState entity has implementation
   → ✅ All tests before implementation
   → ✅ Quickstart scenarios mapped to tests
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

---

## Phase 3.1: Setup

- [x] **T001** Check if Radix UI tooltip exists at `components/ui/tooltip.tsx`; if missing, run `npx shadcn@latest add tooltip`
- [x] **T002** Verify lucide-react dependency in `package.json` (should already exist from shadcn/ui setup)
- [x] **T003** [P] Configure TypeScript types for theme contracts in `types/theme.ts` (ThemeMode, ThemeSource, ThemeState types)

---

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests

- [x] **T004** [P] Contract test for ThemeStorage interface in `lib/__tests__/theme-storage.test.ts`
  - Test: `getTheme()` returns null when no theme saved
  - Test: `setTheme('dark')` saves and retrieves 'dark'
  - Test: `setTheme('light')` saves and retrieves 'light'
  - Test: `getThemeSource()` returns null when no source saved
  - Test: `setThemeSource('manual')` saves and retrieves 'manual'
  - Test: `setThemeSource('system')` saves and retrieves 'system'
  - Test: `isAvailable()` returns true when localStorage works
  - Test: Fallback to sessionStorage when localStorage blocked
  - Test: Returns false when both storage types unavailable
  - Test: Validates theme values (rejects invalid strings)

- [x] **T005** [P] Contract test for system preference detection in `lib/__tests__/theme-detection.test.ts`
  - Test: `detectSystemTheme()` returns 'dark' when system prefers dark
  - Test: `detectSystemTheme()` returns 'light' when system prefers light
  - Test: `detectSystemTheme()` returns 'light' when matchMedia unavailable
  - Test: `watchSystemTheme()` calls callback when preference changes
  - Test: Cleanup function removes event listener
  - Test: SSR safety (returns default when window undefined)

- [x] **T006** [P] Contract test for ThemeToggle component in `app/__tests__/components/theme-toggle.test.tsx`
  - Test: Renders Moon icon in light mode
  - Test: Renders Sun icon in dark mode
  - Test: Toggles theme on click
  - Test: Calls onThemeChange callback when provided
  - Test: Is keyboard accessible (Tab to focus, Enter/Space to toggle)
  - Test: Shows tooltip when showTooltip=true
  - Test: Hides tooltip when showTooltip=false
  - Test: Applies custom className prop
  - Test: Has proper ARIA labels
  - Test: Icon hidden from screen readers (aria-hidden="true")

### Integration Tests (from Quickstart Scenarios)

- [x] **T007** [P] Integration test: Initial load with system preference in `app/__tests__/integration/theme-system-preference.test.ts`
  - Test: App loads in dark mode when OS is dark (Scenario 1)
  - Test: App loads in light mode when OS is light
  - Test: localStorage shows theme-source: "system"

- [x] **T008** [P] Integration test: Manual theme toggle in `app/__tests__/integration/theme-manual-toggle.test.ts`
  - Test: Click toggles light → dark (Scenario 2)
  - Test: Click toggles dark → light
  - Test: localStorage updates to theme-source: "manual"
  - Test: Theme switch completes in <50ms

- [x] **T009** [P] Integration test: Manual override persistence in `app/__tests__/integration/theme-override-persistence.test.ts`
  - Test: Manual selection overrides system preference (Scenario 3)
  - Test: Manual theme persists across page reloads
  - Test: Manual choice respected even when system changes

- [x] **T010** [P] Integration test: Hover and tooltip in `app/__tests__/integration/theme-hover-tooltip.test.tsx`
  - Test: Visual feedback on hover (Scenario 4)
  - Test: Tooltip appears with correct text
  - Test: Tooltip readable in both light and dark modes

- [x] **T011** [P] Integration test: Responsive sizing in `app/__tests__/integration/theme-responsive-sizing.test.tsx`
  - Test: Icon larger on mobile (<768px) (Scenario 5)
  - Test: Icon smaller on desktop (≥768px)
  - Test: Touch target ≥44px on mobile

- [x] **T012** [P] Integration test: Accessibility in `app/__tests__/integration/theme-accessibility.test.tsx`
  - Test: Tab focuses icon (Scenario 6)
  - Test: Enter key toggles theme
  - Test: Space key toggles theme
  - Test: Focus indicator visible

- [x] **T013** [P] Integration test: Visibility in both themes in `app/__tests__/integration/theme-visibility.test.ts`
  - Test: Icon visible in light mode (Scenario 7)
  - Test: Icon visible in dark mode
  - Test: Sufficient contrast in both modes

- [x] **T014** [P] Integration test: localStorage unavailable in `app/__tests__/integration/theme-storage-fallback.test.ts`
  - Test: Theme toggle works in private browsing (Scenario 8)
  - Test: Falls back to sessionStorage
  - Test: Theme resets when session ends
  - Test: No errors when storage blocked

- [x] **T015** [P] Integration test: Old button removed in `app/__tests__/integration/theme-old-button-removed.test.tsx`
  - Test: No centered button present (Scenario 9)
  - Test: No duplicate theme toggles
  - Test: No layout shift or empty space

- [x] **T016** [P] Integration test: System preference change (advanced) in `app/__tests__/integration/theme-system-change.test.ts`
  - Test: App responds when OS theme changes (Scenario 10)
  - Test: System change ignored when manual override active

---

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Storage Layer

- [x] **T017** [P] Create storage abstraction in `lib/theme-storage.ts`
  - Implement `BrowserThemeStorage` class
  - Implement `detectStorage()` with localStorage → sessionStorage fallback
  - Implement `getTheme()`, `setTheme()` with validation
  - Implement `getThemeSource()`, `setThemeSource()` with validation
  - Implement `isAvailable()` to check storage accessibility
  - Export singleton instance `themeStorage`
  - Handle storage quota errors gracefully
  - Include try-catch for all storage operations

### Detection Layer

- [x] **T018** [P] Extend theme detection in `lib/theme-detection.ts`
  - Add `detectSystemTheme()` function using matchMedia
  - Add `watchSystemTheme(callback)` function with event listener
  - Return cleanup function from watchSystemTheme
  - Include SSR safety checks (typeof window)
  - Handle matchMedia unavailable gracefully
  - Preserve existing OKLCH detection functions

### Component

- [x] **T019** Create ThemeToggle component in `components/theme-toggle.tsx`
  - Import Moon and Sun from lucide-react
  - Import Tooltip components from `@/components/ui/tooltip`
  - Import themeStorage from `@/lib/theme-storage`
  - Import detectSystemTheme, watchSystemTheme from `@/lib/theme-detection`
  - Define props interface (className, size, showTooltip, onThemeChange)
  - Implement useState for theme state
  - Implement useEffect for initial theme detection (SSR-safe)
  - Implement system preference watching (cleanup on unmount)
  - Implement toggle handler (updates storage, calls callback)
  - Render button with ARIA attributes
  - Render conditional icon (Moon/Sun)
  - Wrap in Tooltip if showTooltip=true
  - Apply responsive sizing classes (h-6 w-6 md:h-5 md:w-5)
  - Apply hover and focus states
  - Export component

---

## Phase 3.4: Integration

- [x] **T020** Integrate ThemeToggle into root layout in `app/layout.tsx`
  - Import ThemeToggle component
  - Add fixed header wrapper with top-right positioning
  - Position: `fixed top-4 right-4 z-40`
  - Place ThemeToggle inside header
  - Ensure no overlap with existing CompatibilityWarning

- [x] **T021** Remove old theme toggle from `index.html`
  - Remove button markup (lines 306-310)
  - Remove theme toggle JavaScript (lines 439-460)
  - Remove references to `appState.isDark`
  - Verify no other code depends on removed elements

---

## Phase 3.5: Polish

- [x] **T022** [P] Create Storybook stories in `stories/ThemeToggle.stories.tsx`
  - Story: Default state
  - Story: Light mode
  - Story: Dark mode
  - Story: With tooltip
  - Story: Without tooltip
  - Story: With callback
  - Story: Mobile size
  - Story: Desktop size
  - Include controls for all props

- [x] **T023** [P] Verify accessibility compliance in `app/__tests__/accessibility/theme-toggle-a11y.test.ts`
  - Test: Matches existing app accessibility standards
  - Test: Proper semantic HTML (button element)
  - Test: ARIA labels present and dynamic
  - Test: Keyboard navigation works
  - Test: Focus indicators visible
  - Test: Screen reader compatibility

- [x] **T024** [P] Performance validation in `app/__tests__/performance/theme-toggle-perf.test.ts`
  - Test: Theme switch completes in <50ms
  - Test: No layout thrashing
  - Test: No FOUC (flash of unstyled content)
  - Test: CSS variables apply smoothly

- [x] **T025** [P] Add component documentation in `components/theme-toggle.tsx`
  - Add JSDoc comments to component
  - Document all props with examples
  - Add usage examples in comments
  - Document accessibility features

- [ ] **T026** Execute manual testing checklist from `specs/004-change-the-dark/quickstart.md` ⚠️ **REQUIRES MANUAL EXECUTION**
  - Run `npm run dev` and navigate to `http://localhost:3000`
  - Complete all 11 test scenarios from quickstart.md
  - Test in Chrome, Safari, Firefox
  - Test on mobile device or responsive mode
  - Test in private browsing mode
  - Document any issues found

- [ ] **T027** Visual regression check ⚠️ **REQUIRES MANUAL EXECUTION**
  - Run `npm run dev` and navigate to app
  - Take before/after screenshots
  - Verify old centered button removed from index.html page
  - Verify icon visible in both themes on Next.js pages
  - Verify no layout shift when toggling
  - Verify consistent styling with shadcn/ui theme

---

## Dependencies

### Phase Order
```
Setup (T001-T003)
    ↓
Tests (T004-T016)  ← MUST FAIL before proceeding
    ↓
Implementation (T017-T019)
    ↓
Integration (T020-T021)
    ↓
Polish (T022-T027)
```

### Specific Dependencies

**Setup Phase**:
- T001 blocks T019 (tooltip needed for component)
- T003 can run in parallel with T001-T002

**Test Phase** (all parallel):
- T004-T016 can all run simultaneously (different files)
- All must complete and fail before T017-T019

**Implementation Phase**:
- T017 (storage) blocks T019 (component needs storage)
- T018 (detection) blocks T019 (component needs detection)
- T017 and T018 can run in parallel
- T019 must wait for T017 and T018

**Integration Phase**:
- T020 blocks T021 (need component before removing old button)
- T019 blocks T020 (need component before integrating)

**Polish Phase**:
- T022-T025 can run in parallel (different files)
- T026-T027 should run after T020-T021 (need integrated app)

---

## Parallel Execution Examples

### Setup Phase (Parallel)
```bash
# Launch T003 separately (T001-T002 are commands, not code)
Task agent: "Configure TypeScript types for theme contracts in types/theme.ts"
```

### Test Phase (Maximum Parallelism)
```bash
# Launch all contract tests simultaneously (T004-T006)
Task agent: "Contract test for ThemeStorage interface in lib/__tests__/theme-storage.test.ts"
Task agent: "Contract test for system preference detection in lib/__tests__/theme-detection.test.ts"
Task agent: "Contract test for ThemeToggle component in app/__tests__/components/theme-toggle.test.tsx"

# Launch all integration tests simultaneously (T007-T016)
Task agent: "Integration test: Initial load with system preference in app/__tests__/integration/theme-system-preference.test.ts"
Task agent: "Integration test: Manual theme toggle in app/__tests__/integration/theme-manual-toggle.test.ts"
Task agent: "Integration test: Manual override persistence in app/__tests__/integration/theme-override-persistence.test.ts"
Task agent: "Integration test: Hover and tooltip in app/__tests__/integration/theme-hover-tooltip.test.ts"
Task agent: "Integration test: Responsive sizing in app/__tests__/integration/theme-responsive-sizing.test.ts"
Task agent: "Integration test: Accessibility in app/__tests__/integration/theme-accessibility.test.ts"
Task agent: "Integration test: Visibility in both themes in app/__tests__/integration/theme-visibility.test.ts"
Task agent: "Integration test: localStorage unavailable in app/__tests__/integration/theme-storage-fallback.test.ts"
Task agent: "Integration test: Old button removed in app/__tests__/integration/theme-old-button-removed.test.ts"
Task agent: "Integration test: System preference change in app/__tests__/integration/theme-system-change.test.ts"
```

### Implementation Phase (Parallel Storage + Detection)
```bash
# Launch T017 and T018 together (different files)
Task agent: "Create storage abstraction in lib/theme-storage.ts"
Task agent: "Extend theme detection in lib/theme-detection.ts"

# T019 must wait for both to complete
Task agent: "Create ThemeToggle component in components/theme-toggle.tsx"
```

### Polish Phase (Parallel)
```bash
# Launch T022-T025 together (different files)
Task agent: "Create Storybook stories in stories/ThemeToggle.stories.tsx"
Task agent: "Verify accessibility compliance in app/__tests__/accessibility/theme-toggle-a11y.test.ts"
Task agent: "Performance validation in app/__tests__/performance/theme-toggle-perf.test.ts"
Task agent: "Add component documentation in components/theme-toggle.tsx"

# T026-T027 run after integration complete
```

---

## Notes

- **[P] tasks** = different files, no dependencies, safe to parallelize
- **Sequential tasks** (no [P]) = same file or direct dependencies
- **TDD critical**: All tests (T004-T016) must be written and failing before implementation (T017-T019)
- **Commit strategy**: Commit after each task or logical group
- **Verification**: Run `npm run dev` and manually test after integration phase

---

## Validation Checklist

✅ **Contract Coverage**:
- [x] ThemeStorage contract → T004
- [x] System detection contract → T005
- [x] ThemeToggle component contract → T006

✅ **Entity Coverage**:
- [x] ThemeState → Implemented in T017 (storage) and T018 (detection)

✅ **Test Before Implementation**:
- [x] All tests (T004-T016) before implementation (T017-T019)

✅ **Parallel Safety**:
- [x] All [P] tasks modify different files
- [x] No [P] task has dependencies on another [P] task in same phase

✅ **File Paths**:
- [x] Every task specifies exact file path
- [x] Paths are absolute from repository root

✅ **Quickstart Coverage**:
- [x] Scenario 1 → T007
- [x] Scenario 2 → T008
- [x] Scenario 3 → T009
- [x] Scenario 4 → T010
- [x] Scenario 5 → T011
- [x] Scenario 6 → T012
- [x] Scenario 7 → T013
- [x] Scenario 8 → T014
- [x] Scenario 9 → T015
- [x] Scenario 10 → T016
- [x] Scenario 11 (Storybook) → T022

---

## Estimated Time

- **Setup**: 15-30 minutes (T001-T003)
- **Tests**: 2-3 hours (T004-T016) - 13 test files
- **Implementation**: 1.5-2 hours (T017-T019) - Core functionality
- **Integration**: 30-45 minutes (T020-T021) - Layout changes
- **Polish**: 1-1.5 hours (T022-T027) - Storybook, docs, validation

**Total**: ~5.5-7.5 hours

---

**Tasks Status**: ✅ Ready for execution
**Next Step**: Begin with T001 (Setup phase)
