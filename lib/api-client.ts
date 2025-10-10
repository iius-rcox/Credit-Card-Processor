/**
 * API client utilities for communication with Python backend.
 *
 * Provides type-safe wrappers around fetch calls to backend endpoints.
 * Updated for feature 005-lean-internal-deployment with new API structure.
 */

import type {
  UploadResponse,
  ProcessProgressEvent,
  SessionResponse,
  ReportsResponse,
  UpdateResponse,
} from "./types";

// In production on credit-card.ii-us.com, use same origin (ingress routes /api to backend)
// Otherwise use NEXT_PUBLIC_API_URL or empty string for relative paths
const API_BASE_URL = typeof window !== 'undefined' && window.location.hostname === 'credit-card.ii-us.com'
  ? `${window.location.protocol}//${window.location.host}`
  : (process.env.NEXT_PUBLIC_API_URL || "");

/**
 * Generic API request helper with error handling
 */
async function apiRequest<T>(
  url: string,
  options?: RequestInit
): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${url}`, options);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || error.message || `HTTP ${response.status}`);
    }

    return response.json();
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error('Unknown error occurred');
  }
}

// New API Types for feature 005
export interface Session {
  id: string;
  created_at: string;
  expires_at: string;
  status: 'processing' | 'completed' | 'failed' | 'expired';
  upload_count: number;
  total_transactions: number;
  total_receipts: number;
  matched_count: number;
}

export interface Employee {
  id: string;
  session_id: string;
  employee_number: string;
  name: string;
  department?: string;
  cost_center?: string;
}

export interface Transaction {
  id: string;
  session_id: string;
  employee_id: string;
  transaction_date: string;
  amount: number;
  merchant_name: string;
  description?: string;
}

export interface Receipt {
  id: string;
  session_id: string;
  receipt_date: string;
  amount: number;
  vendor_name: string;
  file_name: string;
}

export interface MatchResult {
  id: string;
  transaction_id: string;
  receipt_id?: string;
  confidence_score: number;
  match_status: 'matched' | 'unmatched' | 'manual_review';
}

export interface SessionDetail extends Session {
  employees: Employee[];
  transactions: Transaction[];
  receipts: Receipt[];
  match_results: MatchResult[];
}

export interface PaginatedSessions {
  items: Session[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

/**
 * Upload multiple PDF files to create a new session (Feature 005 API)
 */
export async function uploadFiles(files: File[]): Promise<Session> {
  const formData = new FormData();
  files.forEach(file => {
    formData.append('files', file);
  });

  return apiRequest<Session>('/api/upload', {
    method: 'POST',
    body: formData,
  });
}

/**
 * List all sessions with pagination
 */
export async function listSessions(page: number = 1, pageSize: number = 50): Promise<PaginatedSessions> {
  return apiRequest<PaginatedSessions>(
    `/api/sessions?page=${page}&page_size=${pageSize}`
  );
}

/**
 * Get session details with all related data
 */
export async function getSessionDetail(sessionId: string): Promise<SessionDetail> {
  return apiRequest<SessionDetail>(`/api/sessions/${sessionId}`);
}

/**
 * Download report in specified format
 */
export async function downloadReport(sessionId: string, format: 'xlsx' | 'csv' = 'xlsx'): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/report?format=${format}`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Failed to download report`);
  }

  return response.blob();
}

/**
 * Delete a session and all related data
 */
export async function deleteSession(sessionId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || error.message || `Failed to delete session: HTTP ${response.status}`);
  }
}

/**
 * Upload two PDF files to create a new session.
 *
 * @param creditCardStatement - Credit card statement PDF file
 * @param expenseReport - Expense report PDF file
 * @returns UploadResponse with session_id
 */
export async function uploadPDFs(
  creditCardStatement: File,
  expenseReport: File
): Promise<UploadResponse> {
  const formData = new FormData();
  // Backend expects 'files' field name (List[UploadFile])
  formData.append("files", creditCardStatement);
  formData.append("files", expenseReport);

  const response = await fetch(`${API_BASE_URL}/api/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Upload failed" }));
    const errorMessage = error.detail || error.error || error.message || JSON.stringify(error);
    throw new Error(errorMessage);
  }

  return response.json();
}

/**
 * Process uploaded PDFs with Server-Sent Events progress streaming.
 *
 * @param sessionId - Session UUID
 * @param onProgress - Callback for each progress event
 * @returns Promise that resolves when processing complete
 */
export async function processSession(
  sessionId: string,
  onProgress: (event: ProcessProgressEvent) => void
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/process`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({ session_id: sessionId }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || error.detail || "Processing failed");
  }

  // Parse SSE stream
  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  if (!reader) {
    throw new Error("No response body");
  }

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      // Decode chunk
      const chunk = decoder.decode(value);

      // Parse SSE events
      const lines = chunk.split("\n");

      for (const line of lines) {
        if (line.startsWith("data:")) {
          const jsonStr = line.substring(5).trim();

          if (jsonStr) {
            try {
              const event: ProcessProgressEvent = JSON.parse(jsonStr);
              onProgress(event);

              // Stop if complete or error
              if (event.status === "complete" || event.status === "error") {
                return;
              }
            } catch (e) {
              console.error("Failed to parse SSE event:", e);
            }
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

/**
 * Get session data including employees and matching results.
 *
 * @param sessionId - Session UUID
 * @returns SessionResponse with complete session data
 */
export async function getSession(sessionId: string): Promise<SessionResponse> {
  const response = await fetch(`${API_BASE_URL}/api/session/${sessionId}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || error.detail || "Failed to get session");
  }

  return response.json();
}

/**
 * Get generated reports (Excel and CSV) with summary statistics.
 *
 * @param sessionId - Session UUID
 * @returns ReportsResponse with report URLs and summary
 */
export async function getReports(sessionId: string): Promise<ReportsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/reports/${sessionId}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || error.detail || "Failed to get reports");
  }

  return response.json();
}

/**
 * Upload new expense report to existing session and re-analyze.
 *
 * @param sessionId - Session UUID
 * @param expenseReport - New expense report PDF file
 * @returns UpdateResponse with summary_changes
 */
export async function updateReceipts(sessionId: string, expenseReport: File): Promise<UpdateResponse> {
  const formData = new FormData();
  formData.append("expenseReport", expenseReport);

  const response = await fetch(`${API_BASE_URL}/api/session/${sessionId}/update`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || error.detail || "Update failed");
  }

  return response.json();
}
