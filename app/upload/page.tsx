/**
 * Upload Page for Feature 005
 *
 * Allows users to upload multiple PDF files (credit card statements + receipts)
 * and tracks processing progress with results display.
 */

"use client";

import { useState, useEffect } from "react";
import { UploadForm } from "@/components/upload-form-005";
import { ProgressDisplay } from "@/components/progress-display-005";
import { ResultsPanel } from "@/components/results-panel-005";
import { getSessionDetail } from "@/lib/api-client";
import type { Session, SessionDetail } from "@/lib/api-client";

export default function UploadPage() {
  const [session, setSession] = useState<Session | null>(null);
  const [sessionDetail, setSessionDetail] = useState<SessionDetail | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  // Poll for session status updates
  useEffect(() => {
    if (!session || !isPolling) return;

    const pollInterval = setInterval(async () => {
      try {
        const detail = await getSessionDetail(session.id);

        setSessionDetail(detail);

        // Stop polling when processing is complete
        if (detail.status === "completed" || detail.status === "failed") {
          setIsPolling(false);
        }
      } catch (error) {
        console.error("Error polling session status:", error);
        setIsPolling(false);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(pollInterval);
  }, [session, isPolling]);

  const handleUploadComplete = (newSession: Session) => {
    setSession(newSession);
    setSessionDetail(null);
    setIsPolling(true);
  };

  const handleReset = () => {
    setSession(null);
    setSessionDetail(null);
    setIsPolling(false);
  };

  return (
    <div className="container mx-auto py-8 space-y-8">
      {/* Page Header */}
      <div className="text-center space-y-2">
        <h1 className="text-4xl font-bold">Credit Card Reconciliation</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Upload your credit card statements and receipts for automatic matching
        </p>
      </div>

      {/* Upload Form (shown when no active session) */}
      {!session && <UploadForm onUploadComplete={handleUploadComplete} />}

      {/* Progress Display (shown during processing) */}
      {session && isPolling && (
        <ProgressDisplay session={session} sessionDetail={sessionDetail} />
      )}

      {/* Results Panel (shown when processing complete) */}
      {sessionDetail && (sessionDetail.status === "completed" || sessionDetail.status === "failed") && (
        <div className="space-y-4">
          <ResultsPanel sessionDetail={sessionDetail} />

          {/* Reset Button */}
          <div className="text-center">
            <button
              onClick={handleReset}
              className="px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
            >
              Upload More Files
            </button>
          </div>
        </div>
      )}

      {/* Instructions */}
      {!session && (
        <div className="max-w-3xl mx-auto mt-12 p-6 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">How It Works</h2>
          <ol className="space-y-3 list-decimal list-inside">
            <li>
              <strong>Upload PDF Files:</strong> Select your credit card statements and expense receipts
              (up to 100 files, 10MB each)
            </li>
            <li>
              <strong>Automatic Processing:</strong> Our system extracts employee data, transactions, and
              receipt information from your PDFs
            </li>
            <li>
              <strong>Smart Matching:</strong> Transactions are automatically matched to receipts using
              fuzzy matching algorithms
            </li>
            <li>
              <strong>Download Report:</strong> Get a comprehensive Excel or CSV report with all matches
              and unmatched items
            </li>
            <li>
              <strong>90-Day Storage:</strong> Your data is stored for 90 days, then automatically deleted
              for security
            </li>
          </ol>
        </div>
      )}
    </div>
  );
}
