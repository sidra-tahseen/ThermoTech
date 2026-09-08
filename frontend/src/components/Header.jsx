function Header() {
  return (
    <header className="header">
      <div className="brand">
        <div className="brand-icon">◉</div>

        <div>
          <div className="brand-name">THERMOTECH</div>
          <div className="brand-subtitle">
            SATELLITE THERMAL INTELLIGENCE COMMAND
          </div>
        </div>
      </div>

      <div className="header-status">
        <span className="live-dot"></span>
        LIVE MONITORING
      </div>

      <div className="sync">
        <span>NASA FIRMS</span>
        <strong>VIIRS / MODIS</strong>
        <span className="separator">|</span>
        LAST SYNC
        <strong>09:42:18 UTC</strong>
      </div>
    </header>
  );
}

export default Header;