import type { Meta, StoryObj } from '@storybook/react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle, CardAction } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileText, Upload, CheckCircle, AlertCircle, MoreHorizontal, Download } from 'lucide-react';

const meta: Meta<typeof Card> = {
  title: 'Components/Card',
  component: Card,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A versatile card component with header, content, and footer sections using blue theme.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    className: {
      control: 'text',
      description: 'Additional CSS classes to apply to the card',
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

// Basic card structure
export const Default: Story = {
  render: () => (
    <Card className="w-96">
      <CardHeader>
        <CardTitle>Card Title</CardTitle>
        <CardDescription>Card description goes here. This explains what the card is about.</CardDescription>
      </CardHeader>
      <CardContent>
        <p>This is the main content of the card. It can contain any elements you need.</p>
      </CardContent>
      <CardFooter>
        <Button>Action</Button>
      </CardFooter>
    </Card>
  ),
};

// Card with action button in header
export const WithHeaderAction: Story = {
  render: () => (
    <Card className="w-96">
      <CardHeader>
        <CardTitle>Settings</CardTitle>
        <CardDescription>Manage your account settings and preferences.</CardDescription>
        <CardAction>
          <Button variant="ghost" size="icon">
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </CardAction>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span>Email notifications</span>
            <span className="text-muted-foreground">Enabled</span>
          </div>
          <div className="flex justify-between">
            <span>Dark mode</span>
            <span className="text-muted-foreground">Disabled</span>
          </div>
        </div>
      </CardContent>
    </Card>
  ),
};

// Upload workflow cards
export const UploadCard: Story = {
  render: () => (
    <Card className="w-96">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Upload className="h-5 w-5 text-primary" />
          <CardTitle>Upload Documents</CardTitle>
        </div>
        <CardDescription>Upload your credit card statement and expense report for processing.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="border-2 border-dashed border-border rounded-lg p-6 text-center">
            <FileText className="mx-auto h-12 w-12 text-muted-foreground mb-2" />
            <p className="text-sm text-muted-foreground">Drag and drop files here, or click to browse</p>
          </div>
        </div>
      </CardContent>
      <CardFooter className="gap-2">
        <Button variant="outline" className="flex-1">
          <FileText className="mr-2 h-4 w-4" />
          Credit Card PDF
        </Button>
        <Button variant="outline" className="flex-1">
          <FileText className="mr-2 h-4 w-4" />
          Expense Report PDF
        </Button>
      </CardFooter>
    </Card>
  ),
};

// Progress card
export const ProgressCard: Story = {
  render: () => (
    <Card className="w-96">
      <CardHeader>
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 bg-primary rounded-full animate-pulse" />
          <CardTitle>Processing Files</CardTitle>
        </div>
        <CardDescription>Analyzing your documents and matching transactions...</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-green-500" />
            <span className="text-sm">Credit card PDF uploaded</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-green-500" />
            <span className="text-sm">Expense report PDF uploaded</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-4 w-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            <span className="text-sm">Matching transactions...</span>
          </div>
        </div>
        <div className="mt-4">
          <div className="bg-secondary rounded-full h-2">
            <div className="bg-primary h-2 rounded-full w-3/4 transition-all duration-300" />
          </div>
          <p className="text-xs text-muted-foreground mt-1">75% complete</p>
        </div>
      </CardContent>
    </Card>
  ),
};

// Results card
export const ResultsCard: Story = {
  render: () => (
    <Card className="w-96">
      <CardHeader>
        <div className="flex items-center gap-2">
          <CheckCircle className="h-5 w-5 text-green-500" />
          <CardTitle>Processing Complete</CardTitle>
        </div>
        <CardDescription>Successfully matched 15 out of 18 transactions.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm">Total transactions</span>
            <span className="text-sm font-medium text-muted-foreground">18</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm">Matched</span>
            <span className="text-sm font-medium text-green-600">15</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm">Unmatched</span>
            <span className="text-sm font-medium text-destructive">3</span>
          </div>
        </div>
      </CardContent>
      <CardFooter className="gap-2">
        <Button variant="outline" className="flex-1">
          <Download className="mr-2 h-4 w-4" />
          Download Report
        </Button>
        <Button className="flex-1">View Details</Button>
      </CardFooter>
    </Card>
  ),
};

// Error card
export const ErrorCard: Story = {
  render: () => (
    <Card className="w-96 border-destructive">
      <CardHeader>
        <div className="flex items-center gap-2">
          <AlertCircle className="h-5 w-5 text-destructive" />
          <CardTitle className="text-destructive">Processing Failed</CardTitle>
        </div>
        <CardDescription>There was an error processing your documents. Please try again.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <p className="text-sm text-muted-foreground">Error details:</p>
          <div className="bg-destructive/10 border border-destructive/20 rounded-md p-3">
            <p className="text-sm text-destructive">Unable to parse credit card PDF. The file may be corrupted or in an unsupported format.</p>
          </div>
        </div>
      </CardContent>
      <CardFooter className="gap-2">
        <Button variant="outline" className="flex-1">Try Again</Button>
        <Button variant="destructive" className="flex-1">Report Issue</Button>
      </CardFooter>
    </Card>
  ),
};

// Simple content card
export const SimpleContent: Story = {
  render: () => (
    <Card className="w-80">
      <CardContent>
        <div className="flex items-center gap-4">
          <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
            <FileText className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h3 className="font-semibold">Document Analysis</h3>
            <p className="text-sm text-muted-foreground">AI-powered transaction matching</p>
          </div>
        </div>
      </CardContent>
    </Card>
  ),
};

// All card parts showcase
export const AllParts: Story = {
  render: () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold">Card Components Showcase</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Basic structure */}
        <Card>
          <CardHeader>
            <CardTitle>Basic Card</CardTitle>
            <CardDescription>With header, content, and footer</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm">This demonstrates the basic card structure with all parts.</p>
          </CardContent>
          <CardFooter>
            <Button size="sm">Action</Button>
          </CardFooter>
        </Card>

        {/* With action */}
        <Card>
          <CardHeader>
            <CardTitle>With Header Action</CardTitle>
            <CardDescription>Card with action button in header</CardDescription>
            <CardAction>
              <Button variant="ghost" size="icon-sm">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </CardAction>
          </CardHeader>
          <CardContent>
            <p className="text-sm">The action button is positioned in the top-right corner.</p>
          </CardContent>
        </Card>

        {/* Content only */}
        <Card>
          <CardContent>
            <div className="text-center py-4">
              <CheckCircle className="h-8 w-8 text-green-500 mx-auto mb-2" />
              <p className="font-medium">Content Only</p>
              <p className="text-sm text-muted-foreground">Sometimes you just need content</p>
            </div>
          </CardContent>
        </Card>

        {/* Minimal */}
        <Card>
          <CardContent>
            <div className="flex items-center justify-between">
              <span className="font-medium">Minimal Card</span>
              <span className="text-xs font-medium text-primary px-2 py-1 bg-primary/10 rounded-md">New</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  ),
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        story: 'Showcase of different card compositions and their blue theme application.',
      },
    },
  },
};