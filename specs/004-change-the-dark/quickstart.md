# Quickstart Validation Guide: Dark Mode Toggle Icon

**Feature**: 004-change-the-dark
**Date**: 2025-10-04
**Purpose**: Manual testing checklist to validate all functional requirements before deployment

---

## Prerequisites

- [ ] Development server running (`npm run dev`)
- [ ] Browser with DevTools open (Console + Application tabs)
- [ ] Test in Chrome, Safari, and Firefox if possible
- [ ] Mobile device or browser DevTools responsive mode
- [ ] Private/incognito browsing window ready

---

## Test Scenarios

### ✅ Scenario 1: Initial Load with System Preference

**Objective**: Verify app detects and applies OS dark mode preference on first visit.

**Steps**:
1. Clear all browser storage:
   - Open DevTools → Application → Storage → Clear site data
2. Set your operating system to **Dark Mode**
   - macOS: System Settings → Appearance → Dark
   - Windows: Settings → Personalization → Colors → Dark
3. Navigate to `http://localhost:3000` (or dev server URL)

**Expected Results**:
- [ ] App loads in dark mode (dark background, light text)
- [ ] Theme toggle icon shows **Sun** (☀️ or lucide-react Sun icon)
- [ ] Console shows no errors
- [ ] DevTools Application → localStorage shows:
  - `theme: "dark"`
  - `theme-source: "system"`

**Repeat with Light Mode**:
4. Set OS to **Light Mode**
5. Clear storage and reload

**Expected Results**:
- [ ] App loads in light mode
- [ ] Icon shows **Moon** (🌙 or lucide-react Moon icon)
- [ ] localStorage shows `theme: "light"`, `theme-source: "system"`

---

### ✅ Scenario 2: Manual Theme Toggle

**Objective**: Verify clicking icon toggles theme and sets manual override.

**Setup**:
1. Clear storage
2. Ensure app is in light mode (default)

**Steps**:
1. Locate theme toggle icon in **top-right corner** of page
2. Click the icon

**Expected Results**:
- [ ] Theme switches to dark mode **immediately** (<50ms, no flicker)
- [ ] Icon changes from Moon → Sun
- [ ] localStorage updates:
  - `theme: "dark"`
  - `theme-source: "manual"`

3. Click icon again

**Expected Results**:
- [ ] Theme switches back to light mode
- [ ] Icon changes from Sun → Moon
- [ ] localStorage: `theme: "light"`, `theme-source: "manual"`

---

### ✅ Scenario 3: Manual Override Persistence

**Objective**: Verify manually selected theme persists across reloads and overrides system preference.

**Setup**:
1. Set OS to **Dark Mode**
2. Clear storage, reload (app should load dark)
3. Manually toggle to **Light Mode** (click icon)

**Steps**:
1. Verify localStorage shows `theme-source: "manual"`
2. **Reload the page** (hard refresh: Cmd/Ctrl + Shift + R)

**Expected Results**:
- [ ] App loads in **light mode** (manual choice overrides system dark mode)
- [ ] Icon shows Moon
- [ ] localStorage still shows:
  - `theme: "light"`
  - `theme-source: "manual"`

**Inverse Test**:
4. Set OS to **Light Mode**
5. Manually toggle app to **Dark Mode**
6. Reload page

**Expected Results**:
- [ ] App loads in dark mode (manual override)

---

### ✅ Scenario 4: Hover and Tooltip

**Objective**: Verify visual feedback and tooltip on icon hover.

**Steps**:
1. Hover mouse over theme toggle icon (do not click)

**Expected Results**:
- [ ] Visual feedback appears (e.g., background color change, slight scale, or glow)
- [ ] Tooltip appears after ~200-500ms delay
- [ ] Tooltip text is appropriate:
  - In light mode: "Switch to dark mode" or similar
  - In dark mode: "Switch to light mode" or similar
- [ ] Tooltip is readable in both light and dark modes

2. Move mouse away from icon

**Expected Results**:
- [ ] Hover effect disappears
- [ ] Tooltip fades out

---

### ✅ Scenario 5: Responsive Sizing (Mobile)

**Objective**: Verify icon is larger and touch-friendly on mobile devices.

**Steps**:
1. Open browser DevTools → Responsive mode
2. Select mobile device (e.g., iPhone 12, Pixel 5)
3. Viewport width < 768px

**Expected Results**:
- [ ] Icon is **visibly larger** than on desktop (~24px vs ~20px)
- [ ] Touch target area is ≥44x44px (use DevTools to inspect element size)
- [ ] Icon still positioned in top-right corner
- [ ] No layout overlap with other elements

**Desktop Test**:
4. Resize viewport to > 768px (desktop breakpoint)

**Expected Results**:
- [ ] Icon shrinks to smaller, subtle size
- [ ] Still easily visible and clickable

---

### ✅ Scenario 6: Accessibility (Keyboard Navigation)

**Objective**: Verify keyboard users can access and use the toggle.

**Steps**:
1. Click in browser address bar (to reset focus)
2. Press **Tab** key repeatedly until theme toggle is focused

**Expected Results**:
- [ ] Icon receives focus (visible focus ring/outline)
- [ ] Focus indicator is clear and high-contrast

3. With icon focused, press **Enter** key

**Expected Results**:
- [ ] Theme toggles
- [ ] Icon changes
- [ ] No page scroll or navigation

4. Press **Space** key (with icon focused)

**Expected Results**:
- [ ] Theme toggles (same as Enter)

**Tooltip Keyboard Test**:
5. Focus icon, wait for tooltip to appear
6. Press **Escape** key

**Expected Results**:
- [ ] Tooltip closes (if Radix UI tooltip behavior supports this)

---

### ✅ Scenario 7: Visibility in Both Themes

**Objective**: Verify icon is visible in both light and dark modes.

**Steps**:
1. App in **light mode**
   - [ ] Icon is clearly visible (not washed out)
   - [ ] Sufficient contrast against light background
2. Toggle to **dark mode**
   - [ ] Icon is clearly visible (not invisible)
   - [ ] Sufficient contrast against dark background
3. Test hover states in both modes
   - [ ] Hover feedback visible in light mode
   - [ ] Hover feedback visible in dark mode

---

### ✅ Scenario 8: localStorage Unavailable (Private Browsing)

**Objective**: Verify graceful degradation when storage is blocked.

**Steps**:
1. Open browser in **Private/Incognito** mode
2. Navigate to app
3. Toggle theme

**Expected Results**:
- [ ] Theme toggle **works** (session-only)
- [ ] Icon swaps correctly
- [ ] Console may show warning about storage (acceptable)
- [ ] No errors or broken functionality

4. Within the **same tab/window**, reload page

**Expected Results**:
- [ ] Theme persists (sessionStorage fallback)

5. **Close tab** and open new private tab
6. Navigate to app

**Expected Results**:
- [ ] Theme resets to system preference or default (session lost)
- [ ] App still functional

---

### ✅ Scenario 9: Old Button Removed

**Objective**: Verify the old centered button is gone.

**Steps**:
1. Navigate to app
2. Scroll through page, looking for old theme toggle button

**Expected Results**:
- [ ] **No centered button** with text "🌙 Switch to Dark Mode" present
- [ ] Only the top-right icon visible
- [ ] No duplicate theme toggles anywhere on page

**Visual Regression**:
- [ ] Page layout looks clean, no empty space where button was
- [ ] No layout shift or awkward spacing

---

### ✅ Scenario 10: System Preference Change (Advanced)

**Objective**: Verify app responds when OS theme changes while app is open (only if not manually overridden).

**Setup**:
1. Clear storage
2. Set OS to Light Mode
3. Load app (should be light mode, source: "system")

**Steps**:
1. **Without closing the browser tab**, change OS to Dark Mode
   - macOS: System Settings → Appearance → Dark
   - Windows: Settings → Personalization → Colors → Dark

**Expected Results** (may take a few seconds):
- [ ] App theme automatically switches to dark
- [ ] Icon changes from Moon → Sun
- [ ] localStorage updates to `theme: "dark"`, `theme-source: "system"`

**Manual Override Test**:
2. Manually toggle app to **Light Mode** (click icon)
   - Verify `theme-source: "manual"`
3. Change OS to **Dark Mode** again

**Expected Results**:
- [ ] App **stays in light mode** (manual override respected)
- [ ] localStorage still shows `theme-source: "manual"`

---

### ✅ Scenario 11: Storybook Visual Validation (If Implemented)

**Objective**: Review component in isolation with all variants.

**Steps**:
1. Run Storybook: `npm run storybook`
2. Navigate to `ThemeToggle` story
3. View all variants:
   - [ ] Default state
   - [ ] Light mode
   - [ ] Dark mode
   - [ ] With tooltip
   - [ ] Without tooltip
   - [ ] Hover state
   - [ ] Focus state
   - [ ] Mobile size
   - [ ] Desktop size

**Expected Results**:
- [ ] All variants render correctly
- [ ] No console errors
- [ ] Visual consistency across variants

---

## Browser Compatibility Tests

### Test in Multiple Browsers

| Browser | Version | Light Mode | Dark Mode | System Pref | Tooltip | Keyboard | Mobile |
|---------|---------|------------|-----------|-------------|---------|----------|--------|
| **Chrome** | Latest | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| **Safari** | Latest | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| **Firefox** | Latest | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |
| **Edge** | Latest | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |

**Note**: System preference detection supported in all modern browsers (Chrome 76+, Safari 14+, Firefox 67+).

---

## Performance Validation

### Theme Switch Performance

**Steps**:
1. Open DevTools → Performance tab
2. Start recording
3. Click theme toggle icon
4. Stop recording

**Expected Results**:
- [ ] Theme switch completes in **<50ms**
- [ ] No layout thrashing or forced reflows
- [ ] No "Long Tasks" warnings
- [ ] CSS variable changes applied smoothly

### Page Load Performance

**Steps**:
1. Clear storage
2. Reload page with Performance tab recording

**Expected Results**:
- [ ] No flash of unstyled content (FOUC)
- [ ] No flash of incorrect theme
- [ ] Theme applied before first paint

---

## Regression Tests

### Existing Functionality Preserved

- [ ] OKLCH compatibility warning still works (if browser doesn't support OKLCH)
- [ ] All page content renders correctly in both themes
- [ ] Navigation links still work
- [ ] Session management pages unaffected
- [ ] Upload forms still functional
- [ ] Other interactive elements (buttons, inputs) still accessible

---

## Known Issues / Expected Warnings

### Acceptable Console Messages
- ⚠️ Warning about localStorage unavailable in private browsing (non-blocking)
- ⚠️ OKLCH not supported warning (separate feature, unrelated)

### Unacceptable Errors
- ❌ React hydration mismatch errors
- ❌ "Cannot read property of undefined" errors
- ❌ Uncaught exceptions on theme toggle
- ❌ Infinite loops or excessive re-renders

---

## Sign-Off Checklist

Before marking feature complete:

### Functional Requirements (from spec)
- [ ] FR-001: Icon in top-right corner ✓
- [ ] FR-002: Less visually prominent than old button ✓
- [ ] FR-003: Icon indicates current state (Moon/Sun) ✓
- [ ] FR-004: Click toggles theme ✓
- [ ] FR-005: Icon swaps on toggle ✓
- [ ] FR-006: localStorage persistence preserved ✓
- [ ] FR-007: Visible in both themes ✓
- [ ] FR-008: Old centered button removed ✓
- [ ] FR-009: Matches app accessibility standards ✓
- [ ] FR-010: Detects system preference on first visit ✓
- [ ] FR-011: Manual choice overrides system ✓
- [ ] FR-012: Visual hover feedback ✓
- [ ] FR-013: Tooltip on hover ✓
- [ ] FR-014: Graceful storage fallback ✓
- [ ] FR-015: Session-only when localStorage blocked ✓
- [ ] FR-016: Responsive sizing (larger on mobile) ✓
- [ ] FR-017: Subtle on desktop ✓

### Code Quality
- [ ] No TypeScript errors
- [ ] No ESLint warnings
- [ ] Unit tests passing
- [ ] Storybook stories created
- [ ] Code reviewed

### Documentation
- [ ] Component documented
- [ ] API contract finalized
- [ ] Migration notes clear

---

## Troubleshooting

### Icon not visible
- Check z-index (should be 40)
- Verify icon color uses CSS variables
- Inspect element to confirm it's rendered

### Theme not persisting
- Check DevTools → Application → localStorage
- Verify no browser extensions blocking storage
- Test in incognito mode

### Hydration mismatch errors
- Ensure theme detection happens in `useEffect`, not during render
- Check for `suppressHydrationWarning` if needed on `<html>` tag

### Tooltip not showing
- Verify Radix UI tooltip installed (`components/ui/tooltip.tsx`)
- Check `showTooltip` prop is `true`
- Ensure `TooltipProvider` wraps component

---

**Validation Status**: Ready for Testing
**Tester**: __________
**Date Completed**: __________
**All Tests Passed**: ☐ Yes ☐ No (see notes below)

**Notes**:
_____________________________
_____________________________
_____________________________
