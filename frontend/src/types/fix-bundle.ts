/**
 * TypeScript types mirroring /gim/src/models/fix_bundle.py
 */

export type EnvActionType = "install" | "upgrade" | "downgrade" | "config" | "flag" | "command";

export interface EnvAction {
  order: number;
  type: EnvActionType;
  command: string;
  explanation: string;
}

export interface Constraints {
  working_versions: Record<string, string>;
  incompatible_with: string[];
  required_environment: string[];
}

export interface VerificationStep {
  order: number;
  command: string;
  expected_output: string;
}

export interface FixBundleCreate {
  summary: string;
  fix_steps: string[];
  code_changes: CodeChange[];
  env_actions: EnvAction[];
  constraints: Constraints;
  verification: VerificationStep[];
  patch_diff?: string;
  code_fix?: string;
}

export interface CodeChange {
  file_path: string;
  change_type: "add" | "modify" | "delete";
  before?: string;
  after?: string;
  explanation?: string;
}

export interface FixBundle extends FixBundleCreate {
  id: string;
  master_issue_id: string;
  version: number;
  is_current: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Action type display configuration
 */
export const ACTION_TYPE_DISPLAY: Record<EnvActionType, { label: string; icon: string }> = {
  install: { label: "Install", icon: "download" },
  upgrade: { label: "Upgrade", icon: "arrow-up" },
  downgrade: { label: "Downgrade", icon: "arrow-down" },
  config: { label: "Configure", icon: "settings" },
  flag: { label: "Flag", icon: "flag" },
  command: { label: "Run", icon: "terminal" },
};
