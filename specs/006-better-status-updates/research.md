# Research: Better Status Updates

**Feature**: 006-better-status-updates
**Date**: 2025-10-08
**Research Phase**: Phase 0

## Overview
This document consolidates technical research for implementing detailed progress tracking across PDF processing phases (upload, extraction, matching).

---

## 1. Real-Time Communication Pattern

### Decision: Server-Sent Events (SSE)

**Rationale:**
- **Simplicity**: Works over standard HTTP, native browser support (EventSource API)
- **Unidirectional fit**: Progress updates are server → client only
- **Auto-reconnection**: Built-in browser reconnection handling
- **Performance**: Minimal overhead for 2-3 second intervals
- **Single-user optimization**: No complex connection management needed

**Alternatives Considered:**
- **WebSockets**: Overkill (bi-directional capability unused), more complex setup
- **HTTP Polling**: Simple but inefficient, higher server load, artificial delays

**Implementation Notes:**
- Backend: Use `sse-starlette` library with FastAPI `StreamingResponse`
- Frontend: Native `EventSource` API or `@microsoft/fetch-event-source`
- Include heartbeat to prevent connection timeouts
- Keep payloads compact (JSON, 500-1000 bytes)

---

## 2. Progress State Modeling

### Decision: Hybrid Approach - JSONB Column + Cached Aggregates

**Rationale:**
- **Single-user system**: No lock contention concerns with JSONB
- **Ephemeral data**: Progress only relevant during active processing
- **Flexible schema**: JSONB accommodates varying phase structures without migrations
- **Atomic snapshots**: Each update is complete state, no aggregation queries needed
- **Efficient reads**: Primary key lookup + JSONB extraction (~0.1ms)

**Schema:**
- Add `processing_progress` (JSONB) to existing `sessions` table
- Add `current_phase` (VARCHAR) for fast filtering
- Add `overall_percentage` (INTEGER) for cached aggregate

**JSONB Structure Example:**
```json
{
  "overall_percentage": 45,
  "current_phase": "processing",
  "phases": {
    "upload": {"status": "completed", "percentage": 100},
    "processing": {
      "status": "in_progress",
      "percentage": 35,
      "current_file": {
        "name": "statement_002.pdf",
        "current_page": 5,
        "total_pages": 12
      }
    }
  },
  "last_update": "2025-10-08T14:25:42Z"
}
```

**Alternatives Considered:**
- **Separate ProcessingProgress table**: Adds JOIN overhead, overkill for 1:1 relationship
- **Pure counter columns**: Schema explosion (15+ columns), inflexible
- **Redis/in-memory**: Not persistent across restarts (violates FR-008)

**Write Performance:**
- Single UPDATE every 2.5s: ~0.2-0.5ms with PostgreSQL MVCC
- No contention (single-user system)
- Async SQLAlchemy: Non-blocking updates

---

## 3. Frontend State Management

### Decision: useReducer + Context API + Custom SSE Hook

**Rationale:**
- **useReducer**: Handles complex, interconnected state (overall/per-file/phase)
- **Atomic updates**: Single SSE event → one action → consistent state
- **Context API**: Distributes progress to nested components without prop drilling
- **Testable**: Pure reducer functions testable independently
- **React 19 optimized**: Context re-renders optimized in React 19

**Hook Patterns:**
1. **useSSE**: Manages EventSource connection, reconnection, event parsing
2. **useProgress**: Combines useReducer + useSSE + persistence
3. **useProgressPersistence**: Handles localStorage save/load for recovery
4. **useProgressAnimations**: Smooths progress bar transitions

**State Shape:**
```typescript
{
  sessionId: string,
  overall: { percent: number, phase: string },
  files: [
    {
      id: string,
      name: string,
      percent: number,
      currentPage: number,
      totalPages: number,
      status: 'pending' | 'processing' | 'complete'
    }
  ],
  aggregate: {
    totalFiles: number,
    completedFiles: number,
    processedPages: number
  },
  connectionState: string
}
```

**Alternatives Considered:**
- **useState**: Too fragile for 6+ related state variables
- **Redux**: Overkill, significant boilerplate for single-feature state
- **Zustand**: Viable but external dependency, built-in hooks sufficient

---

## 4. PDF Progress Tracking

### Decision: pdfplumber + State-Based ProgressTracker

**Rationale:**
- **Already in stack**: pdfplumber in current requirements.txt
- **Efficient page counting**: `len(pdf.pages)` reads metadata (~1-5ms)
- **Decoupled tracking**: ProgressTracker class separates concerns
- **Time-based batching**: Updates every 2.5s, not per page
- **Non-blocking**: Async updates don't slow extraction

**Tracking Pattern:**
```python
class ProgressTracker:
    - Batches updates to 2.5-second intervals
    - Forces updates at boundaries (page 1, page N)
    - Supports multi-file aggregate calculation
    - Async callback for persistence
```

**Multi-File Progress Formula:**
```python
files_completed = current_file_index - 1
current_file_contribution = (current_page / total_pages) / total_files
aggregate_pct = ((files_completed + current_file_contribution) / total_files) * 100
```

**Batching Strategy:**
- Store pending update, check elapsed time
- Emit if: `elapsed >= 2.5s` OR `page == 1` OR `page == total_pages`
- Ensures UI sees activity even for fast processing

**Alternatives Considered:**
- **Update every page**: Overwhelms UI/DB (1000+ updates per file)
- **Update every N pages**: Fixed interval doesn't adapt to speed
- **asyncio.Queue**: Over-engineered for this use case

---

## 5. Communication Architecture

### Decision: HTTP Polling (MVP) → SSE (Enhancement)

**Phase 1 (MVP):**
- Frontend polls `GET /api/sessions/{id}/progress` every 2-3 seconds
- Matches existing REST patterns in codebase
- Simple to implement, no WebSocket infrastructure

**Phase 2 (Enhancement):**
- Implement SSE streaming endpoint
- Push updates to frontend as they occur
- Lower latency, reduced network overhead

**Endpoint Design:**
```python
@router.get("/sessions/{id}/progress")
async def get_progress(session_id: UUID) -> ProgressResponse:
    return {
        "session_id": session_id,
        "current_phase": phase,
        "aggregate_progress": percentage,
        "phase_details": details,
        "last_update": timestamp
    }
```

**Why Not WebSockets:**
- Overkill (don't need bidirectional)
- Higher complexity (connection management)
- SSE simpler for one-way updates

---

## 6. Error Handling

### Decision: Fail-Fast with Context Preservation

**Pattern:**
- Capture error with context (file, page, phase)
- Update progress to failed state
- Store error details in JSONB
- Frontend displays which phase failed (FR-015)

**Error Progress Structure:**
```json
{
  "current_phase": "failed",
  "error": {
    "type": "ExtractionError",
    "message": "Regex extraction failed",
    "context": {"file": "doc.pdf", "page": 5}
  }
}
```

**Edge Cases:**
- Empty PDF (0 pages): Skip with warning, continue batch
- Page extraction timeout: Mark page failed, continue
- Server restart: Progress shows "interrupted" status
- Large files (1000+ pages): Time-based batching handles naturally

---

## 7. Performance Characteristics

**Expected Metrics:**
- Page count retrieval: 1-5ms per file
- Progress DB write: 10-50ms (async, non-blocking)
- Update frequency: ~0.4 updates/sec per session
- Memory overhead: <1KB per session
- Processing slowdown: <1% (negligible)

**Optimization Opportunities:**
- Batch writes for multiple concurrent sessions
- Redis cache for high-frequency updates (if needed)
- Connection pooling: Configure async pool size appropriately

---

## 8. Implementation Dependencies

**Backend:**
- `sse-starlette`: FastAPI SSE support
- `pdfplumber`: Already installed, PDF page counting

**Frontend:**
- Native `EventSource` API: Built-in browser support
- Optional: `@microsoft/fetch-event-source` for advanced scenarios

**Database:**
- PostgreSQL JSONB: Already using PostgreSQL
- SQLAlchemy 2.0: Already in use

**No New Dependencies Required** - Leverages existing stack.

---

## 9. Testing Strategy

**Unit Tests:**
- Progress calculation (aggregate percentages)
- Batching behavior (time-based throttling)
- Reducer actions (state transitions)

**Integration Tests:**
- End-to-end extraction with progress tracking
- Multi-file processing scenarios
- Error handling and recovery

**Contract Tests:**
- Progress API response schema
- SSE event format validation

---

## 10. Implementation Phases

**Phase 1: Core Tracking (MVP)**
1. Add progress fields to Session model
2. Implement ProgressTracker class
3. Update ExtractionService for page-level tracking
4. Add GET /sessions/{id}/progress endpoint
5. Unit tests

**Phase 2: Frontend Integration**
1. Implement useProgress hook
2. Create progress UI components
3. Connect to polling endpoint
4. Handle state recovery on refresh

**Phase 3: Multi-File Support**
1. Extend tracker for multiple files
2. Implement aggregate calculations
3. Update UI for summary + detailed views

**Phase 4: Enhancements**
1. Implement SSE streaming
2. Add progress animations
3. Performance profiling and optimization

---

## Summary of Decisions

| Aspect | Decision | Key Benefit |
|--------|----------|-------------|
| **Communication** | SSE | Simple, auto-reconnect, efficient |
| **State Storage** | JSONB in sessions | Flexible, no joins, atomic |
| **Frontend State** | useReducer + Context | Handles complexity, testable |
| **PDF Tracking** | pdfplumber + ProgressTracker | Already in stack, decoupled |
| **Batching** | Time-based (2.5s) | Prevents UI overload |
| **MVP Approach** | HTTP Polling | Matches existing patterns |

All technical unknowns resolved. Ready for Phase 1: Design & Contracts.
