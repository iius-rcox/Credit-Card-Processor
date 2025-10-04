import type { Meta, StoryObj } from '@storybook/react'
import { ResultsPanel } from '@/components/results-panel'
import type { SessionResponse, ReportsResponse } from '@/lib/types'

const meta: Meta<typeof ResultsPanel> = {
  title: 'Integration/ResultsPanel',
  component: ResultsPanel,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: 'Results panel component displaying expense reconciliation results using shadcn/ui components with blue theme.',
      },
    },
  },
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof meta>

// Mock data for stories
const mockSessionData: SessionResponse = {
  session_id: 'demo-session-123',
  employees: [
    {
      employee_id: 'EMP001',
      name: 'John Smith',
      card_number: '**** 1234',
      completion_status: 'complete',
      expenses: [
        {
          transaction_id: 'TXN001',
          transaction_date: '2024-01-15',
          transaction_amount: 125.50,
          transaction_name: 'Office Supplies Store',
          status: 'Complete',
          gl_code: 'OFFICE-SUP',
          receipt_url: 'https://example.com/receipt1.pdf',
        },
        {
          transaction_id: 'TXN002',
          transaction_date: '2024-01-16',
          transaction_amount: 75.00,
          transaction_name: 'Business Lunch',
          status: 'Complete',
          gl_code: 'MEALS',
          receipt_url: 'https://example.com/receipt2.pdf',
        },
      ],
      receipts: [
        {
          receipt_id: 'REC001',
          transaction_id: 'TXN001',
          receipt_url: 'https://example.com/receipt1.pdf',
        },
        {
          receipt_id: 'REC002',
          transaction_id: 'TXN002',
          receipt_url: 'https://example.com/receipt2.pdf',
        },
      ],
    },
    {
      employee_id: 'EMP002',
      name: 'Jane Doe',
      card_number: '**** 5678',
      completion_status: 'incomplete',
      expenses: [
        {
          transaction_id: 'TXN003',
          transaction_date: '2024-01-17',
          transaction_amount: 89.99,
          transaction_name: 'Software License',
          status: 'Missing Receipt',
          gl_code: 'SOFTWARE',
          receipt_url: null,
        },
        {
          transaction_id: 'TXN004',
          transaction_date: '2024-01-18',
          transaction_amount: 250.00,
          transaction_name: 'Conference Registration',
          status: 'Missing Both',
          gl_code: null,
          receipt_url: null,
        },
        {
          transaction_id: 'TXN005',
          transaction_date: '2024-01-19',
          transaction_amount: 45.00,
          transaction_name: 'Taxi Service',
          status: 'Missing GL Code',
          gl_code: null,
          receipt_url: 'https://example.com/receipt3.pdf',
        },
      ],
      receipts: [
        {
          receipt_id: 'REC003',
          transaction_id: 'TXN005',
          receipt_url: 'https://example.com/receipt3.pdf',
        },
      ],
    },
  ],
}

const mockReportsData: ReportsResponse = {
  summary: {
    total_employees: 2,
    complete_employees: 1,
    incomplete_employees: 1,
    total_expenses: 5,
    complete_expenses: 2,
    expenses_missing_receipts: 1,
    expenses_missing_gl_codes: 1,
    expenses_missing_both: 1,
  },
  excel_report: 'https://example.com/report.xlsx',
  csv_export: 'https://example.com/export.csv',
}

export const Default: Story = {
  args: {
    sessionData: mockSessionData,
    reportsData: mockReportsData,
    onDownloadExcel: () => {
      console.log('Download Excel clicked')
      alert('Excel report downloaded!')
    },
    onDownloadCSV: () => {
      console.log('Download CSV clicked')
      alert('CSV export downloaded!')
    },
    onUploadNewReceipts: () => {
      console.log('Upload new receipts clicked')
      alert('Upload new receipts dialog opened!')
    },
  },
}

export const AllComplete: Story = {
  args: {
    sessionData: {
      ...mockSessionData,
      employees: [
        {
          employee_id: 'EMP001',
          name: 'John Smith',
          card_number: '**** 1234',
          completion_status: 'complete',
          expenses: [
            {
              transaction_id: 'TXN001',
              transaction_date: '2024-01-15',
              transaction_amount: 125.50,
              transaction_name: 'Office Supplies',
              status: 'Complete',
              gl_code: 'OFFICE-SUP',
              receipt_url: 'https://example.com/receipt1.pdf',
            },
          ],
          receipts: [
            {
              receipt_id: 'REC001',
              transaction_id: 'TXN001',
              receipt_url: 'https://example.com/receipt1.pdf',
            },
          ],
        },
        {
          employee_id: 'EMP002',
          name: 'Jane Doe',
          card_number: '**** 5678',
          completion_status: 'complete',
          expenses: [
            {
              transaction_id: 'TXN002',
              transaction_date: '2024-01-16',
              transaction_amount: 75.00,
              transaction_name: 'Business Lunch',
              status: 'Complete',
              gl_code: 'MEALS',
              receipt_url: 'https://example.com/receipt2.pdf',
            },
          ],
          receipts: [
            {
              receipt_id: 'REC002',
              transaction_id: 'TXN002',
              receipt_url: 'https://example.com/receipt2.pdf',
            },
          ],
        },
      ],
    },
    reportsData: {
      summary: {
        total_employees: 2,
        complete_employees: 2,
        incomplete_employees: 0,
        total_expenses: 2,
        complete_expenses: 2,
        expenses_missing_receipts: 0,
        expenses_missing_gl_codes: 0,
        expenses_missing_both: 0,
      },
      excel_report: 'https://example.com/complete-report.xlsx',
      csv_export: 'https://example.com/complete-export.csv',
    },
    onDownloadExcel: () => console.log('All complete - Excel download'),
    onDownloadCSV: () => console.log('All complete - CSV download'),
    onUploadNewReceipts: () => console.log('All complete - Upload new receipts'),
  },
}

export const LargeDataset: Story = {
  args: {
    sessionData: {
      session_id: 'large-dataset-session',
      employees: Array.from({ length: 10 }, (_, i) => ({
        employee_id: `EMP${(i + 1).toString().padStart(3, '0')}`,
        name: `Employee ${i + 1}`,
        card_number: `**** ${(1000 + i).toString()}`,
        completion_status: i % 3 === 0 ? 'complete' : 'incomplete',
        expenses: Array.from({ length: Math.floor(Math.random() * 5) + 1 }, (_, j) => ({
          transaction_id: `TXN${i}${j}`,
          transaction_date: '2024-01-15',
          transaction_amount: Math.round(Math.random() * 500 * 100) / 100,
          transaction_name: ['Office Supplies', 'Business Lunch', 'Software License', 'Travel', 'Equipment'][j % 5],
          status: ['Complete', 'Missing Receipt', 'Missing GL Code', 'Missing Both'][Math.floor(Math.random() * 4)],
          gl_code: Math.random() > 0.3 ? 'GL-CODE' : null,
          receipt_url: Math.random() > 0.3 ? 'https://example.com/receipt.pdf' : null,
        })),
        receipts: [],
      })),
    },
    reportsData: {
      summary: {
        total_employees: 10,
        complete_employees: 3,
        incomplete_employees: 7,
        total_expenses: 35,
        complete_expenses: 12,
        expenses_missing_receipts: 8,
        expenses_missing_gl_codes: 7,
        expenses_missing_both: 8,
      },
      excel_report: 'https://example.com/large-report.xlsx',
      csv_export: 'https://example.com/large-export.csv',
    },
    onDownloadExcel: () => console.log('Large dataset - Excel download'),
    onDownloadCSV: () => console.log('Large dataset - CSV download'),
    onUploadNewReceipts: () => console.log('Large dataset - Upload new receipts'),
  },
}

export const EmptyResults: Story = {
  args: {
    sessionData: {
      session_id: 'empty-session',
      employees: [],
    },
    reportsData: {
      summary: {
        total_employees: 0,
        complete_employees: 0,
        incomplete_employees: 0,
        total_expenses: 0,
        complete_expenses: 0,
        expenses_missing_receipts: 0,
        expenses_missing_gl_codes: 0,
        expenses_missing_both: 0,
      },
      excel_report: null,
      csv_export: null,
    },
    onDownloadExcel: () => console.log('Empty results - Excel download'),
    onDownloadCSV: () => console.log('Empty results - CSV download'),
    onUploadNewReceipts: () => console.log('Empty results - Upload new receipts'),
  },
}

export const BlueThemeShowcase: Story = {
  args: {
    sessionData: mockSessionData,
    reportsData: mockReportsData,
    onDownloadExcel: () => console.log('Theme demo - Excel download'),
    onDownloadCSV: () => console.log('Theme demo - CSV download'),
    onUploadNewReceipts: () => console.log('Theme demo - Upload new receipts'),
  },
  render: (args) => (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-lg font-semibold mb-2">Blue Theme Integration</h3>
        <p className="text-sm text-muted-foreground mb-4">
          Demonstrates how the results panel uses the blue theme across all components.
        </p>
      </div>

      <ResultsPanel {...args} />

      <div className="max-w-2xl mx-auto space-y-2 text-sm">
        <h4 className="font-medium">Theme Elements Demonstrated:</h4>
        <ul className="list-disc list-inside space-y-1 text-muted-foreground">
          <li>Card components with blue-tinted borders</li>
          <li>Primary buttons with blue background</li>
          <li>Secondary and outline button variants</li>
          <li>Status badges with semantic colors</li>
          <li>Typography using theme foreground colors</li>
          <li>Grid layouts responsive to container width</li>
        </ul>
      </div>
    </div>
  ),
}

export const InteractiveDemo: Story = {
  args: {
    sessionData: mockSessionData,
    reportsData: mockReportsData,
    onDownloadExcel: () => {
      alert('📊 Excel report with 3 incomplete expenses downloaded!')
      console.log('Interactive demo - Excel downloaded')
    },
    onDownloadCSV: () => {
      alert('📋 CSV export with 2 complete expenses downloaded!')
      console.log('Interactive demo - CSV downloaded')
    },
    onUploadNewReceipts: () => {
      alert('📁 Upload new receipts dialog would open here!')
      console.log('Interactive demo - Upload new receipts')
    },
  },
  render: (args) => (
    <div className="space-y-4">
      <div className="text-center">
        <h3 className="text-lg font-semibold mb-2">Interactive Results Panel</h3>
        <p className="text-sm text-muted-foreground mb-4">
          Click the action buttons to see the component interactions.
          This demonstrates a realistic expense reconciliation scenario.
        </p>
      </div>

      <ResultsPanel {...args} />

      <div className="text-center text-xs text-muted-foreground max-w-4xl mx-auto">
        <p>
          💡 This demo shows a typical reconciliation result with mixed completion status.
          The component demonstrates responsive layout, status indicators, and action buttons.
        </p>
      </div>
    </div>
  ),
}

export const ResponsiveDemo: Story = {
  args: {
    sessionData: mockSessionData,
    reportsData: mockReportsData,
    onDownloadExcel: () => console.log('Responsive demo - Excel download'),
    onDownloadCSV: () => console.log('Responsive demo - CSV download'),
    onUploadNewReceipts: () => console.log('Responsive demo - Upload new receipts'),
  },
  render: (args) => (
    <div className="space-y-4">
      <div className="text-center">
        <h3 className="text-lg font-semibold mb-2">Responsive Layout</h3>
        <p className="text-sm text-muted-foreground mb-4">
          The results panel adapts to different screen sizes while maintaining the blue theme.
        </p>
      </div>

      <div className="space-y-8">
        {/* Mobile simulation */}
        <div className="max-w-sm mx-auto border rounded-lg p-4">
          <h4 className="text-sm font-medium mb-2 text-center">Mobile (max-w-sm)</h4>
          <div className="scale-75 origin-top">
            <ResultsPanel {...args} />
          </div>
        </div>

        {/* Tablet simulation */}
        <div className="max-w-2xl mx-auto border rounded-lg p-4">
          <h4 className="text-sm font-medium mb-2 text-center">Tablet (max-w-2xl)</h4>
          <div className="scale-90 origin-top">
            <ResultsPanel {...args} />
          </div>
        </div>

        {/* Desktop simulation */}
        <div className="max-w-6xl mx-auto border rounded-lg p-4">
          <h4 className="text-sm font-medium mb-2 text-center">Desktop (max-w-6xl)</h4>
          <ResultsPanel {...args} />
        </div>
      </div>
    </div>
  ),
}

export const StatusVariations: Story = {
  render: () => {
    const scenarios = [
      {
        title: 'All Complete',
        data: {
          summary: { total_employees: 1, complete_employees: 1, incomplete_employees: 0, total_expenses: 1, complete_expenses: 1, expenses_missing_receipts: 0, expenses_missing_gl_codes: 0, expenses_missing_both: 0 },
          excel_report: 'report.xlsx',
          csv_export: 'export.csv',
        },
      },
      {
        title: 'Mixed Status',
        data: mockReportsData,
      },
      {
        title: 'All Incomplete',
        data: {
          summary: { total_employees: 1, complete_employees: 0, incomplete_employees: 1, total_expenses: 3, complete_expenses: 0, expenses_missing_receipts: 1, expenses_missing_gl_codes: 1, expenses_missing_both: 1 },
          excel_report: 'report.xlsx',
          csv_export: null,
        },
      },
    ]

    return (
      <div className="space-y-8">
        <div className="text-center">
          <h3 className="text-lg font-semibold mb-4">Status Variations</h3>
          <p className="text-sm text-muted-foreground mb-6">
            Different reconciliation outcomes and their visual representations.
          </p>
        </div>

        {scenarios.map((scenario, index) => (
          <div key={index} className="space-y-4">
            <h4 className="text-center font-medium">{scenario.title}</h4>
            <div className="border rounded-lg p-4">
              <ResultsPanel
                sessionData={{ session_id: `scenario-${index}`, employees: [] }}
                reportsData={scenario.data}
                onDownloadExcel={() => console.log(`${scenario.title} - Excel download`)}
                onDownloadCSV={() => console.log(`${scenario.title} - CSV download`)}
                onUploadNewReceipts={() => console.log(`${scenario.title} - Upload new receipts`)}
              />
            </div>
          </div>
        ))}
      </div>
    )
  },
}