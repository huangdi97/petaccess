import { createClient, ApiError } from "@petaccess/api-client";

const BASE = import.meta.env.VITE_API_BASE ?? "/api/v1";

export const api = createClient({
  baseUrl: BASE,
  getToken: () => localStorage.getItem("admin_token") ?? undefined,
});

export { ApiError };

export async function login(email: string, password: string): Promise<string> {
  const res = await api.request("post", "/auth/login", { body: { email, password } });
  const token = (res as { access_token: string }).access_token;
  localStorage.setItem("admin_token", token);
  return token;
}

export function logout(): void {
  localStorage.removeItem("admin_token");
}

interface PageLike<T> {
  items: T[];
  total: number;
}

export async function page<T>(
  path: string,
  query: Record<string, string | number | undefined> = {},
): Promise<PageLike<T>> {
  return api.request<PageLike<T>>("get", path, { query });
}

export async function get<T>(path: string): Promise<T> {
  return api.request<T>("get", path);
}

export async function post<T>(path: string, body?: unknown): Promise<T> {
  return api.request<T>("post", path, { body });
}

export async function patch<T>(path: string, body?: unknown): Promise<T> {
  return api.request<T>("patch", path, { body });
}

/** Shared error normalisation so every view renders the same message shape. */
export function errText(e: unknown): string {
  if (e instanceof ApiError) {
    const code = (e as unknown as { code?: string }).code;
    return code ? `${e.message}（${code}）` : e.message;
  }
  return String(e);
}

/** Short uuid renderer used across admin tables. */
export function shortId(id?: string | null, len = 8): string {
  if (!id) return "—";
  return `${id.slice(0, len)}…`;
}

/** ISO timestamp → local `YYYY-MM-DD HH:mm` (or em dash). */
export function ts(value?: string | null): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
