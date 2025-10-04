'use client';

/**
 * SessionCard - Individual Session Display Component
 *
 * Displays session information in card format with actions
 * according to specs/003-add-ui-components/plan.md
 */

import React, { useState } from 'react';
import { MonthSession } from '@/lib/session-types';
import { formatSessionDate, formatSessionStatus, getSessionStatusColor, getTimeUntilExpiration } from '@/lib/session-utils';
import { useSession } from './session-provider';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';

import {
  Edit3,
  Trash2,
  Download,
  FileText,
  Users,
  Calendar,
  Clock,
  AlertTriangle,
  CheckCircle,
  Loader,
  XCircle,
} from 'lucide-react';

interface SessionCardProps {
  session: MonthSession;
  onRename?: (sessionId: string) => void;
  onDelete?: (sessionId: string) => void;
  onDownloadReports?: (sessionId: string, format: 'excel' | 'csv') => void;
  onSelect?: (sessionId: string) => void;
  isActive?: boolean;
  showActions?: boolean;
}

export function SessionCard({
  session,
  onRename,
  onDelete,
  onDownloadReports,
  onSelect,
  isActive = false,
  showActions = true,
}: SessionCardProps) {
  const { setActiveSession, isLoading } = useSession();
  const [isExpanded, setIsExpanded] = useState(false);

  // Get status styling
  const statusColor = getSessionStatusColor(session.status);
  const statusText = formatSessionStatus(session.status);

  // Get expiration info
  const expirationInfo = getTimeUntilExpiration(session);

  // Handle card click
  const handleCardClick = () => {
    if (onSelect) {
      onSelect(session.id);
    } else {
      setActiveSession(session.id);
    }
  };

  // Status icon
  const getStatusIcon = () => {
    switch (session.status) {
      case 'Processing':
        return <Loader className="h-4 w-4 animate-spin text-blue-500" />;
      case 'Complete':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'Updated':
        return <CheckCircle className="h-4 w-4 text-amber-500" />;
      case 'Error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  // Action buttons
  const handleRename = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onRename) {
      onRename(session.id);
    }
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDelete) {
      onDelete(session.id);
    }
  };

  const handleDownload = (e: React.MouseEvent, format: 'excel' | 'csv') => {
    e.stopPropagation();
    if (onDownloadReports) {
      onDownloadReports(session.id, format);
    }
  };

  return (
    <Card
      className={`cursor-pointer transition-all duration-200 hover:shadow-md ${
        isActive ? 'ring-2 ring-blue-500 bg-blue-50' : 'hover:bg-gray-50'
      } ${isLoading ? 'opacity-50' : ''}`}
      onClick={handleCardClick}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-lg font-semibold truncate">
              {session.name}
            </CardTitle>
            <CardDescription className="flex items-center gap-2 mt-1">
              {getStatusIcon()}
              <span className={`text-sm font-medium text-${statusColor}-600`}>
                {statusText}
              </span>
            </CardDescription>
          </div>

          {showActions && (
            <div className="flex items-center gap-1 ml-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleRename}
                disabled={isLoading}
                className="h-8 w-8 p-0"
                title="Rename session"
              >
                <Edit3 className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleDelete}
                disabled={isLoading}
                className="h-8 w-8 p-0 hover:text-red-600"
                title="Delete session"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        {/* Session Metadata */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-gray-500" />
            <span className="text-gray-600">Created:</span>
            <span className="font-medium">{formatSessionDate(session.createdAt)}</span>
          </div>

          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-gray-500" />
            <span className="text-gray-600">Updated:</span>
            <span className="font-medium">{formatSessionDate(session.lastUpdated)}</span>
          </div>

          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-gray-500" />
            <span className="text-gray-600">Files:</span>
            <span className="font-medium">{session.fileCount}</span>
          </div>

          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-gray-500" />
            <span className="text-gray-600">Matches:</span>
            <span className="font-medium">{session.matchCount}</span>
          </div>
        </div>

        {/* Expiration Warning */}
        {expirationInfo.expired && (
          <Alert className="mt-3 border-red-200 bg-red-50">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">
              This session has expired and will be automatically cleaned up.
            </AlertDescription>
          </Alert>
        )}

        {/* Near Expiration Warning */}
        {!expirationInfo.expired && expirationInfo.days < 30 && (
          <Alert className="mt-3 border-amber-200 bg-amber-50">
            <AlertTriangle className="h-4 w-4 text-amber-600" />
            <AlertDescription className="text-amber-800">
              Session expires in {expirationInfo.days} days.
            </AlertDescription>
          </Alert>
        )}

        {/* Error Message */}
        {session.status === 'Error' && session.errorMessage && (
          <Alert className="mt-3 border-red-200 bg-red-50">
            <XCircle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">
              {session.errorMessage}
            </AlertDescription>
          </Alert>
        )}

        {/* Reports Section */}
        {session.hasReports && (
          <div className="mt-4 pt-3 border-t">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">Reports Available</span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={(e) => handleDownload(e, 'excel')}
                  disabled={isLoading}
                  className="text-xs"
                >
                  <Download className="h-3 w-3 mr-1" />
                  Excel
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={(e) => handleDownload(e, 'csv')}
                  disabled={isLoading}
                  className="text-xs"
                >
                  <Download className="h-3 w-3 mr-1" />
                  CSV
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Expand/Collapse for Additional Details */}
        {(session.status === 'Processing' || session.status === 'Updated') && (
          <div className="mt-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                setIsExpanded(!isExpanded);
              }}
              className="text-xs text-gray-600 hover:text-gray-800"
            >
              {isExpanded ? 'Show Less' : 'Show Details'}
            </Button>

            {isExpanded && (
              <div className="mt-2 p-3 bg-gray-50 rounded-md text-sm">
                <div className="space-y-1">
                  <div>
                    <span className="font-medium">Backend Session ID:</span>
                    <span className="ml-2 font-mono text-xs text-gray-600">
                      {session.backendSessionId}
                    </span>
                  </div>
                  <div>
                    <span className="font-medium">Expires:</span>
                    <span className="ml-2 text-gray-600">
                      {formatSessionDate(session.expiresAt)}
                    </span>
                  </div>
                  {!expirationInfo.expired && (
                    <div>
                      <span className="font-medium">Time Remaining:</span>
                      <span className="ml-2 text-gray-600">
                        {expirationInfo.days} days, {expirationInfo.hours} hours
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Active Session Indicator */}
        {isActive && (
          <div className="mt-3 pt-3 border-t">
            <div className="flex items-center gap-2 text-sm text-blue-600">
              <div className="h-2 w-2 bg-blue-500 rounded-full animate-pulse" />
              <span className="font-medium">Active Session</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default SessionCard;