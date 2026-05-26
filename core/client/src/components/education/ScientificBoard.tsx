
export default function ScientificBoard() {
  return (
    <div className="mt-12 mb-8 relative p-8 bg-white border border-solid border-gray-200 shadow-sm rounded-md overflow-hidden min-h-[300px]">
      
      <div className="relative z-10 flex flex-col md:flex-row gap-8">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-[20px] font-sans font-semibold text-gray-900">
              Scientific Principles: LIBS
            </h2>
          </div>
          
          <div className="space-y-4 font-sans text-[14px] text-gray-700 leading-relaxed">
            <p className="leading-snug">
              <span className="bg-gray-100 px-2 py-0.5 inline-block rounded-sm font-medium">Laser-Induced Breakdown Spectroscopy</span> works by focusing a high-energy laser pulse onto a target. This creates a high-temperature <span className="underline decoration-blue-300 decoration-solid decoration-2 text-blue-600">plasma plume</span>.
            </p>
            
            <div className="p-4 border border-solid border-gray-200 bg-gray-50 rounded-sm">
              <p className="text-[13px] font-sans font-semibold text-gray-800 mb-2">Researcher Note #01:</p>
              <p className="text-[14px] leading-snug">
                Each element has a "Spectral Fingerprint." As the plasma cools, electrons jump back to lower energy states, emitting light at specific wavelengths unique to each atom.
              </p>
            </div>

            <p className="text-[14px] text-gray-700 leading-snug">
                In this atlas, we map the Chandrayaan-3 lunar data against the standard <strong className="font-sans text-[13px] font-bold text-gray-900 inline-block underline decoration-2 decoration-gray-300">NIST Atomic Spectra Database</strong>. By matching observed peaks to NIST reference lines, we can confirm the presence of Iron, Silicon, and other minerals in the regolith. 
            </p>
          </div>
        </div>

        <div className="md:w-1/3 flex flex-col gap-6 pt-4">
            <div className="p-4 border border-solid border-gray-200 rounded bg-white flex items-start flex-col gap-2 hover:bg-gray-50 transition-colors shadow-sm">
                <h4 className="font-sans font-semibold text-[14px] text-gray-800">High Energy Plasma:</h4>
                <p className="text-[13px] font-sans text-gray-600 leading-snug">Atomic transitions happen at &gt;10,000K, giving us enough light to read the chemical code.</p>
            </div>

            <div className="p-4 border border-solid border-gray-200 rounded bg-white flex items-start flex-col gap-2 hover:bg-gray-50 transition-colors shadow-sm">
                <h4 className="font-sans font-semibold text-[14px] text-gray-800">NIST Backing:</h4>
                <p className="text-[13px] font-sans text-gray-600 leading-snug">We verify every peak against peer-reviewed atomic databases to ensure scientific integrity.</p>
            </div>
        </div>
      </div>
    </div>
  );
}
