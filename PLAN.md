# visual-art, basically

A Python app that listens to live audio and draws visuals with pygame.
Each visual is one file. A CLI plays one visual, or shuffles through all of them
with crossfades, which is what we'll use during a live set. It can also render
a song to an MP4 that plays on any projector or TV without a laptop.

Guiding rule: **simple, obvious, boring code.** One job per file. No magic.

---

## Folder layout

```
visual-art/
├── pyproject.toml
└── src/visual_art/
    ├── __init__.py          # empty
    ├── cli.py               # reads command-line args, starts the Player
    ├── audio.py             # AudioInput (microphone/interface) and AudioFrame (the numbers)
    ├── visual.py            # Visual: the base class every visual extends
    ├── registry.py          # finds every visual in visuals/
    ├── shuffle.py           # Shuffle: picks which visual comes next
    ├── crossfade.py         # Crossfade: blends one visual into the next
    ├── show.py              # Show: current visual + shuffle + crossfade, no window
    ├── player.py            # Player: live window, keyboard, clock (drives a Show)
    ├── render.py            # render(): audio file -> MP4 (drives a Show, no window)
    └── visuals/
        ├── __init__.py      # empty
        ├── _template.py     # copy this to make a new visual
        ├── pulse.py         # example: circle that grows with volume
        └── bars.py          # example: frequency bars
```

Files in `visuals/` that start with `_` are ignored. That's how the template
stays out of the shuffle.

---

## How the pieces fit together

```
  audio interface
        │
        ▼
  AudioInput ──read()──▶ AudioFrame (volume, bass, mids, highs, spectrum)
                              │
                              ▼
  cli.py ──▶ Player (live window)  ─┐
                                    ├──▶ Show ──each frame──▶ visual.update(audio, dt)
  cli.py ──▶ render() (MP4 file)   ─┘     │                  visual.draw(surface)
                                          ├── Shuffle    decides what plays next
                                          └── Crossfade  blends old → new during a switch
```

The `Show` doesn't know whether it's feeding a window or a video file. That's
what lets live mode and video export share every visual, shuffle and fade.

Each frame, live:

1. The Player handles keyboard events.
2. The Player reads the latest audio into an `AudioFrame`.
3. The Player calls `show.step(audio, dt, screen)`, and the Show:
   - checks whether it's time to switch visuals, and if so starts a `Crossfade`;
   - calls `update()` then `draw()` on the current visual, or on both while a fade runs.
4. The Player flips the screen.

When rendering a video, `render()` does steps 2–3 with audio from the file and a
fixed `dt`, then hands the finished frame to ffmpeg instead of the screen.

---

## The classes

### `AudioFrame` (audio.py)

A plain dataclass. It holds numbers only and has no methods to learn.

```python
@dataclass
class AudioFrame:
    samples: np.ndarray    # the raw audio block, mono, floats -1..1
    spectrum: np.ndarray   # FFT magnitudes, low → high frequency
    volume: float          # overall loudness, ~0..1
    bass: float            # ~20–250 Hz, ~0..1
    mids: float            # ~250–4000 Hz, ~0..1
    highs: float           # ~4000 Hz and up, ~0..1
```

Visuals only ever see an `AudioFrame`. They never touch sounddevice.

### `analyze()` (audio.py)

```python
def analyze(samples: np.ndarray, samplerate: int) -> AudioFrame: ...
```

A plain function that turns one block of mono samples into an `AudioFrame`
(FFT, bass/mids/highs, volume). Both `AudioInput` (live) and `render()` (file)
call it, so a visual reacts the same way to a song whether it's live or rendered.

`volume`, `bass`, `mids` and `highs` are the loudness (RMS) in each range,
multiplied by the `*_SCALE` constants at the top of `audio.py` so loud music
reads about 1, and capped at 1. The scales are a first guess from test audio;
tune them once with real music, then use `--gain` per venue.

### `AudioInput` (audio.py)

Wraps `sounddevice.InputStream`.

- `start()` / `stop()`
- `read() -> AudioFrame`

The sounddevice callback runs on its own thread. It only copies the newest audio
block into `self.latest`. All the math (FFT, bass/mids/highs) happens in `read()`
on the main thread (by calling `analyze()`), which keeps threading simple.

`--gain` multiplies the input so we can match loudness at the venue.

### `Visual` (visual.py)

The base class. This is what a visual author implements.

```python
class Visual:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

    def update(self, audio: AudioFrame, dt: float) -> None:
        """Change state. dt = seconds since last frame."""

    def draw(self, surface: pygame.Surface) -> None:
        """Paint the whole surface. Must fill the background first."""
        raise NotImplementedError
```

Rules for visuals:

- **Set up in `__init__`, change things in `update`, paint in `draw`.** Don't draw inside `update`.
- **Multiply movement by `dt`** so speed doesn't depend on frame rate.
- **Always fill the background in `draw`.** The crossfade relies on each visual painting its whole surface.
- **One `Visual` class per file.** The file name is the visual's name: `visuals/bars.py` is `bars`.

A visual gets a fresh instance every time it comes on screen, so it always starts clean.

### `find_visuals()` (registry.py)

A function, not a class.

```python
def find_visuals() -> dict[str, type[Visual]]:
    # {"bars": BarsVisual, "pulse": PulseVisual, ...}
```

It imports every module in `visual_art/visuals/` whose name doesn't start with `_`,
and finds the `Visual` subclass in each one. If a file has zero or more than one
subclass, it raises a clear error that names the file.

No decorators and no manual registration: drop a file in and it shows up.

### `Shuffle` (shuffle.py)

```python
class Shuffle:
    def __init__(self, names: list[str]) -> None: ...
    def next(self) -> str: ...
```

Works like shuffling a deck of cards. It plays every visual once in random order,
then reshuffles, and never plays the same one twice in a row. The audience sees
everything and nothing repeats back to back.

### `Crossfade` (crossfade.py)

```python
class Crossfade:
    def __init__(self, old: Visual, new: Visual, seconds: float) -> None: ...
    def update(self, audio: AudioFrame, dt: float) -> None: ...  # updates both visuals
    def draw(self, screen, old_surface, new_surface) -> None: ...
    @property
    def done(self) -> bool: ...
```

How it draws:

1. `old.draw(old_surface)`, then `new.draw(new_surface)`.
2. Blit `old_surface` to the screen.
3. `new_surface.set_alpha(255 * progress)` and blit it on top.

Drawing the new visual on top with rising alpha is exactly "one fades out while the
other fades in." When `done` is true, the Show drops the old visual.

### `Show` (show.py)

Owns the current visual, the `Shuffle`, the `Crossfade` and the switch timer.
It has no window, clock or audio device. It's handed audio and a time step, and
paints a surface.

```python
class Show:
    def __init__(self, visuals, width, height, names, seconds=None, fade=4.0, seed=None) -> None: ...
    def step(self, audio: AudioFrame, dt: float, surface: pygame.Surface) -> None: ...
    def skip(self) -> None: ...   # start a fade to the next visual now
```

- `names` with one entry and `seconds=None` means one visual, forever (`play`).
- Several names plus `seconds` means rotate with crossfades (`shuffle`).
- `seed` makes `Shuffle` pick the same order every time, so a video re-renders identically.

### `Player` (player.py)

Owns the window, the clock, the keyboard and the live `AudioInput`. Each frame it
reads audio, calls `show.step(audio, dt, screen)` and flips the display.

```python
class Player:
    def __init__(self, show: Show, audio: AudioInput, fullscreen=True, display=0, fps=60) -> None: ...
    def run(self) -> None: ...
```

Keys while running:

| Key          | Does                               |
|--------------|------------------------------------|
| `Esc` / `Q`  | Quit                               |
| `Space`      | Skip to next visual now (with fade) |
| `F`          | Toggle fullscreen                  |

It opens fullscreen by default, on the screen given by `display`, and hides the
mouse. The Show draws at a fixed size (1920×1080 by default, the same as video
export), and pygame's `SCALED` mode stretches that to fit the screen. A projector
with a different shape, such as 16:10 or 4:3, gets black bars instead of a
stretched picture. pygame keeps the Mac from sleeping or starting the screensaver
while the window is open.

`Space` matters for a live set: if a visual doesn't fit the song, move on.

### `render()` (render.py)

Turns an audio file into a video file, frame by frame, without opening a window.

```python
def render(audio_path, out_path, show: Show, width, height, fps=30, include_audio=True) -> None: ...
```

1. Read the whole audio file (`soundfile`) and mix it to mono for analysis.
2. For frame `i`, take the block of samples ending at `i / fps` seconds and call `analyze()`.
3. Call `show.step(audio, 1 / fps, surface)` on an off-screen `pygame.Surface`.
4. Write the surface's raw RGB bytes (`pygame.image.tobytes`) into ffmpeg's stdin.
5. ffmpeg encodes the frames and adds the original audio track.

It renders from a file and doesn't record the live window. That way every frame
is exact, with no dropped frames and no screen-capture stutter. A slow visual
only makes the render take longer; the video still plays smoothly. `dt` is
always exactly `1 / fps`, which is another reason visuals must multiply movement
by `dt`.

**The ffmpeg binary comes from the `imageio-ffmpeg` package**, so collaborators
don't need Homebrew or a separate install. `render.py` gets its path from
`imageio_ffmpeg.get_ffmpeg_exe()`.

#### Output format: chosen to play anywhere

Projectors, smart TVs, media players and venue laptops all play this combination:

| Setting | Value | Why |
|---|---|---|
| Container | `.mp4` with `-movflags +faststart` | Plays from a USB stick and starts instantly |
| Video codec | H.264 (`libx264`), High profile, level 4.1 | Supported by every player made in the last 15 years. HEVC/AV1 are not |
| Pixel format | `yuv420p` | Players often show black or refuse 4:4:4 / RGB video |
| Size | 1920×1080 default, always even numbers | 1080p is the safe maximum for older projectors; H.264 needs even dimensions |
| Frame rate | 30 fps constant (`--fps 60` optional) | Constant rate avoids stutter and drift on hardware players |
| Quality | `-crf 18 -maxrate 12M -bufsize 24M` | Looks clean on busy visuals; the cap keeps cheap players from choking |
| Keyframes | every 2 seconds (`-g 60` at 30 fps) | Seeking and looping work well |
| Colour | Convert with the bt709 matrix (`-vf scale=out_color_matrix=bt709`) and tag the file bt709 | Without both, colours come out washed-out or shifted on TVs |
| Audio | AAC, 48 kHz, 192 kbps stereo | Universal. `--silent` leaves it out for looping backdrops |

Full ffmpeg command `render.py` builds (30 fps, 1080p):

```bash
ffmpeg -y -f rawvideo -pix_fmt rgb24 -s 1920x1080 -r 30 -i - \
       -i song.wav -map 0:v -map 1:a -shortest \
       -c:v libx264 -profile:v high -level 4.1 -preset slow \
       -crf 18 -maxrate 12M -bufsize 24M -g 60 \
       -vf scale=out_color_matrix=bt709:out_range=tv -pix_fmt yuv420p \
       -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
       -x264-params colorprim=bt709:transfer=bt709:colormatrix=bt709 \
       -c:a aac -ar 48000 -b:a 192k -movflags +faststart out.mp4
```

At the 12 Mbps cap an hour is about 5.4 GB. USB sticks formatted FAT32 can't
hold files over 4 GB, so format the stick as exFAT or render the set in parts.

---

## The CLI (cli.py)

Uses `argparse` from the standard library with subcommands.

```bash
visual-art list                               # show available visuals
visual-art devices                            # show audio inputs (find your interface / BlackHole)
visual-art displays                           # show screens (find the projector's number)
visual-art play bars                          # play one visual
visual-art shuffle --seconds 45 --fade 4      # the live set mode
visual-art render song.wav --out show.mp4 --shuffle --seconds 45 --fade 4 --seed 1
visual-art render song.wav --out bars.mp4 --visual bars
```

Options for `render`:

| Option                 | Default          | Meaning                                         |
|------------------------|------------------|-------------------------------------------------|
| `--out`                | `<song>.mp4` in `renders/` | Output file                           |
| `--visual NAME`        |                  | Render one visual for the whole song            |
| `--shuffle`            |                  | Rotate through all visuals (`--seconds`, `--fade` as in `shuffle`) |
| `--seed`               | random           | Fix the shuffle order so re-renders match       |
| `--size`               | `1920x1080`      | Video size                                      |
| `--fps`                | 30               | Frame rate                                      |
| `--silent`             | off              | Leave the audio track out                       |

Options for `play` and `shuffle`:

| Option         | Default | Meaning                                      |
|----------------|---------|----------------------------------------------|
| `--device`     | system  | Audio input, by name or number from `devices` |
| `--gain`       | 1.0     | Input loudness multiplier                    |
| `--display`    | 0       | Screen to open on, number from `displays`    |
| `--windowed`   | off     | Open in a window instead of fullscreen       |
| `--size`       | `1920x1080` | Drawing size, stretched to fit the screen |

In `pyproject.toml`, point the script at the CLI:

```toml
[project.scripts]
visual-art = "visual_art.cli:main"
```

---

## The template (visuals/_template.py)

```python
"""
HOW TO MAKE A NEW VISUAL
  1. Copy this file:   cp _template.py my_thing.py
  2. Rename the class: TemplateVisual -> MyThingVisual
  3. Try it:           visual-art play my_thing
It's automatically included in shuffle.
"""
import pygame

from visual_art.audio import AudioFrame
from visual_art.visual import Visual


class TemplateVisual(Visual):
    def __init__(self, width: int, height: int) -> None:
        super().__init__(width, height)
        # Set up anything you need to remember between frames.
        self.radius = 0.0

    def update(self, audio: AudioFrame, dt: float) -> None:
        # React to the music. Available: audio.volume, audio.bass,
        # audio.mids, audio.highs, audio.spectrum, audio.samples
        self.radius = 50 + audio.bass * 400

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((0, 0, 0))  # always clear first
        center = (self.width // 2, self.height // 2)
        pygame.draw.circle(surface, (255, 255, 255), center, int(self.radius))
```

---

## Build order

Each step runs on its own before moving to the next.

1. **Dependencies:** `uv add pygame-ce`. This is the community edition of pygame. It has the same `import pygame` API and ships wheels for new Python versions.
2. **`audio.py`:** `AudioInput` + `AudioFrame`. Test by printing `bass/mids/highs` in a loop.
3. **`visual.py` + `visuals/_template.py` + `visuals/pulse.py`.**
4. **`show.py` + `player.py`:** one visual only, no switching. Get one visual on screen reacting to sound.
5. **`registry.py` + `cli.py`:** `list`, `devices`, `play`.
6. **`shuffle.py`:** switching in `Show` with hard cuts, no fading yet.
7. **`crossfade.py`:** replace hard cuts with fades.
8. **`visuals/bars.py`:** a second example, so shuffle has something to switch between.
9. **`render.py`:** `uv add soundfile imageio-ffmpeg`. Render a 30-second clip, then check it plays in QuickTime, VLC and from a USB stick in a TV or projector.

## Later, not now

Leave these out until they're needed:

- Auto-gain that adapts to the room's loudness
- Beat detection (`audio.beat: bool`)
- Per-visual settings or a config file
- `shuffle --only bars,pulse` to limit the rotation
- Other transition styles

---

## Setup notes

### Environment

```bash
cd ~/Developer/Visual/visual-art
uv python install 3.14
uv venv --python 3.14
source .venv/bin/activate
```

A venv doesn't hold its own copy of Python. It points to an installed interpreter.
Add packages with `uv add <pkg>`.

### Audio on macOS

- Python has no built-in for mic capture. We use `sounddevice`, which wraps PortAudio and returns NumPy arrays.
- **Mic permission:** if input is silent, go to System Settings → Privacy & Security → Microphone and allow your terminal.
- **System audio** (Spotify, a DAW, etc.): install BlackHole (`brew install blackhole-2ch`), route output through it, and pick it with `--device`.
