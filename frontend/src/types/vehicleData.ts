export type VehicleData = {
  id: number;
  vehicle_id: string;
  timestamp: string;
  speed: number | null;
  odometer: number;
  soc: number;
  elevation: number;
  shift_state: string | null;
};

export type PaginatedVehicleData = {
  items: VehicleData[];
  page: number;
  page_size: number;
  total: number;
  pages: number;
};

export type VehicleDataQuery = {
  vehicleId: string;
  startTimestamp?: string;
  endTimestamp?: string;
  page: number;
  pageSize: number;
  sortBy: keyof VehicleData;
  sortOrder: "asc" | "desc";
};
