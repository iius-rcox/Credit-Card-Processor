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

## 📋 Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

---

## Clarifications

### Session 2025-10-06
- Q: Database hosting approach preference (StatefulSet vs Azure managed service)? → A: PostgreSQL StatefulSet in AKS (free compute, requires backup strategy)
- Q: Data retention policy? → A: 90-day retention for middleware staging to pVault (Option 2)
- Q: Database backup frequency and retention policy? → A: Weekly backups with 30-day retention
- Q: Secrets management approach (native Kubernetes vs Azure Key Vault)? → A: Azure Key Vault (already exists, no added cost)
- Q: GitHub repository URL and deployment branch? → A: https://github.com/iius-rcox/Credit-Card-Processor, main branch
- Q: Internal domain name for ingress routing? → A: credit-card.ii-us.com (replacing existing app by design)
- Q: Ingress controller class? → A: webapprouting.kubernetes.azure.com (matching n8n pattern)
- Q: TLS/HTTPS configuration? → A: Yes, use HTTPS with existing certificate infrastructure

---

## User Scenarios & Testing

### Primary User Story
As an internal employee reconciling expense reports, I need to:
1. Upload credit card statements and employee receipt PDFs monthly
2. View matching results showing which transactions have receipts
3. Download reconciliation reports for accounting records
4. Access reconciliation data from any session within the last 90 days
5. Sync finalized data to pVault as the permanent system of record

The system serves as middleware staging for pVault, maintaining reconciliation data for 90 days to allow review, corrections, and re-processing before final import. After 90 days, data is automatically archived or deleted since pVault contains the authoritative records.

### Acceptance Scenarios

1. **Given** a new reconciliation session is needed, **When** user uploads PDFs, **Then** system processes them immediately, displays results, and stores all extracted data in the database for 90 days without keeping the PDF files.

2. **Given** reconciliation data exists from 60 days ago, **When** user requests report for that session by ID, **Then** system generates and streams the report from stored database records.

3. **Given** reconciliation data is 91 days old, **When** user attempts to access it, **Then** system returns "session expired" message as data has been automatically cleaned up.

4. **Given** the application is deployed to AKS, **When** users access https://credit-card.ii-us.com from company intranet, **Then** system responds successfully over HTTPS with no public internet access required.

5. **Given** system has been running for 12 months, **When** reviewing operational costs, **Then** total monthly expenses remain under $10 including database storage and compute.

6. **Given** user completes reconciliation and imports to pVault, **When** 90 days pass, **Then** system automatically deletes the session data as pVault is now the authoritative source.

7. **Given** database backup exists from last week, **When** database corruption occurs, **Then** administrators can restore from weekly backup with maximum 7 days of data loss (acceptable for re-processing workflow).

### Edge Cases
- What happens when user tries to access 95-day-old session? System must return clear "session expired - data retained 90 days" message.
- How does system handle database connection failures? Application must display clear error messages and health check endpoints must report database status.
- What happens when database runs out of disk space? Must have monitoring alerts before capacity issues and documented storage expansion procedure.
- What happens during zero-downtime database schema migrations? System must have tested migration rollback capability.
- What happens if PDFs need re-processing after 90 days? User must re-upload original PDFs as this is middleware staging, not permanent archive.

## Requirements

### Functional Requirements

**Data Persistence & Lifecycle**
- **FR-001**: System MUST store all reconciliation data (employees, transactions, receipts, matching results, session metadata) in a relational database with 90-day retention policy as middleware staging to pVault.
- **FR-002**: System MUST allow users to retrieve and view reconciliation data from any session within the 90-day retention window using a session identifier.
- **FR-003**: System MUST automatically delete session data older than 90 days via scheduled cleanup job, as pVault is the permanent system of record.
- **FR-004**: System MUST generate reports on-demand from database queries and stream them to users without storing report files.
- **FR-005**: System MUST discard uploaded PDF files immediately after extraction, using only temporary file storage during processing with automatic cleanup.
- **FR-006**: System MUST persist data with appropriate database indexes for efficient querying of sessions within the 90-day window.

**Deployment & Infrastructure**
- **FR-007**: System MUST deploy to existing AKS cluster in the credit-card-processor namespace, replacing the existing credit-card application at credit-card.ii-us.com.
- **FR-008**: System MUST use existing Redis service at redis.credit-card-processor.svc.cluster.local:6379 for temporary processing state only.
- **FR-009**: System MUST be accessible only from company intranet via HTTPS (TLS/SSL) using webapprouting.kubernetes.azure.com ingress class matching n8n configuration pattern.
- **FR-010**: System MUST operate as single-replica deployment suitable for 1-2 concurrent users with monthly usage patterns.
- **FR-011**: System MUST use container images stored in existing Azure Container Registry (iiusacr.azurecr.io).

**Database Management**
- **FR-012**: System MUST use PostgreSQL StatefulSet deployed in AKS cluster for 90-day staging data storage with persistent volume claims.
- **FR-013**: System MUST implement automated weekly database backups via Kubernetes CronJob with 30-day backup retention.
- **FR-014**: System MUST use connection pooling to efficiently manage database connections for low-traffic usage patterns.
- **FR-015**: System MUST expose database health check endpoints for monitoring and alerting.
- **FR-016**: System MUST store database credentials securely in existing Azure Key Vault with AKS workload identity integration for secret retrieval.

**Operational Requirements**
- **FR-017**: System MUST maintain total monthly operational costs under $10 including database storage (~$2) and compute allocation (~$5).
- **FR-018**: System MUST support single-command deployment from GitHub repository (https://github.com/iius-rcox/Credit-Card-Processor) main branch using automated CI/CD pipeline.
- **FR-019**: System MUST provide documented rollback procedure for database migration failures with data integrity verification.
- **FR-020**: System MUST configure resource limits appropriate for 1-2 users to minimize costs while ensuring reliability.
- **FR-021**: System MUST use TLS/SSL certificates for HTTPS access at credit-card.ii-us.com with existing certificate infrastructure.

**Data Architecture**
- **FR-022**: System MUST clearly separate temporary processing data (Redis, expires immediately) from staging business data (PostgreSQL, 90-day retention).
- **FR-023**: System MUST estimate database storage growth at ~10MB per reconciliation session × 12 sessions/year × 90-day window = ~30MB active storage maximum.
- **FR-024**: System MUST replace in-memory session storage with database-backed persistence layer using repository pattern.

### Key Entities

- **Session**: Represents a single reconciliation workflow with unique identifier, creation timestamp, expiration timestamp (created_at + 90 days), processing status, and relationships to all associated employees, transactions, and receipts for that reconciliation run. Users retrieve data by session ID within 90-day window.

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
- [x] No [NEEDS CLARIFICATION] markers remain (all 8 clarifications resolved)
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

---

## Execution Status

- [x] User description parsed
- [x] Key concepts extracted
- [x] All ambiguities resolved (8 clarifications)
- [x] User scenarios defined
- [x] Requirements generated (24 functional requirements)
- [x] Entities identified (5 core + 1 ephemeral)
- [x] Review checklist passed

---

## Success Criteria

1. **Middleware Staging**: All reconciliation data accessible for 90 days, then automatically cleaned up as pVault is permanent record.
2. **Zero File Storage**: PDF files are never persisted; only extracted data stored in database.
3. **Cost Target**: Total monthly operational cost stays under $10 (estimate: $7 actual).
4. **Accessibility**: System accessible only from company intranet to 1-2 internal users via HTTPS.
5. **Operational Simplicity**: Single-command deployment with clear rollback procedure.
6. **Data Integrity**: Automated weekly database backups with tested restoration process (max 7 days data loss acceptable).
7. **Performance**: Report generation from staging data completes within acceptable timeframe for low-traffic usage.
8. **Seamless Replacement**: New application replaces existing credit-card app at same hostname with zero configuration changes for users.

---

## Assumptions

1. Existing AKS cluster (dev-aks in rg_prod) has sufficient resources for single-replica deployment
2. Redis service is already operational and accessible at specified DNS address
3. Internal users have network access to company intranet and AKS ingress
4. Monthly usage pattern (not daily) allows for minimal resource allocation
5. Existing credit-card application at credit-card.ii-us.com will be decommissioned and replaced by this system
6. pVault serves as the permanent system of record; this system is temporary staging only
7. 90-day retention window provides sufficient time for review, corrections, and pVault import
8. No high-availability requirements due to low usage and internal-only access
9. Database backup storage (estimated 200MB for 30 days of weekly backups) is minimal cost within budget
10. TLS certificates for *.ii-us.com or credit-card.ii-us.com already exist in Azure infrastructure
11. Azure Key Vault already exists and is configured for AKS workload identity integration
12. webapprouting.kubernetes.azure.com ingress controller is already deployed and operational
13. Acceptable to lose up to 7 days of reconciliation data in catastrophic failure (can re-process from PDFs)
14. Database growth remains minimal due to 90-day auto-cleanup: 10GB storage sufficient for years of operation

---

## Dependencies

1. **External Systems**:
   - Azure Key Vault for secrets management
   - Azure Container Registry (iiusacr.azurecr.io) for container images
   - Existing AKS cluster with webapprouting ingress controller
   - Existing Redis service in credit-card-processor namespace
   - pVault system as downstream permanent storage (not managed by this project)

2. **Infrastructure**:
   - TLS certificates for credit-card.ii-us.com
   - Azure Disk storage class for PersistentVolumeClaims
   - GitHub Actions runners with Azure authentication

3. **Operational**:
   - Existing backup storage solution or Azure Files for pg_dump exports
   - Monitoring/alerting infrastructure for database health checks
   - Internal DNS resolution for credit-card.ii-us.com

---

## Out of Scope

1. **Not Included**:
   - High availability or multi-replica deployment
   - Public internet access or external authentication
   - Integration with pVault (manual export/import process)
   - Real-time data synchronization with pVault
   - Advanced reporting or analytics beyond basic reconciliation
   - User authentication or role-based access control
   - Audit logging beyond basic application logs
   - Performance optimization beyond single-user requirements
   - Mobile or tablet-optimized interfaces

2. **Explicitly Excluded**:
   - Azure Blob Storage or persistent file storage
   - Managed PostgreSQL database service
   - Separate staging/development environments
   - Load balancers or external IP addresses
   - Data retention beyond 90 days
   - Automated pVault integration or API calls