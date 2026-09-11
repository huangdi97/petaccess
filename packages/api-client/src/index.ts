/**
 * Typed API client wrapper.
 *
 * SSOT: FastAPI OpenAPI (openapi.json snapshot → src/schema.d.ts regenerated
 * via `pnpm generate` when the API changes). Business code must never
 * hand-write DTOs (ADR-011).
 */
import type { paths } from "./schema";

export type ApiPaths = paths;

export interface ClientOptions {
  baseUrl: string;
  /** Returns the current bearer token, when signed in. */
  getToken?: () => string | undefined;
  /** Idempotency-Key header helper for high-risk writes. */
  getIdempotencyKey?: () => string | undefined;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type HttpMethod = "get" | "post" | "patch" | "put" | "delete";

interface RequestOptions {
  query?: Record<string, string | number | boolean | undefined>;
  body?: unknown;
  headers?: Record<string, string>;
}

export function createClient(options: ClientOptions) {
  const base = options.baseUrl.replace(/\/$/, "");

  async function request<T>(
    method: HttpMethod,
    path: string,
    opts: RequestOptions = {},
  ): Promise<T> {
    const url = new URL(base + path);
    for (const [k, v] of Object.entries(opts.query ?? {})) {
      if (v !== undefined) url.searchParams.set(k, String(v));
    }
    const headers: Record<string, string> = {
      Accept: "application/json",
      ...opts.headers,
    };
    const token = options.getToken?.();
    if (token) headers.Authorization = `Bearer ${token}`;
    const idem = options.getIdempotencyKey?.();
    if (idem && (method === "post" || method === "patch")) {
      headers["Idempotency-Key"] = idem;
    }
    if (opts.body !== undefined) headers["Content-Type"] = "application/json";

    const res = await fetch(url.toString(), {
      method: method.toUpperCase(),
      headers,
      body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
    });

    if (res.status === 204) return undefined as T;
    const payload = (await res.json().catch(() => ({}))) as Record<string, unknown>;
    if (!res.ok) {
      const err = (payload.error ?? {}) as { code?: string; message?: string; details?: unknown };
      throw new ApiError(res.status, err.code ?? "unknown", err.message ?? res.statusText,
                         err.details);
    }
    return payload as T;
  }

  return { request, baseUrl: base };
}

export type ApiClient = ReturnType<typeof createClient>;

/** Narrow helper: extract the success response type of an operation. */
export type ApiResponse<P extends keyof ApiPaths, M extends keyof ApiPaths[P]> =
  ApiPaths[P][M] extends { responses: infer R }
    ? R extends { 200: { content: { "application/json": infer J } } }
      ? J
      : unknown
    : never;
