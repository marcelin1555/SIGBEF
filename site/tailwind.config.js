/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Cores da marca (assets/marca). Use estes nomes em vez do código hex.
        primary: '#2E75B6',
        dark: '#1F4E79',
        fundo: '#F5F7FA',
        ambar: { DEFAULT: '#F2A900', claro: '#FFC233' },
      },
    },
  },
  plugins: [],
}
