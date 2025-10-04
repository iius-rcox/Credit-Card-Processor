/**
 * Button Component Contract Validation (T034)
 *
 * Tests that verify the Button component props work as documented in the API contract.
 */

import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { Button } from '@/components/ui/button'

describe('Button Component Contract Validation', () => {
  describe('Variant Props', () => {
    test('renders default variant with primary blue background', () => {
      render(<Button variant="default">Default Button</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('bg-primary')
      expect(button).toBeInTheDocument()
    })

    test('renders destructive variant', () => {
      render(<Button variant="destructive">Destructive Button</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('bg-destructive')
    })

    test('renders outline variant with blue border', () => {
      render(<Button variant="outline">Outline Button</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('border-input')
    })

    test('renders secondary variant', () => {
      render(<Button variant="secondary">Secondary Button</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('bg-secondary')
    })

    test('renders ghost variant', () => {
      render(<Button variant="ghost">Ghost Button</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('hover:bg-accent')
    })

    test('renders link variant', () => {
      render(<Button variant="link">Link Button</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('text-primary')
    })
  })

  describe('Size Props', () => {
    test('renders default size', () => {
      render(<Button size="default">Default Size</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('h-9', 'px-4', 'py-2')
    })

    test('renders small size', () => {
      render(<Button size="sm">Small Size</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('h-8', 'px-3')
    })

    test('renders large size', () => {
      render(<Button size="lg">Large Size</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('h-10', 'px-8')
    })

    test('renders icon size', () => {
      render(<Button size="icon">🔄</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('h-9', 'w-9')
    })
  })

  describe('Functionality Props', () => {
    test('handles onClick events', () => {
      const handleClick = jest.fn()
      render(<Button onClick={handleClick}>Clickable Button</Button>)

      const button = screen.getByRole('button')
      fireEvent.click(button)

      expect(handleClick).toHaveBeenCalledTimes(1)
    })

    test('handles disabled state', () => {
      const handleClick = jest.fn()
      render(<Button disabled onClick={handleClick}>Disabled Button</Button>)

      const button = screen.getByRole('button')
      expect(button).toBeDisabled()

      fireEvent.click(button)
      expect(handleClick).not.toHaveBeenCalled()
    })

    test('supports different button types', () => {
      const { rerender } = render(<Button type="button">Button Type</Button>)
      let button = screen.getByRole('button')
      expect(button).toHaveAttribute('type', 'button')

      rerender(<Button type="submit">Submit Type</Button>)
      button = screen.getByRole('button')
      expect(button).toHaveAttribute('type', 'submit')

      rerender(<Button type="reset">Reset Type</Button>)
      button = screen.getByRole('button')
      expect(button).toHaveAttribute('type', 'reset')
    })

    test('applies custom className', () => {
      render(<Button className="custom-class">Custom Button</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('custom-class')
    })

    test('renders children content', () => {
      render(
        <Button>
          <span>Complex Content</span>
          <strong>Bold Text</strong>
        </Button>
      )

      expect(screen.getByText('Complex Content')).toBeInTheDocument()
      expect(screen.getByText('Bold Text')).toBeInTheDocument()
    })
  })

  describe('Blue Theme Application', () => {
    test('default variant uses primary blue colors', () => {
      render(<Button variant="default">Blue Theme</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('bg-primary', 'text-primary-foreground')
    })

    test('outline variant uses primary blue border', () => {
      render(<Button variant="outline">Blue Outline</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('border-input', 'hover:bg-accent')
    })

    test('focus states use blue ring color', () => {
      render(<Button>Focus Test</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('focus-visible:ring-ring')
    })
  })

  describe('Accessibility', () => {
    test('has proper button role', () => {
      render(<Button>Accessible Button</Button>)
      const button = screen.getByRole('button')
      expect(button).toBeInTheDocument()
    })

    test('supports aria attributes via props spreading', () => {
      render(
        <Button aria-label="Custom aria label" aria-describedby="description">
          Button
        </Button>
      )
      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('aria-label', 'Custom aria label')
      expect(button).toHaveAttribute('aria-describedby', 'description')
    })

    test('disabled state is properly announced', () => {
      render(<Button disabled>Disabled Button</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('disabled')
    })
  })

  describe('Component Composition', () => {
    test('forwards ref to button element', () => {
      const ref = React.createRef<HTMLButtonElement>()
      render(<Button ref={ref}>Ref Button</Button>)

      expect(ref.current).toBeInstanceOf(HTMLButtonElement)
      expect(ref.current?.textContent).toBe('Ref Button')
    })

    test('spreads additional props to button element', () => {
      render(
        <Button data-testid="spread-test" id="custom-id">
          Props Test
        </Button>
      )
      const button = screen.getByTestId('spread-test')
      expect(button).toHaveAttribute('id', 'custom-id')
    })
  })

  describe('Edge Cases', () => {
    test('handles empty children', () => {
      render(<Button></Button>)
      const button = screen.getByRole('button')
      expect(button).toBeInTheDocument()
      expect(button.textContent).toBe('')
    })

    test('handles multiple className props (cn utility)', () => {
      render(<Button className="class1 class2" variant="outline">Multi Class</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveClass('class1', 'class2')
      // Should also maintain variant classes
      expect(button).toHaveClass('border-input')
    })

    test('preserves button behavior with complex event handlers', () => {
      const handleClick = jest.fn()
      const handleMouseDown = jest.fn()
      const handleKeyDown = jest.fn()

      render(
        <Button
          onClick={handleClick}
          onMouseDown={handleMouseDown}
          onKeyDown={handleKeyDown}
        >
          Complex Events
        </Button>
      )

      const button = screen.getByRole('button')

      fireEvent.click(button)
      fireEvent.mouseDown(button)
      fireEvent.keyDown(button, { key: 'Enter' })

      expect(handleClick).toHaveBeenCalledTimes(1)
      expect(handleMouseDown).toHaveBeenCalledTimes(1)
      expect(handleKeyDown).toHaveBeenCalledTimes(1)
    })
  })
})