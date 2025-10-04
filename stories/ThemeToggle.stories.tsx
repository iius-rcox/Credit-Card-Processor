/**
 * Storybook Stories for ThemeToggle Component
 * Feature: 004-change-the-dark
 * Task: T022
 */

import type { Meta, StoryObj } from '@storybook/react';
import { ThemeToggle } from '@/components/theme-toggle';

const meta = {
  title: 'Components/ThemeToggle',
  component: ThemeToggle,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A subtle icon-based theme toggle that supports system preference detection, manual override, and graceful storage fallback.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    className: {
      control: 'text',
      description: 'Additional CSS classes for custom positioning/styling',
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
      description: 'Icon size variant',
    },
    showTooltip: {
      control: 'boolean',
      description: 'Whether to show tooltip on hover',
    },
    onThemeChange: {
      action: 'themeChanged',
      description: 'Callback fired when theme changes',
    },
  },
} satisfies Meta<typeof ThemeToggle>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Default state with all default props
 */
export const Default: Story = {
  args: {},
};

/**
 * Light mode - Shows moon icon
 */
export const LightMode: Story = {
  args: {},
  parameters: {
    backgrounds: {
      default: 'light',
    },
  },
};

/**
 * Dark mode - Shows sun icon
 */
export const DarkMode: Story = {
  args: {},
  parameters: {
    backgrounds: {
      default: 'dark',
    },
  },
  decorators: [
    (Story) => {
      // Apply dark class to simulate dark mode
      if (typeof document !== 'undefined') {
        document.documentElement.classList.add('dark');
      }
      return <Story />;
    },
  ],
};

/**
 * With tooltip enabled (default behavior)
 */
export const WithTooltip: Story = {
  args: {
    showTooltip: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'Tooltip appears on hover, showing the action ("Switch to dark mode" or "Switch to light mode").',
      },
    },
  },
};

/**
 * Without tooltip
 */
export const WithoutTooltip: Story = {
  args: {
    showTooltip: false,
  },
  parameters: {
    docs: {
      description: {
        story: 'Icon displays without tooltip for minimal UI.',
      },
    },
  },
};

/**
 * With callback function
 */
export const WithCallback: Story = {
  args: {
    onThemeChange: (theme) => {
      console.log('Theme changed to:', theme);
    },
  },
  parameters: {
    docs: {
      description: {
        story: 'Callback is triggered when theme changes. Check the Actions panel to see events.',
      },
    },
  },
};

/**
 * Small size variant
 */
export const SmallSize: Story = {
  args: {
    size: 'sm',
  },
  parameters: {
    docs: {
      description: {
        story: 'Smaller icon size for compact UIs.',
      },
    },
  },
};

/**
 * Medium size variant (default)
 */
export const MediumSize: Story = {
  args: {
    size: 'md',
  },
  parameters: {
    docs: {
      description: {
        story: 'Default size, optimized for most use cases.',
      },
    },
  },
};

/**
 * Large size variant
 */
export const LargeSize: Story = {
  args: {
    size: 'lg',
  },
  parameters: {
    docs: {
      description: {
        story: 'Larger icon size for increased visibility.',
      },
    },
  },
};

/**
 * Mobile size (responsive)
 */
export const MobileSize: Story = {
  args: {},
  parameters: {
    viewport: {
      defaultViewport: 'mobile1',
    },
    docs: {
      description: {
        story: 'On mobile devices (<768px), the icon automatically increases in size for better touch targets.',
      },
    },
  },
};

/**
 * Desktop size (responsive)
 */
export const DesktopSize: Story = {
  args: {},
  parameters: {
    viewport: {
      defaultViewport: 'desktop',
    },
    docs: {
      description: {
        story: 'On desktop (≥768px), the icon is more subtle and compact.',
      },
    },
  },
};

/**
 * Custom className for positioning
 */
export const CustomPositioning: Story = {
  args: {
    className: 'ml-4 border-2 border-primary',
  },
  parameters: {
    docs: {
      description: {
        story: 'Custom classes can be applied for positioning and styling.',
      },
    },
  },
};

/**
 * All features combined
 */
export const AllFeatures: Story = {
  args: {
    size: 'md',
    showTooltip: true,
    onThemeChange: (theme) => {
      console.log('Theme changed to:', theme);
    },
    className: 'ring-2 ring-primary ring-offset-2',
  },
  parameters: {
    docs: {
      description: {
        story: 'Demonstrates all props working together.',
      },
    },
  },
};
