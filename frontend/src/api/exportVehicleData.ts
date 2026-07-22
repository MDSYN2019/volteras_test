export type ExportFormat = "json" | "csv" | "xlsx";

function extractFilename(
  response: Response,
  fallback: string,
): string {
  const disposition = response.headers.get("content-disposition");

  if (!disposition) {
    return fallback;
  }

  const match = disposition.match(/filename="?([^"]+)"?/i);

  return match?.[1] ?? fallback;
}

export async function exportVehicleData(
  vehicleId: string,
  format: ExportFormat,
): Promise<void> {
  const url =
    `/vehicles/${encodeURIComponent(vehicleId)}` +
    `/export?format=${encodeURIComponent(format)}`;

  const response = await fetch(url, {
    method: "GET",
    headers: {
      Accept: "*/*",
    },
  });

  if (!response.ok) {
    let message = "Export failed";

    try {
      const errorBody = (await response.json()) as {
        detail?: string;
      };

      message = errorBody.detail ?? message;
    } catch {
      message = `Export failed with status ${response.status}`;
    }

    throw new Error(message);
  }

  const blob = await response.blob();
  const fallbackFilename =
    `${vehicleId}_vehicle_data.${format}`;

  const filename = extractFilename(
    response,
    fallbackFilename,
  );

  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = objectUrl;
  link.download = filename;

  document.body.appendChild(link);
  link.click();
  link.remove();

  URL.revokeObjectURL(objectUrl);
}