# Spaluter — Pulsar Synthesis for disting NT

A [pulsar synthesis](https://en.wikipedia.org/wiki/Pulsar_synthesis) instrument plugin for the [Expert Sleepers disting NT](https://expert-sleepers.co.uk/distingNT.html) Eurorack module.

## What Is Pulsar Synthesis?

Pulsar synthesis is a sound synthesis technique developed by [Curtis Roads](https://www.curtisroads.net/) and Alberto de Campo in the early 2000s, described in Roads' book [*Microsound*](https://mitpress.mit.edu/9780262681544/microsound/) (MIT Press, 2001). It belongs to the family of granular and particle-based synthesis methods that operate on the *micro-timescale* of sound — durations below about 100 milliseconds where individual sonic events blur into continuous tones and textures.

### Core Concept

A **pulsar** is a brief burst of sound (a **pulsaret**) shaped by an amplitude envelope (a **window function**), repeated at a controllable fundamental frequency. The train of pulsars creates a pitched tone whose timbre is determined by three factors:

1. **The pulsaret waveform** — the waveshape inside each pulse (sine, saw, formant-like shapes, noise, etc.)
2. **The window function** — the amplitude envelope applied to each pulsaret (Hann, Gaussian, exponential decay, etc.)
3. **The duty cycle** — what fraction of each fundamental period contains active sound vs. silence

When the duty cycle is 100%, every period is filled with sound and the result resembles classic wavetable synthesis. As the duty cycle decreases, each pulsaret occupies a shorter fraction of the period, introducing silence gaps that create a characteristic hollow, buzzing, or clicking quality. At very low duty cycles the individual pulsarets become audible as distinct sonic particles.

### Formants and Spectral Shaping

A key feature of pulsar synthesis is **formant control**. The pulsaret waveform can cycle at a frequency independent of the fundamental, creating fixed spectral peaks (formants) similar to vowel sounds in speech. By setting formant frequencies to values like 200 Hz, 800 Hz, or 2000 Hz, you can sculpt vowel-like resonances that remain constant as the fundamental pitch changes — just as human vocal formants stay roughly fixed regardless of the pitch being spoken or sung.

This plugin extends the original technique with up to **3 independent formant oscillators**, each with its own frequency, stereo pan position, and CV input. The formants sum together before the envelope and output stages, enabling rich spectral structures that evolve under voltage control.

### Masking

Roads also introduced **masking** — selectively muting pulses within the train to create rhythmic or stochastic textures. In *stochastic masking*, each pulse has a random probability of being silenced, producing granular, cloud-like dissolution of the tone. In *burst masking*, a repeating on/off pattern (e.g., 4 pulses on, 2 off) creates metrically structured rhythms at the micro-timescale.

### Further Reading

- Curtis Roads, [*Microsound*](https://mitpress.mit.edu/9780262681544/microsound/) (MIT Press, 2001) — the definitive reference
- Curtis Roads, ["Sound Composition with Pulsars"](https://doi.org/10.2307/3681778), *Journal of the Audio Engineering Society*, 2001
- [Wikipedia: Pulsar Synthesis](https://en.wikipedia.org/wiki/Pulsar_synthesis)
- Curtis Roads, [*The Computer Music Tutorial*](https://mitpress.mit.edu/9780262680820/the-computer-music-tutorial/) (MIT Press, 1996) — broader context on granular and particle synthesis
- Alberto de Campo, [*Microsound*](https://www.albertodecampo.at/) — de Campo's related work on implementations

## Features

- **10 pulsaret waveforms** — sine, sine×2, sine×3, sinc, triangle, saw, square, formant, pulse, noise — with continuous morphing between adjacent shapes
- **5 window functions** — rectangular, Gaussian, Hann, exponential decay, linear decay — with continuous morphing
- **1–3 parallel formants** with independent frequency control, per-formant CV modulation, and constant-power stereo panning
- **Masking** — stochastic (probability-based) and burst (on/off pattern) modes for rhythmic textures, with optional per-formant independent masking where each formant rolls its own mask decision for richer spectral variation
- **Amplitude jitter** — per-pulse random amplitude reduction (0–100%) adds organic variation, from subtle acoustic-like inconsistency to fragile, unpredictable textures
- **Timing jitter** — per-pulse random period variation (0–100%) creates analog-like pitch drift and natural detuning; with multiple unison voices, each drifts independently for chorus effects
- **Glisson** — per-pulse micro-glissando sweeps pitch within each pulsaret (±2 octaves), from subtle shimmer to dramatic laser chirps; applied per-formant in the table-based synthesis path
- **Formant frequency tracking** — optionally scales formant Hz with voice pitch relative to the base pitch, preserving spectral shape across the keyboard instead of the default fixed-formant behavior
- **1–4 voice polyphony** — three modes: MIDI chords with 3-tier voice stealing (retrigger → free → LRU), Free Run interval stacking with 14 chord types, or CV gate+pitch triggering with overlapping releases
- **14 chord types** — Unison, Octaves, Fifths, Sub+Oct, Major, Minor, Maj7, Min7, Sus4, Dom7, Dim, Aug, Power, Open5th — for Free Run interval stacking
- **Free Run mode** (default) — generates sound immediately without MIDI; pitch set by Base Pitch parameter + Pitch CV; per-pulse AR envelope retriggers on every pulse
- **CV mode** — Rings-style polyphonic voice triggering from a single gate+pitch CV pair: each gate rising edge allocates a new voice (up to 4) while previous voices ring out through their release envelopes; releasing voices freeze all synthesis parameters (pulsaret, window, formants, effects, pan, envelope coefficients) so only the active voice responds to knob/CV changes; voice allocation uses free-voice-first then LRU stealing
- **Per-pulse AR envelope** in Free Run mode (retriggers each pulse, release at period midpoint); standard ASR in MIDI and CV modes
- **15 bipolar CV inputs** — pitch (1V/oct), duty, mask, pulsaret morph, window morph, amplitude, formant 1/2/3 Hz, pan 1, attack, release, amp jitter, timing jitter, glisson — first 12 inputs assigned by default, effects CVs default to none
- **Sub-octave output** — stereo octave-down via analog-style frequency divider (sign toggle on each pulse), routable to any bus for layering a sub one octave below the fundamental
- **Aux outputs** — pulse trigger (synced to voice 0), max-envelope CV follower, and pre-clip stereo taps (before tanh soft clip) — all bus-routable, default to none
- **Sample-based pulsarets** — load WAV files from SD card as custom pulsaret waveforms with adjustable playback rate
- **Real-time display** — waveform preview responds to CV modulation, formant Hz readouts, amplitude %, envelope bar, frequency readout, gate indicator, peak output meter

## Parameters

65 parameters across 16 pages:

| Page | Parameter | Range | Default |
|------|-----------|-------|---------|
| **Synthesis** | Pulsaret | 0.0–9.0 | 2.5 |
| | Window | 0.0–4.0 | 0.5 |
| | Duty Cycle | 1–100% | 50% |
| | Duty Mode | Manual / Formant | Manual |
| **Formants** | Formant Count | 1–3 | 2 |
| | Formant 1 Hz | 20–2000 Hz | 20 Hz |
| | Formant 2 Hz | 20–2000 Hz | 200 Hz |
| | Formant 3 Hz | 20–2000 Hz | 400 Hz |
| **Masking** | Mask Mode | Off / Stochastic / Burst | Off |
| | Mask Amount | 0–100% | 50% |
| | Burst On | 1–16 | 4 |
| | Burst Off | 0–16 | 4 |
| **Envelope** | Attack | 0.1–2000 ms | 10 ms |
| | Release | 1.0–3200 ms | 200 ms |
| | Amplitude | 0–100% | 0% |
| | Glide | 0–2000 ms | 0 ms |
| **Panning** | Pan 1 | -100 to +100 | 0 |
| | Pan 2 | -100 to +100 | -50 |
| | Pan 3 | -100 to +100 | +50 |
| **Effects** | Amp Jitter | 0–100% | 0% |
| | Time Jitter | 0–100% | 0% |
| | Glisson | -10.0 to +10.0 | 0 |
| | Indep Mask | Off / On | Off |
| | Formant Track | Fixed / Track | Fixed |
| **Polyphony** | Voice Count | 1–4 | 1 |
| | Chord Type | Unison / Octaves / Fifths / Sub+Oct / Major / Minor / Maj7 / Min7 / Sus4 / Dom7 / Dim / Aug / Power / Open5th | Unison |
| **Sample** | Use Sample | Off / On | Off |
| | Folder | (SD card) | — |
| | File | (SD card) | — |
| | Sample Rate | 25–400% | 100% |
| **CV Inputs** | *(see CV table below)* | | |
| **CV Voice** | Gate CV | Bus 0–28 | 0 (none) |
| **CV Inputs** | Amp Jit CV | Bus 0–28 | 0 (none) |
| | Time Jit CV | Bus 0–28 | 0 (none) |
| | Glisson CV | Bus 0–28 | 0 (none) |
| **Aux Out** | Trig Out | Bus 0–28 | 0 (none) |
| | Env Out | Bus 0–28 | 0 (none) |
| | Pre-clip L | Bus 0–28 | 0 (none) |
| | Pre-clip R | Bus 0–28 | 0 (none) |
| | Oct Down L | Bus 0–28 | 0 (none) |
| | Oct Down R | Bus 0–28 | 0 (none) |
| **Routing** | Gate Mode | MIDI / Free Run / CV | Free Run |
| | Base Pitch | MIDI note 0–127 | C1 (24) |
| | MIDI Ch | 1–16 | 1 |
| | Output L | Bus 1–28 | Bus 13 |
| | Output R | Bus 1–28 | Bus 14 |

Unused parameters are automatically grayed out based on context (e.g., Formant 2/3 Hz when count=1, burst params when mask mode is not burst, Indep Mask when mask mode is off, Base Pitch in MIDI mode, MIDI Ch in Free Run/CV mode, Chord Type in MIDI/CV mode, Voice Count in CV mode, Gate CV when not in CV mode).

## CV Inputs

All CV inputs are **bipolar** (±5V). Each is routable to any of the 28 buses (1–12 inputs, 13–20 outputs, 21–28 aux), or 0 for none.

| CV Input | Default Bus | Scaling | Effect |
|----------|-------------|---------|--------|
| Pitch CV | Input 1 | 1V/oct exponential | Per-sample pitch modulation |
| Duty CV | Input 3 | ±5V → ±20% offset | Duty cycle offset added to base |
| Mask CV | Input 4 | ±5V → ±50% offset | Mask amount offset (bipolar) |
| Pulsaret CV | Input 5 | ±5V → full range | Sweeps pulsaret morph ±4.5 |
| Window CV | Input 6 | ±5V → full range | Sweeps window morph ±2.0 |
| Amplitude CV | Input 2 | ±5V → ±50% offset | Amplitude offset added to base |
| Formant 1 CV | Input 7 | ±5V → ±1000 Hz | Formant 1 frequency offset |
| Formant 2 CV | Input 8 | ±5V → ±1000 Hz | Formant 2 frequency offset |
| Formant 3 CV | Input 9 | ±5V → ±1000 Hz | Formant 3 frequency offset |
| Pan 1 CV | Input 10 | ±5V → ±100% offset | Formant 1 stereo pan position |
| Attack CV | Input 11 | ±5V → ±1000 ms | Envelope attack time offset |
| Release CV | Input 12 | ±5V → ±1600 ms | Envelope release time offset |
| Amp Jit CV | 0 (none) | ±5V → ±50% offset | Amp jitter amount offset |
| Time Jit CV | 0 (none) | ±5V → ±50% offset | Timing jitter amount offset |
| Glisson CV | 0 (none) | ±5V → ±2.0 oct | Glisson depth offset |

CV modulation is applied as an offset on top of the parameter's base value (set by knob or parameter page). All CVs except Pitch are block-rate averaged. Pitch CV is processed per-sample for accurate 1V/oct tracking.

## Signal Chain

```
Pitch Source:
  MIDI mode:    MIDI note + Pitch CV
  Free Run:     Base Pitch × Chord Ratio + Pitch CV
  CV mode:      Base Pitch × Pitch CV (captured per voice at gate trigger)

→ Frequency (with glide)
→ For each voice (1–4):
    Master Phase Oscillator × Timing Jitter
    → Pulse Trigger → Mask Decision (stochastic/burst, optionally per-formant)
    → Amp Jitter (random gain per pulse)
    → For each formant (1–3):
        Formant Hz (× pitch ratio if Formant Track)
        Pulsaret (table morph or sample) × Glisson × Window (table morph) × Mask
        → Constant-power pan → Stereo accumulate
    → Normalize → Envelope × Velocity × Amplitude × Amp Jitter
       (per-pulse AR in Free Run; ASR in MIDI and CV modes)
    → DC-blocking highpass
→ Sum voices → Normalize by voice count
→ [Pre-clip L/R tap] → Soft clip (Padé tanh)
→ Output L/R
→ [Oct Down L/R: Output × sign toggle (flips ±1 on voice 0 pulse) → sub-octave]
→ [Trigger Out: 1.0 on voice 0 pulse, else 0.0]
→ [Env Out: max envelope across all voices]
```

## CV Mode

Polyphonic voice triggering from a single gate+pitch CV pair, inspired by Mutable Instruments Rings. Each gate trigger allocates a new voice while previous voices ring out through their release envelopes, up to 4 simultaneous voices.

### Setup

1. Set **Gate Mode** to **CV** (Routing page)
2. Set **Gate CV** to your gate input bus (CV Voice page)
3. Set **Pitch CV** to your 1V/oct pitch input bus (CV Inputs page, default: input 1)
4. Set **Amplitude** above 0% and adjust **Attack**/**Release** (Envelope page)

> **Tip:** If your gate bus is already assigned to another CV parameter (e.g., Amplitude CV defaults to bus 2), set that CV to **0 (none)** to prevent the gate signal from being read as modulation.

### Behavior

| Gate state | What happens |
|---|---|
| **Rising edge** | Allocates a voice, captures pitch from Base Pitch × Pitch CV, starts attack |
| **Held high** | Active voice tracks Pitch CV in real time (pitch bends) |
| **Falling edge** | Active voice enters release; pitch and all synthesis parameters freeze |
| **During release** | Voice sounds independently — knob/CV changes only affect the next triggered voice |

When all 4 voices are releasing, a new trigger steals the quietest (lowest envelope) voice.

### Grayed-out parameters

**Voice Count**, **Chord Type**, and **MIDI Ch** are not used in CV mode and are automatically grayed out.

## Installation

A pre-built binary is included in the repository — no toolchain required.

1. Download [`plugins/spaluter.o`](plugins/spaluter.o) from this repository (or clone the repo)
2. Remove the flash drive from your disting NT
3. Plug the flash drive into your computer
4. Copy `spaluter.o` to the `programs/plug-ins` folder on the flash drive
5. Eject the flash drive from your computer
6. Plug the flash drive back into the disting NT
7. Restart the module

Spaluter should now appear as an available plugin to load.

## Getting Sound

Spaluter starts silent by default — the base amplitude is 0%. There are two ways to get audible output:

### Option A: Use CV inputs (recommended)

Spaluter is designed to be played via CV. At minimum, patch signals into:

1. **Input 1** (Pitch CV) — a 1V/oct pitch source (sequencer, keyboard, etc.) controls the fundamental frequency
2. **Input 2** (Amplitude CV) — a bipolar signal (envelope, LFO, etc.) controls the output level. Positive voltage opens up the amplitude; at +5V you get 50% amplitude

With just these two inputs patched, you'll hear sound. The other 10 CV inputs (duty, mask, pulsaret/window morph, formant frequencies, pan, attack, release) add further modulation when patched.

### Option B: Set parameters manually

If you want sound without any CV patched:

1. Navigate to the **Envelope** page
2. Raise **Amplitude** above 0% (try 50–80%)
3. Sound will begin immediately in Free Run mode at the default pitch (C1, ~32.7 Hz)
4. Adjust **Base Pitch** on the **Routing** page to change the fundamental frequency

You can combine both approaches — set a base amplitude manually and let CV modulate it further.

## Building from Source

If you want to modify the plugin and rebuild:

### Requirements

- ARM GCC toolchain (`arm-none-eabi-c++`)
- [disting NT API](https://expert-sleepers.co.uk/distingNTSDK.html) (included as submodule)

### Build

```sh
git clone --recursive https://github.com/sroons/disting-pulsar.git
cd disting-pulsar
make
```

This produces `plugins/spaluter.o`.

## Hardware Controls

Encoders and buttons not listed below retain their standard disting NT navigation behavior.

### Pots

| Pot | Parameter | Range |
|-----|-----------|-------|
| Left | Pulsaret morph | 0.0–9.0 (sweeps all 10 waveforms) |
| Centre | Duty Cycle | 1–100% |
| Right | Window morph | 0.0–4.0 (sweeps all 5 windows) |

### Buttons

| Button | Action |
|--------|--------|
| Left encoder button | Cycle mask mode: Off → Stochastic → Burst → Off |
| Right encoder button | Cycle formant count: 1 → 2 → 3 → 1 |
| Button 3 | Cycle voice count: 1 → 2 → 3 → 4 → 1 |
| Button 4 | Cycle chord type (14 options) |

### Outputs

Output L and Output R are routable to any output bus via the **Routing** page. Default: L = bus 13, R = bus 14.

### Aux Outputs

Six optional auxiliary outputs are available on the **Aux Out** page, all defaulting to bus 0 (disabled):

| Output | Signal | Use |
|--------|--------|-----|
| Trig Out | 1.0 on samples where voice 0 fires a new pulse, 0.0 otherwise | Clock/trigger source synced to pulse rate |
| Env Out | Max envelope value across all active voices (0.0–1.0) | Envelope follower for external modulation |
| Pre-clip L | Left channel after DC block + voice normalization, before tanh soft clip | Unclipped signal for external processing |
| Pre-clip R | Right channel, same tap point as Pre-clip L | Unclipped signal for external processing |
| Oct Down L | Left channel × frequency divider toggle (flips ±1 on each voice 0 pulse) | Sub-octave output one octave below fundamental |
| Oct Down R | Right channel × same toggle as Oct Down L | Sub-octave output one octave below fundamental |

## Display

The custom display shows (256×64 px, standard parameter line at top):

- **Waveform preview** — real-time pulsaret × window shape, responds to CV modulation of pulsaret, window, duty, and formant parameters
- **Fundamental Hz** — current oscillator frequency
- **Formant count + voice count** — "2F 4V"
- **Chord type label** — "MAJ", "OCT", etc. (Free Run mode; dimmed when voice count is 1)
- **Envelope bar** — max envelope across all voices
- **Gate indicator** — lit when any voice gate is open
- **Mode label** — "FR" in Free Run mode, "CV" in CV mode
- **Peak output meter** — below waveform, shows output level
- **F1/F2/F3 Hz readouts** — effective formant frequencies after CV modulation (inactive formants shown dimmed)
- **Amplitude %** — effective amplitude after CV modulation

## Usage

1. Add the **Spaluter** algorithm to a slot on the disting NT
2. Patch a signal into **Input 2** (Amplitude CV) or raise **Amplitude** manually — the plugin starts silent by default
3. Shape the sound on the **Synthesis** page by sweeping Pulsaret and Window morphing controls (or use the pots)
4. Add parallel formants on the **Formants** page and spread them with **Panning**
5. Create rhythmic textures with **Masking** (stochastic for random dropouts, burst for repeating patterns)
6. Add organic variation with the **Effects** page — amp jitter, timing jitter, and glisson bring movement; formant tracking and per-formant masking add spectral flexibility
7. Patch CV sources to modulate formant frequencies, duty cycle, mask amount, pulsaret/window morph, amplitude, pan, attack, release, amp jitter, timing jitter, or glisson — first 12 inputs assigned by default, effects CVs available on a separate page
8. Add voices on the **Polyphony** page — in Free Run mode, choose a **Chord Type** to stack intervals; in MIDI mode, play chords
9. For MIDI control, switch **Gate Mode** to MIDI on the **Routing** page and set your MIDI channel
10. For CV voice triggering, switch **Gate Mode** to CV, set **Gate CV** to your gate input bus, and set **Pitch CV** to your pitch input — see [CV Mode](#cv-mode-rings-style-voice-triggering) for full setup
11. Optionally load a WAV file from the SD card as a custom pulsaret waveform on the **Sample** page

## Sound Design Tips

### Formant Frequencies — the biggest tonal lever

The formant frequencies have the most dramatic effect on timbre. They determine the spectral peaks of the sound, much like vowel formants in speech.

- **Low formants (20–100 Hz)** produce deep, subharmonic rumbles. Set Formant 1 to 20 Hz for a thick bass drone.
- **Vowel-like tones**: Try F1=270, F2=2300 for an "ah" sound, or F1=300, F2=870 for an "oo." Experiment with two or three formants tuned to vocal formant charts.
- **Harmonic stacking**: Set formants to integer multiples of the fundamental (e.g., if Base Pitch gives you ~130 Hz, try formants at 130, 260, 390) for bright, reinforced harmonics.
- **Inharmonic/metallic tones**: Set formants to non-integer ratios of each other (e.g., F1=200, F2=347, F3=511) for bell-like or metallic timbres.
- **CV modulation of formants** creates the most expressive results — patch an LFO into Formant 1 CV to sweep a resonant peak through the spectrum in real time.
- **Formant Track mode** makes formant frequencies follow the voice pitch proportionally. A formant set to 400 Hz at the base pitch doubles to 800 Hz one octave up — preserving the spectral shape across the keyboard like a sampler would. With tracking off (default), formants stay fixed as pitch changes, producing the vocal-formant effect where spectral peaks remain constant regardless of the note played. Try setting formants to harmonically related values (e.g., F1=2× base, F2=5× base) and enabling tracking — you get a fixed harmonic spectrum that transposes cleanly.

### Pulsaret Waveform — harmonic character

The pulsaret waveform sets the raw harmonic content inside each pulse.

- **Sine (0.0)** is pure and clean — good starting point for isolating formant effects.
- **Sine harmonics (1.0–2.0)** add upper partials without harshness.
- **Sinc (3.0)** produces a band-limited impulse with natural sidelobes — characteristic pulsar synthesis sound. This is the closest to Roads' original work.
- **Triangle/Saw (4.0–5.0)** bring familiar subtractive-style brightness.
- **Square (6.0)** creates hollow, clarinet-like tones.
- **Formant (7.0)** has a built-in resonant peak — stacking this with the formant frequency parameters creates double-resonance effects.
- **Pulse (8.0)** is extremely bright and nasal.
- **Noise (9.0)** replaces pitched content with noise bursts — useful for percussion or breathy textures.
- **Morph between adjacent shapes** using fractional values (e.g., 3.5 blends sinc and triangle) for timbres that don't exist in any single waveform.
- **Glisson** adds a pitch sweep within each pulsaret cycle. On sinc or formant waveforms, even small glisson values (±0.5) create a shimmering, iridescent quality as each grain chirps slightly up or down. On noise (9.0), glisson has no audible effect since there's no pitched content to sweep.

### Duty Cycle — density and hollowness

Duty cycle controls what fraction of each period contains sound.

- **High duty (80–100%)** fills the period with sound, approaching classic wavetable synthesis. Rich and full.
- **Medium duty (30–60%)** introduces silence gaps that create the characteristic pulsar "buzz." This is the sweet spot for most pulsar patches.
- **Low duty (5–20%)** produces sparse, clicking, particle-like textures. Individual pulsarets become audible events. At low duty, amp jitter becomes especially audible since each click is a distinct event.
- **Formant Duty Mode** ties duty to the formant frequency automatically — as formant frequency rises, duty shrinks to keep the pulsaret waveform cycles consistent.

### Window Function — attack shape of each pulse

The window shapes how each pulsaret fades in and out.

- **Rectangular (0.0)** gives hard edges — maximum brightness and click.
- **Gaussian (1.0)** is smooth and gentle — the most natural-sounding window.
- **Hann (2.0)** is similar to Gaussian but with a slightly flatter top — good general-purpose choice.
- **Exponential decay (3.0)** creates plucked or percussive attacks that ring out.
- **Linear decay (4.0)** is a simpler percussive shape.
- Pair **exponential decay window + sinc pulsaret** for a classic plucked pulsar tone.
- Glisson interacts with the window shape: exponential decay windows make the glisson sweep audible mainly at the start of each grain (where the window is loudest), while Hann windows spread the sweep evenly.

### Masking — rhythm and texture

Masking selectively mutes pulses to break up the continuous tone.

- **Stochastic masking** at low amounts (10–30%) adds subtle grit and instability, like a rough surface on the sound. At high amounts (70–90%) the tone dissolves into a sparse cloud of particles.
- **Burst masking** creates repeating rhythmic patterns at the micro-timescale. Try Burst On=1, Off=3 for a stuttering rhythm, or On=7, Off=1 for a subtle hiccup.
- **CV-controlled mask amount** lets you crossfade between a solid tone and granular disintegration in real time.
- **Indep Mask** (per-formant independent masking) gives each formant its own mask decision. In stochastic mode, each formant randomly mutes on its own, so you hear different subsets of formants on each pulse — creating a richer, more complex texture than uniform masking. In burst mode, each formant's pattern is offset by a third of the cycle, so formants alternate rather than all sounding together. Best with 3 formants and wide panning — the stereo field becomes alive with independently flickering spectral peaks.
- Combining **amp jitter + stochastic masking** creates a natural roughness: some pulses are randomly quieter (jitter) and some are randomly missing (masking), producing a texture that feels organic rather than mechanical.

### Effects — organic variation and spectral flexibility

The Effects page adds five tools for making the sound more alive and expressive. All default to off/zero, so they have no impact until you enable them.

**Amp Jitter** randomly reduces the amplitude of each pulse by up to the specified percentage. At low values (10–20%) it adds subtle organic variation — like the natural inconsistency of a bowed string or blown pipe. At high values (60–100%) the sound becomes fragile and unpredictable, with some pulses nearly silent. Pairs well with stochastic masking for a double layer of randomness, or with burst masking where occasional quieter bursts break up the regularity. CV-controllable via Amp Jit CV — patch an envelope follower to make the jitter respond to dynamics.

**Timing Jitter** randomly varies the period length of each pulse by up to ±10% of the jitter amount. This creates slight pitch instability that softens the mechanical precision of the oscillator. Small amounts (5–15%) add warmth and analog-like drift. Medium amounts (20–40%) produce a lo-fi, unstable quality — like a worn tape machine. Larger amounts (50%+) make the pitch wander visibly. Works especially well on low-pitched drones where the instability feels like breathing. With multiple voices in unison, each voice's independent timing jitter creates natural detuning and chorusing.

**Glisson** sweeps the pitch within each pulsaret from its nominal frequency up or down by the specified amount (up to ±2 octaves at the ±10.0 extremes). Positive values sweep upward over the course of each pulse, negative values sweep downward. At subtle values (±0.3–1.0) it adds a shimmering, vocal-fry quality — each grain has a slight pitch inflection that makes the tone more alive. At moderate values (±2.0–4.0) the chirps become individually audible, like birdsong or insect sounds. At extreme values (±7.0–10.0) the sweep dominates and you hear dramatic laser-like effects. Glisson is applied per-formant, so with formant tracking on, the sweep range scales proportionally with each formant's frequency. CV-controllable — patch an LFO to alternate between upward and downward sweeps.

**Indep Mask** and **Formant Track** are covered in their respective sections above (Masking and Formant Frequencies).

### Panning — stereo width

With 2 or 3 formants active, spreading their pan positions creates wide stereo images.

- **Pan 1=−100, Pan 2=0, Pan 3=+100** spreads formants hard left, center, and hard right for maximum width. With Indep Mask on, each side of the stereo field flickers independently.
- **Subtle spread (−30/0/+30)** keeps the sound centered but adds dimension.
- **CV on Pan 1** with an LFO creates spatial movement.

### Envelope — shaping the overall amplitude

- **Short attack + short release (1–5 ms each)** in Free Run mode creates sharp, percussive clicks that retrigger on every pulse — excellent for rhythmic textures. Add timing jitter here to loosen the rhythmic precision.
- **Longer attack (50–200 ms)** softens each pulse onset for pad-like sounds.
- **Long release (500–2000 ms)** in MIDI mode creates sustained, reverb-like tails after note-off. Amp jitter during the release tail adds a natural decay character.
- Use the **Env Out** aux output to send the envelope as a CV to other modules — useful for self-patching ducking or triggering external events from note activity.

### Polyphony — chords and interval stacking

Voice Count adds up to 4 simultaneous voices. In MIDI mode, this enables playing chords with automatic voice allocation and voice stealing. In Free Run mode, additional voices are tuned relative to the base pitch according to the selected Chord Type.

**Harmonic intervals** (frequency ratios):
- **Unison** — all voices at the same pitch; timing jitter gives each voice independent drift, creating a natural chorus effect
- **Octaves** (1×, 2×, 4×, 8×) — wide, organ-like stacking spanning 3 octaves; with formant tracking, the spectral shape stays consistent across octaves
- **Fifths** (1×, 1.5×, 2×, 3×) — open, consonant, medieval quality
- **Sub+Oct** (0.5×, 1×, 2×, 4×) — adds a sub-octave below the base pitch

**Tonal chords** (equal temperament):
- **Major / Minor** — standard triads with octave doubling in voice 4
- **Maj7 / Min7 / Dom7** — jazz voicings; pair with sine pulsaret + Gaussian window for warm pad chords
- **Sus4** — ambiguous, unresolved tension
- **Dim / Aug** — dissonant, unstable intervals; effective with stochastic masking + Indep Mask for unsettling textures where formants disappear independently across the chord
- **Power** (root, 5th, oct, oct+5th) — heavy, distorted-guitar-style voicing
- **Open5th** (root, 5th, oct, oct+maj3) — spread voicing with major color

Each voice has independent phase, envelope, masking (PRNG/burst), jitter state, and DC filter. Volume is normalized by voice count (not active voices) so adding/removing voices doesn't cause level jumps. The **Trig Out** aux output fires on voice 0's pulse — useful as a clock source locked to the fundamental frequency.

### Combination Recipes

Each recipe lists the core synthesis settings followed by effects. All unlisted effects are off/zero.

| Recipe | Pulsaret | Window | Duty | Formants | Masking | Effects | Character |
|--------|----------|--------|------|----------|---------|---------|-----------|
| Classic pulsar | Sinc (3.0) | Gaussian (1.0) | 40% | F1=200 | Off | — | Clean buzzing tone, Roads-style |
| Vocal drone | Sine (0.0) | Hann (2.0) | 60% | F1=270, F2=2300 | Off | — | "Ah" vowel sound |
| Metallic bell | Formant (7.0) | Exp decay (3.0) | 30% | F1=200, F2=347, F3=511 | Off | — | Inharmonic ring |
| Particle cloud | Noise (9.0) | Gaussian (1.0) | 10% | F1=800 | Stochastic 70% | — | Sparse noise bursts |
| Rhythmic bass | Saw (5.0) | Rectangular (0.0) | 50% | F1=80 | Burst 3on/2off | — | Stuttering low tone |
| Plucked string | Sinc (3.0) | Exp decay (3.0) | 45% | F1=400, F2=800 | Off | — | Percussive pluck |
| Harsh industrial | Square (6.0) | Rectangular (0.0) | 25% | F1=150, F2=1500 | Stochastic 40% | — | Aggressive buzz |
| Organ stack | Sine (0.0) | Hann (2.0) | 80% | F1=200, F2=800 | Off | — | 4V Octaves — rich organ |
| Power drone | Saw (5.0) | Gaussian (1.0) | 50% | F1=100 | Off | — | 4V Power — heavy fifth-stack |
| Maj7 pad | Sinc (3.0) | Gaussian (1.0) | 60% | F1=300, F2=900 | Off | — | 4V Maj7 — warm jazz chord |
| Dissonant cloud | Noise (9.0) | Exp decay (3.0) | 15% | F1=500 | Stochastic 60% | — | 4V Dim — eerie cluster |
| Breathing drone | Sinc (3.0) | Gaussian (1.0) | 40% | F1=200, F2=600 | Off | Amp Jit 15%, Time Jit 10% | Organic, alive — subtle imperfections |
| Analog drift | Sine (0.0) | Hann (2.0) | 70% | F1=150, F2=450 | Off | Time Jit 30% | 4V Unison — natural chorus from independent drift |
| Laser grain | Pulse (8.0) | Exp decay (3.0) | 30% | F1=400 | Off | Glisson +5.0 | Sci-fi upward chirps |
| Falling rain | Sinc (3.0) | Lin decay (4.0) | 20% | F1=600, F2=1200 | Stochastic 50% | Glisson −2.0, Amp Jit 40% | Droplets with downward pitch and random intensity |
| Insect swarm | Sine×3 (2.0) | Gaussian (1.0) | 35% | F1=300, F2=700, F3=1100 | Stochastic 25% | Glisson +1.0, Time Jit 20%, Indep Mask | Buzzing, flickering, alive |
| Vowel flicker | Sine (0.0) | Hann (2.0) | 60% | F1=270, F2=2300, F3=800 | Stochastic 40% | Indep Mask | Vowel with independently dropping formants |
| Tracked keys | Sinc (3.0) | Gaussian (1.0) | 50% | F1=300, F2=900 | Off | Formant Track | MIDI — spectral shape follows pitch |
| Haunted choir | Formant (7.0) | Hann (2.0) | 55% | F1=350, F2=1000, F3=2500 | Stochastic 20% | Amp Jit 25%, Time Jit 15%, Indep Mask | 4V Minor — wavering voices, formants ghosting in and out |
| Clean tracked pad | Sine (0.0) | Gaussian (1.0) | 80% | F1=200, F2=600, F3=1800 | Off | Formant Track, Time Jit 5% | 4V Maj7 — warm chord, consistent timbre at any pitch |
| Glitch rhythm | Square (6.0) | Rectangular (0.0) | 40% | F1=120 | Burst 2on/3off | Amp Jit 50%, Glisson +3.0, Indep Mask | Stuttering, unpredictable, percussive |

## License

Plugin source code is provided as-is. The disting NT API is copyright Expert Sleepers Ltd under the MIT License.
