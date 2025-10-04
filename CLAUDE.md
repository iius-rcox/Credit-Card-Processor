# Claude Code Project Context

**Project**: Expense Reconciliation System
**Generated**: 2025-10-03
**Active Feature**: 002-replace-all-front (Replace Front-End UI with shadcn/ui Blue Theme)

## Tech Stack

### Languages & Frameworks
- TypeScript 5.x
- React 19
- Next.js 15.5.4 (App Directory)

### UI & Styling
- shadcn/ui component library
- Radix UI primitives
- Tailwind CSS 4.x
- class-variance-authority
- OKLCH color format for theming

### Testing & Tools
- Component storybook for visual validation
- Existing test suite preservation
- Browser compatibility detection

## Project Structure

```
app/                    # Next.js app directory
├── layout.tsx         # Root layout
├── page.tsx          # Main page (upload, progress, results)
├── globals.css       # Theme CSS variables
└── __tests__/        # Existing tests

components/
├── ui/               # shadcn/ui components
│   ├── button.tsx
│   ├── card.tsx
│   ├── input.tsx
│   ├── label.tsx
│   ├── alert.tsx
│   ├── progress.tsx
│   └── form.tsx
├── upload-form.tsx   # Upload workflow
├── progress-display.tsx
└── results-panel.tsx

lib/
├── utils.ts          # Tailwind utilities
└── theme-detection.ts # OKLCH browser support

.storybook/           # Component stories
└── stories/
```

## Current Feature: Blue Theme Migration

### Objective
Migrate all front-end UI components to shadcn/ui with blue color theme while preserving all existing functionality.

### Key Requirements
1. Apply blue theme using OKLCH color format
2. Support light and dark modes
3. Preserve all existing component functionality
4. Implement browser compatibility detection
5. Create component storybook for validation
6. No specific performance target (minimize impact)
7. Visual contrast verified through review (no WCAG compliance required)

### Component Migration Map
- Button → @/components/ui/button
- Card → @/components/ui/card
- Input → @/components/ui/input
- Label → @/components/ui/label
- Alert → @/components/ui/alert
- Progress → @/components/ui/progress
- Form → @/components/ui/form

### Theme Configuration
Blue base color configured in `components.json`:
```json
{
  "tailwind": {
    "baseColor": "blue",
    "cssVariables": true
  }
}
```

OKLCH CSS variables defined in `app/globals.css`:
- Primary: Blue brand color for CTAs
- Secondary: Neutral grays
- Accent: Blue highlights
- Destructive: Red for errors
- Muted: Low saturation backgrounds

### Browser Compatibility
- Detect OKLCH support: `CSS.supports('color', 'oklch(0.5 0.2 180)')`
- Display warning if unsupported
- Allow degraded color rendering
- Continue full functionality

## Recent Changes
- 002-replace-all-front: Added TypeScript 5.x + React 19, Next.js 15.5.4, shadcn/ui, Tailwind CSS 4.x, Radix UI

### 2025-10-03: Feature 002 Planning
- Created implementation plan with 5 phases
- Defined theme configuration entity

## Development Guidelines

### Component Migration
1. One component at a time (incremental)
2. Preserve existing props/API
3. Test after each migration
4. Visual comparison (before/after)
5. Wrap in error boundaries

### Theming Approach
1. Define CSS variables in globals.css
2. Use @theme inline directive for Tailwind
3. Light mode (:root) and dark mode (.dark)
4. OKLCH format for perceptual uniformity
5. Detect browser support early

### Testing Strategy
1. Run existing test suite (verify preservation)
2. Create Storybook stories for all components
3. Document all variants and states
4. Visual review in light/dark modes
5. Browser compatibility testing

## Useful Commands

```bash
# Development
npm run dev              # Start Next.js dev server
npm run storybook        # Start Storybook

# Build & Test
npm run build           # Production build
npm test               # Run test suite

# Storybook
npm run build-storybook # Build static storybook
```

## Key Files

### Configuration
- `components.json` - shadcn/ui config (blue theme)
- `tailwind.config.ts` - Tailwind configuration
- `tsconfig.json` - TypeScript configuration

### Documentation
- `specs/002-replace-all-front/spec.md` - Feature specification
- `specs/002-replace-all-front/plan.md` - Implementation plan
- `specs/002-replace-all-front/research.md` - Technical research
- `specs/002-replace-all-front/data-model.md` - Data model
- `specs/002-replace-all-front/quickstart.md` - Validation guide
- `specs/002-replace-all-front/contracts/` - Component contracts

### Source
- `app/globals.css` - Theme CSS variables
- `components/ui/*` - shadcn/ui components
- `lib/theme-detection.ts` - OKLCH support detection (to create)
- `.storybook/*` - Storybook configuration (to create)

## Notes

- No backend changes required (UI-only migration)
- OKLCH browser support: Chrome 111+, Safari 15.4+, Firefox 113+
- Storybook 8.x for visual validation
- Focus on visual consistency and functionality preservation
- Performance impact monitoring (no specific benchmark)

---
*Last Updated: 2025-10-03 | Feature: 002-replace-all-front*
