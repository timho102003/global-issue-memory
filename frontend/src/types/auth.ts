/**
 * TypeScript types mirroring /gim/src/auth/models.py
 */

export type GIMIdentityStatus = "active" | "suspended" | "revoked";

export interface GIMIdentity {
  id: string;
  gim_id: string;
  created_at: string;
  last_used_at?: string;
  status: GIMIdentityStatus;
  daily_search_limit: number;
  daily_search_used: number;
  daily_reset_at?: string;
  total_searches: number;
  total_submissions: number;
  total_confirmations: number;
  total_reports: number;
  description?: string;
  metadata: Record<string, unknown>;
}

export interface GIMIdentityCreate {
  description?: string;
  metadata?: Record<string, unknown>;
}

export interface TokenRequest {
  gim_id: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface JWTClaims {
  sub: string;
  iss: string;
  aud: string;
  exp: number;
  iat: number;
  gim_identity_id: string;
}

export interface RevokeRequest {
  gim_id: string;
}

export interface GIMIdentityResponse {
  gim_id: string;
  created_at: string;
  description?: string;
}

export interface ErrorResponse {
  error: string;
  error_description: string;
}

export interface RateLimitInfo {
  daily_limit: number;
  daily_used: number;
  remaining: number;
  reset_at?: string;
}
