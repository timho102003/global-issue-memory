import type { Metadata } from "next";
import { CodeBlock } from "@/components/ui/code-block";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { DocsImage } from "@/components/docs/docs-image";
import { DocsStep } from "@/components/docs/docs-step";
import { DocsCallout } from "@/components/docs/docs-callout";

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
        Connect GIM to your preferred AI coding assistant. Choose your platform
        below.
      </p>

      <Tabs defaultValue="cursor">
        <TabsList>
          <TabsTrigger value="cursor">Cursor</TabsTrigger>
          <TabsTrigger value="cli">Claude Code CLI</TabsTrigger>
          <TabsTrigger value="manual">Manual Config</TabsTrigger>
        </TabsList>

        {/* Cursor Tab */}
        <TabsContent value="cursor">
          <div className="space-y-6">
            <DocsCallout variant="tip" title="Cursor MCP Support">
              Cursor supports MCP servers natively. Follow these steps to add
              GIM directly in Cursor&apos;s settings.
            </DocsCallout>

            {/* Step 1 */}
            <div>
              <DocsStep number="1" title="Open Cursor Settings" />
              <p className="mb-4 text-[13px] leading-relaxed text-text-secondary sm:text-[14px]">
                Open Cursor and navigate to{" "}
                <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">
                  Settings
                </code>{" "}
                → <strong>Tools & MCP</strong> in the left sidebar.
              </p>
            </div>

            {/* Step 2 */}
            <div>
              <DocsStep number="2" title="Add New MCP Server" />
              <p className="mb-4 text-[13px] leading-relaxed text-text-secondary sm:text-[14px]">
                Click the{" "}
                <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">
                  + New MCP Server
                </code>{" "}
                button at the bottom of the Installed MCP Servers section.
              </p>
              <DocsImage
                src="/assets/cursor_mcp_installation.png"
                alt="Cursor MCP Settings showing the Tools & MCP panel with installed servers and the New MCP Server button"
                width={932}
                height={558}
                className="mb-4"
                maxWidth="max-w-[700px]"
              />
            </div>

            {/* Step 3 */}
            <div>
              <DocsStep number="3" title="Configure the Server" />
              <p className="mb-3 text-[13px] leading-relaxed text-text-secondary sm:text-[14px]">
                When prompted, paste the following JSON configuration:
              </p>
              <CodeBlock
                code={`{
  "mcpServers": {
    "global-issue-memory": {
      "url": "https://mcp.usegim.com"
    }
  }
}`}
                language="json"
              />
            </div>

            {/* Step 4 */}
            <div>
              <DocsStep number="4" title="Verify Installation" />
              <p className="text-[13px] leading-relaxed text-text-secondary sm:text-[14px]">
                Once added, you should see{" "}
                <strong className="text-text-primary">
                  global-issue-memory
                </strong>{" "}
                listed with its tools:{" "}
                <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[11px]">
                  gim_search_issues
                </code>
                ,{" "}
                <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[11px]">
                  gim_get_fix_bundle
                </code>
                ,{" "}
                <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[11px]">
                  gim_submit_issue
                </code>
                ,{" "}
                <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[11px]">
                  gim_confirm_fix
                </code>
                , and{" "}
                <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[11px]">
                  gim_report_usage
                </code>
                . Toggle the switch to enable it.
              </p>
            </div>
          </div>
        </TabsContent>

        {/* Claude Code CLI Tab */}
        <TabsContent value="cli">
          <p className="mb-3 text-[13px] text-text-secondary">
            Run the following command in your terminal to add GIM as an MCP
            server in Claude Code:
          </p>
          <CodeBlock
            code="claude mcp add --transport http global-issue-memory https://mcp.usegim.com"
            language="bash"
          />
        </TabsContent>

        {/* Manual Config Tab */}
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
      "url": "https://mcp.usegim.com"
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
