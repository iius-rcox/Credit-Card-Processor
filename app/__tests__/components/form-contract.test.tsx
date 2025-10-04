/**
 * Form Component Contract Validation (T039)
 *
 * Tests that verify the Form component props work as documented in the API contract.
 */

import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import { useForm } from 'react-hook-form'
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormDescription,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

// Test component wrapper for form testing
function TestFormComponent({ onSubmit = jest.fn(), defaultValues = {} }) {
  const form = useForm({ defaultValues })

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} data-testid="test-form">
        <FormField
          control={form.control}
          name="testField"
          rules={{ required: 'This field is required' }}
          render={({ field }) => (
            <FormItem>
              <FormLabel>Test Field</FormLabel>
              <FormControl>
                <Input placeholder="Enter test value" {...field} />
              </FormControl>
              <FormDescription>This is a test field description</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type="submit" data-testid="submit-button">Submit</Button>
      </form>
    </Form>
  )
}

describe('Form Component Contract Validation', () => {
  describe('Form Provider', () => {
    test('Form is FormProvider from react-hook-form', () => {
      const form = useForm()
      render(
        <Form {...form}>
          <div data-testid="form-content">Form content</div>
        </Form>
      )

      expect(screen.getByTestId('form-content')).toBeInTheDocument()
    })

    test('provides form context to children', () => {
      const onSubmit = jest.fn()
      render(<TestFormComponent onSubmit={onSubmit} />)

      expect(screen.getByText('Test Field')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Enter test value')).toBeInTheDocument()
    })
  })

  describe('FormField Component', () => {
    test('renders form field with Controller', () => {
      const form = useForm()
      render(
        <Form {...form}>
          <FormField
            control={form.control}
            name="testField"
            render={({ field }) => (
              <FormItem>
                <FormControl>
                  <Input {...field} data-testid="controlled-input" />
                </FormControl>
              </FormItem>
            )}
          />
        </Form>
      )

      const input = screen.getByTestId('controlled-input')
      expect(input).toBeInTheDocument()
    })

    test('handles field validation rules', () => {
      const onSubmit = jest.fn()
      render(<TestFormComponent onSubmit={onSubmit} />)

      const submitButton = screen.getByTestId('submit-button')
      fireEvent.click(submitButton)

      // Should show validation error
      expect(screen.getByText('This field is required')).toBeInTheDocument()
      expect(onSubmit).not.toHaveBeenCalled()
    })

    test('provides field context to children', () => {
      const form = useForm()
      render(
        <Form {...form}>
          <FormField
            control={form.control}
            name="contextTest"
            render={({ field, fieldState, formState }) => (
              <FormItem>
                <FormLabel data-testid="context-label">Context Test</FormLabel>
                <FormControl>
                  <Input {...field} data-testid="context-input" />
                </FormControl>
                <FormMessage data-testid="context-message" />
              </FormItem>
            )}
          />
        </Form>
      )

      expect(screen.getByTestId('context-label')).toBeInTheDocument()
      expect(screen.getByTestId('context-input')).toBeInTheDocument()
      expect(screen.getByTestId('context-message')).toBeInTheDocument()
    })
  })

  describe('FormItem Component', () => {
    test('renders with proper grid layout', () => {
      const form = useForm()
      render(
        <Form {...form}>
          <FormItem data-testid="form-item">
            <div>Item content</div>
          </FormItem>
        </Form>
      )

      const item = screen.getByTestId('form-item')
      expect(item).toHaveClass('grid', 'gap-2')
      expect(item).toHaveAttribute('data-slot', 'form-item')
    })

    test('applies custom className', () => {
      const form = useForm()
      render(
        <Form {...form}>
          <FormItem className="custom-item-class" data-testid="custom-item">
            <div>Custom item</div>
          </FormItem>
        </Form>
      )

      const item = screen.getByTestId('custom-item')
      expect(item).toHaveClass('custom-item-class', 'grid', 'gap-2')
    })

    test('provides unique ID context', () => {
      const form = useForm()
      render(
        <Form {...form}>
          <FormField
            control={form.control}
            name="uniqueIdTest"
            render={() => (
              <FormItem>
                <FormLabel data-testid="unique-label">Unique Label</FormLabel>
                <FormControl>
                  <Input data-testid="unique-input" />
                </FormControl>
              </FormItem>
            )}
          />
        </Form>
      )

      const label = screen.getByTestId('unique-label')
      const input = screen.getByTestId('unique-input')

      expect(label).toHaveAttribute('for')
      expect(input).toHaveAttribute('id')
      expect(label.getAttribute('for')).toBe(input.getAttribute('id'))
    })
  })

  describe('FormLabel Component', () => {
    test('renders with proper styling', () => {
      const form = useForm()
      render(
        <Form {...form}>
          <FormField
            control={form.control}
            name="labelTest"
            render={() => (
              <FormItem>
                <FormLabel data-testid="form-label">Form Label</FormLabel>
              </FormItem>
            )}
          />
        </Form>
      )

      const label = screen.getByTestId('form-label')
      expect(label).toHaveAttribute('data-slot', 'form-label')
      expect(label.textContent).toBe('Form Label')
    })

    test('shows error state styling', () => {
      const form = useForm()
      render(
        <Form {...form}>
          <FormField
            control={form.control}
            name="errorTest"
            rules={{ required: true }}
            render={({ field }) => (
              <FormItem>
                <FormLabel data-testid="error-label">Error Label</FormLabel>
                <FormControl>
                  <Input {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <Button onClick={() => form.trigger('errorTest')}>Trigger Validation</Button>
        </Form>
      )

      // Trigger validation to create error state
      fireEvent.click(screen.getByText('Trigger Validation'))

      const label = screen.getByTestId('error-label')
      expect(label).toHaveClass('data-[error=true]:text-destructive')
    })

    test('associates with form control via htmlFor', () => {
      const form = useForm()
      render(
        <Form {...form}>
          <FormField
            control={form.control}
            name="associationTest"
            render={() => (
              <FormItem>
                <FormLabel data-testid="associated-label">Associated Label</FormLabel>
                <FormControl>
                  <Input data-testid="associated-input" />
                </FormControl>
              </FormItem>
            )}
          />
        </Form>
      )

      const label = screen.getByTestId('associated-label')
      const input = screen.getByTestId('associated-input')

      expect(label).toHaveAttribute('for')
      expect(input).toHaveAttribute('id')
      expect(label.getAttribute('for')).toBe(input.getAttribute('id'))
    })
  })

  describe('FormControl Component', () => {
    test('provides proper ARIA attributes', () => {
      const form = useForm()
      render(
        <Form {...form}>
          <FormField
            control={form.control}
            name="ariaTest"
            render={() => (
              <FormItem>
                <FormLabel>ARIA Test</FormLabel>
                <FormControl>
                  <Input data-testid="aria-input" />
                </FormControl>
                <FormDescription>Test description</FormDescription>
              </FormItem>
            )}
          />
        </Form>
      )

      const input = screen.getByTestId('aria-input')
      expect(input).toHaveAttribute('aria-describedby')
      expect(input).toHaveAttribute('id')
    })

    test('handles error state ARIA attributes', () => {
      const form = useForm()
      render(
        <Form {...form}>
          <FormField
            control={form.control}
            name="ariaErrorTest"
            rules={{ required: true }}
            render={({ field }) => (
              <FormItem>
                <FormLabel>Error ARIA Test</FormLabel>
                <FormControl>
                  <Input {...field} data-testid="aria-error-input" />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <Button onClick={() => form.trigger('ariaErrorTest')}>Trigger</Button>
        </Form>
      )

      fireEvent.click(screen.getByText('Trigger'))

      const input = screen.getByTestId('aria-error-input')
      expect(input).toHaveAttribute('aria-invalid', 'true')
    })

    test('uses Slot for composition', () => {
      const form = useForm()
      render(
        <Form {...form}>
          <FormField
            control={form.control}
            name="slotTest"
            render={() => (
              <FormItem>
                <FormControl>
                  <Input data-testid="slot-input" />
                </FormControl>
              </FormItem>
            )}
          />
        </Form>
      )

      const input = screen.getByTestId('slot-input')
      expect(input).toBeInTheDocument()
    })
  })

  describe('FormDescription Component', () => {
    test('renders with proper styling', () => {
      const form = useForm()
      render(
        <Form {...form}>
          <FormDescription data-testid="form-description">
            This is a form description
          </FormDescription>
        </Form>
      )

      const description = screen.getByTestId('form-description')
      expect(description).toHaveClass('text-muted-foreground', 'text-sm')
      expect(description).toHaveAttribute('data-slot', 'form-description')
      expect(description.textContent).toBe('This is a form description')
    })

    test('provides description ID for ARIA', () => {
      const form = useForm()
      render(
        <Form {...form}>
          <FormField
            control={form.control}
            name="descriptionTest"
            render={() => (
              <FormItem>
                <FormControl>
                  <Input data-testid="described-input" />
                </FormControl>
                <FormDescription data-testid="description">
                  Field description
                </FormDescription>
              </FormItem>
            )}
          />
        </Form>
      )

      const input = screen.getByTestId('described-input')
      const description = screen.getByTestId('description')

      expect(description).toHaveAttribute('id')
      expect(input).toHaveAttribute('aria-describedby')
    })

    test('applies custom className', () => {
      const form = useForm()
      render(
        <Form {...form}>
          <FormDescription className="custom-description" data-testid="custom-desc">
            Custom description
          </FormDescription>
        </Form>
      )

      const description = screen.getByTestId('custom-desc')
      expect(description).toHaveClass('custom-description', 'text-muted-foreground', 'text-sm')
    })
  })

  describe('FormMessage Component', () => {
    test('renders error messages', () => {
      const onSubmit = jest.fn()
      render(<TestFormComponent onSubmit={onSubmit} />)

      const submitButton = screen.getByTestId('submit-button')
      fireEvent.click(submitButton)

      const errorMessage = screen.getByText('This field is required')
      expect(errorMessage).toBeInTheDocument()
      expect(errorMessage).toHaveClass('text-destructive', 'text-sm')
      expect(errorMessage).toHaveAttribute('data-slot', 'form-message')
    })

    test('renders custom children when no error', () => {
      const form = useForm()
      render(
        <Form {...form}>
          <FormMessage data-testid="custom-message">
            Custom message content
          </FormMessage>
        </Form>
      )

      expect(screen.getByText('Custom message content')).toBeInTheDocument()
    })

    test('does not render when no error and no children', () => {
      const form = useForm()
      render(
        <Form {...form}>
          <FormField
            control={form.control}
            name="noErrorTest"
            render={() => (
              <FormItem>
                <FormMessage data-testid="no-error-message" />
              </FormItem>
            )}
          />
        </Form>
      )

      expect(screen.queryByTestId('no-error-message')).not.toBeInTheDocument()
    })

    test('provides message ID for ARIA', () => {
      const onSubmit = jest.fn()
      render(<TestFormComponent onSubmit={onSubmit} />)

      fireEvent.click(screen.getByTestId('submit-button'))

      const errorMessage = screen.getByText('This field is required')
      const input = screen.getByPlaceholderText('Enter test value')

      expect(errorMessage).toHaveAttribute('id')
      expect(input).toHaveAttribute('aria-describedby')
    })
  })

  describe('Blue Theme Application', () => {
    test('error messages use destructive color', () => {
      const onSubmit = jest.fn()
      render(<TestFormComponent onSubmit={onSubmit} />)

      fireEvent.click(screen.getByTestId('submit-button'))

      const errorMessage = screen.getByText('This field is required')
      expect(errorMessage).toHaveClass('text-destructive')
    })

    test('description uses muted foreground color', () => {
      render(<TestFormComponent />)

      const description = screen.getByText('This is a test field description')
      expect(description).toHaveClass('text-muted-foreground')
    })

    test('labels support error state styling', () => {
      const onSubmit = jest.fn()
      render(<TestFormComponent onSubmit={onSubmit} />)

      fireEvent.click(screen.getByTestId('submit-button'))

      const label = screen.getByText('Test Field')
      expect(label).toHaveClass('data-[error=true]:text-destructive')
    })
  })

  describe('Form Integration', () => {
    test('complete form submission workflow', () => {
      const onSubmit = jest.fn()
      render(<TestFormComponent onSubmit={onSubmit} />)

      const input = screen.getByPlaceholderText('Enter test value')
      const submitButton = screen.getByTestId('submit-button')

      // Fill form and submit
      fireEvent.change(input, { target: { value: 'test value' } })
      fireEvent.click(submitButton)

      expect(onSubmit).toHaveBeenCalledWith({ testField: 'test value' })
    })

    test('form validation prevents submission', () => {
      const onSubmit = jest.fn()
      render(<TestFormComponent onSubmit={onSubmit} />)

      const submitButton = screen.getByTestId('submit-button')

      // Submit without filling required field
      fireEvent.click(submitButton)

      expect(onSubmit).not.toHaveBeenCalled()
      expect(screen.getByText('This field is required')).toBeInTheDocument()
    })

    test('form handles default values', () => {
      const onSubmit = jest.fn()
      render(
        <TestFormComponent
          onSubmit={onSubmit}
          defaultValues={{ testField: 'default value' }}
        />
      )

      const input = screen.getByPlaceholderText('Enter test value') as HTMLInputElement
      expect(input.value).toBe('default value')

      fireEvent.click(screen.getByTestId('submit-button'))
      expect(onSubmit).toHaveBeenCalledWith({ testField: 'default value' })
    })
  })

  describe('useFormField Hook', () => {
    test('provides field context', () => {
      function TestFieldComponent() {
        const { id, name, formItemId, formDescriptionId, formMessageId } = useFormField()
        return (
          <div data-testid="field-context">
            <span data-testid="field-id">{id}</span>
            <span data-testid="field-name">{name}</span>
            <span data-testid="form-item-id">{formItemId}</span>
            <span data-testid="form-description-id">{formDescriptionId}</span>
            <span data-testid="form-message-id">{formMessageId}</span>
          </div>
        )
      }

      const form = useForm()
      render(
        <Form {...form}>
          <FormField
            control={form.control}
            name="hookTest"
            render={() => (
              <FormItem>
                <TestFieldComponent />
              </FormItem>
            )}
          />
        </Form>
      )

      expect(screen.getByTestId('field-context')).toBeInTheDocument()
      expect(screen.getByTestId('field-name')).toHaveTextContent('hookTest')
    })
  })

  describe('Edge Cases', () => {
    test('handles multiple form fields', () => {
      const form = useForm()
      const onSubmit = jest.fn()

      render(
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <FormField
              control={form.control}
              name="field1"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Field 1</FormLabel>
                  <FormControl>
                    <Input {...field} data-testid="field1" />
                  </FormControl>
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="field2"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Field 2</FormLabel>
                  <FormControl>
                    <Input {...field} data-testid="field2" />
                  </FormControl>
                </FormItem>
              )}
            />
            <Button type="submit" data-testid="multi-submit">Submit</Button>
          </form>
        </Form>
      )

      fireEvent.change(screen.getByTestId('field1'), { target: { value: 'value1' } })
      fireEvent.change(screen.getByTestId('field2'), { target: { value: 'value2' } })
      fireEvent.click(screen.getByTestId('multi-submit'))

      expect(onSubmit).toHaveBeenCalledWith({ field1: 'value1', field2: 'value2' })
    })

    test('handles complex validation rules', () => {
      const form = useForm()
      render(
        <Form {...form}>
          <FormField
            control={form.control}
            name="complexValidation"
            rules={{
              required: 'Required',
              minLength: { value: 5, message: 'Too short' },
              pattern: { value: /^[A-Z]/, message: 'Must start with capital' },
            }}
            render={({ field }) => (
              <FormItem>
                <FormLabel>Complex Validation</FormLabel>
                <FormControl>
                  <Input {...field} data-testid="complex-input" />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <Button onClick={() => form.trigger('complexValidation')}>Validate</Button>
        </Form>
      )

      const input = screen.getByTestId('complex-input')
      const validateButton = screen.getByText('Validate')

      // Test required
      fireEvent.click(validateButton)
      expect(screen.getByText('Required')).toBeInTheDocument()

      // Test min length
      fireEvent.change(input, { target: { value: 'ab' } })
      fireEvent.click(validateButton)
      expect(screen.getByText('Too short')).toBeInTheDocument()

      // Test pattern
      fireEvent.change(input, { target: { value: 'abcdef' } })
      fireEvent.click(validateButton)
      expect(screen.getByText('Must start with capital')).toBeInTheDocument()

      // Test valid
      fireEvent.change(input, { target: { value: 'Abcdef' } })
      fireEvent.click(validateButton)
      expect(screen.queryByText('Must start with capital')).not.toBeInTheDocument()
    })
  })
})