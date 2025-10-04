
# Implementation Plan: Replace Front-End UI with shadcn/ui Blue Theme

**Branch**: `002-replace-all-front` | **Date**: 2025-10-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-replace-all-front/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code, or `AGENTS.md` for all other agents).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Migrate all front-end UI components to shadcn/ui with blue theme while preserving existing functionality. Replace all existing components (Button, Card, Input, Label, Alert, Progress, Form) with shadcn/ui equivalents using blue color palette from OKLCH format, supporting both light and dark modes.

## Technical Context
**Language/Version**: TypeScript 5.x
**Primary Dependencies**: React 19, Next.js 15.5.4, shadcn/ui, Tailwind CSS 4.x, Radix UI
**Storage**: N/A (UI-only migration)
**Testing**: Jest/React Testing Library (existing test suite preservation)
**Target Platform**: Web browsers (Chrome 111+, Safari 15.4+, Firefox 113+ for OKLCH support)
**Project Type**: web - Next.js frontend application
**Performance Goals**: No specific performance target (minimize impact)
**Constraints**: OKLCH browser compatibility warning, preserve all existing functionality
**Scale/Scope**: All UI components (Button, Card, Input, Label, Alert, Progress, Form), component storybook validation

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Incremental Migration Principle
✅ **PASS**: Components migrated one at a time, preserving existing functionality
- Each component migration is isolated and testable
- Existing tests continue to pass during migration

### Testing-First Approach
✅ **PASS**: Existing test suite preserved, new storybook validation added
- All existing tests must continue passing
- Component storybook provides visual validation

### Browser Compatibility
✅ **PASS**: OKLCH feature detection with graceful degradation
- Detects browser support for OKLCH colors
- Displays warning but continues operation with degraded rendering

### Simplicity Principle
✅ **PASS**: UI-only migration, no backend changes
- Focused scope on frontend component replacement
- No complex architectural changes required

### Post-Design Re-evaluation
✅ **PASS**: All constitutional principles maintained after detailed design
- Component contracts preserve existing APIs (incremental principle)
- Storybook provides comprehensive testing approach
- Browser detection with graceful degradation maintains compatibility
- No additional complexity introduced beyond essential theme configuration

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
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->
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

**Structure Decision**: Next.js web application with App Router. Frontend-only migration using existing Next.js structure with shadcn/ui components in `/components/ui/` directory.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh claude`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each component contract → implementation task
- Theme configuration → CSS variables setup task
- Browser detection → utility implementation task
- Storybook setup → story creation tasks
- Testing validation → test execution tasks

**Ordering Strategy**:
1. **Foundation Tasks**: Theme configuration, CSS variables, browser detection
2. **Component Migration**: Button → Card → Input/Label → Alert → Progress → Form (incremental)
3. **Testing Tasks**: Storybook setup, story creation for each component [P]
4. **Validation Tasks**: Integration testing, visual validation, quickstart execution
5. **Preservation Tasks**: Existing test verification after each component

**Task Categorization**:
- **[P]** Parallel execution (independent components, stories)
- **[S]** Sequential (theme setup before components, component order matters)
- **[V]** Validation (after implementation completion)

**Estimated Output**:
- Foundation: 5 tasks (theme setup, browser detection, Storybook init)
- Component migration: 7 tasks (one per component)
- Testing: 8 tasks (story creation per component + integration)
- Validation: 4 tasks (test suite, visual review, quickstart validation, performance check)
- **Total**: ~24 numbered, ordered tasks in tasks.md

**Task Dependencies**:
- Theme CSS variables must be configured before any component migration
- Browser detection utility created early for integration testing
- Component migration follows dependency order (Button first, Form last)
- Storybook stories created for each component after migration
- Integration testing after all components migrated
- Final validation runs quickstart.md checklist

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [x] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none required)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
