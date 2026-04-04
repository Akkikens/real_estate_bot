import type { Metadata } from "next";
import Link from "next/link";
import { LegalLayout } from "@/components/legal-layout";

export const metadata: Metadata = {
  title: "Cookie Policy",
  description:
    "Learn about the cookies HouseMatch uses and how they work.",
};

export default function CookiesPage() {
  return (
    <LegalLayout title="Cookie Policy" lastUpdated="April 2026">
      <p>
        This Cookie Policy explains what cookies are, how HouseMatch Inc.
        (&quot;HouseMatch,&quot; &quot;we,&quot; &quot;our,&quot; or
        &quot;us&quot;) uses cookies on housematch.io, and your choices
        regarding cookies.
      </p>

      <h2>What Are Cookies?</h2>
      <p>
        Cookies are small text files stored on your device by your web browser.
        They are widely used to make websites work efficiently and to provide
        information to the website owner. We also use localStorage, a similar
        browser storage mechanism, for certain functional data.
      </p>

      <h2>Cookies We Use</h2>
      <p>
        We use <strong>only essential cookies</strong> required for the Service
        to function. We do not use advertising, analytics, or tracking cookies.
      </p>

      <table>
        <thead>
          <tr>
            <th>Cookie / Storage</th>
            <th>Provider</th>
            <th>Purpose</th>
            <th>Type</th>
            <th>Duration</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><code>__clerk_db_jwt</code></td>
            <td>Clerk</td>
            <td>Session authentication — keeps you signed in</td>
            <td>Essential</td>
            <td>Session</td>
          </tr>
          <tr>
            <td><code>__client_uat</code></td>
            <td>Clerk</td>
            <td>Session state management</td>
            <td>Essential</td>
            <td>Session</td>
          </tr>
          <tr>
            <td><code>hm_cookie_consent</code></td>
            <td>HouseMatch</td>
            <td>Remembers that you acknowledged the cookie banner</td>
            <td>Essential</td>
            <td>Persistent (localStorage)</td>
          </tr>
          <tr>
            <td><code>hm_onboard_progress</code></td>
            <td>HouseMatch</td>
            <td>
              Saves onboarding progress so you can resume if interrupted
            </td>
            <td>Functional</td>
            <td>30 days (localStorage)</td>
          </tr>
        </tbody>
      </table>

      <h2>Third-Party Cookies</h2>
      <p>
        Clerk (our authentication provider) sets essential session cookies to
        manage your login state. These cookies are strictly necessary for
        authentication and do not track you across other websites.
      </p>
      <p>We do not allow any other third parties to set cookies on our site.</p>

      <h2>Your Choices</h2>
      <p>
        Since we only use essential cookies, there is no cookie preference
        manager needed. However, you can control cookies through your browser
        settings:
      </p>
      <ul>
        <li>
          Most browsers allow you to block or delete cookies in their settings.
          Note that blocking essential cookies will prevent you from signing in
          to HouseMatch.
        </li>
        <li>
          You can clear localStorage data through your browser&apos;s developer
          tools or settings.
        </li>
      </ul>

      <h2>GDPR and Essential Cookies</h2>
      <p>
        Under the GDPR, essential cookies that are strictly necessary for the
        operation of a website do not require user consent. Our authentication
        cookies fall into this category. We display a cookie notice as a
        transparency measure, not because consent is legally required for our
        cookie usage.
      </p>

      <h2>Changes to This Policy</h2>
      <p>
        If we add any new cookies beyond what is listed here, we will update
        this policy and, if the cookies are non-essential, implement a consent
        mechanism before deploying them.
      </p>

      <h2>Contact Us</h2>
      <p>
        Questions about our cookie practices? Contact us at{" "}
        <a href="mailto:privacy@housematch.io">privacy@housematch.io</a>. See
        also our <Link href="/privacy">Privacy Policy</Link>.
      </p>
    </LegalLayout>
  );
}
