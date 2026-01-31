import type { Metadata } from "next";
import { DocsImage } from "@/components/docs/docs-image";
import { DocsCallout } from "@/components/docs/docs-callout";

export const metadata: Metadata = {
  title: "Verify Installation",
};

export default function VerifyInstallationPage() {
  return (
    <div>
      <h1 className="mb-3 text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
        Verify Installation
      </h1>
      <p className="mb-6 text-[14px] leading-relaxed text-text-secondary sm:text-[15px]">
        After adding the server, verify it appears in your installed MCP servers
        list.
      </p>

      <DocsImage
        src="/assets/installed_mcp.jpg"
        alt="GIM shown in installed MCP servers"
        width={860}
        height={480}
      />

      <div className="mt-6">
        <DocsCallout variant="tip" title="Not seeing GIM?">
          Make sure you&apos;ve restarted Claude Code after adding the MCP
          server. You can verify the server is registered by running{" "}
          <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">
            claude mcp list
          </code>{" "}
          in your terminal.
        </DocsCallout>
      </div>
    </div>
  );
}
