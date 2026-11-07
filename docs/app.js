'use strict';
const filter = document.querySelector('#filter');
if (filter) {
  const rows = [...document.querySelectorAll('tbody tr')];
  const status = document.createElement('p');
  status.setAttribute('role', 'status');
  filter.parentElement.after(status);
  const update = () => {
    const query = filter.value.trim().toLowerCase();
    let count = 0;
    rows.forEach(row => { row.hidden = !row.textContent.toLowerCase().includes(query); if (!row.hidden) count++; });
    status.textContent = `${count} of ${rows.length} options shown`;
  };
  filter.addEventListener('input', update);
  update();
}
