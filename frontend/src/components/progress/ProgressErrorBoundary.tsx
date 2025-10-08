/**
 * Error boundary component for progress tracking components.
 *
 * This component catches errors that occur within progress components
 * and displays a fallback UI instead of crashing the entire application.
 */

'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  resetKeys?: Array<string | number>;
  resetOnPropsChange?: boolean;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorCount: number;
  showDetails: boolean;
}

/**
 * ProgressErrorBoundary component
 *
 * Catches and handles errors in child components, providing
 * a graceful fallback UI when progress components fail.
 */
export class ProgressErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0,
      showDetails: false
    };
  }

  /**
   * Update state when an error is caught
   */
  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error
    };
  }

  /**
   * Log error details and call error handler
   */
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ProgressErrorBoundary caught an error:', error, errorInfo);

    this.setState(prevState => ({
      errorInfo,
      errorCount: prevState.errorCount + 1
    }));

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Log to error reporting service in production
    if (process.env.NODE_ENV === 'production') {
      // TODO: Send to error reporting service (e.g., Sentry)
      this.logErrorToService(error, errorInfo);
    }
  }

  /**
   * Reset error state when props change (if enabled)
   */
  componentDidUpdate(prevProps: Props) {
    const { resetKeys, resetOnPropsChange } = this.props;
    const { hasError } = this.state;

    if (hasError && prevProps.resetKeys !== resetKeys) {
      if (resetOnPropsChange) {
        this.resetErrorBoundary();
      }
    }
  }

  /**
   * Log error to external service
   */
  logErrorToService(error: Error, errorInfo: ErrorInfo) {
    // Placeholder for error reporting service integration
    const errorData = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      userAgent: navigator.userAgent
    };

    console.log('Would send to error service:', errorData);
  }

  /**
   * Reset the error boundary state
   */
  resetErrorBoundary = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      showDetails: false
    });
  };

  /**
   * Toggle error details visibility
   */
  toggleDetails = () => {
    this.setState(prevState => ({
      showDetails: !prevState.showDetails
    }));
  };

  render() {
    const { hasError, error, errorInfo, errorCount, showDetails } = this.state;
    const { children, fallback } = this.props;

    if (hasError && error) {
      // Use custom fallback if provided
      if (fallback) {
        return <>{fallback}</>;
      }

      // Default error UI
      return (
        <div className="min-h-[200px] flex items-center justify-center p-4">
          <div className="max-w-md w-full">
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
              {/* Error header */}
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-6 h-6 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-red-900 dark:text-red-100">
                    Progress Display Error
                  </h3>
                  <p className="mt-1 text-sm text-red-700 dark:text-red-300">
                    {error.message || 'An error occurred while displaying progress information'}
                  </p>

                  {/* Error count badge */}
                  {errorCount > 1 && (
                    <div className="mt-2">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 dark:bg-red-800 text-red-800 dark:text-red-200">
                        Error occurred {errorCount} times
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Action buttons */}
              <div className="mt-4 flex items-center gap-2">
                <button
                  onClick={this.resetErrorBoundary}
                  className="
                    inline-flex items-center gap-2 px-3 py-1.5
                    bg-red-600 hover:bg-red-700
                    text-white text-sm font-medium rounded-md
                    transition-colors
                  "
                >
                  <RefreshCw className="w-4 h-4" />
                  Try Again
                </button>

                <button
                  onClick={this.toggleDetails}
                  className="
                    inline-flex items-center gap-1 px-3 py-1.5
                    text-red-700 dark:text-red-300 text-sm font-medium
                    hover:bg-red-100 dark:hover:bg-red-800 rounded-md
                    transition-colors
                  "
                >
                  {showDetails ? (
                    <>
                      <ChevronUp className="w-4 h-4" />
                      Hide Details
                    </>
                  ) : (
                    <>
                      <ChevronDown className="w-4 h-4" />
                      Show Details
                    </>
                  )}
                </button>
              </div>

              {/* Error details */}
              {showDetails && errorInfo && (
                <div className="mt-4 pt-4 border-t border-red-200 dark:border-red-700">
                  <div className="space-y-3">
                    {/* Error name */}
                    <div>
                      <h4 className="text-xs font-semibold text-red-700 dark:text-red-300 uppercase tracking-wider">
                        Error Type
                      </h4>
                      <p className="mt-1 text-sm font-mono text-red-600 dark:text-red-400">
                        {error.name}
                      </p>
                    </div>

                    {/* Stack trace */}
                    {process.env.NODE_ENV === 'development' && error.stack && (
                      <div>
                        <h4 className="text-xs font-semibold text-red-700 dark:text-red-300 uppercase tracking-wider">
                          Stack Trace
                        </h4>
                        <pre className="
                          mt-1 p-2 text-xs font-mono
                          bg-red-900/10 dark:bg-red-900/20 rounded
                          text-red-800 dark:text-red-200
                          overflow-x-auto max-h-32 overflow-y-auto
                        ">
                          {error.stack}
                        </pre>
                      </div>
                    )}

                    {/* Component stack */}
                    {process.env.NODE_ENV === 'development' && errorInfo.componentStack && (
                      <div>
                        <h4 className="text-xs font-semibold text-red-700 dark:text-red-300 uppercase tracking-wider">
                          Component Stack
                        </h4>
                        <pre className="
                          mt-1 p-2 text-xs font-mono
                          bg-red-900/10 dark:bg-red-900/20 rounded
                          text-red-800 dark:text-red-200
                          overflow-x-auto max-h-32 overflow-y-auto
                        ">
                          {errorInfo.componentStack}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Help text */}
            <p className="mt-4 text-center text-xs text-gray-500 dark:text-gray-400">
              If this error persists, please refresh the page or contact support.
            </p>
          </div>
        </div>
      );
    }

    return children;
  }
}

/**
 * Higher-order component to wrap a component with error boundary
 */
export function withProgressErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<Props, 'children'>
) {
  const WrappedComponent = (props: P) => (
    <ProgressErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ProgressErrorBoundary>
  );

  WrappedComponent.displayName = `withProgressErrorBoundary(${Component.displayName || Component.name})`;

  return WrappedComponent;
}