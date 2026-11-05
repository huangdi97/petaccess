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
const ACTIVE_PET_KEY = "pa_active_pet_id";

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

let restoreInFlight: Promise<SessionUser | null> | null = null;

export const session = reactive({
  user: null as SessionUser | null,
  mode: "with_pet" as QueryMode,
  activePet: null as ActivePet | null,
  /** Ephemeral query role; never inferred from images or credentials. */
  declaredRole: null as string | null,
  /**
   * Last persisted-session restoration problem. Public Rule/Reality/Evidence
   * surfaces may continue anonymously, but should not silently pretend the
   * private context was restored successfully.
   */
  restoreIssue: null as null | "auth_invalid" | "unavailable",

  get signedIn(): boolean {
    return getToken() !== undefined;
  },

  async restore(): Promise<SessionUser | null> {
    if (!getToken()) return null;
    // QueryContextBar and the active page can mount together. Share one
    // in-flight restore so every surface sees the same persisted subject
    // without issuing duplicate /me and /pets requests.
    if (restoreInFlight) return restoreInFlight;
    restoreInFlight = (async () => {
      try {
        this.user = await client.me();
        this.restoreIssue = null;
        const activePetId = platformStorage.get(ACTIVE_PET_KEY);
        if (activePetId && this.activePet?.id !== activePetId) {
          const pets = await client.myPets();
          this.activePet = pets.find((pet) => pet.id === activePetId) ?? null;
          if (!this.activePet) {
            platformStorage.remove(ACTIVE_PET_KEY);
          } else if (this.mode === "with_pet" && this.activePet.service_role === "working") {
            // A persisted working service-dog profile must reopen in the matching
            // query mode so the UI can ask for the precise declared role instead
            // of silently presenting a generic ordinary-pet context.
            this.mode = "service_dog";
          }
        }
      } catch (e: unknown) {
        if (e instanceof ApiError && e.status === 401) {
          platformStorage.remove(TOKEN_KEY);
          platformStorage.remove(ACTIVE_PET_KEY);
          this.user = null;
          this.activePet = null;
          this.restoreIssue = "auth_invalid";
        } else {
          // Keep the persisted token for a transient network/server failure,
          // but expose that private context could not be restored.
          this.restoreIssue = "unavailable";
        }
      }
      return this.user;
    })();
    try {
      return await restoreInFlight;
    } finally {
      restoreInFlight = null;
    }
  },

  async login(email: string, password: string): Promise<void> {
    const res = await client.login(email, password);
    platformStorage.set(TOKEN_KEY, res.access_token);
    this.restoreIssue = null;
    await this.restore();
  },

  async register(displayName: string, email: string, password: string): Promise<void> {
    const res = await client.register(displayName, email, password);
    platformStorage.set(TOKEN_KEY, res.access_token);
    this.restoreIssue = null;
    await this.restore();
  },

  setActivePet(pet: ActivePet | null): void {
    this.activePet = pet;
    if (pet) platformStorage.set(ACTIVE_PET_KEY, pet.id);
    else platformStorage.remove(ACTIVE_PET_KEY);
  },

  setDeclaredRole(role: string | null): void {
    this.declaredRole = role;
  },

  logout(): void {
    platformStorage.remove(TOKEN_KEY);
    platformStorage.remove(ACTIVE_PET_KEY);
    this.user = null;
    // Pet context belongs to the authenticated user. Keeping it alive after
    // logout can leak the previous account's profile into the next public
    // query or a different user's session in the same app runtime.
    this.activePet = null;
    this.declaredRole = null;
    this.restoreIssue = null;
    this.mode = "with_pet";
  },
});
