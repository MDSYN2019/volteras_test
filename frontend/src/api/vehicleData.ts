import axios from "axios";
import type { PaginatedVehicleData, VehicleDataQuery } from "../types/vehicleData";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
});

export async function fetchVehicleData(query: VehicleDataQuery): Promise<PaginatedVehicleData> {
  const response = await api.get<PaginatedVehicleData>("/api/v1/vehicle_data/", {
    params: {
      vehicle_id: query.vehicleId,
      start_timestamp: query.startTimestamp || undefined,
      end_timestamp: query.endTimestamp || undefined,
      page: query.page,
      page_size: query.pageSize,
      sort_by: query.sortBy,
      sort_order: query.sortOrder,
    },
  });
  return response.data;
}
