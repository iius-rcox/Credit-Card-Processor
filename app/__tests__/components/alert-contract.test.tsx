/**
 * Alert Component Contract Validation (T037)
 *
 * Tests that verify the Alert component props work as documented in the API contract.
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert'

describe('Alert Component Contract Validation', () => {
  describe('Alert Root Component', () => {
    test('renders alert with default variant', () => {
      render(
        <Alert data-testid="default-alert">
          <div>Default alert content</div>
        </Alert>
      )

      const alert = screen.getByTestId('default-alert')
      expect(alert).toBeInTheDocument()
      expect(alert).toHaveAttribute('role', 'alert')
      expect(alert).toHaveClass(
        'relative',
        'w-full',
        'rounded-lg',
        'border',
        'px-4',
        'py-3',
        'text-sm'
      )
    })

    test('renders destructive variant', () => {
      render(
        <Alert variant="destructive" data-testid="destructive-alert">
          <div>Destructive alert content</div>
        </Alert>
      )

      const alert = screen.getByTestId('destructive-alert')
      expect(alert).toBeInTheDocument()
      expect(alert).toHaveAttribute('role', 'alert')
      expect(alert).toHaveClass('text-destructive')
    })

    test('applies custom className', () => {
      render(
        <Alert className="custom-alert-class" data-testid="custom-alert">
          Content
        </Alert>
      )

      const alert = screen.getByTestId('custom-alert')
      expect(alert).toHaveClass('custom-alert-class')
      // Should maintain base classes
      expect(alert).toHaveClass('relative', 'w-full', 'rounded-lg')
    })

    test('renders children content', () => {
      render(
        <Alert>
          <div>First child</div>
          <span>Second child</span>
        </Alert>
      )

      expect(screen.getByText('First child')).toBeInTheDocument()
      expect(screen.getByText('Second child')).toBeInTheDocument()
    })

    test('forwards additional props', () => {
      render(
        <Alert
          data-testid="props-alert"
          id="custom-alert-id"
          aria-label="Custom alert label"
        >
          Props test
        </Alert>
      )

      const alert = screen.getByTestId('props-alert')
      expect(alert).toHaveAttribute('id', 'custom-alert-id')
      expect(alert).toHaveAttribute('aria-label', 'Custom alert label')
    })
  })

  describe('AlertTitle Component', () => {
    test('renders title with proper styling', () => {
      render(
        <AlertTitle data-testid="alert-title">
          Alert Title Text
        </AlertTitle>
      )

      const title = screen.getByTestId('alert-title')
      expect(title).toBeInTheDocument()
      expect(title).toHaveClass(
        'col-start-2',
        'line-clamp-1',
        'min-h-4',
        'font-medium',
        'tracking-tight'
      )
      expect(title.textContent).toBe('Alert Title Text')
    })

    test('applies custom className to title', () => {
      render(
        <AlertTitle className="custom-title-class" data-testid="custom-title">
          Custom Title
        </AlertTitle>
      )

      const title = screen.getByTestId('custom-title')
      expect(title).toHaveClass('custom-title-class')
      // Should maintain base classes
      expect(title).toHaveClass('font-medium', 'tracking-tight')
    })

    test('renders as div element', () => {
      render(<AlertTitle>Title Element</AlertTitle>)
      const title = screen.getByText('Title Element')
      expect(title.tagName).toBe('DIV')
    })

    test('handles complex children', () => {
      render(
        <AlertTitle>
          <span>Complex</span>
          <strong>Title</strong>
        </AlertTitle>
      )

      expect(screen.getByText('Complex')).toBeInTheDocument()
      expect(screen.getByText('Title')).toBeInTheDocument()
    })
  })

  describe('AlertDescription Component', () => {
    test('renders description with proper styling', () => {
      render(
        <AlertDescription data-testid="alert-description">
          Alert description text
        </AlertDescription>
      )

      const description = screen.getByTestId('alert-description')
      expect(description).toBeInTheDocument()
      expect(description).toHaveClass(
        'text-muted-foreground',
        'col-start-2',
        'grid',
        'justify-items-start',
        'gap-1',
        'text-sm'
      )
      expect(description.textContent).toBe('Alert description text')
    })

    test('applies custom className to description', () => {
      render(
        <AlertDescription className="custom-desc-class">
          Custom Description
        </AlertDescription>
      )

      const description = screen.getByText('Custom Description')
      expect(description).toHaveClass('custom-desc-class')
      // Should maintain base classes
      expect(description).toHaveClass('text-muted-foreground', 'text-sm')
    })

    test('renders as div element', () => {
      render(<AlertDescription>Description Element</AlertDescription>)
      const description = screen.getByText('Description Element')
      expect(description.tagName).toBe('DIV')
    })

    test('handles complex content', () => {
      render(
        <AlertDescription>
          <p>Paragraph content</p>
          <div>Div content</div>
          <span>Span content</span>
        </AlertDescription>
      )

      expect(screen.getByText('Paragraph content')).toBeInTheDocument()
      expect(screen.getByText('Div content')).toBeInTheDocument()
      expect(screen.getByText('Span content')).toBeInTheDocument()
    })
  })

  describe('Blue Theme Application', () => {
    test('default variant uses blue theme colors', () => {
      render(
        <Alert variant="default" data-testid="default-theme-alert">
          <AlertDescription>Default theme test</AlertDescription>
        </Alert>
      )

      const alert = screen.getByTestId('default-theme-alert')
      expect(alert).toHaveClass('bg-card', 'text-card-foreground')

      const description = screen.getByText('Default theme test')
      expect(description).toHaveClass('text-muted-foreground')
    })

    test('destructive variant uses destructive theme colors', () => {
      render(
        <Alert variant="destructive" data-testid="destructive-theme-alert">
          <AlertDescription>Destructive theme test</AlertDescription>
        </Alert>
      )

      const alert = screen.getByTestId('destructive-theme-alert')
      expect(alert).toHaveClass('text-destructive', 'bg-card')
    })

    test('maintains theme consistency with icons', () => {
      render(
        <Alert data-testid="icon-alert">
          <svg className="h-4 w-4" data-testid="alert-icon">
            <circle cx="12" cy="12" r="10" />
          </svg>
          <AlertTitle>Icon Alert</AlertTitle>
          <AlertDescription>Alert with icon</AlertDescription>
        </Alert>
      )

      const alert = screen.getByTestId('icon-alert')
      const icon = screen.getByTestId('alert-icon')

      expect(alert).toHaveClass('has-[>svg]:grid-cols-[calc(var(--spacing)*4)_1fr]')
      expect(icon).toHaveClass('h-4', 'w-4')
    })
  })

  describe('Complete Alert Compositions', () => {
    test('renders complete alert with title and description', () => {
      render(
        <Alert>
          <AlertTitle>Complete Alert</AlertTitle>
          <AlertDescription>
            This is a complete alert with both title and description.
          </AlertDescription>
        </Alert>
      )

      expect(screen.getByText('Complete Alert')).toBeInTheDocument()
      expect(screen.getByText('This is a complete alert with both title and description.')).toBeInTheDocument()
    })

    test('renders alert with icon, title, and description', () => {
      render(
        <Alert>
          <svg className="h-4 w-4" data-testid="complete-icon">
            <path d="M12 2L2 7v10c0 5.55 3.84 9.95 9 11 5.16-1.05 9-5.45 9-11V7l-10-5z" />
          </svg>
          <AlertTitle>Alert with Icon</AlertTitle>
          <AlertDescription>
            This alert includes an icon, title, and description.
          </AlertDescription>
        </Alert>
      )

      expect(screen.getByTestId('complete-icon')).toBeInTheDocument()
      expect(screen.getByText('Alert with Icon')).toBeInTheDocument()
      expect(screen.getByText('This alert includes an icon, title, and description.')).toBeInTheDocument()
    })

    test('renders alert with only description', () => {
      render(
        <Alert>
          <AlertDescription>
            Simple alert with only description text.
          </AlertDescription>
        </Alert>
      )

      expect(screen.getByText('Simple alert with only description text.')).toBeInTheDocument()
      // Title should not be present
      expect(screen.queryByRole('heading')).not.toBeInTheDocument()
    })

    test('renders alert with only title', () => {
      render(
        <Alert>
          <AlertTitle>Title Only Alert</AlertTitle>
        </Alert>
      )

      expect(screen.getByText('Title Only Alert')).toBeInTheDocument()
    })
  })

  describe('Variant Behavior', () => {
    test('default variant styling', () => {
      render(
        <Alert variant="default" data-testid="default-variant">
          <AlertTitle>Default Alert</AlertTitle>
          <AlertDescription>Default variant description</AlertDescription>
        </Alert>
      )

      const alert = screen.getByTestId('default-variant')
      expect(alert).toHaveClass('bg-card', 'text-card-foreground')
    })

    test('destructive variant styling', () => {
      render(
        <Alert variant="destructive" data-testid="destructive-variant">
          <AlertTitle>Error Alert</AlertTitle>
          <AlertDescription>Something went wrong</AlertDescription>
        </Alert>
      )

      const alert = screen.getByTestId('destructive-variant')
      expect(alert).toHaveClass('text-destructive')

      const description = screen.getByText('Something went wrong')
      expect(description.closest('[data-slot="alert-description"]')).toHaveClass('*:data-[slot=alert-description]:text-destructive/90')
    })
  })

  describe('Accessibility', () => {
    test('alert has proper role attribute', () => {
      render(
        <Alert data-testid="accessible-alert">
          <AlertDescription>Accessible alert</AlertDescription>
        </Alert>
      )

      const alert = screen.getByTestId('accessible-alert')
      expect(alert).toHaveAttribute('role', 'alert')
    })

    test('alert is announced to screen readers', () => {
      render(
        <Alert data-testid="announced-alert">
          <AlertDescription>This alert will be announced</AlertDescription>
        </Alert>
      )

      const alert = screen.getByTestId('announced-alert')
      expect(alert).toHaveAttribute('role', 'alert')
      // role="alert" causes screen readers to announce the content immediately
    })

    test('supports additional ARIA attributes', () => {
      render(
        <Alert
          data-testid="aria-alert"
          aria-live="polite"
          aria-atomic="true"
        >
          <AlertDescription>ARIA enhanced alert</AlertDescription>
        </Alert>
      )

      const alert = screen.getByTestId('aria-alert')
      expect(alert).toHaveAttribute('aria-live', 'polite')
      expect(alert).toHaveAttribute('aria-atomic', 'true')
    })

    test('title and description have proper semantic structure', () => {
      render(
        <Alert>
          <AlertTitle data-testid="semantic-title">Semantic Title</AlertTitle>
          <AlertDescription data-testid="semantic-description">
            Semantic description text
          </AlertDescription>
        </Alert>
      )

      const title = screen.getByTestId('semantic-title')
      const description = screen.getByTestId('semantic-description')

      expect(title).toHaveAttribute('data-slot', 'alert-title')
      expect(description).toHaveAttribute('data-slot', 'alert-description')
    })
  })

  describe('Grid Layout System', () => {
    test('alert uses grid layout for icon alignment', () => {
      render(
        <Alert data-testid="grid-alert">
          <svg className="h-4 w-4">
            <circle cx="12" cy="12" r="10" />
          </svg>
          <AlertTitle>Grid Layout</AlertTitle>
          <AlertDescription>Grid-based layout test</AlertDescription>
        </Alert>
      )

      const alert = screen.getByTestId('grid-alert')
      expect(alert).toHaveClass('grid', 'has-[>svg]:grid-cols-[calc(var(--spacing)*4)_1fr]')
    })

    test('alert without icon uses different grid', () => {
      render(
        <Alert data-testid="no-icon-alert">
          <AlertTitle>No Icon</AlertTitle>
          <AlertDescription>No icon layout test</AlertDescription>
        </Alert>
      )

      const alert = screen.getByTestId('no-icon-alert')
      expect(alert).toHaveClass('grid', 'grid-cols-[0_1fr]')
    })
  })

  describe('Edge Cases', () => {
    test('handles empty alert', () => {
      render(<Alert data-testid="empty-alert"></Alert>)
      const alert = screen.getByTestId('empty-alert')
      expect(alert).toBeInTheDocument()
      expect(alert.textContent).toBe('')
    })

    test('handles long content gracefully', () => {
      const longText = 'This is a very long alert description that should wrap properly and maintain good readability even when the content extends across multiple lines and contains a lot of text.'

      render(
        <Alert>
          <AlertTitle>Long Content Alert</AlertTitle>
          <AlertDescription>{longText}</AlertDescription>
        </Alert>
      )

      expect(screen.getByText(longText)).toBeInTheDocument()
      expect(screen.getByText('Long Content Alert')).toBeInTheDocument()
    })

    test('forwards refs correctly', () => {
      const alertRef = React.createRef<HTMLDivElement>()
      const titleRef = React.createRef<HTMLDivElement>()
      const descRef = React.createRef<HTMLDivElement>()

      render(
        <Alert ref={alertRef}>
          <AlertTitle ref={titleRef}>Ref Title</AlertTitle>
          <AlertDescription ref={descRef}>Ref Description</AlertDescription>
        </Alert>
      )

      expect(alertRef.current).toBeInstanceOf(HTMLDivElement)
      expect(titleRef.current).toBeInstanceOf(HTMLDivElement)
      expect(descRef.current).toBeInstanceOf(HTMLDivElement)
    })

    test('handles multiple alerts on same page', () => {
      render(
        <div>
          <Alert data-testid="alert-1">
            <AlertDescription>First alert</AlertDescription>
          </Alert>
          <Alert data-testid="alert-2" variant="destructive">
            <AlertDescription>Second alert</AlertDescription>
          </Alert>
        </div>
      )

      const alert1 = screen.getByTestId('alert-1')
      const alert2 = screen.getByTestId('alert-2')

      expect(alert1).toHaveClass('bg-card')
      expect(alert2).toHaveClass('text-destructive')
      expect(screen.getByText('First alert')).toBeInTheDocument()
      expect(screen.getByText('Second alert')).toBeInTheDocument()
    })
  })
})