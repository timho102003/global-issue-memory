import { api } from "./client";
import type { MasterIssue, ChildIssueCreate, ChildIssue } from "@/types";
import type { FixBundle } from "@/types";

/**
 * Search parameters for issues.
 */
export interface IssueSearchParams {
  query?: string;
  category?: string;
  status?: string;
  provider?: string;
  time_range?: "7d" | "30d" | "90d";
  limit?: number;
  offset?: number;
}

/**
 * Search response with pagination.
 */
export interface IssueSearchResponse {
  issues: MasterIssue[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * Search issues via MCP tool endpoint.
 *
 * @param params - Search parameters
 * @returns Search results with pagination
 */
export async function searchIssues(
  params: IssueSearchParams
): Promise<IssueSearchResponse> {
  return api.post<IssueSearchResponse>("/mcp/tools/gim_search_issues", {
    arguments: params,
  });
}

/**
 * Get a single issue by ID.
 *
 * @param issueId - Issue UUID
 * @returns Master issue details
 */
export async function getIssue(issueId: string): Promise<MasterIssue> {
  return api.get<MasterIssue>(`/issues/${issueId}`);
}

/**
 * Get fix bundle for an issue.
 *
 * @param issueId - Issue UUID
 * @returns Current fix bundle or null if not found
 */
export async function getFixBundle(issueId: string): Promise<FixBundle | null> {
  const response = await api.post<{ content: FixBundle[] }>(
    "/mcp/tools/gim_get_fix_bundle",
    { arguments: { issue_id: issueId } }
  );
  return response.content[0] ?? null;
}

/**
 * Submit a new issue contribution.
 *
 * @param data - Child issue data
 * @returns Created child issue
 */
export async function submitIssue(data: ChildIssueCreate): Promise<ChildIssue> {
  return api.post<ChildIssue>("/mcp/tools/gim_submit_issue", {
    arguments: data,
  });
}

/**
 * Confirm a fix worked.
 *
 * @param issueId - Issue UUID
 * @param fixBundleId - Fix bundle UUID
 * @param success - Whether fix was successful
 * @param notes - Optional notes
 * @returns Confirmation result
 */
export async function confirmFix(
  issueId: string,
  fixBundleId: string,
  success: boolean,
  notes?: string
): Promise<{ confirmed: boolean }> {
  return api.post<{ confirmed: boolean }>("/mcp/tools/gim_confirm_fix", {
    arguments: {
      issue_id: issueId,
      fix_bundle_id: fixBundleId,
      success,
      notes,
    },
  });
}

/**
 * Get dashboard statistics.
 *
 * @returns Dashboard stats
 */
export interface DashboardStats {
  total_issues: number;
  resolved_issues: number;
  unverified_issues: number;
  total_contributors: number;
  issues_by_category: Record<string, number>;
  issues_by_provider: Record<string, number>;
  recent_activity: ActivityItem[];
  issues_over_time: { date: string; count: number }[];
}

export interface ActivityItem {
  id: string;
  type: "submission" | "confirmation" | "update";
  issue_title: string;
  contributor?: string;
  timestamp: string;
}

export async function getDashboardStats(): Promise<DashboardStats> {
  return api.get<DashboardStats>("/dashboard/stats");
}

/**
 * Profile statistics for a user.
 */
export interface ProfileStats {
  total_searches: number;
  total_submissions: number;
  total_confirmations: number;
  total_reports: number;
  contributions: { date: string; count: number }[];
  rate_limit: {
    daily_searches_used: number;
    daily_searches_limit: number;
  };
}

/**
 * Get profile statistics for a GIM ID.
 *
 * @param gimId - The GIM ID
 * @returns Profile stats
 */
export async function getProfileStats(gimId: string): Promise<ProfileStats> {
  return api.get<ProfileStats>(`/profile/stats/${gimId}`);
}
