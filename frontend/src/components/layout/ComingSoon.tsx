interface ComingSoonProps {
  icon: string;
  message: string;
}

/** Placeholder para secciones que aún no tienen implementación. */
export default function ComingSoon({ icon, message }: ComingSoonProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-white/[0.08] bg-zinc-900/40 px-6 py-20 text-center">
      <span aria-hidden className="text-3xl">
        {icon}
      </span>
      <p className="mt-3 text-sm font-medium text-zinc-200">Próximamente</p>
      <p className="mt-1 max-w-sm text-sm text-zinc-500">{message}</p>
    </div>
  );
}
