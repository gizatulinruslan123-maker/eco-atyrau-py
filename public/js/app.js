// Координаты центра города Атырау
const ATYRAU_CENTER = [47.1167, 51.9167];

const TYPE_META = {
  dump: { emoji: '🗑️', color: '#B3452F', label: 'Несанкционированная свалка' },
  cleaned: { emoji: '✅', color: '#2F6F62', label: 'Место убрано' },
  recycling: { emoji: '♻️', color: '#2F6F62', label: 'Пункт переработки' },
  tree: { emoji: '🌳', color: '#3E7D3A', label: 'Место для посадки дерева' },
  shop: { emoji: '🛍', color: '#C97B3D', label: 'Эко-магазин' },
};

const map = L.map('map').setView(ATYRAU_CENTER, 13);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; OpenStreetMap contributors',
}).addTo(map);

let markersLayer = L.layerGroup().addTo(map);
let currentFilter = '';

function makeIcon(type) {
  const meta = TYPE_META[type] || { emoji: '📍', color: '#2F6F62' };
  return L.divIcon({
    className: '',
    html: `<div class="marker-badge" style="background:${meta.color}"><span>${meta.emoji}</span></div>`,
    iconSize: [34, 34],
    iconAnchor: [17, 30],
    popupAnchor: [0, -30],
  });
}

async function loadReports(type = '') {
  const url = type ? `/api/reports?type=${encodeURIComponent(type)}` : '/api/reports';
  const res = await fetch(url);
  const reports = await res.json();

  markersLayer.clearLayers();

  reports.forEach((r) => {
    const meta = TYPE_META[r.type] || {};
    const marker = L.marker([r.lat, r.lon], { icon: makeIcon(r.type) });

    const authorLine =
      r.type === 'cleaned' && r.author_name
        ? `<div class="popup__author">🙌 Убрал(а): ${escapeHtml(r.author_name)}</div>`
        : '';

    marker.bindPopup(`
      <div class="popup">
        ${r.photo_path ? `<img src="${r.photo_path}" alt="Фото" />` : ''}
        <div class="popup__type">${meta.label || r.type}</div>
        ${r.description ? `<div class="popup__desc">${escapeHtml(r.description)}</div>` : ''}
        ${authorLine}
      </div>
    `);

    markersLayer.addLayer(marker);
  });
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

async function loadLeaderboard() {
  const res = await fetch('/api/leaderboard');
  const rows = await res.json();
  const list = document.getElementById('leaderboard');

  if (!rows.length) {
    list.innerHTML = '<li class="leaderboard__empty">Пока никто не убирал мусор. Будьте первым! 🌱</li>';
    return;
  }

  list.innerHTML = rows
    .map((u, i) => {
      const name = u.first_name || u.username || 'Волонтёр';
      return `
        <li class="leaderboard__item">
          <span class="leaderboard__rank">${i + 1}</span>
          <span class="leaderboard__name">${escapeHtml(name)}</span>
          <span class="leaderboard__score">${u.rating}</span>
        </li>`;
    })
    .join('');
}

document.querySelectorAll('.filter-chip').forEach((btn) => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-chip').forEach((b) => b.classList.remove('is-active'));
    btn.classList.add('is-active');
    currentFilter = btn.dataset.type || '';
    loadReports(currentFilter);
  });
});

loadReports();
loadLeaderboard();
setInterval(loadLeaderboard, 30000);
setInterval(() => loadReports(currentFilter), 30000);
