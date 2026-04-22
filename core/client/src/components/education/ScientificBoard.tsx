
import { BookOpen, Zap, Search } from 'lucide-react';

export default function ScientificBoard() {
  return (
    <div className="mt-12 mb-8 relative p-8 bg-white border-2 border-dashed border-gray-400 shadow-[4px_6px_0px_0px_rgba(0,0,0,0.05)] rounded overflow-hidden min-h-[300px]">
      {/* Tape effects for the whiteboard look */}
      <div className="absolute -top-2 -left-2 w-16 h-8 bg-blue-100/60 -rotate-12 border border-blue-200/50" />
      <div className="absolute -bottom-2 -right-2 w-12 h-6 bg-yellow-100/60 -rotate-6 border border-yellow-200/50" />
      
      <div className="relative z-10 flex flex-col md:flex-row gap-8">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-[20px] font-marker font-bold text-blue-800 -rotate-1 origin-left">
              Scientific Principles: LIBS
            </h2>
          </div>
          
          <div className="space-y-4 font-caveat text-[14px] text-gray-800 leading-relaxed">
            <p className="leading-snug">
              <span className="bg-yellow-200 px-2 py-0.5 inline-block -rotate-1 rounded-sm shadow-sm font-bold">Laser-Induced Breakdown Spectroscopy</span> works by focusing a high-energy laser pulse onto a target. This creates a high-temperature <span className="underline decoration-blue-500 decoration-wavy decoration-2 text-blue-700">plasma plume</span>.
            </p>
            
            <div className="p-4 border-2 border-dashed border-red-300 bg-red-50/50 rotate-1 shadow-sm rounded">
              <p className="text-[13px] font-marker font-bold text-red-700 mb-2 underline decoration-red-300">Researcher Note #01:</p>
              <p className="text-[14px] leading-snug">
                Each element has a "Spectral Fingerprint." As the plasma cools, electrons jump back to lower energy states, emitting light at specific wavelengths unique to each atom.
              </p>
            </div>

            <p className="text-[14px] text-gray-700 leading-snug">
                In this atlas, we map the Chandrayaan-3 lunar data against the standard <strong className="font-sans text-[12px] font-black text-black inline-block underline decoration-2 decoration-blue-400">NIST Atomic Spectra Database</strong>. By matching observed peaks to NIST reference lines, we can confirm the presence of Iron, Silicon, and other minerals in the regolith. 
            </p>
          </div>
        </div>

        <div className="md:w-1/3 flex flex-col gap-6 pt-4">
            <div className="p-5 border-2 border-dashed border-blue-400 rounded-lg bg-blue-50/40 flex items-start flex-col gap-2 hover:bg-blue-50 transition-colors shadow-sm rotate-2">
                <h4 className="font-marker font-bold text-[14px] text-blue-800 underline decoration-blue-300">High Energy Plasma:</h4>
                <p className="text-[13px] font-caveat text-blue-900 leading-snug">Atomic transitions happen at &gt;10,000K, giving us enough light to read the chemical code.</p>
            </div>

            <div className="p-5 border-2 border-dashed border-green-400 rounded-lg bg-green-50/40 flex items-start flex-col gap-2 hover:bg-green-50 transition-colors shadow-sm -rotate-1">
                <h4 className="font-marker font-bold text-[14px] text-green-800 underline decoration-green-300">NIST Backing:</h4>
                <p className="text-[13px] font-caveat text-green-900 leading-snug">We verify every peak against peer-reviewed atomic databases to ensure scientific integrity.</p>
            </div>
        </div>
      </div>
    </div>
  );
}
