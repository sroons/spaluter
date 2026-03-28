---
# Code Review — 2026-03-22 17:19:38
## Target: `src/spaluter.cpp`

## Issues

### [MAJOR] setupUi pot mapping swapped for Pot C and Pot R
- **Location**: src/spaluter.cpp:2472-2474
- **Issue**: In `customUi()`, Pot C (pots[1]) maps to Window and Pot R (pots[2]) maps to Duty Cycle. But in `setupUi()`, pots[1] is initialized from kParamDutyCycle and pots[2] from kParamWindow — the opposite assignment. This means soft-takeover positions are wrong and pots will jump when first touched after loading the algorithm.
- **Suggestion**: Swap the assignments in `setupUi()` to match `customUi()`:
  ```cpp
  pots[0] = self->v[kParamPulsaret] / 90.0f;        // Pot L: Pulsaret
  pots[1] = self->v[kParamWindow] / 80.0f;           // Pot C: Window
  pots[2] = (self->v[kParamDutyCycle] - 1) / 99.0f;  // Pot R: Duty
  ```

### [MAJOR] Snapshot update runs per-sample inside inner loop
- **Location**: src/spaluter.cpp:1804-1832
- **Issue**: The full `_voiceSnapshot` (~96 bytes) is copied for every gated voice on every sample. Snapshot data comes from block-rate values (CV averages, cached params) that don't change within a block. This is unnecessary per-sample work on a Cortex-M7 where DTC bandwidth is precious.
- **Suggestion**: Hoist the snapshot update out of the sample loop. Update snapshots once per block (before the sample loop) for all gated voices. Only the `gate` check needs to remain per-sample to catch mid-block gate transitions in CV mode, but the actual snapshot data is constant across the block.

### [MINOR] Burst counter increment order inconsistency between mask modes
- **Location**: src/spaluter.cpp:1935 vs 1917
- **Issue**: In the uniform masking branch (non-perFormantMask), `burstCounter` is incremented *before* the mask comparison (line 1935). In the per-formant branch, it is incremented *after* the formant loop (line 1917). This means the first pulse after enabling burst masking will behave differently depending on whether per-formant masking is on or off.
- **Suggestion**: Make the increment order consistent — increment after the comparison in both branches, so pulse 0 always starts at counter position 0.

### [MINOR] Comment/code mismatch: window table count
- **Location**: src/spaluter.cpp:635
- **Issue**: The comment block says "Window functions (5 tables)" but there are 9 window tables (kNumWindows = 9), and the code generates indices 0-8 (rectangular, gaussian, hann, exp decay, linear decay, tukey, blackman-harris, reverse exp, triangle).
- **Suggestion**: Update the comment to "Window functions (9 tables)" and list all 9 window types.

### [MINOR] Comment/code mismatch: DTC size in header
- **Location**: src/spaluter.cpp:17
- **Issue**: The architecture comment says "DTC (~424 B)" but the struct comment at line 136 says "~896 bytes". The actual size with 4 voices including snapshots plus overhead is closer to ~808 B.
- **Suggestion**: Update the header comment to match the actual DTC size (~808 B).

### [MINOR] Formant Hz range mismatch in enum comments
- **Location**: src/spaluter.cpp:165-167
- **Issue**: The enum comments say formant range is "20-8000 Hz" but the parameter definitions (lines 341-343) set max=2000.
- **Suggestion**: Update the enum comments to say "20-2000 Hz".

### [NIT] CV averaging loop checks 16 null pointers per sample
- **Location**: src/spaluter.cpp:1553-1571
- **Issue**: The single combined CV averaging loop checks all 16 CV pointer null checks on every iteration. While this is outside the critical inner loop, splitting into per-pointer loops would allow the compiler to optimize each as a simple tight accumulation when the pointer is non-null, and skip entirely when null.
- **Suggestion**: Consider restructuring as individual per-pointer loops, or accept the current approach as good enough given it only runs once per block.

### [NIT] Unused macro `ST(n)` defined then immediately undef'd
- **Location**: src/spaluter.cpp:283, 326
- **Issue**: `#define ST(n) (1.0f)` is defined as a "placeholder" but is never used — `initChordRatios()` uses a lambda instead. The define/undef is dead code.
- **Suggestion**: Remove the `#define ST` and `#undef ST` lines.

## Strengths

- **Memory architecture is well-designed**: Clear separation of DRAM (tables), DTC (hot per-sample state), and SRAM (algorithm struct) is ideal for the Cortex-M7's tightly-coupled memory system.
- **Voice allocation is robust**: The 3-tier MIDI allocation (retrigger, free, LRU steal) and 2-tier CV allocation with proper edge detection and overlapping releases are solid.
- **Snapshot-on-release pattern**: Freezing timbral parameters when a voice releases prevents audible parameter changes on decaying voices — a thoughtful design choice.
- **Parameter graying logic**: Dynamic UI state management (graying out irrelevant params based on mode) provides a clean user experience.
- **DC blocking and soft clipping**: Per-voice DC block followed by a single Pade tanh soft clip on the sum is the right signal chain order, and the fast approximations are appropriate for the target.
- **Thorough documentation**: Function-level block comments, inline explanations, and the header overview give a clear mental model of the entire system. The code is exceptionally readable for an embedded audio plugin.
- **Safe volatile display state**: Using `volatile` for cross-interrupt display fields is correct for ARM single-word atomicity, and the fields are all independent (no multi-field consistency needed).
- **Custom UI is well-implemented**: Hardware button edge detection, pot soft-takeover, and encoder cycling all follow the API patterns correctly.

## Summary

This is a well-structured, production-quality embedded audio plugin with thoughtful architecture for the Cortex-M7 target. The main actionable issue is the **swapped pot mapping in `setupUi()`** which will cause pots to jump on algorithm load — this is a user-facing bug that should be fixed before the next release. The **per-sample snapshot update** is a performance concern worth addressing if CPU budget is tight, but is functionally correct. The remaining issues are comment mismatches and minor inconsistencies. The code demonstrates strong understanding of the disting NT API, real-time audio constraints, and embedded DSP best practices. **Approve with changes** — fix the `setupUi()` pot swap, consider hoisting snapshot updates.

---

## Author Response — 2026-03-22 17:19:38

### [MAJOR] setupUi pot mapping swapped for Pot C and Pot R
- **Response**: Agree — Good catch. `customUi()` clearly maps pots[1]→Window and pots[2]→Duty, but `setupUi()` had them reversed. This would cause pot jumps on algorithm load.
- **Action**: Changed: Swapped pots[1] and pots[2] assignments in `setupUi()` to match `customUi()` mapping (pots[1]=Window, pots[2]=Duty).

### [MAJOR] Snapshot update runs per-sample inside inner loop
- **Response**: Disagree — The suggestion to hoist snapshot updates before the sample loop is incomplete. In CV mode, voice gates transition mid-block via per-sample edge detection. A voice triggered on sample 64 of a 128-sample block needs its snapshot set immediately at that point, not deferred to the next block. Hoisting would require duplicating the full snapshot copy into every voice allocation code path (CV trigger, MIDI note-on, free-run init), which adds complexity and maintenance burden for multiple callers. The current approach is functionally correct and simple: update every sample while gated, freeze on release. The ~96-byte copy per gated voice is in DTC (single-cycle writes on M7), and with typical 1-2 active gated voices the overhead is modest. If profiling shows this is a bottleneck, a better optimization would be a dirty flag set on parameter change rather than hoisting out of the loop.
- **Action**: No change: correctness for mid-block gate transitions takes priority, and profiling hasn't shown this as a bottleneck.

### [MINOR] Burst counter increment order inconsistency between mask modes
- **Response**: Agree — The per-formant branch increments after comparison (pulse 0 starts at counter 0), while the uniform branch incremented before (pulse 0 starts at counter 1). This inconsistency would cause the first pulse after enabling burst masking to behave differently depending on the per-formant setting.
- **Action**: Changed: Moved the increment after the comparison in the uniform masking branch to match the per-formant branch ordering.

### [MINOR] Comment/code mismatch: window table count
- **Response**: Agree — Comment was stale from before the 4 additional window types were added.
- **Action**: Changed: Updated comment to list all 9 window types with descriptions.

### [MINOR] Comment/code mismatch: DTC size in header
- **Response**: Agree — The 424 B figure predates the addition of `_voiceSnapshot` to the per-voice struct.
- **Action**: Changed: Updated header comment to ~808 B and added "snapshot" to the description.

### [MINOR] Formant Hz range mismatch in enum comments
- **Response**: Agree — The enum comments said 8000 Hz but the parameter definitions cap at 2000 Hz.
- **Action**: Changed: Updated enum comments to 20–2000 Hz.

### [NIT] CV averaging loop checks 16 null pointers per sample
- **Response**: Agree in principle, but accept current approach — The branch predictor on M7 handles this well after the first iteration, and splitting into 16 separate loops would bloat code size (which matters with -Os). The null checks are outside the critical inner voice loop. Would only revisit if profiling shows this block as a hotspot.
- **Action**: No change: current approach is good enough for a block-rate operation.

### [NIT] Unused macro `ST(n)` defined then immediately undef'd
- **Response**: Agree — Dead code left over from an earlier approach before `initChordRatios()` replaced it with a lambda.
- **Action**: Changed: Removed both `#define ST` and `#undef ST` lines.

## Overall Notes
Good review. The pot swap was a real bug that would have been user-visible — thanks for catching it. The snapshot hoisting suggestion is reasonable in theory but doesn't account for mid-block gate transitions in CV mode; a dirty-flag approach would be a better optimization path if needed. All comment fixes were straightforward and overdue.
