"use client";

import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import { LatLngExpression } from "leaflet";
import "leaflet/dist/leaflet.css";
import { useEffect } from "react";
import { KANPUR_CENTER } from "@/data/kanpur-wards";

const CATEGORY_COLORS: Record<string, string> = {
  roads: '#C24B2A',
  water: '#0D6B6E',
  garbage: '#6B7A2A',
};

export interface NearbyMapProps {
  issues: any[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export default function NearbyMap({ issues, selectedId, onSelect }: NearbyMapProps) {
  useEffect(() => {
    const L = require("leaflet");
    delete L.Icon.Default.prototype._getIconUrl;
    L.Icon.Default.mergeOptions({
      iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
      iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
      shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    });
  }, []);

  return (
    <MapContainer center={[KANPUR_CENTER.lat, KANPUR_CENTER.lng] as LatLngExpression} zoom={14} style={{ height: "100%", width: "100%" }}>
      <TileLayer
        attribution='&copy; OpenStreetMap'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {issues.map((issue: any) => (
        <CircleMarker
          key={issue.id}
          center={[parseFloat(issue.geo_lat), parseFloat(issue.geo_lng)] as LatLngExpression}
          radius={selectedId === issue.id ? 16 : 12}
          pathOptions={{
            fillColor: CATEGORY_COLORS[issue.category?.toLowerCase()] || '#1A1A1A',
            color: '#1A1A1A',
            weight: 2,
            fillOpacity: 1,
          }}
          eventHandlers={{ click: () => onSelect(issue.id) }}
        >
          <Popup>
            <div className="p-2">
              <p className="font-bold text-sm">{issue.title}</p>
              <p className="text-xs text-text-secondary">{issue.category}</p>
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
