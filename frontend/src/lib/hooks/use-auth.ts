"use client";

import { useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/stores/auth-store";
import {
  createGimId,
  getToken,
  getRateLimit,
  signOut as apiSignOut,
  isValidGimId,
} from "@/lib/api/auth";
import { removeAuthToken } from "@/lib/api/client";

/**
 * Hook for authentication operations.
 */
export function useAuth() {
  const queryClient = useQueryClient();
  const {
    gimId,
    isAuthenticated,
    rateLimit,
    signIn: storeSignIn,
    signOut: storeSignOut,
    setRateLimit,
    setError,
    setLoading,
  } = useAuthStore();

  // Query for rate limit info (only when authenticated)
  const rateLimitQuery = useQuery({
    queryKey: ["rateLimit"],
    queryFn: getRateLimit,
    enabled: isAuthenticated,
    refetchInterval: 60000, // Refresh every minute
  });

  // Mutation for creating new GIM ID
  const createGimIdMutation = useMutation({
    mutationFn: createGimId,
    onSuccess: async (data) => {
      // Auto sign in after creating
      await signInMutation.mutateAsync(data.gim_id);
    },
    onError: (error: Error) => {
      setError(error.message);
    },
  });

  // Mutation for signing in with GIM ID
  const signInMutation = useMutation({
    mutationFn: async (gimId: string) => {
      if (!isValidGimId(gimId)) {
        throw new Error("Invalid GIM ID format");
      }
      setLoading(true);
      const response = await getToken(gimId);
      return { gimId, token: response };
    },
    onSuccess: ({ gimId }) => {
      storeSignIn(gimId);
      queryClient.invalidateQueries({ queryKey: ["rateLimit"] });
    },
    onError: (error: Error) => {
      setError(error.message);
    },
    onSettled: () => {
      setLoading(false);
    },
  });

  // Sign out function
  const signOut = () => {
    apiSignOut();
    removeAuthToken();
    storeSignOut();
    queryClient.clear();
  };

  // Update rate limit from query - use useEffect to avoid render-time state updates
  useEffect(() => {
    if (rateLimitQuery.data) {
      setRateLimit(rateLimitQuery.data);
    }
  }, [rateLimitQuery.data, setRateLimit]);

  return {
    gimId,
    isAuthenticated,
    rateLimit: rateLimitQuery.data || rateLimit,
    isLoading: signInMutation.isPending || createGimIdMutation.isPending,
    error: signInMutation.error?.message || createGimIdMutation.error?.message,
    signIn: signInMutation.mutate,
    signInAsync: signInMutation.mutateAsync,
    createGimId: createGimIdMutation.mutate,
    createGimIdAsync: createGimIdMutation.mutateAsync,
    signOut,
    isValidGimId,
  };
}
