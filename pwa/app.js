const DATASET_URL = "/data/generated/paris_segments.geojson";
const VALIDATION_STORAGE_KEY = "mappingParis.segmentValidation.v1";

const elements = {
  totalSegments: document.querySelector("#totalSegments"),
  validatedSegments: document.querySelector("#validatedSegments"),
  arrondissementValue: document.querySelector("#arrondissementValue"),
  segmentDetails: document.querySelector("#segmentDetails"),
  toggleValidation: document.querySelector("#toggleValidation"),
  clearSelection: document.querySelector("#clearSelection"),
  exportValidation: document.querySelector("#exportValidation"),
  resetValidation: document.querySelector("#resetValidation"),
};

const map = L.map("map", {
  preferCanvas: true,
  zoomControl: true,
}).setView([48.8566, 2.3522], 13);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 20,
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

const validationState = loadValidationState();
const layerById = new Map();
let selectedId = null;
let dataset = null;
let meshLayer = null;

bootstrap();

async function bootstrap() {
  registerServiceWorker();
  setDetailsEmpty("Chargement du dataset...");
  const response = await fetch(DATASET_URL);
  dataset = await response.json();
  elements.totalSegments.textContent = dataset.features.length.toLocaleString("fr-FR");
  renderMesh(dataset);
  updateValidatedCount();
  setDetailsEmpty("Clique un segment sur la carte.");
}

function renderMesh(geojson) {
  meshLayer = L.geoJSON(geojson, {
    renderer: L.canvas({ padding: 0.35 }),
    style: (feature) => styleFor(feature.properties.id),
    onEachFeature: (feature, layer) => {
      const id = feature.properties.id;
      layerById.set(id, layer);
      layer.on("click", () => selectSegment(id));
    },
  }).addTo(map);

  const bounds = meshLayer.getBounds();
  if (bounds.isValid()) {
    map.fitBounds(bounds, { padding: [18, 18] });
    window.requestAnimationFrame(() => map.invalidateSize());
  }
}

function styleFor(id) {
  if (id === selectedId) {
    return { color: "#1f5fa8", weight: 6, opacity: 0.95 };
  }
  if (validationState[id]) {
    return { color: "#2f8f5b", weight: 3, opacity: 0.82 };
  }
  return { color: "#b9624b", weight: 2, opacity: 0.58 };
}

function selectSegment(id) {
  const previousId = selectedId;
  selectedId = id;
  refreshLayer(previousId);
  refreshLayer(selectedId);

  const feature = dataset.features.find((item) => item.properties.id === id);
  renderSegmentDetails(feature.properties);
  elements.toggleValidation.disabled = false;
  elements.clearSelection.disabled = false;
  elements.toggleValidation.textContent = validationState[id] ? "Dévalider" : "Valider";
}

function renderSegmentDetails(properties) {
  elements.segmentDetails.classList.remove("empty");
  elements.segmentDetails.innerHTML = `
    <strong>${escapeHtml(properties.street_name)}</strong>
    <span>ID: ${escapeHtml(properties.id)}</span>
    <span>Arrondissement: ${escapeHtml(properties.arrondissement)}</span>
    <span>Longueur: ${Number(properties.length_meters).toLocaleString("fr-FR")} m</span>
    <span>Type OSM: ${escapeHtml(properties.highway)}</span>
    <span>Way OSM: ${escapeHtml(String(properties.source_way_id))}</span>
  `;
  elements.arrondissementValue.textContent = properties.arrondissement;
}

function setDetailsEmpty(message) {
  elements.segmentDetails.classList.add("empty");
  elements.segmentDetails.textContent = message;
}

function refreshLayer(id) {
  if (!id) return;
  const layer = layerById.get(id);
  if (layer) {
    layer.setStyle(styleFor(id));
  }
}

elements.toggleValidation.addEventListener("click", () => {
  if (!selectedId) return;
  validationState[selectedId] = !validationState[selectedId];
  if (!validationState[selectedId]) {
    delete validationState[selectedId];
  }
  saveValidationState();
  refreshLayer(selectedId);
  updateValidatedCount();
  elements.toggleValidation.textContent = validationState[selectedId] ? "Dévalider" : "Valider";
});

elements.clearSelection.addEventListener("click", () => {
  const previousId = selectedId;
  selectedId = null;
  refreshLayer(previousId);
  elements.toggleValidation.disabled = true;
  elements.clearSelection.disabled = true;
  elements.arrondissementValue.textContent = "-";
  setDetailsEmpty("Clique un segment sur la carte.");
});

elements.exportValidation.addEventListener("click", () => {
  const payload = {
    exportedAt: new Date().toISOString(),
    validatedSegmentIds: Object.keys(validationState).sort(),
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "mapping-paris-segment-validation.json";
  link.click();
  URL.revokeObjectURL(url);
});

elements.resetValidation.addEventListener("click", () => {
  if (!window.confirm("Réinitialiser toutes les validations locales ?")) {
    return;
  }
  const previousIds = Object.keys(validationState);
  previousIds.forEach((id) => delete validationState[id]);
  saveValidationState();
  previousIds.forEach(refreshLayer);
  updateValidatedCount();
  if (selectedId) {
    elements.toggleValidation.textContent = "Valider";
  }
});

function updateValidatedCount() {
  elements.validatedSegments.textContent = Object.keys(validationState).length.toLocaleString("fr-FR");
}

function loadValidationState() {
  try {
    return JSON.parse(localStorage.getItem(VALIDATION_STORAGE_KEY) || "{}");
  } catch {
    return {};
  }
}

function saveValidationState() {
  localStorage.setItem(VALIDATION_STORAGE_KEY, JSON.stringify(validationState));
}

function registerServiceWorker() {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker
      .register("./service-worker.js", { updateViaCache: "none" })
      .then((registration) => registration.update())
      .catch(() => undefined);
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
