"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { CodeBlock } from "@/components/ui/code-block";

interface McpConfigCardProps {
  gimId: string;
  apiUrl?: string;
}

/**
 * MCP Configuration card with copyable config.
 */
export function McpConfigCard({ gimId, apiUrl = "http://localhost:8000" }: McpConfigCardProps) {
  const configCode = `{
  "mcpServers": {
    "gim": {
      "command": "uvx",
      "args": ["gim-mcp"],
      "env": {
        "GIM_ID": "${gimId}",
        "GIM_API_URL": "${apiUrl}"
      }
    }
  }
}`;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">MCP Configuration</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <p className="text-sm text-text-secondary">
          Add this to your Claude Desktop or MCP client configuration:
        </p>
        <CodeBlock code={configCode} language="json" />
        <p className="text-xs text-text-muted">
          This configuration enables GIM integration with your AI assistant.
        </p>
      </CardContent>
    </Card>
  );
}
