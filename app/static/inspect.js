const command = document.querySelector('.command');
if (command) {
  const selector = command.querySelector('select');
  const details = command.querySelector('details');
  selector.addEventListener('change', () => {
    if (selector.value === 'custom') {
      details.open = true;
      details.querySelector('input').focus();
    }
  });
  command.addEventListener('submit', () => {
    command.querySelector('output').textContent = '正在核验…';
  });
}
const grid = document.querySelector('#evidence-grid');
if (grid) {
  const rows = Array.from(grid.querySelectorAll('[data-event]'));
  const output = grid.querySelector('output');
  let active = -1;
  function move(step) {
    if (!rows.length) return;
    active = active === -1 ? (step > 0 ? 0 : rows.length - 1) : (active + step + rows.length) % rows.length;
    rows[active].focus();
  }
  grid.querySelector('#event-prev').addEventListener('click', () => move(-1));
  grid.querySelector('#event-next').addEventListener('click', () => move(1));
  grid.addEventListener('focusin', ({target}) => {
    if (target.matches('[data-event]')) {
      active = rows.indexOf(target);
      output.textContent = `当前证据 ${target.dataset.event}`;
    }
  });
  document.addEventListener('keydown', (event) => {
    if (event.ctrlKey || event.altKey || event.metaKey || event.target.matches('input,textarea,select,[contenteditable]')) return;
    if (event.key === 'j' || event.key === 'k') {
      event.preventDefault();
      move(event.key === 'j' ? 1 : -1);
    }
  });
}
