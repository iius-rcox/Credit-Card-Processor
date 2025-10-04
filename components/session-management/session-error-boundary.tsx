/**
 * SessionErrorBoundary - Specialized Error Boundary for Session Components
 *
 * Provides specialized error handling for session management components
 * with session-specific recovery options and user guidance.
 */

'use client';

import React, { Component, ReactNode } from 'react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertTriangle, RefreshCw, Home, Settings } from 'lucide-react';

interface SessionErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  resetOnPropChange?: any; // Reset error state when this prop changes
}

interface SessionErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
  errorId: string;
}

export class SessionErrorBoundary extends Component<
  SessionErrorBoundaryProps,
  SessionErrorBoundaryState
> {
  constructor(props: SessionErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: '',
    };
  }

  static getDerivedStateFromError(error: Error): Partial<SessionErrorBoundaryState> {
    // Generate unique error ID for tracking
    const errorId = `session-error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    return {
      hasError: true,
      error,
      errorId,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log error details for debugging
    console.error('SessionErrorBoundary caught an error:', {
      error,
      errorInfo,
      errorId: this.state.errorId,
      timestamp: new Date().toISOString(),
    });

    // Update state with error info
    this.setState({ errorInfo });

    // Call optional error callback
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Report to error tracking service if available
    if (typeof window !== 'undefined' && (window as any).errorTracker) {
      (window as any).errorTracker.captureException(error, {
        tags: { component: 'SessionManagement' },
        extra: { errorInfo, errorId: this.state.errorId },
      });
    }
  }

  componentDidUpdate(prevProps: SessionErrorBoundaryProps) {
    // Reset error state if resetOnPropChange changes
    if (
      this.state.hasError &&
      this.props.resetOnPropChange !== prevProps.resetOnPropChange
    ) {
      this.setState({
        hasError: false,
        error: null,
        errorInfo: null,
        errorId: '',
      });
    }
  }

  private getErrorType = (error: Error): string => {
    if (error.message.includes('localStorage')) {
      return 'storage';
    }
    if (error.message.includes('network') || error.message.includes('fetch')) {
      return 'network';
    }
    if (error.message.includes('permission') || error.message.includes('unauthorized')) {
      return 'permission';
    }
    if (error.message.includes('session')) {
      return 'session';
    }
    return 'unknown';
  };

  private getErrorMessage = (error: Error): { title: string; description: string; suggestions: string[] } => {
    const errorType = this.getErrorType(error);

    switch (errorType) {
      case 'storage':
        return {
          title: 'Storage Error',
          description: 'There was a problem accessing session data.',
          suggestions: [
            'Clear your browser storage and try again',
            'Check if your browser has sufficient storage space',
            'Disable private browsing mode if enabled',
          ],
        };

      case 'network':
        return {
          title: 'Network Error',
          description: 'Unable to connect to the session management service.',
          suggestions: [
            'Check your internet connection',
            'Try refreshing the page',
            'Contact support if the problem persists',
          ],
        };

      case 'permission':
        return {
          title: 'Permission Error',
          description: 'You may not have permission to perform this action.',
          suggestions: [
            'Try logging out and logging back in',
            'Contact your administrator for access',
            'Check if your session has expired',
          ],
        };

      case 'session':
        return {
          title: 'Session Error',
          description: 'There was a problem with session management.',
          suggestions: [
            'Try creating a new session',
            'Clear expired sessions and try again',
            'Restart the application if needed',
          ],
        };

      default:
        return {
          title: 'Unexpected Error',
          description: 'An unexpected error occurred in session management.',
          suggestions: [
            'Try refreshing the page',
            'Check the browser console for details',
            'Contact support with error ID: ' + this.state.errorId,
          ],
        };
    }
  };

  private handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: '',
    });
  };

  private handleReload = () => {
    window.location.reload();
  };

  private handleNavigateHome = () => {
    window.location.href = '/';
  };

  private handleClearStorage = () => {
    try {
      localStorage.removeItem('expense_sessions');
      this.handleRetry();
    } catch (error) {
      console.error('Failed to clear storage:', error);
      this.handleReload();
    }
  };

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const { title, description, suggestions } = this.getErrorMessage(this.state.error);
      const errorType = this.getErrorType(this.state.error);

      return (
        <div className="w-full max-w-2xl mx-auto p-4">
          <Card className="border-red-200">
            <CardHeader className="pb-4">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-6 w-6 text-red-500" />
                <div>
                  <CardTitle className="text-red-600">{title}</CardTitle>
                  <p className="text-sm text-gray-600 mt-1">
                    Session Management Component Error
                  </p>
                </div>
              </div>
            </CardHeader>

            <CardContent className="space-y-6">
              {/* Error Description */}
              <Alert variant="destructive">
                <AlertDescription>
                  {description}
                </AlertDescription>
              </Alert>

              {/* Error Details (Development Mode) */}
              {process.env.NODE_ENV === 'development' && (
                <details className="bg-gray-50 p-4 rounded-md">
                  <summary className="cursor-pointer font-medium text-sm">
                    Error Details (Development)
                  </summary>
                  <div className="mt-2 space-y-2 text-xs">
                    <div>
                      <strong>Error ID:</strong> {this.state.errorId}
                    </div>
                    <div>
                      <strong>Message:</strong> {this.state.error.message}
                    </div>
                    <div>
                      <strong>Stack:</strong>
                      <pre className="mt-1 bg-white p-2 rounded border text-xs overflow-auto">
                        {this.state.error.stack}
                      </pre>
                    </div>
                    {this.state.errorInfo && (
                      <div>
                        <strong>Component Stack:</strong>
                        <pre className="mt-1 bg-white p-2 rounded border text-xs overflow-auto">
                          {this.state.errorInfo.componentStack}
                        </pre>
                      </div>
                    )}
                  </div>
                </details>
              )}

              {/* Suggestions */}
              <div className="space-y-3">
                <h4 className="font-medium text-sm">Suggested Solutions:</h4>
                <ul className="space-y-2">
                  {suggestions.map((suggestion, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm">
                      <span className="text-blue-500 mt-0.5">•</span>
                      <span>{suggestion}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap gap-3">
                <Button
                  onClick={this.handleRetry}
                  className="flex items-center gap-2"
                >
                  <RefreshCw className="h-4 w-4" />
                  Try Again
                </Button>

                <Button
                  variant="outline"
                  onClick={this.handleReload}
                  className="flex items-center gap-2"
                >
                  <RefreshCw className="h-4 w-4" />
                  Reload Page
                </Button>

                {errorType === 'storage' && (
                  <Button
                    variant="outline"
                    onClick={this.handleClearStorage}
                    className="flex items-center gap-2"
                  >
                    <Settings className="h-4 w-4" />
                    Clear Storage
                  </Button>
                )}

                <Button
                  variant="ghost"
                  onClick={this.handleNavigateHome}
                  className="flex items-center gap-2"
                >
                  <Home className="h-4 w-4" />
                  Go Home
                </Button>
              </div>

              {/* Contact Information */}
              <div className="pt-4 border-t text-xs text-gray-500">
                <p>
                  If the problem persists, please contact support with error ID:{' '}
                  <code className="bg-gray-100 px-1 rounded">{this.state.errorId}</code>
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

export default SessionErrorBoundary;