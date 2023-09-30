/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './{core}/templates/**/*.html',
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ]
}

