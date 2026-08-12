export type VehicleLocation = {
  schema_version: number;
  vehicle_id: string;
  timestamp: string;
  latitude: number;
  longitude: number;
  sequence: number;
  processed_at: string;
  product: "live_vehicle_location";
};
