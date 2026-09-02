"use strict";

const EDITOR_PROTOCOL_VERSION = 1;
const map = L.map("map", { preferCanvas: true }).setView([-20, 0], 2);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 18, attribution: "&copy; OpenStreetMap contributors"
}).addTo(map);

const voyageSelect = document.querySelector("#voyage-select");
const list = document.querySelector("#call-list");
const status = document.querySelector("#status");
const hint = document.querySelector("#hint");
const buttons = {
  port: document.querySelector("#add-port"), point: document.querySelector("#add-point"),
  hidden: document.querySelector("#add-hidden"), remove: document.querySelector("#remove"),
  up: document.querySelector("#move-up"), down: document.querySelector("#move-down"),
  save: document.querySelector("#save"), cancel: document.querySelector("#cancel")
};

let documentState = { revision: "", voyages: [], locations: [] };
let current = null;
let selected = -1;
let addType = null;
let dirty = false;
let layers = L.layerGroup().addTo(map);

function clone(value) { return JSON.parse(JSON.stringify(value)); }
function key(value) { return String(value || "").trim().toLocaleLowerCase("pl"); }
function setStatus(message, kind = "") { status.textContent = message; status.className = kind; }
function markDirty() { dirty = true; setStatus("Zmiany nie zostały jeszcze zapisane."); }
function selectedCall() { return current && selected >= 0 ? current.calls[selected] : null; }
function locationFor(name) { return documentState.locations.find(item => key(item.name) === key(name)); }
function typeClass(call) { return call.callType === "Punkt_trasy" ? "route" : call.callType === "Punkt_trasy_ukryty" ? "hidden" : "port"; }

function markerIcon(call, index) {
  const css = typeClass(call);
  return L.divIcon({
    className: `port-editor-marker ${css}${index === selected ? " selected" : ""}`,
    html: `<span><b>${index + 1}</b></span>`, iconSize: [28, 28], iconAnchor: [14, 27]
  });
}

function render(fit = false) {
  layers.clearLayers(); list.replaceChildren();
  if (!current) return;
  const coordinates = current.calls.map(call => [call.lat, call.lon]);
  if (coordinates.length > 1) L.polyline(coordinates, { color: "#91a7b4", weight: 2, dashArray: "5 7" }).addTo(layers);
  const active = selectedCall();
  if (active) {
    const neighbors = current.calls.slice(Math.max(0, selected - 1), selected + 2).map(call => [call.lat, call.lon]);
    if (neighbors.length > 1) L.polyline(neighbors, { color: "#e76f51", weight: 5 }).addTo(layers);
  }
  current.calls.forEach((call, index) => {
    const marker = L.marker([call.lat, call.lon], {
      draggable: true, icon: markerIcon(call, index), callIndex: index, title: call.name
    }).addTo(layers).bindPopup(`<strong>${call.name}</strong><br>Kolejność: ${index + 1}<br>Lat: ${call.lat.toFixed(6)}<br>Lon: ${call.lon.toFixed(6)}`);
    marker.on("click", () => selectCall(index, true));
    marker.on("dragend", event => {
      const position = event.target.getLatLng();
      const sameName = current.calls.filter(item => key(item.name) === key(call.name));
      sameName.forEach(item => { item.lat = position.lat; item.lon = position.lng; });
      markDirty(); selected = index; render(false);
      if (sameName.length > 1) setStatus(`Zmieniono wspólną lokalizację ${call.name} dla ${sameName.length} wizyt.`);
    });
    const item = document.createElement("li");
    item.className = `${typeClass(call)}${index === selected ? " selected" : ""}`;
    item.innerHTML = `<span class="number">${index + 1}</span><span><strong>${call.name}</strong><small>${call.when} · postój ${call.stayDays} · ${call.lat.toFixed(5)}, ${call.lon.toFixed(5)}</small></span>`;
    item.addEventListener("click", () => { selectCall(index); map.panTo([call.lat, call.lon], { animate: true, duration: .5 }); });
    list.append(item);
  });
  buttons.remove.disabled = selected < 0;
  buttons.up.disabled = selected <= 0;
  buttons.down.disabled = selected < 0 || selected >= current.calls.length - 1;
  if (fit && coordinates.length) map.fitBounds(L.latLngBounds(coordinates).pad(.2), { maxZoom: 8 });
  window.__portEditorState = clone({ voyageId: current.id, calls: current.calls, selected, dirty });
}

function selectCall(index, popup = false) {
  selected = index; render(false);
  if (popup) {
    const marker = layers.getLayers().find(layer => layer.options && layer.options.callIndex === index);
    if (marker) marker.openPopup();
  }
}

function setAddType(callType) {
  addType = addType === callType ? null : callType;
  buttons.port.classList.toggle("active", addType === "");
  buttons.point.classList.toggle("active", addType === "Punkt_trasy");
  buttons.hidden.classList.toggle("active", addType === "Punkt_trasy_ukryty");
  hint.textContent = addType === null ? "Wybierz pozycję z listy. Znaczniki można przeciągać."
    : "Kliknij mapę. Nowa pozycja zostanie wstawiona po zaznaczonej (albo na końcu).";
}

function promptRequired(label, initial = "") {
  const value = prompt(label, initial);
  return value === null ? null : value.trim();
}

function createCallAt(position) {
  const name = promptRequired("Nazwa portu lub punktu:");
  if (!name) return null;
  const routePoint = addType !== "";
  const country = promptRequired("Kraj (może być pusty dla punktu trasy):", "");
  if (country === null) return null;
  const when = promptRequired("Kiedy: RRRR-MM-DD, N albo +N:", "+0");
  if (!when) return null;
  let stayDays = 0;
  if (!routePoint) {
    const entered = promptRequired("Postoj_dni:", "1");
    if (entered === null) return null;
    stayDays = Number(entered);
    if (!Number.isInteger(stayDays) || stayDays < 0) { setStatus("Postoj_dni musi być liczbą całkowitą >= 0.", "error"); return null; }
  }
  const notes = promptRequired("Uwagi (opcjonalnie):", "");
  if (notes === null) return null;
  const existing = locationFor(name);
  let lat = position.lat, lon = position.lng;
  if (existing) {
    const useExisting = confirm(`Lokalizacje zawiera już ${existing.name} (${existing.lat.toFixed(6)}, ${existing.lon.toFixed(6)}).\nOK — użyj istniejącej pozycji.\nAnuluj — świadomie zastąp ją klikniętą pozycją.`);
    if (useExisting) { lat = existing.lat; lon = existing.lon; }
  }
  return {
    sourceVisitId: "", order: 0, name, country, when, stayDays,
    lat, lon, notes, callType: addType
  };
}

map.on("click", event => {
  if (!current || addType === null) return;
  const call = createCallAt(event.latlng);
  if (!call) return;
  const index = selected >= 0 ? selected + 1 : current.calls.length;
  current.calls.splice(index, 0, call); selected = index;
  const sameName = current.calls.filter(item => key(item.name) === key(call.name));
  sameName.forEach(item => { item.lat = call.lat; item.lon = call.lon; });
  markDirty(); setAddType(null); render(false);
});

function loadVoyage(id, fit = true) {
  const found = documentState.voyages.find(item => item.id === id);
  if (!found) return;
  current = clone(found); selected = -1; dirty = false; setAddType(null); setStatus(""); render(fit);
}

function rebuildVoyages(preferred) {
  voyageSelect.replaceChildren();
  documentState.voyages.forEach(voyage => {
    const option = document.createElement("option");
    option.value = voyage.id; option.textContent = `${voyage.name} (${voyage.id})`; voyageSelect.append(option);
  });
  if (preferred) voyageSelect.value = preferred;
  if (voyageSelect.value) loadVoyage(voyageSelect.value);
}

async function refresh(preferred) {
  const response = await fetch("/api/ports", { cache: "no-store" });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "Nie udało się odczytać danych");
  if (payload.editorProtocol !== EDITOR_PROTOCOL_VERSION) throw new Error("Uruchomiony backend edytora jest nieaktualny. Zamknij go i ponownie uruchom Edytuj-Porty.cmd.");
  documentState = payload; rebuildVoyages(preferred || (current && current.id));
}

voyageSelect.addEventListener("change", () => {
  if (dirty && !confirm("Porzucić niezapisane zmiany?")) { voyageSelect.value = current.id; return; }
  loadVoyage(voyageSelect.value);
});
buttons.port.addEventListener("click", () => setAddType(""));
buttons.point.addEventListener("click", () => setAddType("Punkt_trasy"));
buttons.hidden.addEventListener("click", () => setAddType("Punkt_trasy_ukryty"));
buttons.remove.addEventListener("click", () => {
  const call = selectedCall();
  if (!call || !confirm(`Usunąć z Porty pozycję ${call.name}?\nLokalizacje nie zostanie usunięte.`)) return;
  current.calls.splice(selected, 1); selected = Math.min(selected, current.calls.length - 1); markDirty(); render(false);
});
buttons.up.addEventListener("click", () => {
  if (selected <= 0) return;
  [current.calls[selected - 1], current.calls[selected]] = [current.calls[selected], current.calls[selected - 1]];
  selected--; markDirty(); render(false);
});
buttons.down.addEventListener("click", () => {
  if (selected < 0 || selected >= current.calls.length - 1) return;
  [current.calls[selected + 1], current.calls[selected]] = [current.calls[selected], current.calls[selected + 1]];
  selected++; markDirty(); render(false);
});
buttons.cancel.addEventListener("click", async () => {
  try { await refresh(current && current.id); setStatus("Wczytano ponownie dane z Excela.", "ok"); }
  catch (error) { setStatus(error.message, "error"); }
});
buttons.save.addEventListener("click", async () => {
  if (!current) return;
  buttons.save.disabled = true;
  try {
    const request = { voyageId: current.id, calls: current.calls, revision: documentState.revision };
    window.__lastPortSavePayload = clone(request);
    const response = await fetch("/api/ports", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(request) });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Zapis nie powiódł się");
    documentState = payload; dirty = false; rebuildVoyages(current.id); setStatus(payload.message, "ok");
  } catch (error) { setStatus(error.message, "error"); }
  finally { buttons.save.disabled = false; }
});
window.addEventListener("beforeunload", event => { if (dirty) { event.preventDefault(); event.returnValue = ""; } });
refresh().catch(error => setStatus(error.message, "error"));
