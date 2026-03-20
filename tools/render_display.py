#!/usr/bin/env python3
"""Render the Spaluter real-time display layout as a PNG (256x64 scaled up)."""

import math
from PIL import Image, ImageDraw, ImageFont

SCALE = 4  # Scale up for visibility
W, H = 256, 64
IMG_W, IMG_H = W * SCALE, H * SCALE

# Brightness to grayscale (0-15 mapped to 0-255)
def bri(b):
    return int(b * 255 / 15)

def draw_box(draw, x0, y0, x1, y1, b):
    """Draw an unfilled rectangle (box outline)."""
    c = bri(b)
    draw.rectangle([x0*SCALE, y0*SCALE, x1*SCALE, y1*SCALE], outline=(c,c,c), width=max(1, SCALE//2))

def draw_rect(draw, x0, y0, x1, y1, b):
    """Draw a filled rectangle."""
    c = bri(b)
    draw.rectangle([x0*SCALE, y0*SCALE, x1*SCALE, y1*SCALE], fill=(c,c,c))

def draw_line(draw, x0, y0, x1, y1, b):
    c = bri(b)
    draw.line([x0*SCALE, y0*SCALE, x1*SCALE, y1*SCALE], fill=(c,c,c), width=max(1, SCALE//2))

def draw_text(draw, font, x, y, text, b):
    c = bri(b)
    draw.text((x*SCALE, y*SCALE), text, fill=(c,c,c), font=font)

def read_table_morph_sim(pulsaret_idx, t):
    """Simulate pulsaret morph - blend between sine shapes."""
    harmonics = 1 + pulsaret_idx * 0.8
    s = 0.0
    for h in range(1, int(harmonics) + 2):
        weight = 1.0 / h
        if h > harmonics:
            weight *= (harmonics - int(harmonics))
        s += weight * math.sin(2 * math.pi * h * t)
    return max(-1.0, min(1.0, s * 0.7))

def read_window_morph_sim(window_idx, t):
    """Simulate window morph - Hann-like window."""
    return 0.5 * (1.0 - math.cos(2 * math.pi * t))

def main():
    img = Image.new("RGB", (IMG_W, IMG_H), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Try to get a small monospace font
    try:
        font_tiny = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 5 * SCALE // 2)
    except:
        font_tiny = ImageFont.load_default()

    # === Default parameter values ===
    pulsaret_idx = 2.5
    window_idx = 0.5
    duty = 0.5
    fundamental_hz = 32.7
    formant_hz = [20.0, 200.0, 400.0]
    formant_count = 2
    voice_count = 1
    chord_type = 0  # Unison
    gate_mode = 1   # Free Run
    amplitude = 0.0
    drive = 1.0     # 100%
    env_value = 0.0
    any_gate = True
    peak_level = 0.0
    cpu_percent = 3.2

    # === Three separate waveform previews ===
    viewW = 46
    viewH = 20
    viewY = 30
    gap = 4
    x0_puls = 4
    x0_win = x0_puls + viewW + gap
    x0_duty = x0_win + viewW + gap

    formant_ratio = formant_hz[0] / max(fundamental_hz, 0.1)

    # --- Pulsaret preview ---
    draw_box(draw, x0_puls - 1, viewY - viewH // 2 - 1,
             x0_puls + viewW + 1, viewY + viewH // 2 + 1, 3)
    prevY = viewY
    for x in range(viewW):
        phase = x / viewW
        tp = phase * formant_ratio
        tp -= int(tp)
        if tp < 0: tp += 1.0
        s = read_table_morph_sim(pulsaret_idx, tp)
        pixY = viewY - int(s * viewH / 2)
        if x > 0:
            draw_line(draw, x0_puls + x - 1, prevY, x0_puls + x, pixY, 15)
        prevY = pixY

    # --- Window preview ---
    draw_box(draw, x0_win - 1, viewY - viewH // 2 - 1,
             x0_win + viewW + 1, viewY + viewH // 2 + 1, 3)
    prevY = viewY
    for x in range(viewW):
        phase = x / viewW
        s = read_window_morph_sim(window_idx, phase)
        pixY = viewY - int(s * viewH / 2)
        if x > 0:
            draw_line(draw, x0_win + x - 1, prevY, x0_win + x, pixY, 15)
        prevY = pixY

    # --- Duty cycle preview (pulsaret * window, centered in period) ---
    draw_box(draw, x0_duty - 1, viewY - viewH // 2 - 1,
             x0_duty + viewW + 1, viewY + viewH // 2 + 1, 3)
    duty_start = (1.0 - duty) * 0.5
    prevY = viewY
    for x in range(viewW):
        p = x / viewW
        s = 0.0
        if p >= duty_start and p < duty_start + duty:
            pp = (p - duty_start) / duty
            tp = pp * formant_ratio
            tp -= int(tp)
            if tp < 0: tp += 1.0
            s = read_table_morph_sim(pulsaret_idx, tp)
            s *= read_window_morph_sim(window_idx, pp)
        pixY = viewY - int(s * viewH / 2)
        if x > 0:
            draw_line(draw, x0_duty + x - 1, prevY, x0_duty + x, pixY, 15)
        prevY = pixY

    # Layout refs
    waveX = x0_puls
    waveW_total = x0_duty + viewW - x0_puls
    waveY = viewY
    waveH = viewH

    # === Right-side info column ===
    infoX = waveX + waveW_total + 8
    freqY = waveY - 8

    # Formant count + voice count (above frequency)
    fc_text = f"{formant_count}F {voice_count}V"
    draw_text(draw, font_tiny, infoX, waveY - 16, fc_text, 8)

    # Frequency readout + chord type on same line
    freq_str = f"{fundamental_hz:.1f} Hz"
    draw_text(draw, font_tiny, infoX, freqY, freq_str, 15)

    chord_labels = ["UNI","OCT","5TH","SUB","MAJ","MIN","MA7","MI7",
                    "SU4","DM7","DIM","AUG","PWR","OP5"]
    if gate_mode == 1:
        bright = 10 if voice_count > 1 else 4
        freq_text_w = len(freq_str) * 4  # ~4px per char in kNT_textTiny
        draw_text(draw, font_tiny, infoX + freq_text_w + 4, freqY, chord_labels[chord_type], bright)

    # Amplitude readout (beneath frequency)
    amp_text = f"{amplitude * 100:.0f}%"
    draw_text(draw, font_tiny, infoX, waveY, amp_text, 10)

    # Drive readout (beneath amplitude)
    drive_text = f"{drive * 100:.0f}% D"
    drive_bright = 10 if drive > 1.0 else 6
    draw_text(draw, font_tiny, infoX, waveY + 8, drive_text, drive_bright)

    # Envelope level bar
    barX = infoX
    barY = waveY + 8
    barW = 30
    barH = 4
    draw_box(draw, barX, barY, barX + barW, barY + barH, 5)
    fill_w = int(env_value * barW)
    if fill_w > 0:
        draw_rect(draw, barX, barY, barX + fill_w, barY + barH, 15)

    # Gate indicator
    if any_gate:
        draw_rect(draw, barX + barW + 4, barY, barX + barW + 8, barY + barH, 15)

    # Gate mode label
    if gate_mode == 1:
        draw_text(draw, font_tiny, barX + barW + 12, barY, "FR", 15)
    elif gate_mode == 2:
        draw_text(draw, font_tiny, barX + barW + 12, barY, "CV", 15)

    # === Peak level meter (spans all 3 views) ===
    pkBarX = waveX
    pkBarY = waveY + waveH // 2 + 4
    pkBarW = waveW_total
    pkBarH = 3
    draw_box(draw, pkBarX, pkBarY, pkBarX + pkBarW, pkBarY + pkBarH, 3)
    pk_fill = int(peak_level * pkBarW)
    if pk_fill > 0:
        draw_rect(draw, pkBarX, pkBarY, pkBarX + pk_fill, pkBarY + pkBarH, 15)

    # === Formant frequency readouts ===
    fmtY = pkBarY + pkBarH + 4
    for f in range(3):
        brightness = 15 if f < formant_count else 4
        xPos = waveX + f * 56
        label = f"F{f+1}:"
        draw_text(draw, font_tiny, xPos, fmtY, label, brightness)
        draw_text(draw, font_tiny, xPos + 16, fmtY, f"{formant_hz[f]:.0f}", brightness)

    # CPU load readout (bottom right)
    cpu_text = f"CPU:{cpu_percent:.1f}"
    draw_text(draw, font_tiny, barX, fmtY, cpu_text, 6)

    # Draw screen border for reference
    draw.rectangle([0, 0, IMG_W - 1, IMG_H - 1], outline=(40, 40, 40), width=1)

    out_path = "/Users/seanrooney/Dev/distingNT/disting_pulsar/tools/display_layout.png"
    img.save(out_path)
    print(f"Saved to {out_path}")

if __name__ == "__main__":
    main()
