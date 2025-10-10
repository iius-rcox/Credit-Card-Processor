/**
 * Progress display component with SSE streaming.
 *
 * Client Component that shows real-time progress updates.
 */

"use client";

import { useState, useEffect } from "react";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface ProgressDisplayProps {
  sessionId: string;
  onComplete: () => void;
  onError: (error: string) => void;
}

export function ProgressDisplay({ sessionId, onComplete, onError }: ProgressDisplayProps) {
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState("Starting...");
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    setIsProcessing(true);
    setCurrentStep("Processing files...");
    setProgress(10);

    let currentProgress = 10;

    const pollInterval = setInterval(async () => {
      try {
        const { getSessionDetail } = await import("@/lib/api-client");
        const session = await getSessionDetail(sessionId);

        // Update progress based on status
        if (session.status === "processing") {
          currentProgress = Math.min(currentProgress + 10, 90);
          setProgress(currentProgress);
          setCurrentStep("Extracting data and matching transactions...");
        } else if (session.status === "completed") {
          setProgress(100);
          setCurrentStep("Complete!");
          clearInterval(pollInterval);
          setIsProcessing(false);
          onComplete();
        } else if (session.status === "failed") {
          clearInterval(pollInterval);
          setIsProcessing(false);
          onError("Processing failed");
        }
      } catch (err) {
        clearInterval(pollInterval);
        setIsProcessing(false);
        onError(err instanceof Error ? err.message : "Failed to check status");
      }
    }, 2000); // Poll every 2 seconds

    // Cleanup on unmount
    return () => clearInterval(pollInterval);
  }, [sessionId, onComplete, onError]);

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Processing PDFs</CardTitle>
        <CardDescription>Analyzing expenses and generating reports...</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Progress</span>
            <span>{progress}%</span>
          </div>
          <Progress value={progress} className="w-full" />
        </div>

        {/* Current Step */}
        <Alert>
          <AlertDescription>{currentStep}</AlertDescription>
        </Alert>

        {/* Processing Indicator */}
        {isProcessing && (
          <div className="text-sm text-muted-foreground text-center">
            Please wait while we process your files...
          </div>
        )}
      </CardContent>
    </Card>
  );
}
