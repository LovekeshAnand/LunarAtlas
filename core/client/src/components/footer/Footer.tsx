export default function Footer() {
  return (
    <footer className="border-t border-border-dark dark:border-[#222] bg-canvas dark:bg-[#0d0d0d] font-sans transition-colors duration-200">
      <div className="max-w-[1400px] mx-auto px-8 py-[14px] flex items-center justify-center gap-6">
        <span className="text-[11px] text-[#999] dark:text-[#555] tracking-[0.5px]">
          © 2026 LunarAtlas
        </span>
        <span className="text-border-dark dark:text-[#333]">|</span>
        <span className="text-[11px] text-ink-muted dark:text-[#404040] tracking-[0.5px]">
          Spectral Analysis System
        </span>
      </div>
    </footer>
  );
}
