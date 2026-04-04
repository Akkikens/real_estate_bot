import type { Metadata } from "next";
import Link from "next/link";
import { LegalLayout } from "@/components/legal-layout";

export const metadata: Metadata = {
  title: "Data Processing Agreement",
  description:
    "HouseMatch Data Processing Agreement — sub-processors, data handling, and security commitments.",
};

export default function DpaPage() {
  return (
    <LegalLayout title="Data Processing Agreement" lastUpdated="April 2026">
      <p>
        This Data Processing Agreement (&quot;DPA&quot;) supplements our{" "}
        <Link href="/terms">Terms of Service</Link> and{" "}
        <Link href="/privacy">Privacy Policy</Link>. It outlines how HouseMatch
        Inc. (&quot;Processor&quot;) handles personal data on behalf of our
        users (&quot;Controllers&quot;) in compliance with GDPR, CCPA, and
        applicable data protection regulations.
      </p>

      <h2>1. Scope of Processing</h2>
      <p>
        HouseMatch processes personal data solely for the purpose of providing
        the Service as described in our Terms of Service. This includes:
      </p>
      <ul>
        <li>Authenticating users and managing sessions</li>
        <li>
          Storing and retrieving user preferences, watchlists, and scoring
          configurations
        </li>
        <li>
          Delivering personalized property alerts via email, SMS, or WhatsApp
        </li>
        <li>Processing subscription payments</li>
      </ul>

      <h3>Categories of data subjects</h3>
      <ul>
        <li>Registered users of the HouseMatch service</li>
      </ul>

      <h3>Types of personal data processed</h3>
      <ul>
        <li>Email address, name, phone number (optional)</li>
        <li>
          Property preferences (budget, target cities, strategy, must-haves)
        </li>
        <li>Watchlist data (saved properties, notes, pipeline stages)</li>
        <li>Usage data (pages viewed, searches, features used)</li>
        <li>
          Payment data (processed by Stripe — we do not store card numbers)
        </li>
      </ul>

      <h2>2. Sub-Processors</h2>
      <p>
        We use the following sub-processors. Each maintains industry-standard
        security certifications:
      </p>
      <table>
        <thead>
          <tr>
            <th>Sub-Processor</th>
            <th>Purpose</th>
            <th>Location</th>
            <th>Certification</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Clerk</td>
            <td>Authentication &amp; identity</td>
            <td>United States</td>
            <td>SOC 2 Type II</td>
          </tr>
          <tr>
            <td>Supabase (AWS)</td>
            <td>Database hosting</td>
            <td>US — us-east-1</td>
            <td>SOC 2 Type II</td>
          </tr>
          <tr>
            <td>Stripe</td>
            <td>Payment processing</td>
            <td>United States</td>
            <td>PCI DSS Level 1</td>
          </tr>
          <tr>
            <td>Twilio</td>
            <td>SMS / WhatsApp delivery</td>
            <td>United States</td>
            <td>SOC 2 Type II</td>
          </tr>
          <tr>
            <td>Vercel</td>
            <td>Frontend hosting &amp; CDN</td>
            <td>Global (edge)</td>
            <td>SOC 2 Type II</td>
          </tr>
        </tbody>
      </table>
      <p>
        We will notify users via email at least 30 days before adding a new
        sub-processor. Users may object to a new sub-processor by contacting{" "}
        <a href="mailto:privacy@housematch.io">privacy@housematch.io</a>.
      </p>

      <h2>3. Security Measures</h2>
      <ul>
        <li>
          All data encrypted in transit (TLS 1.3) and at rest (AES-256)
        </li>
        <li>Authentication managed by Clerk with session token rotation</li>
        <li>
          Role-based access controls — user data is isolated per account
        </li>
        <li>
          Regular security reviews and dependency updates
        </li>
        <li>
          Secrets managed via environment variables, excluded from version
          control
        </li>
      </ul>

      <h2>4. Data Breach Notification</h2>
      <p>
        In the event of a personal data breach, HouseMatch will:
      </p>
      <ul>
        <li>
          Notify affected users within <strong>72 hours</strong> of becoming
          aware of the breach, as required by GDPR Article 33
        </li>
        <li>
          Provide a description of the nature of the breach, categories of data
          affected, approximate number of records, and remedial measures taken
        </li>
        <li>
          Cooperate with affected users and relevant supervisory authorities
        </li>
      </ul>

      <h2>5. Data Deletion</h2>
      <p>
        Upon termination of service or user request, HouseMatch will delete all
        personal data within 30 days, except where retention is required by law
        (e.g., billing records retained for tax compliance).
      </p>

      <h2>6. Audit Rights</h2>
      <p>
        Enterprise customers (Investor tier and above) may request a summary of
        our security controls and practices. Contact{" "}
        <a href="mailto:security@housematch.io">security@housematch.io</a> to
        request our current security questionnaire or to discuss audit
        arrangements.
      </p>

      <h2>7. International Transfers</h2>
      <p>
        All data processing occurs within the United States. Our sub-processors
        (listed above) process data in the United States, with Vercel using a
        global edge network for frontend delivery (no personal data is stored at
        edge nodes).
      </p>
      <p>
        For EU/EEA users, data transfers to the US are governed by Standard
        Contractual Clauses (SCCs) maintained by our sub-processors.
      </p>

      <h2>8. Contact</h2>
      <p>
        For DPA-related inquiries, contact:
      </p>
      <ul>
        <li>
          Email:{" "}
          <a href="mailto:privacy@housematch.io">privacy@housematch.io</a>
        </li>
        <li>HouseMatch Inc., San Francisco, CA</li>
      </ul>

      <p>
        See also: <Link href="/privacy">Privacy Policy</Link> ·{" "}
        <Link href="/security">Security</Link> ·{" "}
        <Link href="/terms">Terms of Service</Link>
      </p>
    </LegalLayout>
  );
}
