/**
 * E2E global setup: prove the API under test is not pointed at production.
 *
 * The E2E suite drives real user journeys against a real API. `reuseExistingServer`
 * means a dev server left running on the expected port would serve the suite
 * silently — which is exactly how test fixtures ended up inside `petaccess`.
 *
 * The webServer command already provisions and binds `petaccess_e2e`, but a
 * command that failed to bind (port taken) would leave the *old* server
 * answering. So the setup asks the running process which database it is attached
 * to, via the read-only `/health/database` endpoint, and refuses to continue
 * unless it says `petaccess_e2e` with role `E2E`.
 */
import { request } from "@playwright/test";

const API_BASE = "http://127.0.0.1:8010";
const EXPECTED_DATABASE = "petaccess_e2e";
const EXPECTED_ROLE = "E2E";

export default async function globalSetup(): Promise<void> {
  const ctx = await request.newContext({ baseURL: API_BASE });
  let payload: { database?: string; role?: string; app_env?: string };
  try {
    const res = await ctx.get("/health/database");
    if (!res.ok()) {
      throw new Error(`/health/database returned ${res.status()}`);
    }
    payload = (await res.json()) as { database?: string; role?: string; app_env?: string };
  } finally {
    await ctx.dispose();
  }

  console.log(
    `\n[E2E] TARGET_DB = ${payload.database ?? "?"}\n[E2E] TARGET_DB_ROLE = ${payload.role ?? "?"}\n`,
  );

  if (payload.database !== EXPECTED_DATABASE || payload.role !== EXPECTED_ROLE) {
    throw new Error(
      [
        "",
        "E2E_DATABASE_REFUSED — the API on " + API_BASE + " is not the E2E instance.",
        `  expected : ${EXPECTED_DATABASE} (${EXPECTED_ROLE})`,
        `  actual   : ${payload.database ?? "?"} (${payload.role ?? "?"})`,
        "",
        "  Most likely a stale server is holding the port and reuseExistingServer",
        "  handed the suite to it. Nothing in this run may touch that database.",
        "",
        "  Fix: stop the process on " + API_BASE + ", then re-run.",
        "  Provision the E2E database with:",
        "    python scripts/isolated_db.py --role E2E --reset",
        "",
      ].join("\n"),
    );
  }
}
