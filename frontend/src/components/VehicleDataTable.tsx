import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import type { VehicleData } from "../types/vehicleData";

const columnHelper = createColumnHelper<VehicleData>();

const columns = [
  columnHelper.accessor("timestamp", { header: "Timestamp" }),
  columnHelper.accessor("speed", { header: "Speed (km/h)", cell: (info) => info.getValue() ?? "—" }),
  columnHelper.accessor("odometer", { header: "Odometer (km)" }),
  columnHelper.accessor("soc", { header: "SOC (%)" }),
  columnHelper.accessor("elevation", { header: "Elevation (m)" }),
  columnHelper.accessor("shift_state", { header: "Shift", cell: (info) => info.getValue() ?? "—" }),
];

type Props = {
  data: VehicleData[];
  onSort: (column: keyof VehicleData) => void;
};

export function VehicleDataTable({ data, onSort }: Props) {
  const table = useReactTable({ data, columns, getCoreRowModel: getCoreRowModel() });

  return (
    <div className="table-shell">
      <table>
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th key={header.id} onClick={() => onSort(header.column.id as keyof VehicleData)}>
                  {flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id}>
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
