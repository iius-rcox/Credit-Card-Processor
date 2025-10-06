/**
 * Results Panel Component for Feature 005
 *
 * Displays reconciliation results with download options
 */

"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { downloadReport } from "@/lib/api-client";
import type { SessionDetail } from "@/lib/api-client";

interface ResultsPanelProps {
  sessionDetail: SessionDetail;
}

export function ResultsPanel({ sessionDetail }: ResultsPanelProps) {
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const handleDownload = async (format: "xlsx" | "csv") => {
    setIsDownloading(true);
    setDownloadError(null);

    try {
      const blob = await downloadReport(sessionDetail.id, format);

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `reconciliation_${sessionDetail.id.substring(0, 8)}_${new Date().toISOString().split("T")[0]}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      setDownloadError(error instanceof Error ? error.message : "Download failed");
    } finally {
      setIsDownloading(false);
    }
  };

  const matchPercentage = sessionDetail.total_transactions > 0
    ? Math.round((sessionDetail.matched_count / sessionDetail.total_transactions) * 100)
    : 0;

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      {/* Summary Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Reconciliation Complete</span>
            <span className={`text-sm px-3 py-1 rounded-full ${
              sessionDetail.status === "completed"
                ? "bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200"
                : "bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200"
            }`}>
              {sessionDetail.status}
            </span>
          </CardTitle>
          <CardDescription>Session ID: {sessionDetail.id}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Match Statistics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard
              label="Total Transactions"
              value={sessionDetail.total_transactions}
              color="blue"
            />
            <StatCard
              label="Total Receipts"
              value={sessionDetail.total_receipts}
              color="purple"
            />
            <StatCard
              label="Matched"
              value={sessionDetail.matched_count}
              color="green"
            />
            <StatCard
              label="Match Rate"
              value={`${matchPercentage}%`}
              color={matchPercentage >= 80 ? "green" : matchPercentage >= 50 ? "yellow" : "red"}
            />
          </div>

          {/* Match Rate Progress Bar */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Match Success Rate</span>
              <span className="text-sm text-gray-500">{matchPercentage}%</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all ${
                  matchPercentage >= 80
                    ? "bg-green-500"
                    : matchPercentage >= 50
                    ? "bg-yellow-500"
                    : "bg-red-500"
                }`}
                style={{ width: `${matchPercentage}%` }}
              />
            </div>
          </div>

          {/* Download Buttons */}
          <div className="space-y-3">
            <h3 className="text-sm font-medium">Download Report</h3>
            <div className="flex gap-3">
              <Button
                onClick={() => handleDownload("xlsx")}
                disabled={isDownloading}
                className="flex-1"
              >
                {isDownloading ? "Downloading..." : "Download Excel (XLSX)"}
              </Button>
              <Button
                onClick={() => handleDownload("csv")}
                disabled={isDownloading}
                variant="outline"
                className="flex-1"
              >
                {isDownloading ? "Downloading..." : "Download CSV"}
              </Button>
            </div>
          </div>

          {/* Download Error */}
          {downloadError && (
            <Alert variant="destructive">
              <AlertDescription>{downloadError}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Detailed Results */}
      <div className="grid md:grid-cols-3 gap-4">
        {/* Employees */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Employees</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
              {sessionDetail.employees.length}
            </div>
            <p className="text-sm text-gray-500 mt-1">
              Employees found in statements
            </p>
          </CardContent>
        </Card>

        {/* Unmatched Transactions */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Unmatched</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-600 dark:text-orange-400">
              {sessionDetail.total_transactions - sessionDetail.matched_count}
            </div>
            <p className="text-sm text-gray-500 mt-1">
              Transactions without receipts
            </p>
          </CardContent>
        </Card>

        {/* Data Expiry */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Data Expiry</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg font-semibold text-gray-700 dark:text-gray-300">
              {new Date(sessionDetail.expires_at).toLocaleDateString()}
            </div>
            <p className="text-sm text-gray-500 mt-1">
              Data deleted after 90 days
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Match Results Preview */}
      {sessionDetail.match_results.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Recent Matches</CardTitle>
            <CardDescription>Top 5 matches by confidence score</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {sessionDetail.match_results.slice(0, 5).map((match, index) => {
                const transaction = sessionDetail.transactions.find(t => t.id === match.transaction_id);
                const receipt = match.receipt_id
                  ? sessionDetail.receipts.find(r => r.id === match.receipt_id)
                  : null;

                return (
                  <div
                    key={match.id}
                    className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                  >
                    <div className="flex-1">
                      <div className="font-medium">{transaction?.merchant_name || "Unknown"}</div>
                      <div className="text-sm text-gray-500">
                        ${transaction?.amount.toFixed(2)} →{" "}
                        {receipt ? `${receipt.vendor_name} $${receipt.amount.toFixed(2)}` : "No receipt"}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-xs px-2 py-1 rounded ${
                          match.match_status === "matched"
                            ? "bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200"
                            : "bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200"
                        }`}
                      >
                        {match.match_status}
                      </span>
                      <span className="text-sm font-medium">
                        {Math.round(match.confidence_score * 100)}%
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: number | string;
  color: "blue" | "purple" | "green" | "yellow" | "red";
}

function StatCard({ label, value, color }: StatCardProps) {
  const colorClasses = {
    blue: "text-blue-600 dark:text-blue-400",
    purple: "text-purple-600 dark:text-purple-400",
    green: "text-green-600 dark:text-green-400",
    yellow: "text-yellow-600 dark:text-yellow-400",
    red: "text-red-600 dark:text-red-400",
  };

  return (
    <div className="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
      <div className={`text-3xl font-bold ${colorClasses[color]}`}>{value}</div>
      <div className="text-xs text-gray-500 mt-1">{label}</div>
    </div>
  );
}
