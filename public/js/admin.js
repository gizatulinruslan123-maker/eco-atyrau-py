const TYPE_LABELS = {
  dump: '🗑️ Несанкционированная свалка',
  cleaned: '✅ Место убрано волонтёром',
  recycling: '♻️ Пункт переработки',
  tree: '🌳 Место для посадки дерева',
  shop: '🛍 Эко-магазин',
};

let password = sessionStorage.getItem('eco_admin_password') || '';

const loginCard = document.getElementById('login-card');
const pendingSection = document.getElementById('pending-section');
const passwordInput = document.getElementById('password-input');
const loginBtn = document.getElementById('login-btn');
const loginError = document.getElementById('login-error');
const pendingList = document.getElementById('pending-list');
const refreshBtn = document.getElementById('refresh-btn');

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

async function tryLogin(pw) {
  const res = await fetch(`/api/admin/pending?password=${encodeURIComponent(pw)}`);
  if (res.status === 401) return false;
  password = pw;
  sessionStorage.setItem('eco_admin_password', pw);
  loginCard.hidden = true;
  pendingSection.hidden = false;
  const rows = await res.json();
  renderPending(rows);
  return true;
}

function renderPending(rows) {
  if (!rows.length) {
    pendingList.innerHTML = '<div class="pending-empty">Новых заявок нет 🎉</div>';
    return;
  }
  pendingList.innerHTML = rows
    .map((r) => {
      const author = r.author_name ? `Отправил: ${escapeHtml(r.author_name)}` : 'Автор неизвестен';
      const date = new Date(r.created_at).toLocaleString('ru-RU');
      return `
        <div class="pending-card" data-id="${r.id}">
          ${r.photo_path ? `<img src="${r.photo_path}" alt="Фото" />` : '<div></div>'}
          <div>
            <span class="pending-card__type">${TYPE_LABELS[r.type] || r.type}</span>
            <div class="pending-card__desc">${r.description ? escapeHtml(r.description) : '<em>без описания</em>'}</div>
            <div class="pending-card__meta">${author} · ${date}</div>
          </div>
          <div class="pending-card__actions">
            <button class="btn btn--approve" data-action="approve" data-id="${r.id}">Одобрить</button>
            <button class="btn btn--reject" data-action="reject" data-id="${r.id}">Отклонить</button>
          </div>
        </div>`;
    })
    .join('');
}

async function loadPending() {
  const res = await fetch(`/api/admin/pending?password=${encodeURIComponent(password)}`);
  if (res.status === 401) {
    sessionStorage.removeItem('eco_admin_password');
    location.reload();
    return;
  }
  renderPending(await res.json());
}

pendingList.addEventListener('click', async (e) => {
  const btn = e.target.closest('button[data-action]');
  if (!btn) return;
  const { action, id } = btn.dataset;
  btn.disabled = true;
  await fetch(`/api/admin/reports/${id}/${action}?password=${encodeURIComponent(password)}`, {
    method: 'POST',
  });
  loadPending();
});

loginBtn.addEventListener('click', async () => {
  const ok = await tryLogin(passwordInput.value);
  if (!ok) loginError.textContent = 'Неверный пароль';
});

passwordInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') loginBtn.click();
});

refreshBtn.addEventListener('click', loadPending);

// автоматический вход, если пароль сохранён в этой сессии браузера
if (password) tryLogin(password);
