/**
 * SessionBrowser Storybook Stories
 *
 * Visual documentation and testing for SessionBrowser component
 * according to specs/003-add-ui-components/plan.md
 */

import type { Meta, StoryObj } from '@storybook/react';
import { action } from '@storybook/addon-actions';
import { SessionBrowser } from '@/components/session-management/session-browser';
import { SessionProvider } from '@/components/session-management/session-provider';
import { MonthSession, SessionStorage, SessionStatus, SESSION_CONSTRAINTS } from '@/lib/session-types';

// Mock session data helper
const createMockSession = (overrides: Partial<MonthSession> = {}): MonthSession => {
  const statuses: SessionStatus[] = ['Processing', 'Complete', 'Updated', 'Error'];
  const randomStatus = statuses[Math.floor(Math.random() * statuses.length)];

  return {
    id: `session-${Math.random().toString(36).substr(2, 9)}`,
    name: `Session ${Math.floor(Math.random() * 100)}`,
    createdAt: Date.now() - (Math.random() * 60 * 24 * 60 * 60 * 1000), // Random date within 60 days
    expiresAt: Date.now() + (365 * 24 * 60 * 60 * 1000) - (Math.random() * 30 * 24 * 60 * 60 * 1000), // Varying expiration
    status: randomStatus,
    backendSessionId: `backend-${Math.random().toString(36).substr(2, 9)}`,
    lastUpdated: Date.now() - (Math.random() * 7 * 24 * 60 * 60 * 1000), // Random date within 7 days
    hasReports: Math.random() > 0.3, // 70% chance of having reports
    fileCount: Math.floor(Math.random() * 8) + 1,
    matchCount: Math.floor(Math.random() * 100),
    errorMessage: randomStatus === 'Error' ? 'Sample error message' : undefined,
    ...overrides,
  };
};

// Create realistic session names
const sessionNames = [
  'January 2024 Expenses',
  'February 2024 Processing',
  'Q1 2024 Corporate Cards',
  'March 2024 Travel Expenses',
  'April 2024 Office Supplies',
  'May 2024 Client Meetings',
  'June 2024 Project Alpha',
  'Q2 2024 Summary',
  'July 2024 Remote Work',
  'August 2024 Conference',
  'September 2024 Quarterly',
  'October 2024 Year End',
  'November 2024 Holidays',
  'December 2024 Final',
];

// Create mock storage with realistic data
const createMockStorage = (sessionCount: number): SessionStorage => {
  const sessions = Array.from({ length: sessionCount }, (_, i) => {
    const name = sessionNames[i % sessionNames.length];
    const uniqueName = sessionCount > sessionNames.length ? `${name} (${Math.floor(i / sessionNames.length) + 1})` : name;

    return createMockSession({
      id: `session-${i}`,
      name: uniqueName,
      createdAt: Date.now() - (i * 2 * 24 * 60 * 60 * 1000), // Spread over time
    });
  });

  return {
    sessions: sessions.reduce((acc, session) => {
      acc[session.id] = session;
      return acc;
    }, {} as Record<string, MonthSession>),
    activeSessionId: sessions.length > 0 ? sessions[0].id : null,
    lastCleanup: Date.now(),
    version: SESSION_CONSTRAINTS.SCHEMA_VERSION,
  };
};

// Custom SessionProvider wrapper for stories
const SessionProviderWrapper = ({
  children,
  initialSessionCount = 0
}: {
  children: React.ReactNode;
  initialSessionCount?: number;
}) => (
  <SessionProvider initialStorage={createMockStorage(initialSessionCount)}>
    <div className="min-h-screen bg-gray-50">
      {children}
    </div>
  </SessionProvider>
);

const meta = {
  title: 'Session Management/SessionBrowser',
  component: SessionBrowser,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: `
The SessionBrowser component provides a comprehensive interface for managing multiple expense processing sessions.

**Features:**
- Session grid and list view modes
- Real-time search and filtering
- Advanced filters (status, date range, sorting)
- Session statistics dashboard
- Session limit warnings
- Session creation integration
- Bulk operations
- Responsive design
- Accessibility support

**Key Components:**
- Statistics cards showing session counts by status
- Search bar with real-time filtering
- Advanced filter controls
- Session cards in grid or list layout
- Create session integration
- Action buttons for session management
        `,
      },
    },
  },
  argTypes: {
    initialView: {
      control: { type: 'radio' },
      options: ['grid', 'list'],
      description: 'Initial view mode for session display',
    },
    showCreateButton: {
      control: 'boolean',
      description: 'Whether to show the create session button',
    },
    onSessionSelect: {
      action: 'session-selected',
      description: 'Callback when a session is selected',
    },
  },
} satisfies Meta<typeof SessionBrowser>;

export default meta;
type Story = StoryObj<typeof meta>;

// Default story - medium dataset
export const Default: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper initialSessionCount={8}>
        <Story />
      </SessionProviderWrapper>
    ),
  ],
  args: {
    initialView: 'grid',
    showCreateButton: true,
    onSessionSelect: action('session-selected'),
  },
};

// Empty state
export const EmptyState: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper initialSessionCount={0}>
        <Story />
      </SessionProviderWrapper>
    ),
  ],
  args: {
    initialView: 'grid',
    showCreateButton: true,
    onSessionSelect: action('session-selected'),
  },
  parameters: {
    docs: {
      description: {
        story: 'SessionBrowser with no sessions - shows empty state with call to action.',
      },
    },
  },
};

// List view
export const ListView: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper initialSessionCount={6}>
        <Story />
      </SessionProviderWrapper>
    ),
  ],
  args: {
    initialView: 'list',
    showCreateButton: true,
    onSessionSelect: action('session-selected'),
  },
  parameters: {
    docs: {
      description: {
        story: 'SessionBrowser in list view mode for compact display.',
      },
    },
  },
};

// Large dataset
export const LargeDataset: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper initialSessionCount={20}>
        <Story />
      </SessionProviderWrapper>
    ),
  ],
  args: {
    initialView: 'grid',
    showCreateButton: true,
    onSessionSelect: action('session-selected'),
  },
  parameters: {
    docs: {
      description: {
        story: 'SessionBrowser with many sessions - shows performance and pagination.',
      },
    },
  },
};

// Approaching limit
export const ApproachingLimit: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper initialSessionCount={22}>
        <Story />
      </SessionProviderWrapper>
    ),
  ],
  args: {
    initialView: 'grid',
    showCreateButton: true,
    onSessionSelect: action('session-selected'),
  },
  parameters: {
    docs: {
      description: {
        story: 'SessionBrowser when approaching the 24 session limit - shows warning.',
      },
    },
  },
};

// At session limit
export const AtLimit: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper initialSessionCount={24}>
        <Story />
      </SessionProviderWrapper>
    ),
  ],
  args: {
    initialView: 'grid',
    showCreateButton: true,
    onSessionSelect: action('session-selected'),
  },
  parameters: {
    docs: {
      description: {
        story: 'SessionBrowser at maximum session limit - creation is disabled.',
      },
    },
  },
};

// No create button
export const ReadOnlyMode: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper initialSessionCount={12}>
        <Story />
      </SessionProviderWrapper>
    ),
  ],
  args: {
    initialView: 'grid',
    showCreateButton: false,
    onSessionSelect: action('session-selected'),
  },
  parameters: {
    docs: {
      description: {
        story: 'SessionBrowser in read-only mode without create session capability.',
      },
    },
  },
};

// Filter and search demo
export const FilterDemo: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper initialSessionCount={15}>
        <div className="space-y-4">
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-md">
            <h4 className="font-medium text-blue-800">🔍 Try These Filters:</h4>
            <ul className="text-sm text-blue-700 mt-2 space-y-1">
              <li>• Search: "January", "2024", "Project"</li>
              <li>• Filter by status: Processing, Complete, Error</li>
              <li>• Sort by: Name, Created Date, Last Updated</li>
              <li>• Toggle between Grid and List views</li>
            </ul>
          </div>
          <Story />
        </div>
      </SessionProviderWrapper>
    ),
  ],
  args: {
    initialView: 'grid',
    showCreateButton: true,
    onSessionSelect: action('session-selected'),
  },
  parameters: {
    docs: {
      description: {
        story: 'Interactive demo showing search and filter capabilities.',
      },
    },
  },
};

// All status types
export const AllStatusTypes: Story = {
  decorators: [
    (Story) => (
      <SessionProvider
        initialStorage={{
          sessions: {
            'session-1': createMockSession({
              id: 'session-1',
              name: 'Processing Session',
              status: 'Processing',
              hasReports: false,
              fileCount: 2,
              matchCount: 0,
            }),
            'session-2': createMockSession({
              id: 'session-2',
              name: 'Complete Session',
              status: 'Complete',
              hasReports: true,
              fileCount: 3,
              matchCount: 45,
            }),
            'session-3': createMockSession({
              id: 'session-3',
              name: 'Updated Session',
              status: 'Updated',
              hasReports: true,
              fileCount: 4,
              matchCount: 52,
            }),
            'session-4': createMockSession({
              id: 'session-4',
              name: 'Error Session',
              status: 'Error',
              hasReports: false,
              fileCount: 1,
              matchCount: 0,
              errorMessage: 'Failed to process expense report',
            }),
          },
          activeSessionId: 'session-2',
          lastCleanup: Date.now(),
          version: SESSION_CONSTRAINTS.SCHEMA_VERSION,
        }}
      >
        <div className="min-h-screen bg-gray-50">
          <Story />
        </div>
      </SessionProvider>
    ),
  ],
  args: {
    initialView: 'grid',
    showCreateButton: true,
    onSessionSelect: action('session-selected'),
  },
  parameters: {
    docs: {
      description: {
        story: 'SessionBrowser showing all possible session status types.',
      },
    },
  },
};

// Mobile responsive
export const MobileView: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper initialSessionCount={6}>
        <div className="max-w-sm mx-auto">
          <Story />
        </div>
      </SessionProviderWrapper>
    ),
  ],
  args: {
    initialView: 'list',
    showCreateButton: true,
    onSessionSelect: action('session-selected'),
  },
  parameters: {
    viewport: {
      defaultViewport: 'mobile1',
    },
    docs: {
      description: {
        story: 'SessionBrowser optimized for mobile viewport.',
      },
    },
  },
};

// Statistics showcase
export const StatisticsShowcase: Story = {
  decorators: [
    (Story) => (
      <SessionProvider
        initialStorage={{
          sessions: {
            ...Array.from({ length: 5 }, (_, i) => ({
              [`processing-${i}`]: createMockSession({
                id: `processing-${i}`,
                name: `Processing Session ${i + 1}`,
                status: 'Processing' as const,
                hasReports: false,
              }),
            })).reduce((acc, curr) => ({ ...acc, ...curr }), {}),
            ...Array.from({ length: 8 }, (_, i) => ({
              [`complete-${i}`]: createMockSession({
                id: `complete-${i}`,
                name: `Complete Session ${i + 1}`,
                status: 'Complete' as const,
                hasReports: true,
              }),
            })).reduce((acc, curr) => ({ ...acc, ...curr }), {}),
            ...Array.from({ length: 3 }, (_, i) => ({
              [`updated-${i}`]: createMockSession({
                id: `updated-${i}`,
                name: `Updated Session ${i + 1}`,
                status: 'Updated' as const,
                hasReports: true,
              }),
            })).reduce((acc, curr) => ({ ...acc, ...curr }), {}),
            ...Array.from({ length: 2 }, (_, i) => ({
              [`error-${i}`]: createMockSession({
                id: `error-${i}`,
                name: `Error Session ${i + 1}`,
                status: 'Error' as const,
                hasReports: false,
                errorMessage: 'Processing failed',
              }),
            })).reduce((acc, curr) => ({ ...acc, ...curr }), {}),
          },
          activeSessionId: 'complete-0',
          lastCleanup: Date.now(),
          version: SESSION_CONSTRAINTS.SCHEMA_VERSION,
        }}
      >
        <div className="min-h-screen bg-gray-50">
          <Story />
        </div>
      </SessionProvider>
    ),
  ],
  args: {
    initialView: 'grid',
    showCreateButton: true,
    onSessionSelect: action('session-selected'),
  },
  parameters: {
    docs: {
      description: {
        story: 'SessionBrowser with balanced statistics: 5 Processing, 8 Complete, 3 Updated, 2 Error.',
      },
    },
  },
};

// Performance test
export const PerformanceTest: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper initialSessionCount={24}>
        <div className="space-y-4">
          <div className="p-4 bg-amber-50 border border-amber-200 rounded-md">
            <h4 className="font-medium text-amber-800">⚡ Performance Test:</h4>
            <p className="text-sm text-amber-700 mt-1">
              This story loads the maximum number of sessions (24) to test performance and rendering.
            </p>
          </div>
          <Story />
        </div>
      </SessionProviderWrapper>
    ),
  ],
  args: {
    initialView: 'grid',
    showCreateButton: true,
    onSessionSelect: action('session-selected'),
  },
  parameters: {
    docs: {
      description: {
        story: 'Performance test with maximum sessions to validate rendering efficiency.',
      },
    },
  },
};

// Playground
export const Playground: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper initialSessionCount={10}>
        <Story />
      </SessionProviderWrapper>
    ),
  ],
  args: {
    initialView: 'grid',
    showCreateButton: true,
    onSessionSelect: action('session-selected'),
  },
  parameters: {
    docs: {
      description: {
        story: 'Interactive playground to test different configurations and behaviors.',
      },
    },
  },
};