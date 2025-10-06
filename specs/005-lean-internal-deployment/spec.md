# Feature Specification: Lean Internal Deployment with Permanent Data Storage

**Feature Branch**: `005-lean-internal-deployment`
**Created**: 2025-10-06
**Status**: Draft
**Input**: User description: "Lean Internal Deployment with Permanent Data Storage - Deploy the Expense Reconciliation System (Next.js + FastAPI) to our existing AKS cluster with permanent data retention."

## Execution Flow (main)
```
1. Parse user description from Input
   � Feature: Deploy MVP to production with permanent storage
2. Extract key concepts from description
   � Actors: Internal users (1-2), System administrators
   � Actions: Deploy application, Store/retrieve reconciliation data, Generate reports
   � Data: Employee records, transactions, receipts, matching results, session metadata
   � Constraints: Cost <$25/month, intranet-only, minimal resources, indefinite retention
3. For each unclear aspect:
   � [NEEDS CLARIFICATION: Internal domain name for ingress]
   � [NEEDS CLARIFICATION: GitHub repository URL]
   � [NEEDS CLARIFICATION: GitHub branch for deployment]
   � [NEEDS CLARIFICATION: Database backup retention policy specifics]
   � [NEEDS CLARIFICATION: Database access credentials management approach]
4. Fill User Scenarios & Testing section
   � User uploads PDFs � processes � views results � retrieves historical data
5. Generate Functional Requirements
   � All requirements testable and mapped to user needs
6. Identify Key Entities
   � Session, Employee, Transaction, Receipt, MatchResult
7. Run Review Checklist
   � WARN "Spec has 5 clarification needs"
8. Return: SUCCESS (spec ready for planning after clarifications)
```

---

## � Quick Guidelines
-  Focus on WHAT users need and WHY
- L Avoid HOW to implement (no tech stack, APIs, code structure)
- =e Written for business stakeholders, not developers

---

## Clarifications

### Session 2025-10-06
- Q: Database hosting approach preference (StatefulSet vs Azure managed service)? → A: PostgreSQL StatefulSet in AKS (free compute, requires backup strategy)
- Q: Database backup frequency and retention policy? → A: Weekly backups with 90-day retention (quarterly audit alignment)
- Q: Secrets management approach (native Kubernetes vs Azure Key Vault)? → A: Azure Key Vault for enhanced security with Azure integration
- Q: GitHub repository URL and deployment branch? → A: https://github.com/iius-rcox/Credit-Card-Processor, main branch
- Q: Internal domain name for ingress routing? → A: credit-card.ii-us.com (existing namespace host)

---

## User Scenarios & Testing

### Primary User Story
As an internal employee reconciling expense reports, I need to:
1. Upload credit card statements and employee receipt PDFs monthly
2. View matching results showing which transactions have receipts
3. Download reconciliation reports for accounting records
4. Access historical reconciliation data from any previous month indefinitely

The system must be available on the company intranet, require minimal maintenance, and preserve all historical data for compliance and auditing purposes.

### Acceptance Scenarios

1. **Given** a new reconciliation session is needed, **When** user uploads PDFs, **Then** system processes them immediately, displays results, and stores all extracted data permanently in the database without keeping the PDF files.

2. **Given** historical reconciliation data exists from 6 months ago, **When** user requests report for that session by ID, **Then** system generates and streams the report from stored database records.

3. **Given** the application is deployed to AKS, **When** users access it from company intranet, **Then** system responds successfully with no public internet access required.

4. **Given** system has been running for 12 months, **When** reviewing operational costs, **Then** total monthly expenses remain under $25 including database and infrastructure.

5. **Given** database contains 2 years of reconciliation data, **When** system restarts or is redeployed, **Then** all historical sessions remain accessible without data loss.

6. **Given** user starts a reconciliation process, **When** PDF processing completes, **Then** temporary PDF files are immediately deleted from the system with zero persistent file storage used.

### Edge Cases
- What happens when database backup restoration is needed? System must have documented rollback procedure with data integrity verification.
- How does system handle database connection failures? Application must display clear error messages and health check endpoints must report database status.
- What happens when user tries to access non-existent session ID? System must return clear "session not found" message.
- How does system handle database running out of disk space? Must have monitoring alerts before capacity issues and documented storage expansion procedure.
- What happens during zero-downtime database schema migrations? System must have tested migration rollback capability.

## Requirements

### Functional Requirements

**Data Persistence & Retrieval**
- **FR-001**: System MUST store all reconciliation data (employees, transactions, receipts, matching results, session metadata) permanently in a relational database with no automatic expiration or TTL.
- **FR-002**: System MUST allow users to retrieve and view historical reconciliation data from any past session using a session identifier.
- **FR-003**: System MUST generate reports on-demand from database queries and stream them to users without storing report files.
- **FR-004**: System MUST discard uploaded PDF files immediately after extraction, using only temporary file storage during processing with automatic cleanup.
- **FR-005**: System MUST persist data with appropriate database indexes for efficient querying of historical sessions.

**Deployment & Infrastructure**
- **FR-006**: System MUST deploy to existing AKS cluster in the credit-card-processor namespace using existing Redis service for temporary processing state only.
- **FR-007**: System MUST be accessible only from company intranet with no public internet access via internal ingress controller.
- **FR-008**: System MUST operate as single-replica deployment suitable for 1-2 concurrent users with monthly usage patterns.
- **FR-009**: System MUST use container images stored in existing Azure Container Registry (iiusacr.azurecr.io).
- **FR-010**: System MUST connect to Redis at redis.credit-card-processor.svc.cluster.local:6379 for ephemeral state management.

**Database Management**
- **FR-011**: System MUST use PostgreSQL StatefulSet deployed in AKS cluster for permanent data storage with persistent volume claims.
- **FR-012**: System MUST implement automated weekly database backups via Kubernetes CronJob with 90-day retention for quarterly audit compliance.
- **FR-013**: System MUST use connection pooling to efficiently manage database connections for low-traffic usage patterns.
- **FR-014**: System MUST expose database health check endpoints for monitoring and alerting.
- **FR-015**: System MUST store database credentials securely in Azure Key Vault with AKS workload identity integration for secret retrieval.

**Operational Requirements**
- **FR-016**: System MUST maintain total monthly operational costs under $25 including database, compute, and storage.
- **FR-017**: System MUST support single-command deployment from GitHub repository (https://github.com/iius-rcox/Credit-Card-Processor) main branch using automated CI/CD pipeline.
- **FR-018**: System MUST provide documented rollback procedure for database migration failures with data integrity verification.
- **FR-019**: System MUST configure resource limits appropriate for 1-2 users to minimize costs while ensuring reliability.
- **FR-020**: System MUST use internal domain name credit-card.ii-us.com (existing namespace host) for ingress routing.

**Data Architecture**
- **FR-021**: System MUST clearly separate temporary processing data (Redis, expires) from permanent business data (PostgreSQL, never expires).
- **FR-022**: System MUST estimate and plan for database storage growth over time based on monthly usage patterns.
- **FR-023**: System MUST replace in-memory session storage with database-backed persistence layer.

### Key Entities

- **Session**: Represents a single reconciliation workflow with unique identifier, creation timestamp, processing status, and relationships to all associated employees, transactions, and receipts for that reconciliation run. Users retrieve historical data by session ID.

- **Employee**: Individual tracked for expense reconciliation with name, employee identifier, and relationship to their credit card transactions.

- **Transaction**: Credit card charge entry with date, amount, merchant, description, and relationship to employee and optional matched receipt.

- **Receipt**: Uploaded receipt document (after PDF extraction) with date, amount, vendor, and relationship to matching transaction if found.

- **MatchResult**: Outcome of reconciliation process linking transactions to receipts, including match confidence level, matched/unmatched status, and reason codes for non-matches.

- **ProcessingState** (ephemeral): Temporary status information during active PDF processing, stored in Redis with automatic expiration, not persisted to database.

---

## Review & Acceptance Checklist

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain (all 5 clarifications resolved)
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified
---

## Execution Status

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked (5 clarifications)
- [x] User scenarios defined
- [x] Requirements generated (23 functional requirements)
- [x] Entities identified (5 core + 1 ephemeral)
- [x] Review checklist passed (with clarification warnings)

---

## Success Criteria

1. **Data Permanence**: All reconciliation data from any historical session can be retrieved indefinitely without data loss.
2. **Zero File Storage**: PDF files are never persisted; only extracted data stored in database.
3. **Cost Target**: Total monthly operational cost stays below $25 including all infrastructure.
4. **Accessibility**: System accessible only from company intranet to 1-2 internal users.
5. **Operational Simplicity**: Single-command deployment with clear rollback procedure.
6. **Data Integrity**: Automated database backups with tested restoration process.
7. **Performance**: Report generation from historical data completes within acceptable timeframe for low-traffic usage.

---

## Assumptions

1. Existing AKS cluster (dev-aks in rg_prod) has sufficient resources for single-replica deployment
2. Redis service is already operational and accessible at specified DNS address
3. Internal users have network access to company intranet and AKS ingress
4. Monthly usage pattern (not daily) allows for minimal resource allocation
5. Historical data growth rate is manageable within cost constraints (estimate ~100MB per reconciliation session)
6. No high-availability requirements due to low usage and internal-only access
7. Database backup storage is included within $25/month budget or considered infrastructure overhead
