# disting NT Plugin Development Guide

You are assisting with development of a plugin for the Expert Sleepers disting NT Eurorack module. Apply the following knowledge to all code you write or review.

## Platform

- **MCU**: STM32H7 Cortex-M7 at 480 MHz
- **Compiler**: `arm-none-eabi-c++` with `-std=c++11 -mcpu=cortex-m7 -mfpu=fpv5-d16 -mfloat-abi=hard -mthumb -fno-rtti -fno-exceptions -Os -ffast-math -fPIC -Wall`
- **No RTTI, no exceptions** — cannot use `dynamic_cast`, `typeid`, `throw`, or `try/catch`
- **Build**: `make` produces `plugins/<name>.o`, copy to SD card `plugins/` folder
- **Sample rate**: available at runtime via `NT_globals.sampleRate` (typically 48000)
- **Display**: 256x64 px, 4-bit grayscale (0-15), each byte = 2 pixels in `NT_screen[128*64]`
- **Profiling**: `NT_getCpuCycleCount()` — 480 MHz clock, so 1 cycle ~2.08 ns

## Memory Architecture

Four memory regions with different performance characteristics:

| Region | Purpose | Speed | Use for |
|--------|---------|-------|---------|
| **SRAM** | Algorithm struct, cached params | Fast | Main algorithm state, non-hot-path data |
| **DRAM** | Large allocations | Slower | Lookup tables, sample buffers, large arrays |
| **DTC** | Tightly-coupled data memory | Fastest | Per-sample hot state (voices, filters, oscillators) |
| **ITC** | Tightly-coupled instruction memory | Fastest | Code only (hot functions) |

Memory pointers (`ptrs.sram`, `ptrs.dram`, `ptrs.dtc`, `ptrs.itc`) are `uint8_t*` — use `reinterpret_cast`, not `static_cast`, when casting to your struct types.

Request sizes in `calculateRequirements()`:
```cpp
req.numParameters = kNumParams;
req.sram = sizeof(_myAlgorithm);
req.dram = sizeof(_myDRAM);
req.dtc = sizeof(_myDTC);
```

## Plugin Lifecycle

```
calculateStaticRequirements() → initialise()     // once per plugin scan/load (shared data)
calculateRequirements() → construct()            // per instance
parameterChanged()                               // when user changes a param
step()                                           // audio callback (per block)
draw()                                           // display callback (host-controlled rate)
customUi()                                       // button/encoder/pot input (if hasCustomUi)
```

### construct()
- Allocate your `_NT_algorithm` subclass from one of the memory regions
- Use placement new: `_myAlgorithm* alg = new(ptrs.sram) _myAlgorithm;`
- Set `alg->parameters` and `alg->parameterPages`
- Initialize all state
- Return the `_NT_algorithm*`

### step()
- `busFrames` contains all buses contiguously: `numFrames` of bus 0, then bus 1, etc.
- `numFramesBy4` is frame count / 4 — actual frame count is `numFramesBy4 * 4`
- Bus offset: `busFrames + (busIndex - 1) * numFrames` (buses are 1-indexed in params)
- Runs at audio rate — performance-critical

### draw()
- Return `true` to suppress the default parameter line at the top
- Use `NT_drawText()`, `NT_drawShapeI()`, `NT_drawShapeF()`, `NT_intToString()`, `NT_floatToString()`
- Write directly to `NT_screen[]` for pixel-level control
- No `requestDraw` API — host controls call frequency
- Cross-interrupt safety: use `volatile` fields written by `step()`, read by `draw()`

## Parameters

### Definition
```cpp
struct _NT_parameter {
    const char* name;
    int16_t min, max, def;
    uint8_t unit;       // kNT_unitNone, kNT_unitEnum, kNT_unitHz, kNT_unitPercent, kNT_unitMIDINote, etc.
    uint8_t scaling;    // kNT_scalingNone, kNT_scaling10, kNT_scaling100, kNT_scaling1000
    char const * const * enumStrings;  // NULL unless unit is kNT_unitEnum
};
```

- `kNT_scaling10` divides stored `int16_t` by 10 for display (e.g., stored 25 = displayed 2.5)
- `kNT_unitHasStrings` — `parameterString()` callback provides display text
- `kNT_unitConfirm` — user must confirm changes, also calls `parameterString()`
- Values accessed via `self->v[paramIndex]` (int16_t)

### Parameter Pages
```cpp
struct _NT_parameterPage {
    const char* name;
    uint8_t numParams;
    uint8_t group;       // non-zero! pages with same group share cursor position
    uint8_t unused[2];
    const uint8_t* params;  // array of parameter indices
};
```
**All page groups must be explicit non-zero** to avoid auto-assign collisions (group 0 gets auto-assigned to page index).

### Validation
Use `static_assert(kNumParams == ARRAY_SIZE(parametersDefault))` to catch count mismatches at compile time. Enum order must match `parametersDefault[]` array order exactly.

### I/O Parameters (macros that expand to entries)
```cpp
NT_PARAMETER_AUDIO_INPUT("name", min, default)     // 1 entry
NT_PARAMETER_CV_INPUT("name", min, default)         // 1 entry
NT_PARAMETER_AUDIO_OUTPUT("name", min, default)     // 1 entry
NT_PARAMETER_AUDIO_OUTPUT_WITH_MODE("name", min, d) // 2 entries (bus + mode)
NT_PARAMETER_CV_OUTPUT_WITH_MODE("name", min, d)    // 2 entries (bus + mode)
```

## API Offset Rules — CRITICAL

These are the #1 source of bugs. Get these wrong and parameters silently affect the wrong thing.

| Function | Offset needed? | Index type |
|----------|---------------|------------|
| `NT_setParameterGrayedOut(algIdx, param + NT_parameterOffset(), gray)` | YES | Global |
| `NT_setParameterFromUi(algIdx, param + NT_parameterOffset(), value)` | YES | Global |
| `NT_setParameterFromAudio(algIdx, param + NT_parameterOffset(), value)` | YES | Global |
| `NT_updateParameterDefinition(algIdx, param)` | NO | Plugin-local |
| `NT_updateParameterPages(algIdx)` | NO | N/A |
| `self->v[param]` | NO | Plugin-local |
| `self->parameters[param]` | NO | Plugin-local |

**`NT_setParameterFromAudio()` sets `v[]` AND triggers `parameterChanged()`** — calling it from `step()` on a parameter you also read from `v[]` creates a feedback loop. Use local variables instead.

## Buses

- 64 total: 1-12 inputs, 13-20 outputs, 21-64 aux
- Default output bus = 13
- Bus selector param value 0 = "none" (no bus assigned)
- Read input: `float* input = busFrames + (busValue - 1) * numFrames;`
- Write output: `float* output = busFrames + (busValue - 1) * numFrames;`

## Custom UI (Buttons, Encoders, Pots)

```cpp
uint32_t hasCustomUi(_NT_algorithm* self) {
    return kNT_button3 | kNT_button4 | kNT_encoderButtonL | kNT_encoderButtonR;
}

void customUi(_NT_algorithm* self, const _NT_uiData& data) {
    // Edge detection for buttons:
    if ((data.controls & kNT_button3) && !(data.lastButtons & kNT_button3)) {
        // button 3 just pressed
    }
    // Encoders: data.encoders[0] = left (±1 or 0), data.encoders[1] = right
    // Pots: data.pots[0..2] = 0.0-1.0 positions
}

void setupUi(_NT_algorithm* self, _NT_float3& pots) {
    // Called when UI appears — sync soft-takeover positions
    pots[0] = /* current value mapped to 0.0-1.0 */;
}
```

Available controls: `kNT_button1`-`4`, `kNT_potButtonL/C/R`, `kNT_encoderButtonL/R`, `kNT_encoderL/R`, `kNT_potL/C/R`

## MIDI

```cpp
void midiMessage(_NT_algorithm* self, uint8_t status, uint8_t data1, uint8_t data2) {
    uint8_t type = status & 0xF0;
    uint8_t channel = status & 0x0F;
    // 0x90 = note on, 0x80 = note off, 0xB0 = CC, 0xE0 = pitch bend
}
```

Send MIDI: `NT_sendMidi3ByteMessage(kNT_destinationUSB | kNT_destinationBreakout, b0, b1, b2)`

## SD Card / WAV Samples

### Async sample loading
```cpp
_NT_wavRequest wavRequest;
wavRequest.folder = folderIndex;
wavRequest.sample = sampleIndex;
wavRequest.dst = myBuffer;
wavRequest.numFrames = count;
wavRequest.startOffset = 0;
wavRequest.channels = kNT_WavMono;    // or kNT_WavStereo
wavRequest.bits = kNT_WavBits32;      // float output
wavRequest.progress = kNT_WavProgress; // show progress bar
wavRequest.callback = myCallback;
wavRequest.callbackData = this;
NT_readSampleFrames(wavRequest);       // returns true if initiated
```

- The `_NT_wavRequest` struct **must persist** until callback fires (not stack-allocated)
- Callback receives `(void* callbackData, bool success)`
- Query folders: `NT_getNumSampleFolders()`, `NT_getSampleFolderInfo(idx, info)`
- Query files: `NT_getSampleFileInfo(folder, sample, info)` — gives `numFrames`, `sampleRate`, `channels`, `bits`
- Check SD card: `NT_isSdCardMounted()` — card may not be ready when plugin constructs

### Streaming (for long samples)
```cpp
_NT_stream stream;  // allocate NT_globals.streamSizeBytes
_NT_streamOpenData openData;
openData.streamBuffer = myBuffer;  // allocate NT_globals.streamBufferSizeBytes
openData.folder = f; openData.sample = s;
openData.velocity = 1.0f;
openData.startOffset = 0;
openData.reverse = false;
openData.rrMode = kNT_RRModeSequential;
NT_streamOpen(stream, openData);
uint32_t rendered = NT_streamRender(stream, frameBuffer, numFrames, speed);
```

### Wavetables
```cpp
_NT_wavetableRequest req;
req.index = wavetableIndex;
req.table = myInt16Buffer;
req.tableSize = maxFrames;
req.callback = myCallback;
req.callbackData = this;
NT_readWavetable(req);
// After load: req.numWaves, req.waveLength, req.usingMipMaps
float value = NT_evaluateWavetable(req, eval); // convenience function
```

## Display Text Gotchas

- `kNT_textTiny` (3x5 font) **lacks `%` glyph** — use `" pct."` or `kNT_textNormal` instead
- `NT_drawText(x, y, str, colour, alignment, size)` — colour 0-15 (4-bit grayscale)
- `NT_intToString(buf, value)` and `NT_floatToString(buf, value, decimalPlaces)` return string length

## Performance Tips

- FPv5 single-precision: `fmul` ~1 cycle, `fdiv` ~14 cycles, `fsqrt` ~14 cycles — prefer multiply by reciprocal
- Keep per-sample state in DTC for cache-free access
- `-ffast-math` is enabled — `NaN` propagation is not guaranteed, use explicit guards
- `expf()`, `sinf()`, `cosf()` are expensive — precompute in tables or use polynomial approximations where possible
- Voice loops inside sample loops (not the other way around) to keep voice state in registers

## Common Patterns

### One-pole filter (envelope, smoothing)
```cpp
float coeff = expf(-1.0f / (ms * sr * 0.001f));
// Per sample:
smoothed = target + coeff * (smoothed - target);
```

### DC-blocking highpass (~25 Hz)
```cpp
float dcCoeff = 1.0f - (2.0f * M_PI * 25.0f / sr);
// Per sample:
float y = x - prevX + dcCoeff * prevY;
prevX = x; prevY = y;
```

### Soft clip (Pade tanh approximation)
```cpp
float fastTanh(float x) {
    float x2 = x * x;
    return x * (27.0f + x2) / (27.0f + 9.0f * x2);
}
```

### Table read with linear interpolation (power-of-2 size)
```cpp
float readTable(const float* table, int size, float phase) {
    float pos = phase * size;
    int idx = (int)pos;
    float frac = pos - idx;
    idx &= (size - 1);         // wrap
    int idx2 = (idx + 1) & (size - 1);
    return table[idx] + frac * (table[idx2] - table[idx]);
}
```
