function CriticalEvent() {
  return (
    <aside className="critical-panel">

      <div className="critical-header">
        <span className="critical-badge">CRITICAL</span>
        <span>FLAME EVENT</span>
      </div>

      <div className="priority">
        PRIORITY 01
      </div>

      <h2>LIVE TELEMETRY</h2>

      <div className="event-id">
        #EVT-2026-9402
      </div>

      <div className="event-risk">
        HIGH RISK ANOMALY
      </div>

      <div className="coordinates">
        21.8472° N • 86.3219° E
      </div>

      <div className="event-time">
        PASS TIMESTAMP
        <strong>09:28:44 UTC</strong>
      </div>

      <div className="event-source">
        INGEST SOURCE
        <strong>NOAA-20 VIIRS</strong>
        <span>Band M13 / I4 • 375m</span>
      </div>

      <div className="metrics">

        <div>
          <span>FIRE RADIATIVE POWER</span>
          <strong>268.4 MW</strong>
          <small>99th Percentile</small>
        </div>

        <div>
          <span>BRIGHTNESS TEMP</span>
          <strong>374.2 K</strong>
          <small>+101°C Equivalent</small>
        </div>

        <div>
          <span>DIURNAL Δ BASELINE</span>
          <strong>+86.5 K</strong>
          <small>Above 5-Year Norm</small>
        </div>

        <div>
          <span>HISTORICAL PERSISTENCE</span>
          <strong>0.0%</strong>
          <small>Zero Prior 730d</small>
        </div>

      </div>

      <div className="confidence">

        <div className="confidence-header">
          <span>AI CONFIDENCE</span>
          <strong>98.4%</strong>
        </div>

        <div className="confidence-bar">
          <div></div>
        </div>

      </div>

      <div className="classification">

        <span>CLASSIFICATION</span>

        <strong>
          Uncontrolled Crown Wildfire
        </strong>

        <p>
          Protected deciduous forest
        </p>

      </div>

      <div className="reasons">

        <div>
          <strong>⚡ FRP Surge</strong>
          <span>+184 MW/hr</span>
        </div>

        <div>
          <strong>⌂ OSM Land Use</strong>
          <span>Dense Sal canopy</span>
        </div>

        <div>
          <strong>↗ Vector Spread</strong>
          <span>18 km/h NW</span>
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