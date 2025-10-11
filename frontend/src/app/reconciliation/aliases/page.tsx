/**
 * Employee Name Aliases Page
 *
 * Page for managing employee name aliases used during PDF extraction.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { AliasManager } from '@/components/AliasManager';

/**
 * Aliases management page
 *
 * @returns JSX element for the aliases page
 */
export default function AliasesPage() {
  const [employees, setEmployees] = useState<Array<{ id: string; name: string; email?: string }>>([]);
  const [loading, setLoading] = useState(true);

  // Load employees from API
  useEffect(() => {
    loadEmployees();
  }, []);

  const loadEmployees = async () => {
    try {
      setLoading(true);

      // Fetch employees from API
      // For now, using mock data - real implementation would fetch from /api/employees
      // const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/employees`);
      // const data = await response.json();
      // setEmployees(data.employees || []);

      // Mock data for development
      setEmployees([
        { id: '123e4567-e89b-12d3-a456-426614174000', name: 'John Doe', email: 'john@example.com' },
        { id: '123e4567-e89b-12d3-a456-426614174001', name: 'Jane Smith', email: 'jane@example.com' },
        { id: '123e4567-e89b-12d3-a456-426614174002', name: 'Bob Johnson', email: 'bob@example.com' },
      ]);
    } catch (error) {
      console.error('Failed to load employees:', error);
      setEmployees([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="mb-6">
          <nav className="text-sm text-gray-500 dark:text-gray-400 mb-2">
            <a href="/" className="hover:text-gray-700 dark:hover:text-gray-200">
              Home
            </a>
            {' / '}
            <span className="text-gray-900 dark:text-gray-100">Employee Aliases</span>
          </nav>
        </div>

        {/* Alias Manager Component */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">Loading...</p>
          </div>
        ) : (
          <AliasManager
            employees={employees}
            onAliasCreated={(alias) => {
              console.log('Alias created:', alias);
            }}
            onAliasDeleted={(aliasId) => {
              console.log('Alias deleted:', aliasId);
            }}
          />
        )}
      </div>
    </div>
  );
}
