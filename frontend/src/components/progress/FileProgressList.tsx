/**
 * FileProgressList component for displaying per-file progress details.
 *
 * This component shows a list of files being processed with individual
 * progress bars and page counts.
 */

'use client';

import React from 'react';
import { FileText, Check, AlertCircle } from 'lucide-react';
import { ProgressState, FileProgress } from '@/types/progress';

export interface FileProgressListProps {
  state: ProgressState;
  className?: string;
  showDetails?: boolean;
  compact?: boolean;
}

/**
 * FileProgressList component
 *
 * @param props - Component props
 * @returns JSX element displaying file-level progress
 */
export function FileProgressList({
  state,
  className = '',
  showDetails = true,
  compact = false
}: FileProgressListProps) {
  // Extract file progress from processing phase
  const processingPhase = state.phases.processing;
  const currentFile = processingPhase?.currentFile;
  const totalFiles = processingPhase?.totalFiles || 0;
  const currentFileIndex = processingPhase?.currentFileIndex || 0;

  // If no file data, show empty state
  if (!processingPhase || totalFiles === 0) {
    return (
      <div className={`${className} text-center py-8 text-gray-500 dark:text-gray-400`}>
        <FileText className="w-12 h-12 mx-auto mb-2 opacity-50" />
        <p className="text-sm">No files being processed</p>
      </div>
    );
  }

  /**
   * Render a single file progress item
   */
  const renderFileItem = (
    file: FileProgress | null,
    index: number,
    isCurrent: boolean
  ) => {
    const isCompleted = index < currentFileIndex;
    const isPending = index > currentFileIndex;

    // Calculate percentage
    const percentage = file?.percentage ||
      (isCompleted ? 100 : isPending ? 0 :
        (file ? Math.round((file.currentPage / file.totalPages) * 100) : 0));

    return (
      <div
        key={index}
        className={`
          ${compact ? 'py-2' : 'py-3'}
          border-b last:border-b-0 border-gray-200 dark:border-gray-700
          ${isCurrent ? 'bg-blue-50 dark:bg-blue-900/20 -mx-4 px-4' : ''}
        `}
      >
        <div className="flex items-start gap-3">
          {/* File icon with status */}
          <div className="flex-shrink-0 mt-0.5">
            {isCompleted ? (
              <div className="relative">
                <FileText className="w-5 h-5 text-green-500" />
                <Check className="w-3 h-3 text-green-500 absolute -bottom-1 -right-1" />
              </div>
            ) : isCurrent ? (
              <FileText className="w-5 h-5 text-blue-500 animate-pulse" />
            ) : (
              <FileText className="w-5 h-5 text-gray-400" />
            )}
          </div>

          {/* File details */}
          <div className="flex-1 min-w-0">
            {/* File name and status */}
            <div className="flex items-center justify-between mb-1">
              <span
                className={`
                  ${compact ? 'text-xs' : 'text-sm'}
                  font-medium truncate
                  ${isCompleted ? 'text-gray-600 dark:text-gray-400' : ''}
                  ${isCurrent ? 'text-blue-600 dark:text-blue-400' : ''}
                  ${isPending ? 'text-gray-400 dark:text-gray-600' : ''}
                `}
              >
                {file?.name || `File ${index + 1}`}
              </span>
              <span
                className={`
                  ${compact ? 'text-xs' : 'text-sm'}
                  font-semibold ml-2 flex-shrink-0
                  ${isCompleted ? 'text-green-600' : ''}
                  ${isCurrent ? 'text-blue-600' : ''}
                  ${isPending ? 'text-gray-400' : ''}
                `}
              >
                {percentage}%
              </span>
            </div>

            {/* Progress bar */}
            <div className={`bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden ${compact ? 'h-1.5' : 'h-2'}`}>
              <div
                className={`
                  h-full transition-all duration-300
                  ${isCompleted ? 'bg-green-500' : ''}
                  ${isCurrent ? 'bg-blue-500' : ''}
                  ${isPending ? 'bg-gray-300' : ''}
                `}
                style={{ width: `${percentage}%` }}
              />
            </div>

            {/* Additional details */}
            {showDetails && file && isCurrent && (
              <div className="mt-1 flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
                <span>
                  Page {file.currentPage} of {file.totalPages}
                </span>
                {file.regexMatchesFound > 0 && (
                  <span>
                    {file.regexMatchesFound} matches found
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  /**
   * Generate file list
   */
  const renderFileList = () => {
    const files: JSX.Element[] = [];

    for (let i = 0; i < totalFiles; i++) {
      const isCurrent = i === currentFileIndex - 1;
      const file = isCurrent ? currentFile : null;

      files.push(renderFileItem(file, i, isCurrent));
    }

    return files;
  };

  return (
    <div className={className}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className={`font-semibold text-gray-900 dark:text-gray-100 ${compact ? 'text-sm' : 'text-base'}`}>
          File Progress
        </h3>
        <span className={`text-gray-500 dark:text-gray-400 ${compact ? 'text-xs' : 'text-sm'}`}>
          {currentFileIndex} of {totalFiles} files
        </span>
      </div>

      {/* File list */}
      <div className="space-y-0">
        {renderFileList()}
      </div>

      {/* Summary stats */}
      {showDetails && !compact && (
        <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <span className="text-gray-500 dark:text-gray-400">Completed:</span>
              <span className="ml-2 font-semibold text-gray-900 dark:text-gray-100">
                {Math.max(0, currentFileIndex - 1)} files
              </span>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">Remaining:</span>
              <span className="ml-2 font-semibold text-gray-900 dark:text-gray-100">
                {totalFiles - currentFileIndex} files
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}