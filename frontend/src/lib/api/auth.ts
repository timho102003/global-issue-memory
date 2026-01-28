import { api, setAuthToken, removeAuthToken } from "./client";
import type {
  TokenResponse,
  GIMIdentityResponse,
  GIMIdentityCreate,
  RateLimitInfo,
} from "@/types";

/**
 * Create a new GIM ID.
 *
 * @param data - Optional creation data
 * @returns Created GIM identity
 */
export async function createGimId(
  data?: GIMIdentityCreate
): Promise<GIMIdentityResponse> {
  return api.post<GIMIdentityResponse>("/auth/gim-id", data || {});
}

/**
 * Exchange GIM ID for JWT token.
 *
 * @param gimId - GIM ID (UUID format)
 * @returns Token response
 */
export async function getToken(gimId: string): Promise<TokenResponse> {
  const response = await api.post<TokenResponse>("/auth/token", { gim_id: gimId });
  setAuthToken(response.access_token);
  return response;
}

/**
 * Get current rate limit info.
 *
 * @returns Rate limit information
 */
export async function getRateLimit(): Promise<RateLimitInfo> {
  return api.get<RateLimitInfo>("/auth/rate-limit");
}

/**
 * Sign out - removes stored token.
 */
export function signOut(): void {
  removeAuthToken();
}

/**
 * Check if a string is a valid UUID format.
 *
 * @param str - String to check
 * @returns True if valid UUID
 */
export function isValidGimId(str: string): boolean {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  return uuidRegex.test(str);
}
