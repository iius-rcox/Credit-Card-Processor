# Component API Contracts

**Date**: 2025-10-03
**Feature**: 002-replace-all-front

## Overview

This document defines the API contracts for shadcn/ui components that must be preserved during migration. Each component must maintain backward compatibility with existing usage patterns.

## Button Component

### Interface Contract
```typescript
interface ButtonProps {
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link'
  size?: 'default' | 'sm' | 'lg' | 'icon'
  asChild?: boolean
  disabled?: boolean
  className?: string
  children: React.ReactNode
  onClick?: (event: MouseEvent<HTMLButtonElement>) => void
  type?: 'button' | 'submit' | 'reset'
}
```

### Blue Theme Application
- `variant="default"`: Uses --primary background color (blue)
- `variant="outline"`: Uses --primary border color (blue)
- Focus ring: Uses --ring color (blue)
- Hover states: Blue color variations

### Validation Requirements
- All variants must render with blue theme colors
- Existing onClick handlers must be preserved
- Disabled state must work correctly
- Focus/hover states must use blue variations

## Card Component

### Interface Contract
```typescript
interface CardProps {
  className?: string
  children: React.ReactNode
}

interface CardHeaderProps {
  className?: string
  children: React.ReactNode
}

interface CardTitleProps {
  className?: string
  children: React.ReactNode
}

interface CardDescriptionProps {
  className?: string
  children: React.ReactNode
}

interface CardContentProps {
  className?: string
  children: React.ReactNode
}

interface CardFooterProps {
  className?: string
  children: React.ReactNode
}
```

### Blue Theme Application
- Card border: Uses --border color (blue-tinted)
- Card background: Uses --card color
- Card content: Uses --card-foreground color

### Validation Requirements
- Card structure (Header/Content/Footer) must be preserved
- Existing card layouts must not break
- Responsive behavior must be maintained

## Input Component

### Interface Contract
```typescript
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  className?: string
  type?: string
  placeholder?: string
  disabled?: boolean
  value?: string
  defaultValue?: string
  onChange?: (event: ChangeEvent<HTMLInputElement>) => void
}
```

### Blue Theme Application
- Border: Uses --border color (blue-tinted)
- Focus border: Uses --ring color (blue)
- Background: Uses --background color

### Validation Requirements
- All HTML input attributes must be supported
- Focus states must show blue ring
- Error states must work with form validation

## Label Component

### Interface Contract
```typescript
interface LabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {
  className?: string
  htmlFor?: string
  children: React.ReactNode
}
```

### Blue Theme Application
- Text color: Uses --foreground color
- Associated input focus: May highlight label

### Validation Requirements
- htmlFor association must work correctly
- Form accessibility must be preserved

## Alert Component

### Interface Contract
```typescript
interface AlertProps {
  variant?: 'default' | 'destructive'
  className?: string
  children: React.ReactNode
}

interface AlertTitleProps {
  className?: string
  children: React.ReactNode
}

interface AlertDescriptionProps {
  className?: string
  children: React.ReactNode
}
```

### Blue Theme Application
- `variant="default"`: Uses --accent background (blue)
- `variant="destructive"`: Uses --destructive background (red)
- Border colors match background variants

### Validation Requirements
- Alert content must remain readable
- Icon colors must match theme variants
- Multiple alert types must be distinguishable

## Progress Component

### Interface Contract
```typescript
interface ProgressProps {
  value?: number
  max?: number
  className?: string
  'aria-label'?: string
  'aria-describedby'?: string
}
```

### Blue Theme Application
- Progress fill: Uses --primary color (blue)
- Progress background: Uses --secondary color
- Track color: Muted variant

### Validation Requirements
- Progress animation must work smoothly
- Value updates must be visually smooth
- Accessibility attributes must be preserved

## Form Component

### Interface Contract
```typescript
interface FormFieldProps {
  control: Control<any>
  name: string
  render: ({ field, fieldState, formState }) => React.ReactElement
}

interface FormItemProps {
  className?: string
  children: React.ReactNode
}

interface FormLabelProps {
  className?: string
  children: React.ReactNode
}

interface FormControlProps {
  className?: string
  children: React.ReactNode
}

interface FormDescriptionProps {
  className?: string
  children: React.ReactNode
}

interface FormMessageProps {
  className?: string
  children?: React.ReactNode
}
```

### Blue Theme Application
- Error messages: Uses --destructive color (red)
- Success indicators: Uses --primary color (blue)
- Focus indicators: Uses --ring color (blue)

### Validation Requirements
- react-hook-form integration must work
- Validation error display must be clear
- Form submission states must be preserved

## Theme Detection Contract

### Interface Contract
```typescript
interface ThemeDetection {
  supportsOKLCH(): boolean
  showCompatibilityWarning(): void
  dismissWarning(): void
  isWarningDismissed(): boolean
}
```

### Implementation Requirements
```typescript
// Browser support detection
const supportsOKLCH = CSS.supports('color', 'oklch(0.5 0.2 180)');

// Warning display logic
if (!supportsOKLCH && !isWarningDismissed()) {
  showCompatibilityWarning();
}
```

### Validation Requirements
- Detection must run early in application lifecycle
- Warning must be user-dismissible
- localStorage must persist dismissal state
- Functionality must work even without OKLCH support

## Contract Testing Strategy

### Component Testing
Each component contract will be validated through:

1. **Props Interface Testing**
   ```typescript
   // Ensure all required props are accepted
   expect(() => render(<Button>Click me</Button>)).not.toThrow();
   expect(() => render(<Button variant="default">Click me</Button>)).not.toThrow();
   ```

2. **Theme Application Testing**
   ```typescript
   // Verify blue theme CSS variables are applied
   const button = render(<Button variant="default">Click me</Button>);
   expect(button.getByRole('button')).toHaveClass('bg-primary');
   ```

3. **Existing Functionality Testing**
   ```typescript
   // Verify existing behavior is preserved
   const handleClick = jest.fn();
   const button = render(<Button onClick={handleClick}>Click me</Button>);
   fireEvent.click(button.getByRole('button'));
   expect(handleClick).toHaveBeenCalled();
   ```

### Integration Testing
- Upload form with all components working together
- Progress display with theme transitions
- Results panel with various alert states

### Visual Testing
- Storybook stories for all component states
- Light/dark mode theme switching
- Browser compatibility warnings

## Migration Compatibility

### Existing Usage Patterns
All existing component usage must continue working:

```jsx
// Before (existing usage)
<Button onClick={handleClick} disabled={loading}>
  Submit
</Button>

// After (must still work identically)
<Button onClick={handleClick} disabled={loading}>
  Submit
</Button>
```

### Breaking Changes Not Allowed
- No changes to prop names or types
- No removal of supported variants
- No changes to event handler signatures
- No changes to component structure for compound components

### Acceptable Changes
- CSS class names (internal implementation)
- Visual styling (colors, spacing, typography)
- DOM structure (as long as accessibility is preserved)
- Performance optimizations

## Success Criteria

### Functional Validation
- [ ] All existing tests pass without modification
- [ ] All component props work as documented
- [ ] All event handlers trigger correctly
- [ ] All form validation continues working

### Visual Validation
- [ ] All components display with blue theme colors
- [ ] Light/dark mode switching works correctly
- [ ] Focus/hover states use blue variations
- [ ] Browser compatibility warning displays when needed

### Integration Validation
- [ ] Upload form workflow works end-to-end
- [ ] Progress tracking displays correctly
- [ ] Results panel shows appropriate alerts
- [ ] Theme detection works across all components