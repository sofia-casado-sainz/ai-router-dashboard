import Logo from "./Logo";

interface TopbarProps {
  onMenuClick: () => void;
  menuOpen: boolean;
}

/** Barra superior visible solo en móvil/tablet, con el botón que abre la sidebar. */
export default function Topbar({ onMenuClick, menuOpen }: TopbarProps) {
  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-white/[0.06] bg-zinc-950/80 px-4 backdrop-blur lg:hidden">
      <button
        type="button"
        onClick={onMenuClick}
        aria-label="Abrir menú"
        aria-controls="app-sidebar"
        aria-expanded={menuOpen}
        className="rounded-md p-1.5 text-zinc-400 hover:bg-white/[0.06] hover:text-white"
      >
        <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
          <path
            fillRule="evenodd"
            d="M2 4.75A.75.75 0 0 1 2.75 4h14.5a.75.75 0 0 1 0 1.5H2.75A.75.75 0 0 1 2 4.75ZM2 10a.75.75 0 0 1 .75-.75h14.5a.75.75 0 0 1 0 1.5H2.75A.75.75 0 0 1 2 10Zm0 5.25a.75.75 0 0 1 .75-.75h14.5a.75.75 0 0 1 0 1.5H2.75a.75.75 0 0 1-.75-.75Z"
            clipRule="evenodd"
          />
        </svg>
      </button>
      <Logo />
    </header>
  );
}
