# Research: Replace Front-End UI with shadcn/ui Blue Theme

**Date**: 2025-10-03
**Feature**: 002-replace-all-front

## Technology Decisions

### 1. UI Component Library: shadcn/ui
**Decision**: Use shadcn/ui component library with Radix UI primitives

**Rationale**:
- Already configured in project (components.json exists)
- Copy-paste component model provides full control
- Built on Radix UI for accessibility primitives
- Tailwind CSS integration matches project stack
- TypeScript support out of the box

**Alternatives Considered**:
- MUI (Material-UI): Too opinionated, heavier bundle
- Chakra UI: Different styling approach, not Tailwind-based
- Ant Design: Less flexible theming system

### 2. Theme System: OKLCH Color Format
**Decision**: Use OKLCH color format for blue theme with CSS variables

**Rationale**:
- shadcn/ui official theming approach
- Perceptually uniform color space
- Better for programmatic color manipulation
- Supports smooth light/dark mode transitions
- Modern browsers have good support

**Alternatives Considered**:
- RGB/Hex: Less perceptually uniform
- HSL: Legacy color space, less accurate
- CSS Color Module Level 4: Similar to OKLCH but less documented

### 3. Browser Compatibility Strategy
**Decision**: Detect OKLCH support, warn users, allow degraded operation

**Rationale**:
- Clarification requirement (FR-011)
- Progressive enhancement approach
- No hard blocking of unsupported browsers
- User awareness through warning message
- Graceful degradation preserves functionality

**Implementation**:
```typescript
// Pseudo-code for detection
const supportsOKLCH = CSS.supports('color', 'oklch(0.5 0.2 180)');
if (!supportsOKLCH) {
  showWarning('Your browser has limited color support. Display may vary.');
}
```

### 4. Visual Validation: Storybook
**Decision**: Use Storybook 8.x for component visual validation

**Rationale**:
- Clarification requirement (FR-012)
- Industry standard for component documentation
- Supports all component states and variants
- Enables visual regression testing
- Integrates with Next.js and Tailwind

**Alternatives Considered**:
- Chromatic: Paid service for visual regression
- Percy: Also paid, less flexible
- Manual testing: Not scalable or repeatable

### 5. Blue Theme Configuration
**Decision**: Apply blue base color from shadcn/ui theme system

**Rationale**:
- components.json already configured with baseColor: "blue"
- Official shadcn/ui color palette
- Provides light and dark mode variants
- Includes all semantic color roles (primary, secondary, accent, etc.)

**Color Palette** (OKLCH format):
- Primary: Blue with appropriate lightness/chroma
- Secondary: Neutral gray tones
- Accent: Complementary blue variants
- Destructive: Red for errors/warnings
- Muted: Low saturation for backgrounds

## Best Practices

### shadcn/ui Component Usage
1. **Import from @/components/ui**: Always use path alias
2. **Preserve component props**: Maintain existing API surface
3. **Use cn() utility**: Merge Tailwind classes properly
4. **Variants via CVA**: Use class-variance-authority for variants
5. **Composition over props**: Build complex UIs from simple components

### Tailwind CSS 4.x Theming
1. **CSS Variables in globals.css**: Define theme tokens
2. **@theme inline directive**: Register custom properties
3. **Light/dark with :root and .dark**: Standard approach
4. **Color naming convention**: background/foreground pattern
5. **Radius tokens**: Consistent corner radius across components

### Next.js App Directory Integration
1. **Client Components**: Mark with "use client" for interactive components
2. **Server Components**: Keep static parts on server when possible
3. **Layout for theme**: Wrap in theme provider if needed
4. **Import paths**: Use @/ alias for clean imports

### Component Migration Strategy
1. **One component at a time**: Incremental migration
2. **Test after each component**: Verify functionality preserved
3. **Visual comparison**: Before/after screenshots
4. **Props compatibility**: Ensure API remains the same
5. **Error boundaries**: Wrap for graceful failure

## Technical Constraints

### Performance Considerations
- No specific target (FR-013), but monitor:
  - Bundle size impact from shadcn/ui components
  - CSS-in-JS overhead (none - using Tailwind)
  - Theme variable computation cost (minimal)
  - Hydration performance (client components)

### Browser Support
- Modern browsers: Chrome, Firefox, Safari, Edge (latest 2 versions)
- OKLCH support: Chrome 111+, Safari 15.4+, Firefox 113+
- Fallback: Warning message + degraded colors for older browsers

### Accessibility
- Visual review only (no WCAG target per clarification)
- Preserve existing accessibility features
- Radix UI provides ARIA attributes
- Keyboard navigation maintained

## Dependencies

### Existing (Already Installed)
- shadcn/ui CLI (v3.3.1)
- @radix-ui/react-* primitives
- Tailwind CSS (v4.x)
- class-variance-authority
- clsx, tailwind-merge

### New Dependencies Required
- Storybook 8.x (@storybook/react, @storybook/nextjs)
- Storybook addons (@storybook/addon-essentials, @storybook/addon-themes)

## Risk Assessment

### Low Risk
- Component migration (incremental, reversible)
- Theme application (CSS variables, easy rollback)
- Storybook setup (dev dependency only)

### Medium Risk
- OKLCH browser support (mitigated with detection + warning)
- Bundle size increase (monitor, tree-shake unused components)

### Mitigations
- Incremental rollout: One component at a time
- Feature flag: Could gate theme migration if needed
- Rollback plan: Git revert + redeploy
- Testing: Preserve existing test suite, add visual validation
