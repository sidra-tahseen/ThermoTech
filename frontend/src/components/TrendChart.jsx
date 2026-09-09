import { useEffect, useState } from "react";
import axios from "axios";

function TrendChart() {
  const [trendData, setTrendData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios
      .get("/api/trends")
      .then((response) => {
        setTrendData(response.data.points || []);
      })
      .catch((error) => {
        console.error("Failed to fetch trend data:", error);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const hourlyData = Array.from({ length: 24 }, (_, hour) => {
    const point = trendData.find(
      (item) => Number(item.hour) === hour
    );

    return {
      hour,
      frp: point?.average_frp ?? 0,
      baseline: point?.historical_baseline ?? 0,
    };
  });

  const maxValue = Math.max(
    ...hourlyData.map((item) =>
      Math.max(item.frp, item.baseline)
    ),
    1
  );

  // Convert data values into SVG coordinates
  const getPoints = (key) => {
    return hourlyData
      .map((item, index) => {
        const x = (index / 23) * 700;
        const y = 160 - (item[key] / maxValue) * 140;

        return `${x},${y}`;
      })
      .join(" ");
  };

  return (
    <section className="trend-card">

      <div className="trend-header">

        <div>
          <div className="trend-title">
            24-HOUR DIURNAL FIRE RADIATIVE POWER
          </div>

          <div className="trend-subtitle">
            FRP (MW) vs HISTORICAL BASELINE
          </div>
        </div>

        <div className="trend-live">
          {loading ? "LOADING" : "COLLECTED DATA"}
        </div>

      </div>

      <div className="chart">

        <div className="chart-grid">
          <span>{Math.round(maxValue)}</span>
          <span>{Math.round(maxValue * 0.66)}</span>
          <span>{Math.round(maxValue * 0.33)}</span>
          <span>0</span>
        </div>

        <svg
          viewBox="0 0 700 180"
          preserveAspectRatio="none"
          className="chart-svg"
        >

          {!loading && (
            <>
              <polyline
                points={getPoints("frp")}
                fill="none"
                stroke="#4cd7f6"
                strokeWidth="3"
              />

              <polyline
                points={getPoints("baseline")}
                fill="none"
                stroke="#869397"
                strokeWidth="2"
                strokeDasharray="6 6"
              />
            </>
          )}

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