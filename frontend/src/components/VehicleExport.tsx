import { useState } from "react";

import {
  exportVehicleData,
  type ExportFormat,
} from "../api/exportVehicleData";

interface VehicleExportProps {
  vehicleId: string;
}

export function VehicleExport({
  vehicleId,
}: VehicleExportProps) {
  const [format, setFormat] = useState<ExportFormat>("csv");
  const [isDownloading, setIsDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleExport(): Promise<void> {
    setIsDownloading(true);
    setError(null);

    try {
      await exportVehicleData(vehicleId, format);
    } catch (error: unknown) {
      setError(
        error instanceof Error
          ? error.message
          : "Export failed",
      );
    } finally {
      setIsDownloading(false);
    }
  }

  return (
    <div className="vehicle-export">
      <label htmlFor="export-format">
        Export format
      </label>

      <select
        id="export-format"
        value={format}
        onChange={(event) =>
          setFormat(event.target.value as ExportFormat)
        }
      >
        <option value="csv">CSV</option>
        <option value="json">JSON</option>
        <option value="xlsx">Excel</option>
      </select>

      <button
        type="button"
        onClick={handleExport}
        disabled={isDownloading || !vehicleId}
      >
        {isDownloading ? "Exporting..." : "Export"}
      </button>

      {error && <p role="alert">{error}</p>}
    </div>
  );
}