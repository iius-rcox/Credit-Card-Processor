/**
 * Sessions Page - Main Session Management Interface
 *
 * Provides the main session management interface with browser,
 * creation, and management capabilities according to
 * specs/003-add-ui-components/plan.md
 */

import { Metadata } from 'next';
import SessionBrowser from '@/components/session-management/session-browser';

export const metadata: Metadata = {
  title: 'Session Management - Expense Reconciliation System',
  description: 'Manage your monthly expense processing sessions',
};

export default function SessionsPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">
                Expense Reconciliation System
              </h1>
            </div>
            <nav className="flex space-x-4">
              <a
                href="/"
                className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              >
                Process Expenses
              </a>
              <a
                href="/sessions"
                className="bg-blue-100 text-blue-700 px-3 py-2 rounded-md text-sm font-medium"
              >
                Session Management
              </a>
            </nav>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <SessionBrowser
          initialView="grid"
          showCreateButton={true}
          onSessionSelect={(sessionId) => {
            // Navigate to session details page
            window.location.href = `/sessions/${sessionId}`;
          }}
        />
      </div>

      {/* Footer */}
      <footer className="bg-white border-t mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="text-center text-sm text-gray-500">
            <p>
              Session Management System - Manage up to 24 concurrent expense processing sessions
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}