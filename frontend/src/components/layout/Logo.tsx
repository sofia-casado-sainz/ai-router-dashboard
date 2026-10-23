import Link from "next/link";

export default function Logo() {
  return (
    <Link href="/playground" className="flex items-center gap-2.5">
      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-linear-to-br from-indigo-500 to-violet-600 text-sm font-bold text-white shadow-lg shadow-indigo-500/20">
        AR
      </span>
      <span className="text-sm font-semibold tracking-tight text-white">
        AI Router
      </span>
    </Link>
  );
}
