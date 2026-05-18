const DATASET_URL = "/data/generated/paris_segments.geojson";
const VALIDATION_STORAGE_KEY = "mappingParis.segmentValidation.v1";
const PARIS_BOUNDS = L.latLngBounds([48.815, 2.224], [48.906, 2.47]);

const elements = {
  totalSegments: document.querySelector("#totalSegments"),
  validatedSegments: document.querySelector("#validatedSegments"),
  selectedSegments: document.querySelector("#selectedSegments"),
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
  maxBounds: PARIS_BOUNDS.pad(0.15),
  maxBoundsViscosity: 0.85,
  minZoom: 11,
}).setView([48.8566, 2.3522], 12);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  bounds: PARIS_BOUNDS.pad(0.35),
  minZoom: 11,
  maxZoom: 20,
  keepBuffer: 1,
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

const validationState = loadValidationState();
const layerById = new Map();
const featureById = new Map();
const selectedIds = new Set();
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
  renderSelectionDetails();
}

function renderMesh(geojson) {
  meshLayer = L.geoJSON(geojson, {
    renderer: L.canvas({ padding: 0.35 }),
    style: (feature) => styleFor(feature.properties.id),
    onEachFeature: (feature, layer) => {
      const id = feature.properties.id;
      layerById.set(id, layer);
      featureById.set(id, feature);
      layer.on("click", () => toggleSegmentSelection(id));
    },
  }).addTo(map);

  const bounds = meshLayer.getBounds();
  if (bounds.isValid()) {
    map.fitBounds(bounds, { padding: [18, 18] });
    window.requestAnimationFrame(() => map.invalidateSize());
  }
}

function styleFor(id) {
  if (selectedIds.has(id)) {
    return { color: "#1f5fa8", weight: 6, opacity: 0.95 };
  }
  if (validationState[id]) {
    return { color: "#2f8f5b", weight: 3, opacity: 0.82 };
  }
  return { color: "#b9624b", weight: 2, opacity: 0.58 };
}

function toggleSegmentSelection(id) {
  if (selectedIds.has(id)) {
    selectedIds.delete(id);
  } else {
    selectedIds.add(id);
  }
  refreshLayer(id);
  renderSelectionDetails();
}

function renderSelectionDetails() {
  const selectedProperties = [...selectedIds]
    .map((id) => featureById.get(id)?.properties)
    .filter(Boolean);

  elements.selectedSegments.textContent = selectedProperties.length.toLocaleString("fr-FR");
  elements.toggleValidation.disabled = selectedProperties.length === 0;
  elements.clearSelection.disabled = selectedProperties.length === 0;

  if (selectedProperties.length === 0) {
    elements.arrondissementValue.textContent = "-";
    elements.toggleValidation.textContent = "Valider";
    setDetailsEmpty("Clique un segment sur la carte.");
    return;
  }

  const allSelectedValidated = selectedProperties.every((properties) => validationState[properties.id]);
  elements.toggleValidation.textContent = allSelectedValidated ? "Dévalider" : "Valider";

  if (selectedProperties.length === 1) {
    renderSingleSegmentDetails(selectedProperties[0]);
    return;
  }

  const totalLength = selectedProperties.reduce(
    (total, properties) => total + Number(properties.length_meters || 0),
    0,
  );
  const streetNames = uniqueValues(selectedProperties.map((properties) => properties.street_name));
  const arrondissements = uniqueValues(selectedProperties.map((properties) => properties.arrondissement));

  elements.arrondissementValue.textContent = arrondissements.length === 1 ? arrondissements[0] : "Mixte";
  elements.segmentDetails.classList.remove("empty");
  elements.segmentDetails.innerHTML = `
    <strong>${selectedProperties.length.toLocaleString("fr-FR")} segments sélectionnés</strong>
    <span>Longueur totale: ${totalLength.toLocaleString("fr-FR", { maximumFractionDigits: 0 })} m</span>
    <span>Rues: ${escapeHtml(formatPreview(streetNames))}</span>
    <span>Arrondissements: ${escapeHtml(formatPreview(arrondissements))}</span>
  `;
}

function renderSingleSegmentDetails(properties) {
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
  if (selectedIds.size === 0) return;
  const allSelectedValidated = [...selectedIds].every((id) => validationState[id]);
  for (const id of selectedIds) {
    if (allSelectedValidated) {
      delete validationState[id];
    } else {
      validationState[id] = true;
    }
    refreshLayer(id);
  }
  saveValidationState();
  updateValidatedCount();
  renderSelectionDetails();
});

elements.clearSelection.addEventListener("click", () => {
  const previousIds = [...selectedIds];
  selectedIds.clear();
  previousIds.forEach(refreshLayer);
  renderSelectionDetails();
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
  renderSelectionDetails();
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

function uniqueValues(values) {
  return [...new Set(values.filter(Boolean))].sort((a, b) => String(a).localeCompare(String(b), "fr"));
}

function formatPreview(values) {
  if (values.length <= 4) {
    return values.join(", ");
  }
  return `${values.slice(0, 4).join(", ")} +${values.length - 4}`;
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
