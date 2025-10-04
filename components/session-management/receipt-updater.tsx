'use client';

/**
 * ReceiptUpdater - Receipt Upload and Processing Component
 *
 * Provides file upload interface for updating session receipts
 * according to specs/003-add-ui-components/quickstart.md - Scenario 3
 */

import React, { useState, useRef, useCallback } from 'react';
import { useSession } from './session-provider';
import { validateReceiptFile } from '@/lib/session-utils';
import { MonthSession } from '@/lib/session-types';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';

import {
  Upload,
  X,
  AlertTriangle,
  Loader,
  CheckCircle,
  FileText,
  RefreshCw,
  Download,
} from 'lucide-react';

interface ReceiptUpdaterProps {
  sessionId: string | null;
  isOpen: boolean;
  onClose: () => void;
  onUpdated?: (sessionId: string) => void;
}

export function ReceiptUpdater({
  sessionId,
  isOpen,
  onClose,
  onUpdated,
}: ReceiptUpdaterProps) {
  const { storage, updateReceipts, isLoading } = useSession();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Component state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);

  // Get session data
  const session: MonthSession | null = sessionId ? storage.sessions[sessionId] : null;

  // Handle file selection
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) {
      setSelectedFile(null);
      setValidationError(null);
      return;
    }

    // Validate file
    const validation = validateReceiptFile(file);
    if (!validation.isValid) {
      setValidationError(validation.error!);
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
    setValidationError(null);
    setUploadSuccess(false);
  };

  // Handle drag and drop
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];

      // Validate file
      const validation = validateReceiptFile(file);
      if (!validation.isValid) {
        setValidationError(validation.error!);
        setSelectedFile(null);
        return;
      }

      setSelectedFile(file);
      setValidationError(null);
      setUploadSuccess(false);
    }
  };

  // Handle file upload
  const handleUpload = async () => {
    if (!selectedFile || !sessionId || !session) {
      setValidationError('No file selected or session not found');
      return;
    }

    try {
      setIsUploading(true);
      setValidationError(null);
      setUploadProgress(0);

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      // Upload file
      await updateReceipts(sessionId, selectedFile);

      // Complete progress
      clearInterval(progressInterval);
      setUploadProgress(100);
      setUploadSuccess(true);

      // Notify parent
      if (onUpdated) {
        onUpdated(sessionId);
      }

      // Auto-close after success
      setTimeout(() => {
        handleClose();
      }, 2000);

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      setValidationError(errorMessage);
      setUploadProgress(0);
    } finally {
      setIsUploading(false);
    }
  };

  // Handle close
  const handleClose = () => {
    setSelectedFile(null);
    setValidationError(null);
    setUploadProgress(0);
    setIsUploading(false);
    setUploadSuccess(false);
    onClose();
  };

  // Clear file selection
  const handleClearFile = () => {
    setSelectedFile(null);
    setValidationError(null);
    setUploadSuccess(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Format file size
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Don't render if not open or no session
  if (!isOpen || !session) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="w-full max-w-lg mx-4">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="h-5 w-5 text-blue-600" />
                  Update Receipts
                </CardTitle>
                <CardDescription>
                  Upload additional expense reports for "{session.name}"
                </CardDescription>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClose}
                disabled={isUploading}
                className="h-8 w-8 p-0"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>

          <CardContent className="space-y-4">
            {/* Session Info */}
            <div className="p-3 bg-gray-50 rounded-md text-sm">
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="font-medium">Status:</span>
                  <span className="ml-2 text-gray-600">{session.status}</span>
                </div>
                <div>
                  <span className="font-medium">Files:</span>
                  <span className="ml-2 text-gray-600">{session.fileCount}</span>
                </div>
                <div>
                  <span className="font-medium">Matches:</span>
                  <span className="ml-2 text-gray-600">{session.matchCount}</span>
                </div>
                <div>
                  <span className="font-medium">Reports:</span>
                  <span className="ml-2 text-gray-600">
                    {session.hasReports ? 'Available' : 'None'}
                  </span>
                </div>
              </div>
            </div>

            {/* File Upload Area */}
            {!uploadSuccess && (
              <div
                className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                  selectedFile
                    ? 'border-green-300 bg-green-50'
                    : 'border-gray-300 hover:border-gray-400 bg-gray-50'
                } ${isUploading ? 'opacity-50' : ''}`}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
              >
                {selectedFile ? (
                  <div className="space-y-3">
                    <div className="flex items-center justify-center">
                      <FileText className="h-8 w-8 text-green-600" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{selectedFile.name}</p>
                      <p className="text-sm text-gray-500">
                        {formatFileSize(selectedFile.size)} • PDF
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleClearFile}
                      disabled={isUploading}
                      className="text-xs"
                    >
                      Choose Different File
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="flex items-center justify-center">
                      <Upload className="h-8 w-8 text-gray-400" />
                    </div>
                    <div>
                      <p className="text-gray-600">
                        Drag and drop your expense report here, or
                      </p>
                      <Button
                        variant="outline"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isUploading}
                        className="mt-2"
                      >
                        Choose File
                      </Button>
                    </div>
                    <p className="text-xs text-gray-500">
                      PDF files only, max 50MB
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Upload Progress */}
            {isUploading && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>Uploading and processing...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <Progress value={uploadProgress} className="h-2" />
              </div>
            )}

            {/* Success Message */}
            {uploadSuccess && (
              <Alert className="border-green-200 bg-green-50">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <AlertDescription className="text-green-800">
                  Receipt update completed successfully! Reports have been regenerated.
                </AlertDescription>
              </Alert>
            )}

            {/* Validation Error */}
            {validationError && (
              <Alert className="border-red-200 bg-red-50">
                <AlertTriangle className="h-4 w-4 text-red-600" />
                <AlertDescription className="text-red-800">
                  {validationError}
                </AlertDescription>
              </Alert>
            )}

            {/* Form Actions */}
            {!uploadSuccess && (
              <div className="flex gap-3 pt-2">
                <Button
                  onClick={handleUpload}
                  disabled={!selectedFile || isUploading || isLoading}
                  className="flex-1 flex items-center gap-2"
                >
                  {isUploading ? (
                    <>
                      <Loader className="h-4 w-4 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="h-4 w-4" />
                      Update Receipts
                    </>
                  )}
                </Button>
                <Button
                  variant="outline"
                  onClick={handleClose}
                  disabled={isUploading}
                >
                  Cancel
                </Button>
              </div>
            )}

            {/* Success Actions */}
            {uploadSuccess && session.hasReports && (
              <div className="flex gap-3 pt-2">
                <Button
                  variant="outline"
                  className="flex-1 flex items-center gap-2"
                  onClick={handleClose}
                >
                  <Download className="h-4 w-4" />
                  View Updated Reports
                </Button>
                <Button onClick={handleClose}>
                  Done
                </Button>
              </div>
            )}

            {/* Help Text */}
            <div className="text-xs text-gray-500 space-y-1">
              <p>• Only PDF expense reports are accepted</p>
              <p>• Original session data is preserved on upload failure</p>
              <p>• Re-processing may take a few moments</p>
              <p>• New reports will be generated after successful update</p>
            </div>

            {/* Hidden File Input */}
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleFileSelect}
              className="hidden"
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default ReceiptUpdater;