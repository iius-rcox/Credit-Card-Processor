/**
 * Card Component Contract Validation (T035)
 *
 * Tests that verify the Card component props work as documented in the API contract.
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '@/components/ui/card'

describe('Card Component Contract Validation', () => {
  describe('Card Root Component', () => {
    test('renders card with proper structure', () => {
      render(
        <Card data-testid="card-root">
          <div>Card Content</div>
        </Card>
      )

      const card = screen.getByTestId('card-root')
      expect(card).toBeInTheDocument()
      expect(card).toHaveClass('rounded-xl', 'border', 'bg-card', 'text-card-foreground', 'shadow')
    })

    test('applies custom className', () => {
      render(
        <Card className="custom-card-class" data-testid="custom-card">
          Content
        </Card>
      )

      const card = screen.getByTestId('custom-card')
      expect(card).toHaveClass('custom-card-class')
      // Should maintain base classes
      expect(card).toHaveClass('rounded-xl', 'border')
    })

    test('renders children content', () => {
      render(
        <Card>
          <div>First Child</div>
          <span>Second Child</span>
        </Card>
      )

      expect(screen.getByText('First Child')).toBeInTheDocument()
      expect(screen.getByText('Second Child')).toBeInTheDocument()
    })
  })

  describe('CardHeader Component', () => {
    test('renders header with proper spacing', () => {
      render(
        <CardHeader data-testid="card-header">
          <div>Header Content</div>
        </CardHeader>
      )

      const header = screen.getByTestId('card-header')
      expect(header).toBeInTheDocument()
      expect(header).toHaveClass('flex', 'flex-col', 'space-y-1.5', 'p-6')
    })

    test('applies custom className to header', () => {
      render(
        <CardHeader className="custom-header" data-testid="custom-header">
          Header
        </CardHeader>
      )

      const header = screen.getByTestId('custom-header')
      expect(header).toHaveClass('custom-header', 'flex', 'flex-col')
    })

    test('renders header children', () => {
      render(
        <CardHeader>
          <h2>Header Title</h2>
          <p>Header Description</p>
        </CardHeader>
      )

      expect(screen.getByText('Header Title')).toBeInTheDocument()
      expect(screen.getByText('Header Description')).toBeInTheDocument()
    })
  })

  describe('CardTitle Component', () => {
    test('renders title with proper typography', () => {
      render(
        <CardTitle data-testid="card-title">
          Test Card Title
        </CardTitle>
      )

      const title = screen.getByTestId('card-title')
      expect(title).toBeInTheDocument()
      expect(title).toHaveClass('font-semibold', 'leading-none', 'tracking-tight')
      expect(title.textContent).toBe('Test Card Title')
    })

    test('applies custom className to title', () => {
      render(
        <CardTitle className="custom-title" data-testid="custom-title">
          Custom Title
        </CardTitle>
      )

      const title = screen.getByTestId('custom-title')
      expect(title).toHaveClass('custom-title', 'font-semibold')
    })

    test('renders as div element by default', () => {
      render(<CardTitle>Title Text</CardTitle>)
      const title = screen.getByText('Title Text')
      expect(title.tagName).toBe('DIV')
    })
  })

  describe('CardDescription Component', () => {
    test('renders description with muted text', () => {
      render(
        <CardDescription data-testid="card-description">
          This is a card description
        </CardDescription>
      )

      const description = screen.getByTestId('card-description')
      expect(description).toBeInTheDocument()
      expect(description).toHaveClass('text-sm', 'text-muted-foreground')
      expect(description.textContent).toBe('This is a card description')
    })

    test('applies custom className to description', () => {
      render(
        <CardDescription className="custom-description">
          Description
        </CardDescription>
      )

      const description = screen.getByText('Description')
      expect(description).toHaveClass('custom-description', 'text-sm', 'text-muted-foreground')
    })
  })

  describe('CardContent Component', () => {
    test('renders content with proper padding', () => {
      render(
        <CardContent data-testid="card-content">
          <p>Main card content goes here</p>
        </CardContent>
      )

      const content = screen.getByTestId('card-content')
      expect(content).toBeInTheDocument()
      expect(content).toHaveClass('p-6', 'pt-0')
    })

    test('applies custom className to content', () => {
      render(
        <CardContent className="custom-content" data-testid="custom-content">
          Content
        </CardContent>
      )

      const content = screen.getByTestId('custom-content')
      expect(content).toHaveClass('custom-content', 'p-6', 'pt-0')
    })

    test('renders complex content structure', () => {
      render(
        <CardContent>
          <div>
            <h3>Content Title</h3>
            <p>Content paragraph</p>
            <ul>
              <li>List item</li>
            </ul>
          </div>
        </CardContent>
      )

      expect(screen.getByText('Content Title')).toBeInTheDocument()
      expect(screen.getByText('Content paragraph')).toBeInTheDocument()
      expect(screen.getByText('List item')).toBeInTheDocument()
    })
  })

  describe('CardFooter Component', () => {
    test('renders footer with flex layout', () => {
      render(
        <CardFooter data-testid="card-footer">
          <button>Action Button</button>
        </CardFooter>
      )

      const footer = screen.getByTestId('card-footer')
      expect(footer).toBeInTheDocument()
      expect(footer).toHaveClass('flex', 'items-center', 'p-6', 'pt-0')
    })

    test('applies custom className to footer', () => {
      render(
        <CardFooter className="custom-footer justify-end">
          Footer
        </CardFooter>
      )

      const footer = screen.getByText('Footer')
      expect(footer).toHaveClass('custom-footer', 'justify-end', 'flex', 'items-center')
    })
  })

  describe('Blue Theme Application', () => {
    test('card uses theme background and border colors', () => {
      render(<Card data-testid="themed-card">Themed Content</Card>)
      const card = screen.getByTestId('themed-card')
      expect(card).toHaveClass('bg-card', 'text-card-foreground', 'border')
    })

    test('description uses muted foreground color', () => {
      render(<CardDescription>Muted text</CardDescription>)
      const description = screen.getByText('Muted text')
      expect(description).toHaveClass('text-muted-foreground')
    })

    test('maintains theme consistency across components', () => {
      render(
        <Card data-testid="full-card">
          <CardHeader>
            <CardTitle>Theme Test</CardTitle>
            <CardDescription>Theme description</CardDescription>
          </CardHeader>
          <CardContent>
            Theme content
          </CardContent>
          <CardFooter>
            Theme footer
          </CardFooter>
        </Card>
      )

      const card = screen.getByTestId('full-card')
      expect(card).toHaveClass('bg-card', 'text-card-foreground')

      const description = screen.getByText('Theme description')
      expect(description).toHaveClass('text-muted-foreground')
    })
  })

  describe('Complete Card Structure', () => {
    test('renders full card composition correctly', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Complete Card</CardTitle>
            <CardDescription>This is a complete card example</CardDescription>
          </CardHeader>
          <CardContent>
            <p>This is the main content of the card.</p>
            <div>Additional content elements</div>
          </CardContent>
          <CardFooter>
            <button>Primary Action</button>
            <button>Secondary Action</button>
          </CardFooter>
        </Card>
      )

      // Verify all sections are present
      expect(screen.getByText('Complete Card')).toBeInTheDocument()
      expect(screen.getByText('This is a complete card example')).toBeInTheDocument()
      expect(screen.getByText('This is the main content of the card.')).toBeInTheDocument()
      expect(screen.getByText('Additional content elements')).toBeInTheDocument()
      expect(screen.getByText('Primary Action')).toBeInTheDocument()
      expect(screen.getByText('Secondary Action')).toBeInTheDocument()
    })

    test('maintains proper hierarchy and accessibility', () => {
      render(
        <Card role="article" aria-labelledby="card-title">
          <CardHeader>
            <CardTitle id="card-title">Accessible Card</CardTitle>
            <CardDescription>Accessible description</CardDescription>
          </CardHeader>
          <CardContent>
            Content with proper structure
          </CardContent>
        </Card>
      )

      const card = screen.getByRole('article')
      expect(card).toHaveAttribute('aria-labelledby', 'card-title')

      const title = screen.getByText('Accessible Card')
      expect(title).toHaveAttribute('id', 'card-title')
    })
  })

  describe('Responsive Behavior', () => {
    test('maintains responsive layout classes', () => {
      render(
        <Card className="w-full max-w-md" data-testid="responsive-card">
          <CardContent>Responsive content</CardContent>
        </Card>
      )

      const card = screen.getByTestId('responsive-card')
      expect(card).toHaveClass('w-full', 'max-w-md')
    })

    test('content adapts to container width', () => {
      render(
        <Card>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>Column 1</div>
            <div>Column 2</div>
          </CardContent>
        </Card>
      )

      const content = screen.getByText('Column 1').parentElement
      expect(content).toHaveClass('grid', 'grid-cols-1', 'md:grid-cols-2', 'gap-4')
    })
  })

  describe('Edge Cases', () => {
    test('handles empty card', () => {
      render(<Card data-testid="empty-card"></Card>)
      const card = screen.getByTestId('empty-card')
      expect(card).toBeInTheDocument()
      expect(card.textContent).toBe('')
    })

    test('handles card with only some sections', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Title Only</CardTitle>
          </CardHeader>
          <CardContent>Content without footer</CardContent>
        </Card>
      )

      expect(screen.getByText('Title Only')).toBeInTheDocument()
      expect(screen.getByText('Content without footer')).toBeInTheDocument()
      // Footer should not be present
      expect(screen.queryByRole('button')).not.toBeInTheDocument()
    })

    test('forwards refs correctly', () => {
      const cardRef = React.createRef<HTMLDivElement>()
      const headerRef = React.createRef<HTMLDivElement>()

      render(
        <Card ref={cardRef}>
          <CardHeader ref={headerRef}>
            <CardTitle>Ref Test</CardTitle>
          </CardHeader>
        </Card>
      )

      expect(cardRef.current).toBeInstanceOf(HTMLDivElement)
      expect(headerRef.current).toBeInstanceOf(HTMLDivElement)
    })
  })
})