# Component API Contract: ThemeToggle

**Feature**: 004-change-the-dark
**Component**: `components/theme-toggle.tsx`
**Date**: 2025-10-04

## Component Signature

```typescript
import { ThemeToggle } from '@/components/theme-toggle';

<ThemeToggle
  className?: string
  size?: 'sm' | 'md' | 'lg'
  showTooltip?: boolean
  onThemeChange?: (theme: 'light' | 'dark') => void
/>
```

---

## Props

### `className` (optional)
- **Type**: `string`
- **Default**: `undefined`
- **Description**: Additional CSS classes to apply to the button element for custom positioning or styling
- **Example**: `className="mr-4"` to add right margin

### `size` (optional)
- **Type**: `'sm' | 'md' | 'lg'`
- **Default**: `'md'`
- **Description**: Icon size variant
  - `'sm'`: 16px icon (h-4 w-4)
  - `'md'`: 20px icon (h-5 w-5) - Default desktop size
  - `'lg'`: 24px icon (h-6 w-6) - Default mobile size
- **Note**: Responsive sizing overrides this on mobile (automatically larger)

### `showTooltip` (optional)
- **Type**: `boolean`
- **Default**: `true`
- **Description**: Whether to show tooltip on hover. Set to `false` to disable.

### `onThemeChange` (optional)
- **Type**: `(theme: 'light' | 'dark') => void`
- **Default**: `undefined`
- **Description**: Callback fired when theme changes. Receives the new theme mode.
- **Example**:
  ```typescript
  <ThemeToggle onThemeChange={(theme) => {
    console.log('Theme changed to:', theme);
    analytics.track('theme_toggle', { theme });
  }} />
  ```

---

## Accessibility

### ARIA Attributes
```typescript
<button
  role="button"
  aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
  tabIndex={0}
>
```

### Keyboard Support
- **Tab**: Focus the button
- **Enter / Space**: Toggle theme
- **Escape** (when tooltip open): Close tooltip

### Screen Reader
- Icon hidden: `aria-hidden="true"` on SVG
- Button label: Dynamic `aria-label` describes action
- Tooltip: Managed by Radix UI with proper ARIA attributes

---

## Visual States

### Default State
```typescript
// Light mode
<Moon className="h-5 w-5 text-foreground" />

// Dark mode
<Sun className="h-5 w-5 text-foreground" />
```

### Hover State
```typescript
className="hover:bg-accent hover:text-accent-foreground transition-colors"
```

### Focus State
```typescript
className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
```

### Pressed State
```typescript
className="active:scale-95 transition-transform"
```

---

## Responsive Behavior

### Breakpoints
```typescript
// Mobile (<768px): Larger touch target
<button className="h-11 w-11 md:h-9 md:w-9">
  <Moon className="h-6 w-6 md:h-5 md:w-5" />
</button>

// Desktop (≥768px): Subtle size
```

### Touch Target
- Minimum 44x44px on mobile (WCAG guideline)
- Implementation: 28px icon + 16px padding = 44px total

---

## Usage Examples

### Basic Usage (Root Layout)
```typescript
// app/layout.tsx
import { ThemeToggle } from '@/components/theme-toggle';

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <header className="fixed top-4 right-4 z-40">
          <ThemeToggle />
        </header>
        {children}
      </body>
    </html>
  );
}
```

### With Custom Positioning
```typescript
<nav className="flex items-center space-x-4">
  <Link href="/">Home</Link>
  <Link href="/about">About</Link>
  <ThemeToggle className="ml-auto" />
</nav>
```

### With Callback
```typescript
<ThemeToggle
  onThemeChange={(theme) => {
    // Track theme changes
    posthog.capture('theme_toggle', { theme });
  }}
/>
```

### Without Tooltip
```typescript
<ThemeToggle showTooltip={false} />
```

---

## Internal State (Not Exposed)

```typescript
interface InternalState {
  isDark: boolean;          // Current theme mode
  hasHydrated: boolean;     // Client-side hydration complete
  isHovered: boolean;       // Hover state for tooltip
}
```

---

## Dependencies

### Required
- `react`: React 19+
- `lucide-react`: Icons (Moon, Sun)
- `@/components/ui/tooltip`: Radix UI tooltip (shadcn/ui)
- `@/lib/theme-storage`: Storage abstraction
- `@/lib/theme-detection`: System preference detection
- `@/lib/utils`: `cn()` utility for class merging

### CSS
- Tailwind CSS 4.x
- CSS variables from `app/globals.css`:
  - `--accent`, `--accent-foreground`
  - `--ring`
  - `--foreground`

---

## Testing Contract

### Unit Tests
```typescript
describe('ThemeToggle', () => {
  it('renders Moon icon in light mode', () => {
    render(<ThemeToggle />);
    expect(screen.getByLabelText(/switch to dark mode/i)).toBeInTheDocument();
  });

  it('renders Sun icon in dark mode', () => {
    // Set up dark mode
    render(<ThemeToggle />);
    expect(screen.getByLabelText(/switch to light mode/i)).toBeInTheDocument();
  });

  it('toggles theme on click', () => {
    const onChange = jest.fn();
    render(<ThemeToggle onThemeChange={onChange} />);

    const button = screen.getByRole('button');
    fireEvent.click(button);

    expect(onChange).toHaveBeenCalledWith('dark');
  });

  it('is keyboard accessible', () => {
    render(<ThemeToggle />);

    const button = screen.getByRole('button');
    button.focus();

    fireEvent.keyDown(button, { key: 'Enter' });
    // Verify theme toggled
  });

  it('shows tooltip on hover when showTooltip=true', async () => {
    render(<ThemeToggle showTooltip={true} />);

    const button = screen.getByRole('button');
    fireEvent.mouseEnter(button);

    await waitFor(() => {
      expect(screen.getByRole('tooltip')).toBeInTheDocument();
    });
  });

  it('does not show tooltip when showTooltip=false', () => {
    render(<ThemeToggle showTooltip={false} />);

    const button = screen.getByRole('button');
    fireEvent.mouseEnter(button);

    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();
  });
});
```

### Storybook Stories
```typescript
export const Default: Story = {};

export const LightMode: Story = {
  parameters: {
    theme: 'light',
  },
};

export const DarkMode: Story = {
  parameters: {
    theme: 'dark',
  },
};

export const WithoutTooltip: Story = {
  args: {
    showTooltip: false,
  },
};

export const WithCallback: Story = {
  args: {
    onThemeChange: (theme) => console.log('Theme changed:', theme),
  },
};
```

---

## Performance

### Render Optimization
- Memoize icon components to prevent unnecessary re-renders
- Debounce not needed (instant toggle is desired)
- Use `useEffect` for side effects (DOM updates, storage)

### Bundle Size
- lucide-react icons are tree-shakeable (only Moon and Sun imported)
- Estimated component size: ~2KB (gzipped)

---

## Migration Notes

### From Existing Button (index.html)
**Before**:
```html
<button id="theme-toggle" class="btn btn-outline">
  <span id="theme-text">🌙 Switch to Dark Mode</span>
</button>
```

**After**:
```typescript
<ThemeToggle />
```

**Removed Code**:
- `index.html` lines 306-310 (button markup)
- `index.html` lines 439-460 (theme toggle JS)

**Preserved Functionality**:
- ✅ localStorage persistence
- ✅ Theme application to `<html>` class
- ✅ Icon swap on toggle
- ➕ **New**: System preference detection
- ➕ **New**: Tooltip
- ➕ **New**: Responsive sizing
- ➕ **New**: Storage fallback

---

**Contract Status**: ✅ COMPLETE
**Related**: [theme-state.md](./theme-state.md)
