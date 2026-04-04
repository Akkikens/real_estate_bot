import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";

interface LegalLayoutProps {
  title: string;
  lastUpdated: string;
  children: React.ReactNode;
}

export function LegalLayout({ title, lastUpdated, children }: LegalLayoutProps) {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 py-12 sm:py-20">
          <h1 className="font-[family-name:var(--font-heading)] text-3xl sm:text-4xl font-bold mb-2">
            {title}
          </h1>
          <p className="text-sm text-muted-foreground mb-10">
            Last updated: {lastUpdated}
          </p>
          <div className="prose prose-neutral dark:prose-invert max-w-none [&_h2]:font-[family-name:var(--font-heading)] [&_h2]:text-xl [&_h2]:font-semibold [&_h2]:mt-10 [&_h2]:mb-4 [&_h3]:text-base [&_h3]:font-semibold [&_h3]:mt-6 [&_h3]:mb-2 [&_p]:text-sm [&_p]:leading-relaxed [&_p]:text-muted-foreground [&_p]:mb-4 [&_li]:text-sm [&_li]:text-muted-foreground [&_li]:leading-relaxed [&_ul]:mb-4 [&_ol]:mb-4 [&_table]:text-sm [&_th]:text-left [&_th]:font-semibold [&_th]:p-2 [&_th]:border-b [&_th]:border-border [&_td]:p-2 [&_td]:border-b [&_td]:border-border/60 [&_td]:text-muted-foreground [&_a]:text-amber-dark [&_a]:dark:text-amber [&_a]:underline [&_a]:underline-offset-2">
            {children}
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
