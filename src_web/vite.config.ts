import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Plugin to inject CSS link in dev mode for Chromium compatibility
function injectCssLinkInDev({linkHref}: {linkHref: string }): Plugin {
  return {
    name: 'inject-css-link-dev',
    transformIndexHtml: {
      order: 'pre',
      handler(html, ctx) {
        const isLocalDevelopment = !!ctx.server;
        // Check if the link is already present to avoid duplicates
        if (isLocalDevelopment && !html.includes(`<link rel="stylesheet" href="${linkHref}"`)) {
          return html.replace(
            '</head>',
            `<link rel="stylesheet" href="${linkHref}">\n</head>`
          );
        }

        return html;
      },
    },
  };
}
export default defineConfig({
  base: './',
  plugins: [
    react({
      babel: {
        plugins: [['babel-plugin-react-compiler']],
      },
    }),
    tailwindcss(),
    injectCssLinkInDev({ linkHref: '/src/index.css' })
  ],
})
