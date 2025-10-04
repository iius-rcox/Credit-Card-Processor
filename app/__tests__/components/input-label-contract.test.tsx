/**
 * Input/Label Component Contract Validation (T036)
 *
 * Tests that verify the Input and Label component props work as documented in the API contract.
 */

import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

describe('Input/Label Component Contract Validation', () => {
  describe('Input Component', () => {
    test('renders input with default styles', () => {
      render(<Input data-testid="default-input" />)
      const input = screen.getByTestId('default-input')

      expect(input).toBeInTheDocument()
      expect(input).toHaveClass(
        'flex',
        'h-9',
        'w-full',
        'rounded-md',
        'border',
        'border-input',
        'bg-transparent',
        'px-3',
        'py-1',
        'text-base',
        'shadow-sm'
      )
    })

    test('supports all standard input types', () => {
      const inputTypes = ['text', 'email', 'password', 'number', 'tel', 'url', 'search']

      inputTypes.forEach((type) => {
        const { rerender } = render(<Input type={type} data-testid={`input-${type}`} />)
        const input = screen.getByTestId(`input-${type}`)
        expect(input).toHaveAttribute('type', type)

        if (type !== inputTypes[inputTypes.length - 1]) {
          rerender(<></>)
        }
      })
    })

    test('handles placeholder text', () => {
      render(<Input placeholder="Enter your email" data-testid="placeholder-input" />)
      const input = screen.getByTestId('placeholder-input')
      expect(input).toHaveAttribute('placeholder', 'Enter your email')
    })

    test('handles value prop (controlled)', () => {
      render(<Input value="controlled value" readOnly data-testid="controlled-input" />)
      const input = screen.getByTestId('controlled-input') as HTMLInputElement
      expect(input.value).toBe('controlled value')
    })

    test('handles defaultValue prop (uncontrolled)', () => {
      render(<Input defaultValue="default value" data-testid="uncontrolled-input" />)
      const input = screen.getByTestId('uncontrolled-input') as HTMLInputElement
      expect(input.value).toBe('default value')
    })

    test('handles onChange events', () => {
      const handleChange = jest.fn()
      render(<Input onChange={handleChange} data-testid="change-input" />)

      const input = screen.getByTestId('change-input')
      fireEvent.change(input, { target: { value: 'new value' } })

      expect(handleChange).toHaveBeenCalledTimes(1)
      expect(handleChange).toHaveBeenCalledWith(expect.objectContaining({
        target: expect.objectContaining({
          value: 'new value'
        })
      }))
    })

    test('handles disabled state', () => {
      render(<Input disabled data-testid="disabled-input" />)
      const input = screen.getByTestId('disabled-input')

      expect(input).toBeDisabled()
      expect(input).toHaveClass('disabled:cursor-not-allowed', 'disabled:opacity-50')
    })

    test('applies custom className', () => {
      render(<Input className="custom-input-class" data-testid="custom-input" />)
      const input = screen.getByTestId('custom-input')

      expect(input).toHaveClass('custom-input-class')
      // Should maintain base classes
      expect(input).toHaveClass('border-input', 'rounded-md')
    })

    test('supports focus ring styling (blue theme)', () => {
      render(<Input data-testid="focus-input" />)
      const input = screen.getByTestId('focus-input')

      expect(input).toHaveClass(
        'focus-visible:outline-none',
        'focus-visible:ring-1',
        'focus-visible:ring-ring'
      )
    })

    test('forwards ref correctly', () => {
      const inputRef = React.createRef<HTMLInputElement>()
      render(<Input ref={inputRef} defaultValue="ref test" />)

      expect(inputRef.current).toBeInstanceOf(HTMLInputElement)
      expect(inputRef.current?.value).toBe('ref test')
    })

    test('spreads additional HTML input attributes', () => {
      render(
        <Input
          data-testid="attributes-input"
          id="custom-id"
          name="custom-name"
          required
          minLength={5}
          maxLength={20}
          pattern="[A-Za-z]*"
          autoComplete="email"
        />
      )

      const input = screen.getByTestId('attributes-input')
      expect(input).toHaveAttribute('id', 'custom-id')
      expect(input).toHaveAttribute('name', 'custom-name')
      expect(input).toHaveAttribute('required')
      expect(input).toHaveAttribute('minlength', '5')
      expect(input).toHaveAttribute('maxlength', '20')
      expect(input).toHaveAttribute('pattern', '[A-Za-z]*')
      expect(input).toHaveAttribute('autocomplete', 'email')
    })
  })

  describe('Label Component', () => {
    test('renders label with default styles', () => {
      render(<Label data-testid="default-label">Default Label</Label>)
      const label = screen.getByTestId('default-label')

      expect(label).toBeInTheDocument()
      expect(label).toHaveClass(
        'text-sm',
        'font-medium',
        'leading-none'
      )
      expect(label.textContent).toBe('Default Label')
    })

    test('handles htmlFor attribute for accessibility', () => {
      render(
        <div>
          <Label htmlFor="associated-input" data-testid="associated-label">
            Associated Label
          </Label>
          <Input id="associated-input" data-testid="associated-input" />
        </div>
      )

      const label = screen.getByTestId('associated-label')
      const input = screen.getByTestId('associated-input')

      expect(label).toHaveAttribute('for', 'associated-input')
      expect(input).toHaveAttribute('id', 'associated-input')

      // Test clicking label focuses input
      fireEvent.click(label)
      expect(input).toHaveFocus()
    })

    test('applies custom className', () => {
      render(<Label className="custom-label-class">Custom Label</Label>)
      const label = screen.getByText('Custom Label')

      expect(label).toHaveClass('custom-label-class')
      // Should maintain base classes
      expect(label).toHaveClass('text-sm', 'font-medium')
    })

    test('renders complex children content', () => {
      render(
        <Label>
          <span>Complex</span>
          <strong>Label</strong>
          <em>Content</em>
        </Label>
      )

      expect(screen.getByText('Complex')).toBeInTheDocument()
      expect(screen.getByText('Label')).toBeInTheDocument()
      expect(screen.getByText('Content')).toBeInTheDocument()
    })

    test('forwards ref correctly', () => {
      const labelRef = React.createRef<HTMLLabelElement>()
      render(<Label ref={labelRef}>Ref Label</Label>)

      expect(labelRef.current).toBeInstanceOf(HTMLLabelElement)
      expect(labelRef.current?.textContent).toBe('Ref Label')
    })

    test('spreads additional HTML label attributes', () => {
      render(
        <Label
          data-testid="attributes-label"
          id="custom-label-id"
          title="Label tooltip"
        >
          Attributes Label
        </Label>
      )

      const label = screen.getByTestId('attributes-label')
      expect(label).toHaveAttribute('id', 'custom-label-id')
      expect(label).toHaveAttribute('title', 'Label tooltip')
    })
  })

  describe('Blue Theme Application', () => {
    test('input uses theme border and focus colors', () => {
      render(<Input data-testid="themed-input" />)
      const input = screen.getByTestId('themed-input')

      expect(input).toHaveClass('border-input', 'focus-visible:ring-ring')
    })

    test('label uses theme text color', () => {
      render(<Label data-testid="themed-label">Themed Label</Label>)
      const label = screen.getByTestId('themed-label')

      expect(label).toHaveClass('text-sm', 'font-medium')
    })

    test('disabled input uses theme opacity', () => {
      render(<Input disabled data-testid="disabled-themed-input" />)
      const input = screen.getByTestId('disabled-themed-input')

      expect(input).toHaveClass('disabled:opacity-50')
    })
  })

  describe('Input/Label Integration', () => {
    test('complete form field with label and input', () => {
      render(
        <div className="space-y-2">
          <Label htmlFor="email-input">Email Address</Label>
          <Input
            id="email-input"
            type="email"
            placeholder="Enter your email"
            data-testid="email-input"
          />
        </div>
      )

      const label = screen.getByText('Email Address')
      const input = screen.getByTestId('email-input')

      expect(label).toHaveAttribute('for', 'email-input')
      expect(input).toHaveAttribute('id', 'email-input')
      expect(input).toHaveAttribute('type', 'email')
      expect(input).toHaveAttribute('placeholder', 'Enter your email')
    })

    test('required field indication', () => {
      render(
        <div>
          <Label htmlFor="required-input">
            Required Field <span className="text-red-500">*</span>
          </Label>
          <Input id="required-input" required data-testid="required-input" />
        </div>
      )

      const label = screen.getByText('Required Field')
      const asterisk = screen.getByText('*')
      const input = screen.getByTestId('required-input')

      expect(label).toBeInTheDocument()
      expect(asterisk).toHaveClass('text-red-500')
      expect(input).toHaveAttribute('required')
    })

    test('error state handling', () => {
      render(
        <div>
          <Label htmlFor="error-input" className="text-destructive">
            Input with Error
          </Label>
          <Input
            id="error-input"
            className="border-destructive focus-visible:ring-destructive"
            data-testid="error-input"
            aria-invalid="true"
            aria-describedby="error-message"
          />
          <div id="error-message" className="text-sm text-destructive">
            This field has an error
          </div>
        </div>
      )

      const label = screen.getByText('Input with Error')
      const input = screen.getByTestId('error-input')
      const errorMessage = screen.getByText('This field has an error')

      expect(label).toHaveClass('text-destructive')
      expect(input).toHaveClass('border-destructive')
      expect(input).toHaveAttribute('aria-invalid', 'true')
      expect(input).toHaveAttribute('aria-describedby', 'error-message')
      expect(errorMessage).toHaveClass('text-destructive')
    })
  })

  describe('Accessibility', () => {
    test('input is focusable and keyboard accessible', () => {
      render(<Input data-testid="keyboard-input" />)
      const input = screen.getByTestId('keyboard-input')

      // Focus the input
      input.focus()
      expect(input).toHaveFocus()

      // Tab should move focus away (in a real test environment)
      fireEvent.keyDown(input, { key: 'Tab' })
      // Note: In jest environment, we can't fully test tab navigation
    })

    test('label provides accessible name for input', () => {
      render(
        <div>
          <Label htmlFor="accessible-input">Accessible Input Label</Label>
          <Input id="accessible-input" data-testid="accessible-input" />
        </div>
      )

      const input = screen.getByTestId('accessible-input')
      const label = screen.getByText('Accessible Input Label')

      expect(input).toHaveAccessibleName('Accessible Input Label')
      expect(label).toHaveAttribute('for', 'accessible-input')
    })

    test('input supports aria attributes', () => {
      render(
        <Input
          data-testid="aria-input"
          aria-label="Custom aria label"
          aria-describedby="input-description"
          aria-required="true"
        />
      )

      const input = screen.getByTestId('aria-input')
      expect(input).toHaveAttribute('aria-label', 'Custom aria label')
      expect(input).toHaveAttribute('aria-describedby', 'input-description')
      expect(input).toHaveAttribute('aria-required', 'true')
    })
  })

  describe('Edge Cases', () => {
    test('input handles empty value', () => {
      render(<Input value="" readOnly data-testid="empty-input" />)
      const input = screen.getByTestId('empty-input') as HTMLInputElement
      expect(input.value).toBe('')
    })

    test('label handles empty content', () => {
      render(<Label data-testid="empty-label"></Label>)
      const label = screen.getByTestId('empty-label')
      expect(label).toBeInTheDocument()
      expect(label.textContent).toBe('')
    })

    test('input handles special characters in value', () => {
      const specialValue = 'Test!@#$%^&*()_+-=[]{}|;:,.<>?'
      render(<Input value={specialValue} readOnly data-testid="special-input" />)
      const input = screen.getByTestId('special-input') as HTMLInputElement
      expect(input.value).toBe(specialValue)
    })

    test('multiple className merging works correctly', () => {
      render(
        <Input
          className="custom-class another-class"
          data-testid="multi-class-input"
        />
      )
      const input = screen.getByTestId('multi-class-input')
      expect(input).toHaveClass('custom-class', 'another-class')
      // Should maintain base classes
      expect(input).toHaveClass('border-input', 'rounded-md')
    })
  })
})