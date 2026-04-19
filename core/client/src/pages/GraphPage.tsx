import RangeSelectorPanel from '../components/rangeSelector/rangeSelector';
import SpectralGraph from '../components/graph/SpectralGraph';

export default function GraphPage() {
  return (
    <div className="max-w-[1400px] w-full mx-auto px-8 py-7 box-border font-sans">
      <div className="mb-5">
        <h1 className="text-[13px] font-bold tracking-[2.5px] text-ink dark:text-[#f0f0f0] uppercase m-0">
          Spectral Analysis
        </h1>
        <p className="text-[11px] text-[#999] dark:text-[#555] tracking-[0.3px] mt-1 mb-0">
          Configure observation parameters and wavelength range below.
        </p>
      </div>

      <RangeSelectorPanel />
      <SpectralGraph />
    </div>
  );
}
