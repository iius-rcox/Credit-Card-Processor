# Data Model: Replace Front-End UI with shadcn/ui Blue Theme

**Date**: 2025-10-03
**Feature**: 002-replace-all-front

## Overview
This feature involves UI theming and component migration. The "data model" consists of theme configuration, component variants, and browser capability detection.

## Entity: Theme Configuration

### Purpose
Defines the blue color palette and visual design tokens for the application theme.

### Attributes

#### Color Variables (OKLCH Format)
- `--background`: oklch(lightness chroma hue) - Page background
- `--foreground`: oklch(lightness chroma hue) - Primary text color
- `--primary`: oklch(lightness chroma hue) - Primary blue brand color
- `--primary-foreground`: oklch(lightness chroma hue) - Text on primary
- `--secondary`: oklch(lightness chroma hue) - Secondary UI elements
- `--secondary-foreground`: oklch(lightness chroma hue) - Text on secondary
- `--accent`: oklch(lightness chroma hue) - Accent/highlight color
- `--accent-foreground`: oklch(lightness chroma hue) - Text on accent
- `--muted`: oklch(lightness chroma hue) - Muted backgrounds
- `--muted-foreground`: oklch(lightness chroma hue) - Muted text
- `--destructive`: oklch(lightness chroma hue) - Error/danger color
- `--destructive-foreground`: oklch(lightness chroma hue) - Text on destructive
- `--border`: oklch(lightness chroma hue) - Border color
- `--input`: oklch(lightness chroma hue) - Input border color
- `--ring`: oklch(lightness chroma hue) - Focus ring color
- `--card`: oklch(lightness chroma hue) - Card background
- `--card-foreground`: oklch(lightness chroma hue) - Card text
- `--popover`: oklch(lightness chroma hue) - Popover background
- `--popover-foreground`: oklch(lightness chroma hue) - Popover text

#### Radius Variables
- `--radius`: Base border radius value (e.g., 0.5rem)
- `--radius-sm`: Small radius (calc(var(--radius) - 4px))
- `--radius-md`: Medium radius (calc(var(--radius) - 2px))
- `--radius-lg`: Large radius (var(--radius))
- `--radius-xl`: Extra large radius (calc(var(--radius) + 4px))

### States
- **Light Mode** (`:root`): Applied by default
- **Dark Mode** (`.dark`): Applied when dark class present on html/body

### Validation Rules
- All OKLCH values must have valid lightness (0-1), chroma (0+), and hue (0-360)
- Contrast ratios verified through visual review (no automated check)
- Colors must be visually distinct for different semantic roles

### Relationships
- Consumed by: Component Library entity
- Defined in: `app/globals.css`
- Referenced by: Tailwind utility classes via @theme directive

## Entity: Component Library

### Purpose
Collection of shadcn/ui components that consume theme configuration and provide UI building blocks.

### Components

#### Button
**Variants**:
- `default`: Primary blue background
- `destructive`: Destructive/error action
- `outline`: Bordered with transparent background
- `secondary`: Secondary gray background
- `ghost`: No background, hover effect only
- `link`: Text-only, link styling

**Sizes**:
- `default`: Standard padding
- `sm`: Small padding
- `lg`: Large padding
- `icon`: Square, icon-only

**States**:
- Default, Hover, Focus, Active, Disabled

#### Card
**Variants**:
- `default`: Standard card with border

**Parts**:
- CardHeader, CardTitle, CardDescription, CardContent, CardFooter

**States**:
- Default, Hover

#### Input
**Variants**:
- `default`: Standard input field

**States**:
- Default, Focus, Disabled, Error (via form)

#### Label
**Variants**:
- `default`: Standard label

**States**:
- Default, Disabled

#### Alert
**Variants**:
- `default`: Informational alert
- `destructive`: Error/warning alert

**Parts**:
- Alert container, AlertTitle, AlertDescription

**States**:
- Default, Dismissible

#### Progress
**Variants**:
- `default`: Blue progress bar

**Attributes**:
- `value`: 0-100 percentage
- `max`: Maximum value (default 100)

**States**:
- Indeterminate, Determinate

#### Form
**Parts**:
- FormField, FormItem, FormLabel, FormControl, FormDescription, FormMessage

**States**:
- Valid, Invalid, Disabled

### Relationships
- Depends on: Theme Configuration entity
- Used by: Page components (upload-form, progress-display, results-panel)
- Composed with: Radix UI primitives

## Entity: Browser Capability

### Purpose
Detects browser support for OKLCH color format and manages fallback behavior.

### Attributes
- `supportsOKLCH`: boolean - Whether browser supports OKLCH
- `warningDisplayed`: boolean - Whether warning shown to user
- `fallbackApplied`: boolean - Whether degraded mode active

### Detection Logic
```typescript
// Check OKLCH support
const supportsOKLCH = CSS.supports('color', 'oklch(0.5 0.2 180)');

// Alternative check
const supportsOKLCH = window.CSS?.supports?.('color', 'oklch(0.5 0.2 180)') ?? false;
```

### States
- **Supported**: Browser supports OKLCH, full theme active
- **Unsupported + Warned**: Browser lacks OKLCH, warning displayed, degraded colors
- **Unsupported + Not Warned**: Initial state before detection

### Validation Rules
- Detection must run early in application lifecycle
- Warning must be dismissible but persist across page refreshes (localStorage)
- Degraded mode must not break functionality (FR-011)

### Relationships
- Affects: Theme Configuration rendering
- Triggers: User warning/notification
- Stored in: Browser localStorage (warning dismissal state)

## Component Migration Map

### Existing Components → shadcn/ui Equivalents

| Current Component | shadcn/ui Component | Migration Notes |
|-------------------|---------------------|-----------------|
| Button | @/components/ui/button | Direct replacement, check variants |
| Card | @/components/ui/card | Use CardHeader, CardContent parts |
| Input | @/components/ui/input | Direct replacement |
| Label | @/components/ui/label | Direct replacement |
| Alert | @/components/ui/alert | Use AlertDescription part |
| Progress | @/components/ui/progress | Direct replacement |
| Form | @/components/ui/form | Integrate with react-hook-form |

### Page-Level Usage

#### upload-form.tsx
- Uses: Card, Button, Input, Label, Alert
- Theme impact: Primary actions use blue primary color
- States: Upload, uploading, success, error

#### progress-display.tsx
- Uses: Card, Progress, Alert
- Theme impact: Progress bar uses blue primary color
- States: Processing, complete, error

#### results-panel.tsx
- Uses: Card, Button, Alert
- Theme impact: Action buttons use blue variants
- States: Success, partial success, error

## Storybook Story Structure

### Story Organization
```
stories/
├── Button.stories.tsx       # All button variants + states
├── Card.stories.tsx         # Card compositions
├── Input.stories.tsx        # Input states (focus, error, disabled)
├── Label.stories.tsx        # Label variants
├── Alert.stories.tsx        # Alert variants (info, destructive)
├── Progress.stories.tsx     # Progress states (0%, 50%, 100%, indeterminate)
├── Form.stories.tsx         # Form validation states
├── UploadForm.stories.tsx   # Integrated upload form
├── ProgressDisplay.stories.tsx  # Integrated progress view
└── ResultsPanel.stories.tsx     # Integrated results view
```

### Story Coverage
Each story must demonstrate:
1. All variants (per component)
2. All states (default, hover, focus, disabled, error)
3. Light mode rendering
4. Dark mode rendering
5. Responsive behavior

## Design Tokens Summary

### Blue Theme Palette (Conceptual)
Based on shadcn/ui blue base color:
- **Primary Blue**: Rich, saturated blue for CTAs
- **Secondary Gray**: Neutral grays for secondary actions
- **Accent Blue**: Lighter/darker blue variants for accents
- **Destructive Red**: Warm red for errors/warnings
- **Muted Grays**: Low saturation for backgrounds/disabled states

### Spacing (Inherited from Tailwind)
- Uses standard Tailwind spacing scale
- Component-specific padding via CVA variants

### Typography (Inherited from Next.js)
- Font family: Geist Sans (already configured)
- Font sizes: Tailwind typography scale
- Line heights: Standard Tailwind values
