import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import SignUpModal from '../components/auth/SignUpModal';

const F = "'Helvetica', 'Helvetica Neue', Arial, sans-serif";

// ═══════════════════════════════════════════════════════════
export default function HomePage() {
  const [showModal, setShowModal] = useState(false);
  const { isLoggedIn } = useAuth();
  const navigate = useNavigate();

  function handleCTA() {
    if (isLoggedIn) navigate('/graph');
    else setShowModal(true);
  }

  return (
    <div style={{ fontFamily: F }}>

      {/* ═══════════════════════════════════════════════════
          HERO
      ═══════════════════════════════════════════════════ */}
      <section
        id="home-hero"
        style={{
          borderBottom: '1px solid #eee',
        }}
      >

        <div style={{
          maxWidth: '1400px', margin: '0 auto',
          padding: '88px 48px 80px',
          position: 'relative', zIndex: 1,
        }}>
          {/* Mission badge */}
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: '8px',
            border: '1px solid #ddd', padding: '5px 14px',
            marginBottom: '32px',
          }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#111', display: 'inline-block' }} />
            <span style={{ fontSize: '9px', fontWeight: '700', letterSpacing: '2px', color: '#666', textTransform: 'uppercase' }}>
              Chandrayaan-3 · LIBS · Level-1 · PDS4
            </span>
          </div>

          {/* Main wordmark */}
          <h1 style={{
            fontFamily: F,
            fontSize: 'clamp(42px, 7vw, 86px)',
            fontWeight: '700',
            letterSpacing: '-1px',
            color: '#111',
            margin: '0 0 6px',
            lineHeight: 1,
          }}>
            LUNAR<span style={{ fontWeight: '300' }}>ATLAS</span>
          </h1>

          {/* Tagline */}
          <div style={{
            fontSize: 'clamp(14px, 2vw, 18px)',
            fontWeight: '300',
            color: '#555',
            letterSpacing: '0.5px',
            marginBottom: '16px',
            maxWidth: '600px',
            lineHeight: 1.5,
          }}>
            From PDS4 Archives to Analysis-Ready Spectra
          </div>

          <div style={{
            fontSize: '12px',
            color: '#999',
            letterSpacing: '0.3px',
            marginBottom: '40px',
            maxWidth: '540px',
            lineHeight: 1.6,
          }}>
            Transforming 2,049 wavelength channels (164.35–878.26 nm) from
            Chandrayaan-3 LIBS Level-1 products into cleaned, versioned,
            machine-accessible spectral records.
          </div>

          {/* CTA buttons */}
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <button
              id="home-cta-signup"
              onClick={handleCTA}
              style={{
                fontFamily: F,
                fontSize: '11px',
                fontWeight: '700',
                letterSpacing: '2px',
                textTransform: 'uppercase',
                background: '#111',
                color: '#fff',
                border: 'none',
                padding: '14px 32px',
                cursor: 'pointer',
                transition: 'background 0.15s ease',
              }}
              onMouseEnter={e => (e.currentTarget.style.background = '#333')}
              onMouseLeave={e => (e.currentTarget.style.background = '#111')}
            >
              {isLoggedIn ? 'View Spectral Graph' : 'Request Access'}
            </button>
          </div>

          {/* Stats row */}
          <div style={{
            display: 'flex', gap: '0', marginTop: '56px',
            borderTop: '1px solid #eee', paddingTop: '28px',
            flexWrap: 'wrap',
          }}>
            {[
              { val: '2,049', label: 'Wavelength Channels' },
              { val: '164–878 nm', label: 'Spectral Range' },
              { val: '~7.1×', label: 'Baseline Suppression Factor' },
            ].map(({ val, label }) => (
              <div key={label} style={{
                flex: '1 0 180px',
                padding: '0 48px 0 0',
                marginBottom: '12px',
              }}>
                <div style={{ fontSize: '22px', fontWeight: '700', color: '#111', letterSpacing: '-0.5px' }}>{val}</div>
                <div style={{ fontSize: '10px', color: '#999', letterSpacing: '1px', textTransform: 'uppercase', marginTop: '4px' }}>{label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════
          ABSTRACT
      ═══════════════════════════════════════════════════ */}
      <section
        id="home-abstract"
        style={{ background: '#fafafa' }}
      >
        <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '64px 48px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '64px', alignItems: 'start' }}>
            <div>
              <div style={{
                fontSize: '9px', fontWeight: '700', letterSpacing: '2.5px',
                color: '#999', textTransform: 'uppercase', marginBottom: '16px',
              }}>
                Abstract
              </div>
              <div style={{ fontSize: '13px', fontWeight: '700', color: '#111', lineHeight: 1.4 }}>
                Reproducible Spectral Data Infrastructure for Chandrayaan-3 LIBS
              </div>
              <div style={{ marginTop: '20px', fontSize: '11px', color: '#999', lineHeight: 1.6 }}>
                Anand, L. & Saeed, D.<br />
                Independent Researchers, India<br />
                April 2026
              </div>
            </div>
            <div style={{
              borderLeft: '2px solid #eee',
              paddingLeft: '40px',
            }}>
              <p style={{ fontSize: '13px', color: '#333', lineHeight: '1.75', margin: '0 0 16px', letterSpacing: '0.2px' }}>
                We present <strong>LunarAtlas</strong>, a reproducible data-processing infrastructure
                that transforms publicly available Chandrayaan-3 Laser-Induced Breakdown Spectroscopy
                (LIBS) Level-1 products into cleaned, machine-accessible, long-form spectral records
                suitable for quantitative lunar science.
              </p>
              <p style={{ fontSize: '13px', color: '#333', lineHeight: '1.75', margin: '0 0 16px', letterSpacing: '0.2px' }}>
                Starting from calibrated L1 tables released through ISRO's PDS4-compliant archive,
                LunarAtlas implements a transparent Python pipeline that parses XML metadata, reshapes
                wide-format tables in which <strong>2,049 wavelength channels appear as column headers
                spanning 164.35–878.26 nm</strong>, identifies and correctly pairs plasma and background
                measurements, and performs physically motivated background subtraction.
              </p>
              <p style={{ fontSize: '13px', color: '#333', lineHeight: '1.75', margin: '0', letterSpacing: '0.2px' }}>
                Applied to real Chandrayaan-3 L1 data, the pipeline yields cleaned measurements with a
                <strong> baseline suppression factor of ~7.1</strong>. The Measurement ID is the cornerstone
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
