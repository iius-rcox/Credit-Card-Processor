import type { StorybookConfig } from '@storybook/nextjs';

const config: StorybookConfig = {
  stories: [
    '../stories/**/*.stories.@(js|jsx|ts|tsx|mdx)',
    '../components/**/*.stories.@(js|jsx|ts|tsx|mdx)',
  ],
  addons: [
    '@storybook/addon-essentials',
    '@storybook/addon-themes',
    '@storybook/addon-docs',
    '@storybook/addon-controls',
    '@storybook/addon-viewport',
  ],
  framework: {
    name: '@storybook/nextjs',
    options: {
      builder: {
        useSWC: true,
      },
    },
  },
  core: {
    disableTelemetry: true,
  },
  typescript: {
    check: false,
    reactDocgen: 'react-docgen-typescript',
    reactDocgenTypescriptOptions: {
      shouldExtractLiteralValuesFromEnum: true,
      propFilter: (prop) => (prop.parent ? !/node_modules/.test(prop.parent.fileName) : true),
    },
  },
  nextConfigPath: '../next.config.js',
  features: {
    experimentalRSC: false, // Disable RSC for Storybook compatibility
  },
  staticDirs: ['../public'],
  webpackFinal: async (config) => {
    // Ensure proper handling of CSS imports
    const fileLoaderRule = config.module?.rules?.find((rule) => {
      if (typeof rule !== 'object' || !rule) return false;
      if ('test' in rule && rule.test instanceof RegExp) {
        return rule.test.test('.svg');
      }
      return false;
    });

    if (fileLoaderRule && typeof fileLoaderRule === 'object' && 'exclude' in fileLoaderRule) {
      if (Array.isArray(fileLoaderRule.exclude)) {
        fileLoaderRule.exclude.push(/\.svg$/);
      } else {
        fileLoaderRule.exclude = [fileLoaderRule.exclude, /\.svg$/];
      }
    }

    // Add SVG support
    config.module?.rules?.push({
      test: /\.svg$/,
      use: ['@svgr/webpack'],
    });

    return config;
  },
};

export default config;