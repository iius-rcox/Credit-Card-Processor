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
import { processSession } from "@/lib/api-client";
import type { ProcessProgressEvent } from "@/lib/types";

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
    // Start processing when component mounts
    startProcessing();
  }, [sessionId]);

  const startProcessing = async () => {
    setIsProcessing(true);

    try {
      await processSession(sessionId, (event: ProcessProgressEvent) => {
        setProgress(event.progress);
        setCurrentStep(event.step);

        if (event.status === "complete") {
          setIsProcessing(false);
          onComplete();
        } else if (event.status === "error") {
          setIsProcessing(false);
          onError(event.error || "Processing failed");
        }
      });
    } catch (err) {
      setIsProcessing(false);
      onError(err instanceof Error ? err.message : "Processing failed");
    }
  };

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
