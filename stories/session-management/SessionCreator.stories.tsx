/**
 * SessionCreator Storybook Stories
 *
 * Visual documentation and testing for SessionCreator component
 * according to specs/003-add-ui-components/plan.md
 */

import type { Meta, StoryObj } from '@storybook/react';
import { action } from '@storybook/addon-actions';
import { SessionCreator } from '@/components/session-management/session-creator';
import { SessionProvider } from '@/components/session-management/session-provider';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import { MonthSession, SessionStorage, SESSION_CONSTRAINTS } from '@/lib/session-types';

// Mock session data helper
const createMockSession = (overrides: Partial<MonthSession> = {}): MonthSession => ({
  id: `session-${Math.random().toString(36).substr(2, 9)}`,
  name: `Test Session ${Math.floor(Math.random() * 100)}`,
  createdAt: Date.now() - (Math.random() * 30 * 24 * 60 * 60 * 1000), // Random date within 30 days
  expiresAt: Date.now() + (365 * 24 * 60 * 60 * 1000), // 1 year from now
  status: 'Complete',
  backendSessionId: `backend-${Math.random().toString(36).substr(2, 9)}`,
  lastUpdated: Date.now() - (Math.random() * 7 * 24 * 60 * 60 * 1000), // Random date within 7 days
  hasReports: Math.random() > 0.5,
  fileCount: Math.floor(Math.random() * 5) + 1,
  matchCount: Math.floor(Math.random() * 50),
  ...overrides,
});

// Create mock storage with specific number of sessions
const createMockStorage = (sessionCount: number): SessionStorage => {
  const sessions = Array.from({ length: sessionCount }, (_, i) =>
    createMockSession({ id: `session-${i}`, name: `Session ${i + 1}` })
  );

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
    <div className="p-4 bg-gray-50 min-h-screen">
      <div className="max-w-md mx-auto">
        {children}
      </div>
    </div>
  </SessionProvider>
);

const meta = {
  title: 'Session Management/SessionCreator',
  component: SessionCreator,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: `
The SessionCreator component provides a form interface for creating new expense processing sessions with comprehensive validation.

**Features:**
- Session name validation (length, uniqueness)
- Session limit enforcement (maximum 24 sessions)
- Real-time validation feedback
- Loading states during creation
- Integration with SessionProvider context
- Configurable trigger element
- Warning when approaching session limit

**Validation Rules:**
- Session names must be 2-100 characters
- Session names must be unique within storage
- Maximum 24 sessions allowed
- Names are trimmed of whitespace
        `,
      },
    },
  },
  argTypes: {
    isOpen: {
      control: 'boolean',
      description: 'Whether the creator form is initially open',
    },
    onSessionCreated: {
      action: 'session-created',
      description: 'Callback when a session is successfully created',
    },
    onCancel: {
      action: 'cancelled',
      description: 'Callback when creation is cancelled',
    },
    trigger: {
      control: false,
      description: 'Custom trigger element (if not provided, uses default button)',
    },
  },
} satisfies Meta<typeof SessionCreator>;

export default meta;
type Story = StoryObj<typeof meta>;

// Default story - closed state
export const Default: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper initialSessionCount={3}>
        <Story />
      </SessionProviderWrapper>
    ),
  ],
  args: {
    isOpen: false,
    onSessionCreated: action('session-created'),
    onCancel: action('cancelled'),
  },
};

// Open form state
export const OpenForm: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper initialSessionCount={3}>
        <Story />
      </SessionProviderWrapper>
    ),
  ],
  args: {
    isOpen: true,
    onSessionCreated: action('session-created'),
    onCancel: action('cancelled'),
  },
  parameters: {
    docs: {
      description: {
        story: 'SessionCreator with form open and ready for input.',
      },
    },
  },
};

// Custom trigger
export const CustomTrigger: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper initialSessionCount={5}>
        <Story />
      </SessionProviderWrapper>
    ),
  ],
  args: {
    isOpen: false,
    onSessionCreated: action('session-created'),
    onCancel: action('cancelled'),
    trigger: (
      <Button variant="outline" className="flex items-center gap-2">
        <Plus className="h-4 w-4" />
        Add New Session
      </Button>
    ),
  },
  parameters: {
    docs: {
      description: {
        story: 'SessionCreator with a custom trigger button.',
      },
    },
  },
};

// Approaching limit warning
export const ApproachingLimit: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper initialSessionCount={22}>
        <Story />
      </SessionProviderWrapper>
    ),
  ],
  args: {
    isOpen: true,
    onSessionCreated: action('session-created'),
    onCancel: action('cancelled'),
  },
  parameters: {
    docs: {
      description: {
        story: 'SessionCreator when approaching the 24 session limit (22+ sessions exist).',
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
    isOpen: false,
    onSessionCreated: action('session-created'),
    onCancel: action('cancelled'),
  },
  parameters: {
    docs: {
      description: {
        story: 'SessionCreator when at the maximum session limit (24 sessions). Creation is blocked.',
      },
    },
  },
};

// Empty storage
export const EmptyStorage: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper initialSessionCount={0}>
        <Story />
      </SessionProviderWrapper>
    ),
  ],
  args: {
    isOpen: true,
    onSessionCreated: action('session-created'),
    onCancel: action('cancelled'),
  },
  parameters: {
    docs: {
      description: {
        story: 'SessionCreator with no existing sessions - first session creation.',
      },
    },
  },
};

// Loading state simulation
export const LoadingState: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper initialSessionCount={3}>
        <div className="space-y-4">
          <Story />
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-md">
            <p className="text-sm text-blue-800">
              💡 <strong>Tip:</strong> Fill in a session name and click "Create Session" to see the loading state.
            </p>
          </div>
        </div>
      </SessionProviderWrapper>
    ),
  ],
  args: {
    isOpen: true,
    onSessionCreated: action('session-created'),
    onCancel: action('cancelled'),
  },
  parameters: {
    docs: {
      description: {
        story: 'Interactive example to test the loading state during session creation.',
      },
    },
  },
};

// Validation examples
export const ValidationExamples: Story = {
  render: () => (
    <SessionProviderWrapper initialSessionCount={3}>
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold mb-2">Validation Examples</h3>
          <p className="text-sm text-gray-600 mb-4">
            Try these examples to see different validation states:
          </p>
        </div>

        <SessionCreator
          isOpen={true}
          onSessionCreated={action('session-created')}
          onCancel={action('cancelled')}
        />

        <div className="space-y-3">
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <h4 className="font-medium text-red-800">❌ Invalid Examples:</h4>
            <ul className="text-sm text-red-700 mt-1 space-y-1">
              <li>• Empty name: ""</li>
              <li>• Too short: "A"</li>
              <li>• Too long: {"A".repeat(101)}</li>
              <li>• Duplicate: "Session 1" (already exists)</li>
            </ul>
          </div>

          <div className="p-3 bg-green-50 border border-green-200 rounded-md">
            <h4 className="font-medium text-green-800">✅ Valid Examples:</h4>
            <ul className="text-sm text-green-700 mt-1 space-y-1">
              <li>• "January 2024 Expenses"</li>
              <li>• "Q1 2024 Processing"</li>
              <li>• "Year End Review 2023"</li>
              <li>• "AB" (minimum length)</li>
            </ul>
          </div>
        </div>
      </div>
    </SessionProviderWrapper>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Interactive examples showing different validation scenarios.',
      },
    },
  },
};

// Integration example
export const IntegrationExample: Story = {
  render: () => (
    <SessionProviderWrapper initialSessionCount={5}>
      <div className="space-y-4">
        <div className="text-center">
          <h3 className="text-lg font-semibold">Session Management Dashboard</h3>
          <p className="text-sm text-gray-600">
            Current sessions: 5/24
          </p>
        </div>

        <div className="flex justify-center">
          <SessionCreator
            onSessionCreated={(sessionId) => {
              action('session-created')(sessionId);
              alert(`Session created with ID: ${sessionId}`);
            }}
            onCancel={action('cancelled')}
            trigger={
              <Button className="flex items-center gap-2">
                <Plus className="h-4 w-4" />
                Create New Session
              </Button>
            }
          />
        </div>

        <div className="text-center text-sm text-gray-500">
          <p>Click the button above to create a new session</p>
        </div>
      </div>
    </SessionProviderWrapper>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Example of SessionCreator integrated into a dashboard interface.',
      },
    },
  },
};

// Accessibility demonstration
export const AccessibilityDemo: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper initialSessionCount={3}>
        <div className="space-y-4">
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-md">
            <h4 className="font-medium text-blue-800">♿ Accessibility Features:</h4>
            <ul className="text-sm text-blue-700 mt-2 space-y-1">
              <li>• Keyboard navigation (Tab, Enter, Escape)</li>
              <li>• Screen reader labels and descriptions</li>
              <li>• Focus management</li>
              <li>• Error announcements</li>
              <li>• Semantic HTML structure</li>
            </ul>
          </div>
          <Story />
        </div>
      </SessionProviderWrapper>
    ),
  ],
  args: {
    isOpen: true,
    onSessionCreated: action('session-created'),
    onCancel: action('cancelled'),
  },
  parameters: {
    docs: {
      description: {
        story: 'Demonstrates accessibility features of the SessionCreator component.',
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
    isOpen: false,
    onSessionCreated: action('session-created'),
    onCancel: action('cancelled'),
  },
  parameters: {
    docs: {
      description: {
        story: 'Interactive playground to test different configurations.',
      },
    },
  },
};