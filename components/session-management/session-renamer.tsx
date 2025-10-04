'use client';

/**
 * SessionRenamer - Session Rename Dialog Component
 *
 * Provides modal dialog for renaming sessions with validation
 * according to specs/003-add-ui-components/quickstart.md - Scenario 2
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useSession } from './session-provider';
import { validateSessionName, isSessionNameUnique } from '@/lib/session-utils';
import { SESSION_CONSTRAINTS } from '@/lib/session-types';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';

import {
  Edit3,
  X,
  AlertTriangle,
  Loader,
  CheckCircle,
  Save,
} from 'lucide-react';

interface SessionRenamerProps {
  sessionId: string | null;
  isOpen: boolean;
  onClose: () => void;
  onRenamed?: (sessionId: string, newName: string) => void;
}

export function SessionRenamer({
  sessionId,
  isOpen,
  onClose,
  onRenamed,
}: SessionRenamerProps) {
  const { storage, renameSession, isLoading, error } = useSession();

  // Component state
  const [newName, setNewName] = useState('');
  const [originalName, setOriginalName] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);
  const [isRenaming, setIsRenaming] = useState(false);

  // Get session data
  const session = sessionId ? storage.sessions[sessionId] : null;

  // Initialize form when opened
  useEffect(() => {
    if (isOpen && session) {
      setNewName(session.name);
      setOriginalName(session.name);
      setValidationError(null);
    } else if (!isOpen) {
      // Reset form when closed
      setNewName('');
      setOriginalName('');
      setValidationError(null);
    }
  }, [isOpen, session]);

  // Validate session name in real-time
  const validateName = useCallback((name: string): string | null => {
    const trimmedName = name.trim();

    // Check if name changed
    if (trimmedName === originalName) {
      return null; // No change is valid
    }

    // Basic validation
    const nameValidation = validateSessionName(trimmedName);
    if (!nameValidation.isValid) {
      return nameValidation.error!;
    }

    // Check uniqueness (excluding current session)
    if (!isSessionNameUnique(storage, trimmedName, sessionId!)) {
      return 'A session with this name already exists';
    }

    return null;
  }, [storage, sessionId, originalName]);

  // Handle name input change
  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const name = e.target.value;
    setNewName(name);

    // Clear validation error if name becomes valid
    if (validationError && name.trim()) {
      const error = validateName(name);
      setValidationError(error);
    }
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const trimmedName = newName.trim();

    // Check if name actually changed
    if (trimmedName === originalName) {
      onClose();
      return;
    }

    // Validate name
    const nameError = validateName(trimmedName);
    if (nameError) {
      setValidationError(nameError);
      return;
    }

    if (!sessionId) {
      setValidationError('No session selected');
      return;
    }

    try {
      setIsRenaming(true);
      setValidationError(null);

      // Rename session
      await renameSession(sessionId, trimmedName);

      // Success - close dialog and notify parent
      onClose();

      if (onRenamed) {
        onRenamed(sessionId, trimmedName);
      }

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to rename session';
      setValidationError(errorMessage);
    } finally {
      setIsRenaming(false);
    }
  };

  // Handle cancel
  const handleCancel = () => {
    setNewName(originalName); // Reset to original name
    setValidationError(null);
    onClose();
  };

  // Handle keyboard shortcuts
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      handleCancel();
    }
  };

  // Don't render if not open or no session
  if (!isOpen || !session) {
    return null;
  }

  const hasChanges = newName.trim() !== originalName;
  const isNameValid = !validateName(newName);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="w-full max-w-md mx-4">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Edit3 className="h-5 w-5 text-blue-600" />
                  Rename Session
                </CardTitle>
                <CardDescription>
                  Change the name of "{originalName}"
                </CardDescription>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCancel}
                className="h-8 w-8 p-0"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Session Name Input */}
              <div className="space-y-2">
                <Label htmlFor="new-session-name" className="text-sm font-medium">
                  Session Name *
                </Label>
                <Input
                  id="new-session-name"
                  type="text"
                  value={newName}
                  onChange={handleNameChange}
                  onKeyDown={handleKeyDown}
                  placeholder="Enter new session name"
                  disabled={isRenaming}
                  className={validationError ? 'border-red-300' : ''}
                  maxLength={SESSION_CONSTRAINTS.MAX_NAME_LENGTH}
                  autoFocus
                />
                <div className="flex justify-between text-xs text-gray-500">
                  <span>
                    {newName.length}/{SESSION_CONSTRAINTS.MAX_NAME_LENGTH} characters
                  </span>
                  {newName.trim() && isNameValid && hasChanges && (
                    <span className="flex items-center gap-1 text-green-600">
                      <CheckCircle className="h-3 w-3" />
                      Valid name
                    </span>
                  )}
                  {!hasChanges && newName.trim() && (
                    <span className="text-gray-400">
                      No changes
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

              {/* Session Info */}
              <div className="p-3 bg-gray-50 rounded-md text-sm">
                <div className="space-y-1">
                  <div>
                    <span className="font-medium">Current Name:</span>
                    <span className="ml-2 text-gray-600">{originalName}</span>
                  </div>
                  <div>
                    <span className="font-medium">Status:</span>
                    <span className="ml-2 text-gray-600">{session.status}</span>
                  </div>
                  <div>
                    <span className="font-medium">Created:</span>
                    <span className="ml-2 text-gray-600">
                      {new Date(session.createdAt).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>

              {/* Form Actions */}
              <div className="flex gap-3 pt-2">
                <Button
                  type="submit"
                  disabled={!hasChanges || !isNameValid || isRenaming}
                  className="flex-1 flex items-center gap-2"
                >
                  {isRenaming ? (
                    <>
                      <Loader className="h-4 w-4 animate-spin" />
                      Renaming...
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4" />
                      Save Changes
                    </>
                  )}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleCancel}
                  disabled={isRenaming}
                >
                  Cancel
                </Button>
              </div>

              {/* Help Text */}
              <div className="text-xs text-gray-500 space-y-1">
                <p>• Press Escape to cancel</p>
                <p>• Session functionality will remain unchanged</p>
                <p>• Name must be unique among your sessions</p>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default SessionRenamer;