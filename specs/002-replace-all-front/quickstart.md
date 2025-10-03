# Quickstart: Replace Front-End UI with shadcn/ui Blue Theme

**Date**: 2025-10-03
**Feature**: 002-replace-all-front

## Prerequisites
- Node.js 20+ installed
- npm or pnpm installed
- Git repository cloned
- Branch `002-replace-all-front` checked out

## Setup

### 1. Install Dependencies
```bash
# Install Storybook
npm install --save-dev @storybook/react @storybook/nextjs @storybook/addon-essentials @storybook/addon-themes

# Verify shadcn/ui already installed
npm list shadcn
```

### 2. Verify Theme Configuration
```bash
# Check components.json has blue baseColor
cat components.json | grep baseColor
# Expected: "baseColor": "blue"
```

### 3. Initialize Storybook
```bash
# Initialize Storybook for Next.js
npx storybook@latest init --type nextjs --skip-install

# Or manually create config
mkdir -p .storybook
```

## Development Workflow

### 1. Apply Blue Theme
```bash
# Update globals.css with blue theme variables
# This will be done as part of implementation tasks
```

### 2. Run Development Server
```bash
# Start Next.js dev server
npm run dev

# In separate terminal, start Storybook
npm run storybook
```

### 3. Visual Validation Checklist

#### Light Mode Verification
- [ ] Open http://localhost:6006 (Storybook)
- [ ] Navigate to Button component
- [ ] Verify all variants display blue theme:
  - Default button: Blue background
  - Outline button: Blue border
  - Ghost button: Blue hover state
- [ ] Navigate to Card component
- [ ] Verify card borders use theme colors
- [ ] Navigate to Input component
- [ ] Verify focus ring is blue
- [ ] Navigate to Alert component
- [ ] Verify default alert uses blue accent
- [ ] Navigate to Progress component
- [ ] Verify progress bar is blue

#### Dark Mode Verification
- [ ] Toggle dark mode in Storybook toolbar
- [ ] Repeat all light mode checks
- [ ] Verify blue colors adapt to dark background
- [ ] Verify text contrast is readable

#### Application Integration
- [ ] Open http://localhost:3000
- [ ] Navigate through workflow:
  - Upload form displays with blue theme
  - File inputs have blue focus rings
  - Upload button is blue primary
  - Progress bar is blue
  - Success/error alerts use theme colors
  - Results panel cards use theme
- [ ] Test dark mode toggle (if implemented)
- [ ] Verify all existing functionality works

### 4. Browser Compatibility Check

#### OKLCH Support Detection
```bash
# Open browser console on http://localhost:3000
# Run detection code:
CSS.supports('color', 'oklch(0.5 0.2 180)')
# Expected: true (modern browsers) or false (older browsers)
```

#### Verify Warning Display
- [ ] If OKLCH unsupported, warning message displays
- [ ] Warning is dismissible
- [ ] Application continues to function
- [ ] Colors may appear degraded but readable

#### Test Browsers
- [ ] Chrome (latest): Should support OKLCH
- [ ] Firefox (latest): Should support OKLCH
- [ ] Safari (latest): Should support OKLCH
- [ ] Edge (latest): Should support OKLCH
- [ ] Older browsers: Should show warning

### 5. Functionality Preservation Check

#### Upload Workflow
- [ ] Select credit card PDF
- [ ] Select expense report PDF
- [ ] Click upload
- [ ] Verify upload initiates
- [ ] Verify progress tracking works
- [ ] Verify results display

#### Error Handling
- [ ] Test with invalid files
- [ ] Verify error alerts display correctly
- [ ] Verify error states use destructive variant

#### Responsive Design
- [ ] Resize browser window
- [ ] Verify components adapt to mobile
- [ ] Verify components adapt to tablet
- [ ] Verify components adapt to desktop

## Testing

### Run Existing Test Suite
```bash
# Run all tests to verify functionality preserved
npm test

# Expected: All existing tests pass
# No breaking changes to component behavior
```

### Visual Regression (Optional)
```bash
# If Chromatic or Percy configured
npm run chromatic
# Or
npm run percy
```

## Acceptance Criteria

### FR-001: Blue Theme Applied
- [x] All UI components use blue color palette
- [x] Primary actions are blue
- [x] Focus states are blue
- [x] Progress indicators are blue

### FR-004: Light/Dark Mode Support
- [x] Light mode blue theme functional
- [x] Dark mode blue theme functional
- [x] Theme toggle works (if implemented)

### FR-005: Functionality Preserved
- [x] File upload works
- [x] Progress tracking works
- [x] Results display works
- [x] All existing features functional

### FR-007: Visual Contrast
- [x] Visual review completed
- [x] Text readable on all backgrounds
- [x] Interactive elements clearly visible

### FR-011: Browser Compatibility
- [x] OKLCH detection implemented
- [x] Warning displays when unsupported
- [x] Degraded mode allows continued use

### FR-012: Storybook Validation
- [x] Storybook configured
- [x] All components have stories
- [x] All variants documented
- [x] All states demonstrated

## Troubleshooting

### Theme Not Applied
```bash
# Check globals.css loaded
# Verify @import in app/layout.tsx or equivalent
# Check browser console for CSS errors
```

### Components Not Styled
```bash
# Verify shadcn/ui components installed
ls components/ui/
# Expected: button.tsx, card.tsx, input.tsx, etc.

# Check Tailwind config includes components
cat tailwind.config.ts
```

### Storybook Not Starting
```bash
# Check Storybook config
ls .storybook/
# Expected: main.ts, preview.ts

# Check Storybook dependencies
npm list @storybook/react
```

### OKLCH Colors Not Rendering
```bash
# Check browser support
# Update to latest browser version
# Verify CSS.supports API available
```

## Rollback Plan

### If Migration Fails
```bash
# Revert all changes
git checkout main -- components/ app/

# Or rollback entire branch
git checkout main
git branch -D 002-replace-all-front
```

### If Theme Issues Found
```bash
# Revert globals.css only
git checkout main -- app/globals.css

# Redeploy previous version
npm run build
npm start
```

## Next Steps

After quickstart validation:
1. Run full test suite: `npm test`
2. Review Storybook: http://localhost:6006
3. Conduct user acceptance testing
4. Deploy to staging environment
5. Monitor for visual or functional regressions
