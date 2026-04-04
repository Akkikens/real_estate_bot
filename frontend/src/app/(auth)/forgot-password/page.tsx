"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);

    // TODO: wire up to API
    await new Promise((r) => setTimeout(r, 1000));
    setSubmitted(true);
    setLoading(false);
  }

  return (
    <div className="rounded-2xl border border-border/60 bg-card p-8 shadow-xl">
      {/* Logo */}
      <div className="flex items-center gap-2.5 mb-8">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber text-amber-foreground font-bold text-sm">
          H
        </div>
        <span className="font-[family-name:var(--font-heading)] text-xl font-semibold">
          HouseMatch
        </span>
      </div>

      {submitted ? (
        <div className="text-center py-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-amber/10 mx-auto mb-4">
            <Mail className="h-6 w-6 text-amber-dark dark:text-amber" />
          </div>
          <h1 className="font-[family-name:var(--font-heading)] text-2xl font-bold mb-1">
            Check your email
          </h1>
          <p className="text-sm text-muted-foreground mb-6">
            If an account exists for <strong>{email}</strong>, we sent a password
            reset link.
          </p>
          <Link
            href="/login"
            className="text-sm text-amber-dark dark:text-amber font-medium hover:underline"
          >
            Back to Sign In
          </Link>
        </div>
      ) : (
        <>
          <h1 className="font-[family-name:var(--font-heading)] text-2xl font-bold mb-1">
            Reset your password
          </h1>
          <p className="text-sm text-muted-foreground mb-6">
            Enter your email and we&apos;ll send you a reset link.
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>

            <Button
              type="submit"
              className="w-full bg-amber text-amber-foreground hover:bg-amber-dark h-10"
              disabled={loading}
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <span className="h-4 w-4 border-2 border-amber-foreground/30 border-t-amber-foreground rounded-full animate-spin" />
                  Sending...
                </span>
              ) : (
                "Send Reset Link"
              )}
            </Button>
          </form>

          <p className="text-center text-sm text-muted-foreground mt-6">
            <Link
              href="/login"
              className="inline-flex items-center gap-1 text-amber-dark dark:text-amber font-medium hover:underline"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Back to Sign In
            </Link>
          </p>
        </>
      )}
    </div>
  );
}
