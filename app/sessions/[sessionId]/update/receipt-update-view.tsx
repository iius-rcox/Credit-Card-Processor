/**
 * Receipt Update View Component
 *
 * Allows uploading additional receipts to an existing reconciliation session.
 * Used for incremental updates after initial session creation.
 */

"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ArrowLeft, Upload, FileText, CheckCircle2, XCircle } from "lucide-react";
import Link from "next/link";

interface ReceiptUpdateViewProps {
  sessionId: string;
}

const MAX_FILES = 50;
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export default function ReceiptUpdateView({ sessionId }: ReceiptUpdateViewProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadComplete, setUploadComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validateFiles = (files: File[]): string | null => {
    if (files.length === 0) {
      return "Please select at least one PDF file";
    }
    if (files.length > MAX_FILES) {
      return `Maximum ${MAX_FILES} files allowed`;
    }

    for (const file of files) {
      if (file.type !== "application/pdf") {
        return `File "${file.name}" is not a PDF`;
      }
      if (file.size > MAX_FILE_SIZE) {
        return `File "${file.name}" exceeds 10MB limit`;
      }
    }

    return null;
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
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

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      setError("Please select files to upload");
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      // TODO: Implement API call to upload additional receipts
      // await updateSessionReceipts(sessionId, selectedFiles);

      // Simulate upload for now
      await new Promise(resolve => setTimeout(resolve, 2000));

      setUploadComplete(true);
      setIsUploading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setIsUploading(false);
    }
  };

  const handleRemoveFile = (index: number) => {
    setSelectedFiles(files => files.filter((_, i) => i !== index));
  };

  if (uploadComplete) {
    return (
      <div className="container mx-auto py-8 max-w-2xl">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2 text-green-600">
              <CheckCircle2 className="h-6 w-6" />
              <CardTitle>Upload Complete</CardTitle>
            </div>
            <CardDescription>
              Additional receipts have been uploaded successfully
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              {selectedFiles.length} receipt{selectedFiles.length !== 1 ? 's' : ''} uploaded
            </p>
            <div className="flex gap-4">
              <Button asChild variant="default">
                <Link href={`/sessions/${sessionId}`}>
                  View Session Details
                </Link>
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setUploadComplete(false);
                  setSelectedFiles([]);
                }}
              >
                Upload More
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 max-w-4xl">
      <div className="mb-6">
        <Button asChild variant="ghost" size="sm">
          <Link href={`/sessions/${sessionId}`}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Session
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Update Receipts</CardTitle>
          <CardDescription>
            Upload additional receipt PDFs for session {sessionId.slice(0, 8)}...
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {error && (
            <Alert variant="destructive">
              <XCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="space-y-4">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
              <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <label
                htmlFor="receipt-upload"
                className="cursor-pointer text-blue-600 hover:text-blue-500"
              >
                <span className="text-sm font-medium">Click to select PDF files</span>
                <input
                  id="receipt-upload"
                  type="file"
                  accept="application/pdf"
                  multiple
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </label>
              <p className="text-xs text-gray-500 mt-2">
                Maximum {MAX_FILES} files, 10MB each
              </p>
            </div>

            {selectedFiles.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium">
                  Selected Files ({selectedFiles.length})
                </h4>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {selectedFiles.map((file, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <FileText className="h-5 w-5 text-blue-600" />
                        <div>
                          <p className="text-sm font-medium">{file.name}</p>
                          <p className="text-xs text-gray-500">
                            {(file.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemoveFile(index)}
                        disabled={isUploading}
                      >
                        <XCircle className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex gap-4">
              <Button
                onClick={handleUpload}
                disabled={selectedFiles.length === 0 || isUploading}
                className="flex-1"
              >
                {isUploading ? (
                  <>
                    <span className="animate-spin mr-2">⏳</span>
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4 mr-2" />
                    Upload {selectedFiles.length} Receipt{selectedFiles.length !== 1 ? 's' : ''}
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
