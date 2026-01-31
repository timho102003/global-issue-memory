import type { Metadata } from "next";
import { DocsImage } from "@/components/docs/docs-image";
import { DocsCallout } from "@/components/docs/docs-callout";

export const metadata: Metadata = {
  title: "Authentication",
};

export default function AuthenticationPage() {
  return (
    <div>
      <h1 className="mb-3 text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
        Authentication
      </h1>
      <p className="mb-8 text-[14px] leading-relaxed text-text-secondary sm:text-[15px]">
        GIM uses a secure OAuth 2.1 flow for authentication. When you first use
        a GIM tool, you&apos;ll be guided through the process automatically.
      </p>

      {/* Step 1: Trigger Auth */}
      <h2 className="mb-3 text-lg font-semibold text-text-primary">
        1. Trigger Authentication
      </h2>
      <p className="mb-4 text-[14px] leading-relaxed text-text-secondary sm:text-[15px]">
        When you first use a GIM tool, you&apos;ll be prompted to authenticate.
        Click the link provided in your terminal to begin the OAuth flow.
      </p>
      <div className="mb-8">
        <DocsImage
          src="/assets/authentication.jpg"
          alt="GIM authentication prompt"
          width={520}
          height={290}
          centered
        />
      </div>

      {/* Step 2: Authorize */}
      <h2 className="mb-3 text-lg font-semibold text-text-primary">
        2. Authorize via OAuth
      </h2>
      <p className="mb-4 text-[14px] leading-relaxed text-text-secondary sm:text-[15px]">
        Authorize GIM to access your account. This uses a secure OAuth 2.1
        flow — your credentials are never stored by GIM.
      </p>
      <div className="mb-8">
        <DocsImage
          src="/assets/oauth.jpg"
          alt="OAuth authorization screen"
          width={520}
          height={290}
          centered
        />
      </div>

      {/* Step 3: Confirm */}
      <h2 className="mb-3 text-lg font-semibold text-text-primary">
        3. Confirm Success
      </h2>
      <p className="mb-4 text-[14px] leading-relaxed text-text-secondary sm:text-[15px]">
        You&apos;ll see a success message confirming your authentication. GIM is
        now ready to use.
      </p>
      <div className="mb-8">
        <DocsImage
          src="/assets/auth_success.jpg"
          alt="Authentication success confirmation"
          width={520}
          height={290}
          centered
        />
      </div>

      <DocsCallout variant="info" title="Session expiry">
        If your session expires, re-authenticate by triggering any GIM
        tool — the OAuth flow will automatically start again.
      </DocsCallout>
    </div>
  );
}
