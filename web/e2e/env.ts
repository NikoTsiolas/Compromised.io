// Shared settings for the browser suite. Every value can be overridden by environment variable,
// so several checkouts can run the suite at once against their own database and ports.
export const databaseUrl =
  process.env.E2E_DATABASE_URL ?? "postgresql:///compromised_test";
export const apiPort = Number(process.env.E2E_API_PORT ?? 8100);
export const webPort = Number(process.env.E2E_WEB_PORT ?? 3100);
