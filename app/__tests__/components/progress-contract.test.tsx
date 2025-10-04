/**
 * Progress Component Contract Validation (T038)
 *
 * Tests that verify the Progress component props work as documented in the API contract.
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { Progress } from '@/components/ui/progress'

describe('Progress Component Contract Validation', () => {
  describe('Basic Functionality', () => {
    test('renders progress component with default props', () => {
      render(<Progress data-testid="default-progress" />)
      const progress = screen.getByTestId('default-progress')

      expect(progress).toBeInTheDocument()
      expect(progress).toHaveClass(
        'bg-primary/20',
        'relative',
        'h-2',
        'w-full',
        'overflow-hidden',
        'rounded-full'
      )
      expect(progress).toHaveAttribute('data-slot', 'progress')
    })

    test('renders with specified value', () => {
      render(<Progress value={50} data-testid="valued-progress" />)
      const progress = screen.getByTestId('valued-progress')
      const indicator = progress.querySelector('[data-slot="progress-indicator"]')

      expect(progress).toBeInTheDocument()
      expect(indicator).toBeInTheDocument()
      expect(indicator).toHaveStyle({ transform: 'translateX(-50%)' })
    })

    test('handles zero value', () => {
      render(<Progress value={0} data-testid="zero-progress" />)
      const progress = screen.getByTestId('zero-progress')
      const indicator = progress.querySelector('[data-slot="progress-indicator"]')

      expect(indicator).toHaveStyle({ transform: 'translateX(-100%)' })
    })

    test('handles 100% value', () => {
      render(<Progress value={100} data-testid="full-progress" />)
      const progress = screen.getByTestId('full-progress')
      const indicator = progress.querySelector('[data-slot="progress-indicator"]')

      expect(indicator).toHaveStyle({ transform: 'translateX(-0%)' })
    })

    test('handles undefined value (indeterminate)', () => {
      render(<Progress data-testid="indeterminate-progress" />)
      const progress = screen.getByTestId('indeterminate-progress')
      const indicator = progress.querySelector('[data-slot="progress-indicator"]')

      expect(indicator).toHaveStyle({ transform: 'translateX(-100%)' })
    })
  })

  describe('Value Validation', () => {
    test('handles values between 0 and 100', () => {
      const testValues = [25, 33.5, 66.7, 99]

      testValues.forEach((value) => {
        const { rerender } = render(<Progress value={value} data-testid={`progress-${value}`} />)
        const progress = screen.getByTestId(`progress-${value}`)
        const indicator = progress.querySelector('[data-slot="progress-indicator"]')

        expect(indicator).toHaveStyle({ transform: `translateX(-${100 - value}%)` })

        if (value !== testValues[testValues.length - 1]) {
          rerender(<></>)
        }
      })
    })

    test('handles edge case values gracefully', () => {
      // Test negative values
      render(<Progress value={-10} data-testid="negative-progress" />)
      let progress = screen.getByTestId('negative-progress')
      let indicator = progress.querySelector('[data-slot="progress-indicator"]')
      expect(indicator).toHaveStyle({ transform: 'translateX(-110%)' })

      // Test values over 100
      const { rerender } = render(<Progress value={150} data-testid="over-progress" />)
      progress = screen.getByTestId('over-progress')
      indicator = progress.querySelector('[data-slot="progress-indicator"]')
      expect(indicator).toHaveStyle({ transform: 'translateX(50%)' })
    })

    test('handles decimal values', () => {
      render(<Progress value={33.333} data-testid="decimal-progress" />)
      const progress = screen.getByTestId('decimal-progress')
      const indicator = progress.querySelector('[data-slot="progress-indicator"]')

      expect(indicator).toHaveStyle({ transform: 'translateX(-66.667%)' })
    })
  })

  describe('Custom Max Value', () => {
    test('respects max prop for custom ranges', () => {
      render(<Progress value={75} max={150} data-testid="custom-max-progress" />)
      const progress = screen.getByTestId('custom-max-progress')

      expect(progress).toHaveAttribute('max', '150')
      expect(progress).toHaveAttribute('value', '75')
    })

    test('calculates percentage correctly with custom max', () => {
      render(<Progress value={30} max={60} data-testid="custom-calc-progress" />)
      const progress = screen.getByTestId('custom-calc-progress')
      const indicator = progress.querySelector('[data-slot="progress-indicator"]')

      // 30/60 = 50%, so transform should be -50%
      expect(indicator).toHaveStyle({ transform: 'translateX(-50%)' })
    })
  })

  describe('Styling and Theme', () => {
    test('applies custom className', () => {
      render(<Progress className="custom-progress-class" data-testid="custom-progress" />)
      const progress = screen.getByTestId('custom-progress')

      expect(progress).toHaveClass('custom-progress-class')
      // Should maintain base classes
      expect(progress).toHaveClass('bg-primary/20', 'relative', 'h-2')
    })

    test('uses blue theme colors', () => {
      render(<Progress value={50} data-testid="themed-progress" />)
      const progress = screen.getByTestId('themed-progress')
      const indicator = progress.querySelector('[data-slot="progress-indicator"]')

      expect(progress).toHaveClass('bg-primary/20')
      expect(indicator).toHaveClass('bg-primary')
    })

    test('supports size customization via className', () => {
      render(<Progress className="h-4" value={50} data-testid="tall-progress" />)
      const progress = screen.getByTestId('tall-progress')

      expect(progress).toHaveClass('h-4')
    })

    test('indicator has proper styling', () => {
      render(<Progress value={75} data-testid="indicator-progress" />)
      const progress = screen.getByTestId('indicator-progress')
      const indicator = progress.querySelector('[data-slot="progress-indicator"]')

      expect(indicator).toHaveClass(
        'bg-primary',
        'h-full',
        'w-full',
        'flex-1',
        'transition-all'
      )
    })
  })

  describe('Accessibility', () => {
    test('has proper ARIA attributes', () => {
      render(
        <Progress
          value={60}
          aria-label="Upload progress"
          data-testid="aria-progress"
        />
      )
      const progress = screen.getByTestId('aria-progress')

      expect(progress).toHaveAttribute('aria-label', 'Upload progress')
      expect(progress).toHaveAttribute('value', '60')
    })

    test('supports aria-describedby', () => {
      render(
        <div>
          <Progress
            value={40}
            aria-describedby="progress-description"
            data-testid="described-progress"
          />
          <div id="progress-description">Loading files...</div>
        </div>
      )

      const progress = screen.getByTestId('described-progress')
      expect(progress).toHaveAttribute('aria-describedby', 'progress-description')
    })

    test('is accessible to screen readers', () => {
      render(<Progress value={80} data-testid="screen-reader-progress" />)
      const progress = screen.getByTestId('screen-reader-progress')

      // Should be accessible as a progress element
      expect(progress).toBeInTheDocument()
      expect(progress).toHaveAttribute('value', '80')
    })

    test('handles aria-label for context', () => {
      render(
        <Progress
          value={25}
          aria-label="File upload progress: 25%"
          data-testid="labeled-progress"
        />
      )

      const progress = screen.getByTestId('labeled-progress')
      expect(progress).toHaveAttribute('aria-label', 'File upload progress: 25%')
    })
  })

  describe('Animation and Transitions', () => {
    test('indicator has transition classes', () => {
      render(<Progress value={50} data-testid="animated-progress" />)
      const progress = screen.getByTestId('animated-progress')
      const indicator = progress.querySelector('[data-slot="progress-indicator"]')

      expect(indicator).toHaveClass('transition-all')
    })

    test('smooth value updates', () => {
      const { rerender } = render(<Progress value={20} data-testid="smooth-progress" />)
      let progress = screen.getByTestId('smooth-progress')
      let indicator = progress.querySelector('[data-slot="progress-indicator"]')

      expect(indicator).toHaveStyle({ transform: 'translateX(-80%)' })

      // Update value
      rerender(<Progress value={60} data-testid="smooth-progress" />)
      progress = screen.getByTestId('smooth-progress')
      indicator = progress.querySelector('[data-slot="progress-indicator"]')

      expect(indicator).toHaveStyle({ transform: 'translateX(-40%)' })
      expect(indicator).toHaveClass('transition-all')
    })
  })

  describe('Component Integration', () => {
    test('works with Radix UI Progress primitive props', () => {
      render(
        <Progress
          value={70}
          max={100}
          data-testid="radix-progress"
          onValueChange={() => {}}
        />
      )

      const progress = screen.getByTestId('radix-progress')
      expect(progress).toHaveAttribute('max', '100')
      expect(progress).toHaveAttribute('value', '70')
    })

    test('forwards ref correctly', () => {
      const progressRef = React.createRef<HTMLDivElement>()
      render(<Progress ref={progressRef} value={45} />)

      expect(progressRef.current).toBeInstanceOf(HTMLDivElement)
      expect(progressRef.current).toHaveAttribute('value', '45')
    })

    test('spreads additional props', () => {
      render(
        <Progress
          value={35}
          data-testid="props-progress"
          id="custom-progress-id"
          role="progressbar"
        />
      )

      const progress = screen.getByTestId('props-progress')
      expect(progress).toHaveAttribute('id', 'custom-progress-id')
      expect(progress).toHaveAttribute('role', 'progressbar')
    })
  })

  describe('Visual States', () => {
    test('empty state (0%)', () => {
      render(<Progress value={0} data-testid="empty-state" />)
      const progress = screen.getByTestId('empty-state')
      const indicator = progress.querySelector('[data-slot="progress-indicator"]')

      expect(progress).toHaveClass('bg-primary/20')
      expect(indicator).toHaveStyle({ transform: 'translateX(-100%)' })
    })

    test('partial state (50%)', () => {
      render(<Progress value={50} data-testid="partial-state" />)
      const progress = screen.getByTestId('partial-state')
      const indicator = progress.querySelector('[data-slot="progress-indicator"]')

      expect(indicator).toHaveStyle({ transform: 'translateX(-50%)' })
    })

    test('complete state (100%)', () => {
      render(<Progress value={100} data-testid="complete-state" />)
      const progress = screen.getByTestId('complete-state')
      const indicator = progress.querySelector('[data-slot="progress-indicator"]')

      expect(indicator).toHaveStyle({ transform: 'translateX(-0%)' })
    })

    test('indeterminate state (no value)', () => {
      render(<Progress data-testid="indeterminate-state" />)
      const progress = screen.getByTestId('indeterminate-state')
      const indicator = progress.querySelector('[data-slot="progress-indicator"]')

      expect(indicator).toHaveStyle({ transform: 'translateX(-100%)' })
    })
  })

  describe('Edge Cases', () => {
    test('handles rapid value changes', () => {
      const { rerender } = render(<Progress value={0} data-testid="rapid-progress" />)

      const values = [10, 25, 50, 75, 90, 100]
      values.forEach((value) => {
        rerender(<Progress value={value} data-testid="rapid-progress" />)
        const progress = screen.getByTestId('rapid-progress')
        const indicator = progress.querySelector('[data-slot="progress-indicator"]')
        expect(indicator).toHaveStyle({ transform: `translateX(-${100 - value}%)` })
      })
    })

    test('handles null and undefined values', () => {
      render(<Progress value={undefined} data-testid="undefined-progress" />)
      const progress = screen.getByTestId('undefined-progress')
      const indicator = progress.querySelector('[data-slot="progress-indicator"]')

      expect(indicator).toHaveStyle({ transform: 'translateX(-100%)' })
    })

    test('maintains performance with complex className combinations', () => {
      render(
        <Progress
          value={42}
          className="h-3 bg-secondary/20 rounded-sm custom-class another-class"
          data-testid="complex-progress"
        />
      )

      const progress = screen.getByTestId('complex-progress')
      expect(progress).toHaveClass(
        'h-3',
        'bg-secondary/20',
        'rounded-sm',
        'custom-class',
        'another-class'
      )
      // Should maintain base functionality
      const indicator = progress.querySelector('[data-slot="progress-indicator"]')
      expect(indicator).toHaveStyle({ transform: 'translateX(-58%)' })
    })

    test('works with very small values', () => {
      render(<Progress value={0.1} data-testid="tiny-progress" />)
      const progress = screen.getByTestId('tiny-progress')
      const indicator = progress.querySelector('[data-slot="progress-indicator"]')

      expect(indicator).toHaveStyle({ transform: 'translateX(-99.9%)' })
    })

    test('works with very large max values', () => {
      render(<Progress value={500} max={1000} data-testid="large-max-progress" />)
      const progress = screen.getByTestId('large-max-progress')
      const indicator = progress.querySelector('[data-slot="progress-indicator"]')

      // 500/1000 = 50%
      expect(indicator).toHaveStyle({ transform: 'translateX(-50%)' })
    })
  })
})