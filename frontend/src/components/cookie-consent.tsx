"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Cookie, X } from "lucide-react";

const STORAGE_KEY = "hm_cookie_consent";

export function CookieConsent() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    // Only show if not already accepted
    const consent = localStorage.getItem(STORAGE_KEY);
    if (!consent) {
      // Small delay so it doesn't pop up instantly
      const timer = setTimeout(() => setVisible(true), 1500);
      return () => clearTimeout(timer);
    }
  }, []);

  const accept = () => {
    localStorage.setItem(STORAGE_KEY, "accepted");
    setVisible(false);
  };

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ y: 100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 100, opacity: 0 }}
          transition={{ type: "spring", damping: 25, stiffness: 300 }}
          className="fixed bottom-4 left-4 right-4 z-[60] sm:left-auto sm:right-6 sm:max-w-md"
        >
          <div className="rounded-xl border border-border/60 bg-card shadow-xl p-4">
            <div className="flex items-start gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-amber/10 text-amber-dark dark:text-amber">
                <Cookie className="h-4 w-4" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm leading-relaxed text-muted-foreground">
                  We use essential cookies to keep you signed in. No tracking, no
                  ads. Read our{" "}
                  <Link
                    href="/cookies"
                    className="text-foreground underline underline-offset-2 hover:text-amber-dark dark:hover:text-amber"
                  >
                    Cookie Policy
                  </Link>
                  .
                </p>
                <div className="mt-3 flex items-center gap-2">
                  <button
                    onClick={accept}
                    className="rounded-lg bg-amber px-4 py-1.5 text-sm font-medium text-amber-foreground hover:bg-amber-dark transition-colors cursor-pointer"
                  >
                    Got it
                  </button>
                </div>
              </div>
              <button
                onClick={accept}
                className="shrink-0 p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors cursor-pointer"
                aria-label="Dismiss"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
