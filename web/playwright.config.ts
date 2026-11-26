import { defineConfig, devices } from "@playwright/test";

// The browser suite starts its own API (port 8100) and web app (port 3100) against a test
// database seeded from captured samples, so it never touches the dev servers or dev data.
const databaseUrl =
  process.env.E2E_DATABASE_URL ?? "postgresql:///compromised_test";
const apiPort = 8100;
const webPort = 3100;

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
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
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
      env: { API_URL: `http://127.0.0.1:${apiPort}` },
      url: `http://127.0.0.1:${webPort}`,
      reuseExistingServer: false,
      timeout: 180_000,
    },
  ],
});
