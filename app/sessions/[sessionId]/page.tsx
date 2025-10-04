/**
 * Session Details Page - Individual Session Management
 *
 * Provides detailed view and management for a specific session
 * according to specs/003-add-ui-components/quickstart.md
 */

import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import SessionDetailsView from './session-details-view';

interface SessionPageProps {
  params: {
    sessionId: string;
  };
}

export async function generateMetadata({ params }: SessionPageProps): Promise<Metadata> {
  // In a real application, you would fetch session data here
  // For now, we'll use the sessionId directly
  return {
    title: `Session Details - ${params.sessionId}`,
    description: 'View and manage session details, reports, and receipts',
  };
}

export default function SessionPage({ params }: SessionPageProps) {
  const { sessionId } = params;

  // Validate sessionId format (should be UUID)
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  if (!uuidRegex.test(sessionId)) {
    notFound();
  }

  return <SessionDetailsView sessionId={sessionId} />;
}