
// Use bundled TeX/SVG components only; optional extensions must never fetch a CDN.
window.MathJax = {
  tex: {
    inlineMath: [['\\(', '\\)']],
    displayMath: [['\\[', '\\]']],
    packages: { '[+]': ['ams', 'noerrors', 'noundefined'], '[-]': ['autoload', 'require'] }
  },
  svg: { fontCache: 'global' },
  options: {
    enableMenu: false,
    skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
  },
  startup: { typeset: true }
};
