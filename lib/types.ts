/**
 * TypeScript type definitions mirroring Python Pydantic models.
 *
 * These types ensure type safety across the Next.js frontend.
 */

// Enums

export type CompletionStatus = "complete" | "incomplete";

export type ExpenseStatus = "Missing Receipt" | "Missing GL Code" | "Missing Both" | "Complete";

export type ProcessingStatus = "pending" | "processing" | "complete" | "error";

export type MatchReason = "exact_match" | "no_receipt_found" | "multiple_matches";

// Entity Types

export interface ReceiptRecord {
  receipt_id: string;
  employee_id: string;
  amount: number;
  gl_code?: string | null;
  project_code?: string | null;
}

export interface ExpenseTransaction {
  transaction_id: string;
  employee_id: string;
  transaction_date: string; // ISO 8601 date
  transaction_amount: number;
  transaction_name: string;
  vendor_invoice_number?: string | null;
  invoice_date?: string | null;
  header_description?: string | null;
  job?: string | null;
  phase?: string | null;
  cost_type?: string | null;
  gl_account?: string | null;
  item_description?: string | null;
  um?: string | null;
  tax?: number | null;
  pay_type?: string | null;
  has_receipt: boolean;
  has_gl_code: boolean;
  status: ExpenseStatus;
}

export interface Employee {
  employee_id: string;
  name: string;
  card_number: string;
  expenses: ExpenseTransaction[];
  receipts: ReceiptRecord[];
  completion_status: CompletionStatus;
}

export interface MatchingResult {
  expense_transaction_id: string;
  matched_receipt_id?: string | null;
  has_gl_code: boolean;
  match_reason: MatchReason;
}

export interface Session {
  session_id: string;
  created_at: string;
  updated_at: string;
  processing_status: ProcessingStatus;
  error_message?: string | null;
  employees: Employee[];
  matching_results: MatchingResult[];
}

// API Response Types

export interface UploadResponse {
  session_id: string;
  uploaded_files: {
    credit_card_statement: {
      filename: string;
      size: number;
    };
    expense_report: {
      filename: string;
      size: number;
    };
  };
  created_at: string;
}

export interface ProcessProgressEvent {
  progress: number; // 0-100
  step: string;
  status: "processing" | "complete" | "error";
  error?: string;
}

export interface SessionResponse {
  session_id: string;
  created_at: string;
  updated_at: string;
  processing_status: ProcessingStatus;
  error_message?: string | null;
  employees: Employee[];
  matching_results: MatchingResult[];
}

export interface ReportSummary {
  total_employees: number;
  complete_employees: number;
  incomplete_employees: number;
  total_expenses: number;
  complete_expenses: number;
  expenses_missing_receipts: number;
  expenses_missing_gl_codes: number;
  expenses_missing_both: number;
}

export interface ReportsResponse {
  session_id: string;
  excel_report?: {
    url: string;
    file_size: number;
    row_count: number;
    generated_at: string;
  } | null;
  csv_export?: {
    url: string;
    file_size: number;
    row_count: number;
    included_employee_count: number;
    generated_at: string;
  } | null;
  summary: ReportSummary;
}

export interface UpdateResponse {
  session_id: string;
  updated: boolean;
  updated_at: string;
  summary_changes: {
    previous: {
      complete_employees: number;
      incomplete_expenses: number;
    };
    current: {
      complete_employees: number;
      incomplete_expenses: number;
    };
    newly_complete_employees: string[];
    newly_incomplete_expenses: string[];
  };
  new_excel_report_url?: string | null;
  new_csv_export_url?: string | null;
}
