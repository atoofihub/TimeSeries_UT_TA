/* Offline navigation, lesson search and code copying. */
(() => {
  'use strict';
  const fa = number => number.toLocaleString('fa-IR');
  const normalize = text => text.toLowerCase().replace(/[أإآ]/g, 'ا').replace(/ي/g, 'ی').replace(/ك/g, 'ک').replace(/[\u200c\u200e\u200f]/g, '').replace(/\s+/g, ' ').trim();

  document.getElementById('lesson-search')?.addEventListener('input', event => {
    const words = normalize(event.target.value).split(' ').filter(Boolean);
    let count = 0;
    document.querySelectorAll('.lesson-row').forEach(row => {
      const text = normalize(row.querySelector('.lesson-summary').textContent);
      row.hidden = !words.every(word => text.includes(word));
      if (!row.hidden) count++;
    });
    document.querySelectorAll('.learning-phase').forEach(phase => {
      phase.hidden = ![...phase.querySelectorAll('.lesson-row')].some(row => !row.hidden);
    });
    const status = document.getElementById('search-status');
    status.hidden = !words.length;
    status.textContent = count ? `${fa(count)} بخش پیدا شد.` : 'درسی با این عبارت پیدا نشد. عبارت دیگری را امتحان کنید.';
  });

  document.querySelectorAll('.copy').forEach(button => button.addEventListener('click', async () => {
    const code = button.parentElement.querySelector('pre');
    if (!code) return;
    try {
      await navigator.clipboard.writeText(code.textContent);
      button.textContent = 'کپی شد';
    } catch (_) {
      const selection = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(code);
      selection.removeAllRanges(); selection.addRange(range);
      button.textContent = 'کد انتخاب شد؛ کپی کنید';
    }
    setTimeout(() => { button.textContent = 'کپی کد'; }, 2000);
  }));

  const headings = document.querySelectorAll('article h3[id]');
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        document.querySelectorAll('.section-menu a').forEach(link => {
          if (link.hash === '#' + entry.target.id) link.setAttribute('aria-current', 'location');
          else link.removeAttribute('aria-current');
        });
      }
    }, { rootMargin: '-5% 0px -70% 0px' });
    headings.forEach(heading => observer.observe(heading));
  }
})();
