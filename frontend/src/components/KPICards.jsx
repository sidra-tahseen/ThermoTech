import { useEffect, useState } from "react";
import axios from "axios";

function KPICards() {
  const [data, setData] = useState(null);

  useEffect(() => {
    axios
      .get("/api/hotspots")
      .then((response) => {
        setData(response.data);
      })
      .catch((error) => {
        console.error("Failed to fetch hotspot data:", error);
      });
  }, []);

  const counts = data?.counts || {};

  const cards = [
    {
      label: "TRACKED HOTSPOTS",
      value: data?.total ?? "—",
      change: "COLLECTED DATA",
      icon: "◉",
      type: "normal",
    },
    {
      label: "HIGH-RISK ANOMALIES",
      value: counts["NEW_ABNORMAL_EVENT"] ?? "—",
      change: "NEW ABNORMAL EVENTS",
      icon: "⚠",
      type: "danger",
    },
    {
      label: "PERSISTENT THERMAL SOURCES",
      value: counts["PERSISTENT_SOURCE"] ?? "—",
      change: "BASELINE MATCHED",
      icon: "▣",
      type: "warning",
    },
    {
      label: "OTHER ANOMALIES",
      value: counts["OTHER_ANOMALY"] ?? "—",
      change: "OTHER CLASSIFIED EVENTS",
      icon: "↗",
      type: "danger",
    },
  ];

  return (
    <section className="kpi-grid">
      {cards.map((card) => (
        <div className={`kpi-card ${card.type}`} key={card.label}>
          <div className="kpi-top">
            <span>{card.icon}</span>
            <span>{card.label}</span>
          </div>

          <div className="kpi-value">{card.value}</div>

          <div className="kpi-change">{card.change}</div>
        </div>
      ))}
    </section>
  );
}

export default KPICards;