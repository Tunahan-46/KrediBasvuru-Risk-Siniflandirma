import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "KrediLens",
  description: "Kredi başvurularının risk gruplarına göre sınıflandırılması",
};

const pages = [
  { href: "/", label: "Ana sayfa" },
  { href: "/basvuru", label: "Yeni başvuru" },
  { href: "/gecmis", label: "Başvuru geçmişi" },
  { href: "/simulator", label: "Senaryo simülatörü" },
  { href: "/portfoy", label: "Portföy paneli" },
  { href: "/modeller", label: "Model karşılaştırma" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr">
      <body className="min-h-screen bg-slate-50 text-slate-900">
        <header className="border-b bg-white">
          <nav className="mx-auto flex max-w-5xl flex-wrap items-center gap-4 px-4 py-3 text-sm">
            <span className="mr-4 text-lg font-semibold">KrediLens</span>
            {pages.map((p) => (
              <Link key={p.href} href={p.href} className="text-slate-600 hover:text-slate-900">
                {p.label}
              </Link>
            ))}
          </nav>
        </header>
        <main className="mx-auto max-w-5xl px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
