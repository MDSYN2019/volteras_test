import { useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { VehicleData } from "../types/vehicleData";


type ChartField =
  | "speed"
  | "odometer"
  | "soc"
  | "elevation";


type VehicleDataChartProps = {
  data: VehicleData[];
};


const FIELD_LABELS: Record<ChartField, string> = {
  speed: "Speed",
  odometer: "Odometer",
  soc: "State of charge",
  elevation: "Elevation",
};


export function VehicleDataChart({
  data,
}: VehicleDataChartProps) {
  // The field currently selected by the user.
  const [selectedField, setSelectedField] =
    useState<ChartField>("speed");

  /*
   * Recharts expects an array of simple objects.
   *
   * We transform each VehicleData object into:
   *
   * {
   *   timestamp: "21/07/2026, 10:30",
   *   value: 45.5
   * }
   */
  const chartData = data
    .filter(
      (row) =>
        typeof row[selectedField] === "number",
    )
    .map((row) => ({
      timestamp: new Date(
        row.timestamp,
      ).toLocaleString(),
      value: row[selectedField] as number,
    }));

  return (
    <section className="chart-section">
      <div className="chart-header">
        <div>
          <h2>Vehicle telemetry chart</h2>
          <p>
            Plot vehicle values against their timestamps.
          </p>
        </div>

        <label>
          Value
          <select
            value={selectedField}
            onChange={(event) =>
              setSelectedField(
                event.target.value as ChartField,
              )
            }
          >
            <option value="speed">Speed</option>
            <option value="odometer">
              Odometer
            </option>
            <option value="soc">
              State of charge
            </option>
            <option value="elevation">
              Elevation
            </option>
          </select>
        </label>
      </div>

      {chartData.length === 0 ? (
        <p>No values are available for this field.</p>
      ) : (
        <LineChart
          responsive
          data={chartData}
          style={{
            width: "100%",
            height: 360,
          }}
          margin={{
            top: 20,
            right: 30,
            bottom: 70,
            left: 20,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" />

          <XAxis
            dataKey="timestamp"
            angle={-30}
            textAnchor="end"
            height={90}
            interval="preserveStartEnd"
          />

          <YAxis
            width="auto"
            label={{
              value: FIELD_LABELS[selectedField],
              angle: -90,
              position: "insideLeft",
            }}
          />

          <Tooltip />

          <Line
            type="monotone"
            dataKey="value"
            name={FIELD_LABELS[selectedField]}
            stroke="#2563eb"
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 6 }}
            connectNulls={false}
          />
        </LineChart>
      )}
    </section>
  );
}