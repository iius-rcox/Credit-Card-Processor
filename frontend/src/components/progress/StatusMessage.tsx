/**
 * StatusMessage component for displaying descriptive status text.
 *
 * This component shows human-readable status messages with appropriate
 * styling and icons based on the current state.
 */

'use client';

import React from 'react';
import { Info, CheckCircle, AlertCircle, Clock, Loader2 } from 'lucide-react';
import { ProgressState } from '@/types/progress';

export interface StatusMessageProps {
  state: ProgressState;
  className?: string;
  showIcon?: boolean;
  variant?: 'default' | 'inline' | 'banner';
}

/**
 * StatusMessage component
 *
 * @param props - Component props
 * @returns JSX element displaying status message
 */
export function StatusMessage({
  state,
  className = '',
  showIcon = true,
  variant = 'default'
}: StatusMessageProps) {
  const { statusMessage, overall, error, connectionState } = state;

  /**
   * Determine message priority and content
   */
  const getMessage = () => {
    // Error takes priority
    if (error) {
      return {
        text: error.message || 'An error occurred during processing',
        type: 'error' as const,
        icon: <AlertCircle className="w-5 h-5" />
      };
    }

    // Connection issues
    if (connectionState === 'error') {
      return {
        text: 'Connection lost. Attempting to reconnect...',
        type: 'warning' as const,
        icon: <AlertCircle className="w-5 h-5" />
      };
    }

    // Completed state
    if (overall.phase === 'completed') {
      return {
        text: 'Processing completed successfully',
        type: 'success' as const,
        icon: <CheckCircle className="w-5 h-5" />
      };
    }

    // Failed state
    if (overall.phase === 'failed') {
      return {
        text: 'Processing failed. Please check the error details.',
        type: 'error' as const,
        icon: <AlertCircle className="w-5 h-5" />
      };
    }

    // Active processing
    if (statusMessage) {
      return {
        text: statusMessage,
        type: 'info' as const,
        icon: <Loader2 className="w-5 h-5 animate-spin" />
      };
    }

    // Pending
    if (overall.phase === 'pending') {
      return {
        text: 'Waiting to start processing...',
        type: 'info' as const,
        icon: <Clock className="w-5 h-5" />
      };
    }

    // Default
    return {
      text: `Current phase: ${overall.phase}`,
      type: 'info' as const,
      icon: <Info className="w-5 h-5" />
    };
  };

  const message = getMessage();

  /**
   * Get styling based on message type and variant
   */
  const getStyles = () => {
    const baseStyles = {
      error: 'text-red-700 dark:text-red-300',
      warning: 'text-yellow-700 dark:text-yellow-300',
      success: 'text-green-700 dark:text-green-300',
      info: 'text-blue-700 dark:text-blue-300'
    };

    const variantStyles = {
      default: {
        container: 'flex items-center gap-2 p-3 rounded-lg',
        background: {
          error: 'bg-red-50 dark:bg-red-900/20',
          warning: 'bg-yellow-50 dark:bg-yellow-900/20',
          success: 'bg-green-50 dark:bg-green-900/20',
          info: 'bg-blue-50 dark:bg-blue-900/20'
        }
      },
      inline: {
        container: 'flex items-center gap-2',
        background: {}
      },
      banner: {
        container: 'flex items-center gap-3 px-4 py-3 border-l-4',
        background: {
          error: 'bg-red-50 dark:bg-red-900/10 border-red-500',
          warning: 'bg-yellow-50 dark:bg-yellow-900/10 border-yellow-500',
          success: 'bg-green-50 dark:bg-green-900/10 border-green-500',
          info: 'bg-blue-50 dark:bg-blue-900/10 border-blue-500'
        }
      }
    };

    const selectedVariant = variantStyles[variant];
    const textColor = baseStyles[message.type];
    const background = selectedVariant.background[message.type] || '';

    return `${selectedVariant.container} ${textColor} ${background}`;
  };

  // Don't render if no meaningful message
  if (!statusMessage && !error && overall.phase === 'pending' && connectionState === 'disconnected') {
    return null;
  }

  return (
    <div className={`${getStyles()} ${className}`}>
      {showIcon && (
        <div className="flex-shrink-0">
          {message.icon}
        </div>
      )}
      <div className="flex-1">
        <p className={variant === 'inline' ? 'text-sm' : 'text-sm font-medium'}>
          {message.text}
        </p>

        {/* Show additional context for errors */}
        {error && error.context && variant !== 'inline' && (
          <div className="mt-1 text-xs opacity-75">
            {error.context.file && (
              <span>File: {error.context.file}</span>
            )}
            {error.context.page && (
              <span className="ml-2">Page: {error.context.page}</span>
            )}
          </div>
        )}

        {/* Show last update time */}
        {state.lastUpdate && variant === 'banner' && (
          <div className="mt-1 text-xs opacity-60">
            Last updated: {new Date(state.lastUpdate).toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  );
}