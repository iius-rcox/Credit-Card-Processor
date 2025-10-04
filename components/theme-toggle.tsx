"use client"

/**
 * ThemeToggle Component
 * Feature: 004-change-the-dark
 * Task: T019
 *
 * A subtle icon-based theme toggle positioned in the top-right corner.
 * Supports system preference detection, manual override, and graceful storage fallback.
 *
 * ## Features
 * - **System Preference Detection**: Automatically detects OS dark mode on first visit
 * - **Manual Override**: User selection overrides system preference
 * - **Storage Fallback**: localStorage → sessionStorage → in-memory
 * - **SSR Safe**: No hydration mismatches in Next.js
 * - **Accessible**: Keyboard navigation, ARIA labels, screen reader support
 * - **Responsive**: Larger touch targets on mobile (<768px)
 *
 * ## Usage
 *
 * ### Basic (default settings)
 * ```tsx
 * import { ThemeToggle } from '@/components/theme-toggle';
 *
 * export default function Layout({ children }) {
 *   return (
 *     <html lang="en">
 *       <body>
 *         <header className="fixed top-4 right-4 z-40">
 *           <ThemeToggle />
 *         </header>
 *         {children}
 *       </body>
 *     </html>
 *   );
 * }
 * ```
 *
 * ### With callback
 * ```tsx
 * <ThemeToggle
 *   onThemeChange={(theme) => {
 *     console.log('Theme changed to:', theme);
 *     analytics.track('theme_toggle', { theme });
 *   }}
 * />
 * ```
 *
 * ### Without tooltip
 * ```tsx
 * <ThemeToggle showTooltip={false} />
 * ```
 *
 * ### Custom size
 * ```tsx
 * <ThemeToggle size="lg" />
 * ```
 *
 * ### Custom positioning
 * ```tsx
 * <nav className="flex items-center space-x-4">
 *   <Link href="/">Home</Link>
 *   <ThemeToggle className="ml-auto" />
 * </nav>
 * ```
 *
 * ## Accessibility
 * - ✅ Semantic `<button>` element
 * - ✅ Keyboard navigation (Tab, Enter, Space)
 * - ✅ Dynamic ARIA labels ("Switch to dark mode" / "Switch to light mode")
 * - ✅ Focus indicators (visible outline)
 * - ✅ Icons hidden from screen readers (aria-hidden="true")
 * - ✅ Touch target ≥44px on mobile (WCAG 2.1)
 *
 * ## Theme Priority
 * 1. **Manual selection** (highest priority) - User clicked toggle
 * 2. **System preference** - OS/browser dark mode setting
 * 3. **Default** (light) - Fallback when no preference
 *
 * ## Browser Support
 * - Chrome 76+ (matchMedia API)
 * - Safari 14+
 * - Firefox 67+
 * - Edge 79+
 *
 * Older browsers gracefully degrade to light mode (default).
 */

import React, { useState, useEffect } from 'react';
import { Moon, Sun } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { themeStorage } from '@/lib/theme-storage';
import { detectSystemTheme, watchSystemTheme } from '@/lib/theme-detection';
import { cn } from '@/lib/utils';
import type { ThemeMode } from '@/types/theme';

/**
 * Props for ThemeToggle component
 */
export interface ThemeToggleProps {
  /** Additional CSS classes for custom positioning/styling */
  className?: string;
  /** Icon size variant (default: 'md') */
  size?: 'sm' | 'md' | 'lg';
  /** Whether to show tooltip on hover (default: true) */
  showTooltip?: boolean;
  /** Callback fired when theme changes */
  onThemeChange?: (theme: ThemeMode) => void;
}

/**
 * Apply theme to document
 */
function applyTheme(mode: ThemeMode): void {
  if (typeof document === 'undefined') return;

  if (mode === 'dark') {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
}

/**
 * ThemeToggle Component
 *
 * Displays a moon icon (light mode) or sun icon (dark mode) that toggles the theme.
 * Detects system preference on first visit, manual selection overrides system.
 */
export function ThemeToggle({
  className,
  size = 'md',
  showTooltip = true,
  onThemeChange,
}: ThemeToggleProps) {
  const [theme, setTheme] = useState<ThemeMode>('light');
  const [hasHydrated, setHasHydrated] = useState(false);

  // Size variants for button
  const buttonSizeClasses = {
    sm: 'h-8 w-8 md:h-7 md:w-7',
    md: 'h-11 w-11 md:h-9 md:w-9',
    lg: 'h-12 w-12 md:h-10 md:w-10',
  };

  // Size variants for icon
  const iconSizeClasses = {
    sm: 'h-4 w-4 md:h-3 md:w-3',
    md: 'h-6 w-6 md:h-5 md:w-5',
    lg: 'h-7 w-7 md:h-6 md:w-6',
  };

  // Initialize theme on client-side mount (SSR safety)
  useEffect(() => {
    setHasHydrated(true);

    // Priority 1: Check for manual preference (highest priority)
    const savedTheme = themeStorage.getTheme();
    const savedSource = themeStorage.getThemeSource();

    if (savedTheme && savedSource === 'manual') {
      setTheme(savedTheme);
      applyTheme(savedTheme);
      return;
    }

    // Priority 2: Detect system preference
    const systemTheme = detectSystemTheme();
    setTheme(systemTheme);
    applyTheme(systemTheme);

    // Save as system source
    themeStorage.setTheme(systemTheme);
    themeStorage.setThemeSource('system');
  }, []);

  // Watch for system preference changes (only if not manual override)
  useEffect(() => {
    if (!hasHydrated) return;

    const cleanup = watchSystemTheme((newSystemTheme) => {
      const currentSource = themeStorage.getThemeSource();

      // Only apply system changes if source is NOT manual
      if (currentSource !== 'manual') {
        setTheme(newSystemTheme);
        applyTheme(newSystemTheme);

        // Update storage with new system preference
        themeStorage.setTheme(newSystemTheme);
        themeStorage.setThemeSource('system');
      }
    });

    return cleanup; // Remove listener on unmount
  }, [hasHydrated]);

  // Handle theme toggle
  const handleToggle = () => {
    const newTheme: ThemeMode = theme === 'dark' ? 'light' : 'dark';

    // Update state and DOM
    setTheme(newTheme);
    applyTheme(newTheme);

    // Save as manual preference (overrides system)
    themeStorage.setTheme(newTheme);
    themeStorage.setThemeSource('manual');

    // Call optional callback
    if (onThemeChange) {
      onThemeChange(newTheme);
    }
  };

  // SSR: Render placeholder to avoid hydration mismatch
  if (!hasHydrated) {
    return (
      <div
        className={cn(buttonSizeClasses[size], className)}
        aria-hidden="true"
      />
    );
  }

  // Tooltip text based on current theme
  const tooltipText = theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';

  // Icon component based on current theme
  const IconComponent = theme === 'dark' ? Sun : Moon;

  // Button with optional tooltip
  const button = (
    <button
      onClick={handleToggle}
      aria-label={tooltipText}
      className={cn(
        // Base styles
        'rounded-md transition-all',
        'flex items-center justify-center flex-shrink-0',
        // Hover state
        'hover:bg-accent hover:text-accent-foreground',
        // Focus state
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
        // Active state
        'active:scale-95',
        // Size
        buttonSizeClasses[size],
        // Custom classes
        className
      )}
    >
      <IconComponent
        className={cn(iconSizeClasses[size], 'text-foreground')}
        aria-hidden="true"
      />
    </button>
  );

  // Wrap in tooltip if enabled
  if (showTooltip) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            {button}
          </TooltipTrigger>
          <TooltipContent>
            <p>{tooltipText}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  // Return button without tooltip
  return button;
}
