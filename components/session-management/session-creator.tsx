'use client';

/**
 * SessionCreator - New Session Creation Component
 *
 * Provides form interface for creating new sessions with validation
 * according to specs/003-add-ui-components/data-model.md
 */

import React, { useState, useCallback } from 'react';
import { useSession } from './session-provider';
import { validateSessionName, isSessionNameUnique, generateSessionId } from '@/lib/session-utils';
import { SESSION_CONSTRAINTS } from '@/lib/session-types';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';

import {
  Plus,
  X,
  AlertTriangle,
  Loader,
  CheckCircle,
} from 'lucide-react';

interface SessionCreatorProps {
  onSessionCreated?: (sessionId: string) => void;
  onCancel?: () => void;
  isOpen?: boolean;
  trigger?: React.ReactNode;
}

export function SessionCreator({
  onSessionCreated,
  onCancel,
  isOpen = false,
  trigger,
}: SessionCreatorProps) {
  const { storage, createSession, isLoading, error } = useSession();

  // Component state
  const [isFormOpen, setIsFormOpen] = useState(isOpen);
  const [sessionName, setSessionName] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  // Check if approaching session limit
  const sessionCount = Object.keys(storage.sessions).length;
  const isApproachingLimit = sessionCount >= SESSION_CONSTRAINTS.MAX_SESSIONS - 2;
  const isAtLimit = sessionCount >= SESSION_CONSTRAINTS.MAX_SESSIONS;

  // Handle form open/close
  const handleOpen = () => {
    if (isAtLimit) {
      setValidationError('Maximum number of sessions (24) reached. Please delete old sessions first.');
      return;
    }
    setIsFormOpen(true);
    setSessionName('');
    setValidationError(null);
  };

  const handleClose = () => {
    setIsFormOpen(false);
    setSessionName('');
    setValidationError(null);
    if (onCancel) {
      onCancel();
    }
  };

  // Validate session name in real-time
  const validateName = useCallback((name: string): string | null => {
    const trimmedName = name.trim();

    // Basic validation
    const nameValidation = validateSessionName(trimmedName);
    if (!nameValidation.isValid) {
      return nameValidation.error!;
    }

    // Check uniqueness
    if (!isSessionNameUnique(storage, trimmedName)) {
      return 'A session with this name already exists';
    }

    return null;
  }, [storage]);

  // Handle name input change
  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newName = e.target.value;
    setSessionName(newName);

    // Clear validation error if name becomes valid
    if (validationError && newName.trim()) {
      const error = validateName(newName);
      setValidationError(error);
    }
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate name
    const nameError = validateName(sessionName);
    if (nameError) {
      setValidationError(nameError);
      return;
    }

    try {
      setIsCreating(true);
      setValidationError(null);

      // Generate backend session ID (this would normally come from backend)
      const backendSessionId = generateSessionId();

      // Create session
      const sessionId = await createSession(sessionName.trim(), backendSessionId);

      // Success - close form and notify parent
      setIsFormOpen(false);
      setSessionName('');

      if (onSessionCreated) {
        onSessionCreated(sessionId);
      }

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create session';
      setValidationError(errorMessage);
    } finally {
      setIsCreating(false);
    }
  };

  // Default trigger button
  const defaultTrigger = (
    <Button
      onClick={handleOpen}
      disabled={isAtLimit || isLoading}
      className="flex items-center gap-2"
    >
      <Plus className="h-4 w-4" />
      Create New Session
    </Button>
  );

  // If closed and no custom trigger, show default trigger
  if (!isFormOpen && !trigger) {
    return (
      <div className="space-y-2">
        {defaultTrigger}
        {isApproachingLimit && (
          <Alert className="border-amber-200 bg-amber-50">
            <AlertTriangle className="h-4 w-4 text-amber-600" />
            <AlertDescription className="text-amber-800">
              {sessionCount} of {SESSION_CONSTRAINTS.MAX_SESSIONS} sessions used.
              Consider deleting old sessions.
            </AlertDescription>
          </Alert>
        )}
        {validationError && (
          <Alert className="border-red-200 bg-red-50">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">
              {validationError}
            </AlertDescription>
          </Alert>
        )}
      </div>
    );
  }

  // Custom trigger
  if (!isFormOpen && trigger) {
    return (
      <div onClick={handleOpen} className="cursor-pointer">
        {trigger}
      </div>
    );
  }

  // Form is open
  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Plus className="h-5 w-5 text-blue-600" />
              Create New Session
            </CardTitle>
            <CardDescription>
              Add a new monthly expense processing session
            </CardDescription>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClose}
            className="h-8 w-8 p-0"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>

      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Session Count Warning */}
          {isApproachingLimit && (
            <Alert className="border-amber-200 bg-amber-50">
              <AlertTriangle className="h-4 w-4 text-amber-600" />
              <AlertDescription className="text-amber-800">
                {sessionCount} of {SESSION_CONSTRAINTS.MAX_SESSIONS} sessions used.
              </AlertDescription>
            </Alert>
          )}

          {/* Session Name Input */}
          <div className="space-y-2">
            <Label htmlFor="session-name" className="text-sm font-medium">
              Session Name *
            </Label>
            <Input
              id="session-name"
              type="text"
              value={sessionName}
              onChange={handleNameChange}
              placeholder="e.g., January 2024 Expenses"
              disabled={isCreating}
              className={validationError ? 'border-red-300' : ''}
              maxLength={SESSION_CONSTRAINTS.MAX_NAME_LENGTH}
              autoFocus
            />
            <div className="flex justify-between text-xs text-gray-500">
              <span>
                {sessionName.length}/{SESSION_CONSTRAINTS.MAX_NAME_LENGTH} characters
              </span>
              {sessionName.trim() && !validationError && (
                <span className="flex items-center gap-1 text-green-600">
                  <CheckCircle className="h-3 w-3" />
                  Valid name
                </span>
              )}
            </div>
          </div>

          {/* Validation Error */}
          {validationError && (
            <Alert className="border-red-200 bg-red-50">
              <AlertTriangle className="h-4 w-4 text-red-600" />
              <AlertDescription className="text-red-800">
                {validationError}
              </AlertDescription>
            </Alert>
          )}

          {/* General Error */}
          {error && !validationError && (
            <Alert className="border-red-200 bg-red-50">
              <AlertTriangle className="h-4 w-4 text-red-600" />
              <AlertDescription className="text-red-800">
                {error}
              </AlertDescription>
            </Alert>
          )}

          {/* Form Actions */}
          <div className="flex gap-3 pt-2">
            <Button
              type="submit"
              disabled={!sessionName.trim() || !!validationError || isCreating}
              className="flex-1 flex items-center gap-2"
            >
              {isCreating ? (
                <>
                  <Loader className="h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Plus className="h-4 w-4" />
                  Create Session
                </>
              )}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={isCreating}
            >
              Cancel
            </Button>
          </div>

          {/* Help Text */}
          <div className="text-xs text-gray-500 space-y-1">
            <p>• Sessions automatically expire after 1 year</p>
            <p>• Use descriptive names like "Q1 2024" or "January Expenses"</p>
            <p>• You can rename sessions later</p>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

export default SessionCreator;