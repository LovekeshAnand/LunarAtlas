
import { BookOpen, Zap, Search } from 'lucide-react';

export default function ScientificBoard() {
  return (
    <div className="mt-12 mb-8 relative p-8 bg-[#fdfdfd] border-[3px] border-[#222] shadow-[8px_8px_0px_0px_rgba(0,0,0,0.1)] rounded-sm overflow-hidden min-h-[300px]">
      {/* Tape effects for the whiteboard look */}
      <div className="absolute -top-2 -left-2 w-12 h-6 bg-yellow-100/50 -rotate-12 border border-yellow-200/50" />
      <div className="absolute -top-2 -right-2 w-12 h-6 bg-yellow-100/50 rotate-12 border border-yellow-200/50" />
      
      <div className="relative z-10 flex flex-col md:flex-row gap-8">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-blue-100 rounded-full">
              <BookOpen size={20} className="text-blue-600" />
            </div>
            <h2 className="text-2xl font-black uppercase tracking-tighter text-[#111] italic">
              Scientific Principles: LIBS
            </h2>
          </div>
          
          <div className="space-y-4 text-[#333] leading-relaxed">
            <p className="font-medium text-lg leading-snug">
              <span className="bg-yellow-200 px-1">Laser-Induced Breakdown Spectroscopy (LIBS)</span> works by focusing a high-energy laser pulse onto a target. This creates a high-temperature <span className="underline decoration-blue-400 decoration-2">plasma plume</span>.
            </p>
            
            <div className="pl-4 border-l-4 border-blue-500 py-2 bg-blue-50/30">
              <p className="text-sm italic font-bold text-blue-900 uppercase tracking-widest mb-1">Researcher Note #01</p>
              <p className="text-sm">
                Each element has a "Spectral Fingerprint." As the plasma cools, electrons jump back to lower energy states, emitting light at specific wavelengths unique to each atom.
              </p>
            </div>

            <p className="text-sm text-gray-600">
                In this atlas, we map the Chandrayaan-3 lunar data against the standard <span className="font-bold">NIST Atomic Spectra Database</span>. By matching observed peaks to NIST reference lines, we can confirm the presence of Iron, Silicon, and other lunar minerals.
            </p>
          </div>
        </div>

        <div className="md:w-1/3 flex flex-col gap-4">
            <div className="p-5 border-2 border-dashed border-gray-300 rounded-lg bg-gray-50 flex items-start gap-4 hover:border-blue-400 transition-colors">
                <Zap className="shrink-0 text-yellow-500" />
                <div>
                   <h4 className="font-black text-xs uppercase tracking-widest mb-1 text-[#444]">High Energy Plasma</h4>
                   <p className="text-[11px] text-gray-500">Atomic transitions happen at &gt;10,000K, giving us enough light to read the chemical code.</p>
                </div>
            </div>

            <div className="p-5 border-2 border-dashed border-gray-300 rounded-lg bg-gray-50 flex items-start gap-4 hover:border-blue-400 transition-colors">
                <Search className="shrink-0 text-blue-500" />
                <div>
                   <h4 className="font-black text-xs uppercase tracking-widest mb-1 text-[#444]">NIST Backing</h4>
                   <p className="text-[11px] text-gray-500">We verify every peak against peer-reviewed atomic databases to ensure scientific integrity.</p>
                </div>
            </div>
            
            <div className="mt-auto bg-[#111] p-4 text-white rounded-sm">
                 <div className="text-[9px] uppercase tracking-[3px] text-gray-500 mb-2 font-bold">Calibration Active</div>
                 <div className="text-xl font-mono font-bold text-green-400">100% OK</div>
            </div>
        </div>
      </div>

      {/* Decorative board decorations */}
      <div className="absolute bottom-4 right-4 opacity-10">
          <div className="w-16 h-1 bg-black mb-1 rounded-full" />
          <div className="w-10 h-1 bg-black rounded-full ml-auto" />
      </div>
    </div>
  );
}
