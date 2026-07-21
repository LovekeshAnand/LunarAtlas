import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import SignUpModal from '../components/auth/SignUpModal';
import LttbVisualizer from '../components/education/LttbVisualizer';

export default function HomePage() {
  const [showModal, setShowModal] = useState(false);
  const { isLoggedIn } = useAuth();
  const navigate = useNavigate();


  function handleCTA() {
    if (isLoggedIn) navigate('/analyzer');
    else setShowModal(true);
  }

  return (
    <div className="font-sans bg-canvas dark:bg-[#0d0d0d] transition-colors duration-200">

      {/* ── HERO SECTION WITH LEFT TYPOGRAPHY & LTTB VISUALIZER ── */}
      <section id="home-hero" className="border-b border-[#eee] dark:border-[#1e1e1e] grid-mesh relative overflow-hidden min-h-[calc(100vh-61px)] flex items-center">
        
        {/* Ambient grayscale glows */}
        <div className="absolute top-1/4 left-1/3 w-[300px] h-[300px] bg-neutral-200 dark:bg-neutral-850 rounded-full blur-[120px] opacity-10 dark:opacity-5 pointer-events-none" />
        <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-neutral-300 dark:bg-neutral-900 rounded-full blur-[140px] opacity-10 dark:opacity-5 pointer-events-none" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[450px] bg-gradient-to-tr from-neutral-100/50 to-neutral-200/50 dark:from-[#111] dark:to-[#161616] rounded-full blur-[120px] opacity-40 dark:opacity-60 pointer-events-none" />

        <div className="max-w-[1400px] mx-auto px-12 py-16 relative z-[1] w-full">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            
            {/* Left Column: Text content */}
            <div className="lg:col-span-6 flex flex-col items-start text-left">
              
              {/* Mission badge */}
              <div className="inline-flex items-center gap-2 border border-border-dark dark:border-[#2a2a2a] px-[14px] py-[5px] mb-8 bg-canvas-alt dark:bg-[#141414] rounded-full">
                <span className="w-[6px] h-[6px] rounded-full bg-ink dark:bg-[#f0f0f0] inline-block animate-pulse" />
                <span className="text-[9px] font-bold tracking-[2px] text-neutral-800 dark:text-neutral-300 uppercase">
                  Chandrayaan-3 · LIBS · Level-1 · PDS4
                </span>
              </div>
 
              {/* Main wordmark */}
              <h1 className="font-sans text-[clamp(48px,8vw,82px)] font-black tracking-[-3px] text-neutral-900 dark:text-[#f3f3f3] m-0 mb-4 leading-[0.9] select-none">
                LUNARATLAS
              </h1>

              {/* Tagline */}
              <div className="text-[clamp(18px,2.8vw,24px)] font-light text-neutral-800 dark:text-neutral-200 tracking-[-0.5px] mb-6 max-w-[650px] leading-[1.3] font-sans">
                A Reproducible Data Ingestion &amp; <span className="font-semibold text-neutral-900 dark:text-white underline decoration-neutral-800 dark:decoration-neutral-200 decoration-3 underline-offset-4">Interactive Visualization</span> Infrastructure
              </div>

              {/* Description */}
              <div className="text-[13.5px] text-neutral-700 dark:text-neutral-400 tracking-[0.2px] mb-10 max-w-[600px] leading-[1.6]">
                A reproducible open infrastructure for parsing, processing, and exploring Chandrayaan-3 LIBS Level-1 data products.
              </div>

              {/* CTA buttons */}
              <div className="flex gap-4 justify-start items-center flex-wrap">
                <button
                  id="home-cta-signup"
                  onClick={handleCTA}
                  className="group/cta font-sans text-[11px] font-bold tracking-[2px] uppercase bg-neutral-900 dark:bg-white text-white dark:text-neutral-950 px-8 py-[15px] cursor-pointer transition-all duration-200 hover:bg-neutral-800 dark:hover:bg-neutral-100 hover:shadow-[0_0_20px_rgba(0,0,0,0.1)] dark:hover:shadow-[0_0_20px_rgba(255,255,255,0.15)] hover:-translate-y-[1px] rounded-md flex items-center gap-2 border-0"
                >
                  <span>{isLoggedIn ? 'View Spectral Analyzer' : 'Request Access'}</span>
                  <svg className="w-3.5 h-3.5 transform transition-transform duration-200 group-hover/cta:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                  </svg>
                </button>
                <Link
                  to="/developers"
                  className="font-sans text-[11px] font-bold tracking-[2px] uppercase border border-neutral-300 dark:border-neutral-800 text-neutral-800 dark:text-neutral-200 px-8 py-[15px] no-underline transition-all duration-200 hover:bg-neutral-50 dark:hover:bg-[#141414] hover:border-neutral-400 dark:hover:border-neutral-700 hover:-translate-y-[1px] rounded-md"
                >
                  Explore API Reference
                </Link>
              </div>

            </div>

            {/* Right Column: Dynamic LTTB Downsampling Visualizer */}
            <div className="lg:col-span-6 flex justify-center items-center relative mt-12 lg:mt-0 w-full">
              <div className="w-full max-w-[580px]">
                <LttbVisualizer />
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* ── LIBS PROCESS EXPLANATION SECTION ── */}
      <section className="border-b border-[#eee] dark:border-[#1e1e1e] py-20 bg-neutral-50/30 dark:bg-[#0b0b0b]/30">
        <div className="max-w-[1400px] mx-auto px-12">
          
          <div className="text-center max-w-[800px] mx-auto mb-16">
            <div className="text-[9px] font-bold tracking-[2.5px] text-neutral-800 dark:text-neutral-500 uppercase mb-3">
              Spectroscopic Analysis Workflow
            </div>
            <h2 className="text-[clamp(28px,4vw,38px)] font-black text-neutral-900 dark:text-[#f3f3f3] tracking-tight leading-none mb-4 uppercase">
              Understanding LIBS
            </h2>
            <p className="text-[14px] text-neutral-700 dark:text-neutral-400 leading-[1.6]">
              Laser-Induced Breakdown Spectroscopy (LIBS) determines the elemental composition of materials in-situ. Below is the simplified, concrete sequence of the Pragyan spectrometer's spectral capture.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-16 items-center">
            
            {/* Left Column: LIBS Process Diagram */}
            <div className="lg:col-span-6 flex justify-center items-center">
              <div className="relative group rounded-2xl overflow-hidden border border-neutral-200 dark:border-neutral-800 shadow-xl bg-white dark:bg-[#111] p-3 transition-all duration-300 hover:scale-[1.01] hover:border-neutral-300 dark:hover:border-neutral-700">
                <img 
                  src="/libs.png" 
                  alt="Laser-Induced Breakdown Spectroscopy Process Diagram" 
                  className="w-full h-auto object-contain rounded-lg select-none"
                />
              </div>
            </div>

            {/* Right Column: Concrete scientific steps in clean black & white */}
            <div className="lg:col-span-6 space-y-8">
              
              {/* Step 1 */}
              <div className="flex gap-5 group">
                <div className="w-10 h-10 rounded-lg bg-neutral-100 dark:bg-neutral-800 border border-neutral-200 dark:border-[#222] flex items-center justify-center font-mono text-[14px] font-bold text-neutral-700 dark:text-neutral-300 shrink-0 group-hover:border-neutral-500 dark:group-hover:border-neutral-450 group-hover:bg-neutral-50 dark:group-hover:bg-neutral-900/50 transition-colors duration-200">
                  01
                </div>
                <div>
                  <h4 className="text-[14px] font-bold text-neutral-900 dark:text-white uppercase tracking-wider mb-1.5 flex items-center gap-2">
                    Laser Ablation
                    <span className="text-[9px] bg-neutral-100 dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200 border border-neutral-200 dark:border-neutral-750 font-mono px-1.5 py-0.5 rounded tracking-normal">
                      1064 nm Nd:YAG
                    </span>
                  </h4>
                  <p className="text-[12.5px] text-neutral-700 dark:text-neutral-450 leading-relaxed m-0">
                    A high-energy Nd:YAG pulsed laser targets the lunar surface from a distance of ~200 mm, focusing dense thermal energy onto a micro-spot.
                  </p>
                </div>
              </div>

              {/* Step 2 */}
              <div className="flex gap-5 group">
                <div className="w-10 h-10 rounded-lg bg-neutral-100 dark:bg-neutral-800 border border-neutral-200 dark:border-[#222] flex items-center justify-center font-mono text-[14px] font-bold text-neutral-700 dark:text-neutral-300 shrink-0 group-hover:border-neutral-500 dark:group-hover:border-neutral-450 group-hover:bg-neutral-50 dark:group-hover:bg-neutral-900/50 transition-colors duration-200">
                  02
                </div>
                <div>
                  <h4 className="text-[14px] font-bold text-neutral-900 dark:text-white uppercase tracking-wider mb-1.5 flex items-center gap-2">
                    Plasma Plume
                    <span className="text-[9px] bg-neutral-100 dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200 border border-neutral-200 dark:border-neutral-750 font-mono px-1.5 py-0.5 rounded tracking-normal">
                      &gt; 10,000 Kelvin
                    </span>
                  </h4>
                  <p className="text-[12.5px] text-neutral-700 dark:text-neutral-450 leading-relaxed m-0">
                    The surface material undergoes explosive melt vaporization, creating a highly ionized plasma plume of excited atomic species.
                  </p>
                </div>
              </div>

              {/* Step 3 */}
              <div className="flex gap-5 group">
                <div className="w-10 h-10 rounded-lg bg-neutral-100 dark:bg-neutral-800 border border-neutral-200 dark:border-[#222] flex items-center justify-center font-mono text-[14px] font-bold text-neutral-700 dark:text-neutral-300 shrink-0 group-hover:border-neutral-500 dark:group-hover:border-neutral-450 group-hover:bg-neutral-50 dark:group-hover:bg-neutral-900/50 transition-colors duration-200">
                  03
                </div>
                <div>
                  <h4 className="text-[14px] font-bold text-neutral-900 dark:text-white uppercase tracking-wider mb-1.5 flex items-center gap-2">
                    Atomic Emission
                    <span className="text-[9px] bg-neutral-100 dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200 border border-neutral-200 dark:border-neutral-750 font-mono px-1.5 py-0.5 rounded tracking-normal">
                      Photon Decay
                    </span>
                  </h4>
                  <p className="text-[12.5px] text-neutral-700 dark:text-neutral-450 leading-relaxed m-0">
                    As the plasma cools, excited electrons decay back to lower energy levels, emitting photons at characteristic atomic spectral wavelengths.
                  </p>
                </div>
              </div>

              {/* Step 4 */}
              <div className="flex gap-5 group">
                <div className="w-10 h-10 rounded-lg bg-neutral-100 dark:bg-neutral-800 border border-neutral-200 dark:border-[#222] flex items-center justify-center font-mono text-[14px] font-bold text-neutral-700 dark:text-neutral-300 shrink-0 group-hover:border-neutral-500 dark:group-hover:border-neutral-450 group-hover:bg-neutral-50 dark:group-hover:bg-neutral-900/50 transition-colors duration-200">
                  04
                </div>
                <div>
                  <h4 className="text-[14px] font-bold text-neutral-900 dark:text-white uppercase tracking-wider mb-1.5 flex items-center gap-2">
                    Czerny-Turner Dispersion
                    <span className="text-[9px] bg-neutral-100 dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200 border border-neutral-200 dark:border-neutral-750 font-mono px-1.5 py-0.5 rounded tracking-normal">
                      164.35 - 878.26 nm
                    </span>
                  </h4>
                  <p className="text-[12.5px] text-neutral-700 dark:text-neutral-450 leading-relaxed m-0">
                    Fiber optics capture the light and feed it to a spectrometer, where a diffraction grating disperses wavelengths onto a 2,094-channel CCD array.
                  </p>
                </div>
              </div>

              {/* Step 5 */}
              <div className="flex gap-5 group">
                <div className="w-10 h-10 rounded-lg bg-neutral-100 dark:bg-neutral-800 border border-neutral-200 dark:border-[#222] flex items-center justify-center font-mono text-[14px] font-bold text-neutral-700 dark:text-neutral-300 shrink-0 group-hover:border-neutral-500 dark:group-hover:border-neutral-450 group-hover:bg-neutral-50 dark:group-hover:bg-neutral-900/50 transition-colors duration-200">
                  05
                </div>
                <div>
                  <h4 className="text-[14px] font-bold text-neutral-900 dark:text-white uppercase tracking-wider mb-1.5 flex items-center gap-2">
                    LunarAtlas Ingestion
                    <span className="text-[9px] bg-neutral-100 dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200 border border-neutral-200 dark:border-neutral-750 font-mono px-1.5 py-0.5 rounded tracking-normal">
                      PDS4 Processing
                    </span>
                  </h4>
                  <p className="text-[12.5px] text-neutral-700 dark:text-neutral-450 leading-relaxed m-0">
                    LunarAtlas parses raw PDS4 spreadsheets, subtracts background noise records, and serves clean abundance spectra through normalised APIs.
                  </p>
                </div>
              </div>

            </div>

          </div>

        </div>
      </section>

      {/* ── FEATURES GRID ── */}
      <section className="border-b border-[#eee] dark:border-[#1e1e1e] py-16">
        <div className="max-w-[1200px] mx-auto px-12">
          <div className="text-[9px] font-bold tracking-[2.5px] text-neutral-800 dark:text-neutral-500 uppercase mb-10 text-center">
            Key Infrastructure Capabilities
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="border border-[#eee] dark:border-[#222] p-6 rounded-md hover:border-ink dark:hover:border-white transition-colors">
              <div className="w-8 h-8 flex items-center justify-center border border-ink dark:border-white mb-4">
                <span className="font-mono text-[11px] font-bold">PDS4</span>
              </div>
              <h3 className="text-[14px] font-bold text-ink dark:text-[#f0f0f0] mb-2 uppercase tracking-wide">PDS4 Compliant Metadata</h3>
              <p className="text-[12.5px] text-neutral-700 dark:text-neutral-400 leading-relaxed m-0">
                Parsed directly from ISRO's Planetary Data System archives. Every observations session is bound to its logical identifier, processing level, and purpose.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="border border-[#eee] dark:border-[#222] p-6 rounded-md hover:border-ink dark:hover:border-white transition-colors">
              <div className="w-8 h-8 flex items-center justify-center border border-ink dark:border-white mb-4">
                <span className="font-mono text-[11px] font-bold">API</span>
              </div>
              <h3 className="text-[14px] font-bold text-ink dark:text-[#f0f0f0] mb-2 uppercase tracking-wide">REST API Data Access</h3>
              <p className="text-[12.5px] text-neutral-700 dark:text-neutral-400 leading-relaxed m-0">
                Ditch the file-scraping archive downloads. Integrate our structured endpoints to fetch specific instruments, missions, observations, and telemetry on demand.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="border border-[#eee] dark:border-[#222] p-6 rounded-md hover:border-ink dark:hover:border-white transition-colors">
              <div className="w-8 h-8 flex items-center justify-center border border-ink dark:border-white mb-4">
                <span className="font-mono text-[11px] font-bold">LTTB</span>
              </div>
              <h3 className="text-[14px] font-bold text-ink dark:text-[#f0f0f0] mb-2 uppercase tracking-wide">LTTB Peak Preservation</h3>
              <p className="text-[12.5px] text-neutral-700 dark:text-neutral-400 leading-relaxed m-0">
                Largest-Triangle-Three-Buckets algorithm is applied on downsampling requests, preserving the scientific maximum/minimum plasma emission lines.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS PIPELINE VISUALIZATION ── */}
      <section className="border-b border-[#eee] dark:border-[#1e1e1e] py-16 bg-canvas-alt dark:bg-[#141414] transition-colors duration-200">
        <div className="max-w-[1200px] mx-auto px-12">
          <div className="text-[9px] font-bold tracking-[2.5px] text-neutral-800 dark:text-neutral-500 uppercase mb-12 text-center">
            How Processing Works
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
            {/* Step 1 */}
            <div className="flex gap-4 items-start">
              <div className="font-mono text-[24px] font-extrabold text-neutral-400 dark:text-neutral-700 leading-none">01</div>
              <div>
                <h4 className="text-[13px] font-bold text-ink dark:text-[#f0f0f0] uppercase tracking-wide mb-1.5">Download L1 Archive</h4>
                <p className="text-[12px] text-neutral-700 dark:text-neutral-450 leading-relaxed m-0">
                  XML schemas and wide-format CSV spreadsheets containing 2,094 wavelength channels are fetched from ISRO's Pradan portal.
                </p>
              </div>
            </div>

            {/* Step 2 */}
            <div className="flex gap-4 items-start">
              <div className="font-mono text-[24px] font-extrabold text-neutral-400 dark:text-neutral-700 leading-none">02</div>
              <div>
                <h4 className="text-[13px] font-bold text-ink dark:text-[#f0f0f0] uppercase tracking-wide mb-1.5">Execute Ingestion</h4>
                <p className="text-[12px] text-neutral-700 dark:text-neutral-450 leading-relaxed m-0">
                  We match plasma and background zaps using force reset/laser flags, suppress continuum noise, and store records relationally.
                </p>
              </div>
            </div>

            {/* Step 3 */}
            <div className="flex gap-4 items-start">
              <div className="font-mono text-[24px] font-extrabold text-neutral-400 dark:text-neutral-700 leading-none">03</div>
              <div>
                <h4 className="text-[13px] font-bold text-ink dark:text-[#f0f0f0] uppercase tracking-wide mb-1.5">Query Normalized API</h4>
                <p className="text-[12px] text-neutral-700 dark:text-neutral-450 leading-relaxed m-0">
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
              <div className="text-[9px] font-bold tracking-[2.5px] text-neutral-805 dark:text-neutral-500 uppercase mb-4">
                Abstract
              </div>
              <div className="text-[13px] font-bold text-ink dark:text-[#f0f0f0] leading-[1.4]">
                A Reproducible Data Processing and Interactive Visualization Infrastructure
              </div>
              <div className="mt-5 text-[11.5px] text-neutral-700 dark:text-neutral-500 leading-[1.6]">
                <div className="font-semibold text-neutral-900 dark:text-neutral-350">
                  <a href="https://orcid.org/0009-0009-4947-4040" target="_blank" rel="noopener noreferrer" className="hover:underline text-ink dark:text-white font-bold">Lovekesh Anand</a>
                  <span className="text-[10px] text-neutral-450 dark:text-neutral-500 block font-normal">
                    orcid: <span className="font-mono text-[#888]">0009-0009-4947-4040</span> | <a href="mailto:lovekeshanand6@gmail.com" className="hover:underline text-[#555] dark:text-[#888]">lovekeshanand6@gmail.com</a>
                  </span>
                </div>
                <div className="mt-3.5 font-semibold text-neutral-900 dark:text-neutral-350">
                  <a href="https://orcid.org/0009-0003-4871-0546" target="_blank" rel="noopener noreferrer" className="hover:underline text-ink dark:text-white font-bold">Dua Saeed</a>
                  <span className="text-[10px] text-neutral-450 dark:text-neutral-500 block font-normal">
                    orcid: <span className="font-mono text-[#888]">0009-0003-4871-0546</span> | <a href="mailto:23f1000825@ds.study.iitm.ac.in" className="hover:underline text-[#555] dark:text-[#888]">23f1000825@ds.study.iitm.ac.in</a>
                  </span>
                </div>
                <div className="mt-4 text-[10px] uppercase tracking-wider text-[#555] dark:text-[#666] font-medium leading-relaxed">
                  Mahavir Swami Institute of Technology<br />
                  June 2026
                </div>
              </div>
            </div>

            <div className="border-l-2 border-[#eee] dark:border-[#222] md:pl-10 pl-4">
              <p className="text-[13px] text-neutral-800 dark:text-[#aaa] leading-[1.75] mb-4 tracking-[0.2px]">
                <strong className="text-ink dark:text-[#f0f0f0]">LunarAtlas</strong> is an open-source, reproducible data processing infrastructure that transforms publicly available Chandrayaan-3 laser-induced breakdown spectroscopy (LIBS) Level-1 (L1) products from the ISRO Planetary Data Archive into normalised, analysis-ready spectral records suitable for quantitative lunar science. The Chandrayaan-3 LE-LIBS L1 archive distributes calibrated spectra in wide-format tables where 2,094 wavelength channels (instrument range: 220–800 nm; stored channel range: 164.35–878.26 nm) appear as individual columns, with plasma and background acquisitions interleaved. To our knowledge, no publicly documented, reproducible pipeline exists to ingest and clean these products automatically.
              </p>
              <p className="text-[13px] text-neutral-800 dark:text-[#aaa] leading-[1.75] mb-4 tracking-[0.2px]">
                LunarAtlas implements a six-stage deterministic Python pipeline that: (i) parses PDS4 XML metadata; (ii) verifies file provenance via MD5 checksums; (iii) reshapes wide-format records into a normalised long-form relational layout <code className="font-mono bg-neutral-100 dark:bg-neutral-800 px-1.5 py-0.5 rounded text-[11px] text-ink dark:text-[#eee]">(Measurement_ID, Wavelength_nm) → Intensity (a.u.)</code>; (iv) identifies plasma and background shots from mission status flags; (v) applies paired background subtraction with clamping; and (vi) assigns file-unique Measurement IDs.
              </p>
              <p className="text-[13px] text-neutral-800 dark:text-[#aaa] leading-[1.75] m-0 tracking-[0.2px]">
                For interactive visualisation, LunarAtlas employs an LTTB+Peaks adaptive downsampling algorithm that retains 100% of detected spectral peaks. A versioned REST API delivers spectral data with API response latency below 500 ms on a single-node workstation.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── CONTRIBUTIONS SECTION ── */}
      <section id="home-contributions" className="border-b border-[#eee] dark:border-[#1e1e1e] py-16 bg-white dark:bg-[#0d0d0d] transition-colors duration-200">
        <div className="max-w-[1400px] mx-auto px-12">
          <div className="max-w-[800px] mx-auto">
            <div className="text-[9px] font-bold tracking-[2.5px] text-neutral-800 dark:text-neutral-500 uppercase mb-6 text-center">
              Paper Contributions
            </div>
            
            <div className="space-y-6">
              <div className="flex gap-4 items-start border-b border-[#f5f5f5] dark:border-[#161616] pb-4">
                <div className="font-mono text-[14px] font-bold text-ink dark:text-white shrink-0">C1</div>
                <div>
                  <h4 className="text-[13.5px] font-bold text-ink dark:text-[#f0f0f0] uppercase tracking-wide mb-1">
                    Reproducible L1 Processing Pipeline
                  </h4>
                  <p className="text-[12.5px] text-[#666] dark:text-[#888] leading-relaxed m-0">
                    A documented Python workflow that ingests PDS4 products, reshapes wide-format spectra, identifies plasma-background pairs, performs background subtraction, and records processing provenance.
                  </p>
                </div>
              </div>

              <div className="flex gap-4 items-start border-b border-[#f5f5f5] dark:border-[#161616] pb-4">
                <div className="font-mono text-[14px] font-bold text-ink dark:text-white shrink-0">C2</div>
                <div>
                  <h4 className="text-[13.5px] font-bold text-ink dark:text-[#f0f0f0] uppercase tracking-wide mb-1">
                    Measurement-ID Semantics
                  </h4>
                  <p className="text-[12.5px] text-[#666] dark:text-[#888] leading-relaxed m-0">
                    A shot-resolved data model that preserves links between processed spectra, acquisition metadata, and instrument operating conditions.
                  </p>
                </div>
              </div>

              <div className="flex gap-4 items-start border-b border-[#f5f5f5] dark:border-[#161616] pb-4">
                <div className="font-mono text-[14px] font-bold text-ink dark:text-white shrink-0">C3</div>
                <div>
                  <h4 className="text-[13.5px] font-bold text-ink dark:text-[#f0f0f0] uppercase tracking-wide mb-1">
                    PDS4-Aware Data Model
                  </h4>
                  <p className="text-[12.5px] text-[#666] dark:text-[#888] leading-relaxed m-0">
                    A normalised PostgreSQL schema supporting efficient storage, querying, and provenance tracking of spectral observations.
                  </p>
                </div>
              </div>

              <div className="flex gap-4 items-start border-b border-[#f5f5f5] dark:border-[#161616] pb-4">
                <div className="font-mono text-[14px] font-bold text-ink dark:text-white shrink-0">C4</div>
                <div>
                  <h4 className="text-[13.5px] font-bold text-ink dark:text-[#f0f0f0] uppercase tracking-wide mb-1">
                    Interactive Spectral Visualisation
                  </h4>
                  <p className="text-[12.5px] text-[#666] dark:text-[#888] leading-relaxed m-0">
                    An adaptive LTTB+peaks downsampling strategy that preserves diagnostically important spectral features during interactive exploration.
                  </p>
                </div>
              </div>

              <div className="flex gap-4 items-start pb-4">
                <div className="font-mono text-[14px] font-bold text-ink dark:text-white shrink-0">C5</div>
                <div>
                  <h4 className="text-[13.5px] font-bold text-ink dark:text-[#f0f0f0] uppercase tracking-wide mb-1">
                    Processing Validation
                  </h4>
                  <p className="text-[12.5px] text-[#666] dark:text-[#888] leading-relaxed m-0">
                    Quantitative evaluation of background subtraction and preprocessing effects on Chandrayaan-3 LE-LIBS spectra.
                  </p>
                </div>
              </div>
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
                className="font-sans text-[11px] font-bold tracking-[2px] uppercase bg-ink dark:bg-[#f0f0f0] text-white dark:text-[#0d0d0d] border-0 px-8 py-[14px] cursor-pointer transition-colors hover:bg-[#333] dark:hover:bg-[#d0d0d0] rounded-md"
              >
                Sign In Now
              </button>
            ) : (
              <Link
                to="/dashboard"
                className="font-sans text-[11px] font-bold tracking-[2px] uppercase bg-ink dark:bg-[#f0f0f0] text-white dark:text-[#0d0d0d] px-8 py-[14px] no-underline transition-colors hover:bg-[#333] dark:hover:bg-[#d0d0d0] rounded-md"
              >
                Go To Dashboard
              </Link>
            )}
            <Link
              to="/developers"
              className="font-sans text-[11px] font-bold tracking-[2px] uppercase border border-[#ddd] dark:border-[#2a2a2a] text-ink dark:text-white px-8 py-[14px] no-underline transition-colors hover:bg-canvas-alt dark:hover:bg-[#141414] rounded-md"
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
