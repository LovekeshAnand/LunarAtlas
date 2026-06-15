import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer className="border-t border-[#eee] dark:border-[#1e1e1e] bg-canvas-alt dark:bg-[#111111] font-sans transition-colors duration-200 py-12">
      <div className="max-w-[1200px] mx-auto px-8 grid grid-cols-1 md:grid-cols-4 gap-8">
        
        {/* Brand / Info */}
        <div className="space-y-3">
          <div className="text-[12px] font-bold tracking-[2px] text-ink dark:text-white uppercase">
            LUNAR<span className="font-light">ATLAS</span>
          </div>
          <p className="text-[11px] text-[#666] dark:text-[#888] leading-relaxed m-0">
            A reproducible data-processing infrastructure for Chandrayaan-3 Laser-Induced Breakdown Spectroscopy (LIBS) Level-1 products.
          </p>
          <div className="text-[10px] text-[#888] dark:text-[#555] font-semibold tracking-wide uppercase pt-2">
            Built for Chandrayaan-3 Science
          </div>
        </div>

        {/* Column 1: Product */}
        <div className="flex flex-col gap-2.5">
          <span className="text-[10px] font-bold text-ink-muted dark:text-[#444] uppercase tracking-wider">Product</span>
          <Link to="/" className="text-[11.5px] text-[#666] dark:text-[#999] hover:text-ink dark:hover:text-white no-underline transition-colors w-fit">Home Platform</Link>
          <Link to="/pipeline" className="text-[11.5px] text-[#666] dark:text-[#999] hover:text-ink dark:hover:text-white no-underline transition-colors w-fit">Processing Pipeline</Link>
          <Link to="/graph" className="text-[11.5px] text-[#666] dark:text-[#999] hover:text-ink dark:hover:text-white no-underline transition-colors w-fit">Spectral Analyzer</Link>
        </div>

        {/* Column 2: Resources */}
        <div className="flex flex-col gap-2.5">
          <span className="text-[10px] font-bold text-ink-muted dark:text-[#444] uppercase tracking-wider">Resources</span>
          <Link to="/docs" className="text-[11.5px] text-[#666] dark:text-[#999] hover:text-ink dark:hover:text-white no-underline transition-colors w-fit">Documentation</Link>
          <Link to="/developers" className="text-[11.5px] text-[#666] dark:text-[#999] hover:text-ink dark:hover:text-white no-underline transition-colors w-fit">API Reference</Link>
          <a href="https://github.com/lunaratlas/libs" target="_blank" rel="noopener noreferrer" className="text-[11.5px] text-[#666] dark:text-[#999] hover:text-ink dark:hover:text-white no-underline transition-colors w-fit">GitHub Repository</a>
        </div>

        {/* Column 3: Legal & Metadata */}
        <div className="flex flex-col gap-2.5">
          <span className="text-[10px] font-bold text-ink-muted dark:text-[#444] uppercase tracking-wider">Legal / Archive</span>
          <span className="text-[11.5px] text-[#666] dark:text-[#999]">PDS4 Compliance Archive</span>
          <span className="text-[11.5px] text-[#666] dark:text-[#999]">MIT License</span>
          <span className="text-[11.5px] text-[#666] dark:text-[#999]">ISRO Data Policy</span>
        </div>

      </div>

      {/* Copy row */}
      <div className="max-w-[1200px] mx-auto px-8 mt-10 border-t border-[#eee] dark:border-[#222] pt-6 flex justify-between items-center text-[10px] text-ink-muted dark:text-[#444] tracking-[0.5px]">
        <span>© 2026 LunarAtlas. All rights reserved.</span>
        <span>Version 2.0.0 (Chandrayaan-3 LIBS L1-L2 Ingestion Engine)</span>
      </div>
    </footer>
  );
}
