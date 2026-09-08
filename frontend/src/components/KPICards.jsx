const cards = [
  {
    label: "TRACKED HOTSPOTS",
    value: "1,428",
    change: "+12%",
    icon: "◉",
    type: "normal",
  },
  {
    label: "HIGH-RISK ANOMALIES",
    value: "23",
    change: "NDRF ALERT ACTIVE",
    icon: "⚠",
    type: "danger",
  },
  {
    label: "PERSISTENT THERMAL SOURCES",
    value: "312",
    change: "BASELINE MATCHED",
    icon: "▣",
    type: "warning",
  },
  {
    label: "ABNORMAL SURGES",
    value: "47",
    change: ">120 MW",
    icon: "↗",
    type: "danger",
  },
];

function KPICards() {
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