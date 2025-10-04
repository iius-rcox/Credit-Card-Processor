import type { Meta, StoryObj } from '@storybook/react'
import { UploadForm } from '@/components/upload-form'
import { useState } from 'react'
import { Alert, AlertDescription } from '@/components/ui/alert'

// Mock the API client for Storybook
jest.mock('@/lib/api-client', () => ({
  uploadPDFs: jest.fn(),
}))

jest.mock('@/lib/session-storage', () => ({
  saveSession: jest.fn(),
}))

const meta: Meta<typeof UploadForm> = {
  title: 'Integration/UploadForm',
  component: UploadForm,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: 'Upload form component for PDF file uploads using shadcn/ui components with blue theme.',
      },
    },
  },
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    onUploadComplete: (sessionId: string) => {
      console.log('Upload completed with session ID:', sessionId)
      alert(`Upload completed! Session ID: ${sessionId}`)
    },
  },
}

export const WithMockedSuccess: Story = {
  args: {
    onUploadComplete: (sessionId: string) => {
      console.log('Mocked upload success:', sessionId)
    },
  },
  render: (args) => {
    // Mock successful API response
    const mockUploadPDFs = require('@/lib/api-client').uploadPDFs
    mockUploadPDFs.mockResolvedValue({
      session_id: 'mock-session-123',
      status: 'success',
    })

    return <UploadForm {...args} />
  },
}

export const WithMockedError: Story = {
  args: {
    onUploadComplete: (sessionId: string) => {
      console.log('Upload completed with session ID:', sessionId)
    },
  },
  render: (args) => {
    // Mock API error
    const mockUploadPDFs = require('@/lib/api-client').uploadPDFs
    mockUploadPDFs.mockRejectedValue(new Error('Network error: Unable to reach server'))

    return <UploadForm {...args} />
  },
}

export const InteractiveDemo: Story = {
  render: () => {
    const [uploadStatus, setUploadStatus] = useState<string | null>(null)
    const [lastSessionId, setLastSessionId] = useState<string | null>(null)

    const handleUploadComplete = (sessionId: string) => {
      setLastSessionId(sessionId)
      setUploadStatus('success')
      setTimeout(() => setUploadStatus(null), 5000)
    }

    // Mock API with random success/failure
    const mockUploadPDFs = require('@/lib/api-client').uploadPDFs
    mockUploadPDFs.mockImplementation(() => {
      const shouldSucceed = Math.random() > 0.3 // 70% success rate
      return new Promise((resolve, reject) => {
        setTimeout(() => {
          if (shouldSucceed) {
            resolve({
              session_id: `demo-session-${Date.now()}`,
              status: 'success',
            })
          } else {
            reject(new Error('Simulated upload failure'))
          }
        }, 2000) // 2 second delay to show loading state
      })
    })

    return (
      <div className="space-y-4">
        <div className="text-center">
          <h3 className="text-lg font-semibold mb-2">Interactive Upload Demo</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Select PDF files and click upload to see the component in action.
            This demo has a 70% success rate to demonstrate both success and error states.
          </p>
        </div>

        {uploadStatus === 'success' && lastSessionId && (
          <Alert className="max-w-2xl mx-auto">
            <AlertDescription>
              ✅ Demo upload completed! Session ID: {lastSessionId}
            </AlertDescription>
          </Alert>
        )}

        <UploadForm onUploadComplete={handleUploadComplete} />

        <div className="text-center text-xs text-muted-foreground max-w-2xl mx-auto">
          <p>
            💡 Tip: This is a demo environment. No files are actually uploaded.
            The component demonstrates the blue theme styling and interaction patterns.
          </p>
        </div>
      </div>
    )
  },
}

export const BlueThemeShowcase: Story = {
  args: {
    onUploadComplete: (sessionId: string) => {
      console.log('Theme demo upload completed:', sessionId)
    },
  },
  render: (args) => (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-lg font-semibold mb-2">Blue Theme Integration</h3>
        <p className="text-sm text-muted-foreground mb-4">
          Demonstrates how the upload form uses the blue theme across all components.
        </p>
      </div>

      <UploadForm {...args} />

      <div className="max-w-2xl mx-auto space-y-2 text-sm">
        <h4 className="font-medium">Theme Elements Demonstrated:</h4>
        <ul className="list-disc list-inside space-y-1 text-muted-foreground">
          <li>Card component with blue-tinted borders</li>
          <li>Input fields with blue focus rings</li>
          <li>Primary button with blue background</li>
          <li>Alert components using theme variants</li>
          <li>Typography using theme foreground colors</li>
        </ul>
      </div>
    </div>
  ),
}

export const AllStates: Story = {
  render: () => {
    const [currentState, setCurrentState] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle')

    // Mock different states
    const mockUploadPDFs = require('@/lib/api-client').uploadPDFs

    const handleStateChange = (newState: typeof currentState) => {
      setCurrentState(newState)

      if (newState === 'uploading') {
        mockUploadPDFs.mockImplementation(() => {
          return new Promise((resolve, reject) => {
            setTimeout(() => {
              if (newState === 'success') {
                resolve({ session_id: 'state-demo-123', status: 'success' })
              } else {
                reject(new Error('State demonstration error'))
              }
            }, 1000)
          })
        })
      }
    }

    const handleUploadComplete = (sessionId: string) => {
      console.log('State demo completed:', sessionId)
    }

    return (
      <div className="space-y-6">
        <div className="text-center">
          <h3 className="text-lg font-semibold mb-4">Upload Form States</h3>
          <div className="flex justify-center gap-2 mb-4">
            <button
              onClick={() => handleStateChange('idle')}
              className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
            >
              Idle
            </button>
            <button
              onClick={() => handleStateChange('uploading')}
              className="px-3 py-1 text-xs bg-blue-100 hover:bg-blue-200 rounded"
            >
              Uploading
            </button>
            <button
              onClick={() => handleStateChange('success')}
              className="px-3 py-1 text-xs bg-green-100 hover:bg-green-200 rounded"
            >
              Success
            </button>
            <button
              onClick={() => handleStateChange('error')}
              className="px-3 py-1 text-xs bg-red-100 hover:bg-red-200 rounded"
            >
              Error
            </button>
          </div>
          <p className="text-sm text-muted-foreground">
            Click the buttons above to see different component states
          </p>
        </div>

        <UploadForm onUploadComplete={handleUploadComplete} />
      </div>
    )
  },
}

export const ResponsiveDemo: Story = {
  args: {
    onUploadComplete: (sessionId: string) => {
      console.log('Responsive demo upload completed:', sessionId)
    },
  },
  render: (args) => (
    <div className="space-y-4">
      <div className="text-center">
        <h3 className="text-lg font-semibold mb-2">Responsive Layout</h3>
        <p className="text-sm text-muted-foreground mb-4">
          The upload form adapts to different screen sizes while maintaining the blue theme.
        </p>
      </div>

      <div className="space-y-8">
        {/* Mobile simulation */}
        <div className="max-w-sm mx-auto border rounded-lg p-4">
          <h4 className="text-sm font-medium mb-2 text-center">Mobile (max-w-sm)</h4>
          <UploadForm {...args} />
        </div>

        {/* Tablet simulation */}
        <div className="max-w-md mx-auto border rounded-lg p-4">
          <h4 className="text-sm font-medium mb-2 text-center">Tablet (max-w-md)</h4>
          <UploadForm {...args} />
        </div>

        {/* Desktop simulation */}
        <div className="max-w-2xl mx-auto border rounded-lg p-4">
          <h4 className="text-sm font-medium mb-2 text-center">Desktop (max-w-2xl)</h4>
          <UploadForm {...args} />
        </div>
      </div>
    </div>
  ),
}

export const AccessibilityDemo: Story = {
  args: {
    onUploadComplete: (sessionId: string) => {
      console.log('Accessibility demo upload completed:', sessionId)
    },
  },
  render: (args) => (
    <div className="space-y-4">
      <div className="text-center">
        <h3 className="text-lg font-semibold mb-2">Accessibility Features</h3>
        <p className="text-sm text-muted-foreground mb-4">
          The upload form includes proper labeling, focus management, and ARIA attributes.
        </p>
      </div>

      <UploadForm {...args} />

      <div className="max-w-2xl mx-auto space-y-2 text-sm">
        <h4 className="font-medium">Accessibility Features:</h4>
        <ul className="list-disc list-inside space-y-1 text-muted-foreground">
          <li>Proper label associations with htmlFor attributes</li>
          <li>Required field indicators</li>
          <li>Focus management and visible focus rings</li>
          <li>Alert components with role="alert" for screen readers</li>
          <li>Disabled state handling during upload</li>
          <li>Error messages associated with form fields</li>
        </ul>
      </div>
    </div>
  ),
}