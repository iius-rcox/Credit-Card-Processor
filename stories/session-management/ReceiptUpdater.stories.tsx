/**
 * ReceiptUpdater Storybook Stories
 *
 * Visual documentation and testing for ReceiptUpdater component
 * according to specs/003-add-ui-components/plan.md
 */

import type { Meta, StoryObj } from '@storybook/react';
import { action } from '@storybook/addon-actions';
import { ReceiptUpdater } from '@/components/session-management/receipt-updater';
import { SessionProvider } from '@/components/session-management/session-provider';
import { Button } from '@/components/ui/button';
import { Upload } from 'lucide-react';
import { MonthSession, SessionStorage, SessionStatus, SESSION_CONSTRAINTS } from '@/lib/session-types';

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

// Create mock storage with a test session
const createMockStorage = (session: MonthSession): SessionStorage => ({
  sessions: {
    [session.id]: session,
  },
  activeSessionId: session.id,
  lastCleanup: Date.now(),
  version: SESSION_CONSTRAINTS.SCHEMA_VERSION,
});

// Custom SessionProvider wrapper for stories
const SessionProviderWrapper = ({
  children,
  session = createMockSession(),
}: {
  children: React.ReactNode;
  session?: MonthSession;
}) => (
  <SessionProvider initialStorage={createMockStorage(session)}>
    <div className="p-4 bg-gray-50 min-h-screen">
      <div className="max-w-md mx-auto">
        {children}
      </div>
    </div>
  </SessionProvider>
);

const meta = {
  title: 'Session Management/ReceiptUpdater',
  component: ReceiptUpdater,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: `
The ReceiptUpdater component provides a file upload interface for adding new expense reports to existing sessions.

**Features:**
- Drag and drop file upload
- File type validation (PDF only)
- File size validation (max 50MB)
- Progress tracking during upload
- Success and error handling
- Session validation
- Accessible file input
- Real-time validation feedback

**Validation Rules:**
- Only PDF files accepted
- Maximum file size: 50MB
- Session must exist and not be expired
- Only one file upload at a time

**Upload Process:**
1. File selection (drag/drop or click)
2. Client-side validation
3. Upload with progress tracking
4. Backend processing
5. Success/error feedback
        `,
      },
    },
  },
  argTypes: {
    sessionId: {
      control: 'text',
      description: 'ID of the session to update',
    },
    isOpen: {
      control: 'boolean',
      description: 'Whether the updater dialog is open',
    },
    onClose: {
      action: 'closed',
      description: 'Callback when updater is closed',
    },
    onUpdated: {
      action: 'updated',
      description: 'Callback when receipts are successfully updated',
    },
  },
} satisfies Meta<typeof ReceiptUpdater>;

export default meta;
type Story = StoryObj<typeof meta>;

// Default story - closed state
export const Default: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper>
        <Story />
      </SessionProviderWrapper>
    ),
  ],
  args: {
    sessionId: '550e8400-e29b-41d4-a716-446655440000',
    isOpen: false,
    onClose: action('closed'),
    onUpdated: action('updated'),
  },
};

// Open dialog
export const OpenDialog: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper>
        <Story />
      </SessionProviderWrapper>
    ),
  ],
  args: {
    sessionId: '550e8400-e29b-41d4-a716-446655440000',
    isOpen: true,
    onClose: action('closed'),
    onUpdated: action('updated'),
  },
  parameters: {
    docs: {
      description: {
        story: 'ReceiptUpdater dialog open and ready for file upload.',
      },
    },
  },
};

// Processing session
export const ProcessingSession: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper
        session={createMockSession({
          status: 'Processing',
          hasReports: false,
          fileCount: 2,
          matchCount: 0,
        })}
      >
        <Story />
      </SessionProviderWrapper>
    ),
  ],
  args: {
    sessionId: '550e8400-e29b-41d4-a716-446655440000',
    isOpen: true,
    onClose: action('closed'),
    onUpdated: action('updated'),
  },
  parameters: {
    docs: {
      description: {
        story: 'ReceiptUpdater for a session currently being processed.',
      },
    },
  },
};

// Error session
export const ErrorSession: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper
        session={createMockSession({
          status: 'Error',
          hasReports: false,
          fileCount: 1,
          matchCount: 0,
          errorMessage: 'Previous upload failed - invalid PDF format',
        })}
      >
        <Story />
      </SessionProviderWrapper>
    ),
  ],
  args: {
    sessionId: '550e8400-e29b-41d4-a716-446655440000',
    isOpen: true,
    onClose: action('closed'),
    onUpdated: action('updated'),
  },
  parameters: {
    docs: {
      description: {
        story: 'ReceiptUpdater for a session with previous error - allows retry.',
      },
    },
  },
};

// Session without reports
export const NoReportsSession: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper
        session={createMockSession({
          status: 'Complete',
          hasReports: false,
          fileCount: 2,
          matchCount: 15,
        })}
      >
        <Story />
      </SessionProviderWrapper>
    ),
  ],
  args: {
    sessionId: '550e8400-e29b-41d4-a716-446655440000',
    isOpen: true,
    onClose: action('closed'),
    onUpdated: action('updated'),
  },
  parameters: {
    docs: {
      description: {
        story: 'ReceiptUpdater for a session that completed but has no reports.',
      },
    },
  },
};

// Invalid session ID
export const InvalidSession: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper>
        <Story />
      </SessionProviderWrapper>
    ),
  ],
  args: {
    sessionId: 'non-existent-session-id',
    isOpen: true,
    onClose: action('closed'),
    onUpdated: action('updated'),
  },
  parameters: {
    docs: {
      description: {
        story: 'ReceiptUpdater with invalid session ID - shows error state.',
      },
    },
  },
};

// With custom trigger
export const CustomTrigger: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper>
        <div className="space-y-4">
          <div className="text-center">
            <h3 className="text-lg font-semibold mb-2">Session: January 2024 Expenses</h3>
            <p className="text-sm text-gray-600 mb-4">
              Status: Complete • Files: 3 • Matches: 42 • Reports: Available
            </p>
          </div>
          <Story />
        </div>
      </SessionProviderWrapper>
    ),
  ],
  render: (args) => (
    <ReceiptUpdater
      {...args}
      trigger={
        <Button className="flex items-center gap-2 w-full">
          <Upload className="h-4 w-4" />
          Upload Additional Receipts
        </Button>
      }
    />
  ),
  args: {
    sessionId: '550e8400-e29b-41d4-a716-446655440000',
    isOpen: false,
    onClose: action('closed'),
    onUpdated: action('updated'),
  },
  parameters: {
    docs: {
      description: {
        story: 'ReceiptUpdater with custom trigger button in context.',
      },
    },
  },
};

// File validation demo
export const FileValidationDemo: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper>
        <div className="space-y-4">
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-md">
            <h4 className="font-medium text-blue-800">📁 File Validation Rules:</h4>
            <ul className="text-sm text-blue-700 mt-2 space-y-1">
              <li>✅ <strong>Accepted:</strong> PDF files up to 50MB</li>
              <li>❌ <strong>Rejected:</strong> Non-PDF files (JPG, PNG, DOC, etc.)</li>
              <li>❌ <strong>Rejected:</strong> Files larger than 50MB</li>
              <li>💡 <strong>Tip:</strong> Try dragging different file types to see validation</li>
            </ul>
          </div>
          <Story />
        </div>
      </SessionProviderWrapper>
    ),
  ],
  args: {
    sessionId: '550e8400-e29b-41d4-a716-446655440000',
    isOpen: true,
    onClose: action('closed'),
    onUpdated: action('updated'),
  },
  parameters: {
    docs: {
      description: {
        story: 'Interactive demo showing file validation behavior.',
      },
    },
  },
};

// Upload progress simulation
export const UploadProgressDemo: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper>
        <div className="space-y-4">
          <div className="p-4 bg-amber-50 border border-amber-200 rounded-md">
            <h4 className="font-medium text-amber-800">📤 Upload Process:</h4>
            <ol className="text-sm text-amber-700 mt-2 space-y-1">
              <li>1. Select or drag a PDF file</li>
              <li>2. File validation occurs</li>
              <li>3. Upload progress is displayed</li>
              <li>4. Backend processing with feedback</li>
              <li>5. Success confirmation or error handling</li>
            </ol>
          </div>
          <Story />
        </div>
      </SessionProviderWrapper>
    ),
  ],
  args: {
    sessionId: '550e8400-e29b-41d4-a716-446655440000',
    isOpen: true,
    onClose: action('closed'),
    onUpdated: action('updated'),
  },
  parameters: {
    docs: {
      description: {
        story: 'Demo showing the complete upload process with progress indication.',
      },
    },
  },
};

// Mobile view
export const MobileView: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper>
        <div className="max-w-xs mx-auto">
          <Story />
        </div>
      </SessionProviderWrapper>
    ),
  ],
  args: {
    sessionId: '550e8400-e29b-41d4-a716-446655440000',
    isOpen: true,
    onClose: action('closed'),
    onUpdated: action('updated'),
  },
  parameters: {
    viewport: {
      defaultViewport: 'mobile1',
    },
    docs: {
      description: {
        story: 'ReceiptUpdater optimized for mobile devices.',
      },
    },
  },
};

// Accessibility demo
export const AccessibilityDemo: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper>
        <div className="space-y-4">
          <div className="p-4 bg-green-50 border border-green-200 rounded-md">
            <h4 className="font-medium text-green-800">♿ Accessibility Features:</h4>
            <ul className="text-sm text-green-700 mt-2 space-y-1">
              <li>• Keyboard navigation (Tab, Enter, Escape)</li>
              <li>• Screen reader support for file input</li>
              <li>• ARIA labels and descriptions</li>
              <li>• Focus management in dialog</li>
              <li>• Error announcements</li>
              <li>• Progress updates for screen readers</li>
            </ul>
          </div>
          <Story />
        </div>
      </SessionProviderWrapper>
    ),
  ],
  args: {
    sessionId: '550e8400-e29b-41d4-a716-446655440000',
    isOpen: true,
    onClose: action('closed'),
    onUpdated: action('updated'),
  },
  parameters: {
    docs: {
      description: {
        story: 'Demonstrates accessibility features of the ReceiptUpdater component.',
      },
    },
  },
};

// Integration example
export const IntegrationExample: Story = {
  render: () => (
    <SessionProviderWrapper>
      <div className="space-y-6">
        <div className="text-center">
          <h3 className="text-xl font-semibold">Session Management</h3>
          <p className="text-gray-600">January 2024 Expenses</p>
        </div>

        <div className="bg-white rounded-lg border p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium">Status:</span>
              <span className="ml-2 text-green-600">Complete</span>
            </div>
            <div>
              <span className="font-medium">Files:</span>
              <span className="ml-2">3 uploaded</span>
            </div>
            <div>
              <span className="font-medium">Matches:</span>
              <span className="ml-2">42 processed</span>
            </div>
            <div>
              <span className="font-medium">Reports:</span>
              <span className="ml-2 text-blue-600">Available</span>
            </div>
          </div>

          <div className="flex gap-2">
            <Button variant="outline" className="flex-1">
              Download Excel
            </Button>
            <Button variant="outline" className="flex-1">
              Download CSV
            </Button>
          </div>

          <ReceiptUpdater
            sessionId="550e8400-e29b-41d4-a716-446655440000"
            onClose={action('closed')}
            onUpdated={action('updated')}
            trigger={
              <Button className="w-full flex items-center gap-2">
                <Upload className="h-4 w-4" />
                Upload Additional Receipts
              </Button>
            }
          />
        </div>
      </div>
    </SessionProviderWrapper>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Real-world integration example within a session management interface.',
      },
    },
  },
};

// Error states showcase
export const ErrorStatesShowcase: Story = {
  render: () => (
    <SessionProviderWrapper>
      <div className="space-y-6">
        <h3 className="text-lg font-semibold text-center">Error States Demo</h3>

        <div className="grid gap-4">
          <div className="p-4 border rounded-lg">
            <h4 className="font-medium mb-2">File Type Error</h4>
            <p className="text-sm text-gray-600 mb-3">
              Upload a non-PDF file to see validation error
            </p>
            <ReceiptUpdater
              sessionId="550e8400-e29b-41d4-a716-446655440000"
              isOpen={true}
              onClose={action('file-type-error-closed')}
              onUpdated={action('file-type-error-updated')}
            />
          </div>
        </div>
      </div>
    </SessionProviderWrapper>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Showcase of different error states and validation messages.',
      },
    },
  },
};

// Playground
export const Playground: Story = {
  decorators: [
    (Story) => (
      <SessionProviderWrapper>
        <Story />
      </SessionProviderWrapper>
    ),
  ],
  args: {
    sessionId: '550e8400-e29b-41d4-a716-446655440000',
    isOpen: false,
    onClose: action('closed'),
    onUpdated: action('updated'),
  },
  parameters: {
    docs: {
      description: {
        story: 'Interactive playground to test different configurations and states.',
      },
    },
  },
};