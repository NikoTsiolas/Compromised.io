import { defineConfig, devices } from "@playwright/test";

import { apiPort, databaseUrl, webPort } from "./e2e/env";

// The browser suite starts its own API and web app against a test database seeded from captured
// samples, so it never touches the dev servers or dev data. Ports and database: see e2e/env.ts.
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: `http://127.0.0.1:${webPort}`,
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      testIgnore: /new-events\.spec\.ts/,
      use: { ...devices["Desktop Chrome"] },
    },
    {
      // Adds events to the shared test database, so it runs only after every read-only test.
      name: "chromium-writes",
      testMatch: /new-events\.spec\.ts/,
      dependencies: ["chromium"],
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command:
        "uv run python -m compromised.seed --reset" +
        " bleepingcomputer=tests/fixtures/real/bleepingcomputer.xml" +
        " bleepingcomputer=tests/fixtures/synthetic/text-not-markup.xml" +
        ` && uv run uvicorn compromised.api:create_app --factory --port ${apiPort}`,
      cwd: "../api",
      env: { DATABASE_URL: databaseUrl, ENVIRONMENT: "test" },
      url: `http://127.0.0.1:${apiPort}/healthz`,
      reuseExistingServer: false,
    },
    {
      command: `pnpm build && pnpm start --port ${webPort}`,
      // SAMPLE_PREVIEW builds the clearly labelled /preview route so the suite can check it.
      env: { API_URL: `http://127.0.0.1:${apiPort}`, SAMPLE_PREVIEW: "1" },
      url: `http://127.0.0.1:${webPort}`,
      reuseExistingServer: false,
      timeout: 180_000,
    },
  ],
});
