import type { Metadata } from "next";
import Link from "next/link";
import { LegalLayout } from "@/components/legal-layout";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description:
    "Learn how HouseMatch collects, uses, and protects your personal information.",
};

export default function PrivacyPage() {
  return (
    <LegalLayout title="Privacy Policy" lastUpdated="April 2026">
      <p>
        HouseMatch Inc. (&quot;HouseMatch,&quot; &quot;we,&quot; &quot;our,&quot;
        or &quot;us&quot;) respects your privacy and is committed to protecting
        your personal information. This Privacy Policy explains how we collect,
        use, disclose, and safeguard your information when you use our website
        and services at housematch.io (the &quot;Service&quot;).
      </p>

      <h2>1. Information We Collect</h2>

      <h3>Information you provide directly</h3>
      <ul>
        <li>
          <strong>Account information</strong> — email address, name, and
          optionally phone number, provided when you create an account via Clerk
          authentication
        </li>
        <li>
          <strong>Property preferences</strong> — budget range, target cities,
          investment strategy, must-haves, and deal-breakers you set during
          onboarding
        </li>
        <li>
          <strong>Watchlist data</strong> — properties you save, notes you add,
          and pipeline stages you assign
        </li>
        <li>
          <strong>Payment information</strong> — processed and stored securely by
          Stripe. We never see or store your full credit card number.
        </li>
      </ul>

      <h3>Information collected automatically</h3>
      <ul>
        <li>
          <strong>Device and browser information</strong> — IP address, browser
          type, operating system, collected via standard web server logs
        </li>
        <li>
          <strong>Usage data</strong> — pages visited, searches performed,
          properties viewed, features used
        </li>
        <li>
          <strong>Cookies</strong> — essential session cookies managed by Clerk
          for authentication. See our{" "}
          <Link href="/cookies">Cookie Policy</Link> for details.
        </li>
      </ul>

      <h2>2. How We Use Your Information</h2>
      <p>We use the information we collect to:</p>
      <ul>
        <li>
          Provide personalized property scores tailored to your strategy and
          preferences
        </li>
        <li>
          Deliver daily alerts via SMS, WhatsApp, or email based on your settings
        </li>
        <li>Maintain and improve the Service</li>
        <li>Process subscription payments</li>
        <li>Send service-related communications (e.g., account verification, security alerts)</li>
        <li>Respond to support requests</li>
        <li>Analyze aggregate usage patterns to improve our scoring algorithms</li>
      </ul>

      <h2>3. How We Store and Protect Your Data</h2>
      <ul>
        <li>
          <strong>Database</strong> — Supabase PostgreSQL with encryption at rest
          (AES-256) hosted on AWS
        </li>
        <li>
          <strong>Authentication</strong> — Clerk (SOC 2 Type II certified)
          manages all passwords and session tokens. We never store passwords
          directly.
        </li>
        <li>
          <strong>Encryption in transit</strong> — all data transmitted via TLS
          1.3
        </li>
        <li>
          <strong>Payments</strong> — Stripe (PCI DSS Level 1) handles all
          payment processing
        </li>
      </ul>
      <p>
        For more details about our security practices, visit our{" "}
        <Link href="/security">Security</Link> page.
      </p>

      <h2>4. Data Sharing and Disclosure</h2>
      <p>
        <strong>We do not sell your personal information.</strong> We share data
        only with the following third-party service providers necessary to
        operate the Service:
      </p>
      <table>
        <thead>
          <tr>
            <th>Provider</th>
            <th>Purpose</th>
            <th>Data Shared</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Clerk</td>
            <td>Authentication</td>
            <td>Email, name, session data</td>
          </tr>
          <tr>
            <td>Stripe</td>
            <td>Payment processing</td>
            <td>Email, payment method</td>
          </tr>
          <tr>
            <td>Twilio</td>
            <td>SMS / WhatsApp alerts</td>
            <td>Phone number, alert content</td>
          </tr>
          <tr>
            <td>Supabase</td>
            <td>Database hosting</td>
            <td>All account and preference data</td>
          </tr>
          <tr>
            <td>Vercel</td>
            <td>Frontend hosting</td>
            <td>Standard web request logs</td>
          </tr>
        </tbody>
      </table>
      <p>
        We may also disclose information if required by law, subpoena, or court
        order, or to protect our rights, safety, or property.
      </p>

      <h2>5. Data Retention</h2>
      <ul>
        <li>
          <strong>Active accounts</strong> — your data is retained for as long as
          your account is active
        </li>
        <li>
          <strong>Deleted accounts</strong> — upon request, we delete your
          personal data within 30 days. Anonymized, aggregate usage data may be
          retained for analytics.
        </li>
        <li>
          <strong>Billing records</strong> — retained for 7 years as required by
          tax law
        </li>
      </ul>

      <h2>6. Your Rights Under CCPA (California Residents)</h2>
      <p>If you are a California resident, you have the right to:</p>
      <ul>
        <li>
          <strong>Know</strong> — request a copy of the personal information we
          hold about you
        </li>
        <li>
          <strong>Delete</strong> — request deletion of your personal information
        </li>
        <li>
          <strong>Opt-out of sale</strong> — we do not sell personal information,
          but you can submit a request to confirm this
        </li>
        <li>
          <strong>Non-discrimination</strong> — we will not discriminate against
          you for exercising these rights
        </li>
      </ul>
      <p>
        To exercise these rights, email{" "}
        <a href="mailto:privacy@housematch.io">privacy@housematch.io</a>.
      </p>

      <h2>7. Your Rights Under GDPR (EU/EEA Residents)</h2>
      <p>
        If you are located in the EU or EEA, you have additional rights under
        the General Data Protection Regulation:
      </p>
      <ul>
        <li>
          <strong>Access</strong> — obtain a copy of your personal data
        </li>
        <li>
          <strong>Rectification</strong> — correct inaccurate personal data
        </li>
        <li>
          <strong>Erasure</strong> — request deletion of your personal data
          (&quot;right to be forgotten&quot;)
        </li>
        <li>
          <strong>Portability</strong> — receive your data in a structured,
          machine-readable format
        </li>
        <li>
          <strong>Restrict processing</strong> — limit how we process your data
        </li>
        <li>
          <strong>Object</strong> — object to processing based on legitimate
          interests
        </li>
      </ul>
      <p>
        Our legal basis for processing is (a) contract performance (providing the
        Service you signed up for) and (b) legitimate interest (improving the
        Service).
      </p>

      <h2>8. Cookies</h2>
      <p>
        We use only essential cookies required for authentication and basic
        functionality. We do not use advertising, tracking, or analytics cookies.
        See our <Link href="/cookies">Cookie Policy</Link> for a complete list.
      </p>

      <h2>9. Children&apos;s Privacy</h2>
      <p>
        The Service is not directed at individuals under 18 years of age. We do
        not knowingly collect personal information from children. If you believe
        we have collected data from a minor, please contact us at{" "}
        <a href="mailto:privacy@housematch.io">privacy@housematch.io</a> and we
        will promptly delete it.
      </p>

      <h2>10. Changes to This Policy</h2>
      <p>
        We may update this Privacy Policy from time to time. If we make material
        changes, we will notify you by email (sent to the address associated with
        your account) at least 30 days before the changes take effect. Your
        continued use of the Service after the effective date constitutes
        acceptance of the updated policy.
      </p>

      <h2>11. Contact Us</h2>
      <p>
        If you have questions about this Privacy Policy or wish to exercise your
        data rights, contact us at:
      </p>
      <ul>
        <li>
          Email:{" "}
          <a href="mailto:privacy@housematch.io">privacy@housematch.io</a>
        </li>
        <li>HouseMatch Inc., San Francisco, CA</li>
      </ul>
    </LegalLayout>
  );
}
