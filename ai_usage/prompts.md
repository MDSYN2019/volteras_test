# AI usage log

The challenge asks candidates who use AI tooling to preserve the prompts and relevant generated output. This log summarises the meaningful ways AI was used during the project.

## Prompt 1

**Purpose:** Create an initial repository structure.

**Prompt:**

> Create a production-shaped FastAPI, PostgreSQL and React/TypeScript starter for an EV telemetry take-home challenge. Include Docker Compose, pagination, sorting, tests, CSV import and documentation.

**Relevant output:**

* Suggested a FastAPI backend, PostgreSQL database and React/TypeScript frontend.
* Proposed a Docker Compose setup and an initial directory structure.
* Included example pagination, sorting, import and export functionality.

**How the output was used:**

* Used as the initial project scaffold.
* All generated code was reviewed, run and modified.
* The API models, routes, CSV handling, export functionality and frontend behaviour were adjusted while implementing and testing the application.

**Validation:**

* Built and ran the services with Docker Compose.
* Tested the FastAPI endpoints manually and with pytest.
* Tested the frontend against the running backend.

## Prompt 2

**Purpose:** Understand and modify the React/TypeScript frontend.

**Prompt summary:**

> Explain the TypeScript and React frontend structure in simple terms, including `main.tsx`, `App.tsx`, components, API modules, types and Vite.

**Relevant output:**

* Explained React components, state, props and event handlers.
* Explained how TypeScript types describe API response data.
* Identified that HTTP requests to FastAPI were made through the functions in `src/api`.

**How the output was used:**

* Used as a learning aid because I had not previously worked with TypeScript.
* Used to understand the generated frontend before modifying it.
* I then updated `App.tsx`, component props, filtering, pagination and API integration myself.

**Validation:**

* Ran the TypeScript/Vite build.
* Opened the frontend in the browser.
* Confirmed that filtering, pagination, sorting and export actions called the expected FastAPI endpoints.

## Prompt 3

**Purpose:** Add a visualisation of telemetry data.

**Prompt:**

> Plot vehicle data values in the frontend rather than only displaying them in a table.

**Relevant output:**

* Suggested using Recharts.
* Produced an example `VehicleDataChart` component.
* Suggested allowing the user to select speed, odometer, state of charge or elevation.
* Showed how to pass the paginated API response into both the chart and the table.

**How the output was used:**

* Used as boilerplate for the chart component.
* Reviewed and integrated the component into `App.tsx`.
* Adapted the component to the existing `VehicleData` type and API response.
* The chart currently displays values from the current paginated result set.

**Validation:**

* Rebuilt the frontend Docker image.
* Loaded the application in the browser.
* Confirmed that changing the selected field changed the plotted values.

## Prompt 4

**Purpose:** Add backend test coverage.

**Prompt summary:**

> Create pytest tests for the CSV import service, export service, vehicle-data API routes, database-session dependency and health endpoint.

**Relevant output:**

* Generated example pytest fixtures and test cases.
* Suggested mocking SQLAlchemy sessions with `MagicMock`.
* Suggested using `monkeypatch` to isolate CSV parsing, database insertion and export behaviour.
* Included tests for successful responses, validation failures, missing records and unsupported inputs.

**How the output was used:**

* Used as boilerplate for pytest mocking and monkeypatching, which I was less familiar with.
* Reviewed each test against the implementation.
* Modified fixtures, imports, mocked return values and assertions where required.
* Added coverage for error branches such as malformed CSV rows, duplicate records, invalid filenames and missing API data.

**Validation:**

* Ran the test suite with pytest.
* Ran pytest-cov to inspect uncovered lines and branches.
* Corrected tests that used an isolated router application when the full FastAPI application was required, such as the `/health` endpoint test.

## Prompt 5

**Purpose:** Diagnose frontend dependency and Docker build problems.

**Prompt summary:**

> Diagnose npm network errors and a Vite/plugin-react dependency conflict during the frontend Docker build.

**Relevant output:**

* Identified a stale npm proxy configuration from the `ENOTFOUND` error.
* Identified that Vite 8 was incompatible with the installed version of `@vitejs/plugin-react`.
* Suggested aligning dependency versions rather than using `--force` or `--legacy-peer-deps`.
* Suggested excluding `node_modules` from the Docker build context.

**How the output was used:**

* Used to identify the source of the build failures.
* Updated the dependency versions and Docker configuration.
* Did not use the suggestion to bypass dependency checks with `--force` or `--legacy-peer-deps`.

**Validation:**

* Rebuilt the frontend image using Docker Compose.
* Confirmed that npm dependency installation completed successfully.
* Confirmed that the Vite development server started and served the frontend.

## Overall use of AI

AI was mainly used for:

* Creating an initial scaffold.
* Explaining unfamiliar React and TypeScript concepts.
* Producing boilerplate tests involving pytest mocks and monkeypatching.
* Suggesting debugging steps for Docker, npm and dependency issues.

The generated output was not treated as authoritative. Code was reviewed, adapted and validated through automated tests, Docker builds, API requests and browser testing.


