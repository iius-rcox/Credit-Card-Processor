# Tasks: Session Management UI Components

**Input**: Design documents from `/specs/003-add-ui-components/`
**Prerequisites**: plan.md (✓), research.md (✓), data-model.md (✓), contracts/ (✓)

## Execution Flow (main)
```
1. Load plan.md from feature directory ✓
   → Extract: TypeScript 5.x, React 19, Next.js 15.5.4, shadcn/ui
2. Load optional design documents: ✓
   → data-model.md: Extract entities → model tasks
   → contracts/: session-management.yaml → contract test task
   → research.md: Extract decisions → setup tasks
3. Generate tasks by category:
   → Setup: project init, dependencies, linting
   → Tests: contract tests, integration tests
   → Core: models, services, components
   → Integration: context, storage, pages
   → Polish: unit tests, storybook, validation
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness: ✓
   → All contracts have tests ✓
   → All entities have models ✓
   → All user stories have integration tests ✓
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Web app**: Frontend components at repository root
- Paths shown below assume Next.js app directory structure

## Phase 3.1: Setup
- [x] T001 Create session management component directory structure at `components/session-management/`
- [x] T002 Initialize session type definitions in `lib/session-types.ts`
- [x] T003 [P] Configure session management utilities in `lib/session-utils.ts`

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [x] T004 [P] Contract test GET /api/session/{sessionId} in `__tests__/contracts/test_session_get.ts`
- [x] T005 [P] Contract test POST /api/session/{sessionId}/update in `__tests__/contracts/test_session_update.ts`
- [x] T006 [P] Contract test GET /api/reports/{sessionId} in `__tests__/contracts/test_reports_get.ts`
- [x] T007 [P] Integration test session creation workflow in `__tests__/integration/test_session_creation.ts`
- [x] T008 [P] Integration test session renaming in `__tests__/integration/test_session_renaming.ts`
- [x] T009 [P] Integration test receipt update workflow in `__tests__/integration/test_receipt_update.ts`
- [x] T010 [P] Integration test session browser filtering in `__tests__/integration/test_session_filtering.ts`

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [x] T011 [P] MonthSession model implementation in `lib/session-types.ts`
- [x] T012 [P] SessionStorage model implementation in `lib/session-types.ts`
- [x] T013 [P] Session storage utilities in `lib/session-storage.ts`
- [x] T014 [P] SessionProvider context in `components/session-management/session-provider.tsx`
- [x] T015 [P] SessionCard component in `components/session-management/session-card.tsx`
- [x] T016 [P] SessionCreator component in `components/session-management/session-creator.tsx`
- [x] T017 [P] SessionRenamer component in `components/session-management/session-renamer.tsx`
- [x] T018 [P] ReceiptUpdater component in `components/session-management/receipt-updater.tsx`
- [x] T019 [P] SessionBrowser container in `components/session-management/session-browser.tsx`

## Phase 3.4: Integration
- [x] T020 SessionProvider integration in `app/layout.tsx`
- [x] T021 Sessions page at `app/sessions/page.tsx`
- [x] T022 Session details page at `app/sessions/[sessionId]/page.tsx`
- [x] T023 Receipt update page at `app/sessions/[sessionId]/update/page.tsx`
- [x] T024 Main page integration in `app/page.tsx`
- [x] T025 API client session methods in existing API utilities
- [x] T026 Session browser filtering and search functionality

## Phase 3.5: Polish
- [x] T027 [P] Unit tests for session utilities in `__tests__/unit/test_session_utils.ts`
- [x] T028 [P] Unit tests for storage functions in `__tests__/unit/test_session_storage.ts`
- [x] T029 [P] SessionCard storybook story in `stories/session-management/SessionCard.stories.tsx`
- [x] T030 [P] SessionCreator storybook story in `stories/session-management/SessionCreator.Stories.tsx`
- [x] T031 [P] SessionBrowser storybook story in `stories/session-management/SessionBrowser.stories.tsx`
- [x] T032 [P] ReceiptUpdater storybook story in `stories/session-management/ReceiptUpdater.stories.tsx`
- [x] T033 Performance optimization for session list rendering
- [x] T034 Error boundary implementation for session components
- [x] T035 Execute quickstart validation scenarios from `quickstart.md`

## Dependencies
- Tests (T004-T010) before implementation (T011-T019)
- T011-T012 block T013 (types before utilities)
- T013 blocks T014 (storage before context)
- T014 blocks T015-T018 (context before components)
- T015-T018 block T019 (components before container)
- T019 blocks T020-T024 (container before pages)
- Implementation (T011-T026) before polish (T027-T035)

## Parallel Example
```bash
# Launch T004-T006 together (contract tests):
Task --subagent_type=test-automator --description="Contract test GET session" --prompt="Create contract test for GET /api/session/{sessionId} endpoint in __tests__/contracts/test_session_get.ts following contracts/session-management.yaml schema. Test must FAIL initially."

Task --subagent_type=test-automator --description="Contract test POST update" --prompt="Create contract test for POST /api/session/{sessionId}/update endpoint in __tests__/contracts/test_session_update.ts following contracts/session-management.yaml schema. Test must FAIL initially."

Task --subagent_type=test-automator --description="Contract test GET reports" --prompt="Create contract test for GET /api/reports/{sessionId} endpoint in __tests__/contracts/test_reports_get.ts following contracts/session-management.yaml schema. Test must FAIL initially."
```

```bash
# Launch T015-T018 together (independent components):
Task --subagent_type=frontend-developer --description="Create SessionCard component" --prompt="Implement SessionCard component in components/session-management/session-card.tsx using shadcn/ui primitives. Display session name, status, dates, file counts from MonthSession interface."

Task --subagent_type=frontend-developer --description="Create SessionCreator component" --prompt="Implement SessionCreator component in components/session-management/session-creator.tsx with form for creating new sessions. Use shadcn/ui form components with validation."

Task --subagent_type=frontend-developer --description="Create SessionRenamer component" --prompt="Implement SessionRenamer component in components/session-management/session-renamer.tsx as modal dialog for renaming sessions. Use shadcn/ui dialog and form components."

Task --subagent_type=frontend-developer --description="Create ReceiptUpdater component" --prompt="Implement ReceiptUpdater component in components/session-management/receipt-updater.tsx with file upload and progress tracking. Validate PDF files only."
```

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing
- Commit after each task
- All components use shadcn/ui blue theme
- Session storage uses localStorage with 1-year TTL
- Maximum 24 sessions enforced

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts**:
   - session-management.yaml → 3 contract test tasks [P]
   - Each endpoint → implementation integration task

2. **From Data Model**:
   - MonthSession entity → model creation task [P]
   - SessionStorage entity → storage utilities task [P]
   - Relationships → service layer tasks

3. **From User Stories** (quickstart.md):
   - Session creation workflow → integration test [P]
   - Session renaming → integration test [P]
   - Receipt update workflow → integration test [P]
   - Session filtering → integration test [P]

4. **Ordering**:
   - Setup → Tests → Models → Components → Pages → Polish
   - Dependencies block parallel execution

## Validation Checklist
*GATE: Checked by main() before returning*

- [x] All contracts have corresponding tests (T004-T006)
- [x] All entities have model tasks (T011-T012)
- [x] All tests come before implementation (T004-T010 before T011+)
- [x] Parallel tasks truly independent (different files, no shared state)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] Component architecture follows shadcn/ui patterns
- [x] Integration tests cover all quickstart scenarios