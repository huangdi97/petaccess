/**
 * Unified domain error → presentation (M2 §28, V020_EMPTY_ERROR_OFFLINE_SPEC).
 *
 * Every failure a consumer surface can hit is folded into one of six kinds:
 * NETWORK_OFFLINE / SERVICE_UNAVAILABLE / AUTH_EXPIRED / MAP_UNAVAILABLE /
 * CONTENT_NOT_FOUND / UNKNOWN_ERROR. The consumer UI must never display raw
 * 500 / SQLAlchemy / FastAPI / Tauri / Rust strings or a stack trace; pages
 * render the presentation this module returns.
 */
import {
  ERROR_PRESENTATIONS,
  type DomainErrorKind,
  type ErrorPresentation,
} from "@petaccess/design-tokens";
import { ApiError } from "@petaccess/client-core";

/** Server error codes the API surfaces (complemented by HTTP status). */
const SERVER_CODE_KINDS: Readonly<Record<string, DomainErrorKind>> = {
  auth_expired: "AUTH_EXPIRED",
  token_expired: "AUTH_EXPIRED",
  invalid_token: "AUTH_EXPIRED",
  not_found: "CONTENT_NOT_FOUND",
  resource_not_found: "CONTENT_NOT_FOUND",
  service_unavailable: "SERVICE_UNAVAILABLE",
  maintenance: "SERVICE_UNAVAILABLE",
};

/**
 * Map any thrown value to its presentation. Defaults to UNKNOWN_ERROR so a
 * caller can always render without checking the kind first.
 */
export function presentError(e: unknown): ErrorPresentation {
  if (typeof navigator !== "undefined" && navigator.onLine === false) {
    return ERROR_PRESENTATIONS.NETWORK_OFFLINE;
  }
  if (e instanceof ApiError) {
    const fromCode = SERVER_CODE_KINDS[e.code];
    if (fromCode) return ERROR_PRESENTATIONS[fromCode];
    if (e.status === 401) return ERROR_PRESENTATIONS.AUTH_EXPIRED;
    if (e.status === 404) return ERROR_PRESENTATIONS.CONTENT_NOT_FOUND;
    if (e.status >= 500) return ERROR_PRESENTATIONS.SERVICE_UNAVAILABLE;
    return ERROR_PRESENTATIONS.UNKNOWN_ERROR;
  }
  if (e instanceof TypeError) {
    // fetch() throws TypeError on network-level failure (DNS, refused, offline).
    return ERROR_PRESENTATIONS.NETWORK_OFFLINE;
  }
  return ERROR_PRESENTATIONS.UNKNOWN_ERROR;
}

/** Convenience: the presentation for a specific error kind. */
export function presentationFor(kind: DomainErrorKind): ErrorPresentation {
  return ERROR_PRESENTATIONS[kind];
}

/** The six kinds in a tuple for tests. */
export const ALL_ERROR_KINDS: readonly DomainErrorKind[] = [
  "NETWORK_OFFLINE",
  "SERVICE_UNAVAILABLE",
  "AUTH_EXPIRED",
  "MAP_UNAVAILABLE",
  "CONTENT_NOT_FOUND",
  "UNKNOWN_ERROR",
];
