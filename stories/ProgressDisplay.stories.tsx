import type { Meta, StoryObj } from '@storybook/react'
import { ProgressDisplay } from '@/components/progress-display'
import { useState, useEffect } from 'react'
import { Alert, AlertDescription } from '@/components/ui/alert'

// Mock the API client for Storybook
jest.mock('@/lib/api-client', () => ({
  processSession: jest.fn(),
}))

const meta: Meta<typeof ProgressDisplay> = {
  title: 'Integration/ProgressDisplay',
  component: ProgressDisplay,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: 'Progress display component with real-time updates using shadcn/ui components with blue theme.',
      },
    },
  },
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    sessionId: 'demo-session-123',
    onComplete: () => {
      console.log('Processing completed')
      alert('Processing completed!')
    },
    onError: (error: string) => {
      console.error('Processing error:', error)
      alert(`Error: ${error}`)
    },
  },
}

export const WithMockedProgress: Story = {
  args: {
    sessionId: 'mock-progress-session',
    onComplete: () => console.log('Mocked progress completed'),
    onError: (error: string) => console.error('Mocked progress error:', error),
  },
  render: (args) => {
    // Mock progressive updates
    const mockProcessSession = require('@/lib/api-client').processSession
    mockProcessSession.mockImplementation((sessionId: string, callback: any) => {
      const steps = [
        { progress: 10, step: 'Initializing processing...', status: 'processing' },
        { progress: 25, step: 'Reading credit card statement...', status: 'processing' },
        { progress: 40, step: 'Parsing expense report...', status: 'processing' },
        { progress: 60, step: 'Matching transactions...', status: 'processing' },
        { progress: 80, step: 'Generating reconciliation report...', status: 'processing' },
        { progress: 100, step: 'Processing complete!', status: 'complete' },
      ]

      return new Promise((resolve) => {
        let stepIndex = 0
        const interval = setInterval(() => {
          if (stepIndex < steps.length) {
            callback(steps[stepIndex])
            stepIndex++
          } else {
            clearInterval(interval)
            resolve(undefined)
          }
        }, 1000)
      })
    })

    return <ProgressDisplay {...args} />
  },
}

export const WithMockedError: Story = {
  args: {
    sessionId: 'mock-error-session',
    onComplete: () => console.log('Should not complete'),
    onError: (error: string) => console.error('Mocked error:', error),
  },
  render: (args) => {
    // Mock error scenario
    const mockProcessSession = require('@/lib/api-client').processSession
    mockProcessSession.mockImplementation((sessionId: string, callback: any) => {
      const steps = [
        { progress: 10, step: 'Initializing processing...', status: 'processing' },
        { progress: 25, step: 'Reading credit card statement...', status: 'processing' },
        { progress: 40, step: 'Error: Unable to parse PDF format', status: 'error', error: 'Invalid PDF format detected' },
      ]

      return new Promise((resolve, reject) => {
        let stepIndex = 0
        const interval = setInterval(() => {
          if (stepIndex < steps.length) {
            callback(steps[stepIndex])
            if (steps[stepIndex].status === 'error') {
              clearInterval(interval)
              reject(new Error(steps[stepIndex].error))
            }
            stepIndex++
          } else {
            clearInterval(interval)
            resolve(undefined)
          }
        }, 1000)
      })
    })

    return <ProgressDisplay {...args} />
  },
}

export const InteractiveDemo: Story = {
  render: () => {
    const [sessionId, setSessionId] = useState<string>('interactive-demo-session')
    const [status, setStatus] = useState<'idle' | 'processing' | 'completed' | 'error'>('idle')
    const [errorMessage, setErrorMessage] = useState<string | null>(null)
    const [key, setKey] = useState(0) // Force re-render

    const handleComplete = () => {
      setStatus('completed')
      setTimeout(() => {
        setStatus('idle')
        setKey(prev => prev + 1)
      }, 3000)
    }

    const handleError = (error: string) => {
      setStatus('error')
      setErrorMessage(error)
      setTimeout(() => {
        setStatus('idle')
        setErrorMessage(null)
        setKey(prev => prev + 1)
      }, 3000)
    }

    const startProcessing = () => {
      setStatus('processing')
      setSessionId(`demo-${Date.now()}`)
      setKey(prev => prev + 1)
    }

    // Mock realistic progress
    const mockProcessSession = require('@/lib/api-client').processSession
    mockProcessSession.mockImplementation((sessionId: string, callback: any) => {
      const shouldSucceed = Math.random() > 0.3 // 70% success rate

      const successSteps = [
        { progress: 0, step: 'Starting expense reconciliation...', status: 'processing' },
        { progress: 15, step: 'Loading credit card statement...', status: 'processing' },
        { progress: 30, step: 'Extracting transaction data...', status: 'processing' },
        { progress: 45, step: 'Reading expense report...', status: 'processing' },
        { progress: 60, step: 'Matching transactions...', status: 'processing' },
        { progress: 75, step: 'Identifying discrepancies...', status: 'processing' },
        { progress: 90, step: 'Generating final report...', status: 'processing' },
        { progress: 100, step: 'Reconciliation complete!', status: 'complete' },
      ]

      const errorSteps = [
        { progress: 0, step: 'Starting expense reconciliation...', status: 'processing' },
        { progress: 15, step: 'Loading credit card statement...', status: 'processing' },
        { progress: 30, step: 'Error processing file...', status: 'error', error: 'PDF parsing failed' },
      ]

      const steps = shouldSucceed ? successSteps : errorSteps

      return new Promise((resolve, reject) => {
        let stepIndex = 0
        const interval = setInterval(() => {
          if (stepIndex < steps.length) {
            callback(steps[stepIndex])
            if (steps[stepIndex].status === 'error') {
              clearInterval(interval)
              reject(new Error(steps[stepIndex].error))
              return
            }
            stepIndex++
          } else {
            clearInterval(interval)
            resolve(undefined)
          }
        }, 800)
      })
    })

    return (
      <div className="space-y-4">
        <div className="text-center">
          <h3 className="text-lg font-semibold mb-2">Interactive Progress Demo</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Click "Start Processing" to see the component in action with realistic progress updates.
            This demo has a 70% success rate to demonstrate both success and error scenarios.
          </p>
        </div>

        {status === 'idle' && (
          <div className="text-center">
            <button
              onClick={startProcessing}
              className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90"
            >
              Start Processing
            </button>
          </div>
        )}

        {status === 'processing' && (
          <ProgressDisplay
            key={key}
            sessionId={sessionId}
            onComplete={handleComplete}
            onError={handleError}
          />
        )}

        {status === 'completed' && (
          <Alert className="max-w-2xl mx-auto">
            <AlertDescription>
              ✅ Processing completed successfully! The component will reset in 3 seconds.
            </AlertDescription>
          </Alert>
        )}

        {status === 'error' && errorMessage && (
          <Alert variant="destructive" className="max-w-2xl mx-auto">
            <AlertDescription>
              ❌ Processing failed: {errorMessage}. The component will reset in 3 seconds.
            </AlertDescription>
          </Alert>
        )}

        <div className="text-center text-xs text-muted-foreground max-w-2xl mx-auto">
          <p>
            💡 This is a demo environment with simulated processing steps.
            The component demonstrates real-time progress updates and blue theme styling.
          </p>
        </div>
      </div>
    )
  },
}

export const BlueThemeShowcase: Story = {
  args: {
    sessionId: 'theme-demo-session',
    onComplete: () => console.log('Theme demo completed'),
    onError: (error: string) => console.error('Theme demo error:', error),
  },
  render: (args) => {
    // Mock for theme demonstration
    const mockProcessSession = require('@/lib/api-client').processSession
    mockProcessSession.mockImplementation((sessionId: string, callback: any) => {
      callback({ progress: 65, step: 'Demonstrating blue theme progress...', status: 'processing' })
      return Promise.resolve()
    })

    return (
      <div className="space-y-6">
        <div className="text-center">
          <h3 className="text-lg font-semibold mb-2">Blue Theme Integration</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Demonstrates how the progress display uses the blue theme across all components.
          </p>
        </div>

        <ProgressDisplay {...args} />

        <div className="max-w-2xl mx-auto space-y-2 text-sm">
          <h4 className="font-medium">Theme Elements Demonstrated:</h4>
          <ul className="list-disc list-inside space-y-1 text-muted-foreground">
            <li>Card component with blue-tinted borders</li>
            <li>Progress bar with primary blue fill color</li>
            <li>Alert component using default (blue-tinted) variant</li>
            <li>Typography using theme foreground colors</li>
            <li>Muted text using theme muted-foreground</li>
          </ul>
        </div>
      </div>
    )
  },
}

export const ProgressStates: Story = {
  render: () => {
    const progressSteps = [
      { progress: 0, step: 'Initializing...', status: 'processing' },
      { progress: 20, step: 'Processing credit card data...', status: 'processing' },
      { progress: 50, step: 'Analyzing expense report...', status: 'processing' },
      { progress: 75, step: 'Generating reconciliation...', status: 'processing' },
      { progress: 100, step: 'Complete!', status: 'complete' },
    ]

    return (
      <div className="space-y-8">
        <div className="text-center">
          <h3 className="text-lg font-semibold mb-4">Progress Display States</h3>
          <p className="text-sm text-muted-foreground mb-6">
            Different states of the progress component during processing.
          </p>
        </div>

        {progressSteps.map((step, index) => {
          const mockProcessSession = require('@/lib/api-client').processSession
          mockProcessSession.mockImplementation((sessionId: string, callback: any) => {
            callback(step)
            return Promise.resolve()
          })

          return (
            <div key={index} className="space-y-2">
              <h4 className="text-sm font-medium text-center">
                State {index + 1}: {step.progress}% - {step.step}
              </h4>
              <ProgressDisplay
                sessionId={`state-${index}`}
                onComplete={() => console.log(`State ${index + 1} completed`)}
                onError={(error) => console.error(`State ${index + 1} error:`, error)}
              />
            </div>
          )
        })}
      </div>
    )
  },
}

export const ResponsiveDemo: Story = {
  args: {
    sessionId: 'responsive-demo-session',
    onComplete: () => console.log('Responsive demo completed'),
    onError: (error: string) => console.error('Responsive demo error:', error),
  },
  render: (args) => {
    // Mock for responsive demonstration
    const mockProcessSession = require('@/lib/api-client').processSession
    mockProcessSession.mockImplementation((sessionId: string, callback: any) => {
      callback({ progress: 42, step: 'Processing in responsive layout...', status: 'processing' })
      return Promise.resolve()
    })

    return (
      <div className="space-y-4">
        <div className="text-center">
          <h3 className="text-lg font-semibold mb-2">Responsive Layout</h3>
          <p className="text-sm text-muted-foreground mb-4">
            The progress display adapts to different screen sizes while maintaining the blue theme.
          </p>
        </div>

        <div className="space-y-8">
          {/* Mobile simulation */}
          <div className="max-w-sm mx-auto border rounded-lg p-4">
            <h4 className="text-sm font-medium mb-2 text-center">Mobile (max-w-sm)</h4>
            <ProgressDisplay {...args} />
          </div>

          {/* Tablet simulation */}
          <div className="max-w-md mx-auto border rounded-lg p-4">
            <h4 className="text-sm font-medium mb-2 text-center">Tablet (max-w-md)</h4>
            <ProgressDisplay {...args} />
          </div>

          {/* Desktop simulation */}
          <div className="max-w-2xl mx-auto border rounded-lg p-4">
            <h4 className="text-sm font-medium mb-2 text-center">Desktop (max-w-2xl)</h4>
            <ProgressDisplay {...args} />
          </div>
        </div>
      </div>
    )
  },
}