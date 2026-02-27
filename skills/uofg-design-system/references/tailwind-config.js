/**
 * University of Glasgow Design System — Tailwind CSS Configuration
 * Source: https://design.gla.ac.uk
 *
 * Usage:
 *   1. Copy this into your tailwind.config.js (or import/spread it)
 *   2. Add the Google Fonts link for Noto Sans to your HTML <head>
 *   3. Use classes like: bg-uofg-blue, text-uofg-white, p-uofg-6, etc.
 *
 * The 'uofg' prefix keeps the design system tokens separate from
 * Tailwind defaults, so you can use both without conflicts.
 */

/** @type {import('tailwindcss').Config} */
module.exports = {
  theme: {
    extend: {

      /* ---- COLOURS ---- */
      colors: {
        uofg: {
          // Primary
          'university-blue': '#011451',  // Deep navy — footers, dark headers
          blue: {
            DEFAULT: '#005398',          // Practical blue — buttons, links, accents
            80: '#344374',
            60: '#677297',
            40: '#99A1B9',
            20: '#CCD0DC',
            10: '#E6E7EE',
          },
          // Vanilla (greys)
          'dark-grey': {
            1: '#666666',
            2: '#4D4D4D',
            3: '#323232',
          },
          'light-grey': {
            1: '#F5F5F5',
            2: '#E6E6E6',
            3: '#CCCCCC',
          },
          'mid-grey': {
            1: '#B3B3B3',
            2: '#999999',
            3: '#757575',
          },
          // UI / status
          error: '#D4351C',
          success: '#8BC34A',
          highlight: '#FFDD00',
          // Common
          white: '#FFFFFF',
          black: '#000000',
        },
      },

      /* ---- TYPOGRAPHY ---- */
      fontFamily: {
        uofg: ['"Noto Sans"', 'system-ui', '-apple-system', 'sans-serif'],
      },

      fontSize: {
        'uofg-xs':   ['0.75rem',  { lineHeight: '1rem' }],     // 12px
        'uofg-sm':   ['0.875rem', { lineHeight: '1.25rem' }],  // 14px
        'uofg-base': ['1rem',     { lineHeight: '1.5rem' }],   // 16px
        'uofg-lg':   ['1.125rem', { lineHeight: '1.75rem' }],  // 18px
        'uofg-xl':   ['1.25rem',  { lineHeight: '1.75rem' }],  // 20px
        'uofg-2xl':  ['1.5rem',   { lineHeight: '2rem' }],     // 24px
        'uofg-3xl':  ['1.875rem', { lineHeight: '2.25rem' }],  // 30px
        'uofg-4xl':  ['2.25rem',  { lineHeight: '2.5rem' }],   // 36px
        'uofg-5xl':  ['3rem',     { lineHeight: '1.15' }],     // 48px
      },

      /* ---- SPACING (extends Tailwind's default scale) ---- */
      spacing: {
        'uofg-1':  '0.25rem',   // 4px
        'uofg-2':  '0.5rem',    // 8px
        'uofg-3':  '0.75rem',   // 12px
        'uofg-4':  '1rem',      // 16px
        'uofg-5':  '1.25rem',   // 20px
        'uofg-6':  '1.5rem',    // 24px
        'uofg-7':  '2rem',      // 32px
        'uofg-8':  '2.5rem',    // 40px
        'uofg-9':  '3rem',      // 48px
        'uofg-10': '3.5rem',    // 56px
        'uofg-11': '4rem',      // 64px
        'uofg-12': '6rem',      // 96px
      },

      /* ---- GRID / BREAKPOINTS ---- */
      screens: {
        'uofg-xs': '0px',
        'uofg-sm': '768px',
        'uofg-md': '1024px',
        'uofg-lg': '1400px',
        'uofg-xl': '1900px',
      },

      /* ---- GRID TEMPLATE ---- */
      gridTemplateColumns: {
        'uofg': 'repeat(12, minmax(0, 1fr))',
      },

      gap: {
        'uofg': '24px',
      },

      /* ---- MISC ---- */
      borderRadius: {
        'uofg-sm': '4px',
        'uofg-md': '8px',
        'uofg-lg': '12px',
      },

      ringColor: {
        'uofg-focus': '#FFDD00',
      },

      ringOffsetWidth: {
        'uofg': '2px',
      },

      outlineColor: {
        'uofg-focus': '#FFDD00',
      },

      maxWidth: {
        'uofg-container': '1200px',
      },
    },
  },

  plugins: [],
};

/*
 * USAGE EXAMPLES:
 *
 * Primary button:
 *   <button class="bg-uofg-blue text-uofg-white font-semibold
 *                  px-uofg-6 py-uofg-3 rounded-uofg-sm
 *                  hover:bg-uofg-blue-80
 *                  focus-visible:outline focus-visible:outline-3
 *                  focus-visible:outline-uofg-focus focus-visible:outline-offset-2">
 *     Submit
 *   </button>
 *
 * Secondary button:
 *   <button class="bg-uofg-light-grey-2 text-uofg-dark-grey-3 font-semibold
 *                  px-uofg-6 py-uofg-3 rounded-uofg-sm
 *                  hover:bg-uofg-light-grey-3">
 *     Edit
 *   </button>
 *
 * Outline button:
 *   <button class="bg-transparent text-uofg-blue border-2 border-uofg-blue
 *                  font-semibold px-uofg-6 py-uofg-3 rounded-uofg-sm
 *                  hover:bg-uofg-blue-10">
 *     Cancel
 *   </button>
 *
 * 12-column grid:
 *   <div class="grid grid-cols-uofg gap-uofg max-w-uofg-container mx-auto px-uofg-6">
 *     <div class="col-span-8">Main content</div>
 *     <div class="col-span-4">Sidebar</div>
 *   </div>
 *
 * Footer:
 *   <footer class="bg-uofg-blue text-uofg-white py-uofg-9 px-uofg-6">
 *     ...
 *   </footer>
 *
 * Tile card:
 *   <a href="#" class="block border border-uofg-light-grey-3 rounded-uofg-md
 *                      overflow-hidden hover:shadow-lg
 *                      focus-visible:outline focus-visible:outline-3
 *                      focus-visible:outline-uofg-focus">
 *     <img class="w-full aspect-video object-cover" src="..." alt="..." />
 *     <div class="p-uofg-6">
 *       <h3 class="text-uofg-lg font-bold text-uofg-blue">Title</h3>
 *       <p class="text-uofg-sm text-uofg-dark-grey-1 mt-uofg-2">Description</p>
 *     </div>
 *   </a>
 */
