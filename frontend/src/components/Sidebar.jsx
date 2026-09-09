import { useEffect, useState } from "react";
import axios from "axios";

function Sidebar() {
  const [counts, setCounts] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios
      .get("/api/hotspots")
      .then((response) => {
        setCounts(response.data.counts || {});
      })
      .catch((error) => {
        console.error("Failed to fetch hotspot counts:", error);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  return (
    <aside className="sidebar">

      <div className="sidebar-section">
        <div className="section-title">OPERATIONAL MODULES</div>

        <div className="nav-item active">
          <span>◉</span>
          Tactical Ops Console
        </div>

        <div className="nav-item">
          <span>▣</span>
          Hotspot Matrix
        </div>

        <div className="nav-item">
          <span>◇</span>
          Spectral FRP Analysis
        </div>

        <div className="nav-item">
          <span>⚠</span>
          Escalation Queue
        </div>

        <div className="nav-item">
          <span>↗</span>
          EOC Dispatch
        </div>
      </div>

      <div className="sidebar-section">

        <div className="section-title">AREA OF INTEREST</div>

        <select className="select-box">
          <option>Similipal Biosphere, Odisha</option>
          <option>Bandipur</option>
          <option>Singrauli Belt</option>
          <option>Vidarbha</option>
        </select>

      </div>

      <div className="sidebar-section">

        <div className="section-title">
          EVENT CATEGORY
        </div>

        <label className="filter">
          <input type="checkbox" defaultChecked />
          Persistent Source
          <span>
            {loading ? "—" : counts["PERSISTENT_SOURCE"] ?? 0}
          </span>
        </label>

        <label className="filter">
          <input type="checkbox" defaultChecked />
          New Abnormal Event
          <span>
            {loading ? "—" : counts["NEW_ABNORMAL_EVENT"] ?? 0}
          </span>
        </label>

        <label className="filter">
          <input type="checkbox" defaultChecked />
          Other Anomaly
          <span>
            {loading ? "—" : counts["OTHER_ANOMALY"] ?? 0}
          </span>
        </label>

      </div>

      <div className="sidebar-section">

        <div className="section-title">TEMPORAL PASS SCOPE</div>

        <div className="time-buttons">
          <button>1H</button>
          <button className="selected">24H</button>
          <button>72H</button>
        </div>

      </div>

      <div className="sidebar-section">

        <div className="section-title">
          MIN FIRE RADIATIVE POWER
        </div>

        <div className="slider-value">40 MW</div>

        <input
          className="range"
          type="range"
          min="0"
          max="300"
          defaultValue="40"
        />

      </div>

    </aside>
  );
}

export default Sidebar;