import type { Metadata } from "next";
import Link from "next/link";
import { LegalLayout } from "@/components/legal-layout";

export const metadata: Metadata = {
  title: "Terms of Service",
  description:
    "Terms of Service for HouseMatch — AI-powered property scoring and alerts.",
};

export default function TermsPage() {
  return (
    <LegalLayout title="Terms of Service" lastUpdated="April 2026">
      <p>
        These Terms of Service (&quot;Terms&quot;) govern your access to and use
        of the HouseMatch website and services (the &quot;Service&quot;) provided
        by HouseMatch Inc. (&quot;HouseMatch,&quot; &quot;we,&quot;
        &quot;our,&quot; or &quot;us&quot;). By creating an account or using the
        Service, you agree to be bound by these Terms.
      </p>

      <h2>1. Description of Service</h2>
      <p>
        HouseMatch provides AI-powered property scoring, personalized alerts,
        watchlist management, and underwriting tools for residential real estate
        in the Bay Area. The Service aggregates data from third-party listing
        sources and applies proprietary scoring algorithms to help users evaluate
        properties against their investment strategy.
      </p>

      <h2>2. Account Registration</h2>
      <p>
        To use certain features of the Service, you must create an account.
        Authentication is managed by Clerk, a third-party identity provider. You
        are responsible for maintaining the security of your account credentials
        and for all activities that occur under your account.
      </p>
      <ul>
        <li>You must provide accurate and complete registration information</li>
        <li>You must be at least 18 years of age</li>
        <li>
          You may not create accounts for others without their consent or
          maintain multiple accounts
        </li>
        <li>
          You must promptly notify us of any unauthorized use of your account
        </li>
      </ul>

      <h2>3. Subscriptions and Billing</h2>
      <p>
        HouseMatch offers Free, Pro, and Investor subscription tiers. Payment is
        processed by Stripe.
      </p>
      <ul>
        <li>
          <strong>Free tier</strong> — genuinely free with no hidden charges.
          Includes basic property browsing and scoring.
        </li>
        <li>
          <strong>Paid tiers</strong> — billed monthly or annually. Annual plans
          are billed upfront for the full year at a discounted rate.
        </li>
        <li>
          <strong>Cancellation</strong> — you may cancel your subscription at any
          time from Settings → Subscription. Your paid features remain active
          until the end of the current billing period, after which your account
          reverts to the Free tier.
        </li>
        <li>
          <strong>Refunds</strong> — we do not offer refunds for partial billing
          periods. If you cancel mid-month, you retain access through the end of
          that month.
        </li>
        <li>
          <strong>Price changes</strong> — we will notify you at least 30 days
          before any price increase takes effect.
        </li>
      </ul>

      <h2>4. Acceptable Use</h2>
      <p>You agree not to:</p>
      <ul>
        <li>
          Scrape, crawl, or use automated tools to extract data from the Service
          (except via the Investor API if included in your subscription)
        </li>
        <li>Resell, redistribute, or sublicense data obtained from the Service</li>
        <li>
          Interfere with or disrupt the Service, servers, or networks connected
          to the Service
        </li>
        <li>
          Use the Service for any unlawful purpose or in violation of any
          applicable local, state, national, or international law
        </li>
        <li>
          Impersonate any person or entity, or falsely state or misrepresent your
          affiliation with a person or entity
        </li>
        <li>
          Attempt to gain unauthorized access to any portion of the Service or
          any other systems or networks connected to the Service
        </li>
      </ul>

      <h2>5. Data Accuracy Disclaimer</h2>
      <p>
        Property data displayed on HouseMatch is sourced from third-party listing
        services including Redfin, Zillow, Realtor.com, and Craigslist. While we
        strive for accuracy, <strong>we do not guarantee</strong> the
        completeness, accuracy, or timeliness of any property information,
        scores, or estimates displayed on the Service.
      </p>
      <p>
        <strong>
          HouseMatch is not a substitute for professional real estate advice.
        </strong>{" "}
        Our property scores are algorithmic estimates and should not be the sole
        basis for any real estate investment decision. We recommend consulting
        with a licensed real estate agent, financial advisor, or attorney before
        making any purchase decisions.
      </p>

      <h2>6. Intellectual Property</h2>
      <ul>
        <li>
          Our scoring algorithms, user interface, code, and original content are
          the intellectual property of HouseMatch Inc. and are protected by
          copyright and trade secret law.
        </li>
        <li>
          Property listing data belongs to the respective listing services and
          public records sources.
        </li>
        <li>
          You retain ownership of any notes, preferences, and other content you
          create within the Service.
        </li>
      </ul>

      <h2>7. Limitation of Liability</h2>
      <p>
        To the maximum extent permitted by applicable law, HouseMatch and its
        officers, directors, employees, and agents shall not be liable for:
      </p>
      <ul>
        <li>
          Any indirect, incidental, special, consequential, or punitive damages
        </li>
        <li>
          Any loss of profits, data, use, goodwill, or other intangible losses
        </li>
        <li>
          Any investment decisions made based on property scores, estimates, or
          other information provided by the Service
        </li>
        <li>
          Any inaccuracies in property data sourced from third parties
        </li>
      </ul>
      <p>
        Our total liability for any claims arising under these Terms shall not
        exceed the amount you paid to HouseMatch in the 12 months preceding the
        claim.
      </p>

      <h2>8. Termination</h2>
      <p>
        We reserve the right to suspend or terminate your account if you violate
        these Terms or engage in conduct that we determine, in our sole
        discretion, to be harmful to the Service, other users, or third parties.
      </p>
      <p>
        Upon termination, your right to use the Service ceases immediately. We
        may delete your data in accordance with our{" "}
        <Link href="/privacy">Privacy Policy</Link>.
      </p>

      <h2>9. Governing Law</h2>
      <p>
        These Terms shall be governed by and construed in accordance with the
        laws of the State of California, without regard to its conflict of law
        provisions.
      </p>

      <h2>10. Dispute Resolution</h2>
      <p>
        Any dispute arising from these Terms or your use of the Service shall be
        resolved through binding arbitration administered by the American
        Arbitration Association (AAA) in San Francisco, California, in
        accordance with its Commercial Arbitration Rules.
      </p>
      <p>
        <strong>Opt-out</strong> — you may opt out of this arbitration provision
        by sending written notice to{" "}
        <a href="mailto:legal@housematch.io">legal@housematch.io</a> within 30
        days of creating your account.
      </p>

      <h2>11. Changes to These Terms</h2>
      <p>
        We may update these Terms from time to time. If we make material changes,
        we will notify you by email at least 30 days before the changes take
        effect. Your continued use of the Service after the effective date
        constitutes acceptance of the updated Terms.
      </p>

      <h2>12. Contact Us</h2>
      <p>
        If you have questions about these Terms, contact us at:
      </p>
      <ul>
        <li>
          Email: <a href="mailto:legal@housematch.io">legal@housematch.io</a>
        </li>
        <li>HouseMatch Inc., San Francisco, CA</li>
      </ul>
    </LegalLayout>
  );
}
