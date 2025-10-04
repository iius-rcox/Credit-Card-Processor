# Tasks: Replace Front-End UI with shadcn/ui Blue Theme

**Input**: Design documents from `/specs/002-replace-all-front/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Tech stack: TypeScript 5.x, React 19, Next.js 15.5.4, shadcn/ui, Tailwind CSS 4.x
   → Structure: Next.js web application with App Router
2. Load design documents:
   → data-model.md: Theme Configuration, Component Library, Browser Capability entities
   → contracts/: Component API contracts for 7 components + theme detection
   → research.md: Technology decisions for OKLCH, Storybook, migration strategy
3. Generate tasks by category:
   → Setup: Storybook installation, theme configuration
   → Tests: Component stories, contract validation tests
   → Core: Theme CSS variables, browser detection, component migration
   → Integration: Application integration, existing test verification
   → Polish: Visual validation, performance check, quickstart execution
4. Apply task rules:
   → Component migrations can be parallel [P] (different files)
   → Story creation can be parallel [P] (different files)
   → Theme setup must come before component migration
   → Integration tests after all components migrated
5. Number tasks sequentially (T001, T002...)
6. Task dependencies: Theme → Components → Stories → Integration → Validation
7. Parallel execution for independent components and stories
8. All component contracts have implementation and stories
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Next.js App Router**: `app/`, `components/`, `lib/` at repository root
- **Storybook**: `.storybook/`, `stories/` directories
- **Tests**: `app/__tests__/` (existing test location)

## Phase 3.1: Setup & Foundation

### Theme Configuration Setup
- [x] T001 Configure blue theme CSS variables in `/Users/rogercox/Credit-Card-Processor/app/globals.css`
- [x] T002 Create browser OKLCH support detection utility in `/Users/rogercox/Credit-Card-Processor/lib/theme-detection.ts`
- [x] T003 Install Storybook dependencies for Next.js 15.5.4 integration

### Storybook Configuration
- [x] T004 Initialize Storybook configuration for Next.js in `/Users/rogercox/Credit-Card-Processor/.storybook/main.ts`
- [x] T005 Configure Storybook preview with Tailwind CSS and theme support in `/Users/rogercox/Credit-Card-Processor/.storybook/preview.ts`

## Phase 3.2: Component Migration (TDD Approach)
**CRITICAL: Component implementations MUST be done incrementally, preserving existing functionality**

### Button Component Migration
- [x] T006 [P] Create Button component story in `/Users/rogercox/Credit-Card-Processor/stories/Button.stories.tsx`
- [x] T007 Migrate Button component to shadcn/ui in `/Users/rogercox/Credit-Card-Processor/components/ui/button.tsx`
- [x] T008 Verify existing Button usage and run tests after migration

### Card Component Migration
- [x] T009 [P] Create Card component stories in `/Users/rogercox/Credit-Card-Processor/stories/Card.stories.tsx`
- [x] T010 Migrate Card component to shadcn/ui in `/Users/rogercox/Credit-Card-Processor/components/ui/card.tsx`
- [x] T011 Verify existing Card usage and run tests after migration

### Input & Label Component Migration
- [x] T012 [P] Create Input component story in `/Users/rogercox/Credit-Card-Processor/stories/Input.stories.tsx`
- [x] T013 [P] Create Label component story in `/Users/rogercox/Credit-Card-Processor/stories/Label.stories.tsx`
- [x] T014 Migrate Input component to shadcn/ui in `/Users/rogercox/Credit-Card-Processor/components/ui/input.tsx`
- [x] T015 Migrate Label component to shadcn/ui in `/Users/rogercox/Credit-Card-Processor/components/ui/label.tsx`
- [x] T016 Verify existing Input/Label usage and run tests after migration

### Alert Component Migration
- [x] T017 [P] Create Alert component story in `/Users/rogercox/Credit-Card-Processor/stories/Alert.stories.tsx`
- [x] T018 Migrate Alert component to shadcn/ui in `/Users/rogercox/Credit-Card-Processor/components/ui/alert.tsx`
- [x] T019 Verify existing Alert usage and run tests after migration

### Progress Component Migration
- [x] T020 [P] Create Progress component story in `/Users/rogercox/Credit-Card-Processor/stories/Progress.stories.tsx`
- [x] T021 Migrate Progress component to shadcn/ui in `/Users/rogercox/Credit-Card-Processor/components/ui/progress.tsx`
- [x] T022 Verify existing Progress usage and run tests after migration

### Form Component Migration
- [x] T023 [P] Create Form component story in `/Users/rogercox/Credit-Card-Processor/stories/Form.stories.tsx`
- [x] T024 Migrate Form component to shadcn/ui in `/Users/rogercox/Credit-Card-Processor/components/ui/form.tsx`
- [x] T025 Verify existing Form usage and run tests after migration

## Phase 3.3: Application Integration

### Page Component Integration
- [x] T026 [P] Create UploadForm integration story in `/Users/rogercox/Credit-Card-Processor/stories/UploadForm.stories.tsx`
- [x] T027 [P] Create ProgressDisplay integration story in `/Users/rogercox/Credit-Card-Processor/stories/ProgressDisplay.stories.tsx`
- [x] T028 [P] Create ResultsPanel integration story in `/Users/rogercox/Credit-Card-Processor/stories/ResultsPanel.stories.tsx`
- [x] T029 Update upload-form.tsx to use new shadcn/ui components in `/Users/rogercox/Credit-Card-Processor/components/upload-form.tsx`
- [x] T030 Update progress-display.tsx to use new shadcn/ui components in `/Users/rogercox/Credit-Card-Processor/components/progress-display.tsx`
- [x] T031 Update results-panel.tsx to use new shadcn/ui components in `/Users/rogercox/Credit-Card-Processor/components/results-panel.tsx`

### Browser Compatibility Integration
- [x] T032 Integrate OKLCH detection into app layout in `/Users/rogercox/Credit-Card-Processor/app/layout.tsx`
- [x] T033 Create browser compatibility warning component in `/Users/rogercox/Credit-Card-Processor/components/compatibility-warning.tsx`

## Phase 3.4: Validation & Testing

### Contract Validation
- [x] T034 Verify all component props work as documented (Button contract validation)
- [x] T035 Verify all component props work as documented (Card contract validation)
- [x] T036 Verify all component props work as documented (Input/Label contract validation)
- [x] T037 Verify all component props work as documented (Alert contract validation)
- [x] T038 Verify all component props work as documented (Progress contract validation)
- [x] T039 Verify all component props work as documented (Form contract validation)

### Integration Testing
- [x] T040 Run complete existing test suite to verify no functionality broken
- [x] T041 Test upload workflow end-to-end with new components
- [x] T042 Test browser compatibility warning display and dismissal
- [x] T043 Test light/dark mode theme switching functionality

### Visual Validation
- [x] T044 Execute quickstart visual validation checklist for light mode
- [x] T045 Execute quickstart visual validation checklist for dark mode
- [x] T046 Verify Storybook displays all component variants correctly
- [x] T047 Test responsive behavior across device sizes

## Phase 3.5: Polish & Performance

### Performance Validation
- [x] T048 Measure and verify bundle size impact is acceptable
- [x] T049 Test theme switching performance and responsiveness
- [x] T050 Verify page load times maintained

### Documentation & Cleanup
- [x] T051 Execute complete quickstart.md validation checklist
- [x] T052 Verify all acceptance criteria from feature specification met
- [x] T053 Clean up any unused imports or component files
- [x] T054 Final review of all component implementations

## Dependencies

### Sequential Dependencies
- T001, T002 must complete before any component migration
- T003, T004, T005 must complete before story creation
- T007 blocks T008 (Button impl before verification)
- T010 blocks T011 (Card impl before verification)
- T014, T015 block T016 (Input/Label impl before verification)
- T018 blocks T019 (Alert impl before verification)
- T021 blocks T022 (Progress impl before verification)
- T024 blocks T025 (Form impl before verification)
- T029, T030, T031 block T041 (Page updates before workflow testing)
- T032, T033 block T042 (Compatibility feature before testing)
- All component migrations must complete before T040 (test suite)

### Independent Parallel Tasks
**Story Creation (After Storybook Setup)**:
- T006, T009, T012, T013, T017, T020, T023 can run in parallel
- T026, T027, T028 can run in parallel

**Component Implementation (After Theme Setup)**:
- Component files are independent, but should be done incrementally for safety
- Contract validations T034-T039 can run in parallel

**Final Validation (After All Implementation)**:
- T044, T045, T046 can run in parallel
- T048, T049, T050 can run in parallel

## Parallel Execution Examples

### Foundation Setup (Parallel)
```bash
# After T001, T002 complete, launch Storybook setup:
Task: "Install Storybook dependencies for Next.js 15.5.4 integration"
Task: "Initialize Storybook configuration for Next.js in .storybook/main.ts"
Task: "Configure Storybook preview with Tailwind CSS in .storybook/preview.ts"
```

### Story Creation (Parallel)
```bash
# After Storybook configured, create all component stories:
Task: "Create Button component story in stories/Button.stories.tsx"
Task: "Create Card component stories in stories/Card.stories.tsx"
Task: "Create Input component story in stories/Input.stories.tsx"
Task: "Create Label component story in stories/Label.stories.tsx"
Task: "Create Alert component story in stories/Alert.stories.tsx"
Task: "Create Progress component story in stories/Progress.stories.tsx"
Task: "Create Form component story in stories/Form.stories.tsx"
```

### Integration Stories (Parallel)
```bash
# After page components updated:
Task: "Create UploadForm integration story in stories/UploadForm.stories.tsx"
Task: "Create ProgressDisplay integration story in stories/ProgressDisplay.stories.tsx"
Task: "Create ResultsPanel integration story in stories/ResultsPanel.stories.tsx"
```

### Contract Validation (Parallel)
```bash
# After all components migrated:
Task: "Verify all component props work as documented (Button contract validation)"
Task: "Verify all component props work as documented (Card contract validation)"
Task: "Verify all component props work as documented (Input/Label contract validation)"
Task: "Verify all component props work as documented (Alert contract validation)"
Task: "Verify all component props work as documented (Progress contract validation)"
Task: "Verify all component props work as documented (Form contract validation)"
```

## Notes
- **[P] tasks** = different files, no dependencies between them
- **Incremental migration**: Test after each component to catch issues early
- **Theme-first approach**: CSS variables must be configured before any component work
- **Storybook-driven development**: Stories help validate component behavior visually
- **Contract preservation**: All existing component APIs must work identically
- **Browser compatibility**: OKLCH detection ensures graceful degradation

## Task Generation Rules
*Applied during execution*

1. **From Component Contracts**:
   - Each component contract → story creation task [P]
   - Each component contract → implementation task (sequential for safety)
   - Each component contract → validation task [P]

2. **From Data Model Entities**:
   - Theme Configuration → CSS variables setup task
   - Browser Capability → detection utility task
   - Component Library → individual component migration tasks

3. **From Quickstart Scenarios**:
   - Visual validation → Storybook story tasks
   - Functionality preservation → existing test verification
   - Browser compatibility → warning component and integration

4. **Ordering**:
   - Setup → Theme → Components → Integration → Validation
   - Stories can be created in parallel with implementation
   - Testing after each component for incremental validation

## Validation Checklist
*GATE: Checked before completion*

- [x] All component contracts have corresponding implementation tasks
- [x] All component contracts have story creation tasks
- [x] All component contracts have validation tasks
- [x] Theme setup comes before component migration
- [x] Integration testing after all components migrated
- [x] Parallel tasks truly independent (different files)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] Quickstart scenarios covered by validation tasks
- [x] Browser compatibility requirements addressed
- [x] Existing functionality preservation verified