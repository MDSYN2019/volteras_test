import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { fetchVehicleData } from "./api/vehicleData";
import { VehicleDataChart } from "./components/VehicleDataChart";
import { VehicleDataTable } from "./components/VehicleDataTable";
import { VehicleExport } from "./components/VehicleExport";
import type { VehicleData } from "./types/vehicleData";

import "./styles.css";

export default function App() {
  // Values currently entered into the filter form.
  const [vehicleIdInput, setVehicleIdInput] = useState("car-1");
  const [startTimestampInput, setStartTimestampInput] =
    useState("");
  const [endTimestampInput, setEndTimestampInput] =
    useState("");

  // Values currently applied to the API request.
  const [vehicleId, setVehicleId] = useState("car-1");
  const [startTimestamp, setStartTimestamp] = useState("");
  const [endTimestamp, setEndTimestamp] = useState("");

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  const [sortBy, setSortBy] =
    useState<keyof VehicleData>("timestamp");

  const [sortOrder, setSortOrder] =
    useState<"asc" | "desc">("asc");

  const query = useQuery({
    queryKey: [
      "vehicle-data",
      vehicleId,
      startTimestamp,
      endTimestamp,
      page,
      pageSize,
      sortBy,
      sortOrder,
    ],

    queryFn: () =>
      fetchVehicleData({
        vehicleId,
        startTimestamp: startTimestamp || undefined,
        endTimestamp: endTimestamp || undefined,
        page,
        pageSize,
        sortBy,
        sortOrder,
      }),

    enabled: vehicleId.length > 0,
  });

  function applyFilters(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setPage(1);
    setVehicleId(vehicleIdInput.trim());
    setStartTimestamp(startTimestampInput);
    setEndTimestamp(endTimestampInput);
  }

  function handleSort(column: keyof VehicleData) {
    if (sortBy === column) {
      setSortOrder((current) =>
        current === "asc" ? "desc" : "asc",
      );
    } else {
      setSortBy(column);
      setSortOrder("asc");
    }

    setPage(1);
  }

  function handlePageSizeChange(
    event: React.ChangeEvent<HTMLSelectElement>,
  ) {
    setPageSize(Number(event.target.value));
    setPage(1);
  }

  return (
    <main>
      <header>
        <p className="eyebrow">EV telemetry</p>

        <h1>Vehicle data</h1>

        <p>
          Filter, sort, plot and page through generated
          vehicle records.
        </p>
      </header>

      <form
        className="filters"
        onSubmit={applyFilters}
      >
        <label>
          Vehicle ID

          <input
            value={vehicleIdInput}
            onChange={(event) =>
              setVehicleIdInput(event.target.value)
            }
            required
          />
        </label>

        <label>
          Initial timestamp

          <input
            type="datetime-local"
            value={startTimestampInput}
            onChange={(event) =>
              setStartTimestampInput(event.target.value)
            }
          />
        </label>

        <label>
          Final timestamp

          <input
            type="datetime-local"
            value={endTimestampInput}
            onChange={(event) =>
              setEndTimestampInput(event.target.value)
            }
          />
        </label>

        <button type="submit">
          Filter
        </button>
      </form>

      {query.isLoading && (
        <p>Loading…</p>
      )}

      {query.isError && (
        <p role="alert">
          Could not load data. Check the API and filter
          values.
        </p>
      )}

      {query.data && (
        <>
          <div className="table-meta">
            <span>
              {query.data.total} records
            </span>

            <div className="table-actions">
              <label>
                Rows

                <select
                  value={pageSize}
                  onChange={handlePageSizeChange}
                >
                  {[10, 25, 50, 100].map((size) => (
                    <option
                      key={size}
                      value={size}
                    >
                      {size}
                    </option>
                  ))}
                </select>
              </label>

              <VehicleExport
                vehicleId={vehicleId}
              />
            </div>
          </div>

          <VehicleDataChart
            data={query.data.items}
          />

          <VehicleDataTable
            data={query.data.items}
            onSort={handleSort}
          />

          <nav
            className="pagination"
            aria-label="Pagination"
          >
            <button
              type="button"
              onClick={() =>
                setPage((currentPage) =>
                  currentPage - 1,
                )
              }
              disabled={page <= 1}
            >
              Previous
            </button>

            <span>
              Page {page} of{" "}
              {Math.max(query.data.pages, 1)}
            </span>

            <button
              type="button"
              onClick={() =>
                setPage((currentPage) =>
                  currentPage + 1,
                )
              }
              disabled={
                query.data.pages === 0 ||
                page >= query.data.pages
              }
            >
              Next
            </button>
          </nav>
        </>
      )}
    </main>
  );
}
