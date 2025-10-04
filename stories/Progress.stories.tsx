import type { Meta, StoryObj } from '@storybook/react'
import { Progress } from '@/components/ui/progress'
import { useState, useEffect } from 'react'

const meta: Meta<typeof Progress> = {
  title: 'Components/Progress',
  component: Progress,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
  argTypes: {
    value: {
      control: { type: 'range', min: 0, max: 100, step: 1 },
    },
    max: {
      control: { type: 'number' },
    },
  },
}

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    value: 33,
  },
}

export const ZeroPercent: Story = {
  args: {
    value: 0,
  },
}

export const FiftyPercent: Story = {
  args: {
    value: 50,
  },
}

export const Complete: Story = {
  args: {
    value: 100,
  },
}

export const CustomMax: Story = {
  args: {
    value: 75,
    max: 150,
  },
  render: (args) => (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span>Custom Max Value</span>
        <span>{args.value}/{args.max}</span>
      </div>
      <Progress {...args} />
      <p className="text-xs text-muted-foreground">
        This progress bar has a maximum value of {args.max} instead of the default 100.
      </p>
    </div>
  ),
}

export const WithLabel: Story = {
  args: {
    value: 65,
  },
  render: (args) => (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span>Upload Progress</span>
        <span>{args.value}%</span>
      </div>
      <Progress {...args} />
    </div>
  ),
}

export const Indeterminate: Story = {
  args: {
    value: undefined,
  },
  render: (args) => (
    <div className="space-y-2">
      <div className="text-sm">Loading...</div>
      <Progress {...args} className="animate-pulse" />
      <p className="text-xs text-muted-foreground">
        Indeterminate progress (no value provided)
      </p>
    </div>
  ),
}

export const AnimatedProgress: Story = {
  render: () => {
    const [progress, setProgress] = useState(0)

    useEffect(() => {
      const timer = setTimeout(() => setProgress(66), 500)
      return () => clearTimeout(timer)
    }, [])

    return (
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span>Animated Progress</span>
          <span>{progress}%</span>
        </div>
        <Progress value={progress} className="transition-all duration-500 ease-out" />
        <p className="text-xs text-muted-foreground">
          Watch the progress animate from 0% to 66%
        </p>
      </div>
    )
  },
}

export const ProgressStates: Story = {
  render: () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold">Progress Bar States</h3>

      <div className="space-y-4">
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Not Started</span>
            <span>0%</span>
          </div>
          <Progress value={0} />
        </div>

        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>In Progress</span>
            <span>45%</span>
          </div>
          <Progress value={45} />
        </div>

        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Almost Complete</span>
            <span>85%</span>
          </div>
          <Progress value={85} />
        </div>

        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Complete</span>
            <span>100%</span>
          </div>
          <Progress value={100} />
        </div>
      </div>
    </div>
  ),
}

export const BlueThemeShowcase: Story = {
  render: () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold">Blue Theme Progress Bars</h3>

      <div className="space-y-4">
        <div className="space-y-2">
          <div className="text-sm font-medium">Primary Blue Progress</div>
          <Progress value={60} />
          <p className="text-xs text-muted-foreground">
            Uses the primary blue color from the theme
          </p>
        </div>

        <div className="space-y-2">
          <div className="text-sm font-medium">Custom Blue Variant</div>
          <Progress value={40} className="[&>div]:bg-blue-600" />
          <p className="text-xs text-muted-foreground">
            Custom blue shade applied via className
          </p>
        </div>
      </div>
    </div>
  ),
}

export const SizeVariations: Story = {
  render: () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold">Progress Bar Sizes</h3>

      <div className="space-y-4">
        <div className="space-y-2">
          <div className="text-sm font-medium">Thin (h-1)</div>
          <Progress value={70} className="h-1" />
        </div>

        <div className="space-y-2">
          <div className="text-sm font-medium">Default (h-2)</div>
          <Progress value={70} />
        </div>

        <div className="space-y-2">
          <div className="text-sm font-medium">Medium (h-3)</div>
          <Progress value={70} className="h-3" />
        </div>

        <div className="space-y-2">
          <div className="text-sm font-medium">Thick (h-4)</div>
          <Progress value={70} className="h-4" />
        </div>
      </div>
    </div>
  ),
}

export const ResponsiveDemo: Story = {
  render: () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold mb-4">Responsive Progress Bars</h3>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <div className="text-sm font-medium">Mobile Layout</div>
          <Progress value={35} />
          <p className="text-xs text-muted-foreground">
            Adapts to narrow containers
          </p>
        </div>

        <div className="space-y-2">
          <div className="text-sm font-medium">Desktop Layout</div>
          <Progress value={75} />
          <p className="text-xs text-muted-foreground">
            Scales to wider containers
          </p>
        </div>
      </div>
    </div>
  ),
}