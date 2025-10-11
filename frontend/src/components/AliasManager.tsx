/**
 * AliasManager component for managing employee name aliases.
 *
 * Allows users to create, view, and delete mappings between extracted
 * employee names from PDFs and actual employee records.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Trash2, Plus, User, AlertCircle, CheckCircle } from 'lucide-react';
import {
  createAlias,
  deleteAlias,
  getAliases,
  type EmployeeAlias,
} from '@/services/aliasService';

export interface AliasManagerProps {
  employees?: Array<{ id: string; name: string; email?: string }>;
  onAliasCreated?: (alias: EmployeeAlias) => void;
  onAliasDeleted?: (aliasId: string) => void;
}

/**
 * AliasManager component
 *
 * @param props - Component props
 * @returns JSX element for alias management
 */
export function AliasManager({
  employees = [],
  onAliasCreated,
  onAliasDeleted,
}: AliasManagerProps) {
  const [aliases, setAliases] = useState<EmployeeAlias[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Form state
  const [extractedName, setExtractedName] = useState('');
  const [selectedEmployeeId, setSelectedEmployeeId] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Load aliases on mount
  useEffect(() => {
    loadAliases();
  }, []);

  /**
   * Load all aliases from API
   */
  const loadAliases = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getAliases();
      setAliases(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load aliases');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle alias creation form submission
   */
  const handleCreateAlias = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!extractedName.trim() || !selectedEmployeeId) {
      setError('Please fill in all fields');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      setSuccessMessage(null);

      const newAlias = await createAlias(extractedName.trim(), selectedEmployeeId);

      // Add to list
      setAliases((prev) => [...prev, newAlias]);

      // Reset form
      setExtractedName('');
      setSelectedEmployeeId('');

      setSuccessMessage(`Alias "${extractedName}" created successfully`);

      // Call callback if provided
      if (onAliasCreated) {
        onAliasCreated(newAlias);
      }

      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create alias');
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Handle alias deletion
   */
  const handleDeleteAlias = async (aliasId: string, aliasName: string) => {
    if (!confirm(`Are you sure you want to delete the alias "${aliasName}"?`)) {
      return;
    }

    try {
      setError(null);
      await deleteAlias(aliasId);

      // Remove from list
      setAliases((prev) => prev.filter((a) => a.id !== aliasId));

      setSuccessMessage(`Alias "${aliasName}" deleted successfully`);

      // Call callback if provided
      if (onAliasDeleted) {
        onAliasDeleted(aliasId);
      }

      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete alias');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Employee Name Aliases
        </h2>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Map employee names as they appear in PDFs to existing employee records
        </p>
      </div>

      {/* Error/Success Messages */}
      {error && (
        <div className="flex items-start gap-3 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-red-800 dark:text-red-200">Error</p>
            <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
          </div>
          <button
            onClick={() => setError(null)}
            className="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200"
          >
            ×
          </button>
        </div>
      )}

      {successMessage && (
        <div className="flex items-start gap-3 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
          <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-green-800 dark:text-green-200">Success</p>
            <p className="text-sm text-green-700 dark:text-green-300">{successMessage}</p>
          </div>
        </div>
      )}

      {/* Create Alias Form */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Create New Alias
        </h3>

        <form onSubmit={handleCreateAlias} className="space-y-4">
          <div>
            <label
              htmlFor="extractedName"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              Name from PDF <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="extractedName"
              value={extractedName}
              onChange={(e) => setExtractedName(e.target.value)}
              placeholder="e.g., JOHNSMITH"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100
                       focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Enter the employee name exactly as it appears in the PDF
            </p>
          </div>

          <div>
            <label
              htmlFor="employeeId"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              Map to Employee <span className="text-red-500">*</span>
            </label>
            <select
              id="employeeId"
              value={selectedEmployeeId}
              onChange={(e) => setSelectedEmployeeId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100
                       focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            >
              <option value="">Select an employee...</option>
              {employees.map((emp) => (
                <option key={emp.id} value={emp.id}>
                  {emp.name} {emp.email ? `(${emp.email})` : ''}
                </option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            disabled={submitting || !extractedName.trim() || !selectedEmployeeId}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md
                     hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed
                     transition-colors"
          >
            <Plus className="w-4 h-4" />
            {submitting ? 'Creating...' : 'Create Alias'}
          </button>
        </form>
      </div>

      {/* Aliases Table */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Existing Aliases ({aliases.length})
          </h3>
        </div>

        {loading ? (
          <div className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
            <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-2"></div>
            <p className="text-sm">Loading aliases...</p>
          </div>
        ) : aliases.length === 0 ? (
          <div className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
            <User className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No aliases created yet</p>
            <p className="text-xs mt-1">Create an alias above to get started</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    PDF Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Mapped Employee
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {aliases.map((alias) => (
                  <tr
                    key={alias.id}
                    className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <User className="w-4 h-4 text-gray-400" />
                        <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {alias.extractedName}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900 dark:text-gray-100">
                        {alias.employee?.name || 'Unknown'}
                      </div>
                      {alias.employee?.email && (
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          {alias.employee.email}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {new Date(alias.createdAt).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <button
                        onClick={() => handleDeleteAlias(alias.id, alias.extractedName)}
                        className="inline-flex items-center gap-1 px-3 py-1 text-sm text-red-600 dark:text-red-400
                                 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md transition-colors"
                        title="Delete alias"
                      >
                        <Trash2 className="w-4 h-4" />
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
