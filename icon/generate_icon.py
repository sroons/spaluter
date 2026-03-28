#!/usr/bin/env python3
"""Generate Spaluter icon PNG — three overlapping windowed-sinc formant
waveforms (blue F1, orange F2, green F3) on dark navy, flat colors.
Rectangular format, simplified."""

import math
import struct
import zlib

WIDTH = 800
HEIGHT = 320
BG = (24, 28, 40)

BASELINE_Y_FRAC = 0.55

# Formant waveforms: (sigma, omega, amplitude_px, color)
FORMANTS = [
    # F1 blue — widest, tallest, slow oscillation
    (160, 0.038, 100, (88, 152, 224)),
    # F2 orange — medium
    (80, 0.08, 52, (224, 112, 64)),
    # F3 green — narrowest, tightest
    (36, 0.17, 24, (80, 216, 104)),
]


def sinc_wave(x, cx, sigma, omega, amp):
    dx = x - cx
    envelope = math.exp(-0.5 * (dx / sigma) ** 2)
    return amp * envelope * math.cos(omega * dx)


def make_icon():
    base_y = int(HEIGHT * BASELINE_Y_FRAC)
    cx = WIDTH * 0.5

    # Precompute curves
    curves = []
    for sigma, omega, amp, color in FORMANTS:
        wave = []
        for x in range(WIDTH):
            val = sinc_wave(x, cx, sigma, omega, amp)
            wave.append(base_y - val)
        curves.append((wave, color))

    pixels = []
    for y in range(HEIGHT):
        row = []
        for x in range(WIDTH):
            r, g, b = BG

            # Baseline
            if abs(y - base_y) <= 0.6:
                r = int(r + (42 - r) * 0.4)
                g = int(g + (48 - g) * 0.4)
                b = int(b + (72 - b) * 0.4)

            # Draw each formant curve
            for wave, color in curves:
                curve_y = wave[x]
                dist = abs(y - curve_y)
                if dist < 2.0:
                    alpha = max(0.0, 1.0 - dist / 1.8)
                    r = int(r + (color[0] - r) * alpha)
                    g = int(g + (color[1] - g) * alpha)
                    b = int(b + (color[2] - b) * alpha)

            row.append((max(0, min(255, r)),
                        max(0, min(255, g)),
                        max(0, min(255, b)), 255))
        pixels.append(row)

    return pixels


def write_png(filename, pixels, width, height):
    def make_chunk(chunk_type, data):
        chunk = chunk_type + data
        crc = zlib.crc32(chunk) & 0xFFFFFFFF
        return struct.pack('>I', len(data)) + chunk + struct.pack('>I', crc)

    sig = b'\x89PNG\r\n\x1a\n'
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    ihdr = make_chunk(b'IHDR', ihdr_data)

    raw = b''
    for row_data in pixels:
        raw += b'\x00'
        for r, g, b, a in row_data:
            raw += struct.pack('BBBB', r, g, b, a)
    compressed = zlib.compress(raw, 9)
    idat = make_chunk(b'IDAT', compressed)
    iend = make_chunk(b'IEND', b'')

    with open(filename, 'wb') as f:
        f.write(sig + ihdr + idat + iend)


if __name__ == '__main__':
    import os
    print(f"Generating Spaluter icon ({WIDTH}x{HEIGHT})...")
    pixels = make_icon()
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'spaluter_icon.png')
    write_png(out_path, pixels, WIDTH, HEIGHT)
    print(f"Saved to {out_path}")
