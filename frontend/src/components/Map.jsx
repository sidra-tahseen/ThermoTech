import { useEffect, useState } from "react";
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Popup,
  ZoomControl,
} from "react-leaflet";

import { fetchHotspots, classColor, classLabel } from "../services/api";
import "leaflet/dist/leaflet.css";

function Map({ filters }) {
  const [hotspots, setHotspots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchHotspots()
      .then((data) => {
        setHotspots(data.hotspots || []);
      })
      .catch((err) => {
        console.error("Failed to fetch hotspots:", err);
        setError("Unable to load hotspot data");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  return (
    <section className="map-card">
      <div className="map-header">
        <div>
          <div className="map-title">
            SIMILIPAL SECTOR GRID
          </div>

          <div className="map-subtitle">
            NASA FIRMS THERMAL DETECTIONS
          </div>
        </div>

        <div className="map-controls">
          <button>ORTHO</button>
          <button>TOPO</button>
          <button>WIND</button>
        </div>
      </div>

      <MapContainer
        center={[21.8472, 86.3219]}
        zoom={8}
        zoomControl={false}
        className="leaflet-map"
      >
        <ZoomControl position="bottomright" />

        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {hotspots
  .filter((hotspot) => {
    const categoryEnabled =
      filters.categories[hotspot.classification] ?? true;

    const frp = Number(hotspot.raw?.frp ?? hotspot.frp ?? 0);
    const frpEnabled = frp >= filters.minFrp;

    return categoryEnabled && frpEnabled;
  })
  .map((hotspot, index) => {
          const latitude = Number(hotspot.latitude);
          const longitude = Number(hotspot.longitude);
          const classification = hotspot.classification;
          const risk = hotspot.risk ?? {};

          if (isNaN(latitude) || isNaN(longitude)) {
            return null;
          }

          const color = classColor(classification);

          return (
            <CircleMarker
              key={hotspot.id ?? `hotspot-${index}`}
              center={[latitude, longitude]}
              radius={8}
              pathOptions={{
                color: color,
                fillColor: color,
                fillOpacity: 0.75,
                weight: 2,
              }}
            >
              <Popup>
                <strong>
                  {hotspot.id ?? `HOTSPOT-${index + 1}`}
                </strong>

                <br />

                Location: {latitude.toFixed(4)},{" "}
                {longitude.toFixed(4)}

                <br />

                Classification:{" "}
                {classLabel(classification)}

                <br />

                Confidence:{" "}
                {hotspot.confidence !== undefined
                  ? `${(Number(hotspot.confidence) * 100).toFixed(1)}%`
                  : "N/A"}

                <br />
FRP:{" "}
{hotspot.raw?.frp !== undefined
  ? `${Number(hotspot.raw.frp).toFixed(1)} MW`
  : "N/A"}

<br />

Risk Score:{" "}
{risk.risk_score !== undefined
  ? `${Number(risk.risk_score).toFixed(1)} / 100`
  : "N/A"}

<br />

Risk Level:{" "}
{risk.severity ?? "N/A"}

                
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>

      <div className="map-overlay">
        <div>
          {loading
  ? "LOADING HOTSPOTS..."
  : `${hotspots.filter((hotspot) => {
      const categoryEnabled =
        filters.categories[hotspot.classification] ?? true;

      const frp = Number(hotspot.raw?.frp ?? hotspot.frp ?? 0);

      return categoryEnabled && frp >= filters.minFrp;
    }).length} HOTSPOTS`}
        </div>

        <div>
          {error
            ? error
            : "SIMILIPAL AOI"}
        </div>

        <div>
          10 KM OSM LAND USE
        </div>
      </div>
    </section>
  );
}

export default Map;
