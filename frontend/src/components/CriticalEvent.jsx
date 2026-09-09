import { useEffect, useState } from "react";
import axios from "axios";

function CriticalEvent() {
  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios
      .get("/api/critical-event")
      .then((response) => {
        setEvent(response.data);
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
        <p>No critical event data was returned.</p>
      </aside>
    );
  }

  const confidence = Number(event.ai_confidence ?? 0);
  const frp = Number(event.frp ?? 0);
  const brightTemp = Number(event.brightness_temp ?? 0);
  const persistenceDays = Number(
    event.historical_persistence_days ?? 0
  );
  const persistenceRatio = Number(event.persistence_ratio ?? 0);
  const baseline = Number(event.historical_baseline ?? 0);

  return (
    <aside className="critical-panel">

      <div className="critical-header">
        <span className="critical-badge">
          {event.risk_level === "HIGH" ? "CRITICAL" : "PRIORITY"}
        </span>

        <span>THERMAL EVENT</span>
      </div>

      <div className="priority">
        {event.priority}
      </div>

      <h2>EVENT TELEMETRY</h2>

      <div className="event-id">
        #{event.event_id}
      </div>

      <div className="event-risk">
        {event.risk_level} RISK
      </div>

      <div className="event-source">
        CLASSIFICATION
        <strong>{event.classification}</strong>
        <span>ML classification result</span>
      </div>

      <div className="event-time">
        DATA SOURCE
        <strong>COLLECTED FIRMS DATA</strong>
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
            {brightTemp > 0
              ? `${brightTemp.toFixed(1)} K`
              : "N/A"}
          </strong>
          <small>VIIRS thermal measurement</small>
        </div>

        <div>
          <span>HISTORICAL PERSISTENCE</span>
          <strong>{persistenceDays.toFixed(1)} days</strong>
          <small>Historical persistence</small>
        </div>

        <div>
          <span>PERSISTENCE RATIO</span>
          <strong>{persistenceRatio.toFixed(1)}%</strong>
          <small>Historical baseline</small>
        </div>

      </div>

      <div className="confidence">

        <div className="confidence-header">
          <span>AI CONFIDENCE</span>

          <strong>
            {(confidence * 100).toFixed(1)}%
          </strong>
        </div>

        <div className="confidence-bar">
          <div
            style={{
              width: `${Math.min(
                100,
                Math.max(0, confidence * 100)
              )}%`,
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
            {event.industrial_distance !== null &&
            event.industrial_distance !== undefined
              ? `${Number(event.industrial_distance).toFixed(2)} km`
              : "N/A"}
          </span>
        </div>

        <div>
          <strong>↗ HISTORICAL BASELINE</strong>

          <span>
            {baseline > 0
              ? `${baseline.toFixed(2)} MW`
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