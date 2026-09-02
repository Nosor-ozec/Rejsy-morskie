"use strict";

const EDITOR_PROTOCOL_VERSION = 3;

const map = L.map("map", { preferCanvas: true }).setView([-20, 0], 2);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 18,
  attribution: "&copy; OpenStreetMap contributors"
}).addTo(map);

const select = document.querySelector("#passage-select");
const list = document.querySelector("#point-list");
const status = document.querySelector("#status");
const count = document.querySelector("#point-count");
const passageStatus = document.querySelector("#passage-status");
const hint = document.querySelector("#mode-hint");
const buttons = {
  add: document.querySelector("#add-point"),
  insert: document.querySelector("#insert-point"),
  remove: document.querySelector("#delete-point"),
  up: document.querySelector("#move-up"),
  down: document.querySelector("#move-down"),
  save: document.querySelector("#save"),
  cancel: document.querySelector("#cancel"),
  create: document.querySelector("#new-passage")
};

let documentState = { revision: "", passages: [] };
let current = null;
let originalName = null;
let selected = -1;
let mode = null;
let dirty = false;
let layers = L.layerGroup().addTo(map);

function clone(value) { return JSON.parse(JSON.stringify(value)); }
function normalized(value) { return value.trim().toLocaleLowerCase("pl"); }
function pointName(index) { return `${current.name} ${String(index + 1).padStart(2, "0")}`; }

function setStatus(message, kind = "") {
  status.textContent = message;
  status.className = kind;
}

function icon(index, isSelected) {
  return L.divIcon({
    className: `passage-marker${isSelected ? " selected" : ""}`,
    html: `<span><b>${index + 1}</b></span>`,
    iconSize: [28, 28], iconAnchor: [14, 28], popupAnchor: [0, -30]
  });
}

function popupHtml(point, index) {
  return `<strong>${pointName(index)}</strong><br>Numer: ${index + 1}<br>` +
    `Lat: ${point.lat.toFixed(6)}<br>Lon: ${point.lon.toFixed(6)}`;
}

function markDirty() { dirty = true; setStatus("Zmiany nie zostały jeszcze zapisane."); }

function savePayload() {
  return {
    name: current.name,
    status: current.status,
    originalName,
    revision: documentState.revision,
    points: current.points
  };
}

function selectPoint(index, openPopup = false) {
  selected = index;
  render(false);
  if (openPopup) {
    const marker = layers.getLayers().find(layer => layer.options && layer.options.pointIndex === index);
    if (marker) marker.openPopup();
  }
}

function render(fit = false) {
  layers.clearLayers();
  list.replaceChildren();
  if (!current) {
    count.textContent = "0";
    window.__passageEditorState = null;
    document.body.dataset.editorState = "null";
    return;
  }
  window.__passageEditorState = clone(savePayload());
  document.body.dataset.editorState = JSON.stringify(window.__passageEditorState);
  count.textContent = String(current.points.length);
  passageStatus.value = current.status;
  const coordinates = current.points.map(point => [point.lat, point.lon]);
  if (coordinates.length > 1) L.polyline(coordinates, { color: "#0b6380", weight: 4 }).addTo(layers);
  current.points.forEach((point, index) => {
    const marker = L.marker([point.lat, point.lon], {
      draggable: true, icon: icon(index, index === selected), pointIndex: index
    }).addTo(layers).bindPopup(popupHtml(point, index));
    marker.on("click", () => selectPoint(index, true));
    marker.on("dragend", event => {
      const position = event.target.getLatLng();
      point.lat = position.lat;
      point.lon = position.lng;
      selected = index;
      markDirty();
      render(false);
    });
    const item = document.createElement("li");
    if (index === selected) item.classList.add("selected");
    item.innerHTML = `<span class="number">${index + 1}</span><span><strong>${pointName(index)}</strong>` +
      `<small>${point.lat.toFixed(6)}, ${point.lon.toFixed(6)}</small></span>`;
    item.addEventListener("click", () => { selected = index; render(false); map.panTo([point.lat, point.lon]); });
    list.append(item);
  });
  buttons.remove.disabled = selected < 0;
  buttons.insert.disabled = selected < 0;
  buttons.up.disabled = selected <= 0;
  buttons.down.disabled = selected < 0 || selected >= current.points.length - 1;
  if (fit && coordinates.length) map.fitBounds(L.latLngBounds(coordinates).pad(0.35), { maxZoom: 12 });
}

function setMode(next) {
  mode = mode === next ? null : next;
  buttons.add.classList.toggle("active", mode === "add");
  buttons.insert.classList.toggle("active", mode === "insert");
  hint.textContent = mode === "add" ? "Kliknij mapę, aby dodać punkt na końcu."
    : mode === "insert" ? "Kliknij mapę, aby wstawić punkt po zaznaczonym."
    : "Wybierz narzędzie, a potem kliknij mapę. Punkty można przeciągać.";
}

function loadPassage(name, fit = true) {
  const found = documentState.passages.find(item => normalized(item.name) === normalized(name));
  if (!found) return;
  current = clone(found);
  originalName = found.name;
  selected = -1;
  dirty = false;
  setMode(null);
  setStatus("");
  render(fit);
}

function rebuildSelect(preferredName) {
  select.replaceChildren();
  documentState.passages.forEach(passage => {
    const option = document.createElement("option");
    option.value = passage.name;
    option.textContent = passage.name;
    select.append(option);
  });
  if (preferredName) select.value = preferredName;
  if (select.value) {
    loadPassage(select.value);
  } else {
    current = null;
    originalName = null;
    selected = -1;
    render(false);
  }
}

function showDraftInSelect(name) {
  const option = document.createElement("option");
  option.value = name;
  option.textContent = `${name} (nowe)`;
  option.dataset.draft = "true";
  select.append(option);
  select.value = name;
}

async function refresh(preferredName) {
  const response = await fetch("/api/passages", { cache: "no-store" });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "Nie udało się odczytać danych");
  if (payload.editorProtocol !== EDITOR_PROTOCOL_VERSION) {
    throw new Error(
      "Uruchomiony proces edytora jest nieaktualny. Zamknij jego okno i ponownie uruchom Edytuj-Przejscia.cmd."
    );
  }
  documentState = payload;
  rebuildSelect(preferredName || (current && current.name));
}

map.on("click", event => {
  if (!current || !mode) return;
  const point = {
    lat: event.latlng.lat, lon: event.latlng.lng,
    country: current.points[0]?.country || "",
    locationType: current.points[0]?.locationType || "Przejscie",
    notes: ""
  };
  if (mode === "insert" && selected >= 0) {
    current.points.splice(selected + 1, 0, point);
    selected += 1;
  } else {
    current.points.push(point);
    selected = current.points.length - 1;
  }
  markDirty();
  setMode(null);
  render(false);
});

select.addEventListener("change", () => {
  if (dirty && !confirm("Porzucić niezapisane zmiany?")) { select.value = current.name; return; }
  const draft = select.querySelector("option[data-draft='true']");
  if (draft && select.value !== draft.value) draft.remove();
  loadPassage(select.value);
});
buttons.add.addEventListener("click", () => setMode("add"));
buttons.insert.addEventListener("click", () => selected >= 0 && setMode("insert"));
buttons.remove.addEventListener("click", () => {
  if (selected < 0) return;
  current.points.splice(selected, 1);
  selected = Math.min(selected, current.points.length - 1);
  markDirty(); render(false);
});
buttons.up.addEventListener("click", () => {
  if (selected <= 0) return;
  [current.points[selected - 1], current.points[selected]] = [current.points[selected], current.points[selected - 1]];
  selected -= 1; markDirty(); render(false);
});
buttons.down.addEventListener("click", () => {
  if (selected < 0 || selected >= current.points.length - 1) return;
  [current.points[selected + 1], current.points[selected]] = [current.points[selected], current.points[selected + 1]];
  selected += 1; markDirty(); render(false);
});
buttons.create.addEventListener("click", () => {
  if (dirty && !confirm("Porzucić niezapisane zmiany?")) return;
  const name = prompt("Nazwa nowego przejścia:");
  if (!name || !name.trim()) return;
  if (documentState.passages.some(item => normalized(item.name) === normalized(name))) {
    setStatus("Przejście o tej nazwie już istnieje.", "error"); return;
  }
  current = { name: name.trim(), status: "development", points: [] };
  originalName = null; selected = -1; dirty = true;
  showDraftInSelect(current.name);
  setStatus("Kliknij „Dodaj punkt”, a następnie mapę. Potrzebne są co najmniej 2 punkty.");
  setMode("add"); render(false);
});
passageStatus.addEventListener("change", () => {
  if (!current) return;
  current.status = passageStatus.value;
  markDirty();
  render(false);
});
buttons.cancel.addEventListener("click", async () => {
  try { await refresh(originalName || undefined); setStatus("Wczytano ponownie dane z Excela.", "ok"); }
  catch (error) { setStatus(error.message, "error"); }
});
buttons.save.addEventListener("click", async () => {
  if (!current) return;
  buttons.save.disabled = true;
  try {
    const requestPayload = savePayload();
    window.__lastPassageSavePayload = clone(requestPayload);
    document.body.dataset.lastSavePayload = JSON.stringify(requestPayload);
    const response = await fetch("/api/passages", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestPayload)
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Zapis nie powiódł się");
    documentState = { revision: payload.revision, passages: payload.passages };
    dirty = false; originalName = current.name;
    rebuildSelect(current.name);
    setStatus(payload.message, "ok");
  } catch (error) { setStatus(error.message, "error"); }
  finally { buttons.save.disabled = false; }
});

window.addEventListener("beforeunload", event => {
  if (!dirty) return;
  event.preventDefault(); event.returnValue = "";
});

refresh().catch(error => setStatus(error.message, "error"));
