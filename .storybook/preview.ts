import type { Preview } from '@storybook/react';
import '../app/globals.css';

const preview: Preview = {
  parameters: {
    actions: { argTypesRegex: '^on[A-Z].*' },

    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/,
      },
    },

    docs: {
      toc: true,
    },

    viewport: {
      viewports: {
        mobile: {
          name: 'Mobile',
          styles: {
            width: '375px',
            height: '667px',
          },
        },
        tablet: {
          name: 'Tablet',
          styles: {
            width: '768px',
            height: '1024px',
          },
        },
        desktop: {
          name: 'Desktop',
          styles: {
            width: '1024px',
            height: '768px',
          },
        },
        large: {
          name: 'Large Desktop',
          styles: {
            width: '1440px',
            height: '900px',
          },
        },
      },
    },

    backgrounds: {
      default: 'light',
      values: [
        {
          name: 'light',
          value: 'oklch(1 0 0)',
        },
        {
          name: 'dark',
          value: 'oklch(0.145 0 0)',
        },
      ],
    },

    a11y: {
      // 'todo' - show a11y violations in the test UI only
      // 'error' - fail CI on a11y violations
      // 'off' - skip a11y checks entirely
      test: 'todo'
    }
  },
  globalTypes: {
    theme: {
      description: 'Global theme for components',
      defaultValue: 'light',
      toolbar: {
        title: 'Theme',
        icon: 'circlehollow',
        items: [
          { value: 'light', title: 'Light Mode', icon: 'sun' },
          { value: 'dark', title: 'Dark Mode', icon: 'moon' },
        ],
        dynamicTitle: true,
      },
    },
  },
  decorators: [
    (Story, context) => {
      const theme = context.globals.theme || 'light';

      // Apply theme class to the story container
      const themeClass = theme === 'dark' ? 'dark' : '';

      return (
        <div
          className={`${themeClass} min-h-screen bg-background text-foreground p-4`}
          style={{
            // Ensure OKLCH colors are applied correctly
            background: theme === 'dark' ? 'oklch(0.145 0 0)' : 'oklch(1 0 0)',
            color: theme === 'dark' ? 'oklch(0.985 0 0)' : 'oklch(0.145 0 0)',
          }}
        >
          <Story />
        </div>
      );
    },
  ],
  tags: ['autodocs'],
};

export default preview;