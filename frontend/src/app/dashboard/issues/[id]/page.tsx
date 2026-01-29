"use client";

import { use } from "react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CodeBlock } from "@/components/ui/code-block";
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbSeparator,
  BreadcrumbPage,
} from "@/components/ui/breadcrumb";
import { FixBundleCard } from "@/components/issue/fix-bundle-card";
import { TrustSignals } from "@/components/issue/trust-signals";
import { useIssue, useFixBundle } from "@/lib/hooks/use-issues";
import { CATEGORY_DISPLAY } from "@/types";
import type { RootCauseCategory, FixBundle } from "@/types";

// Mock data for development
const mockIssue = {
  id: "1",
  canonical_title: "LangChain @tool decorator causing schema validation errors",
  description:
    "The @tool decorator in LangChain fails to generate valid JSON schema for certain Python type hints, particularly when using Optional types or complex Pydantic models. This causes tool calling to fail with schema validation errors.",
  root_cause_category: "api_integration" as RootCauseCategory,
  root_cause_subcategory: "Tool Calling",
  confidence_score: 0.92,
  child_issue_count: 24,
  environment_coverage: ["Claude 3", "GPT-4"],
  verification_count: 156,
  last_confirmed_at: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
  status: "active" as const,
  created_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3).toISOString(),
  updated_at: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
};

const mockFixBundle: FixBundle = {
  id: "fix-1",
  master_issue_id: "1",
  summary: "Use explicit args_schema parameter with Pydantic BaseModel instead of relying on type inference for complex types",
  fix_steps: [
    "Create a Pydantic BaseModel class for your tool arguments",
    "Pass the model as args_schema parameter to @tool decorator",
    "Remove Optional type hints from the function signature if using args_schema",
  ],
  code_changes: [],
  env_actions: [
    {
      order: 1,
      type: "upgrade",
      command: "pip install langchain>=0.1.0",
      explanation: "Upgrade to latest LangChain with fixed schema generation",
    },
    {
      order: 2,
      type: "config",
      command: 'export LANGCHAIN_TRACING_V2="false"',
      explanation: "Disable tracing to avoid schema conflicts",
    },
  ],
  constraints: {
    working_versions: {
      langchain: ">=0.1.0",
      python: ">=3.9",
    },
    incompatible_with: ["langchain<0.0.350"],
    required_environment: ["Python 3.9+"],
  },
  verification: [
    {
      order: 1,
      command: "python -c \"from langchain.tools import tool; print('OK')\"",
      expected_output: "OK",
    },
  ],
  code_fix: `from langchain.tools import tool
from typing import Optional

# Use explicit schema instead of type inference
@tool(args_schema=MyArgsSchema)
def my_tool(query: str) -> str:
    """Tool description here."""
    return f"Result: {query}"`,
  version: 2,
  is_current: true,
  created_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
  updated_at: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
};

const mockCodeExample = `from langchain.tools import tool
from typing import Optional
from pydantic import BaseModel

class QueryArgs(BaseModel):
    query: str
    limit: Optional[int] = 10

@tool
def search_docs(query: str, limit: Optional[int] = 10) -> str:
    """Search the documentation.

    Args:
        query: The search query
        limit: Max results to return
    """
    # This fails with schema validation error
    return f"Found {limit} results for: {query}"

# Error: Invalid schema generated for Optional[int]
# Expected: {"type": "integer"}
# Got: {"anyOf": [{"type": "integer"}, {"type": "null"}]}`;

/**
 * Issue Detail page matching GIM.pen design (qnZGX).
 */
export default function IssueDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { data: issue } = useIssue(id);
  const { data: fixBundle } = useFixBundle(id);

  // Use mock data if no real data
  const displayIssue = issue || mockIssue;
  const displayFixBundle = fixBundle || mockFixBundle;
  const categoryInfo = CATEGORY_DISPLAY[displayIssue.root_cause_category];

  return (
    <main className="flex flex-1 flex-col gap-6 py-6 sm:py-8">
      {/* Breadcrumbs */}
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink href="/dashboard/issues">Issues</BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator>/</BreadcrumbSeparator>
          <BreadcrumbItem>
            <BreadcrumbLink href={`/dashboard/issues?category=${displayIssue.root_cause_category}`}>
              {categoryInfo.label}
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator>/</BreadcrumbSeparator>
          <BreadcrumbItem>
            <BreadcrumbPage>{displayIssue.canonical_title}</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      {/* Content Row */}
      <div className="flex flex-1 flex-col gap-5 lg:flex-row lg:gap-6">
        {/* Left Column */}
        <div className="flex min-w-0 flex-1 flex-col gap-5">
          {/* Issue Card */}
          <Card>
            <CardHeader>
              <div className="flex items-start justify-between gap-4">
                <CardTitle className="text-lg leading-snug sm:text-xl">
                  {displayIssue.canonical_title}
                </CardTitle>
                <Badge
                  category={displayIssue.root_cause_category.replace("_", "-") as "environment" | "model" | "api" | "codegen" | "framework"}
                >
                  {categoryInfo.label}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed text-text-secondary">
                {displayIssue.description}
              </p>
            </CardContent>
          </Card>

          {/* Code Block */}
          <Card>
            <CardHeader>
              <CardTitle>Example Code</CardTitle>
            </CardHeader>
            <CardContent>
              <CodeBlock code={mockCodeExample} language="python" />
            </CardContent>
          </Card>

          {/* Trust Signals */}
          <TrustSignals
            verificationCount={displayIssue.verification_count}
            successRate={displayIssue.confidence_score}
            lastConfirmedAt={displayIssue.last_confirmed_at}
          />
        </div>

        {/* Right Column - Fix Bundle */}
        <div className="w-full lg:w-[380px]">
          <FixBundleCard fixBundle={displayFixBundle} />
        </div>
      </div>
    </main>
  );
}
