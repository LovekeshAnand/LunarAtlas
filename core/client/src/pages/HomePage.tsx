import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import SignUpModal from '../components/auth/SignUpModal';

// ═══════════════════════════════════════════════════════════════
export default function HomePage() {
  const [showModal, setShowModal] = useState(false);
  const { isLoggedIn } = useAuth();
  const navigate = useNavigate();

  function handleCTA() {
    if (isLoggedIn) navigate('/graph');
    else setShowModal(true);
  }

  return (
    <div className="font-sans">

      {/* ═══════════════════════════════════════════════════
          HERO  ·  grid-mesh applies the subtle 40 px mesh;
          color is handled by --grid-line CSS var in index.css
      ═══════════════════════════════════════════════════ */}
      <section id="home-hero" className="border-b border-[#eee] dark:border-[#1e1e1e] grid-mesh">
        <div className="max-w-[1400px] mx-auto px-12 pt-[88px] pb-20 relative z-[1]">

          {/* Mission badge */}
          <div className="inline-flex items-center gap-2 border border-border-dark dark:border-[#2a2a2a] px-[14px] py-[5px] mb-8">
            <span className="w-[6px] h-[6px] rounded-full bg-ink dark:bg-[#f0f0f0] inline-block" />
            <span className="text-[9px] font-bold tracking-[2px] text-[#666] dark:text-[#555] uppercase">
              Chandrayaan-3 · LIBS · Level-1 · PDS4
            </span>
          </div>

          {/* Main wordmark */}
          <h1 className="font-sans text-[clamp(42px,7vw,86px)] font-bold tracking-[-1px] text-ink dark:text-[#f0f0f0] m-0 mb-[6px] leading-none">
            LUNAR<span className="font-light">ATLAS</span>
          </h1>

          {/* Tagline */}
          <div className="text-[clamp(14px,2vw,18px)] font-light text-[#555] dark:text-[#888] tracking-[0.5px] mb-4 max-w-[600px] leading-[1.5]">
            From PDS4 Archives to Analysis-Ready Spectra
          </div>

          <div className="text-[12px] text-[#999] dark:text-[#555] tracking-[0.3px] mb-10 max-w-[540px] leading-[1.6]">
            Transforming 2,049 wavelength channels (164.35–878.26 nm) from
            Chandrayaan-3 LIBS Level-1 products into cleaned, versioned,
            machine-accessible spectral records.
          </div>

          {/* CTA buttons */}
          <div className="flex gap-3 flex-wrap">
            <button
              id="home-cta-signup"
              onClick={handleCTA}
              className="font-sans text-[11px] font-bold tracking-[2px] uppercase bg-ink dark:bg-[#f0f0f0] text-white dark:text-[#0d0d0d] border-0 px-8 py-[14px] cursor-pointer transition-colors duration-150 hover:bg-[#333] dark:hover:bg-[#d0d0d0]"
            >
              {isLoggedIn ? 'View Spectral Graph' : 'Request Access'}
            </button>
          </div>

          {/* Stats row */}
          <div className="flex gap-0 mt-14 border-t border-[#eee] dark:border-[#1e1e1e] pt-7 flex-wrap">
            {[
              { val: '2,049',      label: 'Wavelength Channels' },
              { val: '164–878 nm', label: 'Spectral Range' },
              { val: '~7.1×',     label: 'Baseline Suppression Factor' },
            ].map(({ val, label }) => (
              <div key={label} className="flex-[1_0_180px] pr-12 mb-3">
                <div className="text-[22px] font-bold text-ink dark:text-[#f0f0f0] tracking-[-0.5px]">{val}</div>
                <div className="text-[10px] text-[#999] dark:text-[#555] tracking-[1px] uppercase mt-1">{label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════
          ABSTRACT
      ═══════════════════════════════════════════════════ */}
      <section id="home-abstract" className="bg-canvas-alt dark:bg-[#141414] transition-colors duration-200">
        <div className="max-w-[1400px] mx-auto px-12 py-16">
          <div className="grid grid-cols-[1fr_2fr] gap-16 items-start">

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

            <div className="border-l-2 border-[#eee] dark:border-[#222] pl-10">
              <p className="text-[13px] text-[#333] dark:text-[#aaa] leading-[1.75] mb-4 tracking-[0.2px]">
                We present <strong className="text-ink dark:text-[#f0f0f0]">LunarAtlas</strong>, a reproducible data-processing infrastructure
                that transforms publicly available Chandrayaan-3 Laser-Induced Breakdown Spectroscopy
                (LIBS) Level-1 products into cleaned, machine-accessible, long-form spectral records
                suitable for quantitative lunar science.
              </p>
              <p className="text-[13px] text-[#333] dark:text-[#aaa] leading-[1.75] mb-4 tracking-[0.2px]">
                Starting from calibrated L1 tables released through ISRO's PDS4-compliant archive,
                LunarAtlas implements a transparent Python pipeline that parses XML metadata, reshapes
                wide-format tables in which <strong className="text-ink dark:text-[#f0f0f0]">2,049 wavelength channels appear as column headers
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

      {showModal && <SignUpModal onClose={() => setShowModal(false)} />}
    </div>
  );
}
