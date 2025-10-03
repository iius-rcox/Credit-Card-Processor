# Research Document: Expense Reconciliation System

**Feature**: Expense Reconciliation System
**Date**: 2025-10-03
**Status**: Complete

## Research Areas

### 1. Python PDF Parsing Libraries

**Decision**: **pdfplumber**

**Rationale**:
- pdfplumber provides superior table extraction capabilities compared to PyPDF2
- Better handling of multi-page tables that span boundaries
- Built-in text positioning and bounding box detection for structured data
- More robust regex pattern matching on extracted text
- Active maintenance and community support

**Alternatives Considered**:
- **PyPDF2**: Good for simple text extraction but struggles with complex table layouts
- **PyMuPDF (fitz)**: Fast but overkill for text-only extraction, larger dependency
- **tabula-py**: Excellent for tables but requires Java runtime (deployment complexity)

**Implementation Approach**:
```python
import pdfplumber

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        tables = page.extract_tables()  # For structured data
```

---

### 2. Excel Generation in Python

**Decision**: **openpyxl**

**Rationale**:
- Native support for .xlsx format (modern Excel standard)
- Excellent cell styling capabilities for Status column differentiation
- Can set column widths, add filters, freeze panes for better UX
- Pure Python (no external dependencies)
- Well-documented and widely used

**Alternatives Considered**:
- **xlsxwriter**: Fast but read-only after creation (can't modify existing files)
- **pandas.to_excel()**: Convenient but less control over formatting
- **pyexcel**: Simpler API but limited formatting options

**Implementation Approach**:
```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

wb = Workbook()
ws = wb.active
ws.append(["Employee ID", "Name", "Amount", "Status"])

# Style Status column based on value
for row in ws.iter_rows(min_row=2):
    status_cell = row[3]
    if status_cell.value == "Missing Both":
        status_cell.fill = PatternFill(start_color="FFC7CE", fill_type="solid")  # Red
    elif status_cell.value == "Missing Receipt":
        status_cell.fill = PatternFill(start_color="FFEB9C", fill_type="solid")  # Yellow
```

---

### 3. CSV Generation Best Practices

**Decision**: **Python csv module with strict quoting**

**Rationale**:
- pvault format requires precise column ordering and no extra formatting
- csv module provides fine-grained control over delimiters, quoting, encoding
- Lighter weight than pandas for simple write-once CSV generation
- Explicit UTF-8 encoding ensures compatibility
- QUOTE_MINIMAL strategy avoids unnecessary quotes while protecting special chars

**Alternatives Considered**:
- **pandas.to_csv()**: More overhead, potential for unwanted index column
- **Custom string concatenation**: Error-prone, doesn't handle escaping properly

**Implementation Approach**:
```python
import csv

headers = [
    "Transaction ID", "Transaction Date", "Transaction Amount",
    "Transaction Name", "Vendor Invoice #", "Invoice Date",
    "Header Description", "Job", "Phase", "Cost Type",
    "GL Account", "Item Description", "UM", "Tax",
    "Pay Type", "Card Holder", "Credit Card Number", "Credit Card Vendor"
]

with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=headers, quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()
    writer.writerows(complete_transactions)
```

---

### 4. Next.js 15 File Upload Patterns

**Decision**: **Server Actions for file upload**

**Rationale**:
- Server Actions provide built-in progressive enhancement
- Cleaner API compared to Route Handlers for form submissions
- Automatic revalidation and cache management
- Better TypeScript inference for form data
- Simplified error handling with useFormState hook

**Alternatives Considered**:
- **Route Handlers**: More verbose, requires manual fetch calls
- **Client-side fetch**: Loses progressive enhancement benefits

**Implementation Approach**:
```typescript
// app/actions/upload.ts
'use server'

export async function uploadPDFs(formData: FormData) {
  const creditCardPDF = formData.get('creditCard') as File
  const expenseReportPDF = formData.get('expenseReport') as File

  // Forward to Python backend
  const response = await fetch('http://localhost:8000/api/upload', {
    method: 'POST',
    body: formData
  })

  return await response.json()
}

// app/components/upload-form.tsx
'use client'

import { uploadPDFs } from '@/actions/upload'

export function UploadForm() {
  return (
    <form action={uploadPDFs}>
      <input type="file" name="creditCard" accept=".pdf" required />
      <input type="file" name="expenseReport" accept=".pdf" required />
      <button type="submit">Upload</button>
    </form>
  )
}
```

---

### 5. Python FastAPI + Next.js Integration

**Decision**: **Next.js proxy Route Handlers + CORS on FastAPI**

**Rationale**:
- Next.js Route Handlers proxy to Python backend (same-origin for frontend)
- FastAPI CORS middleware allows Next.js dev server origins
- Clean separation: Python handles processing, Next.js handles UI/routing
- Server-side API calls avoid CORS issues in production
- Progress streaming via Server-Sent Events (SSE) for real-time updates

**Alternatives Considered**:
- **Direct frontend→Python calls**: CORS complexity, exposes backend URL
- **WebSockets**: Overkill for one-way progress updates
- **Polling**: Less efficient than SSE, delays in updates

**Implementation Approach**:
```python
# server/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/process")
async def process_pdfs(session_id: str):
    async def generate_progress():
        yield f"data: {json.dumps({'progress': 10, 'step': 'Parsing PDFs...'})}\n\n"
        # ... processing steps
        yield f"data: {json.dumps({'progress': 100, 'step': 'Complete'})}\n\n"

    return StreamingResponse(generate_progress(), media_type="text/event-stream")
```

```typescript
// app/api/proxy/process/route.ts
export async function POST(request: Request) {
  const { sessionId } = await request.json()

  const response = await fetch('http://localhost:8000/api/process', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId })
  })

  return new Response(response.body, {
    headers: { 'Content-Type': 'text/event-stream' }
  })
}
```

---

### 6. Regex Pattern Implementation

**Decision**: **Named capture groups with verbose patterns**

**Rationale**:
- Named groups improve code readability and maintainability
- re.VERBOSE flag allows comments in regex for documentation
- Pattern compilation once at module load improves performance
- Case-insensitive matching handles formatting variations

**Implementation Approach**:
```python
import re

# Employee Header Pattern
EMPLOYEE_HEADER_PATTERN = re.compile(
    r"""
    (?P<employee_id>\w{4,6})      # 4-6 alphanumeric chars
    \s+                            # Whitespace
    (?P<name>[A-Z][a-z]+\s+[A-Z][a-z]+)  # First Last name
    \s+                            # Whitespace
    (?P<card_number>
        \d{16}                     # 16 digits, OR
        |\d{4}-\d{4}-\d{4}-\d{4}   # 4-4-4-4 format, OR
        |\*{12}\d{4}               # Masked format
    )
    """,
    re.VERBOSE | re.IGNORECASE
)

# Totals Marker Pattern
TOTALS_MARKER_PATTERN = re.compile(
    r"Totals\s+For(?:\s+Card\s+Nbr)?:",
    re.IGNORECASE
)

# Transaction Totals Pattern
TRANSACTION_TOTALS_PATTERN = re.compile(
    r"\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"
)

# Employee ID Validation
EMPLOYEE_ID_VALIDATION = re.compile(
    r"^[A-Z0-9_-]+$",
    re.IGNORECASE
)

# UUID Validation
UUID_VALIDATION = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE
)
```

---

### 7. Browser Local Storage Best Practices

**Decision**: **Structured session storage with TTL and compression**

**Rationale**:
- Local storage limit ~5-10MB (sufficient for session metadata)
- Store session ID + timestamp, fetch full data from backend on demand
- Use LZ-string library for compression if storing parsed data
- Implement TTL (24 hours) to auto-expire stale sessions
- Validate stored data on retrieval to handle schema changes

**Alternatives Considered**:
- **IndexedDB**: Overkill for simple session metadata
- **SessionStorage**: Cleared on tab close (not suitable for "return later" requirement)
- **Cookies**: Size limits too restrictive

**Implementation Approach**:
```typescript
// app/lib/session-storage.ts

interface SessionData {
  sessionId: string
  createdAt: number
  expiresAt: number
}

const SESSION_TTL = 24 * 60 * 60 * 1000 // 24 hours

export function saveSession(sessionId: string): void {
  const session: SessionData = {
    sessionId,
    createdAt: Date.now(),
    expiresAt: Date.now() + SESSION_TTL
  }
  localStorage.setItem('expense_session', JSON.stringify(session))
}

export function getSession(): string | null {
  const stored = localStorage.getItem('expense_session')
  if (!stored) return null

  const session: SessionData = JSON.parse(stored)

  // Check expiration
  if (Date.now() > session.expiresAt) {
    localStorage.removeItem('expense_session')
    return null
  }

  return session.sessionId
}

export function clearSession(): void {
  localStorage.removeItem('expense_session')
}
```

---

## Summary of Decisions

| Area | Technology | Key Benefit |
|------|-----------|-------------|
| PDF Parsing | pdfplumber | Superior table extraction, multi-page handling |
| Excel Generation | openpyxl | Rich formatting for Status column |
| CSV Generation | Python csv module | Precise control, UTF-8 compliance |
| File Upload | Next.js Server Actions | Progressive enhancement, cleaner API |
| API Integration | Route Handler proxy + SSE | Same-origin security, real-time progress |
| Regex Patterns | Named groups + VERBOSE | Maintainable, documented patterns |
| Session Storage | LocalStorage + TTL | Simple, persistent, auto-expiring |

---

## Next Steps

Proceed to Phase 1: Design & Contracts
- Create data-model.md using entity definitions
- Generate OpenAPI contracts for 5 endpoints
- Write quickstart.md test scenarios
- Update .cursorrules agent context

---

*Research complete: 2025-10-03*
