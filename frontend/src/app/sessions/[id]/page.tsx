/**
 * SessionDetail page showing progress tracking for a processing session.
 *
 * This page demonstrates the integration of all progress components
 * to provide a comprehensive view of the processing status.
 */

'use client';

import React, { useEffect } from 'react';
import { useParams } from 'next/navigation';
import { ArrowLeft, RefreshCw, Download, Pause, Play } from 'lucide-react';
import Link from 'next/link';

// Progress components
import { ProgressOverview } from '@/components/progress/ProgressOverview';
import { PhaseIndicator } from '@/components/progress/PhaseIndicator';
import { FileProgressList } from '@/components/progress/FileProgressList';
import { StatusMessage } from '@/components/progress/StatusMessage';
import { ErrorDisplay } from '@/components/progress/ErrorDisplay';

// Progress hooks
import { useProgress } from '@/hooks/useProgress';

export default function SessionDetailPage() {
  const params = useParams();
  const sessionId = params?.id as string;

  // Initialize progress tracking
  const {
    state,
    connect,
    disconnect,
    refresh,
    clearError,
    reset
  } = useProgress({
    sessionId,
    enableSSE: true,
    enablePolling: false,
    enablePersistence: true,
    onComplete: () => {
      console.log('Processing completed!');
    },
    onError: (error) => {
      console.error('Processing error:', error);
    }
  });

  // Connect to SSE on mount
  useEffect(() => {
    if (sessionId) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [sessionId, connect, disconnect]);

  const isProcessing = state.overall.phase !== 'completed' &&
                      state.overall.phase !== 'failed' &&
                      state.overall.phase !== 'pending';

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Back button */}
            <Link
              href="/sessions"
              className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Sessions</span>
            </Link>

            {/* Session ID */}
            <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Session: <span className="font-mono text-sm">{sessionId}</span>
            </h1>

            {/* Actions */}
            <div className="flex items-center gap-2">
              {/* Refresh button */}
              <button
                onClick={refresh}
                disabled={state.isLoading}
                className="
                  p-2 rounded-lg
                  text-gray-600 dark:text-gray-400
                  hover:bg-gray-100 dark:hover:bg-gray-700
                  disabled:opacity-50 disabled:cursor-not-allowed
                  transition-colors
                "
                aria-label="Refresh progress"
              >
                <RefreshCw className={`w-4 h-4 ${state.isLoading ? 'animate-spin' : ''}`} />
              </button>

              {/* Pause/Resume (for demo) */}
              {isProcessing && (
                <button
                  onClick={() => state.connectionState === 'connected' ? disconnect() : connect()}
                  className="
                    p-2 rounded-lg
                    text-gray-600 dark:text-gray-400
                    hover:bg-gray-100 dark:hover:bg-gray-700
                    transition-colors
                  "
                  aria-label={state.connectionState === 'connected' ? 'Pause updates' : 'Resume updates'}
                >
                  {state.connectionState === 'connected' ? (
                    <Pause className="w-4 h-4" />
                  ) : (
                    <Play className="w-4 h-4" />
                  )}
                </button>
              )}

              {/* Download report (when complete) */}
              {state.overall.phase === 'completed' && (
                <button
                  className="
                    flex items-center gap-2 px-4 py-2 rounded-lg
                    bg-green-600 text-white
                    hover:bg-green-700
                    transition-colors
                  "
                >
                  <Download className="w-4 h-4" />
                  <span>Download Report</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Status message banner */}
        <div className="mb-6">
          <StatusMessage state={state} variant="banner" />
        </div>

        {/* Error display */}
        {state.error && (
          <div className="mb-6">
            <ErrorDisplay
              error={state.error}
              onDismiss={clearError}
              variant="detailed"
            />
          </div>
        )}

        {/* Progress overview */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Overall Progress
          </h2>
          <ProgressOverview state={state} animated />
        </div>

        {/* Phase indicator */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Processing Phases
          </h2>
          <PhaseIndicator state={state} orientation="horizontal" />
        </div>

        {/* Two column layout for file progress and details */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* File progress */}
          {state.phases.processing && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
              <FileProgressList state={state} showDetails />
            </div>
          )}

          {/* Session details */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Session Details
            </h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Status
                </dt>
                <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100 capitalize">
                  {state.overall.phase}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Progress
                </dt>
                <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                  {state.overall.percentage}%
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Last Update
                </dt>
                <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                  {state.lastUpdate
                    ? new Date(state.lastUpdate).toLocaleString()
                    : 'No updates yet'}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Connection
                </dt>
                <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100 capitalize">
                  {state.connectionState}
                </dd>
              </div>
            </dl>
          </div>
        </div>

        {/* Debug panel (development only) */}
        {process.env.NODE_ENV === 'development' && (
          <details className="mt-8 bg-gray-100 dark:bg-gray-800 rounded-lg p-4">
            <summary className="cursor-pointer text-sm font-medium text-gray-700 dark:text-gray-300">
              Debug Information
            </summary>
            <pre className="mt-4 text-xs text-gray-600 dark:text-gray-400 overflow-auto">
              {JSON.stringify(state, null, 2)}
            </pre>
            <div className="mt-4 flex gap-2">
              <button
                onClick={() => reset()}
                className="px-3 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700"
              >
                Reset State
              </button>
            </div>
          </details>
        )}
      </main>
    </div>
  );
}