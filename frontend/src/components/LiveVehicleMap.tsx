import { useEffect, useMemo, useState } from "react";

import type { VehicleLocation } from "../types/vehicleLocation";

const wsUrl = import.meta.env.VITE_LOCATION_WS_URL ?? "ws://localhost:8080/locations";

export function LiveVehicleMap() {
  const [locations, setLocations] = useState<VehicleLocation[]>([]);
  const [status, setStatus] = useState<"connecting" | "live" | "offline">("connecting");

  useEffect(() => {
    let socket: WebSocket | undefined;
    let retry: number;
    let stopped = false;

    const connect = () => {
      setStatus("connecting");
      socket = new WebSocket(wsUrl);
      socket.onopen = () => setStatus("live");
      socket.onmessage = (event) => {
        const location = JSON.parse(event.data) as VehicleLocation;
        setLocations((current) => [...current.slice(-59), location]);
      };
      socket.onerror = () => socket?.close();
      socket.onclose = () => {
        if (!stopped) {
          setStatus("offline");
          retry = window.setTimeout(connect, 2000);
        }
      };
    };
    connect();
    return () => {
      stopped = true;
      window.clearTimeout(retry);
      socket?.close();
    };
  }, []);

  const points = useMemo(() => {
    if (!locations.length) return [];
    const lats = locations.map(({ latitude }) => latitude);
    const lons = locations.map(({ longitude }) => longitude);
    const latMin = Math.min(...lats) - 0.002;
    const latRange = Math.max(Math.max(...lats) - latMin + 0.002, 0.004);
    const lonMin = Math.min(...lons) - 0.002;
    const lonRange = Math.max(Math.max(...lons) - lonMin + 0.002, 0.004);
    return locations.map((location) => ({
      ...location,
      x: 30 + ((location.longitude - lonMin) / lonRange) * 740,
      y: 30 + (1 - (location.latitude - latMin) / latRange) * 320,
    }));
  }, [locations]);

  const current = locations[locations.length - 1];
  const latestPoint = points[points.length - 1];

  return (
    <section className="live-map" aria-labelledby="live-map-title">
      <div className="live-map-header">
        <div>
          <p className="eyebrow">Kafka location product</p>
          <h2 id="live-map-title">Live vehicle location</h2>
          <p>Raw GPS → validated location topic → WebSocket consumer</p>
        </div>
        <span className={`stream-status ${status}`}>{status}</span>
      </div>
      <div className="map-canvas">
        <svg viewBox="0 0 800 380" role="img" aria-label="Vehicle route plotted from live coordinates">
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#d7e8e2" strokeWidth="1" />
            </pattern>
          </defs>
          <rect width="800" height="380" fill="url(#grid)" />
          <polyline points={points.map(({ x, y }) => `${x},${y}`).join(" ")} fill="none" stroke="#1b8066" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" />
          {latestPoint && <circle cx={latestPoint.x} cy={latestPoint.y} r="10" fill="#ff6b35" stroke="white" strokeWidth="4" />}
        </svg>
        {!current && <p className="map-empty">Start the live-tracking profile to see the vehicle move.</p>}
      </div>
      <div className="coordinate-strip">
        <strong>{current?.vehicle_id ?? "Waiting for vehicle…"}</strong>
        <span>Latitude <b>{current?.latitude.toFixed(6) ?? "—"}</b></span>
        <span>Longitude <b>{current?.longitude.toFixed(6) ?? "—"}</b></span>
        <span>Updated <b>{current ? new Date(current.timestamp).toLocaleTimeString() : "—"}</b></span>
      </div>
    </section>
  );
}
