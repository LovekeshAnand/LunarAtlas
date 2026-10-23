// Runs the web viewer's own TypeScript LTTB (core/client/src/workers/downsampleWorker.ts) and its
// own target list (ELEMENT_PEAKS in core/client/src/utils/spectralUtils.ts) under Node >= 22.6
// (native type stripping). stdin: JSON [{key, wavelength[], intensity[], threshold, targets|null}]
// stdout: JSON {viewer_targets: [...], results: {key: [indices]}}
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import { resolve } from "node:path";

const src = resolve(import.meta.dirname, "../core/client/src");
const { lttb } = await import(pathToFileURL(`${src}/workers/downsampleWorker.ts`));
const { ALL_PEAK_WAVELENGTHS } = await import(pathToFileURL(`${src}/utils/spectralUtils.ts`));

const jobs = JSON.parse(readFileSync(0, "utf8"));
const results = {};
for (const j of jobs) {
  const data = j.wavelength.map((w, i) => ({ wavelength: w, intensity: j.intensity[i], index: i }));
  const targets = j.targets === "viewer" ? ALL_PEAK_WAVELENGTHS : j.targets ?? undefined;
  results[j.key] = lttb(data, j.threshold, targets).map((p) => p.index);
}
process.stdout.write(JSON.stringify({ viewer_targets: ALL_PEAK_WAVELENGTHS, results }));
