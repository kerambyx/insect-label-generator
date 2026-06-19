import csv
import sys
import os
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ==========================================
# CONFIGURATION
# ==========================================
CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else "labels.csv"
OUTPUT   = os.path.splitext(CSV_PATH)[0] + "_labels.pdf"

# --- Font Customization ---
USE_CUSTOM_FONT = False
FONT_NAME        = "Charter"
FONT_FILE_REG   = "Charter Regular.ttf"         # Standard style font file
FONT_FILE_ITALIC = "Charter Italic.ttf"  # Italic style font file (for species)

# Fallback fonts if USE_CUSTOM_FONT is False
FALLBACK_REG    = "Courier" 
FALLBACK_ITALIC = "Courier-Oblique"

# --- Label Layout Metrics ---
LW, LH = 27 * mm, 10 * mm # Label width and height
# 5pt font and 27mm x 10mm labels are far larger than would be used in any professional capacity but my printer resolution isn't very high and the larger labels are more pleasing to me - worth the space tradeoff 
PAGE_W, PAGE_H = LETTER
MARGIN_X, MARGIN_Y = 10 * mm, 10 * mm
GAP_X, GAP_Y, PAIR_GAP = 2 * mm, 1 * mm, 3.0 * mm

# --- Font Sizing ---
FS_DEFAULT = 5.0   # Starting target font size (pt)
FS_MIN     = 4.0   # Floor limit. Font will never shrink smaller than this

# --- Grid Metrics ---
COLS     = int((PAGE_W - 2 * MARGIN_X + GAP_X) // (LW + GAP_X))
ROW_STEP = LH + LH + PAIR_GAP + GAP_Y
PAD_X    = 0.65 * mm
PAD_Y    = 0.5 * mm
MAX_TW   = LW - 2 * PAD_X


# ===============
# INITIALIZATION
# ===============
def register_fonts():
    # Registers font based on configuration.
    if USE_CUSTOM_FONT:
        try:
            pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_FILE_REG))
            pdfmetrics.registerFont(TTFont(f"{FONT_NAME}-Italic", FONT_FILE_ITALIC))
            return FONT_NAME, f"{FONT_NAME}-Italic"
        except Exception as e:
            print(f"Warning: Could not load custom fonts ({e}). Falling back to Helvetica.")
    
    return FALLBACK_REG, FALLBACK_ITALIC

REG_FONT, ITALIC_FONT = register_fonts()


# ==========================================
# GENERATION ENGINE FUNCTIONS
# ==========================================
def fit_size(text, font, max_w, start=FS_DEFAULT):
    # Shrink font size until text fits, down to FS_MIN.
    fs = start
    while fs >= FS_MIN and stringWidth(text, font, fs) > max_w:
        fs -= 0.05
    return fs


def draw_label(c, x, y, lines):
    # Outlines one individual label
    p = c.beginPath()
    p.rect(x + 0.15, y + 0.15, LW - 0.3, LH - 0.3)
    c.saveState()
    c.clipPath(p, stroke=0, fill=0)

    n = len(lines)
    if n:
        usable = LH - (2 * PAD_Y)
        step   = usable / n
        for i, (text, font) in enumerate(lines):
            if not text.strip():
                continue
                
            fs = fit_size(text, font, MAX_TW)
            # Alignment to keep lower text bounds within boundaries
            ty = y + LH - PAD_Y - (step * i) - (fs * 0.85)
            c.setFont(font, fs)
            c.setFillColor(colors.black)
            c.drawString(x + PAD_X, ty, text)

    c.restoreState()
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.3)
    c.rect(x, y, LW, LH)


def draw_locality(c, x, y, row):
    # Formats and prints the data label.
    country, province, city, locality, lat, lon, elevation, date, collector = row
    
    prov_city = f"{province}, {city}" if province and city else (province or city)
    country_line = f"{country}: {prov_city}" if country and prov_city else (country or prov_city)
    
    date_line    = "  ".join(filter(None, [date, collector]))
    coords_parts = [p for p in [lat, lon] if p]
    if elevation:
        coords_parts.append(f"{elevation} m")
    coords_line  = "  ".join(coords_parts)
    
    lines = [
        (country_line, REG_FONT),
        (locality,     REG_FONT),
        (coords_line,  REG_FONT),
        (date_line,    REG_FONT),
    ]
    draw_label(c, x, y, lines)


def draw_id(c, x, y, row):
    # Formats and prints the identification label
    order, family, genus, species, det = row
    order_family  = ": ".join(filter(None, [order, family]))
    genus_species = " ".join(filter(None, [genus, species]))
    
    lines = [
        (order_family,  REG_FONT),
        (genus_species, ITALIC_FONT), 
        (det,           REG_FONT),
    ]
    draw_label(c, x, y, lines)


def load_csv(path):
    # Reads elements from CSV.
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = []
        for r in csv.DictReader(f):
            g = lambda k: r.get(k, "").strip()
            loc = (g("country").upper(), g("province"), g("city"), g("locality"),
                   g("latitude"), g("longitude"), g("elevation"),
                   g("date"), g("collector"))
            idd = (g("order").upper(), g("family"), g("genus"), g("species"), g("det"))
            rows.append((loc, idd))
    return rows


def generate(specimens, out):
    # Builds layout sheets and populates the remaining slots with empty templates for handwritten field labels.
    if os.path.dirname(out):
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        
    c = canvas.Canvas(out, pagesize=LETTER)
    c.setTitle("Insect Labels")
    col, row_y = 0, PAGE_H - MARGIN_Y - LH

    # 1. Output true specimens from CSV
    for loc_row, id_row in specimens:
        x     = MARGIN_X + col * (LW + GAP_X)
        loc_y = row_y
        id_y  = row_y - LH - PAIR_GAP

        if id_y < MARGIN_Y:
            c.showPage()
            col, row_y = 0, PAGE_H - MARGIN_Y - LH
            x     = MARGIN_X
            loc_y = row_y
            id_y  = row_y - LH - PAIR_GAP

        draw_locality(c, x, loc_y, loc_row)
        draw_id(c, x, id_y, id_row)

        col += 1
        if col >= COLS:
            col    = 0
            row_y -= ROW_STEP

    # 2. Fill the remainder of the current sheet with blanks
    while row_y - LH - PAIR_GAP >= MARGIN_Y:
        x     = MARGIN_X + col * (LW + GAP_X)
        loc_y = row_y
        id_y  = row_y - LH - PAIR_GAP

        draw_locality(c, x, loc_y, ("", "", "", "", "", "", "", "", ""))
        draw_id(c, x, id_y, ("", "", "", "", ""))

        col += 1
        if col >= COLS:
            col    = 0
            row_y -= ROW_STEP
            
        if row_y - LH - PAIR_GAP < MARGIN_Y and col == 0:
            break

    c.save()
    print(f"{len(specimens)} parsed specimen records → {out} ({COLS} columns, US Letter)")


if __name__ == "__main__":
    generate(load_csv(CSV_PATH), OUTPUT)
