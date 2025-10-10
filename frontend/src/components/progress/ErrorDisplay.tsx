/**
 * ErrorDisplay component for showing error details with context.
 *
 * This component displays error information when processing fails,
 * including error type, message, and contextual details.
 */

'use client';

import React, { useState } from 'react';
import { AlertTriangle, ChevronDown, ChevronUp, XCircle, Copy, CheckCircle } from 'lucide-react';
import { ErrorContext } from '@/types/progress';

export interface ErrorDisplayProps {
  error: ErrorContext | null;
  className?: string;
  variant?: 'compact' | 'detailed' | 'inline';
  showTraceback?: boolean;
  onDismiss?: () => void;
}

/**
 * ErrorDisplay component
 *
 * @param props - Component props
 * @returns JSX element displaying error information
 */
export function ErrorDisplay({
  error,
  className = '',
  variant = 'detailed',
  showTraceback = false,
  onDismiss
}: ErrorDisplayProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  if (!error) {
    return null;
  }

  /**
   * Copy error details to clipboard
   */
  const copyErrorDetails = () => {
    const details = `
Error Type: ${error.type}
Message: ${error.message}
Time: ${error.timestamp}
Context: ${JSON.stringify(error.context, null, 2)}
${error.traceback ? `\nTraceback:\n${error.traceback}` : ''}
`.trim();

    navigator.clipboard.writeText(details);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  /**
   * Format timestamp
   */
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  /**
   * Render inline variant
   */
  if (variant === 'inline') {
    return (
      <div className={`flex items-center gap-2 text-sm text-red-600 dark:text-red-400 ${className}`}>
        <AlertTriangle className="w-4 h-4 flex-shrink-0" />
        <span>{error.message}</span>
      </div>
    );
  }

  /**
   * Render compact variant
   */
  if (variant === 'compact') {
    return (
      <div
        className={`
          flex items-start gap-3 p-3 rounded-lg
          bg-red-50 dark:bg-red-900/20
          border border-red-200 dark:border-red-800
          ${className}
        `}
      >
        <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <p className="text-sm font-medium text-red-800 dark:text-red-200">
            {error.message}
          </p>
          {error.context.file && (
            <p className="text-xs text-red-600 dark:text-red-400 mt-1">
              File: {error.context.file}
              {error.context.page && ` (Page ${error.context.page})`}
            </p>
          )}
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-red-500 hover:text-red-700 dark:hover:text-red-300"
            aria-label="Dismiss error"
          >
            <XCircle className="w-4 h-4" />
          </button>
        )}
      </div>
    );
  }

  /**
   * Render detailed variant
   */
  return (
    <div
      className={`
        border border-red-200 dark:border-red-800
        bg-red-50 dark:bg-red-900/10
        rounded-lg overflow-hidden
        ${className}
      `}
    >
      {/* Header */}
      <div className="px-4 py-3 bg-red-100 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5" />
            <div>
              <h3 className="font-semibold text-red-900 dark:text-red-100">
                Processing Error
              </h3>
              <p className="text-sm text-red-700 dark:text-red-300 mt-0.5">
                {error.type}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={copyErrorDetails}
              className="
                p-1.5 rounded hover:bg-red-200 dark:hover:bg-red-800
                text-red-600 dark:text-red-400
                transition-colors
              "
              aria-label="Copy error details"
            >
              {copied ? (
                <CheckCircle className="w-4 h-4" />
              ) : (
                <Copy className="w-4 h-4" />
              )}
            </button>
            {onDismiss && (
              <button
                onClick={onDismiss}
                className="
                  p-1.5 rounded hover:bg-red-200 dark:hover:bg-red-800
                  text-red-600 dark:text-red-400
                  transition-colors
                "
                aria-label="Dismiss error"
              >
                <XCircle className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="p-4 space-y-3">
        {/* Error message */}
        <div>
          <h4 className="text-xs font-semibold text-red-700 dark:text-red-300 uppercase tracking-wider mb-1">
            Message
          </h4>
          <p className="text-sm text-red-800 dark:text-red-200">
            {error.message}
          </p>
        </div>

        {/* Context */}
        {Object.keys(error.context).length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-red-700 dark:text-red-300 uppercase tracking-wider mb-1">
              Context
            </h4>
            <div className="text-sm text-red-700 dark:text-red-300 space-y-1">
              {error.context.phase && (
                <div>Phase: <span className="font-mono">{error.context.phase}</span></div>
              )}
              {error.context.file && (
                <div>File: <span className="font-mono">{error.context.file}</span></div>
              )}
              {error.context.page && (
                <div>Page: <span className="font-mono">{error.context.page}</span></div>
              )}
              {error.context.sessionId && (
                <div>Session: <span className="font-mono text-xs">{error.context.sessionId}</span></div>
              )}
            </div>
          </div>
        )}

        {/* Timestamp */}
        <div>
          <h4 className="text-xs font-semibold text-red-700 dark:text-red-300 uppercase tracking-wider mb-1">
            Occurred At
          </h4>
          <p className="text-sm text-red-700 dark:text-red-300">
            {formatTime(error.timestamp)}
          </p>
        </div>

        {/* Traceback (expandable) */}
        {showTraceback && error.traceback && (
          <div>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="
                flex items-center gap-2
                text-xs font-semibold text-red-700 dark:text-red-300
                uppercase tracking-wider
                hover:text-red-800 dark:hover:text-red-200
              "
            >
              <span>Technical Details</span>
              {isExpanded ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </button>
            {isExpanded && (
              <pre className="
                mt-2 p-2 rounded
                bg-red-900/10 dark:bg-red-900/20
                text-xs text-red-800 dark:text-red-200
                font-mono overflow-x-auto
              ">
                {error.traceback}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
}