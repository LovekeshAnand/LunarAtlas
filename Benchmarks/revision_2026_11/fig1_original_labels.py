"""Figure 1 for the revision: the ORIGINAL vector figure (publication_figures/fig1_architecture.pdf), unchanged
except for three text labels that contradicted the code:
  - viewer box   "(SVG Graphics Canvas)"            -> "(browser-side LTTB+Peaks)"
  - API bullet   "LTTB + Peaks Downsampling Engine" -> "LTTB + Peaks Downsampling (API clients)"
  - API->viewer  "Responds with denoised, / downsampled data" -> "Full-resolution spectra / (optionally denoised)"
(the web viewer fetches full-resolution spectra and downsamples in the browser; server-side downsampling serves
API clients). Only the text of these spans is removed (vector graphics kept) and re-set in Helvetica at the same
size, weight, colour and position. Writes publication_figures/fig1_architecture_rev.{pdf,png}.
usage: python -P fig1_original_labels.py
"""
import fitz

SRC, OUT = "publication_figures/fig1_architecture.pdf", "publication_figures/fig1_architecture_rev"
NEW = {  # old span text -> (new text, alignment)
    "(SVG Graphics Canvas)": ("(browser-side LTTB+Peaks)", "center"),
    "LTTB + Peaks Downsampling Engine": ("LTTB + Peaks Downsampling (API clients)", "left"),
    "Responds with denoised,": ("Full-resolution spectra", "left"),
    "downsampled data": ("(optionally denoised)", "left"),
}
doc = fitz.open(SRC); page = doc[0]
spans = [s for b in page.get_text("rawdict")["blocks"] for l in b.get("lines", []) for s in l["spans"]]
todo = []
for old, (new, align) in NEW.items():
    hit = [s for s in spans if "".join(c["c"] for c in s["chars"]).strip().endswith(old)]
    assert len(hit) == 1, (old, len(hit))
    s = hit[0]
    chars = [c for c in s["chars"]][-len(old):]          # only the label characters (keeps a leading bullet)
    r = fitz.Rect(chars[0]["bbox"][0], s["bbox"][1], chars[-1]["bbox"][2], s["bbox"][3])
    cut = fitz.Rect(r.x0, r.y0 + 2.5, r.x1, r.y1 - 2.5)  # inset: line boxes overlap the neighbouring line
    page.add_redact_annot(cut, fill=False)
    todo.append((s, r, new, align))
page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE)
for s, r, new, align in todo:
    bold = "Bold" in s["font"] or "Black" in s["font"]
    font = "hebo" if bold else "helv"
    w = fitz.get_text_length(new, fontname=font, fontsize=s["size"])
    x = (r.x0 + r.x1 - w) / 2 if align == "center" else r.x0
    c = s["color"]; rgb = ((c >> 16) & 255) / 255, ((c >> 8) & 255) / 255, (c & 255) / 255
    page.insert_text((x, s["origin"][1]), new, fontname=font, fontsize=s["size"], color=rgb)
doc.save(OUT + ".pdf", garbage=3, deflate=True)
page.get_pixmap(dpi=300).save(OUT + ".png")
print("written", OUT + ".{pdf,png}")
