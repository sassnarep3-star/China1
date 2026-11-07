(function () {
  'use strict';

  /* Client-side filter for any table inside a [data-filterable] block.
     Purely additive: with scripting disabled every table is fully readable. */
  document.querySelectorAll('.tablewrap').forEach(function (wrap) {
    var table = wrap.querySelector('table');
    if (!table || table.querySelectorAll('tbody tr').length < 8) { return; }

    var bar = document.createElement('div');
    bar.className = 'toolbar';
    var input = document.createElement('input');
    input.type = 'search';
    input.placeholder = 'Filter this table\u2026';
    input.setAttribute('aria-label', 'Filter table rows');
    var count = document.createElement('span');
    count.className = 'count';
    bar.appendChild(input);
    bar.appendChild(count);
    wrap.parentNode.insertBefore(bar, wrap);

    var rows = Array.prototype.slice.call(table.querySelectorAll('tbody tr'));
    function apply() {
      var q = input.value.trim().toLowerCase();
      var shown = 0;
      rows.forEach(function (tr) {
        var hit = !q || tr.textContent.toLowerCase().indexOf(q) !== -1;
        tr.style.display = hit ? '' : 'none';
        if (hit) { shown++; }
      });
      count.textContent = shown + ' of ' + rows.length + ' rows';
    }
    input.addEventListener('input', apply);
    apply();
  });

  /* Reveal the row a fragment identifier points at on long pages. */
  function focusTarget() {
    if (!location.hash) { return; }
    var el = document.getElementById(location.hash.slice(1));
    if (el && el.scrollIntoView) {
      el.scrollIntoView({ block: 'start' });
    }
  }
  window.addEventListener('hashchange', focusTarget);
  focusTarget();
}());
