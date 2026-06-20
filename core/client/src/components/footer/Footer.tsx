import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function Footer() {
  const { isLoggedIn } = useAuth();

  return (
    <footer className="border-t border-[#eee] dark:border-[#1e1e1e] bg-canvas-alt dark:bg-[#111111] font-sans transition-colors duration-200 py-12">
      <div className="max-w-[1200px] mx-auto px-8 grid grid-cols-1 md:grid-cols-4 gap-8">
        
        {/* Brand / Info */}
        <div className="space-y-3">
          <div className="text-[12px] font-bold tracking-[2px] text-ink dark:text-white uppercase">
            LUNAR<span className="font-light">ATLAS</span>
          </div>
          <p className="text-[11px] text-[#444] dark:text-[#aaa] leading-relaxed m-0">
            A reproducible data-processing infrastructure for Chandrayaan-3 Laser-Induced Breakdown Spectroscopy (LIBS) Level-1 products.
          </p>
          <div className="text-[10px] text-[#555] dark:text-[#888] font-semibold tracking-wide uppercase pt-2">
            Built for Chandrayaan-3 Science
          </div>
        </div>

        {/* Column 1: Links */}
        <div className="flex flex-col gap-2.5">
          <span className="text-[10px] font-bold text-ink dark:text-[#f0f0f0] uppercase tracking-wider">Links</span>
          <Link to="/" className="text-[11.5px] text-[#444] dark:text-[#999] hover:text-ink dark:hover:text-white no-underline transition-colors w-fit">Home</Link>
          <Link to="/analyzer" className="text-[11.5px] text-[#444] dark:text-[#999] hover:text-ink dark:hover:text-white no-underline transition-colors w-fit">Spectral Analyzer</Link>
          <Link to="/docs" className="text-[11.5px] text-[#444] dark:text-[#999] hover:text-ink dark:hover:text-white no-underline transition-colors w-fit">Documentation</Link>
          <Link to="/developers" className="text-[11.5px] text-[#444] dark:text-[#999] hover:text-ink dark:hover:text-white no-underline transition-colors w-fit">Developers</Link>
          {isLoggedIn && (
            <Link to="/dashboard" className="text-[11.5px] text-[#444] dark:text-[#999] hover:text-ink dark:hover:text-white no-underline transition-colors w-fit">Dashboard</Link>
          )}
        </div>

        {/* Column 2: Resources */}
        <div className="flex flex-col gap-2.5">
          <span className="text-[10px] font-bold text-ink dark:text-[#f0f0f0] uppercase tracking-wider">Resources</span>
          <a href="https://github.com/LovekeshAnand/LunarAtlas" target="_blank" rel="noopener noreferrer" className="text-[11.5px] text-[#444] dark:text-[#999] hover:text-ink dark:hover:text-white no-underline transition-colors w-fit">GitHub Repository</a>
          <a href="https://pradan.issdc.gov.in" target="_blank" rel="noopener noreferrer" className="text-[11.5px] text-[#444] dark:text-[#999] hover:text-ink dark:hover:text-white no-underline transition-colors w-fit">ISRO Pradan Portal</a>
          <a href="https://pds.nasa.gov/datastandards/about/" target="_blank" rel="noopener noreferrer" className="text-[11.5px] text-[#444] dark:text-[#999] hover:text-ink dark:hover:text-white no-underline transition-colors w-fit">PDS4 Standards</a>
        </div>

        {/* Column 3: Contact */}
        <div className="flex flex-col gap-2.5">
          <span className="text-[10px] font-bold text-ink dark:text-[#f0f0f0] uppercase tracking-wider">Contact</span>
          <a href="mailto:lovekeshanand6@gmail.com" className="text-[11.5px] text-[#444] dark:text-[#999] hover:text-ink dark:hover:text-white no-underline transition-colors w-fit">lovekeshanand6@gmail.com</a>
          <a href="mailto:duasaeed641@gmail.com" className="text-[11.5px] text-[#444] dark:text-[#999] hover:text-ink dark:hover:text-white no-underline transition-colors w-fit">duasaeed641@gmail.com</a>
        </div>

      </div>

      {/* Copy row */}
      <div className="max-w-[1200px] mx-auto px-8 mt-10 border-t border-[#eee] dark:border-[#222] pt-6 flex justify-center items-center text-[10px] text-[#555] dark:text-[#888] tracking-[0.5px]">
        <span>© 2026 LunarAtlas. All rights reserved.</span>
      </div>
    </footer>
  );
}
