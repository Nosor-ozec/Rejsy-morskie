'use strict';

const map = L.map('map', { zoomControl: true });
const mapElement = document.getElementById('map');

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

function invalidateMapSize() {
  window.requestAnimationFrame(() => map.invalidateSize({ animate: false, pan: false }));
}

if ('ResizeObserver' in window) {
  const mapResizeObserver = new ResizeObserver(invalidateMapSize);
  mapResizeObserver.observe(mapElement);
} else {
  window.addEventListener('resize', invalidateMapSize, { passive: true });
}

Promise.all([
  fetch('data/route.json').then(response => response.ok ? response.json() : Promise.reject(new Error('Brak danych trasy'))),
  fetch('data/media.json').then(response => response.ok ? response.json() : Promise.reject(new Error('Brak danych mediów')))
]).then(([routeData, mediaData]) => render(routeData, mediaData)).catch(error => {
  document.getElementById('map').innerHTML = `<p class="error">${escapeHtml(error.message)}</p>`;
});

function render(routeData, mediaData) {
  const voyage = routeData.voyages[0];
  if (voyage) document.getElementById('voyage-title').textContent = voyage.name;
  const mediaByPort = new Map();
  for (const item of mediaData.media.filter(item => !item.atSea)) {
    if (!mediaByPort.has(item.port)) mediaByPort.set(item.port, []);
    mediaByPort.get(item.port).push(item);
  }

  const routeGroup = L.featureGroup().addTo(map);
  for (const leg of routeData.legs) {
    L.polyline(leg.coordinates, { color: voyage?.color || '#0057B8', weight: 4, opacity: 0.86 }).addTo(routeGroup);
  }

  const markers = [];
  const list = document.getElementById('ports');
  routeData.ports.forEach((port, index) => {
    const marker = L.marker(port.position, { title: port.name }).addTo(routeGroup);
    marker.bindPopup(popup(port.name, mediaByPort.get(port.name) || []));
    markers.push(marker);
    const item = document.createElement('li');
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = `${port.order}. ${port.name}`;
    button.addEventListener('click', () => focus(index));
    item.appendChild(button);
    list.appendChild(item);
  });

  for (const item of mediaData.media.filter(item => item.atSea)) {
    const marker = L.circleMarker(item.position, { radius: 7, color: '#fff', weight: 2, fillColor: '#e76f51', fillOpacity: 1 }).addTo(routeGroup);
    marker.bindPopup(popup('Na morzu', [item]));
  }

  let current = 0;
  function focus(index) {
    current = Math.max(0, Math.min(markers.length - 1, index));
    map.panTo(markers[current].getLatLng(), { animate: true, duration: 0.7 });
  }
  document.getElementById('previous').addEventListener('click', () => focus(current - 1));
  document.getElementById('next').addEventListener('click', () => focus(current + 1));
  function showWholeRoute() {
    map.invalidateSize({ animate: false, pan: false });
    map.fitBounds(routeGroup.getBounds(), { padding: [30, 30] });
  }

  document.getElementById('whole-route').addEventListener('click', showWholeRoute);
  window.requestAnimationFrame(() => window.requestAnimationFrame(showWholeRoute));
}

function popup(portName, items) {
  const links = items.map(item => `<li><a href="${escapeAttribute(item.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.description)}</a></li>`).join('');
  return `<div class="popup"><strong>${escapeHtml(portName)}</strong>${links ? `<ul>${links}</ul>` : ''}</div>`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
}
function escapeAttribute(value) { return escapeHtml(value); }
