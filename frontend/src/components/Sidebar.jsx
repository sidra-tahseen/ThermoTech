function Sidebar() {
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
          Wildfire / Crown Flare
          <span>38</span>
        </label>

        <label className="filter">
          <input type="checkbox" defaultChecked />
          Industrial Flaring
          <span>312</span>
        </label>

        <label className="filter">
          <input type="checkbox" defaultChecked />
          Agricultural
          <span>1,012</span>
        </label>

        <label className="filter">
          <input type="checkbox" defaultChecked />
          Rapid Surge
          <span>66</span>
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