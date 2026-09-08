import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Popup,
  ZoomControl,
} from "react-leaflet";
import { getHotspots } from "../services/api";
import "leaflet/dist/leaflet.css";

const hotspots = [
  {
    id: "EVT-9402",
    lat: 21.8472,
    lng: 86.3219,
    frp: 268.4,
    type: "Wildfire",
    risk: "HIGH",
  },
  {
    id: "EVT-8110",
    lat: 22.2604,
    lng: 84.8536,
    frp: 114,
    type: "Industrial",
    risk: "MEDIUM",
  },
  {
    id: "EVT-7301",
    lat: 21.75,
    lng: 86.15,
    frp: 18,
    type: "Agricultural",
    risk: "LOW",
  },
  {
    id: "EVT-9419",
    lat: 21.91,
    lng: 86.42,
    frp: 92,
    type: "Rapid Surge",
    risk: "HIGH",
  },
];

function getRiskColor(risk) {
  if (risk === "HIGH") return "#ff4d4d";
  if (risk === "MEDIUM") return "#ffb84d";
  return "#4cd7f6";
}

function Map() {
  return (
    <section className="map-card">

      <div className="map-header">
        <div>
          <div className="map-title">
            SIMILIPAL SECTOR GRID
          </div>

          <div className="map-subtitle">
            LIVE NASA FIRMS THERMAL DETECTIONS
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
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {hotspots.map((hotspot) => (
          <CircleMarker
            key={hotspot.id}
            center={[hotspot.lat, hotspot.lng]}
            radius={10}
            pathOptions={{
              color: getRiskColor(hotspot.risk),
              fillColor: getRiskColor(hotspot.risk),
              fillOpacity: 0.75,
              weight: 2,
            }}
          >
            <Popup>
              <strong>{hotspot.id}</strong>
              <br />
              FRP: {hotspot.frp} MW
              <br />
              Type: {hotspot.type}
              <br />
              Risk: {hotspot.risk}
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