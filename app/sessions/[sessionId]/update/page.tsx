/**
 * Receipt Update Page - Dedicated Receipt Upload Interface
 *
 * Provides dedicated page for receipt updates according to
 * specs/003-add-ui-components/quickstart.md - Scenario 3
 */

import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import ReceiptUpdateView from './receipt-update-view';

interface ReceiptUpdatePageProps {
  params: {
    sessionId: string;
  };
}

export async function generateMetadata({ params }: ReceiptUpdatePageProps): Promise<Metadata> {
  return {
    title: `Update Receipts - ${params.sessionId}`,
    description: 'Upload additional expense reports to update session processing',
  };
}

export default function ReceiptUpdatePage({ params }: ReceiptUpdatePageProps) {
  const { sessionId } = params;

  // Validate sessionId format (should be UUID)
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  if (!uuidRegex.test(sessionId)) {
    notFound();
  }

  return <ReceiptUpdateView sessionId={sessionId} />;
}