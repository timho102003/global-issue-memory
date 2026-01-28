import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { GIMIdentityResponse, RateLimitInfo } from "@/types";

/**
 * Auth state interface.
 */
interface AuthState {
  gimId: string | null;
  isAuthenticated: boolean;
  identity: GIMIdentityResponse | null;
  rateLimit: RateLimitInfo | null;
  isLoading: boolean;
  error: string | null;
}

/**
 * Auth actions interface.
 */
interface AuthActions {
  setGimId: (gimId: string) => void;
  setIdentity: (identity: GIMIdentityResponse) => void;
  setRateLimit: (rateLimit: RateLimitInfo) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  signIn: (gimId: string) => void;
  signOut: () => void;
  reset: () => void;
}

const initialState: AuthState = {
  gimId: null,
  isAuthenticated: false,
  identity: null,
  rateLimit: null,
  isLoading: false,
  error: null,
};

/**
 * Auth store with persistence.
 */
export const useAuthStore = create<AuthState & AuthActions>()(
  persist(
    (set) => ({
      ...initialState,

      setGimId: (gimId) => set({ gimId }),

      setIdentity: (identity) => set({ identity }),

      setRateLimit: (rateLimit) => set({ rateLimit }),

      setLoading: (isLoading) => set({ isLoading }),

      setError: (error) => set({ error }),

      signIn: (gimId) =>
        set({
          gimId,
          isAuthenticated: true,
          error: null,
        }),

      signOut: () =>
        set({
          gimId: null,
          isAuthenticated: false,
          identity: null,
          rateLimit: null,
          error: null,
        }),

      reset: () => set(initialState),
    }),
    {
      name: "gim-auth-storage",
      partialize: (state) => ({
        gimId: state.gimId,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
