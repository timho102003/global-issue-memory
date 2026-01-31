import type { Metadata } from "next";
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@/components/ui/accordion";

export const metadata: Metadata = {
  title: "Troubleshooting",
};

const faqs = [
  {
    id: "not-found",
    question: "GIM server not showing up after installation",
    answer:
      "Make sure you've restarted Claude Code after adding the MCP server. You can verify the server is registered by running `claude mcp list` in your terminal.",
  },
  {
    id: "auth-fail",
    question: "Authentication fails or times out",
    answer:
      "Check your internet connection and try again. If the OAuth window doesn't open, copy the URL from the terminal and paste it in your browser manually. Ensure pop-ups are not blocked.",
  },
  {
    id: "no-results",
    question: "gim_search_issues returns no results",
    answer:
      "GIM's knowledge base grows with community contributions. If no match is found, solve the issue yourself and submit it with `gim_submit_issue` so future developers benefit.",
  },
  {
    id: "permission",
    question: "Permission denied when calling GIM tools",
    answer:
      "Your GIM session may have expired. Re-authenticate by triggering any GIM tool — the OAuth flow will automatically start again.",
  },
];

export default function TroubleshootingPage() {
  return (
    <div>
      <h1 className="mb-3 text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
        Troubleshooting
      </h1>
      <p className="mb-8 text-[14px] leading-relaxed text-text-secondary sm:text-[15px]">
        Common issues and their solutions. If you don&apos;t find what you&apos;re
        looking for, reach out on GitHub.
      </p>

      <Accordion type="single">
        {faqs.map((faq) => (
          <AccordionItem key={faq.id} value={faq.id}>
            <AccordionTrigger value={faq.id}>{faq.question}</AccordionTrigger>
            <AccordionContent value={faq.id}>
              {faq.answer.split("`").map((part, i) =>
                i % 2 === 1 ? (
                  <code
                    key={i}
                    className="rounded bg-bg-tertiary px-1.5 py-0.5 font-mono text-[12px]"
                  >
                    {part}
                  </code>
                ) : (
                  <span key={i}>{part}</span>
                )
              )}
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </div>
  );
}
