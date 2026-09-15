/**
 * Session store: current user, active pet, query mode.
 * Platform-neutral — no DOM, no uni.* APIs (platform adapters live in ./platform).
 */
import { reactive } from "vue";
import { ApiError, client, setTokenProvider } from "../api/client";

export type QueryMode = "with_pet" | "restrictions" | "service_dog" | "rules_only";

export interface SessionUser {
  id: string;
  display_name: string;
  email: string | null;
  role: string;
}

export interface ActivePet {
  id: string;
  display_name: string;
  species: string;
  breed_text: string | null;
  weight_kg: number | null;
  service_role: string;
  /**
   * ADR-025 / Consumer UX §14 — the precise animal role, when the user declares
   * one (e.g. `guide_dog`). Optional: without it a service-dog query expands to
   * the whole assistance group (query-side only), so a hearing dog would still
   * see a guide-dog proviso. Declaring the role removes that ambiguity.
   */
  declared_role?: string | null;
}

const TOKEN_KEY = "pa_token";

function getToken(): string | undefined {
  return platformStorage.get(TOKEN_KEY);
}

/** Storage adapter injected per platform (localStorage / uni storage). */
export const platformStorage = {
  get: (_k: string): string | undefined => undefined,
  set: (_k: string, _v: string): void => undefined,
  remove: (_k: string): void => undefined,
};

export function bindStorage(impl: Pick<typeof platformStorage, "get" | "set" | "remove">) {
  Object.assign(platformStorage, impl);
  setTokenProvider(getToken);
}

export const session = reactive({
  user: null as SessionUser | null,
  mode: "with_pet" as QueryMode,
  activePet: null as ActivePet | null,

  get signedIn(): boolean {
    return getToken() !== undefined;
  },

  async restore(): Promise<SessionUser | null> {
    if (!getToken()) return null;
    try {
      this.user = await client.me();
    } catch (e: unknown) {
      if (e instanceof ApiError && e.status === 401) {
        platformStorage.remove(TOKEN_KEY);
        this.user = null;
      }
    }
    return this.user;
  },

  async login(email: string, password: string): Promise<void> {
    const res = await client.login(email, password);
    platformStorage.set(TOKEN_KEY, res.access_token);
    await this.restore();
  },

  async register(displayName: string, email: string, password: string): Promise<void> {
    const res = await client.register(displayName, email, password);
    platformStorage.set(TOKEN_KEY, res.access_token);
    await this.restore();
  },

  logout(): void {
    platformStorage.remove(TOKEN_KEY);
    this.user = null;
  },
});
