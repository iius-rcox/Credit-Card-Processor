'use client';

/**
 * SessionDetailsView - Session Details Interface
 *
 * Client component for session details, reports, and management
 */

import React, { useState } from 'react';
import Link from 'next/link';
import { useSession } from '@/components/session-management/session-provider';
import { formatSessionDate, formatSessionStatus, getSessionStatusColor, getTimeUntilExpiration } from '@/lib/session-utils';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';

import {
  ArrowLeft,
  Edit3,
  Upload,
  Download,
  Trash2,
  RefreshCw,
  Calendar,
  Clock,
  FileText,
  Users,
  CheckCircle,
  XCircle,
  Loader,
  AlertTriangle,
  Settings,
} from 'lucide-react';

import SessionRenamer from '@/components/session-management/session-renamer';
import ReceiptUpdater from '@/components/session-management/receipt-updater';

interface SessionDetailsViewProps {
  sessionId: string;
}

export default function SessionDetailsView({ sessionId }: SessionDetailsViewProps) {
  const { storage, deleteSession, downloadReports, isLoading } = useSession();
  const [showRenamer, setShowRenamer] = useState(false);
  const [showUpdater, setShowUpdater] = useState(false);

  // Get session data
  const session = storage.sessions[sessionId];

  // Handle session not found
  if (!session) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Alert className="border-red-200 bg-red-50">
            <XCircle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">
              Session not found. It may have been deleted or expired.
            </AlertDescription>
          </Alert>
          <div className="mt-6">
            <Link href="/sessions">
              <Button variant="outline" className="flex items-center gap-2">
                <ArrowLeft className="h-4 w-4" />
                Back to Sessions
              </Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Get status styling and expiration info
  const statusColor = getSessionStatusColor(session.status);
  const statusText = formatSessionStatus(session.status);
  const expirationInfo = getTimeUntilExpiration(session);

  // Handle actions
  const handleDelete = async () => {
    if (window.confirm(`Are you sure you want to delete "${session.name}"? This action cannot be undone.`)) {
      try {
        await deleteSession(sessionId);
        window.location.href = '/sessions';
      } catch (error) {
        console.error('Failed to delete session:', error);
      }
    }
  };

  const handleDownload = async (format: 'excel' | 'csv') => {
    try {
      await downloadReports(sessionId, format);
    } catch (error) {
      console.error(`Failed to download ${format} report:`, error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Header */}
      <div className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Link href="/sessions">
                <Button variant="ghost" size="sm" className="mr-4">
                  <ArrowLeft className="h-4 w-4" />
                </Button>
              </Link>
              <h1 className="text-xl font-semibold text-gray-900">
                Session Details
              </h1>
            </div>
            <nav className="flex space-x-4">
              <Link href="/" className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
                Process Expenses
              </Link>
              <Link href="/sessions" className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">
                All Sessions
              </Link>
            </nav>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Session Header */}
        <div className="mb-8">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{session.name}</h1>
              <div className="flex items-center gap-2 mt-2">
                {session.status === 'Processing' && <Loader className="h-4 w-4 animate-spin text-blue-500" />}
                {session.status === 'Complete' && <CheckCircle className="h-4 w-4 text-green-500" />}
                {session.status === 'Updated' && <CheckCircle className="h-4 w-4 text-amber-500" />}
                {session.status === 'Error' && <XCircle className="h-4 w-4 text-red-500" />}
                <span className={`text-sm font-medium text-${statusColor}-600`}>
                  {statusText}
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowRenamer(true)}
                disabled={isLoading}
                className="flex items-center gap-2"
              >
                <Edit3 className="h-4 w-4" />
                Rename
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowUpdater(true)}
                disabled={isLoading}
                className="flex items-center gap-2"
              >
                <Upload className="h-4 w-4" />
                Update Receipts
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleDelete}
                disabled={isLoading}
                className="flex items-center gap-2 hover:text-red-600"
              >
                <Trash2 className="h-4 w-4" />
                Delete
              </Button>
            </div>
          </div>
        </div>

        {/* Alerts */}
        {expirationInfo.expired && (
          <Alert className="mb-6 border-red-200 bg-red-50">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">
              This session has expired and will be automatically cleaned up.
            </AlertDescription>
          </Alert>
        )}

        {!expirationInfo.expired && expirationInfo.days < 30 && (
          <Alert className="mb-6 border-amber-200 bg-amber-50">
            <AlertTriangle className="h-4 w-4 text-amber-600" />
            <AlertDescription className="text-amber-800">
              Session expires in {expirationInfo.days} days.
            </AlertDescription>
          </Alert>
        )}

        {session.status === 'Error' && session.errorMessage && (
          <Alert className="mb-6 border-red-200 bg-red-50">
            <XCircle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">
              {session.errorMessage}
            </AlertDescription>
          </Alert>
        )}

        {/* Session Information */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5 text-blue-600" />
                Timeline
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <p className="text-sm text-gray-600">Created</p>
                <p className="font-medium">{formatSessionDate(session.createdAt)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Last Updated</p>
                <p className="font-medium">{formatSessionDate(session.lastUpdated)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Expires</p>
                <p className="font-medium">{formatSessionDate(session.expiresAt)}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-blue-600" />
                Processing
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <p className="text-sm text-gray-600">Files Processed</p>
                <p className="font-medium text-2xl">{session.fileCount}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Expense Matches</p>
                <p className="font-medium text-2xl">{session.matchCount}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Status</p>
                <p className={`font-medium text-${statusColor}-600`}>{statusText}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5 text-blue-600" />
                System
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <p className="text-sm text-gray-600">Session ID</p>
                <p className="font-mono text-xs text-gray-500 break-all">{session.id}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Backend Session</p>
                <p className="font-mono text-xs text-gray-500 break-all">{session.backendSessionId}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Reports Available</p>
                <p className="font-medium">{session.hasReports ? 'Yes' : 'No'}</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Reports Section */}
        {session.hasReports && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Download className="h-5 w-5 text-blue-600" />
                Reports & Downloads
              </CardTitle>
              <CardDescription>
                Download expense reports and export data for this session
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 border rounded-lg">
                  <h3 className="font-medium mb-2">Excel Report</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    Comprehensive expense report with all transaction details
                  </p>
                  <Button
                    onClick={() => handleDownload('excel')}
                    disabled={isLoading}
                    className="w-full flex items-center gap-2"
                  >
                    <Download className="h-4 w-4" />
                    Download Excel
                  </Button>
                </div>
                <div className="p-4 border rounded-lg">
                  <h3 className="font-medium mb-2">CSV Export</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    Raw data export for analysis in other tools
                  </p>
                  <Button
                    variant="outline"
                    onClick={() => handleDownload('csv')}
                    disabled={isLoading}
                    className="w-full flex items-center gap-2"
                  >
                    <Download className="h-4 w-4" />
                    Download CSV
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Actions */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <RefreshCw className="h-5 w-5 text-blue-600" />
              Session Actions
            </CardTitle>
            <CardDescription>
              Manage and update this session
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Button
                variant="outline"
                onClick={() => setShowUpdater(true)}
                disabled={isLoading}
                className="flex items-center gap-2"
              >
                <Upload className="h-4 w-4" />
                Update Receipts
              </Button>
              <Link href={`/sessions/${sessionId}/update`}>
                <Button
                  variant="outline"
                  disabled={isLoading}
                  className="w-full flex items-center gap-2"
                >
                  <Upload className="h-4 w-4" />
                  Receipt Update Page
                </Button>
              </Link>
              <Button
                variant="outline"
                onClick={() => setShowRenamer(true)}
                disabled={isLoading}
                className="flex items-center gap-2"
              >
                <Edit3 className="h-4 w-4" />
                Rename Session
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Dialogs */}
      <SessionRenamer
        sessionId={showRenamer ? sessionId : null}
        isOpen={showRenamer}
        onClose={() => setShowRenamer(false)}
        onRenamed={() => setShowRenamer(false)}
      />

      <ReceiptUpdater
        sessionId={showUpdater ? sessionId : null}
        isOpen={showUpdater}
        onClose={() => setShowUpdater(false)}
        onUpdated={() => setShowUpdater(false)}
      />
    </div>
  );
}