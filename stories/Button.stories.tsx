import type { Meta, StoryObj } from '@storybook/react';
import { Button } from '@/components/ui/button';
import { ChevronRight, Download, Trash2, Plus } from 'lucide-react';

const meta: Meta<typeof Button> = {
  title: 'Components/Button',
  component: Button,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A versatile button component built with shadcn/ui using blue theme colors.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['default', 'destructive', 'outline', 'secondary', 'ghost', 'link'],
      description: 'The visual style variant of the button',
    },
    size: {
      control: { type: 'select' },
      options: ['default', 'sm', 'lg', 'icon', 'icon-sm', 'icon-lg'],
      description: 'The size of the button',
    },
    asChild: {
      control: { type: 'boolean' },
      description: 'Change the component to the HTML tag or custom component of the only child',
    },
    disabled: {
      control: { type: 'boolean' },
      description: 'Whether the button is disabled',
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

// Default button with blue primary theme
export const Default: Story = {
  args: {
    children: 'Primary Button',
    variant: 'default',
    size: 'default',
  },
};

export const Destructive: Story = {
  args: {
    children: 'Delete Item',
    variant: 'destructive',
    size: 'default',
  },
};

export const Outline: Story = {
  args: {
    children: 'Outline Button',
    variant: 'outline',
    size: 'default',
  },
};

export const Secondary: Story = {
  args: {
    children: 'Secondary Button',
    variant: 'secondary',
    size: 'default',
  },
};

export const Ghost: Story = {
  args: {
    children: 'Ghost Button',
    variant: 'ghost',
    size: 'default',
  },
};

export const Link: Story = {
  args: {
    children: 'Link Button',
    variant: 'link',
    size: 'default',
  },
};

// Size variations
export const Small: Story = {
  args: {
    children: 'Small Button',
    variant: 'default',
    size: 'sm',
  },
};

export const Large: Story = {
  args: {
    children: 'Large Button',
    variant: 'default',
    size: 'lg',
  },
};

// Icon buttons
export const Icon: Story = {
  args: {
    children: <Plus className="h-4 w-4" />,
    variant: 'default',
    size: 'icon',
  },
};

export const IconSmall: Story = {
  args: {
    children: <Download className="h-3 w-3" />,
    variant: 'outline',
    size: 'icon-sm',
  },
};

export const IconLarge: Story = {
  args: {
    children: <Trash2 className="h-5 w-5" />,
    variant: 'destructive',
    size: 'icon-lg',
  },
};

// Buttons with icons and text
export const WithIcon: Story = {
  args: {
    children: (
      <>
        Continue <ChevronRight className="ml-2 h-4 w-4" />
      </>
    ),
    variant: 'default',
    size: 'default',
  },
};

export const WithLeftIcon: Story = {
  args: {
    children: (
      <>
        <Download className="mr-2 h-4 w-4" />
        Download
      </>
    ),
    variant: 'outline',
    size: 'default',
  },
};

// States
export const Disabled: Story = {
  args: {
    children: 'Disabled Button',
    variant: 'default',
    size: 'default',
    disabled: true,
  },
};

export const Loading: Story = {
  args: {
    children: 'Loading...',
    variant: 'default',
    size: 'default',
    disabled: true,
  },
};

// Blue theme showcase - all variants together
export const AllVariants: Story = {
  render: () => (
    <div className="flex flex-wrap gap-4 p-4">
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Default Variants</h3>
        <div className="flex gap-2">
          <Button variant="default">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="outline">Outline</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="link">Link</Button>
          <Button variant="destructive">Destructive</Button>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Sizes</h3>
        <div className="flex items-center gap-2">
          <Button size="sm">Small</Button>
          <Button size="default">Default</Button>
          <Button size="lg">Large</Button>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Icon Buttons</h3>
        <div className="flex items-center gap-2">
          <Button size="icon-sm" variant="outline">
            <Plus className="h-3 w-3" />
          </Button>
          <Button size="icon" variant="default">
            <Download className="h-4 w-4" />
          </Button>
          <Button size="icon-lg" variant="destructive">
            <Trash2 className="h-5 w-5" />
          </Button>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-semibold">States</h3>
        <div className="flex gap-2">
          <Button disabled>Disabled</Button>
          <Button variant="outline" disabled>
            Disabled Outline
          </Button>
        </div>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Showcase of all button variants demonstrating the blue theme application.',
      },
    },
  },
};

// Upload workflow specific buttons (matching the application use case)
export const UploadWorkflow: Story = {
  render: () => (
    <div className="space-y-4 p-4">
      <h3 className="text-lg font-semibold">Upload Workflow Buttons</h3>
      <div className="flex flex-col gap-4">
        <div className="flex gap-2">
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Select Credit Card PDF
          </Button>
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Select Expense Report PDF
          </Button>
        </div>
        <Button variant="default" size="lg">
          Upload & Process Files
        </Button>
        <div className="flex gap-2">
          <Button variant="secondary">View Results</Button>
          <Button variant="ghost">Download Report</Button>
        </div>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Button examples specific to the credit card expense reconciliation workflow.',
      },
    },
  },
};