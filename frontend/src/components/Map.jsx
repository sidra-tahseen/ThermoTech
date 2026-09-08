import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Popup,
  ZoomControl,
} from "react-leaflet";

import "leaflet/dist/leaflet.css";
import { useEffect, useState } from "react";
import { fetchHotspots } from "../services/api";

function getRiskColor(classification) {
  if (classification === "NEW_ABNORMAL_EVENT") return "#ff4d4d";
  if (classification === "PERSISTENT_SOURCE") return "#ffb84d";
  return "#4cd7f6";
}

function Map() {
  const [hotspots, setHotspots] = useState([]);

  useEffect(() => {
    fetchHotspots(861)
      .then((data) => {
        setHotspots(data.hotspots || []);
      })
      .catch((error) => {
        console.error("Failed to load hotspots:", error);
      });
  }, []);

  return (
    <section className="map-card">
      <div className="map-header">
        <div>
          <div className="map-title">SIMILIPAL SECTOR GRID</div>

          <div className="map-subtitle">LIVE NASA FIRMS THERMAL DETECTIONS</div>
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

        {hotspots.map((hotspot) => (
          <CircleMarker
            key={hotspot.id}
            center={[hotspot.latitude, hotspot.longitude]}
            radius={10}
            pathOptions={{
              color: getRiskColor(hotspot.classification),
              fillColor: getRiskColor(hotspot.classification),
              fillOpacity: 0.75,
              weight: 2,
            }}
          >
            <Popup>
              <strong>HOTSPOT #{hotspot.source_row_id}</strong>
              <br />
              FRP: {hotspot.frp} MW
              <br />
              Classification: {hotspot.classification}
              <br />
              Confidence: {(hotspot.confidence * 100).toFixed(0)}%
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>

      <div className="map-overlay">
        <div>84 / 1,428 HOTSPOTS</div>
        <div>21°45'12" N, 86°20'44" E</div>
        <div>10 KM OSM LAND USE</div>
      </div>
    </section>
  );
}

export default Map;
