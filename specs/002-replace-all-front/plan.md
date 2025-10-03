# Implementation Plan: Replace Front-End UI with shadcn/ui Blue Theme

**Branch**: `002-replace-all-front` | **Date**: 2025-10-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-replace-all-front/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path ✓
2. Fill Technical Context (scan for NEEDS CLARIFICATION) ✓
   → Detect Project Type: Web (Next.js frontend)
   → Set Structure Decision: Web application structure
3. Fill Constitution Check section ✓
4. Evaluate Constitution Check section ✓
5. Execute Phase 0 → research.md ✓
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md ✓
7. Re-evaluate Constitution Check ✓
8. Plan Phase 2 → Describe task generation approach ✓
9. STOP - Ready for /tasks command ✓
```

## Summary
Migrate all existing front-end UI components to shadcn/ui component library with blue theme styling. Replace custom components (Button, Card, Input, Label, Alert, Progress, Form) with shadcn/ui equivalents while maintaining all existing functionality. Apply blue color palette using OKLCH CSS variables for both light and dark modes. Implement browser compatibility detection and storybook for visual validation.

## Technical Context
**Language/Version**: TypeScript 5.x, React 19, Next.js 15.5.4
**Primary Dependencies**: shadcn/ui, Radix UI, Tailwind CSS 4.x, class-variance-authority
**Storage**: N/A (UI-only migration)
**Testing**: Component storybook for visual validation, existing test suite preservation
**Target Platform**: Web browsers (Chrome, Firefox, Safari, Edge)
**Project Type**: Web - Next.js application with app directory structure
**Performance Goals**: No specific performance target (FR-013: minimize impact, no benchmark)
**Constraints**:
  - Preserve all existing component functionality (FR-005)
  - Support OKLCH color format with degraded fallback (FR-011)
  - Visual contrast verification through manual review (FR-007)
**Scale/Scope**:
  - All existing components: Button, Card, Input, Label, Alert, Progress, Form
  - Upload form, Progress display, Results panel workflows
  - Light and dark mode support

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution file is a template placeholder. Proceeding with standard React/Next.js best practices:
- ✓ Component-based architecture (React standard)
- ✓ Type safety with TypeScript
- ✓ Accessibility considerations (visual review)
- ✓ Responsive design maintenance (FR-009)
- ✓ Test preservation (existing test suite)

**Status**: PASS (no constitutional violations - template constitution)

## Project Structure

### Documentation (this feature)
```
specs/002-replace-all-front/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
app/
├── layout.tsx           # Root layout (theme provider context)
├── page.tsx            # Main page (upload, progress, results)
├── globals.css         # Theme CSS variables (blue palette)
└── __tests__/          # Existing tests to preserve

components/
├── ui/                 # shadcn/ui components
│   ├── button.tsx
│   ├── card.tsx
│   ├── input.tsx
│   ├── label.tsx
│   ├── alert.tsx
│   ├── progress.tsx
│   └── form.tsx
├── upload-form.tsx     # Uses shadcn components
├── progress-display.tsx # Uses shadcn components
└── results-panel.tsx   # Uses shadcn components

lib/
├── utils.ts            # Tailwind utilities
└── theme-detection.ts  # OKLCH browser support detection

.storybook/             # Component storybook (new)
└── stories/            # Component stories for validation
```

**Structure Decision**: Web application structure with Next.js app directory. Frontend-only migration focusing on UI components and theming. No backend changes required.

## Phase 0: Outline & Research
**Status**: ✓ Complete

All technical context is known from existing project and shadcn/ui documentation:
- **Next.js 15.5.4**: App directory, React 19, Turbopack
- **shadcn/ui**: Component library setup with components.json already configured
- **Tailwind CSS 4.x**: Using CSS variables for theming
- **Blue theme**: OKLCH color format from shadcn/ui theming documentation
- **Storybook**: For visual component validation (Storybook 8.x)

No NEEDS CLARIFICATION items - all requirements clear from spec and clarifications session.

**Output**: research.md created with decisions and rationale

## Phase 1: Design & Contracts
**Status**: ✓ Complete

### Data Model
**Theme Configuration Entity**:
- Color variables (primary, secondary, accent, muted, destructive, etc.)
- Light mode values (OKLCH format)
- Dark mode values (OKLCH format)
- Radius values for component corners

**Component Library Entity**:
- shadcn/ui component variants
- Component states (default, hover, focus, disabled, error)
- Theme variable consumption patterns

### Contracts
Since this is a UI-only migration with no API changes, contracts focus on:
1. **Theme contract** (`contracts/theme-variables.yaml`): CSS variable definitions
2. **Component contract** (`contracts/component-variants.yaml`): Component prop interfaces
3. **Browser detection contract** (`contracts/browser-detection.yaml`): OKLCH support check

### Integration Tests
From acceptance scenarios:
1. Theme consistency test (all components display blue theme)
2. Interactive states test (hover, focus feedback)
3. Light/dark mode test (theme switching)
4. Workflow consistency test (upload → processing → results)
5. Functionality preservation test (existing features work)
6. Storybook validation test (all component states/variants)

**Output**: data-model.md, /contracts/*, quickstart.md, CLAUDE.md

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
1. Theme setup tasks:
   - Update globals.css with blue theme OKLCH variables
   - Configure light mode colors
   - Configure dark mode colors
   - Add OKLCH browser detection utility

2. Component migration tasks (parallel where possible):
   - Update Button component imports/usage [P]
   - Update Card component imports/usage [P]
   - Update Input component imports/usage [P]
   - Update Label component imports/usage [P]
   - Update Alert component imports/usage [P]
   - Update Progress component imports/usage [P]
   - Update Form component imports/usage [P]

3. Page integration tasks:
   - Update upload-form.tsx with themed components
   - Update progress-display.tsx with themed components
   - Update results-panel.tsx with themed components
   - Update main page.tsx with themed components

4. Storybook setup tasks:
   - Install Storybook 8.x
   - Configure Storybook with Tailwind/theme
   - Create stories for each component
   - Create stories for all states/variants

5. Validation tasks:
   - Run existing test suite (verify preservation)
   - Visual review in storybook (light mode)
   - Visual review in storybook (dark mode)
   - Browser compatibility testing

**Ordering Strategy**:
- Theme setup first (foundation)
- Component migrations in parallel (independent)
- Page integrations after components
- Storybook setup after components
- Validation last

**Estimated Output**: 20-25 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, storybook review, browser testing)

## Complexity Tracking
*No constitutional violations - template constitution used*

No complexity deviations to track.

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none)

---
*Based on Constitution template - See `.specify/memory/constitution.md`*
