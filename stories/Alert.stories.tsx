import type { Meta, StoryObj } from '@storybook/react'
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert'
import { AlertCircle, CheckCircle, Info } from 'lucide-react'

const meta: Meta<typeof Alert> = {
  title: 'Components/Alert',
  component: Alert,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['default', 'destructive'],
    },
  },
}

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    variant: 'default',
  },
  render: (args) => (
    <Alert {...args}>
      <Info className="h-4 w-4" />
      <AlertTitle>Information</AlertTitle>
      <AlertDescription>
        This is a default alert with informational content using the blue theme.
      </AlertDescription>
    </Alert>
  ),
}

export const Destructive: Story = {
  args: {
    variant: 'destructive',
  },
  render: (args) => (
    <Alert {...args}>
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>Error</AlertTitle>
      <AlertDescription>
        This is a destructive alert indicating an error or warning state.
      </AlertDescription>
    </Alert>
  ),
}

export const Success: Story = {
  args: {
    variant: 'default',
  },
  render: (args) => (
    <Alert {...args} className="border-green-200 bg-green-50 text-green-800">
      <CheckCircle className="h-4 w-4" />
      <AlertTitle>Success</AlertTitle>
      <AlertDescription>
        Operation completed successfully! This shows a success variant using green colors.
      </AlertDescription>
    </Alert>
  ),
}

export const WithoutIcon: Story = {
  args: {
    variant: 'default',
  },
  render: (args) => (
    <Alert {...args}>
      <AlertTitle>Alert Title Only</AlertTitle>
      <AlertDescription>
        This alert demonstrates the layout without an icon, showing clean typography hierarchy.
      </AlertDescription>
    </Alert>
  ),
}

export const TitleOnly: Story = {
  args: {
    variant: 'default',
  },
  render: (args) => (
    <Alert {...args}>
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>This alert only has a title with an icon</AlertTitle>
    </Alert>
  ),
}

export const DescriptionOnly: Story = {
  args: {
    variant: 'destructive',
  },
  render: (args) => (
    <Alert {...args}>
      <AlertDescription>
        This alert only contains a description without a title, useful for simple notifications.
      </AlertDescription>
    </Alert>
  ),
}

export const LongContent: Story = {
  args: {
    variant: 'default',
  },
  render: (args) => (
    <Alert {...args}>
      <Info className="h-4 w-4" />
      <AlertTitle>Long Content Alert</AlertTitle>
      <AlertDescription>
        This alert demonstrates how the component handles longer content that may wrap to multiple lines.
        The layout should remain consistent and readable regardless of content length. This helps test
        the responsive behavior and ensures proper spacing and typography in various scenarios.
      </AlertDescription>
    </Alert>
  ),
}

// Theme showcase stories
export const BlueThemeShowcase: Story = {
  render: () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold mb-4">Blue Theme Alert Variants</h3>

      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>Default Blue Theme</AlertTitle>
        <AlertDescription>
          Shows the default blue-tinted alert using the primary theme colors.
        </AlertDescription>
      </Alert>

      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Destructive Variant</AlertTitle>
        <AlertDescription>
          Shows the destructive variant with red colors for errors and warnings.
        </AlertDescription>
      </Alert>
    </div>
  ),
}

export const ResponsiveDemo: Story = {
  render: () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold mb-4">Responsive Behavior</h3>
      <div className="grid gap-4 md:grid-cols-2">
        <Alert>
          <Info className="h-4 w-4" />
          <AlertTitle>Mobile Layout</AlertTitle>
          <AlertDescription>
            This alert adapts to smaller screens with proper spacing.
          </AlertDescription>
        </Alert>

        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Desktop Layout</AlertTitle>
          <AlertDescription>
            This alert shows how content adapts to wider layouts.
          </AlertDescription>
        </Alert>
      </div>
    </div>
  ),
}