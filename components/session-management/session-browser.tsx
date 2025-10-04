'use client';

/**
 * SessionBrowser - Main Session Management Container
 *
 * Provides comprehensive session browsing interface with filtering,
 * search, and management capabilities according to
 * specs/003-add-ui-components/data-model.md
 */

import React, { useState, useMemo, useCallback, useRef, useEffect } from 'react';
import { useSession } from './session-provider';
import { SessionFilter, DEFAULT_SESSION_FILTER, SESSION_CONSTRAINTS } from '@/lib/session-types';
import { isApproachingSessionLimit, isAtSessionLimit, getTimeUntilExpiration } from '@/lib/session-utils';

import SessionCard from './session-card';
import SessionCreator from './session-creator';
import SessionRenamer from './session-renamer';
import ReceiptUpdater from './receipt-updater';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';

import {
  Search,
  Filter,
  Grid,
  List,
  Plus,
  AlertTriangle,
  Trash2,
  Settings,
  Download,
  RefreshCw,
  Users,
  Calendar,
  Clock,
  CheckCircle,
  XCircle,
  Loader,
} from 'lucide-react';

interface SessionBrowserProps {
  initialView?: 'grid' | 'list';
  showCreateButton?: boolean;
  onSessionSelect?: (sessionId: string) => void;
}

// Custom hook for debounced search
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

// Memoized SessionCard component to prevent unnecessary re-renders
const MemoizedSessionCard = React.memo(SessionCard, (prevProps, nextProps) => {
  // Custom comparison function for optimal re-rendering
  return (
    prevProps.session.id === nextProps.session.id &&
    prevProps.session.lastUpdated === nextProps.session.lastUpdated &&
    prevProps.session.status === nextProps.session.status &&
    prevProps.session.name === nextProps.session.name &&
    prevProps.session.hasReports === nextProps.session.hasReports &&
    prevProps.session.fileCount === nextProps.session.fileCount &&
    prevProps.session.matchCount === nextProps.session.matchCount &&
    prevProps.isActive === nextProps.isActive
  );
});

export const SessionBrowser = React.memo(function SessionBrowser({
  initialView = 'grid',
  showCreateButton = true,
  onSessionSelect,
}: SessionBrowserProps) {
  const {
    storage,
    activeSession,
    filteredSessions,
    isLoading,
    error,
    setFilter,
    clearFilter,
    deleteSession,
  } = useSession();

  // Component state
  const [viewMode, setViewMode] = useState<'grid' | 'list'>(initialView);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'Processing' | 'Complete' | 'Updated' | 'Error'>('all');
  const [sortBy, setSortBy] = useState<'name' | 'createdAt' | 'lastUpdated'>('lastUpdated');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [showFilters, setShowFilters] = useState(false);

  // Debounced search term to reduce filtering frequency
  const debouncedSearchTerm = useDebounce(searchTerm, 300);

  // Dialog states
  const [isCreatorOpen, setIsCreatorOpen] = useState(false);
  const [renamerSessionId, setRenamerSessionId] = useState<string | null>(null);
  const [updaterSessionId, setUpdaterSessionId] = useState<string | null>(null);

  // Statistics
  const sessionStats = useMemo(() => {
    const allSessions = Object.values(storage.sessions);
    return {
      total: allSessions.length,
      processing: allSessions.filter(s => s.status === 'Processing').length,
      complete: allSessions.filter(s => s.status === 'Complete').length,
      updated: allSessions.filter(s => s.status === 'Updated').length,
      error: allSessions.filter(s => s.status === 'Error').length,
      withReports: allSessions.filter(s => s.hasReports).length,
      expiring: allSessions.filter(s => {
        const timeLeft = getTimeUntilExpiration(s);
        return !timeLeft.expired && timeLeft.days < 30;
      }).length,
    };
  }, [storage.sessions]);

  // Update filters when debounced values change (performance optimization)
  useEffect(() => {
    const filter: SessionFilter = {
      searchTerm: debouncedSearchTerm,
      statusFilter: statusFilter === 'all' ? 'all' : [statusFilter],
      dateRange: {},
      sortBy,
      sortOrder,
    };
    setFilter(filter);
  }, [debouncedSearchTerm, statusFilter, sortBy, sortOrder, setFilter]);

  // Memoized event handlers for performance
  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  }, []);

  const handleClearFilters = useCallback(() => {
    setSearchTerm('');
    setStatusFilter('all');
    setSortBy('lastUpdated');
    setSortOrder('desc');
    clearFilter();
  }, [clearFilter]);

  const handleSessionSelect = useCallback((sessionId: string) => {
    if (onSessionSelect) {
      onSessionSelect(sessionId);
    }
  }, [onSessionSelect]);

  const handleSessionRename = useCallback((sessionId: string) => {
    setRenamerSessionId(sessionId);
  }, []);

  const handleSessionDelete = useCallback(async (sessionId: string) => {
    const session = storage.sessions[sessionId];
    if (session && window.confirm(`Are you sure you want to delete "${session.name}"?`)) {
      try {
        await deleteSession(sessionId);
      } catch (error) {
        console.error('Failed to delete session:', error);
      }
    }
  }, [storage.sessions, deleteSession]);

  const handleUpdateReceipts = useCallback((sessionId: string) => {
    setUpdaterSessionId(sessionId);
  }, []);

  const handleDownloadReports = useCallback(async (sessionId: string, format: 'excel' | 'csv') => {
    // This will be implemented in Phase 3.4 Integration
    console.log(`Download ${format} report for session ${sessionId}`);
  }, []);

  // Memoized storage limit checks for performance
  const { approachingLimit, atLimit } = useMemo(() => ({
    approachingLimit: isApproachingSessionLimit(storage),
    atLimit: isAtSessionLimit(storage),
  }), [storage]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Session Management</h1>
          <p className="text-gray-600">
            Manage your monthly expense processing sessions
          </p>
        </div>

        {showCreateButton && (
          <SessionCreator
            isOpen={isCreatorOpen}
            onSessionCreated={() => setIsCreatorOpen(false)}
            onCancel={() => setIsCreatorOpen(false)}
            trigger={
              <Button
                onClick={() => setIsCreatorOpen(true)}
                disabled={atLimit || isLoading}
                className="flex items-center gap-2"
              >
                <Plus className="h-4 w-4" />
                Create Session
              </Button>
            }
          />
        )}
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-blue-600" />
              <div>
                <p className="text-sm text-gray-600">Total</p>
                <p className="text-lg font-semibold">{sessionStats.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Loader className="h-4 w-4 text-blue-600" />
              <div>
                <p className="text-sm text-gray-600">Processing</p>
                <p className="text-lg font-semibold">{sessionStats.processing}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <div>
                <p className="text-sm text-gray-600">Complete</p>
                <p className="text-lg font-semibold">{sessionStats.complete}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <RefreshCw className="h-4 w-4 text-amber-600" />
              <div>
                <p className="text-sm text-gray-600">Updated</p>
                <p className="text-lg font-semibold">{sessionStats.updated}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <XCircle className="h-4 w-4 text-red-600" />
              <div>
                <p className="text-sm text-gray-600">Errors</p>
                <p className="text-lg font-semibold">{sessionStats.error}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Download className="h-4 w-4 text-purple-600" />
              <div>
                <p className="text-sm text-gray-600">Reports</p>
                <p className="text-lg font-semibold">{sessionStats.withReports}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-orange-600" />
              <div>
                <p className="text-sm text-gray-600">Expiring</p>
                <p className="text-lg font-semibold">{sessionStats.expiring}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Alerts */}
      {atLimit && (
        <Alert className="border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            You've reached the maximum of {SESSION_CONSTRAINTS.MAX_SESSIONS} sessions.
            Please delete old sessions to create new ones.
          </AlertDescription>
        </Alert>
      )}

      {approachingLimit && !atLimit && (
        <Alert className="border-amber-200 bg-amber-50">
          <AlertTriangle className="h-4 w-4 text-amber-600" />
          <AlertDescription className="text-amber-800">
            You're approaching the session limit ({sessionStats.total}/{SESSION_CONSTRAINTS.MAX_SESSIONS}).
            Consider deleting old sessions.
          </AlertDescription>
        </Alert>
      )}

      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            {error}
          </AlertDescription>
        </Alert>
      )}

      {/* Search and Filters */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Browse Sessions</CardTitle>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowFilters(!showFilters)}
                className="flex items-center gap-2"
              >
                <Filter className="h-4 w-4" />
                Filters
              </Button>
              <div className="flex items-center border rounded-md">
                <Button
                  variant={viewMode === 'grid' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setViewMode('grid')}
                  className="rounded-r-none"
                >
                  <Grid className="h-4 w-4" />
                </Button>
                <Button
                  variant={viewMode === 'list' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setViewMode('list')}
                  className="rounded-l-none"
                >
                  <List className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              type="text"
              placeholder="Search sessions..."
              value={searchTerm}
              onChange={handleSearchChange}
              className="pl-10"
            />
          </div>

          {/* Advanced Filters */}
          {showFilters && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
              <div className="space-y-2">
                <Label htmlFor="status-filter" className="text-sm font-medium">
                  Status
                </Label>
                <select
                  id="status-filter"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as any)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="all">All Statuses</option>
                  <option value="Processing">Processing</option>
                  <option value="Complete">Complete</option>
                  <option value="Updated">Updated</option>
                  <option value="Error">Error</option>
                </select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="sort-by" className="text-sm font-medium">
                  Sort By
                </Label>
                <select
                  id="sort-by"
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="lastUpdated">Last Updated</option>
                  <option value="createdAt">Created Date</option>
                  <option value="name">Name</option>
                </select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="sort-order" className="text-sm font-medium">
                  Order
                </Label>
                <select
                  id="sort-order"
                  value={sortOrder}
                  onChange={(e) => setSortOrder(e.target.value as any)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="desc">Newest First</option>
                  <option value="asc">Oldest First</option>
                </select>
              </div>

              <div className="md:col-span-3 flex justify-end">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleClearFilters}
                  className="text-xs"
                >
                  Clear Filters
                </Button>
              </div>
            </div>
          )}

          {/* Results Summary */}
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>
              {filteredSessions.length} session{filteredSessions.length !== 1 ? 's' : ''} found
            </span>
            {(searchTerm || statusFilter !== 'all') && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClearFilters}
                className="text-xs"
              >
                Clear filters
              </Button>
            )}
          </div>

          {/* Session Grid/List */}
          {filteredSessions.length === 0 ? (
            <div className="text-center py-12">
              <Users className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No sessions found</h3>
              <p className="mt-1 text-sm text-gray-500">
                {searchTerm || statusFilter !== 'all'
                  ? 'Try adjusting your search or filters'
                  : 'Get started by creating your first session'}
              </p>
              {showCreateButton && !searchTerm && statusFilter === 'all' && (
                <div className="mt-6">
                  <Button
                    onClick={() => setIsCreatorOpen(true)}
                    disabled={atLimit}
                    className="flex items-center gap-2"
                  >
                    <Plus className="h-4 w-4" />
                    Create Your First Session
                  </Button>
                </div>
              )}
            </div>
          ) : (
            <div
              className={
                viewMode === 'grid'
                  ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'
                  : 'space-y-3'
              }
            >
              {filteredSessions.map((session) => (
                <MemoizedSessionCard
                  key={session.id}
                  session={session}
                  isActive={activeSession?.id === session.id}
                  onSelect={handleSessionSelect}
                  onRename={handleSessionRename}
                  onDelete={handleSessionDelete}
                  onDownloadReports={handleDownloadReports}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Dialogs */}
      <SessionRenamer
        sessionId={renamerSessionId}
        isOpen={!!renamerSessionId}
        onClose={() => setRenamerSessionId(null)}
        onRenamed={() => setRenamerSessionId(null)}
      />

      <ReceiptUpdater
        sessionId={updaterSessionId}
        isOpen={!!updaterSessionId}
        onClose={() => setUpdaterSessionId(null)}
        onUpdated={() => setUpdaterSessionId(null)}
      />
    </div>
  );
});

export default SessionBrowser;