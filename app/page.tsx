/**
 * Main page for Expense Reconciliation System.
 *
 * Orchestrates the multi-step workflow:
 * 1. Upload PDFs
 * 2. Process with progress display
 * 3. Show results
 */

"use client";

import { useState, useEffect } from "react";
import { UploadForm } from "@/components/upload-form";
import { ProgressDisplay } from "@/components/progress-display";
import { ResultsPanel } from "@/components/results-panel";
import { ErrorBoundary } from "@/components/error-boundary";
import { getSession as getSessionFromStorage, clearSession } from "@/lib/session-storage";
import { getSessionDetail, downloadReport } from "@/lib/api-client";
import type { SessionDetail } from "@/lib/api-client";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

type AppStep = "upload" | "processing" | "results";

export default function Home() {
  const [currentStep, setCurrentStep] = useState<AppStep>("upload");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionData, setSessionData] = useState<SessionDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRestoring, setIsRestoring] = useState(true);

  // On mount, check for existing session in localStorage
  useEffect(() => {
    const existingSessionId = getSessionFromStorage();

    if (existingSessionId) {
      // Try to restore session
      restoreSession(existingSessionId);
    } else {
      setIsRestoring(false);
    }
  }, []);

  const restoreSession = async (sessionId: string) => {
    try {
      // Fetch session data
      const session = await getSessionDetail(sessionId);

      setSessionId(sessionId);
      setSessionData(session);

      // Check if processing is complete
      if (session.status === "completed") {
        setCurrentStep("results");
      } else if (session.status === "processing") {
        // Resume processing
        setCurrentStep("processing");
      } else if (session.status === "failed") {
        setError("Session processing failed");
        setCurrentStep("upload");
      }
    } catch (err) {
      // Session not found or error - clear and start fresh
      clearSession();
    } finally {
      setIsRestoring(false);
    }
  };

  const handleUploadComplete = (newSessionId: string) => {
    setSessionId(newSessionId);
    setCurrentStep("processing");
  };

  const handleProcessingComplete = async () => {
    if (!sessionId) return;

    try {
      // Fetch session data
      const session = await getSessionDetail(sessionId);
      setSessionData(session);
      setCurrentStep("results");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load results");
    }
  };

  const handleProcessingError = (errorMsg: string) => {
    setError(errorMsg);
    // Still try to show partial results
    if (sessionId) {
      getSessionDetail(sessionId)
        .then((session) => {
          setSessionData(session);
          // Partial results might be available
        })
        .catch(() => {
          // Ignore
        });
    }
  };

  const handleDownloadExcel = async () => {
    if (!sessionId) return;
    try {
      const blob = await downloadReport(sessionId, 'xlsx');
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `reconciliation_${sessionId}.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to download Excel report");
    }
  };

  const handleDownloadCSV = async () => {
    if (!sessionId) return;
    try {
      const blob = await downloadReport(sessionId, 'csv');
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `reconciliation_${sessionId}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to download CSV report");
    }
  };

  const handleUploadNewReceipts = () => {
    if (sessionId) {
      // Navigate to receipt update page
      window.location.href = `/sessions/${sessionId}/update`;
    }
  };

  const handleStartNew = () => {
    clearSession();
    setSessionId(null);
    setSessionData(null);
    setError(null);
    setCurrentStep("upload");
  };

  if (isRestoring) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto mb-4"></div>
          <div>Restoring session...</div>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <div className="min-h-screen">
        {/* Navigation Header */}
        <div className="bg-white border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center">
                <h1 className="text-xl font-semibold text-gray-900">
                  Expense Reconciliation System
                </h1>
              </div>
              <nav className="flex items-center space-x-4">
                <a
                  href="/"
                  className="bg-blue-100 text-blue-700 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Process Expenses
                </a>
                <a
                  href="/sessions"
                  className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Session Management
                </a>
              </nav>
            </div>
          </div>
        </div>

        <div className="p-8 pb-20 gap-16 sm:p-20">
          <header className="mb-8 text-center">
            <h1 className="text-4xl font-bold mb-2">Expense Reconciliation System</h1>
            <p className="text-muted-foreground">
              Upload credit card statements and expense reports for automated matching
            </p>
          </header>

        <main>
          {/* Global Error Display */}
          {error && (
            <Alert variant="destructive" className="mb-6 max-w-2xl mx-auto">
              <AlertDescription>
                {error}
              </AlertDescription>
            </Alert>
          )}

          {/* Step 1: Upload */}
          {currentStep === "upload" && <UploadForm onUploadComplete={handleUploadComplete} />}

          {/* Step 2: Processing */}
          {currentStep === "processing" && sessionId && (
            <ProgressDisplay
              sessionId={sessionId}
              onComplete={handleProcessingComplete}
              onError={handleProcessingError}
            />
          )}

          {/* Step 3: Results */}
          {currentStep === "results" && sessionData && (
            <ResultsPanel
              sessionData={sessionData}
              onDownloadExcel={handleDownloadExcel}
              onDownloadCSV={handleDownloadCSV}
              onUploadNewReceipts={handleUploadNewReceipts}
            />
          )}

          {/* Start New Session Button (always visible in results view) */}
          {currentStep === "results" && (
            <div className="mt-8 text-center">
              <Button onClick={handleStartNew} variant="outline">
                Start New Session
              </Button>
            </div>
          )}
        </main>
        </div>
      </div>
    </ErrorBoundary>
  );
}
