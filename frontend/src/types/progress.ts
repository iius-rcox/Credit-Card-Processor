/**
 * TypeScript types for progress tracking feature.
 *
 * These types mirror the backend Pydantic schemas for type safety
 * across the frontend application.
 */

/**
 * File progress information for a single PDF file
 */
export interface FileProgress {
  name: string;
  fileId?: string;
  totalPages: number;
  currentPage: number;
  regexMatchesFound: number;
  startedAt: string;
  completedAt?: string;
  percentage?: number;
}

/**
 * Error context information when processing fails
 */
export interface ErrorContext {
  type: string;
  message: string;
  context: {
    phase?: string;
    file?: string;
    page?: number;
    sessionId?: string;
    [key: string]: any;
  };
  timestamp: string;
  traceback?: string;
}

/**
 * Phase status type
 */
export type PhaseStatus = 'pending' | 'in_progress' | 'completed' | 'failed';

/**
 * Progress information for a single processing phase
 */
export interface PhaseProgress {
  status: PhaseStatus;
  percentage: number;
  startedAt?: string;
  completedAt?: string;

  // Upload phase specific
  filesUploaded?: number;
  bytesUploaded?: number;

  // Processing phase specific
  totalFiles?: number;
  currentFileIndex?: number;
  currentFile?: FileProgress;

  // Matching phase specific
  matchesFound?: number;
  unmatchedCount?: number;

  // Report generation specific
  reportType?: string;
  recordsWritten?: number;
}

/**
 * Complete progress response from the API
 */
export interface ProgressResponse {
  sessionId: string;
  overallPercentage: number;
  currentPhase: string;
  phases: Record<string, PhaseProgress>;
  lastUpdate: string;
  statusMessage: string;
  error?: ErrorContext;
}

/**
 * Progress state for useProgress hook
 */
export interface ProgressState {
  sessionId: string;
  overall: {
    percentage: number;
    phase: string;
  };
  phases: Record<string, PhaseProgress>;
  statusMessage: string;
  lastUpdate: string | null;
  error: ErrorContext | null;
  isLoading: boolean;
  connectionState: 'connecting' | 'connected' | 'disconnected' | 'error';
}

/**
 * Actions for progress state reducer
 */
export type ProgressAction =
  | { type: 'SET_PROGRESS'; payload: ProgressResponse }
  | { type: 'SET_CONNECTION_STATE'; payload: ProgressState['connectionState'] }
  | { type: 'SET_ERROR'; payload: ErrorContext }
  | { type: 'CLEAR_ERROR' }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'RESET' };

/**
 * SSE event types
 */
export type SSEEventType = 'progress' | 'heartbeat' | 'complete' | 'error';

/**
 * SSE event data structure
 */
export interface SSEEvent {
  event: SSEEventType;
  data: any;
}

/**
 * Progress summary for list views
 */
export interface ProgressSummary {
  sessionId: string;
  currentPhase: string;
  overallPercentage: number;
  status: string;
  lastUpdate: string;
}

/**
 * Phase names enum for consistency
 */
export enum PhaseName {
  UPLOAD = 'upload',
  PROCESSING = 'processing',
  MATCHING = 'matching',
  REPORT_GENERATION = 'report_generation',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

/**
 * Phase configuration for UI display
 */
export interface PhaseConfig {
  name: PhaseName;
  label: string;
  description: string;
  icon?: string;
  color?: string;
}

/**
 * Default phase configurations
 */
export const PHASE_CONFIGS: PhaseConfig[] = [
  {
    name: PhaseName.UPLOAD,
    label: 'Upload',
    description: 'Uploading PDF files',
    color: '#3B82F6' // blue
  },
  {
    name: PhaseName.PROCESSING,
    label: 'Processing',
    description: 'Extracting data from PDFs',
    color: '#F59E0B' // amber
  },
  {
    name: PhaseName.MATCHING,
    label: 'Matching',
    description: 'Matching transactions to receipts',
    color: '#8B5CF6' // violet
  },
  {
    name: PhaseName.REPORT_GENERATION,
    label: 'Report',
    description: 'Generating reconciliation report',
    color: '#10B981' // emerald
  }
];