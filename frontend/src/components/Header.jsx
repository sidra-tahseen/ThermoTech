import { useEffect, useState } from "react";
import axios from "axios";

function Header() {
  const [model, setModel] = useState(null);

  useEffect(() => {
    axios
      .get("/api/model")
      .then((response) => {
        setModel(response.data);
      })
      .catch((error) => {
        console.error("Failed to fetch model status:", error);
      });
  }, []);

  const modelStatus = model?.trained
    ? "MODEL READY"
    : "PROVISIONAL MODEL";

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
        COLLECTED DATA ANALYSIS
      </div>

      <div className="sync">
        <span>NASA FIRMS</span>
        <strong>VIIRS / MODIS</strong>

        <span className="separator">|</span>

        <span>AI STATUS</span>
        <strong>{modelStatus}</strong>
      </div>
    </header>
  );
}

export default Header;