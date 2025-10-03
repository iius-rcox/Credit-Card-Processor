<!--
SYNC IMPACT REPORT
==================
Version Change: [Initial version] → 1.0.0
Rationale: Initial constitution creation for expense reconciliation web application

Added Sections:
- Technology Stack (5 principles)
- Code Quality and Structure (3 principles)
- Version Control (1 principle)

Templates Status:
✅ plan-template.md - Reviewed, compatible with new constitution
✅ spec-template.md - Reviewed, compatible with new constitution
✅ tasks-template.md - Reviewed, compatible with new constitution

Follow-up Items:
- None - all placeholders filled
-->

# Expense Reconciliation App Constitution

## Core Principles

### I. Next.js 15 Frontend Architecture
The frontend MUST be built with Next.js 15 using the App Router, Route Handlers, and Server Actions. All UI components MUST use Shad.CN components to ensure a professional and clean design. This principle ensures modern React patterns, optimal performance through server components, and consistent UI/UX.

**Rationale**: Next.js 15 App Router provides server-side rendering, streaming, and optimal bundle splitting. Shad.CN ensures accessible, well-tested UI components with consistent design system.

### II. Python Backend for Heavy Processing
All heavy data processing tasks including PDF parsing, regex matching, and file generation (Excel/CSV) MUST be handled by a Python backend service. The Next.js application communicates with this service via API calls. Frontend MUST NOT perform compute-intensive operations.

**Rationale**: Python excels at data processing with mature libraries (PyPDF2, pandas, openpyxl). Separating concerns ensures the Next.js app remains responsive while Python handles CPU-intensive tasks efficiently.

### III. Local Storage for Session Management
Session data MUST be persisted using browser local storage. User authentication and formal database systems MUST NOT be implemented at this stage. Data persistence is limited to client-side storage only.

**Rationale**: Simplifies initial development by avoiding backend session management complexity. Allows rapid prototyping while deferring authentication and database concerns to future phases.

### IV. Python Backend Organization
All Python backend logic MUST be organized in a `/server` directory within the source folder. Python code MUST follow modular design with clear separation of concerns (parsing, processing, generation).

**Rationale**: Clear separation of frontend and backend code improves maintainability. Centralized Python services make it easier to test, deploy, and scale backend processing independently.

### V. Test-Driven Development (NON-NEGOTIABLE)
All new functionality MUST follow TDD principles. Tests MUST be created before implementation. The Red-Green-Refactor cycle is strictly enforced: write failing test → implement minimal code → pass test → refactor.

**Rationale**: TDD ensures reliability, prevents regressions, and serves as living documentation. Writing tests first forces clear requirement definition and leads to more testable, maintainable code.

## Code Quality and Structure

### VI. Next.js 15 Best Practices
Code MUST be clean, modular, and well-documented following Next.js 15 best practices:
- Use Server Components by default, Client Components only when needed
- Implement proper error boundaries and loading states
- Follow file-based routing conventions
- Optimize images with next/image
- Implement proper TypeScript types

**Rationale**: Following framework conventions ensures predictable code structure, optimal performance, and easier onboarding for new developers.

### VII. Modular Python Services
Python backend services MUST be:
- Organized by function (parsing/, processing/, generation/)
- Self-contained with clear interfaces
- Independently testable
- Well-documented with docstrings and type hints

**Rationale**: Modular design enables parallel development, easier testing, and simpler debugging. Clear interfaces prevent tight coupling between services.

### VIII. Documentation Standards
Every module MUST include:
- Purpose and responsibility description
- API contracts for public functions
- Usage examples
- Test coverage requirements

Code comments MUST explain "why" not "what". Complex algorithms MUST have detailed explanations.

**Rationale**: Documentation reduces knowledge silos, speeds up debugging, and facilitates team collaboration. Self-documenting code combined with strategic comments creates maintainable systems.

## Version Control

### IX. Git Feature Branch Workflow
Git MUST be used for version control. All new features MUST be developed on separate feature branches created by SpecKit. Direct commits to the main branch are PROHIBITED. Feature branches MUST follow naming convention: `###-feature-name`.

**Rationale**: Feature branches enable parallel development, easier code review, and safer integration. Branch isolation prevents incomplete features from affecting main codebase stability.

## Governance

This constitution supersedes all other development practices and guidelines. All pull requests and code reviews MUST verify compliance with constitutional principles before approval.

**Amendment Process**:
- Amendments require documentation of rationale and impact analysis
- Constitution version MUST be incremented following semantic versioning
- All dependent templates and documentation MUST be updated to reflect changes
- Migration plan required for breaking changes

**Compliance Review**:
- Constitution compliance checked at PR review
- Complexity deviations MUST be explicitly justified in implementation plans
- Violations require architectural review and approved exception or redesign

**Version**: 1.0.0 | **Ratified**: 2025-10-03 | **Last Amended**: 2025-10-03
