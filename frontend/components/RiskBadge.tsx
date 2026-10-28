import type { RiskGroup } from "@/lib/api";

const styles: Record<RiskGroup, string> = {
  Düşük: "bg-emerald-100 text-emerald-800 border-emerald-300",
  Orta: "bg-amber-100 text-amber-800 border-amber-300",
  Yüksek: "bg-rose-100 text-rose-800 border-rose-300",
};

export default function RiskBadge({ group, large = false }: { group: RiskGroup; large?: boolean }) {
  return (
    <span className={`inline-block rounded-full border font-medium ${styles[group]} ${large ? "px-4 py-1.5 text-lg" : "px-2 py-0.5 text-xs"}`}>
      {group} risk
    </span>
  );
}
