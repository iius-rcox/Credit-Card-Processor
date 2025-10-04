import type { Meta, StoryObj } from '@storybook/react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Search, Eye, EyeOff, Mail, Lock, User, FileText } from 'lucide-react';
import { useState } from 'react';

const meta: Meta<typeof Input> = {
  title: 'Components/Input',
  component: Input,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A flexible input component with blue theme focus states and validation styling.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    type: {
      control: { type: 'select' },
      options: ['text', 'email', 'password', 'number', 'tel', 'url', 'search', 'file'],
      description: 'The type of input',
    },
    placeholder: {
      control: 'text',
      description: 'Placeholder text for the input',
    },
    disabled: {
      control: 'boolean',
      description: 'Whether the input is disabled',
    },
    className: {
      control: 'text',
      description: 'Additional CSS classes',
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

// Basic input
export const Default: Story = {
  args: {
    placeholder: 'Type something...',
    type: 'text',
  },
};

export const WithLabel: Story = {
  render: (args) => (
    <div className="space-y-2 w-64">
      <Label htmlFor="input-example">Email Address</Label>
      <Input id="input-example" {...args} />
    </div>
  ),
  args: {
    type: 'email',
    placeholder: 'Enter your email',
  },
};

export const Password: Story = {
  render: () => {
    const [showPassword, setShowPassword] = useState(false);

    return (
      <div className="space-y-2 w-64">
        <Label htmlFor="password">Password</Label>
        <div className="relative">
          <Input
            id="password"
            type={showPassword ? 'text' : 'password'}
            placeholder="Enter your password"
            className="pr-10"
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute inset-y-0 right-0 flex items-center pr-3 text-muted-foreground hover:text-foreground"
          >
            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>
      </div>
    );
  },
};

export const WithIcon: Story = {
  render: () => (
    <div className="space-y-2 w-64">
      <Label htmlFor="search">Search</Label>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          id="search"
          type="search"
          placeholder="Search documents..."
          className="pl-10"
        />
      </div>
    </div>
  ),
};

export const FileInput: Story = {
  render: () => (
    <div className="space-y-2 w-80">
      <Label htmlFor="file-upload">Upload Document</Label>
      <Input
        id="file-upload"
        type="file"
        accept=".pdf,.doc,.docx"
        className="file:mr-4 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-primary file:text-primary-foreground hover:file:bg-primary/90"
      />
      <p className="text-xs text-muted-foreground">PDF, DOC, or DOCX files only</p>
    </div>
  ),
};

export const Disabled: Story = {
  args: {
    placeholder: 'Disabled input',
    disabled: true,
    value: 'This input is disabled',
  },
};

export const ErrorState: Story = {
  render: () => (
    <div className="space-y-2 w-64">
      <Label htmlFor="error-input">Email Address</Label>
      <Input
        id="error-input"
        type="email"
        placeholder="Enter your email"
        aria-invalid={true}
        defaultValue="invalid-email"
        className="border-destructive focus-visible:ring-destructive/20"
      />
      <p className="text-sm text-destructive">Please enter a valid email address</p>
    </div>
  ),
};

export const Sizes: Story = {
  render: () => (
    <div className="space-y-4 w-80">
      <div className="space-y-2">
        <Label>Small Input</Label>
        <Input
          placeholder="Small input"
          className="h-8 text-xs"
        />
      </div>
      <div className="space-y-2">
        <Label>Default Input</Label>
        <Input placeholder="Default input" />
      </div>
      <div className="space-y-2">
        <Label>Large Input</Label>
        <Input
          placeholder="Large input"
          className="h-11 text-base"
        />
      </div>
    </div>
  ),
};

// Input types showcase
export const InputTypes: Story = {
  render: () => (
    <div className="space-y-4 w-80">
      <h3 className="text-lg font-semibold mb-4">Input Types</h3>

      <div className="space-y-2">
        <Label htmlFor="text-input">Text</Label>
        <Input id="text-input" type="text" placeholder="Enter text" />
      </div>

      <div className="space-y-2">
        <Label htmlFor="email-input">Email</Label>
        <Input id="email-input" type="email" placeholder="user@example.com" />
      </div>

      <div className="space-y-2">
        <Label htmlFor="number-input">Number</Label>
        <Input id="number-input" type="number" placeholder="Enter a number" />
      </div>

      <div className="space-y-2">
        <Label htmlFor="tel-input">Phone</Label>
        <Input id="tel-input" type="tel" placeholder="+1 (555) 123-4567" />
      </div>

      <div className="space-y-2">
        <Label htmlFor="url-input">URL</Label>
        <Input id="url-input" type="url" placeholder="https://example.com" />
      </div>

      <div className="space-y-2">
        <Label htmlFor="date-input">Date</Label>
        <Input id="date-input" type="date" />
      </div>
    </div>
  ),
  parameters: {
    layout: 'padded',
  },
};

// Upload workflow specific inputs
export const UploadWorkflow: Story = {
  render: () => (
    <Card className="w-96">
      <CardHeader>
        <CardTitle>Document Upload Form</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="credit-card-file">Credit Card Statement</Label>
          <div className="relative">
            <FileText className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              id="credit-card-file"
              type="file"
              accept=".pdf"
              className="pl-10 file:mr-4 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-primary file:text-primary-foreground hover:file:bg-primary/90"
            />
          </div>
          <p className="text-xs text-muted-foreground">Upload your credit card PDF statement</p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="expense-report-file">Expense Report</Label>
          <div className="relative">
            <FileText className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              id="expense-report-file"
              type="file"
              accept=".pdf,.csv,.xlsx"
              className="pl-10 file:mr-4 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-primary file:text-primary-foreground hover:file:bg-primary/90"
            />
          </div>
          <p className="text-xs text-muted-foreground">Upload your expense report (PDF, CSV, or XLSX)</p>
        </div>

        <div className="pt-4">
          <Button className="w-full">Process Documents</Button>
        </div>
      </CardContent>
    </Card>
  ),
};

// Form example with validation
export const FormExample: Story = {
  render: () => (
    <Card className="w-96">
      <CardHeader>
        <CardTitle>User Registration</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="full-name">Full Name</Label>
          <div className="relative">
            <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              id="full-name"
              type="text"
              placeholder="John Doe"
              className="pl-10"
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="user-email">Email</Label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              id="user-email"
              type="email"
              placeholder="john@example.com"
              className="pl-10"
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="user-password">Password</Label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              id="user-password"
              type="password"
              placeholder="Enter password"
              className="pl-10"
            />
          </div>
        </div>

        <div className="pt-4">
          <Button className="w-full">Create Account</Button>
        </div>
      </CardContent>
    </Card>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Example form showing input components with icons and labels in a real-world context.',
      },
    },
  },
};