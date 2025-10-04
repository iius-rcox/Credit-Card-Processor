import type { Meta, StoryObj } from '@storybook/react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Asterisk, Info, HelpCircle } from 'lucide-react';

const meta: Meta<typeof Label> = {
  title: 'Components/Label',
  component: Label,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A label component that provides accessible labeling for form controls.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    htmlFor: {
      control: 'text',
      description: 'The id of the form control this label is associated with',
    },
    className: {
      control: 'text',
      description: 'Additional CSS classes',
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

// Basic label
export const Default: Story = {
  args: {
    children: 'Email Address',
  },
};

// Label with input
export const WithInput: Story = {
  render: () => (
    <div className="space-y-2 w-64">
      <Label htmlFor="email-input">Email Address</Label>
      <Input id="email-input" type="email" placeholder="Enter your email" />
    </div>
  ),
};

// Required field label
export const Required: Story = {
  render: () => (
    <div className="space-y-2 w-64">
      <Label htmlFor="required-input" className="flex items-center gap-1">
        Full Name
        <Asterisk className="h-3 w-3 text-destructive" />
      </Label>
      <Input id="required-input" type="text" placeholder="Enter your full name" />
    </div>
  ),
};

// Label with help text
export const WithHelpText: Story = {
  render: () => (
    <div className="space-y-2 w-80">
      <Label htmlFor="password-input" className="flex items-center gap-2">
        Password
        <HelpCircle className="h-4 w-4 text-muted-foreground" />
      </Label>
      <Input id="password-input" type="password" placeholder="Enter password" />
      <p className="text-xs text-muted-foreground">
        Password must be at least 8 characters long with uppercase, lowercase, and numbers.
      </p>
    </div>
  ),
};

// Label with info icon
export const WithInfoIcon: Story = {
  render: () => (
    <div className="space-y-2 w-80">
      <Label htmlFor="tax-id" className="flex items-center gap-2">
        Tax ID Number
        <Info className="h-4 w-4 text-primary" />
      </Label>
      <Input id="tax-id" type="text" placeholder="XX-XXXXXXX" />
      <p className="text-xs text-muted-foreground">
        Enter your federal tax identification number for expense reporting.
      </p>
    </div>
  ),
};




// Disabled label
export const Disabled: Story = {
  render: () => (
    <div className="space-y-2 w-64" data-disabled="true">
      <Label htmlFor="disabled-input" className="opacity-50">
        Disabled Field
      </Label>
      <Input id="disabled-input" disabled placeholder="This is disabled" />
    </div>
  ),
};

// Different label sizes
export const Sizes: Story = {
  render: () => (
    <div className="space-y-6 w-80">
      <div className="space-y-2">
        <Label className="text-xs">Extra Small Label</Label>
        <Input placeholder="Extra small label" />
      </div>

      <div className="space-y-2">
        <Label className="text-sm">Small Label (Default)</Label>
        <Input placeholder="Small label" />
      </div>

      <div className="space-y-2">
        <Label className="text-base">Medium Label</Label>
        <Input placeholder="Medium label" />
      </div>

      <div className="space-y-2">
        <Label className="text-lg">Large Label</Label>
        <Input placeholder="Large label" />
      </div>
    </div>
  ),
};

// Upload form labels (matching the application context)
export const UploadFormLabels: Story = {
  render: () => (
    <Card className="w-96">
      <CardHeader>
        <CardTitle>Document Upload</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="credit-card-upload" className="flex items-center gap-2">
            Credit Card Statement
            <Asterisk className="h-3 w-3 text-destructive" />
          </Label>
          <Input
            id="credit-card-upload"
            type="file"
            accept=".pdf"
            className="file:mr-4 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-primary file:text-primary-foreground hover:file:bg-primary/90"
          />
          <p className="text-xs text-muted-foreground">
            Upload your credit card PDF statement for the reporting period.
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="expense-upload" className="flex items-center gap-2">
            Expense Report
            <Asterisk className="h-3 w-3 text-destructive" />
          </Label>
          <Input
            id="expense-upload"
            type="file"
            accept=".pdf,.csv,.xlsx"
            className="file:mr-4 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-primary file:text-primary-foreground hover:file:bg-primary/90"
          />
          <p className="text-xs text-muted-foreground">
            Upload your expense report in PDF, CSV, or Excel format.
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="reporting-period" className="flex items-center gap-2">
            Reporting Period
            <Info className="h-4 w-4 text-primary" />
          </Label>
          <Input
            id="reporting-period"
            type="text"
            placeholder="e.g., January 2024"
            className="w-full"
          />
          <p className="text-xs text-muted-foreground">
            Enter the period these expenses cover for proper categorization.
          </p>
        </div>

      </CardContent>
    </Card>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Label examples specific to the document upload and expense processing workflow.',
      },
    },
  },
};

// All label variations showcase
export const AllVariations: Story = {
  render: () => (
    <div className="space-y-8 p-6">
      <h3 className="text-lg font-semibold">Label Variations</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Basic labels */}
        <div className="space-y-4">
          <h4 className="font-medium text-muted-foreground">Basic Labels</h4>
          <div className="space-y-3">
            <div className="space-y-1">
              <Label>Standard Label</Label>
              <Input placeholder="Enter text" />
            </div>

            <div className="space-y-1">
              <Label className="flex items-center gap-1">
                Required Field
                <Asterisk className="h-3 w-3 text-destructive" />
              </Label>
              <Input placeholder="Required field" />
            </div>
          </div>
        </div>

        {/* Additional labels */}
        <div className="space-y-4">
          <h4 className="font-medium text-muted-foreground">Additional Examples</h4>
          <div className="space-y-3">
            <div className="space-y-1">
              <Label className="text-xs">Small Label</Label>
              <Input placeholder="Small input" className="text-xs" />
            </div>
            <div className="space-y-1">
              <Label className="text-lg">Large Label</Label>
              <Input placeholder="Large input" className="text-lg" />
            </div>
          </div>
        </div>
      </div>
    </div>
  ),
  parameters: {
    layout: 'fullscreen',
  },
};