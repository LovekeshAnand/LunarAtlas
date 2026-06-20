import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import SignUpModal from '../components/auth/SignUpModal';

export default function HomePage() {
  const [showModal, setShowModal] = useState(false);
  const { isLoggedIn } = useAuth();
  const navigate = useNavigate();
  const [copied, setCopied] = useState(false);

  const handleCopyCurl = () => {
    navigator.clipboard.writeText('curl https://api.lunaratlas.org/v1/spectra/spot_002');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  function handleCTA() {
    if (isLoggedIn) navigate('/analyzer');
    else setShowModal(true);
  }

  return (
    <div className="font-sans bg-canvas dark:bg-[#0d0d0d] transition-colors duration-200">

      {/* ── HERO SECTION WITH CENTERED TYPOGRAPHY ── */}
      <section id="home-hero" className="border-b border-[#eee] dark:border-[#1e1e1e] grid-mesh relative overflow-hidden">
        
        {/* Glowing backdrop ambient gradient */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-gradient-to-r from-neutral-100 to-neutral-200 dark:from-[#161616] dark:to-[#1a1a1a] rounded-full blur-3xl opacity-30 pointer-events-none" />

        <div className="max-w-[1400px] mx-auto px-12 pt-[110px] pb-24 relative z-[1]">
          
          <div className="flex flex-col items-center text-center max-w-[800px] mx-auto">
            
            {/* Mission badge */}
            <div className="inline-flex items-center gap-2 border border-border-dark dark:border-[#2a2a2a] px-[14px] py-[5px] mb-8 bg-canvas-alt dark:bg-[#141414] rounded-full">
              <span className="w-[6px] h-[6px] rounded-full bg-ink dark:bg-[#f0f0f0] inline-block animate-pulse" />
              <span className="text-[9px] font-bold tracking-[2px] text-[#666] dark:text-[#888] uppercase">
                Chandrayaan-3 · LIBS · Level-1 · PDS4
              </span>
            </div>

            {/* Main wordmark */}
            <h1 className="font-sans text-[clamp(48px,8vw,92px)] font-bold tracking-[-2px] text-ink dark:text-[#f0f0f0] m-0 mb-4 leading-none select-none">
              LUNAR<span className="font-light">ATLAS</span>
            </h1>

            {/* Tagline */}
            <div className="text-[clamp(16px,2.5vw,22px)] font-light text-[#444] dark:text-[#aaa] tracking-[0.5px] mb-6 max-w-[650px] leading-[1.4]">
              From PDS4 Archives to Analysis-Ready Spectra
            </div>

            {/* Description */}
            <div className="text-[13px] text-[#666] dark:text-[#888] tracking-[0.3px] mb-10 max-w-[600px] leading-[1.6]">
              Transforming 2,094 wavelength channels (164.35–878.26 nm) from
              Chandrayaan-3 LIBS Level-1 products into cleaned, versioned,
              machine-accessible spectral records.
            </div>

            {/* CTA buttons */}
            <div className="flex gap-4 justify-center items-center flex-wrap mb-12">
              <button
                id="home-cta-signup"
                onClick={handleCTA}
                className="font-sans text-[11px] font-bold tracking-[2px] uppercase bg-ink dark:bg-[#f0f0f0] text-white dark:text-[#0d0d0d] border-0 px-8 py-[14px] cursor-pointer transition-colors duration-150 hover:bg-[#333] dark:hover:bg-[#d0d0d0] rounded-sm"
              >
                {isLoggedIn ? 'View Spectral Analyzer' : 'Request Access'}
              </button>
              <Link
                to="/developers"
                className="font-sans text-[11px] font-bold tracking-[2px] uppercase border border-[#ddd] dark:border-[#2a2a2a] text-ink dark:text-white px-8 py-[14px] no-underline transition-colors hover:bg-canvas-alt dark:hover:bg-[#141414] rounded-sm"
              >
                Explore API Reference
              </Link>
            </div>

            {/* Simple API Copy Pill */}
            <div className="flex items-center gap-4 bg-neutral-50 dark:bg-[#111111] border border-neutral-200 dark:border-[#222] rounded-full pl-6 pr-3 py-2.5 font-mono text-[13px] text-neutral-600 dark:text-[#b0b0b0] max-w-[640px] w-full justify-between shadow-sm">
              <div className="flex items-center gap-2.5 overflow-x-auto scrollbar-none whitespace-nowrap">
                <span className="text-emerald-500 select-none font-bold">$</span>
                <span>curl https://api.lunaratlas.org/v1/spectra/spot_002</span>
              </div>
              <button
                onClick={handleCopyCurl}
                className={`text-[10px] font-bold tracking-wider uppercase px-4 py-2 rounded-full cursor-pointer transition-all duration-150 shrink-0 flex items-center justify-center border-0 ${
                  copied
                    ? 'bg-emerald-600 text-white'
                    : 'bg-ink text-white hover:bg-neutral-800'
                }`}
              >
                {copied ? (
                  <>
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="mr-1">
                      <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                    Copied
                  </>
                ) : (
                  <>
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="mr-1">
                      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                    </svg>
                    Copy
                  </>
                )}
              </button>
            </div>

          </div>

        </div>
      </section>

      {/* ── FEATURES GRID ── */}
      <section className="border-b border-[#eee] dark:border-[#1e1e1e] py-16">
        <div className="max-w-[1200px] mx-auto px-12">
          <div className="text-[9px] font-bold tracking-[2.5px] text-ink-muted dark:text-[#555] uppercase mb-10 text-center">
            Key Infrastructure Capabilities
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="border border-[#eee] dark:border-[#222] p-6 rounded-md hover:border-ink dark:hover:border-white transition-colors">
              <div className="w-8 h-8 flex items-center justify-center border border-ink dark:border-white mb-4">
                <span className="font-mono text-[11px] font-bold">PDS4</span>
              </div>
              <h3 className="text-[14px] font-bold text-ink dark:text-[#f0f0f0] mb-2 uppercase tracking-wide">PDS4 Compliant Metadata</h3>
              <p className="text-[12.5px] text-[#666] dark:text-[#999] leading-relaxed m-0">
                Parsed directly from ISRO's Planetary Data System archives. Every observations session is bound to its logical identifier, processing level, and purpose.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="border border-[#eee] dark:border-[#222] p-6 rounded-md hover:border-ink dark:hover:border-white transition-colors">
              <div className="w-8 h-8 flex items-center justify-center border border-ink dark:border-white mb-4">
                <span className="font-mono text-[11px] font-bold">API</span>
              </div>
              <h3 className="text-[14px] font-bold text-ink dark:text-[#f0f0f0] mb-2 uppercase tracking-wide">REST API Data Access</h3>
              <p className="text-[12.5px] text-[#666] dark:text-[#999] leading-relaxed m-0">
                Ditch the file-scraping archive downloads. Integrate our structured endpoints to fetch specific instruments, missions, observations, and telemetry on demand.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="border border-[#eee] dark:border-[#222] p-6 rounded-md hover:border-ink dark:hover:border-white transition-colors">
              <div className="w-8 h-8 flex items-center justify-center border border-ink dark:border-white mb-4">
                <span className="font-mono text-[11px] font-bold">LTTB</span>
              </div>
              <h3 className="text-[14px] font-bold text-ink dark:text-[#f0f0f0] mb-2 uppercase tracking-wide">LTTB Peak Preservation</h3>
              <p className="text-[12.5px] text-[#666] dark:text-[#999] leading-relaxed m-0">
                Largest-Triangle-Three-Buckets algorithm is applied on downsampling requests, preserving the scientific maximum/minimum plasma emission lines.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS PIPELINE VISUALIZATION ── */}
      <section className="border-b border-[#eee] dark:border-[#1e1e1e] py-16 bg-canvas-alt dark:bg-[#141414] transition-colors duration-200">
        <div className="max-w-[1200px] mx-auto px-12">
          <div className="text-[9px] font-bold tracking-[2.5px] text-ink-muted dark:text-[#555] uppercase mb-12 text-center">
            How Processing Works
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
            {/* Step 1 */}
            <div className="flex gap-4 items-start">
              <div className="font-mono text-[24px] font-extrabold text-ink-muted/30 dark:text-[#444]/40 leading-none">01</div>
              <div>
                <h4 className="text-[13px] font-bold text-ink dark:text-[#f0f0f0] uppercase tracking-wide mb-1.5">Download L1 Archive</h4>
                <p className="text-[12px] text-[#666] dark:text-[#888] leading-relaxed m-0">
                  XML schemas and wide-format CSV spreadsheets containing 2,094 wavelength channels are fetched from ISRO's Pradan portal.
                </p>
              </div>
            </div>

            {/* Step 2 */}
            <div className="flex gap-4 items-start">
              <div className="font-mono text-[24px] font-extrabold text-ink-muted/30 dark:text-[#444]/40 leading-none">02</div>
              <div>
                <h4 className="text-[13px] font-bold text-ink dark:text-[#f0f0f0] uppercase tracking-wide mb-1.5">Execute Ingestion</h4>
                <p className="text-[12px] text-[#666] dark:text-[#888] leading-relaxed m-0">
                  We match plasma and background zaps using force reset/laser flags, suppress continuum noise, and store records relationally.
                </p>
              </div>
            </div>

            {/* Step 3 */}
            <div className="flex gap-4 items-start">
              <div className="font-mono text-[24px] font-extrabold text-ink-muted/30 dark:text-[#444]/40 leading-none">03</div>
              <div>
                <h4 className="text-[13px] font-bold text-ink dark:text-[#f0f0f0] uppercase tracking-wide mb-1.5">Query Normalized API</h4>
                <p className="text-[12px] text-[#666] dark:text-[#888] leading-relaxed m-0">
                  Researchers query clean data products using simple developer REST keys with optional downsampling and peak retention filters.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── ABSTRACT SECTION ── */}
      <section id="home-abstract" className="border-b border-[#eee] dark:border-[#1e1e1e] py-16">
        <div className="max-w-[1400px] mx-auto px-12">
          <div className="grid grid-cols-1 md:grid-cols-[1fr_2fr] gap-16 items-start">

            <div>
              <div className="text-[9px] font-bold tracking-[2.5px] text-[#999] dark:text-[#555] uppercase mb-4">
                Abstract
              </div>
              <div className="text-[13px] font-bold text-ink dark:text-[#f0f0f0] leading-[1.4]">
                Reproducible Spectral Data Infrastructure for Chandrayaan-3 LIBS
              </div>
              <div className="mt-5 text-[11px] text-[#999] dark:text-[#555] leading-[1.6]">
                Anand, L. &amp; Saeed, D.<br />
                Independent Researchers, India<br />
                April 2026
              </div>
            </div>

            <div className="border-l-2 border-[#eee] dark:border-[#222] md:pl-10 pl-4">
              <p className="text-[13px] text-[#333] dark:text-[#aaa] leading-[1.75] mb-4 tracking-[0.2px]">
                We present <strong className="text-ink dark:text-[#f0f0f0]">LunarAtlas</strong>, a reproducible data-processing infrastructure
                that transforms publicly available Chandrayaan-3 Laser-Induced Breakdown Spectroscopy
                (LIBS) Level-1 products into cleaned, machine-accessible, long-form spectral records
                suitable for quantitative lunar science.
              </p>
              <p className="text-[13px] text-[#333] dark:text-[#aaa] leading-[1.75] mb-4 tracking-[0.2px]">
                Starting from calibrated L1 tables released through ISRO's PDS4-compliant archive,
                LunarAtlas implements a transparent Python pipeline that parses XML metadata, reshapes
                wide-format tables in which <strong className="text-ink dark:text-[#f0f0f0]">2,094 wavelength channels appear as column headers
                spanning 164.35–878.26 nm</strong>, identifies and correctly pairs plasma and background
                measurements, and performs physically motivated background subtraction.
              </p>
              <p className="text-[13px] text-[#333] dark:text-[#aaa] leading-[1.75] m-0 tracking-[0.2px]">
                Applied to real Chandrayaan-3 L1 data, the pipeline yields cleaned measurements with a
                <strong className="text-ink dark:text-[#f0f0f0]"> baseline suppression factor of ~7.1</strong>. The Measurement ID is the cornerstone
                identifier linking each spectral record to its originating plasma shot — shot-to-shot
                variability ranges from 0.5% to 76.8% negative samples, a variability that would be
                completely hidden in bulk averaging.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── CALL TO ACTION FOOTER ── */}
      <section className="bg-canvas-alt dark:bg-[#141414] py-20 text-center transition-colors duration-200">
        <div className="max-w-[800px] mx-auto px-12">
          <h2 className="text-2xl font-bold tracking-tight text-ink dark:text-white mb-3">
            Start Building with LunarAtlas
          </h2>
          <p className="text-[13px] text-[#666] dark:text-[#888] leading-relaxed mb-8 max-w-[560px] mx-auto">
            Get access key credentials, deploy our integration guides, and query Chandrayaan-3 LIBS calibrated 
            spectra within minutes.
          </p>
          <div className="flex justify-center gap-4 flex-wrap">
            {!isLoggedIn ? (
              <button
                onClick={() => setShowModal(true)}
                className="font-sans text-[11px] font-bold tracking-[2px] uppercase bg-ink dark:bg-[#f0f0f0] text-white dark:text-[#0d0d0d] border-0 px-8 py-[14px] cursor-pointer transition-colors hover:bg-[#333] dark:hover:bg-[#d0d0d0] rounded-sm"
              >
                Sign In Now
              </button>
            ) : (
              <Link
                to="/dashboard"
                className="font-sans text-[11px] font-bold tracking-[2px] uppercase bg-ink dark:bg-[#f0f0f0] text-white dark:text-[#0d0d0d] px-8 py-[14px] no-underline transition-colors hover:bg-[#333] dark:hover:bg-[#d0d0d0] rounded-sm"
              >
                Go To Dashboard
              </Link>
            )}
            <Link
              to="/developers"
              className="font-sans text-[11px] font-bold tracking-[2px] uppercase border border-[#ddd] dark:border-[#2a2a2a] text-ink dark:text-white px-8 py-[14px] no-underline transition-colors hover:bg-canvas-alt dark:hover:bg-[#141414] rounded-sm"
            >
              API Reference
            </Link>
          </div>
        </div>
      </section>

      {showModal && <SignUpModal onClose={() => setShowModal(false)} />}
    </div>
  );
}
