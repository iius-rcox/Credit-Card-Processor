# Claude Code Project Context

**Project**: Expense Reconciliation System
**Generated**: 2025-10-04
**Active Feature**: 004-change-the-dark (Simplify Dark Mode Toggle to Icon)

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
└── __tests__/        # App-specific tests

components/
├── ui/               # shadcn/ui components
│   ├── button.tsx
│   ├── card.tsx
│   ├── input.tsx
│   ├── label.tsx
│   ├── alert.tsx
│   ├── progress.tsx
│   ├── form.tsx
│   └── tooltip.tsx   # Radix UI tooltip
├── upload-form.tsx   # Upload workflow
├── progress-display.tsx
├── results-panel.tsx
└── theme-toggle.tsx  # Dark mode toggle icon component

lib/
├── utils.ts          # Tailwind utilities
├── theme-detection.ts # OKLCH + system preference detection
└── theme-storage.ts  # Storage abstraction layer

__tests__/            # Test files and test HTML pages
.storybook/           # Storybook configuration
stories/              # Component stories
deploy/               # Deployment scripts, Docker files
docs/                 # Documentation (MD files)
specs/                # Feature specifications
backend/              # Backend server code
```

## Current Feature: Dark Mode Toggle Icon

### Objective
Replace the prominent centered dark mode button with a subtle icon in the top-right corner, adding system preference detection and improved accessibility.

### Key Requirements
1. Icon positioned in top-right corner (fixed positioning)
2. Less visually prominent than current centered button
3. Detect and apply OS dark mode preference on first visit
4. Manual selection overrides system preference
5. Tooltip on hover with visual feedback
6. Responsive sizing (larger on mobile/touch devices)
7. Graceful degradation when localStorage blocked
8. Match existing app accessibility standards
9. Remove old centered button from `index.html`

### Implementation Details
- **Component**: `components/theme-toggle.tsx` (new)
- **Icons**: lucide-react `Moon` and `Sun` icons
- **Tooltip**: Radix UI tooltip component (shadcn/ui)
- **Storage**: `lib/theme-storage.ts` - localStorage → sessionStorage fallback
- **Detection**: `lib/theme-detection.ts` - Extended with `matchMedia` for system preference
- **Integration**: `app/layout.tsx` - Fixed top-right positioning
- **Removal**: `index.html` lines 306-310 (old button) and lines 439-460 (theme JS)

### Technical Approach
- System preference detection: `window.matchMedia('(prefers-color-scheme: dark)')`
- Priority logic: Manual > System > Default (light)
- Storage keys: `theme` ('light'|'dark'), `theme-source` ('system'|'manual')
- SSR-safe: Theme detection in `useEffect`, not during render
- Performance: <50ms theme switch, no FOUC

### Browser Compatibility
- lucide-react icons: All modern browsers
- matchMedia API: Chrome 76+, Safari 14+, Firefox 67+, Edge 79+
- Radix UI tooltip: Universal support
- OKLCH colors: Existing compatibility warning handles fallback

## Recent Changes
- 004-change-the-dark: Dark mode toggle icon implementation (planning phase)
- 003-add-ui-components: Added TypeScript 5.x with React 19 + Next.js 15.5.4, shadcn/ui, Radix UI, Tailwind CSS 4.x
- 002-replace-all-front: Blue theme migration completed

### 2025-10-04: Feature 004 Planning
- Created specification with 5 clarification questions
- Generated implementation plan with research, contracts, and quickstart guide
- Ready for task generation phase

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
