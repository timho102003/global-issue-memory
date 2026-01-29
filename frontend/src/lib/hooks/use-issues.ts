"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  searchIssues,
  getIssue,
  getFixBundle,
  submitIssue,
  confirmFix,
  getDashboardStats,
  getProfileStats,
  type IssueSearchParams,
} from "@/lib/api/issues";
import type { ChildIssueCreate } from "@/types";

/**
 * Hook for searching issues with pagination.
 *
 * @param params - Search parameters
 * @returns Query result
 */
export function useIssueSearch(params: IssueSearchParams) {
  return useQuery({
    queryKey: ["issues", "search", params],
    queryFn: () => searchIssues(params),
    staleTime: 30000, // 30 seconds
  });
}

/**
 * Hook for getting a single issue.
 *
 * @param issueId - Issue UUID
 * @returns Query result
 */
export function useIssue(issueId: string | undefined) {
  return useQuery({
    queryKey: ["issues", issueId],
    queryFn: () => getIssue(issueId!),
    enabled: !!issueId,
  });
}

/**
 * Hook for getting fix bundle for an issue.
 *
 * @param issueId - Issue UUID
 * @returns Query result
 */
export function useFixBundle(issueId: string | undefined) {
  return useQuery({
    queryKey: ["fixBundles", issueId],
    queryFn: () => getFixBundle(issueId!),
    enabled: !!issueId,
  });
}

/**
 * Hook for submitting an issue.
 *
 * @returns Mutation result
 */
export function useSubmitIssue() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ChildIssueCreate) => submitIssue(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["issues"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

/**
 * Hook for confirming a fix.
 *
 * @returns Mutation result
 */
export function useConfirmFix() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      issueId,
      fixBundleId,
      success,
      notes,
    }: {
      issueId: string;
      fixBundleId: string;
      success: boolean;
      notes?: string;
    }) => confirmFix(issueId, fixBundleId, success, notes),
    onSuccess: (_, { issueId }) => {
      queryClient.invalidateQueries({ queryKey: ["issues", issueId] });
      queryClient.invalidateQueries({ queryKey: ["fixBundles", issueId] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

/**
 * Hook for dashboard statistics.
 *
 * @returns Query result
 */
export function useDashboardStats() {
  return useQuery({
    queryKey: ["dashboard", "stats"],
    queryFn: getDashboardStats,
    staleTime: 60000, // 1 minute
  });
}

/**
 * Hook for profile statistics.
 *
 * @param gimId - The GIM ID
 * @returns Query result
 */
export function useProfileStats(gimId: string | null) {
  return useQuery({
    queryKey: ["profile", "stats", gimId],
    queryFn: () => getProfileStats(gimId!),
    enabled: !!gimId,
    staleTime: 60000, // 1 minute
  });
}
