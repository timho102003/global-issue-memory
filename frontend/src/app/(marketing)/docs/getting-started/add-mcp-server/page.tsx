import type { Metadata } from "next";
import { CodeBlock } from "@/components/ui/code-block";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";

export const metadata: Metadata = {
  title: "Add MCP Server",
};

export default function AddMcpServerPage() {
  return (
    <div>
      <h1 className="mb-3 text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
        Add GIM MCP Server
      </h1>
      <p className="mb-6 text-[14px] leading-relaxed text-text-secondary sm:text-[15px]">
        Run the following command in your terminal to add GIM as an MCP server
        in Claude Code.
      </p>

      <Tabs defaultValue="cli">
        <TabsList>
          <TabsTrigger value="cli">CLI Command</TabsTrigger>
          <TabsTrigger value="manual">Manual Config</TabsTrigger>
        </TabsList>
        <TabsContent value="cli">
          <CodeBlock
            code="claude mcp add --transport http global-issue-memory https://global-issue-memory-production.up.railway.app"
            language="bash"
          />
        </TabsContent>
        <TabsContent value="manual">
          <p className="mb-3 text-[13px] text-text-secondary">
            Add the following to your{" "}
            <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">
              claude_desktop_config.json
            </code>
            :
          </p>
          <CodeBlock
            code={`{
  "mcpServers": {
    "global-issue-memory": {
      "type": "http",
      "url": "https://global-issue-memory-production.up.railway.app"
    }
  }
}`}
            language="json"
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
