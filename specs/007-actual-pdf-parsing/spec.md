# Feature Specification: Actual PDF Parsing

**Feature Branch**: `007-actual-pdf-parsing`
**Created**: 2025-10-10
**Status**: Draft
**Input**: User description: "Actual PDF Parsing - implement actual PDF parsing with regex patterns that extract: Employee names, Expense types (Fuel, Meals, General Expense, etc.), Dates (MM/DD/YYYY format), Amounts (with decimals), Merchant names and addresses"

## Execution Flow (main)
```
1. Parse user description from Input
   → Identified: Need to extract structured transaction data from PDF files
2. Extract key concepts from description
   → Actors: Users uploading credit card statements and bank statements
   → Actions: Extract transaction details from PDF text
   → Data: Employee names, expense types, dates, amounts, merchant info
   → Constraints: Must parse real PDF content, not return placeholder data
3. For each unclear aspect:
   → [NEEDS CLARIFICATION: What PDF formats/layouts are supported?]
   → [NEEDS CLARIFICATION: How should extraction handle OCR errors or malformed data?]
   → [NEEDS CLARIFICATION: Should extraction validate extracted dates/amounts?]
   → [NEEDS CLARIFICATION: What happens if employee name is not found in database?]
   → [NEEDS CLARIFICATION: Are there different regex patterns for different banks/card issuers?]
4. Fill User Scenarios & Testing section
   → Primary scenario: User uploads PDF and system extracts all transactions
5. Generate Functional Requirements
   → Each requirement is testable
6. Identify Key Entities
   → Extracted transactions, OCR results, validation errors
7. Run Review Checklist
   → No implementation details included
   → Ambiguities marked for clarification
8. Return: NEEDS_CLARIFICATION (awaiting answers to marked items)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

### Section Requirements
- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation
When creating this spec from a user prompt:
1. **Mark all ambiguities**: Use [NEEDS CLARIFICATION: specific question] for any assumption you'd need to make
2. **Don't guess**: If the prompt doesn't specify something (e.g., "login system" without auth method), mark it
3. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist item
4. **Common underspecified areas**:
   - User types and permissions
   - Data retention/deletion policies
   - Performance targets and scale
   - Error handling behaviors
   - Integration requirements
   - Security/compliance needs

---

## Clarifications

### Session 2025-10-10
- Q: When extraction encounters a transaction with missing required fields (e.g., no date or amount), what should happen? → A: Extract partial data with null/empty values for missing fields and flag as incomplete
- Q: Should the system support text-based PDFs only, or both text-based AND scanned image PDFs (requiring OCR)? → A: Text-based PDFs only (no OCR support)
- Q: If an employee name extracted from the PDF doesn't match any existing employee record in the database, what should happen? → A: Allow the user to provide an alias of a matching employee
- Q: How should the system handle transactions with negative amounts (refunds/credits)? → A: Store negative amounts as-is and flag them as credits/refunds
- Q: What is the expected maximum number of transactions per PDF? → A: 10000

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
As a user uploading credit card statements and bank statements for reconciliation, I want the system to accurately extract all transaction details (employee names, dates, amounts, merchant information, expense types) from my PDFs so that I can reconcile expenses against receipts without manual data entry.

### Acceptance Scenarios
1. **Given** a user uploads a credit card statement PDF, **When** extraction completes, **Then** the system displays all transactions with employee name, date, amount, merchant name, merchant address, and expense type extracted from the PDF
2. **Given** a PDF contains 50 transactions, **When** extraction runs, **Then** all 50 transactions are extracted and stored individually with their complete details
10. **Given** a PDF contains up to 10,000 transactions, **When** extraction runs, **Then** the system successfully processes all transactions without performance degradation
3. **Given** a transaction has a date in MM/DD/YYYY format, **When** extracted, **Then** the system correctly parses and stores the transaction date
4. **Given** a transaction has an amount with commas and decimal (e.g., "1,234.56"), **When** extracted, **Then** the system correctly parses the numeric value
5. **Given** a merchant name spans multiple lines in the PDF, **When** extracted, **Then** the system captures the complete merchant name without truncation
6. **Given** a PDF contains transactions for multiple employees, **When** extracted, **Then** each transaction is associated with the correct employee name
7. **Given** the system extracts expense type (Fuel, Meals, General Expense, etc.), **When** categorizing transactions, **Then** the expense type is stored and available for filtering/reporting
8. **Given** an extracted employee name doesn't match any existing employee record, **When** the user maps it as an alias to an existing employee, **Then** all transactions with that extracted name are associated with the selected employee and future PDFs automatically use this alias mapping
9. **Given** a transaction has a negative amount in the PDF, **When** extracted, **Then** the system stores the negative value and flags the transaction as a credit/refund

### Edge Cases
- What happens if a required field (date, amount) cannot be extracted from the PDF? (Transaction is still saved with null/empty value for missing field and flagged as incomplete)
- How should the system handle transactions with negative amounts (refunds/credits)? (Store the negative amount as-is and flag the transaction as a credit/refund)
- What if an employee name in the PDF doesn't match any existing employee record? (System allows user to map the extracted name as an alias to an existing employee record)
- What happens if a scanned image PDF is uploaded? (System rejects the file, only text-based PDFs are supported)
- [NEEDS CLARIFICATION: What if the PDF format differs from the expected layout (different bank/card issuer)?]
- What happens if some transactions succeed and others fail during extraction? (All extracted transactions are saved, including incomplete ones flagged with missing fields)
- [NEEDS CLARIFICATION: How are multi-page transactions or page breaks within transaction tables handled?]

## Requirements *(mandatory)*

### Functional Requirements

**Transaction Data Extraction**
- **FR-001**: System MUST extract employee name from each transaction in the PDF
- **FR-002**: System MUST extract transaction date in MM/DD/YYYY format from each transaction
- **FR-003**: System MUST extract transaction amount (including decimals) from each transaction, preserving negative values for credits/refunds
- **FR-004**: System MUST extract merchant name from each transaction
- **FR-005**: System MUST extract merchant address from each transaction
- **FR-006**: System MUST extract expense type (e.g., Fuel, Meals, General Expense, Hotel, Legal, Maintenance) from each transaction
- **FR-007**: System MUST handle amounts with comma separators (e.g., "1,234.56") and extract the numeric value correctly
- **FR-008**: System MUST extract all transactions present in a PDF, not just the first one
- **FR-019**: System MUST flag transactions with negative amounts as credits/refunds
- [NEEDS CLARIFICATION: Should the system extract card last four digits if present?]
- [NEEDS CLARIFICATION: Should the system extract posting date separately from transaction date?]

**Data Quality & Validation**
- **FR-009**: System MUST preserve the original raw text from the PDF for each extracted transaction
- **FR-010**: System MUST flag incomplete transactions where required fields (date, amount, employee name, merchant name) could not be extracted
- **FR-017**: System MUST allow users to create employee name aliases that map extracted names from PDFs to existing employee records
- **FR-018**: System MUST automatically use saved aliases when the same employee name appears in future PDFs
- [NEEDS CLARIFICATION: Should the system validate that extracted dates are in a reasonable range (not future dates, not too old)?]

**Extraction Coverage**
- **FR-011**: System MUST process all pages of a multi-page PDF to extract all transactions
- **FR-020**: System MUST support PDFs containing up to 10,000 transactions
- [NEEDS CLARIFICATION: What is the maximum expected PDF file size to support?]

**Error Handling**
- **FR-012**: System MUST continue extraction when a transaction has missing fields, saving partial data with null/empty values
- **FR-013**: System MUST flag transactions as incomplete when required fields (date, amount, employee name, merchant name) are missing or malformed
- **FR-014**: System MUST save all extracted transactions including incomplete ones, rather than failing the entire PDF extraction
- [NEEDS CLARIFICATION: Should extraction errors be logged for review, or silently skipped?]
- [NEEDS CLARIFICATION: Should users receive feedback about extraction quality (e.g., "45 of 50 transactions extracted, 5 incomplete")?]

**Data Format Support**
- **FR-015**: System MUST support text-based PDFs where text can be extracted programmatically
- **FR-016**: System MUST reject scanned image PDFs that require OCR with a clear error message
- [NEEDS CLARIFICATION: Should the system support different PDF layouts from different banks/card issuers?]
- [NEEDS CLARIFICATION: Are there specific bank statement formats that must be supported (e.g., Chase, Bank of America)?]
- [NEEDS CLARIFICATION: Should receipt images use different extraction logic than credit card statements?]

**Out of Scope**
- Manual correction/editing of extracted data (not included in this feature)
- Machine learning-based extraction (pattern matching only in this feature)
- Automatic bank/issuer detection (manual classification in this feature)
- OCR support for scanned image PDFs (text-based PDFs only in this feature)

### Key Entities *(include if feature involves data)*
- **Extracted Transaction**: Structured data extracted from PDF containing employee name, transaction date, amount (may be negative for credits/refunds), merchant name, merchant address, expense type, original raw text, incomplete flag (true when required fields are missing), and credit/refund flag (true when amount is negative)
- **Extraction Pattern**: Text pattern used to identify and extract transaction fields from PDF text
- **Extraction Result**: Container for all transactions extracted from a single PDF, including success/failure status and any error messages
- **Employee**: Person associated with transaction (referenced by name in PDF)
- **Employee Alias**: Mapping between an extracted name from PDFs and an existing employee record, allowing automatic resolution of name variations
- **Merchant**: Business where transaction occurred, with name and address components
- **Expense Category**: Classification of transaction type (Fuel, Meals, General Expense, Hotel, Legal, Maintenance, etc.)
- [NEEDS CLARIFICATION: Should there be a validation/confidence score for each extraction?]

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain *(Multiple clarifications needed)*
- [ ] Requirements are testable and unambiguous *(Pending clarifications)*
- [ ] Success criteria are measurable *(Pending clarifications on error handling)*
- [x] Scope is clearly bounded
- [ ] Dependencies and assumptions identified *(Need to clarify PDF format dependencies)*

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked (awaiting clarification)
- [x] User scenarios defined
- [x] Requirements generated (with clarification markers)
- [x] Entities identified
- [ ] Review checklist passed (blocked on clarifications)

---

## Clarifications Needed

Before proceeding to planning phase, the following questions must be answered:

1. **PDF Format Support**: What specific PDF layouts/formats need to be supported? Are there example PDFs from target banks/card issuers?
2. **Error Handling Strategy**: Should extraction fail completely if any transaction fails, or continue with partial results?
3. **Data Validation**: Should extracted dates and amounts be validated for reasonableness?
4. **Employee Matching**: How should mismatches between PDF employee names and database records be handled?
5. **OCR vs Text PDFs**: Should both scanned images (OCR) and text-based PDFs be supported?
6. **Extraction Confidence**: Should the system track confidence scores or quality metrics for extractions?
7. **Negative Amounts**: How should credits, refunds, or negative amounts be handled?
8. **Field Requirements**: Which fields are mandatory vs optional for a valid transaction?
9. **Scale Requirements**: What are the maximum expected transactions per PDF and maximum PDF file size?
10. **Multi-Issuer Support**: Should different regex patterns be maintained for different banks/issuers?

---
