function TrendChart() {
  return (
    <section className="trend-card">

      <div className="trend-header">

        <div>
          <div className="trend-title">
            24-HOUR DIURNAL FIRE RADIATIVE POWER
          </div>

          <div className="trend-subtitle">
            FRP (MW) vs 180-DAY BASELINE
          </div>
        </div>

        <div className="trend-live">
          09:42 UTC • NOW
        </div>

      </div>

      <div className="chart">

        <div className="chart-grid">
          <span>300</span>
          <span>200</span>
          <span>100</span>
          <span>0</span>
        </div>

        <svg
          viewBox="0 0 700 180"
          preserveAspectRatio="none"
          className="chart-svg"
        >

          <polyline
            points="0,145 80,138 150,142 220,130 290,134 360,120 430,115 500,108 570,112 640,90 700,35"
            fill="none"
            stroke="#4cd7f6"
            strokeWidth="3"
          />

          <polyline
            points="0,155 80,152 150,150 220,148 290,145 360,142 430,140 500,138 570,136 640,134 700,132"
            fill="none"
            stroke="#869397"
            strokeWidth="2"
            strokeDasharray="6 6"
          />

        </svg>

      </div>

      <div className="chart-axis">
        <span>00:00</span>
        <span>04:00</span>
        <span>08:00</span>
        <span>12:00</span>
        <span>16:00</span>
        <span>20:00</span>
        <span>24:00</span>
      </div>

    </section>
  );
}

export default TrendChart;