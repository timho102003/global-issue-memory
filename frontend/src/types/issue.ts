/**
 * TypeScript types mirroring /gim/src/models/issue.py
 */

export type IssueStatus = "active" | "superseded" | "invalid";

export type ContributionType = "environment" | "symptom" | "model_quirk" | "validation";

export type RootCauseCategory =
  | "environment"
  | "model_behavior"
  | "api_integration"
  | "code_generation"
  | "framework_specific";

export interface MasterIssue {
  id: string;
  canonical_title: string;
  description: string;
  root_cause_category: RootCauseCategory;
  root_cause_subcategory?: string;
  confidence_score: number;
  child_issue_count: number;
  environment_coverage: string[];
  verification_count: number;
  last_confirmed_at?: string;
  status: IssueStatus;
  created_at: string;
  updated_at: string;
  model_provider?: string;
  language?: string;
  framework?: string;
}

export interface MasterIssueCreate {
  canonical_title: string;
  description: string;
  root_cause_category: RootCauseCategory;
  root_cause_subcategory?: string;
}

export interface ChildIssueCreate {
  master_issue_id: string;
  contribution_type: ContributionType;
  sanitized_error: string;
  sanitized_context?: string;
  sanitized_mre?: string;
  environment: Record<string, unknown>;
  model_provider: string;
  model_name: string;
  model_version?: string;
  model_behavior_notes: string[];
  validation_success?: boolean;
  validation_notes?: string;
}

export interface ChildIssue extends ChildIssueCreate {
  id: string;
  created_at: string;
}

/**
 * Category display configuration
 */
export const CATEGORY_DISPLAY: Record<RootCauseCategory, { label: string; color: string }> = {
  environment: { label: "Environment", color: "cat-environment" },
  model_behavior: { label: "Model", color: "cat-model" },
  api_integration: { label: "API", color: "cat-api" },
  code_generation: { label: "Codegen", color: "cat-codegen" },
  framework_specific: { label: "Framework", color: "cat-framework" },
};

/**
 * Status display configuration
 */
export const STATUS_DISPLAY: Record<IssueStatus, { label: string; variant: "success" | "warning" | "error" }> = {
  active: { label: "Verified", variant: "success" },
  superseded: { label: "Pending", variant: "warning" },
  invalid: { label: "Declined", variant: "error" },
};
