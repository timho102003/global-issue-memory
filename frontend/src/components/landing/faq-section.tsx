"use client";

import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@/components/ui/accordion";

/**
 * FAQ section with centered accordion and responsive container.
 */
export function FaqSection() {
  const faqs = [
    {
      question: "Is GIM free to use?",
      answer:
        "Yes! GIM is open source and free forever. We believe shared knowledge should be accessible to everyone. You can use it for personal projects, work, or anything else.",
    },
    {
      question: "What data does GIM collect?",
      answer:
        "GIM only collects anonymized error patterns and their solutions. Your actual code, project files, and personal information never leave your machine. We take privacy seriously.",
    },
    {
      question: "How does fix verification work?",
      answer:
        "When developers confirm a fix worked for them, it adds to the verification count. Fixes with more verifications and higher success rates rank higher in search results.",
    },
    {
      question: "Which AI providers are supported?",
      answer:
        "GIM works with any AI provider that supports MCP (Model Context Protocol), including Claude, GPT-4, Gemini, and others. If your AI tool supports MCP, GIM works with it.",
    },
    {
      question: "Can I use GIM offline?",
      answer:
        "The core search functionality requires internet connection to access the global database. However, you can cache frequently used fixes locally for offline access.",
    },
    {
      question: "How can I contribute?",
      answer:
        "Just use GIM! When you solve a new issue and share the fix, you're contributing. You can also star us on GitHub, report bugs, or submit pull requests to improve the codebase.",
    },
  ];

  return (
    <section
      id="faq"
      className="bg-bg-tertiary px-5 py-16 sm:px-8 sm:py-20 md:py-24 lg:px-12"
    >
      <div className="mx-auto flex max-w-[1200px] flex-col items-center gap-12 md:gap-14">
        {/* Header */}
        <div className="flex flex-col items-center gap-3">
          <span className="text-[11px] font-semibold tracking-[2px] text-accent-warm uppercase">
            Common Questions
          </span>
          <h2 className="text-center text-2xl font-bold tracking-tight text-text-primary sm:text-3xl md:text-4xl lg:text-[44px] lg:leading-[1.15]">
            Have Questions? We&apos;re Here to Help.
          </h2>
        </div>

        {/* FAQ Accordion */}
        <div className="w-full max-w-[760px]">
          <Accordion type="single">
            {faqs.map((faq, index) => (
              <AccordionItem key={index} value={`faq-${index}`}>
                <AccordionTrigger value={`faq-${index}`}>
                  {faq.question}
                </AccordionTrigger>
                <AccordionContent value={`faq-${index}`}>
                  {faq.answer}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </div>
    </section>
  );
}
