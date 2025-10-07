/**
 * Progress Display Component for Feature 005
 *
 * Shows upload and processing progress with status updates
 */

"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import type { Session, SessionDetail } from "@/lib/api-client";

interface ProgressDisplayProps {
  session: Session;
  sessionDetail: SessionDetail | null;
}

export function ProgressDisplay({ session, sessionDetail }: ProgressDisplayProps) {
  // Calculate progress percentage based on status
  const getProgress = () => {
    const status = sessionDetail?.status || session.status;
    switch (status) {
      case "processing":
        return 25;
      case "completed":
        return 100;
      case "failed":
        return 100;
      default:
        return 10;
    }
  };

  const getStatusMessage = () => {
    const status = sessionDetail?.status || session.status;
    switch (status) {
      case "processing":
        return "Processing your files...";
      case "completed":
        return "Processing complete!";
      case "failed":
        return "Processing failed";
      default:
        return "Uploading...";
    }
  };

  const getStatusColor = () => {
    const status = sessionDetail?.status || session.status;
    switch (status) {
      case "completed":
        return "text-green-600 dark:text-green-400";
      case "failed":
        return "text-red-600 dark:text-red-400";
      default:
        return "text-blue-600 dark:text-blue-400";
    }
  };

  return (
    <Card className="w-full max-w-3xl mx-auto">
      <CardHeader>
        <CardTitle>Processing Status</CardTitle>
        <CardDescription>Session ID: {session.id}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className={`text-sm font-medium ${getStatusColor()}`}>
              {getStatusMessage()}
            </span>
            <span className="text-sm text-gray-500">{getProgress()}%</span>
          </div>
          <Progress value={getProgress()} className="h-2" />
        </div>

        {/* Status Details */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Files Uploaded */}
          <div className="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className="text-2xl font-bold">
              {sessionDetail?.upload_count || session.upload_count}
            </div>
            <div className="text-xs text-gray-500">Files Uploaded</div>
          </div>

          {/* Transactions */}
          <div className="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className="text-2xl font-bold">
              {sessionDetail?.total_transactions || session.total_transactions}
            </div>
            <div className="text-xs text-gray-500">Transactions</div>
          </div>

          {/* Receipts */}
          <div className="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className="text-2xl font-bold">
              {sessionDetail?.total_receipts || session.total_receipts}
            </div>
            <div className="text-xs text-gray-500">Receipts</div>
          </div>

          {/* Matches */}
          <div className="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">
              {sessionDetail?.matched_count || session.matched_count}
            </div>
            <div className="text-xs text-gray-500">Matches Found</div>
          </div>
        </div>

        {/* Processing Steps */}
        <div className="space-y-2">
          <ProcessingStep
            label="Upload Complete"
            isComplete={true}
            isCurrent={false}
          />
          <ProcessingStep
            label="Extracting Data"
            isComplete={sessionDetail?.total_transactions ? true : false}
            isCurrent={session.status === "processing" && !sessionDetail}
          />
          <ProcessingStep
            label="Matching Transactions"
            isComplete={sessionDetail?.matched_count ? true : false}
            isCurrent={sessionDetail?.status === "processing"}
          />
          <ProcessingStep
            label="Complete"
            isComplete={sessionDetail?.status === "completed"}
            isCurrent={false}
          />
        </div>

        {/* Session Info */}
        <div className="text-xs text-gray-500 space-y-1">
          <div>Created: {new Date(session.created_at).toLocaleString()}</div>
          <div>Expires: {new Date(session.expires_at).toLocaleString()}</div>
        </div>
      </CardContent>
    </Card>
  );
}

interface ProcessingStepProps {
  label: string;
  isComplete: boolean;
  isCurrent: boolean;
}

function ProcessingStep({ label, isComplete, isCurrent }: ProcessingStepProps) {
  return (
    <div className="flex items-center space-x-3">
      {/* Indicator */}
      <div
        className={`
          w-4 h-4 rounded-full flex items-center justify-center
          ${isComplete ? "bg-green-500" : isCurrent ? "bg-blue-500 animate-pulse" : "bg-gray-300 dark:bg-gray-700"}
        `}
      >
        {isComplete && (
          <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
              clipRule="evenodd"
            />
          </svg>
        )}
      </div>

      {/* Label */}
      <span
        className={`text-sm ${
          isComplete
            ? "text-gray-900 dark:text-gray-100 font-medium"
            : isCurrent
            ? "text-blue-600 dark:text-blue-400 font-medium"
            : "text-gray-500"
        }`}
      >
        {label}
      </span>
    </div>
  );
}
