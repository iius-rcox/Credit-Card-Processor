/**
 * SessionCard Storybook Stories
 *
 * Visual documentation and testing for SessionCard component
 * according to specs/003-add-ui-components/plan.md
 */

import type { Meta, StoryObj } from '@storybook/react';
import { action } from '@storybook/addon-actions';
import SessionCard from '@/components/session-management/session-card';
import { SessionProvider } from '@/components/session-management/session-provider';
import { MonthSession, SessionStatus } from '@/lib/session-types';

// Mock session data helper
const createMockSession = (overrides: Partial<MonthSession> = {}): MonthSession => ({
  id: '550e8400-e29b-41d4-a716-446655440000',
  name: 'January 2024 Expenses',
  createdAt: Date.now() - (7 * 24 * 60 * 60 * 1000), // 7 days ago
  expiresAt: Date.now() + (358 * 24 * 60 * 60 * 1000), // ~1 year from now
  status: 'Complete' as SessionStatus,
  backendSessionId: '550e8400-e29b-41d4-a716-446655440001',
  lastUpdated: Date.now() - (1 * 24 * 60 * 60 * 1000), // 1 day ago
  hasReports: true,
  fileCount: 3,
  matchCount: 42,
  ...overrides,
});

// Wrapper component to provide session context
const SessionCardWrapper = ({ children }: { children: React.ReactNode }) => (
  <SessionProvider>
    <div className="p-4 bg-gray-50 min-h-screen">
      <div className="max-w-sm">
        {children}
      </div>
    </div>
  </SessionProvider>
);

const meta = {
  title: 'Session Management/SessionCard',
  component: SessionCard,
  decorators: [
    (Story) => (
      <SessionCardWrapper>
        <Story />
      </SessionCardWrapper>
    ),
  ],
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: `
The SessionCard component displays individual session information in a card format with status indicators and action buttons.

**Features:**
- Status indicators with appropriate colors and icons
- Session metadata display (dates, file counts, match counts)
- Action buttons for rename, delete, and download reports
- Active state styling
- Expiration warnings
- Click to select functionality
        `,
      },
    },
  },
  argTypes: {
    session: {
      control: false,
      description: 'The session data to display',
    },
    isActive: {
      control: 'boolean',
      description: 'Whether this session is currently active',
    },
    showActions: {
      control: 'boolean',
      description: 'Whether to show action buttons',
    },
    onSelect: {
      action: 'selected',
      description: 'Callback when session is selected',
    },
    onRename: {
      action: 'rename',
      description: 'Callback when rename action is triggered',
    },
    onDelete: {
      action: 'delete',
      description: 'Callback when delete action is triggered',
    },
    onDownloadReports: {
      action: 'download',
      description: 'Callback when download reports action is triggered',
    },
  },
} satisfies Meta<typeof SessionCard>;

export default meta;
type Story = StoryObj<typeof meta>;

// Default story
export const Default: Story = {
  args: {
    session: createMockSession(),
    isActive: false,
    showActions: true,
    onSelect: action('session-selected'),
    onRename: action('session-rename'),
    onDelete: action('session-delete'),
    onDownloadReports: action('download-reports'),
  },
};

// Processing status
export const Processing: Story = {
  args: {
    ...Default.args,
    session: createMockSession({
      name: 'February 2024 Processing',
      status: 'Processing',
      hasReports: false,
      fileCount: 2,
      matchCount: 0,
      lastUpdated: Date.now() - (5 * 60 * 1000), // 5 minutes ago
    }),
  },
  parameters: {
    docs: {
      description: {
        story: 'Session in processing state with animated spinner icon.',
      },
    },
  },
};

// Updated status
export const Updated: Story = {
  args: {
    ...Default.args,
    session: createMockSession({
      name: 'March 2024 - Updated',
      status: 'Updated',
      hasReports: true,
      fileCount: 4,
      matchCount: 38,
      lastUpdated: Date.now() - (2 * 60 * 60 * 1000), // 2 hours ago
    }),
  },
  parameters: {
    docs: {
      description: {
        story: 'Session that has been updated with new receipts.',
      },
    },
  },
};

// Error status
export const Error: Story = {
  args: {
    ...Default.args,
    session: createMockSession({
      name: 'April 2024 - Failed',
      status: 'Error',
      hasReports: false,
      fileCount: 1,
      matchCount: 0,
      errorMessage: 'Invalid PDF format in expense report',
      lastUpdated: Date.now() - (30 * 60 * 1000), // 30 minutes ago
    }),
  },
  parameters: {
    docs: {
      description: {
        story: 'Session with error status showing error message.',
      },
    },
  },
};

// Active session
export const Active: Story = {
  args: {
    ...Default.args,
    session: createMockSession({
      name: 'Current Active Session',
      status: 'Complete',
    }),
    isActive: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'Currently active session with highlighted styling.',
      },
    },
  },
};

// No actions
export const NoActions: Story = {
  args: {
    ...Default.args,
    session: createMockSession({
      name: 'Read-Only Session',
    }),
    showActions: false,
  },
  parameters: {
    docs: {
      description: {
        story: 'Session card without action buttons for read-only display.',
      },
    },
  },
};

// Session without reports
export const NoReports: Story = {
  args: {
    ...Default.args,
    session: createMockSession({
      name: 'Incomplete Session',
      status: 'Processing',
      hasReports: false,
      fileCount: 1,
      matchCount: 0,
    }),
  },
  parameters: {
    docs: {
      description: {
        story: 'Session that hasn\'t generated reports yet.',
      },
    },
  },
};

// Long session name
export const LongName: Story = {
  args: {
    ...Default.args,
    session: createMockSession({
      name: 'Very Long Session Name That Should Wrap Properly And Show Good Text Handling',
      status: 'Complete',
    }),
  },
  parameters: {
    docs: {
      description: {
        story: 'Session with a very long name to test text wrapping.',
      },
    },
  },
};

// High numbers
export const HighNumbers: Story = {
  args: {
    ...Default.args,
    session: createMockSession({
      name: 'Large Enterprise Session',
      status: 'Complete',
      fileCount: 15,
      matchCount: 1247,
      hasReports: true,
    }),
  },
  parameters: {
    docs: {
      description: {
        story: 'Session with high file and match counts.',
      },
    },
  },
};

// Recently created
export const RecentlyCreated: Story = {
  args: {
    ...Default.args,
    session: createMockSession({
      name: 'Just Created Session',
      createdAt: Date.now() - (5 * 60 * 1000), // 5 minutes ago
      lastUpdated: Date.now() - (5 * 60 * 1000),
      status: 'Processing',
      hasReports: false,
      fileCount: 2,
      matchCount: 0,
    }),
  },
  parameters: {
    docs: {
      description: {
        story: 'Newly created session showing recent timestamps.',
      },
    },
  },
};

// Near expiration
export const NearExpiration: Story = {
  args: {
    ...Default.args,
    session: createMockSession({
      name: 'Expiring Soon',
      createdAt: Date.now() - (350 * 24 * 60 * 60 * 1000), // 350 days ago
      expiresAt: Date.now() + (15 * 24 * 60 * 60 * 1000), // 15 days from now
      status: 'Complete',
    }),
  },
  parameters: {
    docs: {
      description: {
        story: 'Session approaching expiration date.',
      },
    },
  },
};

// Grid layout example
export const GridLayout: Story = {
  render: () => (
    <SessionCardWrapper>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <SessionCard
          session={createMockSession({
            id: '1',
            name: 'January 2024',
            status: 'Complete',
          })}
          onSelect={action('session-1-selected')}
          onRename={action('session-1-rename')}
          onDelete={action('session-1-delete')}
          onDownloadReports={action('session-1-download')}
        />
        <SessionCard
          session={createMockSession({
            id: '2',
            name: 'February 2024',
            status: 'Processing',
            hasReports: false,
          })}
          isActive={true}
          onSelect={action('session-2-selected')}
          onRename={action('session-2-rename')}
          onDelete={action('session-2-delete')}
          onDownloadReports={action('session-2-download')}
        />
        <SessionCard
          session={createMockSession({
            id: '3',
            name: 'March 2024',
            status: 'Error',
            hasReports: false,
            errorMessage: 'File processing failed',
          })}
          onSelect={action('session-3-selected')}
          onRename={action('session-3-rename')}
          onDelete={action('session-3-delete')}
          onDownloadReports={action('session-3-download')}
        />
      </div>
    </SessionCardWrapper>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Multiple session cards arranged in a responsive grid layout.',
      },
    },
  },
};

// Interactive playground
export const Playground: Story = {
  args: {
    ...Default.args,
    session: createMockSession(),
  },
  parameters: {
    docs: {
      description: {
        story: 'Interactive playground to test different props and states.',
      },
    },
  },
};