"""
Hybrid Architecture / ER Diagram for LunarAtlas Database
- mission -> instrument -> instrument_spec_libs -> dataset_version are shown
  as plain vertical labels (no boxes), connected by arrows.
- All downstream tables are drawn as standard ER-style boxes (header + PK/FK
  rows only, no full column list), each row carrying an example value so the
  reader can trace one concrete record (e.g. measurement_id = 3) through the
  whole pipeline.
- nist_lines remains a standalone, dashed lookup table with no FK link.
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --------------------------------------------------------------------------
# 1. STRUCTURE
# --------------------------------------------------------------------------

VERTICAL_CHAIN = ["mission", "instrument", "instrument_spec_libs", "dataset_version"]
VLABELS = {
    "mission": "MISSION",
    "instrument": "INSTRUMENT",
    "instrument_spec_libs": "INSTRUMENT_SPEC_LIBS",
    "dataset_version": "DATASET_VERSION",
}

MAIN_CHAIN = ["observation_session", "observation", "observation_file_info"]
BRANCH_TOP = ["measurement_raw", "spectral_data_raw"]
BRANCH_BOTTOM = ["measurement_clean", "spectral_data_clean"]
STANDALONE = ["nist_lines"]

TABLES = {
    "observation_session": [("PK", "session_id", "1"), ("FK", "dataset_version_id", "1")],
    "observation": [("PK", "observation_id", "1"), ("FK", "session_id", "1")],
    "observation_file_info": [("PK", "file_info_id", "1"), ("FK", "observation_id", "1")],
    "measurement_raw": [("PK", "measurement_id", "3"), ("FK", "file_info_id", "1")],
    "spectral_data_raw": [("PK", "spectral_data_id", "7"), ("FK", "measurement_id", "3")],
    "measurement_clean": [("PK", "measurement_id", "3"), ("FK", "file_info_id", "1")],
    "spectral_data_clean": [("PK", "spectral_data_id", "9"), ("FK", "measurement_id", "3")],
    "nist_lines": [("PK", "id", "1")],
}

LABELS = {
    "observation_session": "OBSERVATION_SESSION",
    "observation": "OBSERVATION",
    "observation_file_info": "OBSERVATION_FILE_INFO",
    "measurement_raw": "MEASUREMENT_RAW",
    "spectral_data_raw": "SPECTRAL_DATA_RAW",
    "measurement_clean": "MEASUREMENT_CLEAN",
    "spectral_data_clean": "SPECTRAL_DATA_CLEAN",
    "nist_lines": "NIST_LINES",
}

RELATIONS = [
    ("observation_session", "observation"),
    ("observation", "observation_file_info"),
    ("observation_file_info", "measurement_raw"),
    ("observation_file_info", "measurement_clean"),
    ("measurement_raw", "spectral_data_raw"),
    ("measurement_clean", "spectral_data_clean"),
]

# --------------------------------------------------------------------------
# 2. STYLE
# --------------------------------------------------------------------------

HEADER_BG = "#1c2b39"
HEADER_FG = "#ffffff"
ROW_BG_A = "#ffffff"
ROW_BG_B = "#eef2f5"
BORDER_DARK = "#42505b"
STANDALONE_BORDER = "#9aa5ad"
PK_COLOR = "#c1440e"
FK_COLOR = "#1f6fb2"
TEXT_COLOR = "#1b242c"
VAL_COLOR = "#1c2b39"
LINE_COLOR = "#3c4a56"
ACCENT = "#1c2b39"

MONO = "DejaVu Sans Mono"
SANS = "DejaVu Sans"

FS_VCHAIN = 17
FS_HEADER = 14
FS_ROW = 13
FS_TAG = 12

PAD_X = 0.18
ROW_H = 0.42
HEADER_H = 0.5
MIN_TABLE_W = 2.6

GAP_X_CHAIN = 0.7
GAP_X_BRANCH = 0.7
GAP_Y_BRANCH = 0.55
V_GAP = 0.85
MARGIN = 0.55

# --------------------------------------------------------------------------
# 3. TEXT MEASUREMENT
# --------------------------------------------------------------------------

_measure_fig = plt.figure()
_measure_renderer = _measure_fig.canvas.get_renderer()


def text_width_in(s, fontsize, family=SANS, weight="normal"):
    if s == "":
        return 0.0
    t = _measure_fig.text(0, 0, s, fontsize=fontsize, family=family, weight=weight)
    bbox = t.get_window_extent(renderer=_measure_renderer)
    t.remove()
    return bbox.width / _measure_fig.dpi


# --------------------------------------------------------------------------
# 4. AUTO-SIZE EACH BOX
# --------------------------------------------------------------------------

def size_table(name, rows):
    header_w = text_width_in(LABELS[name], FS_HEADER, family=SANS, weight="bold") + 2 * PAD_X
    max_row_w = 0.0
    for tag, col, val in rows:
        row_str_w = (text_width_in(tag, FS_TAG, family=MONO, weight="bold")
                     + 0.14
                     + text_width_in(col, FS_ROW, family=MONO, weight="bold")
                     + 0.3
                     + text_width_in(f"= {val}", FS_ROW, family=MONO, weight="bold"))
        max_row_w = max(max_row_w, row_str_w + 2 * PAD_X)
    w = max(header_w, max_row_w, MIN_TABLE_W)
    h = HEADER_H + ROW_H * len(rows)
    return w, h


SIZES = {name: size_table(name, rows) for name, rows in TABLES.items()}

# --------------------------------------------------------------------------
# 5. LAYOUT
# --------------------------------------------------------------------------

POS = {}

x_cursor = 0.0
for name in MAIN_CHAIN:
    w, h = SIZES[name]
    POS[name] = (x_cursor, -h / 2.0, w, h)
    x_cursor += w + GAP_X_CHAIN

main_chain_max_h = max(SIZES[n][1] for n in MAIN_CHAIN)
fi_x, fi_y, fi_w, fi_h = POS["observation_file_info"]
branch_x0 = fi_x + fi_w + GAP_X_BRANCH

top_branch_max_h = max(SIZES[n][1] for n in BRANCH_TOP)
y_center_top = main_chain_max_h / 2.0 + GAP_Y_BRANCH + top_branch_max_h / 2.0
xc = branch_x0
for name in BRANCH_TOP:
    w, h = SIZES[name]
    POS[name] = (xc, y_center_top - h / 2.0, w, h)
    xc += w + GAP_X_BRANCH

bottom_branch_max_h = max(SIZES[n][1] for n in BRANCH_BOTTOM)
y_center_bottom = -(main_chain_max_h / 2.0 + GAP_Y_BRANCH + bottom_branch_max_h / 2.0)
xc = branch_x0
for name in BRANCH_BOTTOM:
    w, h = SIZES[name]
    POS[name] = (xc, y_center_bottom - h / 2.0, w, h)
    xc += w + GAP_X_BRANCH

nist_w, nist_h = SIZES["nist_lines"]
obs_sess_x, obs_sess_y, obs_sess_w, obs_sess_h = POS["observation_session"]
nist_y_bottom = max(obs_sess_y + obs_sess_h, y_center_top + top_branch_max_h / 2.0) + 0.35
POS["nist_lines"] = (obs_sess_x, nist_y_bottom, nist_w, nist_h)

# --- plain vertical-text chain, dataset_version aligned to y=0 ---
VPOS = {}
vy = 0.0
for name in reversed(VERTICAL_CHAIN):
    VPOS[name] = vy
    vy += V_GAP

v_label_max_w = max(text_width_in(VLABELS[n], FS_VCHAIN, family=SANS, weight="bold")
                     for n in VERTICAL_CHAIN)
v_chain_width = v_label_max_w + 0.9

all_x0 = min(p[0] for p in POS.values())
all_y0 = min(p[1] for p in POS.values())

shift_x = MARGIN + v_chain_width - all_x0
shift_y = MARGIN - all_y0
for name in POS:
    x, y, w, h = POS[name]
    POS[name] = (x + shift_x, y + shift_y, w, h)
for name in VPOS:
    VPOS[name] = VPOS[name] + shift_y

v_label_x = MARGIN

all_y0b = min(p[1] for p in POS.values())
all_y1b = max(p[1] + p[3] for p in POS.values())
v_top = max(VPOS.values())
v_bottom = min(VPOS.values())

FIG_W = max(p[0] + p[2] for p in POS.values()) + MARGIN
top_extent = max(all_y1b, v_top + 0.4)
bottom_extent = min(all_y0b, v_bottom - 0.4)
FIG_H = (top_extent - bottom_extent) + 2 * MARGIN

y_offset = MARGIN - bottom_extent
for name in POS:
    x, y, w, h = POS[name]
    POS[name] = (x, y + y_offset, w, h)
for name in VPOS:
    VPOS[name] = VPOS[name] + y_offset

# --------------------------------------------------------------------------
# 6. DRAW
# --------------------------------------------------------------------------

plt.close(_measure_fig)
fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=300)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.axis("off")
fig.patch.set_facecolor("white")


def draw_table(ax, name, rows, x, y, w, h, dashed=False):
    edge_color = STANDALONE_BORDER if dashed else BORDER_DARK
    ls = (0, (4, 2)) if dashed else "solid"

    body = patches.FancyBboxPatch(
        (x, y), w, h - HEADER_H,
        boxstyle="round,pad=0,rounding_size=0.05",
        linewidth=1.3, edgecolor=edge_color, facecolor=ROW_BG_A,
        linestyle=ls, zorder=2,
    )
    ax.add_patch(body)

    for i, (tag, col, val) in enumerate(rows):
        row_y_top = y + (h - HEADER_H) - i * ROW_H
        row_y_bot = row_y_top - ROW_H
        if i % 2 == 1:
            ax.add_patch(patches.Rectangle((x, row_y_bot), w, ROW_H, linewidth=0,
                                            facecolor=ROW_BG_B, zorder=2.1))
        if i > 0:
            ax.plot([x, x + w], [row_y_top, row_y_top], color="#d7dde1", lw=0.8, zorder=2.2)

        row_y_c = (row_y_top + row_y_bot) / 2.0
        tag_color = PK_COLOR if tag == "PK" else FK_COLOR
        ax.text(x + PAD_X, row_y_c, tag, fontsize=FS_TAG, family=MONO, fontweight="bold",
                 color=tag_color, va="center", ha="left", zorder=3)
        tag_w = text_width_in(tag, FS_TAG, family=MONO, weight="bold")
        ax.text(x + PAD_X + tag_w + 0.14, row_y_c, col, fontsize=FS_ROW, family=MONO,
                 fontweight="bold", color=TEXT_COLOR, va="center", ha="left", zorder=3)
        ax.text(x + w - PAD_X, row_y_c, f"= {val}", fontsize=FS_ROW, family=MONO,
                 color=VAL_COLOR, va="center", ha="right", zorder=3, fontweight="bold")
        if tag == "PK":
            ax.plot([x, x + w], [row_y_bot, row_y_bot], color=PK_COLOR, lw=1.2,
                     zorder=2.3, alpha=0.55)

    header = patches.FancyBboxPatch(
        (x, y + h - HEADER_H), w, HEADER_H,
        boxstyle="round,pad=0,rounding_size=0.05",
        linewidth=1.3, edgecolor=edge_color, facecolor=HEADER_BG,
        linestyle=ls, zorder=4,
    )
    ax.add_patch(header)
    ax.add_patch(patches.Rectangle((x, y + h - HEADER_H), w, HEADER_H / 2,
                                    linewidth=0, facecolor=HEADER_BG, zorder=3.9))
    ax.text(x + w / 2.0, y + h - HEADER_H / 2.0, LABELS[name], fontsize=FS_HEADER,
            family=SANS, fontweight="bold", color=HEADER_FG, va="center", ha="center", zorder=5)

    if dashed:
        ax.text(x + w / 2.0, y + h + 0.14, "standalone reference \u00b7 no FK",
                fontsize=8.5, family=SANS, color=STANDALONE_BORDER, style="italic",
                ha="center", va="bottom")


for name in MAIN_CHAIN + BRANCH_TOP + BRANCH_BOTTOM:
    x, y, w, h = POS[name]
    draw_table(ax, name, TABLES[name], x, y, w, h)
for name in STANDALONE:
    x, y, w, h = POS[name]
    draw_table(ax, name, TABLES[name], x, y, w, h, dashed=True)

# --- plain vertical-text chain ---------------------------------------------

for name in VERTICAL_CHAIN:
    ax.text(v_label_x, VPOS[name], VLABELS[name], fontsize=FS_VCHAIN, family=SANS,
             fontweight="bold", color=ACCENT, ha="left", va="center", zorder=5)

v_text_widths = {n: text_width_in(VLABELS[n], FS_VCHAIN, family=SANS, weight="bold")
                  for n in VERTICAL_CHAIN}


def arrow(ax, p1, p2, color=LINE_COLOR, lw=2.0, mutation_scale=16):
    ax.annotate("", xy=p2, xytext=p1,
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                 mutation_scale=mutation_scale, shrinkA=2, shrinkB=2),
                zorder=3)


for i in range(len(VERTICAL_CHAIN) - 1):
    upper = VERTICAL_CHAIN[i]
    lower = VERTICAL_CHAIN[i + 1]
    p1 = (v_label_x + v_text_widths[upper] / 2.0, VPOS[upper] - 0.18)
    p2 = (v_label_x + v_text_widths[lower] / 2.0, VPOS[lower] + 0.18)
    arrow(ax, p1, p2)

ds_y = VPOS["dataset_version"]
obs_sess_x2, obs_sess_y2, obs_sess_w2, obs_sess_h2 = POS["observation_session"]
p1 = (v_label_x + v_text_widths["dataset_version"] + 0.18, ds_y)
p2 = (obs_sess_x2, obs_sess_y2 + obs_sess_h2 / 2.0)
arrow(ax, p1, p2, lw=2.2, mutation_scale=18)

# --- ER box-to-box relationship arrows -------------------------------------


def right_mid(name):
    x, y, w, h = POS[name]
    return np.array([x + w, y + h / 2.0])


def left_mid(name):
    x, y, w, h = POS[name]
    return np.array([x, y + h / 2.0])


def route(ax, p_name, c_name, color=LINE_COLOR):
    p1 = right_mid(p_name)
    p2 = left_mid(c_name)
    if abs(p1[1] - p2[1]) < 1e-6:
        path_pts = [p1, p2]
    else:
        midx = p1[0] + (p2[0] - p1[0]) * 0.5
        path_pts = [p1, (midx, p1[1]), (midx, p2[1]), p2]
    xs = [pt[0] for pt in path_pts]
    ys = [pt[1] for pt in path_pts]
    ax.plot(xs, ys, color=color, lw=2.0, zorder=2.5, solid_joinstyle="round")
    ax.annotate("", xy=path_pts[-1], xytext=path_pts[-2],
                arrowprops=dict(arrowstyle="-|>", color=color, lw=2.0,
                                 mutation_scale=16), zorder=2.6)


for parent, child in RELATIONS:
    route(ax, parent, child)

output_path = "/mnt/user-data/outputs/fig7_database_schema_hybrid.png"
os.makedirs(os.path.dirname(output_path), exist_ok=True)
fig.savefig(output_path, dpi=300, facecolor="white")
plt.close(fig)
print(f"[SUCCESS] Hybrid diagram saved to {os.path.abspath(output_path)}  ({FIG_W:.2f}in x {FIG_H:.2f}in)")