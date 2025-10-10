/**
 * Results panel component displaying matched expenses.
 *
 * Shows employee list with completion badges and expense details.
 */

"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { SessionResponse, ReportsResponse } from "@/lib/types";

interface ResultsPanelProps {
  sessionData: SessionResponse;
  reportsData?: ReportsResponse; // Make optional
  onDownloadExcel: () => void;
  onDownloadCSV: () => void;
  onUploadNewReceipts: () => void;
}

export function ResultsPanel({
  sessionData,
  reportsData,
  onDownloadExcel,
  onDownloadCSV,
  onUploadNewReceipts,
}: ResultsPanelProps) {
  // Safely handle missing reportsData with fallback
  const summary = reportsData?.summary || {
    total_employees: 0,
    complete_employees: 0,
    incomplete_employees: 0,
    total_expenses: 0,
    expenses_missing_receipts: 0,
    expenses_missing_gl_codes: 0,
    expenses_missing_both: 0,
  };

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      {/* Summary Statistics Card */}
      <Card>
        <CardHeader>
          <CardTitle>Reconciliation Summary</CardTitle>
          <CardDescription>Overview of expense matching results</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-2xl font-bold">{summary.total_employees}</div>
              <div className="text-sm text-muted-foreground">Total Employees</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">{summary.complete_employees}</div>
              <div className="text-sm text-muted-foreground">Complete Employees</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-red-600">{summary.incomplete_employees}</div>
              <div className="text-sm text-muted-foreground">Incomplete Employees</div>
            </div>
            <div>
              <div className="text-2xl font-bold">{summary.total_expenses}</div>
              <div className="text-sm text-muted-foreground">Total Expenses</div>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-3 gap-4">
            <div>
              <div className="text-lg font-semibold text-yellow-600">
                {summary.expenses_missing_receipts}
              </div>
              <div className="text-xs text-muted-foreground">Missing Receipts</div>
            </div>
            <div>
              <div className="text-lg font-semibold text-orange-600">
                {summary.expenses_missing_gl_codes}
              </div>
              <div className="text-xs text-muted-foreground">Missing GL Codes</div>
            </div>
            <div>
              <div className="text-lg font-semibold text-red-600">{summary.expenses_missing_both}</div>
              <div className="text-xs text-muted-foreground">Missing Both</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <Button onClick={onDownloadExcel} disabled={!reportsData?.excel_report}>
          Download Excel Report ({summary.total_expenses - summary.complete_expenses} incomplete)
        </Button>
        <Button onClick={onDownloadCSV} variant="secondary" disabled={!reportsData?.csv_export}>
          Download CSV Export ({summary.complete_expenses} complete)
        </Button>
        <Button onClick={onUploadNewReceipts} variant="outline">
          Upload New Receipts
        </Button>
      </div>

      {/* Employee List */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Employees</h3>
        {sessionData.employees.map((employee) => (
          <Card key={employee.employee_id}>
            <CardHeader>
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle className="text-base">
                    {employee.name} ({employee.employee_id})
                  </CardTitle>
                  <CardDescription>Card: {employee.card_number}</CardDescription>
                </div>
                <div>
                  {employee.completion_status === "complete" ? (
                    <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                      Complete
                    </span>
                  ) : (
                    <span className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm font-medium">
                      Incomplete
                    </span>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-sm space-y-2">
                <div>
                  Expenses: {employee.expenses.length} | Receipts: {employee.receipts.length}
                </div>

                {/* Show incomplete expenses */}
                {employee.expenses.filter((e) => e.status !== "Complete").length > 0 && (
                  <div className="mt-2">
                    <div className="font-medium mb-1">Incomplete Items:</div>
                    <ul className="list-disc list-inside space-y-1">
                      {employee.expenses
                        .filter((e) => e.status !== "Complete")
                        .slice(0, 5)
                        .map((expense) => (
                          <li key={expense.transaction_id} className="text-xs">
                            ${expense.transaction_amount.toFixed(2)} - {expense.transaction_name}{" "}
                            <span
                              className={`ml-2 px-2 py-0.5 rounded text-xs ${
                                expense.status === "Missing Both"
                                  ? "bg-red-100 text-red-800"
                                  : expense.status === "Missing Receipt"
                                  ? "bg-yellow-100 text-yellow-800"
                                  : "bg-orange-100 text-orange-800"
                              }`}
                            >
                              {expense.status}
                            </span>
                          </li>
                        ))}
                    </ul>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
