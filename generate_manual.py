#!/usr/bin/env python3
"""Generate Spaluter manual PDF — pulsar synthesis plugin for disting NT."""

import math
import os
import random

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import Color, black, white, HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable, Flowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.graphics.shapes import (
    Drawing, Line, Rect, String, Circle, Group, Polygon
)
from reportlab.graphics import renderPDF

# ============================================================
# Colors — matched to website palette
# ============================================================
COL_PULSARET = HexColor('#44aaff')
COL_WINDOW = HexColor('#ffaa22')
COL_F2 = HexColor('#ff6644')
COL_F3 = HexColor('#44dd88')
COL_LABEL = HexColor('#999999')
COL_DARK = HexColor('#333344')
COL_BG_DARK = HexColor('#0f0f1a')
COL_BG_DARK2 = HexColor('#141428')
COL_SILENCE = HexColor('#1a1a2e')

ACCENT = HexColor('#44aaff')
ACCENT_DARK = HexColor('#2266aa')
BODY_TEXT = HexColor('#333333')
MID_GRAY = HexColor('#666666')
LIGHT_GRAY = HexColor('#999999')
VERY_LIGHT = HexColor('#DDDDDD')
TABLE_HEADER_BG = HexColor('#1a2a44')
TABLE_HEADER_TEXT = HexColor('#88bbee')
TABLE_ROW_ALT = HexColor('#f4f7fb')
TABLE_BORDER = HexColor('#cccccc')

OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'spaluter_manual.pdf')
PAGE_W = letter[0] - 1.5 * inch  # usable width with 0.75in margins


# ============================================================
# Styles
# ============================================================

def make_styles():
    ss = getSampleStyleSheet()
    styles = {}
    styles['title'] = ParagraphStyle(
        'Title', parent=ss['Title'], fontSize=32, spaceAfter=8,
        textColor=ACCENT, fontName='Helvetica-Bold', alignment=TA_LEFT)
    styles['subtitle'] = ParagraphStyle(
        'Subtitle', parent=ss['Normal'], fontSize=14, spaceAfter=24,
        textColor=LIGHT_GRAY, fontName='Helvetica', alignment=TA_LEFT)
    styles['h1'] = ParagraphStyle(
        'H1', parent=ss['Heading1'], fontSize=20, spaceBefore=28,
        spaceAfter=12, textColor=HexColor('#1a1a4e'), fontName='Helvetica-Bold',
        alignment=TA_LEFT)
    styles['h2'] = ParagraphStyle(
        'H2', parent=ss['Heading2'], fontSize=14, spaceBefore=18,
        spaceAfter=8, textColor=ACCENT_DARK, fontName='Helvetica-Bold',
        alignment=TA_LEFT)
    styles['h3'] = ParagraphStyle(
        'H3', parent=ss['Heading3'], fontSize=11, spaceBefore=12,
        spaceAfter=6, textColor=HexColor('#3377aa'), fontName='Helvetica-Bold',
        alignment=TA_LEFT)
    styles['body'] = ParagraphStyle(
        'Body', parent=ss['Normal'], fontSize=10, spaceAfter=8,
        leading=14.5, fontName='Helvetica', textColor=BODY_TEXT,
        alignment=TA_LEFT)
    styles['body_tight'] = ParagraphStyle(
        'BodyTight', parent=styles['body'], spaceAfter=4, leading=13)
    styles['bullet'] = ParagraphStyle(
        'Bullet', parent=ss['Normal'], fontSize=10, spaceAfter=4,
        leading=14, leftIndent=20, bulletIndent=8, fontName='Helvetica',
        textColor=BODY_TEXT, alignment=TA_LEFT)
    styles['caption'] = ParagraphStyle(
        'Caption', parent=ss['Normal'], fontSize=9, spaceAfter=14,
        textColor=MID_GRAY, fontName='Helvetica-Oblique', alignment=TA_LEFT)
    styles['tldr_body'] = ParagraphStyle(
        'TldrBody', parent=ss['Normal'], fontSize=10, spaceAfter=3,
        leading=13.5, fontName='Helvetica', textColor=BODY_TEXT,
        leftIndent=12, bulletIndent=4, alignment=TA_LEFT)
    styles['toc_title'] = ParagraphStyle(
        'TocTitle', parent=ss['Heading1'], fontSize=18, spaceBefore=0,
        spaceAfter=12, textColor=HexColor('#1a1a4e'), fontName='Helvetica-Bold',
        alignment=TA_LEFT)
    styles['toc_entry'] = ParagraphStyle(
        'TocEntry', parent=ss['Normal'], fontSize=10, spaceAfter=2,
        leading=14, fontName='Helvetica', textColor=BODY_TEXT,
        leftIndent=8, alignment=TA_LEFT)
    styles['toc_entry_sub'] = ParagraphStyle(
        'TocEntrySub', parent=styles['toc_entry'], fontSize=9,
        leftIndent=24, leading=13)
    return styles


# ============================================================
# Waveform math helpers
# ============================================================

def sinc_func(x):
    if abs(x) < 0.001:
        return 1.0
    return math.sin(math.pi * x) / (math.pi * x)


def pulsaret_sinc(phase, formant_mult=1.0):
    x = (phase - 0.5) * 6 * formant_mult
    return sinc_func(x)


def gaussian_window(phase):
    x = (phase - 0.5) * 2
    return math.exp(-6 * x * x)


def hann_window(phase):
    return 0.5 * (1 - math.cos(2 * math.pi * phase))


def waveform_sample(idx, t):
    """Return sample value for pulsaret waveform idx at phase t (0..1)."""
    if idx == 0:
        return math.sin(2 * math.pi * t)
    elif idx == 1:
        return math.sin(2 * math.pi * t * 2)
    elif idx == 2:
        return math.sin(2 * math.pi * t * 3)
    elif idx == 3:
        x2 = (t - 0.5) * 8
        return math.sin(math.pi * x2) / (math.pi * x2) if abs(x2) > 0.001 else 1.0
    elif idx == 4:
        return 4 * abs(t - 0.5) - 1
    elif idx == 5:
        return 2 * t - 1
    elif idx == 6:
        return 1.0 if t < 0.5 else -1.0
    elif idx == 7:
        return math.sin(2 * math.pi * t * 4) * math.exp(-3 * t)
    elif idx == 8:
        return math.exp(-20 * t)
    elif idx == 9:
        return random.random() * 2 - 1
    return 0.0


def window_sample(idx, t):
    """Return sample value for window function idx at phase t (0..1)."""
    if idx == 0:
        return 1.0
    elif idx == 1:
        return math.exp(-8 * (t - 0.5) ** 2)
    elif idx == 2:
        return 0.5 * (1 - math.cos(2 * math.pi * t))
    elif idx == 3:
        return math.exp(-5 * t)
    elif idx == 4:
        return 1.0 - t
    return 0.0


# ============================================================
# Drawing helpers
# ============================================================

def draw_dark_waveform_box(d, x, y, w, h):
    """Draw a dark rounded rectangle background for waveform diagrams."""
    d.add(Rect(x, y, w, h, fillColor=COL_BG_DARK, strokeColor=COL_DARK,
               strokeWidth=0.5, rx=4, ry=4))


def draw_waveform_line(d, points, color, width=1.5):
    """Draw a polyline from list of (x,y) tuples."""
    for i in range(len(points) - 1):
        d.add(Line(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1],
                    strokeColor=color, strokeWidth=width))


def draw_baseline(d, x, y, w, color=None):
    if color is None:
        color = HexColor('#333355')
    d.add(Line(x, y, x + w, y, strokeColor=color, strokeWidth=0.5))


def draw_arrow_down(d, x, y1, y2, color=None):
    """Draw downward arrow from y1 to y2 (y1 > y2 in ReportLab coords)."""
    if color is None:
        color = MID_GRAY
    d.add(Line(x, y1, x, y2, strokeColor=color, strokeWidth=0.8))
    d.add(Polygon(
        points=[x, y2, x - 3, y2 + 6, x + 3, y2 + 6],
        fillColor=color, strokeColor=color, strokeWidth=0))


def draw_arrow_right(d, x1, y, x2, color=None):
    if color is None:
        color = MID_GRAY
    d.add(Line(x1, y, x2, y, strokeColor=color, strokeWidth=0.8))
    d.add(Polygon(
        points=[x2, y, x2 - 6, y + 3, x2 - 6, y - 3],
        fillColor=color, strokeColor=color, strokeWidth=0))


def draw_rounded_box(d, x, y, w, h, fill, stroke, label, font_size=8, text_color=None):
    """Draw a rounded rectangle with centered label."""
    if text_color is None:
        text_color = HexColor('#eeeeee')
    d.add(Rect(x, y, w, h, fillColor=fill, strokeColor=stroke,
               strokeWidth=0.8, rx=4, ry=4))
    d.add(String(x + w / 2, y + h / 2 - font_size * 0.35, label,
                 fontSize=font_size, fillColor=text_color,
                 fontName='Helvetica', textAnchor='middle'))


# ============================================================
# Small inline waveform drawings for pulsaret/window tables
# ============================================================

def make_inline_waveform(idx, is_window=False):
    """Return a small Drawing (60x30) showing one waveform shape."""
    w, h = 60, 30
    d = Drawing(w, h)
    d.add(Rect(0, 0, w, h, fillColor=COL_BG_DARK, strokeColor=COL_DARK,
               strokeWidth=0.3, rx=2, ry=2))
    mid_y = h / 2
    d.add(Line(2, mid_y, w - 2, mid_y, strokeColor=HexColor('#333355'), strokeWidth=0.3))

    color = COL_WINDOW if is_window else COL_PULSARET
    amp = h * 0.38
    npts = 50
    random.seed(42 + idx)
    points = []
    for i in range(npts):
        t = float(i) / (npts - 1)
        if is_window:
            s = window_sample(idx, t)
            px = 2 + t * (w - 4)
            py = 2 + s * (h - 4)  # window goes up from bottom
        else:
            s = waveform_sample(idx, t)
            px = 2 + t * (w - 4)
            py = mid_y + s * amp
        points.append((px, py))
    draw_waveform_line(d, points, color, 1.2)
    return d


# ============================================================
# Stage diagrams matching website progression
# ============================================================

def draw_stage_pulsaret():
    """Stage 1: Single pulsaret (sinc waveform) on dark background."""
    w, h = int(PAGE_W), 140
    d = Drawing(w, h)
    draw_dark_waveform_box(d, 0, 0, w, h)

    # Title
    d.add(String(20, h - 18, 'Stage 1: Pulsaret', fontSize=11,
                 fillColor=COL_PULSARET, fontName='Helvetica-Bold'))
    d.add(String(20, h - 32, 'The raw burst shape (sinc waveform)',
                 fontSize=9, fillColor=COL_LABEL))

    cx = w / 2
    baseline = 45
    pulse_w = 300
    pulse_h = 55
    draw_baseline(d, cx - pulse_w / 2, baseline, pulse_w)

    # Draw sinc pulsaret
    npts = 200
    points = []
    for i in range(npts):
        t = float(i) / (npts - 1)
        s = pulsaret_sinc(t, 1.0)
        px = cx - pulse_w / 2 + t * pulse_w
        py = baseline + s * pulse_h
        points.append((px, py))
    draw_waveform_line(d, points, COL_PULSARET, 2.0)

    # Label arrow
    d.add(String(cx + pulse_w / 2 + 10, baseline + pulse_h * 0.6,
                 'pulsaret', fontSize=9, fillColor=COL_LABEL))
    return d


def draw_stage_window():
    """Stage 2: Pulsaret with Gaussian window overlay."""
    w, h = int(PAGE_W), 140
    d = Drawing(w, h)
    draw_dark_waveform_box(d, 0, 0, w, h)

    d.add(String(20, h - 18, 'Stage 2: Window', fontSize=11,
                 fillColor=COL_WINDOW, fontName='Helvetica-Bold'))
    d.add(String(20, h - 32, 'Gaussian envelope shapes each burst\'s amplitude',
                 fontSize=9, fillColor=COL_LABEL))

    cx = w / 2
    baseline = 45
    pulse_w = 300
    pulse_h = 55

    draw_baseline(d, cx - pulse_w / 2, baseline, pulse_w)

    # Windowed pulsaret
    npts = 200
    points = []
    for i in range(npts):
        t = float(i) / (npts - 1)
        s = pulsaret_sinc(t, 1.0) * gaussian_window(t)
        px = cx - pulse_w / 2 + t * pulse_w
        py = baseline + s * pulse_h
        points.append((px, py))
    draw_waveform_line(d, points, COL_PULSARET, 2.0)

    # Window envelope (dashed)
    win_pts = []
    for i in range(npts):
        t = float(i) / (npts - 1)
        s = gaussian_window(t)
        px = cx - pulse_w / 2 + t * pulse_w
        py = baseline + s * pulse_h
        win_pts.append((px, py))
    for i in range(len(win_pts) - 1):
        d.add(Line(win_pts[i][0], win_pts[i][1],
                    win_pts[i + 1][0], win_pts[i + 1][1],
                    strokeColor=COL_WINDOW, strokeWidth=1.5,
                    strokeDashArray=[5, 3]))

    d.add(String(cx + pulse_w / 2 + 10, baseline + pulse_h * 0.7,
                 'window', fontSize=9, fillColor=COL_WINDOW))
    return d


def draw_stage_train():
    """Stage 3: Pulsar train — multiple pulsarets at fundamental frequency."""
    w, h = int(PAGE_W), 140
    d = Drawing(w, h)
    draw_dark_waveform_box(d, 0, 0, w, h)

    d.add(String(20, h - 18, 'Stage 3: Train', fontSize=11,
                 fillColor=COL_PULSARET, fontName='Helvetica-Bold'))
    d.add(String(20, h - 32, 'Repetition rate = fundamental frequency (pitch)',
                 fontSize=9, fillColor=COL_LABEL))

    num_pulses = 5
    pulse_w = 80
    spacing = 95
    total_w = (num_pulses - 1) * spacing + pulse_w
    start_x = (w - total_w) / 2
    baseline = 42
    pulse_h = 42

    for p in range(num_pulses):
        px = start_x + p * spacing
        draw_baseline(d, px, baseline, pulse_w)

        npts = 80
        points = []
        for i in range(npts):
            t = float(i) / (npts - 1)
            s = pulsaret_sinc(t, 1.0) * gaussian_window(t)
            x = px + t * pulse_w
            y = baseline + s * pulse_h
            points.append((x, y))
        draw_waveform_line(d, points, COL_PULSARET, 1.5)

        # Period bracket below
        if p < num_pulses - 1:
            bx1 = px
            bx2 = px + spacing
            by = baseline - 12
            d.add(Line(bx1, by, bx2, by, strokeColor=HexColor('#444466'),
                       strokeWidth=0.5))
            d.add(Line(bx1, by - 4, bx1, by + 4, strokeColor=HexColor('#444466'),
                       strokeWidth=0.5))
            d.add(Line(bx2, by - 4, bx2, by + 4, strokeColor=HexColor('#444466'),
                       strokeWidth=0.5))

    d.add(String(w / 2 - 20, baseline - 24, 'one period',
                 fontSize=8, fillColor=HexColor('#555577'), textAnchor='middle'))
    return d


def draw_stage_duty():
    """Stage 4: Duty cycle — silence gaps."""
    w, h = int(PAGE_W), 140
    d = Drawing(w, h)
    draw_dark_waveform_box(d, 0, 0, w, h)

    d.add(String(20, h - 18, 'Stage 4: Duty Cycle', fontSize=11,
                 fillColor=COL_PULSARET, fontName='Helvetica-Bold'))
    d.add(String(20, h - 32, 'Shrinking the active portion introduces silence gaps',
                 fontSize=9, fillColor=COL_LABEL))

    num_pulses = 5
    spacing = 95
    duty = 0.4
    pulse_full_w = 80
    pulse_active_w = pulse_full_w * duty
    total_w = (num_pulses - 1) * spacing + pulse_full_w
    start_x = (w - total_w) / 2
    baseline = 42
    pulse_h = 42

    for p in range(num_pulses):
        px = start_x + p * spacing
        # Silence regions
        gap_w = (pulse_full_w - pulse_active_w) / 2
        d.add(Rect(px, baseline - 3, gap_w, 6,
                    fillColor=COL_SILENCE, strokeColor=None))
        d.add(Rect(px + gap_w + pulse_active_w, baseline - 3, gap_w, 6,
                    fillColor=COL_SILENCE, strokeColor=None))

        draw_baseline(d, px, baseline, pulse_full_w)
        active_x = px + gap_w

        npts = 80
        points = []
        for i in range(npts):
            t = float(i) / (npts - 1)
            s = pulsaret_sinc(t, 1.0) * gaussian_window(t)
            x = active_x + t * pulse_active_w
            y = baseline + s * pulse_h
            points.append((x, y))
        draw_waveform_line(d, points, COL_PULSARET, 1.5)

    # Duty label
    d.add(String(w - 80, baseline + pulse_h + 8, '40% duty',
                 fontSize=9, fillColor=COL_LABEL))
    d.add(String(w - 80, baseline - 4, 'silence',
                 fontSize=8, fillColor=HexColor('#664444')))
    return d


def draw_stage_formants():
    """Stage 5: Formant layers (F1, F2, F3)."""
    w, h = int(PAGE_W), 160
    d = Drawing(w, h)
    draw_dark_waveform_box(d, 0, 0, w, h)

    d.add(String(20, h - 18, 'Stage 5: Formants', fontSize=11,
                 fillColor=COL_PULSARET, fontName='Helvetica-Bold'))
    d.add(String(20, h - 32, 'Multiple formant layers cycle at different frequencies',
                 fontSize=9, fillColor=COL_LABEL))

    cx = w / 2
    baseline = 48
    pulse_w = 340
    duty = 0.6

    draw_baseline(d, cx - pulse_w / 2, baseline, pulse_w)

    npts = 250
    duty_w = pulse_w * duty
    start_x = cx - duty_w / 2

    # F3 (behind, green)
    pts3 = []
    for i in range(npts):
        t = float(i) / (npts - 1)
        s = pulsaret_sinc(t, 6.0) * gaussian_window(t) * 0.4
        px = start_x + t * duty_w
        py = baseline + s * 45
        pts3.append((px, py))
    draw_waveform_line(d, pts3, COL_F3, 1.2)

    # F2 (mid, orange-red)
    pts2 = []
    for i in range(npts):
        t = float(i) / (npts - 1)
        s = pulsaret_sinc(t, 3.5) * gaussian_window(t) * 0.55
        px = start_x + t * duty_w
        py = baseline + s * 50
        pts2.append((px, py))
    draw_waveform_line(d, pts2, COL_F2, 1.3)

    # F1 (front, blue)
    pts1 = []
    for i in range(npts):
        t = float(i) / (npts - 1)
        s = pulsaret_sinc(t, 1.8) * gaussian_window(t)
        px = start_x + t * duty_w
        py = baseline + s * 55
        pts1.append((px, py))
    draw_waveform_line(d, pts1, COL_PULSARET, 1.8)

    # Labels
    lab_y = baseline - 18
    d.add(String(cx - 100, lab_y, 'F1 200 Hz', fontSize=9,
                 fillColor=COL_PULSARET, fontName='Helvetica-Bold'))
    d.add(String(cx - 10, lab_y, 'F2 800 Hz', fontSize=9,
                 fillColor=COL_F2, fontName='Helvetica-Bold'))
    d.add(String(cx + 80, lab_y, 'F3 2000 Hz', fontSize=9,
                 fillColor=COL_F3, fontName='Helvetica-Bold'))

    return d


# ============================================================
# Signal chain diagram
# ============================================================

def draw_signal_chain():
    """Improved top-to-bottom signal chain with color-coded sections."""
    w, h = int(PAGE_W), 380
    d = Drawing(w, h)
    d.add(Rect(0, 0, w, h, fillColor=HexColor('#fafbfe'), strokeColor=VERY_LIGHT,
               strokeWidth=0.5, rx=4, ry=4))

    # Color scheme for sections
    pitch_fill = HexColor('#1a2a44')
    pitch_stroke = HexColor('#3366aa')
    pulse_fill = HexColor('#3a2a10')
    pulse_stroke = HexColor('#aa7722')
    formant_fill = HexColor('#1a3322')
    formant_stroke = HexColor('#44aa66')
    output_fill = HexColor('#2a2a2a')
    output_stroke = HexColor('#888888')

    box_w = 110
    box_h = 24
    cx = w / 2
    text_col = HexColor('#eeeeee')
    desc_col = MID_GRAY

    # --- Row 1: Pitch (blue) ---
    y = h - 45
    d.add(String(20, y + 12, 'PITCH', fontSize=8, fillColor=pitch_stroke,
                 fontName='Helvetica-Bold'))

    bx1 = cx - 180
    draw_rounded_box(d, bx1, y, box_w, box_h, pitch_fill, pitch_stroke,
                     'Pitch Source', 8, text_col)
    d.add(String(bx1, y - 11, 'MIDI / Base Pitch / CV', fontSize=7, fillColor=desc_col))

    draw_arrow_right(d, bx1 + box_w + 2, y + box_h / 2, bx1 + box_w + 18, pitch_stroke)

    bx2 = bx1 + box_w + 20
    draw_rounded_box(d, bx2, y, box_w, box_h, pitch_fill, pitch_stroke,
                     'Freq + Glide', 8, text_col)

    draw_arrow_right(d, bx2 + box_w + 2, y + box_h / 2, bx2 + box_w + 18, pitch_stroke)

    bx3 = bx2 + box_w + 20
    draw_rounded_box(d, bx3, y, box_w, box_h, pitch_fill, pitch_stroke,
                     'Phase Osc', 8, text_col)

    # Arrow down from phase osc
    draw_arrow_down(d, bx3 + box_w / 2, y - 2, y - 28, pitch_stroke)

    # --- Row 2: Per-pulse (amber) ---
    y -= 55
    d.add(String(20, y + 12, 'PER-PULSE', fontSize=8, fillColor=pulse_stroke,
                 fontName='Helvetica-Bold'))

    bx1 = cx - 180
    draw_rounded_box(d, bx1, y, box_w, box_h, pulse_fill, pulse_stroke,
                     'Timing Jitter', 8, text_col)
    d.add(String(bx1, y - 11, 'Random period variation', fontSize=7, fillColor=desc_col))

    draw_arrow_right(d, bx1 + box_w + 2, y + box_h / 2, bx1 + box_w + 18, pulse_stroke)

    bx2 = bx1 + box_w + 20
    draw_rounded_box(d, bx2, y, box_w, box_h, pulse_fill, pulse_stroke,
                     'Mask Decision', 8, text_col)
    d.add(String(bx2, y - 11, 'Stochastic / burst', fontSize=7, fillColor=desc_col))

    draw_arrow_right(d, bx2 + box_w + 2, y + box_h / 2, bx2 + box_w + 18, pulse_stroke)

    bx3 = bx2 + box_w + 20
    draw_rounded_box(d, bx3, y, box_w, box_h, pulse_fill, pulse_stroke,
                     'Amp Jitter', 8, text_col)
    d.add(String(bx3, y - 11, 'Random gain per pulse', fontSize=7, fillColor=desc_col))

    # Arrow down
    draw_arrow_down(d, cx, y - 2, y - 28, pulse_stroke)

    # --- Row 3: Formant loop (green) ---
    y -= 55
    d.add(String(20, y + 12, 'FORMANT', fontSize=8, fillColor=formant_stroke,
                 fontName='Helvetica-Bold'))
    d.add(String(20, y, '(x1-3)', fontSize=8, fillColor=formant_stroke,
                 fontName='Helvetica-Bold'))

    bx1 = cx - 230
    box_sm = 95
    draw_rounded_box(d, bx1, y, box_sm, box_h, formant_fill, formant_stroke,
                     'Formant Hz', 8, text_col)
    d.add(String(bx1, y - 11, 'Fixed or tracking', fontSize=7, fillColor=desc_col))

    draw_arrow_right(d, bx1 + box_sm + 2, y + box_h / 2, bx1 + box_sm + 14, formant_stroke)

    bx2 = bx1 + box_sm + 16
    draw_rounded_box(d, bx2, y, box_sm + 15, box_h, formant_fill, formant_stroke,
                     'Pulsaret x Window', 8, text_col)

    draw_arrow_right(d, bx2 + box_sm + 17, y + box_h / 2, bx2 + box_sm + 29, formant_stroke)

    bx3 = bx2 + box_sm + 31
    draw_rounded_box(d, bx3, y, box_sm - 10, box_h, formant_fill, formant_stroke,
                     'x Glisson', 8, text_col)

    draw_arrow_right(d, bx3 + box_sm - 8, y + box_h / 2, bx3 + box_sm + 4, formant_stroke)

    bx4 = bx3 + box_sm + 6
    draw_rounded_box(d, bx4, y, box_sm - 10, box_h, formant_fill, formant_stroke,
                     'Pan L/R', 8, text_col)
    d.add(String(bx4, y - 11, 'Constant-power', fontSize=7, fillColor=desc_col))

    # Arrow down
    draw_arrow_down(d, cx, y - 2, y - 28, formant_stroke)

    # --- Row 4: Voice output (gray) ---
    y -= 55
    d.add(String(20, y + 12, 'VOICE', fontSize=8, fillColor=output_stroke,
                 fontName='Helvetica-Bold'))

    bx1 = cx - 180
    draw_rounded_box(d, bx1, y, box_w, box_h, output_fill, output_stroke,
                     'Envelope x Amp', 8, text_col)
    d.add(String(bx1, y - 11, 'AR (Free Run) / ASR (MIDI/CV)', fontSize=7, fillColor=desc_col))

    draw_arrow_right(d, bx1 + box_w + 2, y + box_h / 2, bx1 + box_w + 18, output_stroke)

    bx2 = bx1 + box_w + 20
    draw_rounded_box(d, bx2, y, 85, box_h, output_fill, output_stroke,
                     'DC Block', 8, text_col)
    d.add(String(bx2, y - 11, 'Highpass per voice', fontSize=7, fillColor=desc_col))

    draw_arrow_right(d, bx2 + 87, y + box_h / 2, bx2 + 103, output_stroke)

    bx3 = bx2 + 105
    draw_rounded_box(d, bx3, y, box_w, box_h, output_fill, output_stroke,
                     'Sum Voices', 8, text_col)
    d.add(String(bx3, y - 11, 'Normalize by count', fontSize=7, fillColor=desc_col))

    # Arrow down
    draw_arrow_down(d, cx, y - 2, y - 28, output_stroke)

    # --- Row 5: Final output ---
    y -= 55
    d.add(String(20, y + 12, 'OUTPUT', fontSize=8, fillColor=output_stroke,
                 fontName='Helvetica-Bold'))

    bx1 = cx - 130
    draw_rounded_box(d, bx1, y, 85, box_h, output_fill, output_stroke,
                     'Drive (1-4x)', 8, text_col)

    draw_arrow_right(d, bx1 + 87, y + box_h / 2, bx1 + 103, output_stroke)

    bx2 = bx1 + 105
    draw_rounded_box(d, bx2, y, 95, box_h, output_fill, output_stroke,
                     'Soft Clip', 8, text_col)
    d.add(String(bx2, y - 11, 'Pade tanh saturation', fontSize=7, fillColor=desc_col))

    draw_arrow_right(d, bx2 + 97, y + box_h / 2, bx2 + 113, output_stroke)

    d.add(String(bx2 + 118, y + box_h / 2 - 4, 'Output L/R',
                 fontSize=9, fillColor=output_stroke, fontName='Helvetica-Bold'))

    # Aux outputs label
    y -= 30
    d.add(String(cx - 100, y, 'Aux: Trig Out | Env Out | Pre-clip L/R | Oct Down L/R',
                 fontSize=7, fillColor=LIGHT_GRAY))

    return d


# ============================================================
# Annotated display diagram
# ============================================================

def draw_display_annotated():
    """Annotated diagram of the 256x64 OLED display."""
    # The actual display is 256x64 but we scale it up for readability
    scale = 1.5
    disp_w = int(256 * scale)
    disp_h = int(64 * scale)
    margin = 90  # space for annotations on right
    ann_left = 60  # space for annotations on left

    total_w = ann_left + disp_w + margin
    total_h = disp_h + 80
    d = Drawing(total_w, total_h)
    d.add(Rect(0, 0, total_w, total_h, fillColor=HexColor('#fafbfe'),
               strokeColor=None))

    # Display background
    dx = ann_left
    dy = 30
    d.add(Rect(dx, dy, disp_w, disp_h, fillColor=HexColor('#0a0a0f'),
               strokeColor=HexColor('#333333'), strokeWidth=1, rx=4, ry=4))

    # --- Simulated display content ---
    # Three waveform boxes (pulsaret, window, duty)
    box_w = int(56 * scale)
    box_h = int(26 * scale)
    box_y = dy + disp_h - int(6 * scale) - box_h

    for i, label in enumerate(['PULSARET', 'WINDOW', 'DUTY']):
        bx = dx + int((6 + i * 58) * scale)
        d.add(Rect(bx, box_y, box_w, box_h, fillColor=None,
                    strokeColor=HexColor('#333333'), strokeWidth=0.5))
        d.add(String(bx + 4, box_y + box_h - 10, label,
                     fontSize=6, fillColor=HexColor('#888888')))

        # Draw a small waveform inside
        mid_y = box_y + box_h / 2
        npts = 30
        pts = []
        for j in range(npts):
            t = float(j) / (npts - 1)
            if i == 0:
                s = math.sin(2 * math.pi * t * 2.5)
            elif i == 1:
                s = gaussian_window(t)
            else:
                s = math.sin(2 * math.pi * t * 2) * gaussian_window(t)
            px = bx + 3 + t * (box_w - 6)
            if i == 1:
                py = box_y + 4 + s * (box_h - 12)
            else:
                py = mid_y + s * (box_h * 0.35)
            pts.append((px, py))
        color = HexColor('#ffffff') if i != 1 else HexColor('#eeeeee')
        draw_waveform_line(d, pts, color, 1.0)

    # Right-side info area
    info_x = dx + int(178 * scale)
    info_y = dy + disp_h - int(10 * scale)
    d.add(String(info_x, info_y, '130.8 Hz', fontSize=9,
                 fillColor=HexColor('#ffffff'), fontName='Helvetica'))
    d.add(String(info_x + int(50 * scale), info_y, 'MAJ', fontSize=9,
                 fillColor=HexColor('#eeeeee'), fontName='Helvetica-Bold'))
    info_y -= 14
    d.add(String(info_x, info_y, 'Amp 100%', fontSize=8,
                 fillColor=HexColor('#eeeeee')))
    info_y -= 13
    d.add(String(info_x, info_y, 'Drv 100%', fontSize=8,
                 fillColor=HexColor('#888888')))
    info_y -= 13
    d.add(String(info_x, info_y, '2F 4V', fontSize=8,
                 fillColor=HexColor('#eeeeee'), fontName='Helvetica-Bold'))

    # Envelope bar
    env_x = info_x
    env_y = info_y - 15
    env_w = int(60 * scale)
    d.add(Rect(env_x, env_y, env_w, 6, fillColor=HexColor('#1a1a1a'),
               strokeColor=HexColor('#333333'), strokeWidth=0.3))
    d.add(Rect(env_x, env_y, env_w * 0.7, 6, fillColor=HexColor('#ffffff'),
               strokeColor=None))

    # Gate dot
    d.add(Circle(env_x + env_w + 10, env_y + 3, 3,
                 fillColor=HexColor('#ffffff'), strokeColor=None))

    # Mode label
    d.add(String(env_x + env_w + 20, env_y - 1, 'CV', fontSize=8,
                 fillColor=HexColor('#eeeeee'), fontName='Helvetica-Bold'))

    # F1/F2/F3 readouts along bottom
    f_y = dy + int(4 * scale)
    d.add(String(dx + int(10 * scale), f_y, 'F1 270 Hz', fontSize=7,
                 fillColor=HexColor('#ffffff')))
    d.add(String(dx + int(70 * scale), f_y, 'F2 800 Hz', fontSize=7,
                 fillColor=HexColor('#eeeeee')))
    d.add(String(dx + int(130 * scale), f_y, 'F3 2000 Hz', fontSize=7,
                 fillColor=HexColor('#888888')))

    # Peak meter bar
    meter_y = dy + int(32 * scale)
    d.add(Rect(dx + int(6 * scale), meter_y, int(168 * scale), 3,
               fillColor=HexColor('#1a1a1a'), strokeColor=None))
    d.add(Rect(dx + int(6 * scale), meter_y, int(90 * scale), 3,
               fillColor=HexColor('#ffffff'), strokeColor=None))

    # CPU
    d.add(String(dx + int(210 * scale), f_y, '12%', fontSize=7,
                 fillColor=HexColor('#888888')))

    # --- Annotation lines ---
    ann_color = HexColor('#cc6600')
    ann_text_col = HexColor('#994400')
    ann_font = 7

    # Right-side annotations — evenly spaced vertically
    def ann_right(label, target_x, target_y, text_x, text_y):
        # Horizontal line from target to edge, then to text
        edge_x = dx + disp_w + 4
        d.add(Line(target_x, target_y, edge_x, target_y,
                    strokeColor=ann_color, strokeWidth=0.4, strokeDashArray=[2, 2]))
        d.add(Line(edge_x, target_y, text_x - 2, text_y + 3,
                    strokeColor=ann_color, strokeWidth=0.4))
        d.add(Circle(target_x, target_y, 1.5, fillColor=ann_color, strokeColor=None))
        d.add(String(text_x, text_y, label, fontSize=ann_font, fillColor=ann_text_col))

    rx = dx + disp_w + 10
    ann_spacing = 14
    ann_top = dy + disp_h + 2
    ann_right('Frequency + Chord', info_x + 30, dy + disp_h - int(10 * scale) + 4, rx, ann_top - ann_spacing * 0)
    ann_right('Amplitude', info_x + 30, dy + disp_h - int(10 * scale) - 10, rx, ann_top - ann_spacing * 1)
    ann_right('Drive', info_x + 30, dy + disp_h - int(10 * scale) - 23, rx, ann_top - ann_spacing * 2)
    ann_right('Voice/Formant Count', info_x + 20, dy + disp_h - int(10 * scale) - 36, rx, ann_top - ann_spacing * 3)
    ann_right('Envelope Bar', env_x + env_w / 2, env_y + 3, rx, ann_top - ann_spacing * 4)
    ann_right('Trigger + Mode', env_x + env_w + 15, env_y + 3, rx, ann_top - ann_spacing * 5)

    # Left-side annotations — evenly spaced
    def ann_left_fn(label, target_x, target_y, text_x, text_y):
        edge_x = dx - 4
        d.add(Line(target_x, target_y, edge_x, target_y,
                    strokeColor=ann_color, strokeWidth=0.4, strokeDashArray=[2, 2]))
        d.add(Line(edge_x, target_y, text_x + len(label) * 4 + 2, text_y + 3,
                    strokeColor=ann_color, strokeWidth=0.4))
        d.add(Circle(target_x, target_y, 1.5, fillColor=ann_color, strokeColor=None))
        d.add(String(text_x, text_y, label, fontSize=ann_font, fillColor=ann_text_col))

    lx = 2
    ann_left_fn('Waveform Views', dx + int(6 * scale), box_y + box_h / 2, lx, box_y + box_h / 2)
    ann_left_fn('Peak Meter', dx + int(6 * scale), meter_y + 1, lx, meter_y - 1)
    ann_left_fn('F1/F2/F3 Hz', dx + int(10 * scale), f_y + 3, lx, f_y + 1)
    ann_left_fn('CPU', dx + int(200 * scale), f_y + 3, lx, f_y - 12)

    return d


# ============================================================
# TL;DR box helper
# ============================================================

def make_tldr_table(items, styles):
    """Create a shaded TL;DR box with bullet points."""
    content = []
    for item in items:
        content.append(Paragraph('\u2022 ' + item, styles['tldr_body']))

    inner = []
    inner.append(Paragraph('<b>TL;DR</b>', ParagraphStyle(
        'TldrTitle', fontName='Helvetica-Bold', fontSize=11,
        textColor=ACCENT_DARK, spaceAfter=4, alignment=TA_LEFT)))
    inner.extend(content)

    # Wrap in a table cell for the box
    t = Table([[inner]], colWidths=[PAGE_W - 20])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#eef3fa')),
        ('BOX', (0, 0), (-1, -1), 0.5, ACCENT),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
    ]))
    return t


# ============================================================
# Table builder
# ============================================================

def make_table(headers, rows, col_widths=None):
    data = [headers] + rows
    if col_widths is None:
        col_widths = [int(PAGE_W) // len(headers)] * len(headers)
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), TABLE_HEADER_TEXT),
        ('TEXTCOLOR', (0, 1), (-1, -1), BODY_TEXT),
        ('GRID', (0, 0), (-1, -1), 0.3, TABLE_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]
    # Alternate row backgrounds
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), TABLE_ROW_ALT))
    t.setStyle(TableStyle(style_cmds))
    return t


# ============================================================
# Section heading with anchor — records page number
# ============================================================

# Global dict populated during build: anchor_id -> page number
_anchor_pages = {}


class AnchoredHeading(Flowable):
    """H1 heading that registers its page number during layout."""

    def __init__(self, text, anchor_id, style):
        Flowable.__init__(self)
        self._text = text
        self._anchor_id = anchor_id
        self._style = style
        self._para = Paragraph('<a name="%s"/>%s' % (anchor_id, text), style)

    def wrap(self, availWidth, availHeight):
        return self._para.wrap(availWidth, availHeight)

    def drawOn(self, canvas, x, y, _sW=0):
        # Record page number (1-based)
        page_num = canvas.getPageNumber()
        _anchor_pages[self._anchor_id] = page_num
        self._para.drawOn(canvas, x, y, _sW)

    def split(self, availWidth, availHeight):
        return self._para.split(availWidth, availHeight)


def h1_with_anchor(text, anchor_id, styles):
    """Return an AnchoredHeading that records its page number."""
    return AnchoredHeading(text, anchor_id, styles['h1'])


# ============================================================
# Build the PDF
# ============================================================

def build_pdf(output_path=None):
    if output_path is None:
        output_path = OUT_PATH
    styles = make_styles()
    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    story = []

    # ================================================================
    # TITLE PAGE
    # ================================================================
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph('Spaluter', styles['title']))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph('Pulsar Synthesis for disting NT', styles['subtitle']))
    story.append(HRFlowable(width='40%', thickness=1, color=ACCENT, hAlign='LEFT'))
    story.append(Spacer(1, 0.4 * inch))
    story.append(Paragraph(
        'A pulsar synthesis instrument plugin for the Expert Sleepers disting NT Eurorack module. '
        '66 parameters, 15 CV inputs, 4-voice polyphony, 10 pulsaret waveforms, '
        '3 independent formants, stochastic and burst masking.',
        styles['body']))
    story.append(Spacer(1, 0.4 * inch))
    # Pulsaret diagram on title page (Stage 1 — the raw burst shape)
    story.append(draw_stage_pulsaret())
    story.append(Paragraph(
        'A sinc pulsaret \u2014 the raw waveform burst at the core of pulsar synthesis.',
        styles['caption']))
    story.append(Spacer(1, 0.8 * inch))
    story.append(Paragraph('<a href="https://github.com/sroons/spaluter" color="#2266aa">github.com/sroons/spaluter</a>', styles['caption']))

    story.append(PageBreak())

    # ================================================================
    # TABLE OF CONTENTS
    # ================================================================
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph('Contents', styles['toc_title']))
    # TOC entries: (anchor_id, label, is_subsection)
    toc_sections = [
        ('about', 'About Spaluter', False),
        ('whatispulsar', 'What Is Pulsar Synthesis?', False),
        ('pulsarets', 'Pulsaret Waveforms', True),
        ('windows', 'Window Functions', True),
        ('signalchain', 'Signal Chain', False),
        ('display', 'The Display', False),
        ('howtouse', 'How to Use Spaluter', False),
        ('navigating', 'Navigating Parameters', True),
        ('params', 'Parameters', False),
        ('cvinputs', 'CV Inputs', False),
        ('cvmode', 'CV Mode', False),
        ('hardware', 'Hardware Controls', False),
        ('sounddesign', 'Sound Design Tips', False),
        ('patches', 'Patch Ideas', False),
        ('reading', 'Further Reading', False),
    ]
    # Build TOC as a table: [label + dots] [page number right-aligned]
    toc_label_w = PAGE_W - 30
    toc_page_w = 30
    toc_rows = []
    for anchor_id, label, is_sub in toc_sections:
        page_num = _anchor_pages.get(anchor_id, '?')
        page_str = str(page_num)
        # Estimate available dot width: label col minus label text minus padding
        # At ~5.5px per char in Helvetica 10pt, fill remaining space with dots
        font_size = 9 if is_sub else 10
        char_w = font_size * 0.52  # approximate char width
        indent = 16 if is_sub else 0
        label_text_w = len(label) * char_w + indent
        avail_dot_w = toc_label_w - label_text_w - 10
        num_dots = int(avail_dot_w / (char_w * 0.6))  # dots are narrower
        if num_dots < 4:
            num_dots = 4
        dots = ' ' + '.' * num_dots

        prefix = '&nbsp;&nbsp;&nbsp;' if is_sub else ''
        label_para = Paragraph(
            '%s<a href="#%s" color="#2266aa">%s</a>'
            '<font color="#bbbbbb" size="%d">%s</font>' % (
                prefix, anchor_id, label, font_size - 1, dots),
            ParagraphStyle('TocL', fontName='Helvetica', fontSize=font_size,
                           leading=font_size + 4, spaceAfter=0, spaceBefore=0,
                           textColor=BODY_TEXT))
        page_para = Paragraph(
            '<a href="#%s" color="#2266aa">%s</a>' % (anchor_id, page_str),
            ParagraphStyle('TocR', fontName='Helvetica', fontSize=font_size,
                           leading=font_size + 4, spaceAfter=0, spaceBefore=0,
                           textColor=ACCENT_DARK, alignment=2))  # 2 = TA_RIGHT
        toc_rows.append([label_para, page_para])

    toc_table = Table(toc_rows, colWidths=[toc_label_w, toc_page_w])
    toc_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(toc_table)
    story.append(Spacer(1, 0.15 * inch))
    story.append(HRFlowable(width='100%', thickness=0.5, color=VERY_LIGHT))

    # ================================================================
    # ABOUT SPALUTER
    # ================================================================
    story.append(h1_with_anchor('About Spaluter', 'about', styles))
    story.append(Paragraph(
        '<b>Spaluter</b> is a pulsar synthesis instrument for the Expert Sleepers '
        'disting NT. It generates sound by repeating short waveform bursts (pulsarets) '
        'at audio rates, producing timbres that range from thick analog-style bass and '
        'shimmering pads to metallic percussion, vowel-like vocal textures, granular '
        'noise clouds, and deep evolving drones. The synthesis engine provides direct '
        'control over spectral peaks (formants), pulse density (duty cycle), and '
        'micro-level stochastic processes (masking, jitter, glisson) that are difficult '
        'or impossible to achieve with conventional subtractive or FM synthesis.',
        styles['body']))
    story.append(Paragraph(
        'With up to 4 polyphonic voices, 3 independent formant oscillators, 15 CV inputs '
        '(12 pre-routed by default), and real-time waveform display, Spaluter is designed '
        'for both immediate sonic exploration and deep, evolving patches under voltage control.',
        styles['body']))

    story.append(Spacer(1, 0.15 * inch))
    story.append(HRFlowable(width='100%', thickness=0.5, color=VERY_LIGHT))
    story.append(Spacer(1, 0.15 * inch))

    # ================================================================
    # WHAT IS PULSAR SYNTHESIS
    # ================================================================
    story.append(h1_with_anchor('What Is Pulsar Synthesis?', 'whatispulsar', styles))

    # TL;DR box
    tldr_items = [
        'A <b>pulsaret</b> (short waveform burst) is shaped by a <b>window</b> (amplitude envelope) and repeated at the <b>fundamental frequency</b> to produce a pitched tone.',
        'The <b>duty cycle</b> controls what fraction of each period is active sound vs. silence, dramatically affecting timbre.',
        '<b>Formants</b> (1-3 independent spectral peaks) cycle the pulsaret waveform at fixed frequencies, producing vowel-like resonances.',
        '<b>Masking</b> selectively mutes pulses for rhythmic or stochastic textures.',
    ]
    story.append(make_tldr_table(tldr_items, styles))
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph(
        'Pulsar synthesis is a technique developed by Curtis Roads and Alberto de Campo '
        'in the early 2000s, described in Roads\' book <i>Microsound</i> (MIT Press, 2001). '
        'It belongs to the family of granular and particle-based synthesis methods that '
        'operate on the micro-timescale of sound \u2014 durations below approximately 100 '
        'milliseconds, where individual sonic events blur into continuous tones and textures.',
        styles['body']))

    story.append(Paragraph(
        'The following five stages illustrate how a pulsar tone is constructed, '
        'matching the interactive explainer at the Spaluter project page.',
        styles['body']))

    # --- Stage 1: Pulsaret ---
    story.append(Spacer(1, 0.1 * inch))
    story.append(KeepTogether([
        Paragraph('<b>1. Pulsaret</b> \u2014 the raw burst shape', styles['h3']),
        Paragraph(
            'A pulsaret is the waveform contained within a single pulse. It determines the '
            'basic harmonic content of the sound. Common pulsaret shapes include sine waves, '
            'sinc functions (band-limited impulses), and noise.',
            styles['body']),
        draw_stage_pulsaret(),
        Spacer(1, 4),
    ]))

    # --- Stage 2: Window ---
    story.append(KeepTogether([
        Paragraph('<b>2. Window</b> \u2014 the amplitude envelope per burst', styles['h3']),
        Paragraph(
            'A window function shapes the amplitude of each pulsaret, controlling how the '
            'burst fades in and out. The window determines the spectral smoothness of each '
            'pulse: a Gaussian window produces smooth, low-sidelobe spectra; a rectangular '
            'window maximizes brightness at the cost of spectral splatter.',
            styles['body']),
        draw_stage_window(),
        Spacer(1, 4),
    ]))

    # --- Stage 3: Train ---
    story.append(KeepTogether([
        Paragraph('<b>3. Train</b> \u2014 repetition at the fundamental frequency', styles['h3']),
        Paragraph(
            'The windowed pulsaret is repeated periodically. The repetition rate determines '
            'the fundamental frequency (pitch) of the resulting tone. At audio rates '
            '(roughly 20 Hz and above), the train is perceived as a continuous pitched sound.',
            styles['body']),
        draw_stage_train(),
        Spacer(1, 4),
    ]))

    story.append(PageBreak())

    # --- Stage 4: Duty Cycle ---
    story.append(KeepTogether([
        Paragraph('<b>4. Duty Cycle</b> \u2014 active portion vs. silence', styles['h3']),
        Paragraph(
            'The duty cycle specifies what fraction of each fundamental period contains '
            'active sound. The pulsaret is centered within the period with equal silence '
            'gaps before and after. At 100%% duty, the sound approaches conventional '
            'wavetable synthesis. As duty decreases, the characteristic hollow, buzzing '
            'quality of pulsar synthesis emerges. At very low duty cycles, individual '
            'pulsarets become audible as distinct sonic particles.',
            styles['body']),
        draw_stage_duty(),
        Spacer(1, 4),
    ]))

    # --- Stage 5: Formants ---
    story.append(KeepTogether([
        Paragraph('<b>5. Formants</b> \u2014 independent spectral peaks', styles['h3']),
        Paragraph(
            'Formant oscillators cycle the pulsaret waveform at frequencies independent of '
            'the fundamental, creating fixed spectral peaks analogous to vocal formants in '
            'speech. By setting formant frequencies to values such as 200 Hz, 800 Hz, and '
            '2000 Hz, vowel-like resonances emerge that remain constant as pitch changes. '
            'Spaluter provides up to 3 independent formant oscillators, each with its own '
            'frequency, pan position, and CV input.',
            styles['body']),
        draw_stage_formants(),
        Spacer(1, 4),
    ]))

    story.append(Spacer(1, 0.15 * inch))
    story.append(HRFlowable(width='100%', thickness=0.5, color=VERY_LIGHT))

    # ================================================================
    # PULSARET WAVEFORMS
    # ================================================================
    story.append(h1_with_anchor('Pulsaret Waveforms', 'pulsarets', styles))
    story.append(Paragraph(
        'Spaluter provides 10 pulsaret waveforms with continuous morphing between adjacent '
        'shapes. The Pulsaret parameter (0.0\u20139.0) selects and blends waveforms via '
        'bilinear interpolation between adjacent tables of 2048 samples each.',
        styles['body']))

    random.seed(123)
    waveform_descs = [
        ('0.0 \u2014 Sine', 'Pure fundamental. Clean starting point for isolating formant effects.'),
        ('1.0 \u2014 Sine x2', 'Second harmonic. Adds brightness without harshness.'),
        ('2.0 \u2014 Sine x3', 'Third harmonic. Fuller harmonic content.'),
        ('3.0 \u2014 Sinc', 'Band-limited impulse with natural sidelobes. The classic pulsar synthesis waveform, closest to Roads\' original work.'),
        ('4.0 \u2014 Triangle', 'Odd harmonics with rapid rolloff. Mellow, clarinet-adjacent timbre.'),
        ('5.0 \u2014 Saw', 'All harmonics present. Familiar subtractive-style brightness.'),
        ('6.0 \u2014 Square', 'Odd harmonics, hollow quality. Clarinet-like character.'),
        ('7.0 \u2014 Formant', 'Built-in resonant peak. Stacking with formant frequency parameters creates double-resonance effects.'),
        ('8.0 \u2014 Pulse', 'Extremely bright and nasal. Sharp transient with rapid decay.'),
        ('9.0 \u2014 Noise', 'Stochastic waveform. Replaces pitched content with noise bursts for percussion or breathy textures.'),
    ]

    for idx, (name, desc) in enumerate(waveform_descs):
        random.seed(42 + idx)
        row_data = [[
            make_inline_waveform(idx, False),
            Paragraph('<b>%s</b>' % name, styles['body_tight']),
            Paragraph(desc, styles['body_tight']),
        ]]
        t = Table(row_data, colWidths=[68, 110, PAGE_W - 190])
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ]))
        story.append(t)
    story.append(Paragraph(
        'Fractional morph values (e.g. 3.5) blend between adjacent shapes via linear interpolation.',
        styles['caption']))

    story.append(Spacer(1, 0.1 * inch))
    story.append(HRFlowable(width='100%', thickness=0.5, color=VERY_LIGHT))

    # ================================================================
    # WINDOW FUNCTIONS
    # ================================================================
    story.append(h1_with_anchor('Window Functions', 'windows', styles))
    story.append(Paragraph(
        'The window function shapes the amplitude envelope applied to each pulsaret. '
        'The Window parameter (0.0\u20134.0) morphs between 5 window types.',
        styles['body']))

    window_descs = [
        ('0.0 \u2014 Rectangular', 'No fade \u2014 hard edges. Maximum brightness and click. Highest spectral energy but also highest sidelobe levels.'),
        ('1.0 \u2014 Gaussian', 'Smooth, bell-shaped fade. The most natural-sounding option with excellent sidelobe suppression.'),
        ('2.0 \u2014 Hann', 'Raised cosine. Similar to Gaussian with a slightly flatter top. Good general-purpose window.'),
        ('3.0 \u2014 Exp Decay', 'Sharp attack with exponential ringout. Percussive, plucked character. Pairs well with sinc pulsaret.'),
        ('4.0 \u2014 Linear Decay', 'Sharp attack with linear ramp down. Simpler percussive shape than exponential.'),
    ]

    for idx, (name, desc) in enumerate(window_descs):
        row_data = [[
            make_inline_waveform(idx, True),
            Paragraph('<b>%s</b>' % name, styles['body_tight']),
            Paragraph(desc, styles['body_tight']),
        ]]
        t = Table(row_data, colWidths=[68, 130, PAGE_W - 210])
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ]))
        story.append(t)
    story.append(Paragraph(
        'Fractional values blend adjacent windows. The window interacts with glisson: '
        'exponential decay makes pitch sweeps audible mainly at the attack.',
        styles['caption']))

    story.append(PageBreak())

    # ================================================================
    # SIGNAL CHAIN
    # ================================================================
    story.append(h1_with_anchor('Signal Chain', 'signalchain', styles))
    story.append(Paragraph(
        'The signal chain flows from pitch source through per-pulse processing, '
        'formant synthesis, voice envelope, and final output stage. Each voice '
        '(1\u20134) runs the full chain independently; voices are summed and '
        'normalized before the drive and soft clip stages.',
        styles['body']))
    story.append(Spacer(1, 0.1 * inch))
    story.append(draw_signal_chain())
    story.append(Paragraph(
        'Blue = pitch section, amber = per-pulse decisions, green = formant loop '
        '(runs 1\u20133 times per pulse), gray = voice and output mixing.',
        styles['caption']))

    story.append(Spacer(1, 0.1 * inch))
    story.append(HRFlowable(width='100%', thickness=0.5, color=VERY_LIGHT))

    # ================================================================
    # THE DISPLAY
    # ================================================================
    story.append(h1_with_anchor('The Display', 'display', styles))
    story.append(Paragraph(
        'The 256x64 pixel OLED display provides real-time visual feedback across three '
        'waveform previews and a synthesis state readout area. All waveform views '
        'respond to CV modulation in real time.',
        styles['body']))
    story.append(Spacer(1, 0.1 * inch))
    story.append(draw_display_annotated())
    story.append(Paragraph(
        'Annotated display layout showing waveform views, formant readouts, '
        'envelope bar, gate indicator, mode label, and peak meter.',
        styles['caption']))

    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph('Pot Mappings', styles['h3']))
    pot_data = [
        ['Pot Left', 'Pulsaret morph', '0.0\u20139.0 (sweeps all 10 waveforms)'],
        ['Pot Center', 'Window morph', '0.0\u20134.0 (sweeps all 5 windows)'],
        ['Pot Right', 'Duty Cycle', '1\u2013100%'],
    ]
    story.append(make_table(
        ['Pot', 'Parameter', 'Range'],
        pot_data,
        [90, 140, int(PAGE_W) - 240]))

    story.append(PageBreak())

    # ================================================================
    # HOW TO USE SPALUTER
    # ================================================================
    story.append(h1_with_anchor('How to Use Spaluter', 'howtouse', styles))

    # Getting sound
    story.append(Paragraph('Getting Sound Immediately', styles['h2']))
    story.append(Paragraph(
        'Spaluter defaults to <b>CV mode</b> with <b>Amplitude at 100%%</b>. To produce '
        'sound, patch a trigger/gate signal into <b>Input 2</b> (Trigger CV) and a 1V/oct '
        'pitch source into <b>Input 1</b> (Pitch CV). Each rising edge on the trigger input '
        'allocates a new voice at the current pitch. The remaining 10 default CV inputs '
        'add modulation when patched.',
        styles['body']))
    story.append(Paragraph(
        'Alternatively, switch <b>Gate Mode</b> to <b>Free Run</b> on the Mode page for '
        'immediate sound without any CV patching. Free Run generates a continuous tone at the '
        'Base Pitch frequency (default C1, ~32.7 Hz).',
        styles['body']))

    # Modifying timbre
    story.append(Paragraph('Modifying Timbre', styles['h2']))
    timbre_items = [
        '<b>Pulsaret shape</b> (Pot L or Waveform page): Sweeps through 10 waveform types. Start with Sinc (3.0) for the classic pulsar sound, then explore Sine (0.0) for purity or Noise (9.0) for texture.',
        '<b>Window function</b> (Pot C or Waveform page): Shapes the attack and decay of each burst. Gaussian (1.0) for smooth tones, Rectangular (0.0) for maximum brightness, Exp Decay (3.0) for plucked character.',
        '<b>Duty cycle</b> (Pot R or Waveform page): The most dramatic timbral control after formant frequency. 80\u2013100%% is full and warm; 30\u201360%% is the characteristic pulsar buzz; 5\u201320%% produces sparse particle textures.',
        '<b>Formant frequencies</b> (Formants page): Set spectral peak locations. F1=270, F2=2300 produces an "ah" vowel. F1=200, F2=347, F3=511 produces metallic bell tones. Modulate with CV for expressive sweeps.',
    ]
    for item in timbre_items:
        story.append(Paragraph('\u2022 ' + item, styles['bullet']))

    # Parameter interactions
    story.append(Paragraph('Parameter Interactions', styles['h2']))
    story.append(Paragraph(
        '<b>Duty cycle and formant perception:</b> As duty cycle decreases, the pulsaret '
        'occupies less of each period. This narrows the spectral envelope of each pulse, '
        'making formant peaks less distinct at very low duty values. At high duty, formants '
        'are clearly defined. Formant Duty Mode automates this relationship by tying duty '
        'to formant frequency.',
        styles['body']))
    story.append(Paragraph(
        '<b>Formant tracking:</b> With Formant Track set to Fixed (default), formant '
        'frequencies remain constant regardless of pitch \u2014 producing the classic vocal '
        'formant effect where timbre changes with pitch. With Track enabled, formant '
        'frequencies scale proportionally with voice pitch, preserving the spectral shape '
        'like a sampler would.',
        styles['body']))
    story.append(Paragraph(
        '<b>Masking + jitter for organic textures:</b> Stochastic masking (random pulse '
        'muting) combined with amplitude jitter (random gain variation) and timing jitter '
        '(random period variation) layers three independent sources of randomness. '
        'Low amounts (10\u201325%% each) produce subtle organic variation; higher amounts '
        'dissolve the tone into a granular particle cloud. With Independent Masking enabled, '
        'each formant receives its own mask decision, creating spectral flickering.',
        styles['body']))

    story.append(Spacer(1, 0.1 * inch))
    story.append(HRFlowable(width='100%', thickness=0.5, color=VERY_LIGHT))

    # ================================================================
    # NAVIGATING PARAMETERS
    # ================================================================
    story.append(h1_with_anchor('Navigating Parameters', 'navigating', styles))

    story.append(Paragraph('disting NT Parameter Navigation', styles['h2']))
    story.append(Paragraph(
        'Spaluter\'s 66 parameters are organized across 15 pages. On the disting NT hardware, '
        'use the <b>left encoder</b> to scroll through parameter pages and the '
        '<b>right encoder</b> to adjust the selected parameter value. Press an encoder '
        'button to toggle between page selection and value editing modes.',
        styles['body']))
    story.append(Paragraph(
        'Spaluter maps <b>3 pots</b> (Pulsaret, Window, Duty) and <b>4 buttons</b> '
        '(mask mode, formant count, voice count, chord type) for direct, page-free control '
        'of the most frequently adjusted parameters.',
        styles['body']))

    story.append(Paragraph('NT Helper', styles['h2']))
    story.append(Paragraph(
        '<b>NT Helper</b> is a companion app (available for iPad and as a browser-based tool) '
        'that connects to the disting NT over USB. It provides a graphical interface for '
        'editing all parameters simultaneously, making it faster to configure complex patches '
        'than scrolling through pages on the module\'s display. All parameter changes made in '
        'NT Helper are reflected on the module in real time, and vice versa.',
        styles['body']))

    story.append(Spacer(1, 0.15 * inch))
    story.append(HRFlowable(width='100%', thickness=0.5, color=VERY_LIGHT))

    # ================================================================
    # PARAMETERS TABLE
    # ================================================================
    story.append(h1_with_anchor('Parameters', 'params', styles))
    story.append(Paragraph('66 parameters across 15 pages:', styles['body']))

    param_data = [
        ['Mode', 'Gate Mode', 'MIDI / Free Run / CV', 'CV'],
        ['', 'Voice Count', '1\u20134', '1'],
        ['', 'Chord Type', '14 types', 'Unison'],
        ['', 'MIDI Ch', '1\u201316', '1'],
        ['', 'Base Pitch', 'MIDI 0\u2013127', 'C1 (24)'],
        ['Level', 'Amplitude', '0\u2013200%', '100%'],
        ['', 'Drive', '100\u2013400%', '100%'],
        ['', 'Attack', '0.1\u20132000 ms', '10 ms'],
        ['', 'Release', '1.0\u20133200 ms', '200 ms'],
        ['', 'Glide', '0\u20132000 ms', '0 ms'],
        ['Waveform', 'Pulsaret', '0.0\u20139.0', '2.5'],
        ['', 'Window', '0.0\u20134.0', '0.5'],
        ['', 'Duty Cycle', '1\u2013100%', '50%'],
        ['', 'Duty Mode', 'Manual / Formant', 'Manual'],
        ['Formants', 'Formant Count', '1\u20133', '2'],
        ['', 'Formant 1 Hz', '20\u20132000 Hz', '20 Hz'],
        ['', 'Formant 2 Hz', '20\u20132000 Hz', '200 Hz'],
        ['', 'Formant 3 Hz', '20\u20132000 Hz', '400 Hz'],
        ['', 'Formant Track', 'Fixed / Track', 'Fixed'],
        ['Texture', 'Mask Mode', 'Off / Stochastic / Burst', 'Off'],
        ['', 'Mask Amount', '0\u2013100%', '50%'],
        ['', 'Burst On', '1\u201316', '4'],
        ['', 'Burst Off', '0\u201316', '4'],
        ['', 'Indep Mask', 'Off / On', 'Off'],
        ['Texture', 'Amp Jitter', '0\u2013100%', '0%'],
        ['', 'Time Jitter', '0\u2013100%', '0%'],
        ['', 'Glisson', '-10.0 to +10.0', '0'],
        ['Panning', 'Pan 1', '-100 to +100', '0'],
        ['', 'Pan 2', '-100 to +100', '-50'],
        ['', 'Pan 3', '-100 to +100', '+50'],
        ['Sample', 'Use Sample', 'Off / On', 'Off'],
        ['', 'Folder', '(SD card)', '\u2014'],
        ['', 'File', '(SD card)', '\u2014'],
        ['', 'Sample Rate', '25\u2013400%', '100%'],
        ['Outputs', 'Output L', 'Bus 1\u201364', 'Bus 13'],
        ['', 'Output R', 'Bus 1\u201364', 'Bus 14'],
        ['Aux Out', 'Trig Out', 'Bus 0\u201364', '0 (none)'],
        ['', 'Env Out', 'Bus 0\u201364', '0 (none)'],
        ['', 'Pre-clip L', 'Bus 0\u201364', '0 (none)'],
        ['', 'Pre-clip R', 'Bus 0\u201364', '0 (none)'],
        ['', 'Oct Down L', 'Bus 0\u201364', '0 (none)'],
        ['', 'Oct Down R', 'Bus 0\u201364', '0 (none)'],
    ]

    story.append(make_table(
        ['Page', 'Parameter', 'Range', 'Default'],
        param_data,
        [60, 110, 180, 130]))

    story.append(Paragraph(
        'Unused parameters are automatically grayed out based on context '
        '(e.g., Chord Type in MIDI/CV mode, Burst params when mask mode is not Burst).',
        styles['caption']))

    story.append(PageBreak())

    # ================================================================
    # CV INPUTS TABLE
    # ================================================================
    story.append(h1_with_anchor('CV Inputs', 'cvinputs', styles))
    story.append(Paragraph(
        'All CV inputs are <b>bipolar</b> (\u00b15V). Each is routable to any of the '
        '64 buses (1\u201312 inputs, 13\u201320 outputs, 21\u201364 aux), or 0 for none. '
        'CV modulation is applied as an offset on top of the parameter\'s base value. '
        'All CVs except Pitch are block-rate averaged. Pitch CV is processed per-sample '
        'for accurate 1V/oct tracking.',
        styles['body']))

    cv_data = [
        ['Pitch CV', 'Input 1', '1V/oct exponential', 'Per-sample pitch modulation'],
        ['Trigger CV', 'Input 2', '>2.5V = high', 'Trigger for CV mode voice allocation'],
        ['Duty CV', 'Input 3', '\u00b15V \u2192 \u00b120%', 'Duty cycle offset added to base'],
        ['Mask CV', 'Input 4', '\u00b15V \u2192 \u00b150%', 'Mask amount offset (bipolar)'],
        ['Pulsaret CV', 'Input 5', '\u00b15V \u2192 full range', 'Pulsaret morph \u00b14.5'],
        ['Window CV', 'Input 6', '\u00b15V \u2192 full range', 'Window morph \u00b12.0'],
        ['Formant 1 CV', 'Input 7', '\u00b15V \u2192 \u00b11000 Hz', 'Formant 1 frequency offset'],
        ['Formant 2 CV', 'Input 8', '\u00b15V \u2192 \u00b11000 Hz', 'Formant 2 frequency offset'],
        ['Formant 3 CV', 'Input 9', '\u00b15V \u2192 \u00b11000 Hz', 'Formant 3 frequency offset'],
        ['Attack CV', 'Input 10', '\u00b15V \u2192 \u00b11000 ms', 'Envelope attack time offset'],
        ['Release CV', 'Input 11', '\u00b15V \u2192 \u00b11600 ms', 'Envelope release time offset'],
        ['Glisson CV', 'Input 12', '\u00b15V \u2192 \u00b12.0 oct', 'Glisson depth offset'],
        ['Amplitude CV', '0 (none)', '\u00b15V \u2192 \u00b150%', 'Amplitude offset added to base'],
        ['Pan 1 CV', '0 (none)', '\u00b15V \u2192 \u00b1100%', 'Formant 1 stereo pan position'],
        ['Amp Jit CV', '0 (none)', '\u00b15V \u2192 \u00b150%', 'Amp jitter amount offset'],
        ['Time Jit CV', '0 (none)', '\u00b15V \u2192 \u00b150%', 'Timing jitter amount offset'],
    ]

    story.append(make_table(
        ['CV Input', 'Default Bus', 'Scaling', 'Effect'],
        cv_data,
        [85, 70, 130, int(PAGE_W) - 295]))

    story.append(Spacer(1, 0.15 * inch))
    story.append(HRFlowable(width='100%', thickness=0.5, color=VERY_LIGHT))

    # ================================================================
    # CV MODE
    # ================================================================
    story.append(h1_with_anchor('CV Mode (Rings-style Voice Triggering)', 'cvmode', styles))
    story.append(Paragraph(
        'Polyphonic voice triggering from a single trigger+pitch CV pair, inspired by '
        'Mutable Instruments Rings. Each trigger rising edge allocates a new voice while '
        'previous voices ring out through their release envelopes \u2014 up to 4 simultaneous voices.',
        styles['body']))

    story.append(Paragraph('Setup', styles['h3']))
    setup_items = [
        'Set <b>Gate Mode</b> to <b>CV</b> (Mode page) \u2014 this is the default.',
        'Patch a trigger/gate signal into <b>Input 2</b> (Trigger CV, default bus).',
        'Patch a 1V/oct pitch source into <b>Input 1</b> (Pitch CV, default bus).',
        'Adjust <b>Attack</b> and <b>Release</b> on the Level page. Amplitude defaults to 100%%.',
    ]
    for i, item in enumerate(setup_items):
        story.append(Paragraph('%d. %s' % (i + 1, item), styles['bullet']))

    story.append(Paragraph('Behavior', styles['h3']))
    trigger_data = [
        ['Rising edge', 'Allocates a voice, captures pitch from Base Pitch x Pitch CV, starts attack'],
        ['Held high', 'Active voice tracks Pitch CV in real time (enables pitch bends)'],
        ['Falling edge', 'Active voice enters release; pitch and all synthesis parameters freeze'],
        ['During release', 'Voice sounds independently \u2014 knob/CV changes only affect the next triggered voice'],
    ]
    story.append(make_table(
        ['Trigger State', 'What Happens'],
        trigger_data,
        [100, int(PAGE_W) - 110]))

    story.append(Paragraph(
        'When all 4 voices are releasing, a new trigger steals the quietest (lowest envelope) voice. '
        'Voice Count, Chord Type, and MIDI Ch are not used in CV mode and are automatically grayed out.',
        styles['body']))

    story.append(Spacer(1, 0.15 * inch))
    story.append(HRFlowable(width='100%', thickness=0.5, color=VERY_LIGHT))

    # ================================================================
    # HARDWARE CONTROLS
    # ================================================================
    story.append(h1_with_anchor('Hardware Controls', 'hardware', styles))
    story.append(Paragraph(
        'These mappings are active on the realtime display screen. '
        'Encoders and buttons not listed below retain their standard disting NT behavior.',
        styles['body']))

    story.append(Paragraph('Pots', styles['h2']))
    pot_data = [
        ['Left', 'Pulsaret morph', '0.0\u20139.0 (sweeps all 10 waveforms)'],
        ['Center', 'Window morph', '0.0\u20134.0 (sweeps all 5 windows)'],
        ['Right', 'Duty Cycle', '1\u2013100%'],
    ]
    story.append(make_table(
        ['Pot', 'Parameter', 'Range'],
        pot_data,
        [80, 140, int(PAGE_W) - 230]))

    story.append(Paragraph('Buttons', styles['h2']))
    btn_data = [
        ['Left encoder button', 'Cycle mask mode: Off \u2192 Stochastic \u2192 Burst \u2192 Off'],
        ['Right encoder button', 'Cycle formant count: 1 \u2192 2 \u2192 3 \u2192 1'],
        ['Button 3', 'Cycle voice count: 1 \u2192 2 \u2192 3 \u2192 4 \u2192 1'],
        ['Button 4', 'Cycle chord type (14 options)'],
    ]
    story.append(make_table(
        ['Button', 'Action'],
        btn_data,
        [130, int(PAGE_W) - 140]))

    story.append(Paragraph('Outputs', styles['h2']))
    story.append(Paragraph(
        'Output L and R are routable to any bus via the Outputs page (default: L = bus 13, R = bus 14). '
        'Six optional auxiliary outputs are available on the Aux Out page, all defaulting to bus 0 (disabled):',
        styles['body']))

    aux_data = [
        ['Trig Out', '1.0 on each new pulse (voice 0)', 'Clock/trigger synced to pulse rate'],
        ['Env Out', 'Max envelope across all voices', 'Envelope follower for external modulation'],
        ['Pre-clip L/R', 'Stereo before soft clip', 'Raw signal for external processing'],
        ['Oct Down L/R', 'Stereo frequency divider', 'Sub-octave, one octave below fundamental'],
    ]
    story.append(make_table(
        ['Output', 'Signal', 'Use'],
        aux_data,
        [90, 180, int(PAGE_W) - 280]))

    story.append(Spacer(1, 0.1 * inch))
    story.append(HRFlowable(width='100%', thickness=0.5, color=VERY_LIGHT))

    # ================================================================
    # SOUND DESIGN TIPS
    # ================================================================
    story.append(h1_with_anchor('Sound Design Tips', 'sounddesign', styles))

    story.append(Paragraph('Formant Frequencies', styles['h2']))
    story.append(Paragraph(
        'Formant frequencies have the most dramatic effect on timbre. They define '
        'spectral peaks analogous to vocal formants in speech.',
        styles['body']))
    tips_formant = [
        '<b>Low formants (20\u2013100 Hz)</b>: Deep, subharmonic rumbles. F1=20 Hz produces a thick bass drone.',
        '<b>Vowel-like tones</b>: F1=270, F2=2300 for "ah"; F1=300, F2=870 for "oo." Experiment with vocal formant charts.',
        '<b>Harmonic stacking</b>: Set formants to integer multiples of the fundamental for bright, reinforced harmonics.',
        '<b>Inharmonic/metallic</b>: Non-integer ratios (F1=200, F2=347, F3=511) produce bell-like or metallic timbres.',
        '<b>Formant Track mode</b>: Scales formant frequencies with pitch. A formant at 400 Hz doubles to 800 Hz one octave up, preserving spectral shape across the keyboard.',
    ]
    for t in tips_formant:
        story.append(Paragraph('\u2022 ' + t, styles['bullet']))

    story.append(Paragraph('Duty Cycle', styles['h2']))
    tips_duty = [
        '<b>80\u2013100%%</b>: Full, warm \u2014 approaching wavetable synthesis.',
        '<b>30\u201360%%</b>: The characteristic pulsar "buzz." Sweet spot for most patches.',
        '<b>5\u201320%%</b>: Sparse, clicking, particle-like textures. Amp jitter is especially audible here.',
        '<b>Formant Duty Mode</b>: Automatically ties duty to formant frequency, keeping pulsaret waveform cycles consistent.',
    ]
    for t in tips_duty:
        story.append(Paragraph('\u2022 ' + t, styles['bullet']))

    story.append(Paragraph('Masking', styles['h2']))
    tips_mask = [
        '<b>Stochastic masking</b> at 10\u201330%% adds subtle grit. At 70\u201390%% the tone dissolves into a sparse particle cloud.',
        '<b>Burst masking</b> creates micro-rhythmic patterns. Try On=1, Off=3 for stutter; On=7, Off=1 for subtle hiccup.',
        '<b>Indep Mask</b> gives each formant its own mask decision. In stochastic mode, different formant subsets sound on each pulse. In burst mode, formants alternate.',
        '<b>Amp jitter + stochastic masking</b>: Two layers of randomness \u2014 some pulses quieter, some missing entirely.',
    ]
    for t in tips_mask:
        story.append(Paragraph('\u2022 ' + t, styles['bullet']))

    story.append(Paragraph('Effects', styles['h2']))
    tips_fx = [
        '<b>Timing Jitter</b>: 5\u201315%% adds warmth and analog drift. With multiple unison voices, each drifts independently for natural chorusing.',
        '<b>Glisson</b>: Sweeps pitch within each pulsaret. Subtle values (\u00b10.3\u20131.0) add shimmer; extreme values (\u00b17\u201310) create laser-like chirps.',
        '<b>Amp Jitter</b>: 10\u201320%% adds organic variation like a bowed string. High values (60\u2013100%%) make the sound fragile.',
    ]
    for t in tips_fx:
        story.append(Paragraph('\u2022 ' + t, styles['bullet']))

    story.append(Paragraph('Polyphony and Chords', styles['h2']))
    story.append(Paragraph(
        'In Free Run mode, additional voices are tuned relative to the base pitch by the '
        'selected Chord Type. <b>Harmonic intervals</b> (Unison, Octaves, Fifths, Sub+Oct) use '
        'pure frequency ratios. <b>Tonal chords</b> (Major, Minor, Maj7, etc.) use equal '
        'temperament semitone offsets. Each voice has independent phase, envelope, masking, '
        'and jitter state. Volume is normalized by voice count parameter (not active voices) '
        'to prevent level jumps.',
        styles['body']))

    story.append(PageBreak())

    # ================================================================
    # PATCH IDEAS
    # ================================================================
    story.append(h1_with_anchor('Patch Ideas', 'patches', styles))
    story.append(Paragraph(
        'Starting points for exploring Spaluter. Each patch lists specific parameter '
        'settings and describes the resulting sound.',
        styles['body']))

    patch_data = [
        ['Bass Drone',
         'Sinc (3.0), Gaussian, 40%% duty, F1=80 Hz, Free Run, base pitch C1. '
         'Slow LFO on Formant 1 CV for movement. A deep, slowly evolving low-frequency drone.'],
        ['Vocal Pad',
         'Sine (0.0), Hann, 60%% duty, F1=270, F2=2300, F3=800. 4 voices Maj7. '
         'Slow LFO on F1 CV to morph vowels. Lush choral pad with shifting vowel-like timbre.'],
        ['Percussive Texture',
         'Pulse (8.0), Exp Decay, 20%% duty, F1=400. Burst mask 2on/3off. Short attack, '
         'short release. Glisson +3.0. Rhythmic clicking bursts with pitch-swept transients.'],
        ['Evolving Ambient',
         'Sinc (3.0), Gaussian, 50%% duty, F1=200, F2=600, F3=1200. 4 voices Octaves. '
         'Stochastic mask 20%%, Amp Jit 15%%, Time Jit 10%%, Indep Mask on. Slow CV on all '
         '3 formant inputs. A shimmering, constantly shifting ambient texture.'],
        ['Metallic Bell',
         'Triangle (4.0), Hann, 70%% duty, F1=200, F2=347, F3=511 (inharmonic ratios). '
         'CV mode, short attack, long release (2000 ms). No masking. Struck bell tone with '
         'non-harmonic partials and long, ringing decay.'],
        ['Granular Cloud',
         'Noise (9.0), Gaussian, 15%% duty, stochastic mask 60%%, Amp Jit 40%%, '
         'Time Jit 30%%. Free Run, 2 voices Unison. Very sparse, dissolving texture '
         'of random noise grains.'],
        ['Organ Tone',
         'Square (6.0), Rectangular, 100%% duty, F1=fundamental, Formant Track on. '
         '4 voices Power chord. Classic hollow organ sound with stacked fifths.'],
        ['Laser Chirps',
         'Sinc (3.0), Exp Decay, 30%% duty, Glisson +8.0. Short attack, medium release. '
         'Each pulse sweeps pitch dramatically. Add CV trigger for rhythmic firing. '
         'Sci-fi laser and chirp effects.'],
        ['Sub Bass Layer',
         'Saw (5.0), Hann, 80%% duty, F1=40 Hz. Free Run, base pitch C0 (MIDI 12). '
         'Use sub-octave output routed to a separate bus for layering. Deep, warm sub-bass '
         'foundation.'],
        ['Spectral Freeze',
         'Sine x3 (2.0), Gaussian, 50%% duty, F1=300, F2=900. CV mode with long release '
         '(3000 ms). Each triggered voice freezes its parameters on release. Layer 4 frozen '
         'timbres by triggering at different settings for a spectral snapshot collage.'],
    ]
    for name, desc in patch_data:
        story.append(KeepTogether([
            Paragraph('<b>%s:</b> %s' % (name, desc), styles['body']),
        ]))

    story.append(PageBreak())

    # ================================================================
    # FURTHER READING
    # ================================================================
    story.append(h1_with_anchor('Further Reading', 'reading', styles))
    refs = [
        'Curtis Roads, <i>Microsound</i> (MIT Press, 2001) \u2014 the definitive reference on pulsar synthesis and micro-timescale sound.',
        'Curtis Roads, "Sound Composition with Pulsars," <i>Journal of the Audio Engineering Society</i>, 2001.',
        'Curtis Roads, <i>The Computer Music Tutorial</i> (MIT Press, 1996) \u2014 broader context on granular and particle synthesis.',
        'Alberto de Campo \u2014 related implementations and research on microsound techniques.',
        'Wikipedia: Pulsar Synthesis \u2014 en.wikipedia.org/wiki/Pulsar_synthesis',
    ]
    for r in refs:
        story.append(Paragraph('\u2022 ' + r, styles['bullet']))

    story.append(Spacer(1, 0.5 * inch))
    story.append(HRFlowable(width='40%', thickness=0.5, color=VERY_LIGHT, hAlign='LEFT'))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph('<a href="https://github.com/sroons/spaluter" color="#2266aa">github.com/sroons/spaluter</a>', styles['caption']))

    # Build
    doc.build(story)
    return True


if __name__ == '__main__':
    import tempfile
    # Pass 1: build to temp file to capture page numbers
    tmp_path = os.path.join(tempfile.gettempdir(), '_spaluter_toc_pass.pdf')
    build_pdf(tmp_path)
    # Pass 2: rebuild with real page numbers now in _anchor_pages
    build_pdf(OUT_PATH)
    # Clean up temp
    try:
        os.unlink(tmp_path)
    except OSError:
        pass
    print('PDF generated: %s' % OUT_PATH)
