/**
 * Talks to the FastAPI backend.
 *
 * vite.config.js proxies /api/* to http://localhost:8000 and strips the /api
 * prefix, so `/api/hotspots` here reaches `/hotspots` there. Nothing to
 * configure — just have the backend running.
 *
 * Swapping Map.jsx off its mock array is roughly six lines:
 *
 *   const [hotspots, setHotspots] = useState([]);
 *   useEffect(() => { fetchHotspots().then(d => setHotspots(d.hotspots)); }, []);
 *
 * then read h.latitude / h.longitude / h.classification / h.confidence instead
 * of the mock lat / lng / type / risk. Full schema: backend/ml/API_CONTRACT.md
 */

const CLASS_COLORS = {
  NEW_ABNORMAL_EVENT: "#ff4d4d",
  PERSISTENT_SOURCE: "#ffb84d",
  OTHER_ANOMALY: "#4cd7f6",
};

const CLASS_LABELS = {
  NEW_ABNORMAL_EVENT: "New abnormal event",
  PERSISTENT_SOURCE: "Persistent source",
  OTHER_ANOMALY: "Other anomaly",
};

export async function fetchHotspots(limit = 861) {
  const res = await fetch(`/api/hotspots?limit=${limit}`);
  if (!res.ok) throw new Error(`Backend returned ${res.status}`);
  return res.json();
}

export async function fetchModelInfo() {
  const res = await fetch("/api/model");
  if (!res.ok) throw new Error(`Backend returned ${res.status}`);
  return res.json();
}

export function classColor(classification) {
  return CLASS_COLORS[classification] || "#8899a6";
}

export function classLabel(classification) {
  return CLASS_LABELS[classification] || classification;
}

/**
 * True while the classifier is still the rule-based fallback rather than a
 * trained model. Show a "provisional" marker in the UI when this is true —
 * it is the honest thing to do in front of judges, and it disappears on its
 * own once the model is trained.
 */
export function isProvisional(modelInfo) {
  return !modelInfo?.trained;
}
