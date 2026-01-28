import { z } from "zod";

const API_BASE_URL = process.env.NEXT_PUBLIC_GIM_API_URL || "http://localhost:8000";

/**
 * Custom error class for API errors.
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Get the auth token from localStorage.
 *
 * @returns JWT token or null
 */
function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("gim_token");
}

/**
 * Set the auth token in localStorage.
 *
 * @param token - JWT token to store
 */
export function setAuthToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem("gim_token", token);
}

/**
 * Remove the auth token from localStorage.
 */
export function removeAuthToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem("gim_token");
}

/**
 * Base fetch wrapper with auth and error handling.
 *
 * @param endpoint - API endpoint path
 * @param options - Fetch options
 * @returns Response data
 */
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAuthToken();

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      errorData.error_description || errorData.detail || "An error occurred",
      response.status,
      errorData.error
    );
  }

  return response.json();
}

/**
 * API client methods.
 */
export const api = {
  /**
   * GET request.
   *
   * @param endpoint - API endpoint
   * @returns Response data
   */
  get: <T>(endpoint: string) => apiFetch<T>(endpoint, { method: "GET" }),

  /**
   * POST request.
   *
   * @param endpoint - API endpoint
   * @param data - Request body
   * @returns Response data
   */
  post: <T>(endpoint: string, data?: unknown) =>
    apiFetch<T>(endpoint, {
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    }),

  /**
   * PUT request.
   *
   * @param endpoint - API endpoint
   * @param data - Request body
   * @returns Response data
   */
  put: <T>(endpoint: string, data?: unknown) =>
    apiFetch<T>(endpoint, {
      method: "PUT",
      body: data ? JSON.stringify(data) : undefined,
    }),

  /**
   * DELETE request.
   *
   * @param endpoint - API endpoint
   * @returns Response data
   */
  delete: <T>(endpoint: string) => apiFetch<T>(endpoint, { method: "DELETE" }),
};

/**
 * Validate API response with Zod schema.
 *
 * @param schema - Zod schema
 * @param data - Data to validate
 * @returns Validated data
 */
export function validateResponse<T>(schema: z.ZodSchema<T>, data: unknown): T {
  return schema.parse(data);
}
