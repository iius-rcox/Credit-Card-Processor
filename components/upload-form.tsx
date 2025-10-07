/**
 * Upload form component for PDF file uploads.
 *
 * Client Component using Shad.CN components.
 */

"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { uploadPDFs } from "@/lib/api-client";
import { initializeSessionStorage, createNewSession } from "@/lib/session-storage";

interface UploadFormProps {
  onUploadComplete: (sessionId: string) => void;
}

export function UploadForm({ onUploadComplete }: UploadFormProps) {
  const [creditCardFile, setCreditCardFile] = useState<File | null>(null);
  const [expenseReportFile, setExpenseReportFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);

    // Validate files selected
    if (!creditCardFile || !expenseReportFile) {
      setError("Please select both PDF files");
      return;
    }

    setIsUploading(true);

    try {
      // Call API
      const response = await uploadPDFs(creditCardFile, expenseReportFile);

      // Save session to localStorage
      const storage = initializeSessionStorage();
      const { sessionId } = createNewSession(storage, `Session ${new Date().toLocaleDateString()}`, response.session_id);

      // Show success
      setSuccessMessage(`Files uploaded successfully! Session ID: ${response.session_id}`);

      // Notify parent component
      onUploadComplete(response.session_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Upload PDF Files</CardTitle>
        <CardDescription>
          Upload your Cardholder Activity Report and Receipt Report for reconciliation
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Cardholder Activity Report Input */}
          <div className="space-y-2">
            <Label htmlFor="creditCard">Cardholder Activity Report (PDF)</Label>
            <Input
              id="creditCard"
              type="file"
              accept=".pdf"
              onChange={(e) => setCreditCardFile(e.target.files?.[0] || null)}
              disabled={isUploading}
              required
            />
          </div>

          {/* Receipt Report Input */}
          <div className="space-y-2">
            <Label htmlFor="expenseReport">Receipt Report (PDF)</Label>
            <Input
              id="expenseReport"
              type="file"
              accept=".pdf"
              onChange={(e) => setExpenseReportFile(e.target.files?.[0] || null)}
              disabled={isUploading}
              required
            />
          </div>

          {/* Error Alert */}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Success Alert */}
          {successMessage && (
            <Alert>
              <AlertDescription>{successMessage}</AlertDescription>
            </Alert>
          )}

          {/* Submit Button */}
          <Button type="submit" disabled={isUploading} className="w-full">
            {isUploading ? "Processing..." : "Process Reports"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
