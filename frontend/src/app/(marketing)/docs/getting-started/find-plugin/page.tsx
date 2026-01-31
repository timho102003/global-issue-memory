import type { Metadata } from "next";
import { DocsImage } from "@/components/docs/docs-image";

export const metadata: Metadata = {
  title: "Find Plugin",
};

export default function FindPluginPage() {
  return (
    <div>
      <h1 className="mb-3 text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
        Find the Plugin
      </h1>
      <p className="mb-6 text-[14px] leading-relaxed text-text-secondary sm:text-[15px]">
        Use the{" "}
        <code className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]">
          /plugin
        </code>{" "}
        command in Claude Code to browse available MCP servers and locate GIM.
      </p>

      <DocsImage
        src="/assets/find_plugin.jpg"
        alt="Finding the GIM plugin in Claude Code"
        width={860}
        height={480}
      />
    </div>
  );
}
