import { useEffect, useState } from "react";
import axios from "axios";

function CriticalEvent() {
  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios
      .get("/api/hotspots")
      .then((response) => {
        const hotspots = response.data.hotspots || [];

        // Pick the first classified hotspot as the priority event.
        // Later, this can be changed to select the highest-risk event.
        if (hotspots.length > 0) {
          setEvent(hotspots[0]);
        }
      })
      .catch((error) => {
        console.error("Failed to fetch critical event:", error);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <aside className="critical-panel">
        <div className="critical-header">
          <span className="critical-badge">LOADING</span>
          <span>THERMAL EVENT</span>
        </div>

        <h2>ANALYZING EVENT</h2>
      </aside>
    );
  }

  if (!event) {
    return (
      <aside className="critical-panel">
        <div className="critical-header">
          <span className="critical-badge">NO DATA</span>
          <span>THERMAL EVENT</span>
        </div>

        <h2>NO EVENT AVAILABLE</h2>
        <p>No classified hotspot data was returned.</p>
      </aside>
    );
  }

  const raw = event.raw || {};

  const confidence = Number(event.confidence ?? raw.confidence ?? 0);
  const frp = Number(raw.frp ?? 0);
  const brightTemp = Number(raw.bright_ti4 ?? 0);
  const persistenceDays = Number(raw.persistence_days ?? 0);
  const persistenceRatio = Number(raw.persistence_ratio ?? 0);
  const historicalCount = Number(raw.historical_count ?? 0);

  return (
    <aside className="critical-panel">

      <div className="critical-header">
        <span className="critical-badge">CRITICAL</span>
        <span>THERMAL EVENT</span>
      </div>

      <div className="priority">
        PRIORITY 01
      </div>

      <h2>EVENT TELEMETRY</h2>

      <div className="event-id">
        #{event.id ?? "THERMAL-EVENT"}
      </div>

      <div className="event-risk">
        {event.classification}
      </div>

      <div className="coordinates">
        {event.latitude !== undefined && event.longitude !== undefined
          ? `${Number(event.latitude).toFixed(4)}° N • ${Number(
              event.longitude
            ).toFixed(4)}° E`
          : "COORDINATES UNAVAILABLE"}
      </div>

      <div className="event-time">
        DATA SOURCE
        <strong>COLLECTED FIRMS DATA</strong>
      </div>

      <div className="event-source">
        CLASSIFICATION
        <strong>{event.classification}</strong>
        <span>ML classification result</span>
      </div>

      <div className="metrics">

        <div>
          <span>FIRE RADIATIVE POWER</span>
          <strong>{frp.toFixed(1)} MW</strong>
          <small>Observed FRP</small>
        </div>

        <div>
          <span>BRIGHTNESS TEMP</span>
          <strong>
            {brightTemp > 0 ? `${brightTemp.toFixed(1)} K` : "N/A"}
          </strong>
          <small>VIIRS thermal measurement</small>
        </div>

        <div>
          <span>HISTORICAL PERSISTENCE</span>
          <strong>{persistenceDays.toFixed(1)} days</strong>
          <small>{historicalCount} historical detections</small>
        </div>

        <div>
          <span>PERSISTENCE RATIO</span>
          <strong>{(persistenceRatio * 100).toFixed(1)}%</strong>
          <small>Historical baseline</small>
        </div>

      </div>

      <div className="confidence">

        <div className="confidence-header">
          <span>AI CONFIDENCE</span>
          <strong>{(confidence * 100).toFixed(1)}%</strong>
        </div>

        <div className="confidence-bar">
          <div
            style={{
              width: `${Math.min(100, confidence * 100)}%`,
            }}
          ></div>
        </div>

      </div>

      <div className="classification">

        <span>CLASSIFICATION</span>

        <strong>
          {event.classification}
        </strong>

        <p>
          Classified from thermal and historical features
        </p>

      </div>

      <div className="reasons">

        <div>
          <strong>⚡ FRP</strong>
          <span>{frp.toFixed(1)} MW</span>
        </div>

        <div>
          <strong>⌂ INDUSTRIAL PROXIMITY</strong>
          <span>
            {raw.industrial_distance !== undefined
              ? `${Number(raw.industrial_distance).toFixed(2)} km`
              : "N/A"}
          </span>
        </div>

        <div>
          <strong>↗ FRP Z-SCORE</strong>
          <span>
            {raw.frp_zscore !== undefined
              ? Number(raw.frp_zscore).toFixed(2)
              : "N/A"}
          </span>
        </div>

      </div>

      <div className="action-buttons">
        <button className="alert-button">
          NOTIFY NDRF
        </button>

        <button>
          EXPORT SITREP
        </button>
      </div>

    </aside>
  );
}

export default CriticalEvent;