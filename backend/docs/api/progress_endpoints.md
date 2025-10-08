# Progress API Documentation

## Overview

The Progress API provides real-time status updates for PDF processing operations. It tracks progress across multiple phases (upload, processing, matching, report generation) with page-level granularity for PDF files.

## Endpoints

### GET /api/sessions/{session_id}/progress

Retrieve the current progress for a processing session.

#### Parameters
- `session_id` (UUID, path parameter): The unique identifier of the session

#### Response
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "overall_percentage": 45,
  "current_phase": "processing",
  "phases": {
    "upload": {
      "status": "completed",
      "percentage": 100,
      "completed_at": "2025-10-08T14:23:15Z"
    },
    "processing": {
      "status": "in_progress",
      "percentage": 35,
      "total_files": 3,
      "current_file_index": 2,
      "current_file": {
        "name": "statement_002.pdf",
        "total_pages": 12,
        "current_page": 5,
        "regex_matches_found": 23
      }
    },
    "matching": {
      "status": "pending",
      "percentage": 0
    },
    "report_generation": {
      "status": "pending",
      "percentage": 0
    }
  },
  "status_message": "Processing File 2 of 3: Page 5/12",
  "last_update": "2025-10-08T14:25:42Z",
  "error": null
}
```

#### Status Codes
- **200 OK**: Progress data retrieved successfully
- **404 Not Found**: Session not found or expired

### GET /api/sessions/{session_id}/progress/stream

Stream real-time progress updates using Server-Sent Events (SSE).

#### Parameters
- `session_id` (UUID, path parameter): The unique identifier of the session
- `heartbeat` (integer, query parameter, optional): Heartbeat interval in seconds (default: 30)

#### Response
Server-Sent Events stream with the following event types:

##### Event: `progress`
```
event: progress
data: {
  "overall_percentage": 45,
  "current_phase": "processing",
  "status_message": "Processing File 2 of 3: Page 5/12",
  "phases": { ... }
}
```

##### Event: `heartbeat`
```
event: heartbeat
data: {"timestamp": "2025-10-08T14:25:42Z"}
```

##### Event: `complete`
```
event: complete
data: {"message": "Processing completed successfully"}
```

##### Event: `error`
```
event: error
data: {
  "error": "Processing failed: Invalid PDF format",
  "context": {
    "file": "document.pdf",
    "page": 5
  }
}
```

#### Status Codes
- **200 OK**: SSE stream established
- **404 Not Found**: Session not found

#### Usage Example (JavaScript)
```javascript
const eventSource = new EventSource(`/api/sessions/${sessionId}/progress/stream`);

eventSource.addEventListener('progress', (event) => {
  const data = JSON.parse(event.data);
  console.log(`Progress: ${data.overall_percentage}%`);
});

eventSource.addEventListener('complete', (event) => {
  console.log('Processing complete!');
  eventSource.close();
});

eventSource.addEventListener('error', (event) => {
  const data = JSON.parse(event.data);
  console.error('Error:', data.error);
  eventSource.close();
});
```

### POST /api/sessions/{session_id}/progress/test (Development Only)

Test endpoint for manually updating progress. **This endpoint should be disabled in production.**

#### Parameters
- `session_id` (UUID, path parameter): The unique identifier of the session
- `phase` (string, query parameter): Phase name to set (default: "processing")
- `percentage` (integer, query parameter): Overall percentage to set (default: 50)

#### Response
```json
{
  "message": "Progress updated successfully"
}
```

## Data Models

### ProcessingProgress
The main progress state object stored as JSONB in the database.

```typescript
interface ProcessingProgress {
  overall_percentage: number;        // 0-100
  current_phase: string;             // Current phase name
  phases: Record<string, PhaseProgress>;
  last_update: string;               // ISO 8601 timestamp
  status_message: string;            // Human-readable status
  error?: ErrorContext;              // Error details if failed
}
```

### PhaseProgress
Progress details for a single processing phase.

```typescript
interface PhaseProgress {
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  percentage: number;                // 0-100
  started_at?: string;               // ISO 8601 timestamp
  completed_at?: string;             // ISO 8601 timestamp

  // Phase-specific fields
  files_uploaded?: number;           // Upload phase
  bytes_uploaded?: number;           // Upload phase
  total_files?: number;              // Processing phase
  current_file_index?: number;       // Processing phase
  current_file?: FileProgress;       // Processing phase
  matches_found?: number;            // Matching phase
  unmatched_count?: number;          // Matching phase
  report_type?: string;              // Report generation phase
  records_written?: number;          // Report generation phase
}
```

### FileProgress
Tracks progress for a single PDF file during processing.

```typescript
interface FileProgress {
  name: string;                      // Filename
  file_id?: string;                  // UUID reference
  total_pages: number;               // Total page count
  current_page: number;              // Currently processing page (1-indexed)
  regex_matches_found: number;       // Matches extracted so far
  started_at: string;                // ISO 8601 timestamp
  completed_at?: string;             // ISO 8601 timestamp
  percentage?: number;               // Calculated: (current_page / total_pages) * 100
}
```

### ErrorContext
Captures error details when processing fails.

```typescript
interface ErrorContext {
  type: string;                      // Error class name
  message: string;                   // Human-readable error message
  context: {
    phase?: string;                  // Which phase failed
    file?: string;                   // Filename where error occurred
    page?: number;                   // Page number where error occurred
    sessionId?: string;              // Session ID
  };
  timestamp: string;                 // ISO 8601 timestamp
  traceback?: string;                // Stack trace (debug mode only)
}
```

## Progress Calculation

### Overall Progress Weights
The overall progress is calculated as a weighted sum of phase progress:

- **Upload**: 10% of overall progress
- **Processing**: 60% of overall progress
- **Matching**: 20% of overall progress
- **Report Generation**: 10% of overall progress

Formula: `overall = Σ(phase_weight × phase_percentage)`

### Multi-File Progress
For multiple files in the processing phase:

```
files_completed = current_file_index - 1
current_file_contribution = (current_page / total_pages) / total_files
aggregate_percentage = ((files_completed + current_file_contribution) / total_files) × 100
```

## Update Frequency

- **Backend Updates**: Progress is batched and written to database every 2.5 seconds
- **Forced Updates**: First page, last page, and phase boundaries force immediate updates
- **Frontend Polling**: Recommended interval is 2-3 seconds
- **SSE Stream**: Real-time updates as they occur
- **Heartbeat**: SSE sends heartbeat every 30 seconds (configurable)

## Error Handling

### Middleware
The `ProgressErrorMiddleware` catches and formats all errors from progress endpoints:

- Database errors → 503 Service Unavailable
- Integrity errors → 400 Bad Request
- Validation errors → 422 Unprocessable Entity
- Unexpected errors → 500 Internal Server Error

### Error Response Format
```json
{
  "error": {
    "type": "ValidationError",
    "message": "Invalid session ID format",
    "context": {
      "endpoint": "/api/sessions/invalid-id/progress",
      "method": "GET"
    },
    "timestamp": "2025-10-08T14:25:42Z"
  }
}
```

## Performance Characteristics

- **Progress Update Latency**: < 50ms (p95)
- **Calculation Time**: < 1ms for single file, < 10ms for 1000 files
- **Memory Overhead**: ~1KB per session (JSONB storage)
- **Database Write Frequency**: Max 0.4 writes/second per session (batched)

## Storage

Progress data is stored in the `sessions` table:

- `processing_progress` (JSONB): Complete progress state snapshot
- `current_phase` (VARCHAR(50)): Cached for efficient filtering
- `overall_percentage` (DECIMAL(5,2)): Cached aggregate (0.00-100.00)

Progress data is automatically cleared when a session completes to save storage space.

## Best Practices

1. **Use SSE for real-time updates** when the user is actively watching progress
2. **Use polling for background monitoring** when updates aren't critical
3. **Handle connection errors gracefully** - SSE connections may drop
4. **Respect rate limits** - Don't poll more frequently than every 2 seconds
5. **Clean up connections** - Close SSE streams when leaving the page
6. **Cache progress locally** - Use localStorage to recover from page refresh

## Example Integration

### React Hook Usage
```javascript
import { useProgress } from '@/hooks/useProgress';

function SessionProgress({ sessionId }) {
  const { state, connect, disconnect } = useProgress({
    sessionId,
    enableSSE: true,
    enablePersistence: true,
    onComplete: () => {
      console.log('Processing complete!');
    }
  });

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [sessionId]);

  return (
    <div>
      <p>Progress: {state.overall.percentage}%</p>
      <p>Phase: {state.overall.phase}</p>
      <p>Status: {state.statusMessage}</p>
    </div>
  );
}
```