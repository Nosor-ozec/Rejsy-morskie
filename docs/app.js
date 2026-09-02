'use strict';

const map = L.map('map', { zoomControl: true });
const mapElement = document.getElementById('map');

const routePane = map.createPane('route-lines');
routePane.style.zIndex = '410';
routePane.style.pointerEvents = 'none';
const technicalPane = map.createPane('technical-markers');
technicalPane.style.zIndex = '620';
const mediaPane = map.createPane('media-markers');
mediaPane.style.zIndex = '640';
const portPane = map.createPane('port-markers');
portPane.style.zIndex = '660';

const LONG_STAY_PIN_SVG = [
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 25 41">',
  '<path d="M12.5 0C5.6 0 0 5.6 0 12.5C0 21.9 12.5 41 12.5 41S25 21.9 25 12.5C25 5.6 19.4 0 12.5 0Z" fill="#D9480F" stroke="#8F2600" stroke-width="1"/>',
  '<circle cx="12.5" cy="12.5" r="5.5" fill="#FFF4E6"/>',
  '</svg>'
].join('');
const LONG_STAY_PIN_URL = `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(LONG_STAY_PIN_SVG)}`;

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
  const mediaByVisit = new Map();
  for (const item of mediaData.media.filter(item => !item.atSea)) {
    const visitKey = item.baseVisitId || item.base;
    if (!mediaByVisit.has(visitKey)) mediaByVisit.set(visitKey, []);
    mediaByVisit.get(visitKey).push(item);
  }

  const routeGroup = L.featureGroup().addTo(map);
  for (const leg of routeData.legs) {
    L.polyline(leg.coordinates, {
      pane: 'route-lines', color: voyage?.color || '#0057B8', weight: 4, opacity: 0.86
    }).addTo(routeGroup);
  }

  const markers = [];
  const list = document.getElementById('ports');
  routeData.ports.forEach((port, index) => {
    const markerOptions = {
      title: port.name,
      pane: 'port-markers',
      zIndexOffset: 1000,
      riseOnHover: true,
      riseOffset: 2000
    };
    if (port.stayDays > 1) markerOptions.icon = longStayIcon();
    const marker = L.marker(port.position, markerOptions).addTo(routeGroup);
    marker.bindPopup(popup(port.name, mediaByVisit.get(port.visitId) || mediaByVisit.get(port.name) || [], port.stayDays));
    markers.push(marker);
    const item = document.createElement('li');
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = `${port.order}. ${port.name}`;
    button.addEventListener('click', () => focus(index));
    item.appendChild(button);
    list.appendChild(item);
  });

  for (const point of routeData.routePoints || []) {
    const marker = L.circleMarker(point.position, {
      pane: 'technical-markers',
      radius: 6,
      color: '#4c1d95',
      weight: 2,
      fillColor: '#c4b5fd',
      fillOpacity: 1
    }).addTo(routeGroup);
    marker.bindPopup(popup(point.name, mediaByVisit.get(point.visitId) || mediaByVisit.get(point.name) || []));
  }

  for (const item of mediaData.media.filter(item => item.atSea)) {
    const marker = L.circleMarker(item.position, {
      pane: 'media-markers', radius: 7, color: '#fff', weight: 2,
      fillColor: '#e76f51', fillOpacity: 1
    }).addTo(routeGroup);
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

function longStayIcon() {
  return L.icon({
    iconUrl: LONG_STAY_PIN_URL,
    shadowUrl: 'vendor/leaflet/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
  });
}

function popup(portName, items, stayDays = 0) {
  const links = items.map(item => `<li><a href="${escapeAttribute(item.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.description)}</a></li>`).join('');
  const stay = stayDays > 1 ? `<p class="stay-info">Postój: ${stayDays} dni</p>` : '';
  return `<div class="popup"><strong>${escapeHtml(portName)}</strong>${stay}${links ? `<ul>${links}</ul>` : ''}</div>`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
}
function escapeAttribute(value) { return escapeHtml(value); }
