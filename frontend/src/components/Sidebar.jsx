import { useEffect, useState } from "react";
import axios from "axios";


function Sidebar({ filters, setFilters }) {
  const [counts, setCounts] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios
      .get("/api/hotspots")
      .then((response) => {
  const hotspots = response.data.hotspots || [];

  const filteredHotspots = hotspots.filter((hotspot) => {
    const frp = Number(hotspot.raw?.frp ?? hotspot.frp ?? 0);
    return frp >= filters.minFrp;
  });

  const filteredCounts = {
    PERSISTENT_SOURCE: 0,
    NEW_ABNORMAL_EVENT: 0,
    OTHER_ANOMALY: 0,
  };

  filteredHotspots.forEach((hotspot) => {
    if (filteredCounts[hotspot.classification] !== undefined) {
      filteredCounts[hotspot.classification]++;
    }
  });

  setCounts(filteredCounts);
})
      .catch((error) => {
        console.error("Failed to fetch hotspot counts:", error);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [filters.minFrp]);

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
          <input
  type="checkbox"
  checked={filters.categories.PERSISTENT_SOURCE}
  onChange={(e) =>
    setFilters((prev) => ({
      ...prev,
      categories: {
        ...prev.categories,
        PERSISTENT_SOURCE: e.target.checked,
      },
    }))
  }
/>
          Persistent Source
          <span>
            {loading ? "—" : counts["PERSISTENT_SOURCE"] ?? 0}
          </span>
        </label>

        <label className="filter">
          <input
  type="checkbox"
  checked={filters.categories.NEW_ABNORMAL_EVENT}
  onChange={(e) =>
    setFilters((prev) => ({
      ...prev,
      categories: {
        ...prev.categories,
        NEW_ABNORMAL_EVENT: e.target.checked,
      },
    }))
  }
/>
          New Abnormal Event
          <span>
            {loading ? "—" : counts["NEW_ABNORMAL_EVENT"] ?? 0}
          </span>
        </label>

        <label className="filter">
          <input
  type="checkbox"
  checked={filters.categories.OTHER_ANOMALY}
  onChange={(e) =>
    setFilters((prev) => ({
      ...prev,
      categories: {
        ...prev.categories,
        OTHER_ANOMALY: e.target.checked,
      },
    }))
  }
/>
          Other Anomaly
          <span>
            {loading ? "—" : counts["OTHER_ANOMALY"] ?? 0}
          </span>
        </label>

      </div>

      <div className="sidebar-section">

        <div className="section-title">TEMPORAL PASS SCOPE</div>

        <div className="time-buttons">
          <button
  className={filters.timeRange === "1H" ? "selected" : ""}
  onClick={() =>
    setFilters((prev) => ({
      ...prev,
      timeRange: "1H",
    }))
  }
>
  1H
</button>

<button
  className={filters.timeRange === "24H" ? "selected" : ""}
  onClick={() =>
    setFilters((prev) => ({
      ...prev,
      timeRange: "24H",
    }))
  }
>
  24H
</button>

<button
  className={filters.timeRange === "72H" ? "selected" : ""}
  onClick={() =>
    setFilters((prev) => ({
      ...prev,
      timeRange: "72H",
    }))
  }
>
  72H
</button>
        </div>

      </div>

      <div className="sidebar-section">

        <div className="section-title">
          MIN FIRE RADIATIVE POWER
        </div>

        <div className="slider-value">{filters.minFrp} MW</div>

        <input
  className="range"
  type="range"
  min="0"
  max="20"
  step="0.5"
  value={filters.minFrp}
  onChange={(e) =>
    setFilters((prev) => ({
      ...prev,
      minFrp: Number(e.target.value),
    }))
  }
/>

      </div>

    </aside>
  );
}

export default Sidebar;