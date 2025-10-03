/**
 * API client utilities for communication with Python backend.
 *
 * Provides type-safe wrappers around fetch calls to backend endpoints.
 */

import type {
  UploadResponse,
  ProcessProgressEvent,
  SessionResponse,
  ReportsResponse,
  UpdateResponse,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
  formData.append("creditCardStatement", creditCardStatement);
  formData.append("expenseReport", expenseReport);

  const response = await fetch(`${API_BASE_URL}/api/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || error.detail || "Upload failed");
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
