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
import { getSession, getReports } from "@/lib/api-client";
import type { SessionResponse, ReportsResponse } from "@/lib/types";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

type AppStep = "upload" | "processing" | "results";

export default function Home() {
  const [currentStep, setCurrentStep] = useState<AppStep>("upload");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionData, setSessionData] = useState<SessionResponse | null>(null);
  const [reportsData, setReportsData] = useState<ReportsResponse | null>(null);
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
      const session = await getSession(sessionId);

      setSessionId(sessionId);
      setSessionData(session);

      // Check if processing is complete
      if (session.processing_status === "complete") {
        // Fetch reports
        const reports = await getReports(sessionId);
        setReportsData(reports);
        setCurrentStep("results");
      } else if (session.processing_status === "processing") {
        // Resume processing
        setCurrentStep("processing");
      } else if (session.processing_status === "pending") {
        // Ready to process
        setCurrentStep("processing");
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
      // Fetch session and reports data
      const session = await getSession(sessionId);
      const reports = await getReports(sessionId);

      setSessionData(session);
      setReportsData(reports);
      setCurrentStep("results");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load results");
    }
  };

  const handleProcessingError = (errorMsg: string) => {
    setError(errorMsg);
    // Still try to show partial results
    if (sessionId) {
      getSession(sessionId)
        .then((session) => {
          setSessionData(session);
          // Partial results might be available
        })
        .catch(() => {
          // Ignore
        });
    }
  };

  const handleDownloadExcel = () => {
    if (reportsData?.excel_report) {
      window.open(reportsData.excel_report.url, "_blank");
    }
  };

  const handleDownloadCSV = () => {
    if (reportsData?.csv_export) {
      window.open(reportsData.csv_export.url, "_blank");
    }
  };

  const handleUploadNewReceipts = () => {
    // TODO: Implement update workflow
    alert("Update workflow not yet implemented");
  };

  const handleStartNew = () => {
    clearSession();
    setSessionId(null);
    setSessionData(null);
    setReportsData(null);
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
      <div className="min-h-screen p-8 pb-20 gap-16 sm:p-20">
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
                {sessionData && sessionData.error_message && (
                  <div className="mt-2 text-sm">Details: {sessionData.error_message}</div>
                )}
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
          {currentStep === "results" && sessionData && reportsData && (
            <ResultsPanel
              sessionData={sessionData}
              reportsData={reportsData}
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
    </ErrorBoundary>
  );
}
