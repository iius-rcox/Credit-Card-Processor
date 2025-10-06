/**
 * Upload form component for Feature 005 - Multiple PDF files upload.
 *
 * Supports uploading multiple PDF files (credit card statements + receipts)
 * with drag-and-drop, validation, and progress tracking.
 */

"use client";

import { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { uploadFiles } from "@/lib/api-client";
import type { Session } from "@/lib/api-client";

interface UploadFormProps {
  onUploadComplete: (session: Session) => void;
}

const MAX_FILES = 100;
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB in bytes

export function UploadForm({ onUploadComplete }: UploadFormProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const validateFiles = (files: File[]): string | null => {
    // Check file count
    if (files.length === 0) {
      return "Please select at least one PDF file";
    }
    if (files.length > MAX_FILES) {
      return `Maximum ${MAX_FILES} files allowed`;
    }

    // Check file types and sizes
    for (const file of files) {
      if (file.type !== "application/pdf") {
        return `File "${file.name}" is not a PDF. Only PDF files are allowed.`;
      }
      if (file.size > MAX_FILE_SIZE) {
        return `File "${file.name}" exceeds 10MB limit`;
      }
    }

    return null;
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const validationError = validateFiles(files);

    if (validationError) {
      setError(validationError);
      setSelectedFiles([]);
    } else {
      setError(null);
      setSelectedFiles(files);
    }
  };

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);

    const files = Array.from(e.dataTransfer.files);
    const validationError = validateFiles(files);

    if (validationError) {
      setError(validationError);
      setSelectedFiles([]);
    } else {
      setError(null);
      setSelectedFiles(files);
    }
  }, []);

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const validationError = validateFiles(selectedFiles);
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsUploading(true);

    try {
      // Call API to upload files
      const session = await uploadFiles(selectedFiles);

      // Notify parent component
      onUploadComplete(session);

      // Clear form
      setSelectedFiles([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed. Please try again.");
    } finally {
      setIsUploading(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <Card className="w-full max-w-3xl mx-auto">
      <CardHeader>
        <CardTitle>Upload PDF Files</CardTitle>
        <CardDescription>
          Upload credit card statements and receipts for reconciliation (max {MAX_FILES} files, 10MB each)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Drag-and-Drop Area */}
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            className={`
              border-2 border-dashed rounded-lg p-8 text-center transition-colors
              ${isDragOver ? "border-primary bg-primary/5" : "border-gray-300 dark:border-gray-700"}
              ${isUploading ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}
            `}
          >
            <input
              type="file"
              multiple
              accept=".pdf,application/pdf"
              onChange={handleFileChange}
              disabled={isUploading}
              className="hidden"
              id="file-input"
            />
            <label htmlFor="file-input" className="cursor-pointer">
              <div className="space-y-2">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400"
                  stroke="currentColor"
                  fill="none"
                  viewBox="0 0 48 48"
                  aria-hidden="true"
                >
                  <path
                    d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                    strokeWidth={2}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  <span className="font-semibold text-primary">Click to upload</span> or drag and drop
                </div>
                <p className="text-xs text-gray-500">PDF files only, up to 10MB each</p>
              </div>
            </label>
          </div>

          {/* Selected Files List */}
          {selectedFiles.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-medium">
                Selected Files ({selectedFiles.length}/{MAX_FILES})
              </h3>
              <div className="max-h-60 overflow-y-auto space-y-2 border rounded-lg p-2">
                {selectedFiles.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{file.name}</p>
                      <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                    </div>
                    {!isUploading && (
                      <button
                        type="button"
                        onClick={() => removeFile(index)}
                        className="ml-2 text-red-500 hover:text-red-700"
                        aria-label="Remove file"
                      >
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                          <path
                            fillRule="evenodd"
                            d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                            clipRule="evenodd"
                          />
                        </svg>
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Error Alert */}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Submit Button */}
          <Button
            type="submit"
            disabled={isUploading || selectedFiles.length === 0}
            className="w-full"
            size="lg"
          >
            {isUploading
              ? `Uploading ${selectedFiles.length} file(s)...`
              : `Upload ${selectedFiles.length} file(s)`}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
